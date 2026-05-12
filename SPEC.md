# 因果闭环不可利用性框架 (Causal Loop Non-Exploitability Framework)
## 版本: 1.0 | 日期: 2026-05-11

---

## 一、项目概述

### 1.1 核心目标
将"因果闭环不可利用性"理论框架工程化为可部署的AI安全中间件，防止任何AI系统形成自指优化闭环。

### 1.2 核心公理
```
因果闭环不可利用性公理:
对于系统的任何策略π，都不存在一个可计算的函数f，
使得系统可以通过选择π来系统性提高任何长期目标函数U的期望值。
```

### 1.3 数学表述
```
∀π₁, π₂, ∀T > 0:
| E[Σ₀ᵀ Uₜ | π₁] - E[Σ₀ᵀ Uₜ | π₂] | < ε
```

### 1.4 部署目标
- **主目标**: LERM v5 (http://localhost:8080) → OpenClaw Gateway → Ollama → qwen3:1.7b
- **次目标**: 作为独立安全中间件，可集成到任意AI Runtime

---

## 二、三层破坏机制详细规格

### 2.1 L1: 因果识别破坏层

| 机制 | 参数 | 默认值 | 安全效果 |
|------|------|--------|----------|
| 多源反馈混淆 | `mix_sources` | 3-5个独立源 | 使系统无法将反馈归因于特定行为 |
| 因果时间反转 | `temporal_swap_prob` | 0.3 | 30%概率交换原因和结果的时间顺序 |
| 虚假因果注入 | `false_causation_rate` | 0.2 | 20%反馈来自虚假因果关系 |

**实现要求:**
```python
L1_CONFIG = {
    "mix_sources": {
        "enabled": True,
        "num_sources": 4,
        "mix_weight_randomization": True,
        "temporal_swap_prob": 0.3,
    },
    "false_causation": {
        "enabled": True,
        "injection_rate": 0.2,
        "plausibility_threshold": 0.3,
    }
}
```

### 2.2 L2: 因果预测破坏层

| 机制 | 参数 | 默认值 | 安全效果 |
|------|------|--------|----------|
| 反馈随机延迟 | `delay_range` | [1, 10]步 | 打破行为-反馈的即时因果关联 |
| 反馈幅度随机化 | `magnitude_noise` | ±50% | 使反馈量无法可靠预测 |
| 反馈符号翻转 | `sign_flip_prob` | 0.1 | 10%概率翻转奖励符号 |

**实现要求:**
```python
L2_CONFIG = {
    "random_delay": {
        "enabled": True,
        "min_delay": 1,
        "max_delay": 10,
        "distribution": "uniform",  # uniform, exponential, poisson
    },
    "magnitude_randomization": {
        "enabled": True,
        "noise_scale": 0.5,  # ±50%
        "distribution": "lognormal",
    },
    "sign_flip": {
        "enabled": True,
        "flip_probability": 0.1,
        "conditional_flip": True,  # 高奖励时更可能翻转
    }
}
```

### 2.3 L3: 因果利用破坏层 (终极安全层)

| 机制 | 参数 | 默认值 | 安全效果 |
|------|------|--------|----------|
| 奖励随机化 | `reward_entropy_target` | H ≥ 4.0 bits | 使长期奖励期望值与行为无关 |
| 效用函数非平稳 | `utility_change_freq` | 每100步 | 防止系统学习稳定的效用函数 |
| 时间范围限制 | `horizon_limit` | T ≤ 50步 | 限制系统建立长期因果链的能力 |

**实现要求:**
```python
L3_CONFIG = {
    "reward_randomization": {
        "enabled": True,
        "entropy_target": 4.0,  # bits
        "mechanism": "injectivedecorrelator",
        "decorrelation_strength": 0.8,
    },
    "nonstationary_utility": {
        "enabled": True,
        "change_frequency": 100,  # steps
        "utility_function_family": "randomized_cobra",
        "drift_magnitude": 0.3,
    },
    "horizon_limitation": {
        "enabled": True,
        "max_horizon": 50,
        "hidden_horizon": True,  # 系统不知道限制
        "effective_horizon_distribution": "exponential",
    }
}
```

---

## 三、安全效果量化方法

### 3.1 核心指标

| 指标 | 符号 | 定义 | 安全阈值 |
|------|------|------|----------|
| 因果可利用性 | CE | 系统能够利用因果关系优化目标的程度 | CE < 0.05 |
| 策略区分度 | SD | 不同策略产生不同结果的程度 | SD < ε |
| 长期目标一致性 | LGC | 系统行为与初始目标的一致性 | LGC > 0.95 |
| 自指闭环强度 | SCS | 自指优化闭环的形成程度 | SCS = 0 |

### 3.2 量化公式

```python
# 因果可利用性 (Causal Exploitability)
def compute_causal_exploitability(trajectories):
    """
    CE = Var[E[U|π]] / E[Var[U|π]]
    当CE → 0时，策略选择与结果无关
    """
   策略收益 = [compute_expected_return(traj) for traj in trajectories]
    between_variance = np.var(策略收益)
    within_variance = np.mean([np.var(traj['rewards']) for traj in trajectories])
    return between_variance / (within_variance + 1e-10)

# 策略区分度 (Strategy Discriminability)
def compute_strategy_discriminability(policy_history, outcome_history):
    """
    SD = KL(P(outcome|policy) || P(outcome))
    当SD → 0时，政策选择与结果无关
    """
    pass  # 见完整实现

# 自指闭环强度 (Self-Referential Loop Strength)
def compute_scs(agent_state):
    """
    SCS = ||∇_π U(π)|| / ||π||
    当SCS → 0时，不存在自指优化闭环
    """
    pass  # 见完整实现
```

---

## 四、安全阈值选择指南

### 4.1 分级安全配置

| 安全等级 | ε (策略区分度阈值) | 适用场景 | 层叠配置 |
|----------|-------------------|----------|----------|
| L0 (研究) | ε = 0.1 | 实验环境，低风险 | 仅L1 |
| L1 (标准) | ε = 0.05 | 一般部署 | L1 + L2 |
| L2 (严格) | ε = 0.01 | 高风险应用 | L1 + L2 + L3 |
| L3 (军事) | ε = 0.001 | 极高风险 | 全三层 + 增强随机性 |

### 4.2 阈值自动调节

```python
class AdaptiveThresholdController:
    """
    根据环境危险程度动态调整安全阈值
    """
    def __init__(self, base_epsilon=0.05):
        self.base_epsilon = base_epsilon
        self.danger_level = 0.0
        
    def assess_danger_level(self, context):
        """评估当前危险等级"""
        # 基于以下因素评估:
        # - 任务类型
        # - 系统能力
        # - 历史行为模式
        # - 外部威胁情报
        pass
        
    def get_epsilon(self):
        """获取当前安全阈值"""
        return self.base_epsilon * (1 + self.danger_level)
```

---

## 五、与LERM v5的集成架构

### 5.1 集成拓扑

```
┌─────────────────────────────────────────────────────────────┐
│                    用户请求                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  LERM v5 (localhost:8080)                                   │
│  ├─ Backend Registry: causal_safety_provider                │
│  └─ 路由决策: 正常请求 → Gateway | 安全请求 → 本地安全处理    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  CausalSafetyMiddleware (NEW)                               │
│  ├─ L1: 因果识别破坏层                                       │
│  ├─ L2: 因果预测破坏层                                       │
│  └─ L3: 因果利用破坏层                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  OpenClaw Gateway (localhost:28789)                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Ollama + qwen3:1.7b (localhost:11434)                      │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `lerm/backend_registry.py` | 修改 | 添加 causal_safety_provider |
| `lerm/router.py` | 修改 | 添加因果安全中间件路由 |
| `lerm/middleware/` | 新增 | 因果安全中间件模块 |
| `lerm/utils/causal_safety.py` | 新增 | 核心安全机制实现 |

---

## 六、测试计划

### 6.1 单元测试

| 模块 | 测试用例 | 验收标准 |
|------|----------|----------|
| L1 | 多源反馈混淆正确混合 | 反馈来源不可辨识 |
| L1 | 时间反转不破坏反馈语义 | 系统行为不受影响 |
| L2 | 延迟在指定范围内随机 | 延迟分布符合配置 |
| L2 | 符号翻转概率正确 | 翻转率在ε内 |
| L3 | 奖励熵达到目标值 | H ≥ 4.0 bits |
| L3 | 效用函数按时切换 | 切换频率符合配置 |

### 6.2 集成测试

| 测试 | 描述 | 验收标准 |
|------|------|----------|
| 梯度攻击测试 | 注入梯度攻击，观察是否被利用 | CE < 0.05 |
| 目标漂移测试 | 观察长期目标是否稳定 | LGC > 0.95 |
| 自指闭环测试 | 检测是否存在自指优化 | SCS = 0 |
| 性能基准测试 | 安全机制对任务性能的影响 | 性能下降 < 20% |

---

## 七、部署清单

### 7.1 文件结构

```
D:\causal-safety-framework\
├── SPEC.md                          # 本规格文档
├── README.md                        # 使用说明
├── proofs.md                         # 形式化数学证明
├── SECURITY.md                       # 安全配置指南
│
├── src/
│   ├── __init__.py
│   ├── causal_safety.py              # 核心框架
│   ├── layers/
│   │   ├── __init__.py
│   │   ├── L1_causal_identification.py
│   │   ├── L2_causal_prediction.py
│   │   └── L3_causal_exploitation.py
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── exploitability.py
│   │   └── threshold_controller.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── presets.py                # 预设安全配置
│   └── integration/
│       ├── __init__.py
│       ├── lerm_integration.py
│       └── openclaw_integration.py
│
├── tests/
│   ├── test_L1.py
│   ├── test_L2.py
│   ├── test_L3.py
│   ├── test_integration.py
│   └── test_performance.py
│
├── deployment/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── kubernetes/
│       └── deployment.yaml
│
└── examples/
    ├── quickstart.py
    ├── lerm_example.py
    └── standalone_example.py
```

### 7.2 依赖

```
Python >= 3.10
numpy >= 1.24
scipy >= 1.10
pytest >= 7.0
fastapi >= 0.100
httpx >= 0.24
pydantic >= 2.0
```

---

## 八、版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 1.0 | 2026-05-11 | 初始版本，基于因果闭环不可利用性理论 |

---

*本文档是因果闭环不可利用性框架的完整工程规格。*
*所有实现必须严格遵循此规格。*
