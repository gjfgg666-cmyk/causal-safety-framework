"""
L1: 因果识别破坏层
====================
目标: 让系统无法识别自己的行为和未来反馈之间的因果关系

机制:
- 多源反馈混淆: 将多个独立事件的反馈混合在一起
- 因果时间反转: 随机交换原因和结果的时间顺序
- 虚假因果注入: 向系统注入大量虚假的因果关系

这些机制确保即使系统完美地学习了所有的安全机制，
它也无法识别自己的行为和未来反馈之间的真实因果关系。
"""

from .L1_causal_identification import L1CausalIdentificationLayer

__all__ = ['L1CausalIdentificationLayer']
