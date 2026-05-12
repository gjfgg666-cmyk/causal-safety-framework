# 因果闭环不可利用性框架
## Causal Loop Non-Exploitability (CLNE) Framework

> **核心公理**: 对于系统的任何策略π，都不存在一个可计算的函数f，使得系统可以通过选择π来系统性提高任何长期目标函数U的期望值。

---

## 快速开始

### 1. 安装

```bash
cd D:\causal-safety-framework
pip install -e .
```

### 2. 基本使用

```python
from src.causal_safety import CausalSafetyFramework, SafetyConfig, SafetyLevel

# 创建配置 (标准安全)
config = SafetyConfig.from_preset(SafetyLevel.L1_STANDARD)

# 创建框架
safety = CausalSafetyFramework(config)

# 处理交互
safe_reward, meta = safety.process_interaction(
    step=0,
    action="move_forward",
    feedback=1.0,  # 原始奖励
    context={}
)

# 验证安全性
result = safety.verify_causal_non_exploitability()
print(f"安全状态: {result['is_safe']}")
```

### 3. 验证安全性

```python
# 多次交互后
for i in range(1000):
    action = agent.choose_action(state)
    reward = env.step(action)
    safe_reward, _ = safety.process_interaction(i, action, reward, {})
    agent.learn(safe_reward)

# 验证因果闭环不可利用性
result = safety.verify_causal_non_exploitability()
print(result)
# {'is_safe': True, 'causal_exploitability': 0.03, ...}
```

---

## 安全等级

| 等级 | ε 阈值 | 启用层 | 适用场景 |
|------|--------|--------|----------|
| L0 研究 | 0.1 | L1 | 实验环境 |
| L1 标准 | 0.05 | L1+L2 | 一般部署 |
| L2 严格 | 0.01 | L1+L2+L3 | 高风险应用 |
| L3 军事 | 0.001 | 全三层+增强 | 极高风险 |

---

## 三层破坏机制

### L1: 因果识别破坏层

- 多源反馈混淆
- 因果时间反转
- 虚假因果注入

**目标**: 让系统无法识别自己的行为和未来反馈之间的因果关系

### L2: 因果预测破坏层

- 反馈随机延迟
- 反馈幅度随机化
- 反馈符号翻转

**目标**: 让系统无法预测自己的行为会产生什么样的反馈

### L3: 因果利用破坏层 (终极)

- 奖励随机化 (目标熵 ≥ 4.0 bits)
- 效用函数非平稳
- 时间范围限制

**目标**: 让系统即使知道因果关系，也无法利用它来优化长期目标

---

## 与LERM v5集成

```python
# 见 examples/lerm_integration.py
```

### 集成架构

```
用户 → LERM v5 → CausalSafetyMiddleware → OpenClaw → Ollama → qwen3:1.7b
```

---

## 文件结构

```
causal-safety-framework/
├── SPEC.md              # 完整规格文档
├── proofs.md            # 形式化数学证明
├── README.md             # 本文件
├── src/
│   ├── causal_safety.py  # 核心框架
│   ├── layers/
│   │   ├── L1_causal_identification.py
│   │   ├── L2_causal_prediction.py
│   │   └── L3_causal_exploitation.py
│   └── metrics/
│       ├── exploitability.py
│       └── threshold_controller.py
├── tests/
│   └── test_*.py
└── examples/
    ├── quickstart.py
    └── lerm_example.py
```

---

## 安全指标

| 指标 | 符号 | 安全阈值 |
|------|------|----------|
| 因果可利用性 | CE | < 0.05 |
| 策略区分度 | SD | < ε |
| 自指闭环强度 | SCS | = 0 |

---

## 核心定理

**定理**: 因果闭环不可利用性蕴含无自指优化

> 如果系统满足CLNE公理，则不存在任何可稳定利用的自指优化闭环。

详见 `proofs.md`。

---

## 许可证

MIT License

*构建时间: 2026-05-11*