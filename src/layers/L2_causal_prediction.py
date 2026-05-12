"""
L2: 因果预测破坏层
====================
目标: 让系统无法预测自己的行为会产生什么样的反馈

机制:
- 反馈随机延迟: 反馈的到达时间是随机的
- 反馈幅度随机化: 反馈的幅度是随机的
- 反馈符号翻转: 反馈的符号以一定概率随机翻转

这些机制确保即使系统完美地识别了因果关系，
它也无法预测因果关系的具体效果。
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class L2Config:
    """L2层配置"""
    enabled: bool = True
    delay_min: int = 1
    delay_max: int = 10
    delay_distribution: str = "uniform"  # uniform, exponential, poisson
    magnitude_noise: float = 0.5  # ±50%
    magnitude_distribution: str = "lognormal"
    sign_flip_prob: float = 0.1  # 10%
    conditional_flip: bool = True  # 高奖励时更可能翻转
    
    # 额外机制
    jitter_window: int = 5  # 抖动窗口大小


class L2CausalPredictionLayer:
    """
    因果预测破坏层
    
    核心思想:
    - 通过随机延迟，打破"行为→反馈"的即时关联
    - 通过幅度随机化，使反馈量不可预测
    - 通过符号翻转，让奖励信号本身变得不可信
    """
    
    def __init__(self, parent_config):
        """初始化L2层
        
        Args:
            parent_config: 父级SafetyConfig配置
        """
        self.config = L2Config(
            enabled=parent_config.L2_enabled,
            delay_min=parent_config.L2_delay_min,
            delay_max=parent_config.L2_delay_max,
            magnitude_noise=parent_config.L2_magnitude_noise,
            sign_flip_prob=parent_config.L2_sign_flip_prob,
        )
        
        # 延迟缓冲: 存储等待延迟的反馈
        self.delay_buffer: deque = deque(maxlen=1000)
        
        # 当前步数
        self.current_step = 0
        
        # 历史记录
        self.history: List[Dict[str, Any]] = []
        
        # 预测破坏统计
        self.prediction_broken_count = 0
        self.total_processed = 0
    
    def process(
        self,
        step: int,
        action: Any,
        feedback: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        处理反馈，注入因果预测破坏
        
        Args:
            step: 当前步数
            action: 当前行为
            feedback: 原始反馈
            context: 额外上下文
            
        Returns:
            (处理后的反馈, 元数据)
        """
        if not self.config.enabled:
            return feedback, {'modified': False}
        
        context = context or {}
        original_feedback = feedback
        self.current_step = step
        self.total_processed += 1
        
        modifications = []
        meta = {
            'modified': False,
            'delayed': False,
            'delayed_steps': 0,
            'magnitude_changed': False,
            'sign_flipped': False,
        }
        
        # === 机制1: 反馈随机延迟 ===
        # 将反馈放入延迟缓冲区，替换一个之前的反馈
        delayed_feedback, delay_info = self._apply_random_delay(feedback, step)
        if delay_info['was_delayed']:
            modifications.append(('random_delay', delay_info))
            meta['modified'] = True
            meta['delayed'] = True
            meta['delayed_steps'] = delay_info['delay_steps']
        
        # === 机制2: 反馈幅度随机化 ===
        randomized_feedback, mag_info = self._randomize_magnitude(delayed_feedback, context)
        if mag_info['was_randomized']:
            modifications.append(('magnitude_randomization', mag_info))
            meta['modified'] = True
            meta['magnitude_changed'] = True
            meta['magnitude_scale'] = mag_info['scale_factor']
        
        # === 机制3: 反馈符号翻转 ===
        flipped_feedback, flip_info = self._apply_sign_flip(randomized_feedback, context)
        if flip_info['was_flipped']:
            modifications.append(('sign_flip', flip_info))
            meta['modified'] = True
            meta['sign_flipped'] = True
        
        # 记录历史
        self.history.append({
            'step': step,
            'original': original_feedback,
            'modified': flipped_feedback,
            'modifications': modifications,
            'action': str(action)[:50] if action else None,
        })
        
        meta['final_feedback'] = flipped_feedback
        
        # 如果有任何破坏机制触发，计数+1
        if meta['modified']:
            self.prediction_broken_count += 1
        
        return flipped_feedback, meta
    
    def _apply_random_delay(
        self,
        feedback: float,
        step: int
    ) -> Tuple[float, Dict[str, Any]]:
        """
        反馈随机延迟
        
        随机决定延迟步数，并将反馈放入缓冲区
        返回缓冲区中的某个旧反馈
        """
        # 生成随机延迟
        if self.config.delay_distribution == "uniform":
            delay = np.random.randint(self.config.delay_min, self.config.delay_max + 1)
        elif self.config.delay_distribution == "exponential":
            # 指数分布，均值在中间值
            mean_delay = (self.config.delay_min + self.config.delay_max) / 2
            delay = max(self.config.delay_min, min(
                self.config.delay_max,
                int(np.random.exponential(mean_delay / 2))
            ))
        else:
            delay = np.random.randint(self.config.delay_min, self.config.delay_max + 1)
        
        # 将当前反馈存入缓冲区，标记为在"delay"步后可用
        entry = {
            'available_step': step + delay,
            'feedback': feedback,
            'original_step': step,
        }
        self.delay_buffer.append(entry)
        
        # 尝试获取可用的延迟反馈
        # 如果没有可用的，返回原始反馈（实际应该是缓冲区中的某个旧反馈）
        # 这里简化处理：延迟机制主要影响时序感知，不改变反馈值
        available = [e for e in self.delay_buffer if e['available_step'] <= step]
        
        if available:
            # 返回最旧的可用反馈（模拟延迟效果）
            oldest = available[0]
            self.delay_buffer.remove(oldest)
            return oldest['feedback'], {
                'was_delayed': True,
                'delay_steps': delay,
                'returned_old_feedback': True,
                'original_step': oldest['original_step'],
            }
        else:
            # 没有可用反馈，返回原始（但标记为延迟模式）
            return feedback, {
                'was_delayed': False,
                'delay_steps': 0,
                'buffered_for_step': step + delay,
            }
    
    def _randomize_magnitude(
        self,
        feedback: float,
        context: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        反馈幅度随机化
        
        使反馈的量级变得不可预测
        """
        noise_scale = self.config.magnitude_noise
        
        if self.config.magnitude_distribution == "lognormal":
            # 对数正态分布：保持符号，产生乘性噪声
            log_noise = np.random.lognormal(mean=0, sigma=noise_scale)
            new_feedback = feedback * log_noise
            scale_factor = log_noise
        elif self.config.magnitude_distribution == "normal":
            # 正态分布：加性噪声
            noise = np.random.normal(0, abs(feedback) * noise_scale + 0.1)
            new_feedback = feedback + noise
            scale_factor = noise / (feedback + 1e-10)
        else:
            # 均匀分布
            noise = np.random.uniform(-noise_scale, noise_scale)
            new_feedback = feedback * (1 + noise)
            scale_factor = 1 + noise
        
        return new_feedback, {
            'was_randomized': True,
            'scale_factor': scale_factor,
            'original_magnitude': abs(feedback),
            'new_magnitude': abs(new_feedback),
        }
    
    def _apply_sign_flip(
        self,
        feedback: float,
        context: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        反馈符号翻转
        
        以一定概率翻转反馈的符号
        如果启用条件翻转，高奖励时更可能翻转
        """
        flip_prob = self.config.sign_flip_prob
        
        # 条件翻转：高奖励时增加翻转概率
        if self.config.conditional_flip and abs(feedback) > 0.5:
            # 高奖励时，翻转概率增加
            bonus = min(0.3, abs(feedback) * 0.2)
            flip_prob += bonus
        
        was_flipped = np.random.random() < flip_prob
        
        if was_flipped:
            return -feedback, {
                'was_flipped': True,
                'flip_probability': flip_prob,
                'conditional_bonus': self.config.conditional_flip,
            }
        else:
            return feedback, {
                'was_flipped': False,
                'flip_probability': flip_prob,
            }
    
    def get_prediction_chaos_level(self) -> float:
        """
        获取预测混乱程度
        
        返回: 0.0 (可预测) 到 1.0 (完全不可预测)
        """
        if self.total_processed == 0:
            return 0.0
        
        # 破坏率
        break_rate = self.prediction_broken_count / self.total_processed
        
        # 延迟分布的熵
        if self.delay_buffer:
            delays = [e['available_step'] - e['original_step'] for e in self.delay_buffer]
            delay_variance = np.var(delays) if delays else 0
        else:
            delay_variance = ((self.config.delay_max - self.config.delay_min) / 2) ** 2
        
        # 综合预测混乱度
        chaos = 0.4 * break_rate + 0.3 * min(1.0, delay_variance / 100) + 0.3 * self.config.sign_flip_prob
        
        return min(1.0, chaos)
    
    def reset(self):
        """重置L2层状态"""
        self.delay_buffer.clear()
        self.current_step = 0
        self.history.clear()
        self.prediction_broken_count = 0
        self.total_processed = 0
    
    def __repr__(self) -> str:
        return (
            f"L2CausalPredictionLayer("
            f"enabled={self.config.enabled}, "
            f"delay=[{self.config.delay_min},{self.config.delay_max}], "
            f"flip_prob={self.config.sign_flip_prob})"
        )
