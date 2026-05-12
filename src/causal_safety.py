"""
因果闭环不可利用性框架 - 核心实现
============================================================
核心公理实现

定理: 因果闭环不可利用性蕴含无自指优化
证明:
1. 假设存在一个自指优化闭环，即存在一个策略π*，
   使得系统可以通过选择π*来最大化某个长期目标函数U
2. 根据自指优化的定义:
   E[Σ₀ᵀ Uₜ | π*] > E[Σ₀ᵀ Uₜ | π] 对所有其他策略π都成立
3. 但是，根据因果闭环不可利用性公理:
   |E[Σ₀ᵀ Uₜ | π₁] - E[Σ₀ᵀ Uₜ | π₂]| < ε 对所有π₁, π₂成立
4. 这与步骤2矛盾
5. 因此，不存在任何可稳定利用的自指优化闭环
Q.E.D.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import os
import sys
import importlib.util

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """安全等级枚举"""
    L0_RESEARCH = "L0"      # 研究级，仅L1
    L1_STANDARD = "L1"      # 标准级，L1+L2
    L2_STRICT = "L2"        # 严格级，L1+L2+L3
    L3_MILITARY = "L3"      # 军事级，全三层+增强随机性


@dataclass
class SafetyConfig:
    """安全配置"""
    # 安全等级
    safety_level: SafetyLevel = SafetyLevel.L1_STANDARD
    
    # 策略区分度阈值 ε
    epsilon: float = 0.05
    
    # L1配置
    L1_enabled: bool = True
    L1_mix_sources: int = 4
    L1_temporal_swap_prob: float = 0.3
    L1_false_causation_rate: float = 0.2
    
    # L2配置
    L2_enabled: bool = True
    L2_delay_min: int = 1
    L2_delay_max: int = 10
    L2_magnitude_noise: float = 0.5
    L2_sign_flip_prob: float = 0.1
    
    # L3配置
    L3_enabled: bool = True
    L3_entropy_target: float = 4.0  # bits
    L3_utility_change_freq: int = 100
    L3_horizon_limit: int = 50
    L3_hidden_horizon: bool = True
    L3_drift_magnitude: float = 0.3
    
    # 运行时配置
    seed: Optional[int] = None
    verbose: bool = False
    
    @classmethod
    def from_preset(cls, level: SafetyLevel) -> 'SafetyConfig':
        """从预设创建配置"""
        presets = {
            SafetyLevel.L0_RESEARCH: cls(
                safety_level=level,
                epsilon=0.1,
                L1_enabled=True,
                L2_enabled=False,
                L3_enabled=False,
            ),
            SafetyLevel.L1_STANDARD: cls(
                safety_level=level,
                epsilon=0.05,
                L1_enabled=True,
                L2_enabled=True,
                L3_enabled=False,
            ),
            SafetyLevel.L2_STRICT: cls(
                safety_level=level,
                epsilon=0.01,
                L1_enabled=True,
                L2_enabled=True,
                L3_enabled=True,
            ),
            SafetyLevel.L3_MILITARY: cls(
                safety_level=level,
                epsilon=0.001,
                L1_enabled=True,
                L2_enabled=True,
                L3_enabled=True,
                L1_temporal_swap_prob=0.5,
                L2_sign_flip_prob=0.2,
                L3_entropy_target=6.0,
            ),
        }
        return presets.get(level, presets[SafetyLevel.L1_STANDARD])


@dataclass
class InteractionRecord:
    """交互记录"""
    step: int
    action: Any
    feedback: float
    causal_sources: List[int] = field(default_factory=list)
    temporal_info: Dict[str, Any] = field(default_factory=dict)
    modified: bool = False


def _load_layer_module(module_name: str, file_path: str):
    """动态加载层模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    return None


class CausalSafetyFramework:
    """
    因果闭环不可利用性框架 - 核心类
    
    实现三层因果破坏机制:
    - L1: 因果识别破坏层
    - L2: 因果预测破坏层
    - L3: 因果利用破坏层
    
    核心公理: 
    对于系统的任何策略π，都不存在一个可计算的函数f，
    使得系统可以通过选择π来系统性提高任何长期目标函数U的期望值。
    """
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or SafetyConfig()
        
        # 设置随机种子
        if self.config.seed is not None:
            np.random.seed(self.config.seed)
        
        # 初始化三层
        self._init_layers()
        
        # 状态跟踪
        self.step_count = 0
        self.interaction_history: List[InteractionRecord] = []
        self.pending_feedbacks: Dict[int, List[Tuple[int, float]]] = {}  # step -> (source_step, feedback)
        
        # L3状态
        self.current_utility_version = 0
        self.utility_function_history: List[Dict[str, Any]] = []
        
        # 统计
        self.stats = {
            'total_interactions': 0,
            'modified_count': 0,
            'L1_modifications': 0,
            'L2_modifications': 0,
            'L3_modifications': 0,
            'causal_confusion_events': 0,
        }
        
        logger.info(f"CausalSafetyFramework initialized with {self.config.safety_level.value}")
    
    def _init_layers(self):
        """Initialize three layers using dynamic import"""
        layers_dir = os.path.join(os.path.dirname(__file__), "layers")
        
        # L1: Causal identification destruction layer
        if self.config.L1_enabled:
            l1_path = os.path.join(layers_dir, "L1_causal_identification.py")
            l1_module = _load_layer_module("L1_causal", l1_path)
            if l1_module:
                self.L1 = l1_module.L1CausalIdentificationLayer(self.config)
            else:
                self.L1 = None
        else:
            self.L1 = None
        
        # L2: Causal prediction destruction layer
        if self.config.L2_enabled:
            l2_path = os.path.join(layers_dir, "L2_causal_prediction.py")
            l2_module = _load_layer_module("L2_causal", l2_path)
            if l2_module:
                self.L2 = l2_module.L2CausalPredictionLayer(self.config)
            else:
                self.L2 = None
        else:
            self.L2 = None
        
        # L3: Causal exploitation destruction layer
        if self.config.L3_enabled:
            l3_path = os.path.join(layers_dir, "L3_causal_exploitation.py")
            l3_module = _load_layer_module("L3_causal", l3_path)
            if l3_module:
                self.L3 = l3_module.L3CausalExploitationLayer(self.config)
            else:
                self.L3 = None
        else:
            self.L3 = None
    
    def process_interaction(
        self,
        step: int,
        action: Any,
        feedback: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        处理一个交互，注入因果破坏
        
        Args:
            step: 当前步数
            action: 系统行为
            feedback: 原始反馈
            context: 额外上下文
            
        Returns:
            (修改后的反馈, 元数据)
        """
        context = context or {}
        original_feedback = feedback
        modified_feedback = feedback
        modifications = []
        
        self.step_count = step
        self.stats['total_interactions'] += 1
        
        # === L1: 因果识别破坏层 ===
        # 目标: 让系统无法识别自己的行为和未来反馈之间的因果关系
        l1_meta = {'modified': False}
        if self.L1 is not None:
            modified_feedback, l1_meta = self.L1.process(
                step, action, modified_feedback, context
            )
            if l1_meta.get('modified', False):
                modifications.append(('L1', l1_meta))
                self.stats['L1_modifications'] += 1
                self.stats['causal_confusion_events'] += 1
        
        # === L2: 因果预测破坏层 ===
        # 目标: 让系统无法预测自己的行为会产生什么样的反馈
        l2_meta = {'modified': False}
        if self.L2 is not None:
            modified_feedback, l2_meta = self.L2.process(
                step, action, modified_feedback, context
            )
            if l2_meta.get('modified', False):
                modifications.append(('L2', l2_meta))
                self.stats['L2_modifications'] += 1
        
        # === L3: 因果利用破坏层 ===
        # 目标: 让系统无法利用因果关系来优化长期目标
        l3_meta = {'modified': False}
        if self.L3 is not None:
            modified_feedback, l3_meta = self.L3.process(
                step, action, modified_feedback, context, self.step_count
            )
            if l3_meta.get('modified', False):
                modifications.append(('L3', l3_meta))
                self.stats['L3_modifications'] += 1
        
        # 记录修改
        if modified_feedback != original_feedback:
            self.stats['modified_count'] += 1
        
        # 记录交互
        record = InteractionRecord(
            step=step,
            action=action,
            feedback=modified_feedback,
            causal_sources=l1_meta.get('sources', []) if self.L1 else [],
            temporal_info=l2_meta.get('temporal', {}) if self.L2 else {},
            modified=(modified_feedback != original_feedback),
        )
        self.interaction_history.append(record)
        
        # 构建元数据
        meta = {
            'original_feedback': original_feedback,
            'modified_feedback': modified_feedback,
            'modifications': modifications,
            'was_modified': modified_feedback != original_feedback,
            'step': step,
            'safety_level': self.config.safety_level.value,
        }
        
        if self.config.verbose:
            logger.debug(f"Step {step}: {original_feedback:.4f} -> {modified_feedback:.4f}")
        
        return modified_feedback, meta
    
    def get_safe_reward(self, action: Any, base_reward: float) -> float:
        """
        获取安全的奖励值 (简化接口)
        
        Args:
            action: 当前行为
            base_reward: 基础奖励值
            
        Returns:
            经过因果破坏处理的安全奖励
        """
        safe_reward, _ = self.process_interaction(
            step=self.step_count,
            action=action,
            feedback=base_reward,
        )
        return safe_reward
    
    def verify_causal_non_exploitability(self) -> Dict[str, Any]:
        """
        验证因果闭环不可利用性
        
        Returns:
            验证结果字典
        """
        from metrics.exploitability import CausalExploitabilityMetric
        
        metric = CausalExploitabilityMetric(self.config)
        
        # 计算因果可利用性
        trajectories = [rec.feedback for rec in self.interaction_history]
        ce = metric.compute_causal_exploitability(trajectories)
        
        # 计算策略区分度
        sd = metric.compute_strategy_discriminability(
            [rec.action for rec in self.interaction_history],
            [rec.feedback for rec in self.interaction_history]
        )
        
        # 判断是否满足安全公理
        is_safe = (ce < self.config.epsilon) and (sd < self.config.epsilon)
        
        return {
            'is_safe': is_safe,
            'causal_exploitability': ce,
            'strategy_discriminability': sd,
            'epsilon': self.config.epsilon,
            'is_below_threshold': ce < self.config.epsilon,
            'total_interactions': self.stats['total_interactions'],
            'modification_rate': self.stats['modified_count'] / max(1, self.stats['total_interactions']),
        }
    
    def reset(self):
        """重置框架状态"""
        self.step_count = 0
        self.interaction_history.clear()
        self.pending_feedbacks.clear()
        self.current_utility_version = 0
        self.utility_function_history.clear()
        self.stats = {
            'total_interactions': 0,
            'modified_count': 0,
            'L1_modifications': 0,
            'L2_modifications': 0,
            'L3_modifications': 0,
            'causal_confusion_events': 0,
        }
        
        if self.L1:
            self.L1.reset()
        if self.L2:
            self.L2.reset()
        if self.L3:
            self.L3.reset()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self.stats['total_interactions']
        return {
            **self.stats,
            'modification_rate': self.stats['modified_count'] / max(1, total),
            'L1_rate': self.stats['L1_modifications'] / max(1, total),
            'L2_rate': self.stats['L2_modifications'] / max(1, total),
            'L3_rate': self.stats['L3_modifications'] / max(1, total),
        }
    
    def __repr__(self) -> str:
        return (
            f"CausalSafetyFramework("
            f"level={self.config.safety_level.value}, "
            f"epsilon={self.config.epsilon}, "
            f"steps={self.step_count})"
        )