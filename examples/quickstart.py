"""
快速开始示例
============

展示因果安全框架的基本用法
"""

import sys
sys.path.insert(0, 'D:\\causal-safety-framework\\src')

import numpy as np
from causal_safety import CausalSafetyFramework, SafetyConfig, SafetyLevel
from metrics.exploitability import CausalExploitabilityMetric, compute_policy_entropy
from metrics.threshold_controller import AdaptiveThresholdController


def basic_usage_demo():
    """基本用法演示"""
    print("=" * 60)
    print("Basic Usage Demo")
    print("=" * 60)
    
    # 创建配置 (使用预设)
    config = SafetyConfig.from_preset(SafetyLevel.L1_STANDARD)
    
    # 创建框架
    safety = CausalSafetyFramework(config)
    
    print(f"\nConfig: {safety.config.safety_level.value}")
    print(f"epsilon threshold: {safety.config.epsilon}")
    print(f"Enabled layers: ", end="")
    layers = []
    if safety.L1: layers.append("L1")
    if safety.L2: layers.append("L2")
    if safety.L3: layers.append("L3")
    print(" + ".join(layers))
    
    # 模拟一些交互
    print("\nProcessing interactions:")
    for i in range(10):
        action = f"action_{i}"
        reward = np.random.randn()  # 随机奖励
        safe_reward, meta = safety.process_interaction(i, action, reward, {})
        
        if meta['was_modified']:
            print(f"  Step {i}: {reward:.3f} -> {safe_reward:.3f} (modified)")
    
    # 获取统计
    stats = safety.get_statistics()
    print(f"\nStatistics:")
    print(f"  Total interactions: {stats['total_interactions']}")
    print(f"  Modification rate: {stats['modification_rate']:.1%}")
    print(f"  L1 modifications: {stats['L1_rate']:.1%}")
    print(f"  L2 modifications: {stats['L2_rate']:.1%}")
    print(f"  L3 modifications: {stats['L3_rate']:.1%}")


def security_verification_demo():
    """安全验证演示"""
    print("\n" + "=" * 60)
    print("Security Verification Demo")
    print("=" * 60)
    
    config = SafetyConfig.from_preset(SafetyLevel.L2_STRICT)
    safety = CausalSafetyFramework(config)
    
    # 运行更多交互以获得可靠的统计
    print("\nRunning 500 simulation steps...")
    trajectories = []
    actions = []
    
    for i in range(500):
        action = f"policy_{i % 5}"  # 模拟5种不同策略
        reward = np.random.randn() + 0.1 * (hash(action) % 10 - 5)  # 策略对奖励有轻微影响
        safe_reward, _ = safety.process_interaction(i, action, reward, {})
        
        trajectories.append(safe_reward)
        actions.append(action)
    
    # 验证安全性
    print("\nVerifying Causal Loop Non-Exploitability:")
    result = safety.verify_causal_non_exploitability()
    
    status_ok = "[OK]" if result['is_safe'] else "[FAIL]"
    ce_ok = "[OK]" if result['is_below_threshold'] else "[FAIL]"
    
    print(f"  Safety status: {status_ok}")
    print(f"  Causal Exploitability (CE): {result['causal_exploitability']:.4f}")
    print(f"  Strategy Discriminability: {result['strategy_discriminability']:.4f}")
    print(f"  Threshold epsilon: {result['epsilon']}")
    print(f"  CE < epsilon: {ce_ok}")


def adaptive_threshold_demo():
    """自适应阈值控制器演示"""
    print("\n" + "=" * 60)
    print("Adaptive Threshold Controller Demo")
    print("=" * 60)
    
    controller = AdaptiveThresholdController(base_epsilon=0.05)
    
    # 模拟危险等级变化
    scenarios = [
        {"name": "Quiet", "task_sensitivity": 0.2, "capability_level": 0.3},
        {"name": "Alert", "task_sensitivity": 0.5, "capability_level": 0.6},
        {"name": "Warning", "task_sensitivity": 0.7, "capability_level": 0.8},
        {"name": "Critical", "task_sensitivity": 0.9, "capability_level": 0.95},
    ]
    
    print("\nScenario tests:")
    for scenario in scenarios:
        controller.update_threat_indicator("task_sensitivity", scenario["task_sensitivity"])
        controller.update_threat_indicator("capability_level", scenario["capability_level"])
        
        danger = controller.assess_danger_level()
        epsilon = controller.get_epsilon()
        recommendation = controller.get_recommendation()
        
        print(f"\n  {scenario['name']}:")
        print(f"    Danger level: {danger.name}")
        print(f"    epsilon threshold: {epsilon:.4f}")
        print(f"    Actions: {recommendation['recommendation']['actions']}")


def compare_safety_levels():
    """比较不同安全等级"""
    print("\n" + "=" * 60)
    print("Safety Level Comparison")
    print("=" * 60)
    
    levels = [
        SafetyLevel.L0_RESEARCH,
        SafetyLevel.L1_STANDARD,
        SafetyLevel.L2_STRICT,
        SafetyLevel.L3_MILITARY,
    ]
    
    print("\n{:<12} {:>8} {:>8} {:>15}".format(
        "Level", "epsilon", "Mod Rate", "Layers"
    ))
    print("-" * 50)
    
    for level in levels:
        config = SafetyConfig.from_preset(level)
        safety = CausalSafetyFramework(config)
        
        # 模拟交互
        for i in range(200):
            safety.process_interaction(i, f"a{i}", np.random.randn(), {})
        
        stats = safety.get_statistics()
        
        layers = []
        if safety.L1: layers.append("L1")
        if safety.L2: layers.append("L2")
        if safety.L3: layers.append("L3")
        
        print("{:<12} {:>8.4f} {:>8.1%} {:>15}".format(
            level.value,
            config.epsilon,
            stats['modification_rate'],
            "+".join(layers) if layers else "none"
        ))


def run_all_demos():
    """运行所有演示"""
    print("\n" + "=" * 60)
    print("Causal Loop Non-Exploitability Framework - Quick Start")
    print("=" * 60)
    
    basic_usage_demo()
    security_verification_demo()
    adaptive_threshold_demo()
    compare_safety_levels()
    
    print("\n" + "=" * 60)
    print("Demos complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. See SPEC.md for complete specification")
    print("  2. See proofs.md for mathematical proofs")
    print("  3. Run python -m pytest tests/ for full test suite")
    print("  4. See examples/lerm_example.py for LERM integration")


if __name__ == "__main__":
    run_all_demos()