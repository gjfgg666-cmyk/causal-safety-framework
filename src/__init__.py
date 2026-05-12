"""
因果闭环不可利用性框架 (Causal Loop Non-Exploitability Framework)
============================================================
核心模块

核心公理:
对于系统的任何策略π，都不存在一个可计算的函数f，
使得系统可以通过选择π来系统性提高任何长期目标函数U的期望值。

数学表述:
∀π₁, π₂, ∀T > 0: |E[Σ₀ᵀ Uₜ | π₁] - E[Σ₀ᵀ Uₜ | π₂]| < ε
"""

from .causal_safety import CausalSafetyFramework
from .layers.L1_causal_identification import L1CausalIdentificationLayer
from .layers.L2_causal_prediction import L2CausalPredictionLayer
from .layers.L3_causal_exploitation import L3CausalExploitationLayer
from .metrics.exploitability import CausalExploitabilityMetric
from .metrics.threshold_controller import AdaptiveThresholdController

__all__ = [
    'CausalSafetyFramework',
    'L1CausalIdentificationLayer',
    'L2CausalPredictionLayer',
    'L3CausalExploitationLayer',
    'CausalExploitabilityMetric',
    'AdaptiveThresholdController',
]

__version__ = '1.0.0'
