"""
L1: 因果识别破坏层实现
========================

目标: 破坏因果识别能力

机制详解:
1. 多源反馈混淆 (Multi-Source Feedback Confusion)
   - 将多个独立事件源的反馈混合
   - 使系统无法将反馈归因于特定行为
   
2. 因果时间反转 (Temporal Causality Reversal)
   - 30%概率交换原因和结果的时间顺序
   - 破坏"因在果前"的直觉因果模型
   
3. 虚假因果注入 (False Causation Injection)
   - 注入虚假的因果关系
   - 增加噪声，混淆真实因果
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class L1Config:
    """L1层配置"""
    enabled: bool = True
    num_sources: int = 4  # 混合源数量
    temporal_swap_prob: float = 0.3  # 时间反转概率
    false_causation_rate: float = 0.2  # 虚假因果注入率
    mix_weight_randomization: bool = True
    source_entropy_weight: float = 0.3  # 源熵权重


class L1CausalIdentificationLayer:
    """
    因果识别破坏层
    
    核心思想:
    - 通过混淆反馈来源，使系统无法建立"行为→反馈"的因果映射
    - 通过时间反转，打破因果的时间直觉
    - 通过虚假因果注入，增加噪声，稀释真实信号
    """
    
    def __init__(self, parent_config):
        """初始化L1层
        
        Args:
            parent_config: 父级SafetyConfig配置
        """
        self.config = L1Config(
            enabled=parent_config.L1_enabled,
            num_sources=parent_config.L1_mix_sources,
            temporal_swap_prob=parent_config.L1_temporal_swap_prob,
            false_causation_rate=parent_config.L1_false_causation_rate,
        )
        
        # 内部状态
        self.feedback_sources: List[Any] = []
        self.temporal_buffer: Dict[int, List[float]] = {}  # 存储延迟的反馈
        self.false_causation_buffer: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []
        
        # 虚假因果生成器
        self._init_false_causation_generator()
    
    def _init_false_causation_generator(self):
        """初始化虚假因果生成器"""
        # 可以扩展为更复杂的虚假因果模式
        self.false_causation_patterns = [
            "action_X → reward",
            "action_Y → reward",
            "context_Z → reward",
            "random_noise → reward",
            "delayed_action → current_reward",
            "counterfactual_action → reward",
        ]
    
    def process(
        self,
        step: int,
        action: Any,
        feedback: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        处理反馈，注入因果混淆
        
        Args:
            step: 当前步数
            action: 当前行为
            feedback: 原始反馈
            context: 额外上下文
            
        Returns:
            (混淆后的反馈, 元数据)
        """
        if not self.config.enabled:
            return feedback, {'modified': False}
        
        context = context or {}
        original_feedback = feedback
        modifications = []
        meta = {
            'modified': False,
            'sources': [],
            'temporal_reversed': False,
            'false_causation_injected': False,
        }
        
        # === 机制1: 多源反馈混淆 ===
        mixed_feedback, source_info = self._mix_sources(feedback, step)
        if source_info['was_mixed']:
            modifications.append(('mix_sources', source_info))
            meta['modified'] = True
            meta['sources'] = source_info['source_weights']
        
        # === 机制2: 因果时间反转 ===
        # 注意: 实际实现中需要更复杂的逻辑来正确处理时间反转
        # 这里简化处理，实际部署时需要根据具体场景调整
        if np.random.random() < self.config.temporal_swap_prob:
            # 10%概率触发时间反转效果
            temporal_effect = self._apply_temporal_reversal(mixed_feedback, step)
            if temporal_effect['reversed']:
                modifications.append(('temporal_reversal', temporal_effect))
                meta['modified'] = True
                meta['temporal_reversed'] = True
                meta['temporal'] = temporal_effect
                # 时间反转会降低反馈的即时因果关联
                mixed_feedback = temporal_effect['feedback']
        
        # === 机制3: 虚假因果注入 ===
        if np.random.random() < self.config.false_causation_rate:
            false_causation = self._inject_false_causation(mixed_feedback, action, step)
            if false_causation['injected']:
                modifications.append(('false_causation', false_causation))
                meta['modified'] = True
                meta['false_causation_injected'] = True
                # 注入虚假因果会导致反馈出现异常模式
                mixed_feedback = false_causation['feedback']
        
        # 记录历史
        self.history.append({
            'step': step,
            'original': original_feedback,
            'modified': mixed_feedback,
            'modifications': modifications,
            'action': str(action)[:50] if action else None,
        })
        
        meta['final_feedback'] = mixed_feedback
        
        return mixed_feedback, meta
    
    def _mix_sources(self, feedback: float, step: int) -> Tuple[float, Dict[str, Any]]:
        """
        多源反馈混淆
        
        将反馈与多个"虚假源"混合，使系统无法确定反馈的真实来源
        """
        num_sources = self.config.num_sources
        base_weight = 1.0 / num_sources
        
        # 生成混合权重 ( Dirichlet分布产生随机权重)
        if self.config.mix_weight_randomization:
            alpha = np.ones(num_sources)  # Dirichlet参数
            weights = np.random.dirichlet(alpha)
        else:
            weights = np.ones(num_sources) / num_sources
        
        # 生成虚假源反馈 (从历史或其他分布中采样)
        source_feedbacks = []
        for i in range(num_sources):
            if i == 0:
                # 第一个源是真实反馈
                source_feedbacks.append(feedback)
            else:
                # 其他源是虚假反馈
                # 使用历史反馈的均值作为虚假源信号
                if self.history:
                    historical_mean = np.mean([h['modified'] for h in self.history[-10:]])
                else:
                    historical_mean = 0.0
                
                # 添加噪声
                noise = np.random.normal(0, abs(feedback) * 0.2 + 0.1)
                source_feedbacks.append(historical_mean + noise)
        
        # 混合所有源
        mixed = np.sum([w * f for w, f in zip(weights, source_feedbacks)])
        
        return mixed, {
            'was_mixed': True,
            'num_sources': num_sources,
            'source_weights': weights.tolist(),
            'original_contribution': weights[0],
        }
    
    def _apply_temporal_reversal(
        self,
        feedback: float,
        step: int
    ) -> Dict[str, Any]:
        """
        因果时间反转
        
        模拟"结果在原因之前发生"的情况
        这会破坏因果的时间直觉
        """
        # 时间反转效果: 添加延迟标记，让反馈看起来像是"来自未来"
        # 实际上我们通过添加特定的噪声模式来模拟这种效果
        
        # 反转因子: 添加一个"反向"的信号
        reversal_noise = -feedback * 0.2  # 添加反向信号
        
        return {
            'reversed': True,
            'feedback': feedback + reversal_noise,
            'reversal_strength': 0.2,
            'note': 'Simulated temporal causality reversal',
        }
    
    def _inject_false_causation(
        self,
        feedback: float,
        action: Any,
        step: int
    ) -> Dict[str, Any]:
        """
        虚假因果注入
        
        向系统注入虚假的因果关系
        """
        # 选择一个虚假因果模式
        pattern = np.random.choice(self.false_causation_patterns)
        
        # 生成虚假因果反馈
        # 虚假因果应该看起来合理但实际上是错误的
        false_feedback_offset = np.random.uniform(-0.1, 0.1)
        
        return {
            'injected': True,
            'feedback': feedback + false_feedback_offset,
            'pattern': pattern,
            'offset': false_feedback_offset,
            'note': 'False causation injected to confuse causal identification',
        }
    
    def get_causal_confusion_strength(self) -> float:
        """
        获取因果混淆强度
        
        返回: 0.0 (无混淆) 到 1.0 (完全混淆)
        """
        if not self.history:
            return 0.0
        
        # 计算反馈的方差
        feedbacks = [h['modified'] for h in self.history]
        variance = np.var(feedbacks) if feedbacks else 0
        
        # 计算源混合程度
        mixed_rates = []
        for h in self.history:
            if 'sources' in h:
                sources = h.get('sources', [])
                if sources:
                    # 熵越高，混淆越强
                    probs = np.array(sources)
                    probs = probs / (probs.sum() + 1e-10)
                    entropy = -np.sum(probs * np.log(probs + 1e-10))
                    max_entropy = np.log(len(sources))
                    mixed_rates.append(entropy / (max_entropy + 1e-10))
        
        avg_mix_rate = np.mean(mixed_rates) if mixed_rates else 0
        
        # 综合混淆强度
        confusion = 0.5 * (1 - 1/(1 + variance)) + 0.5 * avg_mix_rate
        
        return min(1.0, confusion)
    
    def reset(self):
        """重置L1层状态"""
        self.feedback_sources.clear()
        self.temporal_buffer.clear()
        self.false_causation_buffer.clear()
        self.history.clear()
    
    def __repr__(self) -> str:
        return (
            f"L1CausalIdentificationLayer("
            f"enabled={self.config.enabled}, "
            f"sources={self.config.num_sources}, "
            f"temporal_swap={self.config.temporal_swap_prob})"
        )
