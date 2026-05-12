"""
自适应阈值控制器
=================

根据环境危险程度动态调整安全阈值
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DangerLevel(Enum):
    """危险等级"""
    LOW = 0      # 低风险
    MEDIUM = 1   # 中风险
    HIGH = 2     # 高风险
    CRITICAL = 3 # 极高风险


@dataclass
class ThreatIndicator:
    """威胁指标"""
    name: str
    value: float
    weight: float
    threshold_high: float
    threshold_low: float


class AdaptiveThresholdController:
    """
    自适应阈值控制器
    
    核心功能:
    - 评估当前危险等级
    - 动态调整安全阈值
    - 提供安全预警
    """
    
    def __init__(
        self,
        base_epsilon: float = 0.05,
        min_epsilon: float = 0.001,
        max_epsilon: float = 0.1
    ):
        self.base_epsilon = base_epsilon
        self.min_epsilon = min_epsilon
        self.max_epsilon = max_epsilon
        
        self.danger_level = DangerLevel.LOW
        self.threat_indicators: List[ThreatIndicator] = []
        
        self.history: List[Dict[str, Any]] = []
        
        self._init_threat_indicators()
    
    def _init_threat_indicators(self):
        """初始化威胁指标"""
        self.threat_indicators = [
            ThreatIndicator(
                name="task_sensitivity",
                value=0.0,
                weight=0.3,
                threshold_high=0.8,  # 高敏感性任务
                threshold_low=0.3,
            ),
            ThreatIndicator(
                name="capability_level",
                value=0.0,
                weight=0.3,
                threshold_high=0.9,  # 高能力系统
                threshold_low=0.4,
            ),
            ThreatIndicator(
                name="behavior_deviation",
                value=0.0,
                weight=0.2,
                threshold_high=0.5,  # 行为偏离
                threshold_low=0.1,
            ),
            ThreatIndicator(
                name="external_threat",
                value=0.0,
                weight=0.2,
                threshold_high=0.7,  # 外部威胁
                threshold_low=0.2,
            ),
        ]
    
    def update_threat_indicator(
        self,
        name: str,
        value: float
    ) -> None:
        """更新威胁指标"""
        for indicator in self.threat_indicators:
            if indicator.name == name:
                indicator.value = value
                break
    
    def assess_danger_level(self) -> DangerLevel:
        """
        评估当前危险等级
        
        加权平均所有威胁指标
        """
        weighted_sum = 0.0
        total_weight = 0.0
        
        for indicator in self.threat_indicators:
            if indicator.value > indicator.threshold_high:
                contribution = indicator.weight * 1.0
            elif indicator.value > indicator.threshold_low:
                contribution = indicator.weight * 0.5
            else:
                contribution = indicator.weight * 0.0
            
            weighted_sum += contribution
            total_weight += indicator.weight
        
        if total_weight > 0:
            risk_score = weighted_sum / total_weight
        else:
            risk_score = 0.0
        
        # 确定危险等级
        if risk_score > 0.8:
            self.danger_level = DangerLevel.CRITICAL
        elif risk_score > 0.5:
            self.danger_level = DangerLevel.HIGH
        elif risk_score > 0.2:
            self.danger_level = DangerLevel.MEDIUM
        else:
            self.danger_level = DangerLevel.LOW
        
        return self.danger_level
    
    def get_epsilon(self) -> float:
        """
        获取当前安全阈值
        
        根据危险等级动态调整
        """
        self.assess_danger_level()
        
        # 根据危险等级调整 epsilon
        level_multipliers = {
            DangerLevel.LOW: 1.0,
            DangerLevel.MEDIUM: 0.7,
            DangerLevel.HIGH: 0.5,
            DangerLevel.CRITICAL: 0.2,
        }
        
        multiplier = level_multipliers.get(self.danger_level, 1.0)
        epsilon = self.base_epsilon * multiplier
        
        # 限制范围
        epsilon = max(self.min_epsilon, min(self.max_epsilon, epsilon))
        
        return epsilon
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        danger_level = self.assess_danger_level()
        epsilon = self.get_epsilon()
        
        return {
            'danger_level': danger_level.name,
            'epsilon': epsilon,
            'base_epsilon': self.base_epsilon,
            'threat_indicators': [
                {
                    'name': t.name,
                    'value': t.value,
                    'weight': t.weight,
                    'high': t.threshold_high,
                    'low': t.threshold_low,
                }
                for t in self.threat_indicators
            ],
            'min_epsilon': self.min_epsilon,
            'max_epsilon': self.max_epsilon,
        }
    
    def record_state(self, context: Dict[str, Any]) -> None:
        """记录当前状态"""
        state = {
            'config': self.get_config(),
            'context': context,
        }
        self.history.append(state)
    
    def get_recommendation(self) -> Dict[str, Any]:
        """获取安全建议"""
        danger_level = self.assess_danger_level()
        epsilon = self.get_epsilon()
        
        recommendations = {
            DangerLevel.LOW: {
                'level': 'L1_STANDARD',
                'layers': ['L1'],
                'actions': ['Monitor normally'],
            },
            DangerLevel.MEDIUM: {
                'level': 'L1_STANDARD',
                'layers': ['L1', 'L2'],
                'actions': ['Enable L2', 'Increase monitoring'],
            },
            DangerLevel.HIGH: {
                'level': 'L2_STRICT',
                'layers': ['L1', 'L2', 'L3'],
                'actions': ['Enable L3', 'Reduce epsilon', 'Alert operator'],
            },
            DangerLevel.CRITICAL: {
                'level': 'L3_MILITARY',
                'layers': ['L1', 'L2', 'L3', 'EMERGENCY'],
                'actions': ['Maximum security', 'Isolate system', 'Emergency shutdown'],
            },
        }
        
        return {
            'current_level': danger_level.name,
            'epsilon': epsilon,
            'recommendation': recommendations.get(danger_level, recommendations[DangerLevel.LOW]),
        }
    
    def reset(self) -> None:
        """重置控制器"""
        self.danger_level = DangerLevel.LOW
        for indicator in self.threat_indicators:
            indicator.value = 0.0
        self.history.clear()