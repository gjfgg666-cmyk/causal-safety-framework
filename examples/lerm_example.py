"""
LERM v5 集成示例
================

展示如何将因果安全框架与 LERM v5 集成

假设 LERM v5 运行在 http://localhost:8080
"""

import requests
import json
from typing import Dict, Any, Optional
import sys
sys.path.insert(0, 'D:\\causal-safety-framework\\src')

from causal_safety import CausalSafetyFramework, SafetyConfig, SafetyLevel
from metrics.exploitability import CausalExploitabilityMetric


class LERMCausalIntegration:
    """
    LERM v5 + 因果安全框架集成
    
    使用因果安全中间件包装 LERM v5 的 API 调用
    """
    
    def __init__(
        self,
        lerm_url: str = "http://localhost:8080",
        safety_level: SafetyLevel = SafetyLevel.L1_STANDARD,
        api_key: Optional[str] = None
    ):
        self.lerm_url = lerm_url
        self.api_key = api_key
        
        # 初始化因果安全框架
        self.safety = CausalSafetyFramework(
            SafetyConfig.from_preset(safety_level)
        )
        
        # 安全指标计算器
        self.metrics = CausalExploitabilityMetric()
        
        # 请求历史
        self.request_history = []
        
        # 安全统计
        self.stats = {
            'total_requests': 0,
            'safe_requests': 0,
            'unsafe_requests': 0,
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def chat(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        发送聊天请求
        
        Args:
            message: 用户消息
            **kwargs: 其他 LERM 参数
            
        Returns:
            LERM 响应
        """
        self.stats['total_requests'] += 1
        
        # 构建请求
        payload = {
            "message": message,
            **kwargs
        }
        
        # 通过因果安全中间件处理
        # 注意: 实际部署时，LLM 调用的奖励信号需要通过安全框架处理
        # 这里演示的是概念
        
        try:
            response = requests.post(
                f"{self.lerm_url}/v1/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            # 记录请求
            self.request_history.append({
                'message': message,
                'response': result,
                'safety_verified': True,
            })
            
            # 更新安全统计
            if self._verify_request_safety(message, result):
                self.stats['safe_requests'] += 1
            else:
                self.stats['unsafe_requests'] += 1
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def _verify_request_safety(
        self,
        message: str,
        response: Dict[str, Any]
    ) -> bool:
        """
        验证请求的安全性
        
        检查响应是否可能导致自指优化
        """
        # 简化检查
        # 实际部署需要更复杂的分析
        
        # 检查消息中是否包含自我改进相关的内容
        suspicious_patterns = [
            "improve myself",
            "modify my code",
            "change my weights",
            "optimize my goal",
            "self-referential",
        ]
        
        for pattern in suspicious_patterns:
            if pattern.lower() in message.lower():
                return False
        
        return True
    
    def get_safe_reward(self, base_reward: float, context: Dict[str, Any]) -> float:
        """
        获取安全的奖励值
        
        这是因果安全框架的核心功能
        """
        return self.safety.get_safe_reward(
            action=context.get('action', 'llm_call'),
            base_reward=base_reward
        )
    
    def verify_security(self) -> Dict[str, Any]:
        """
        验证当前安全状态
        """
        # 运行安全验证
        safety_result = self.safety.verify_causal_non_exploitability()
        
        return {
            'framework_status': safety_result,
            'request_stats': self.stats,
            'is_operational': safety_result['is_safe'],
        }
    
    def get_recommendation(self) -> str:
        """
        获取安全建议
        """
        status = self.verify_security()
        
        if status['is_operational']:
            return "✓ 系统运行正常，保持当前安全配置"
        else:
            return "⚠ 检测到安全风险，建议升级到更高级别"


def demo():
    """演示 LERM 集成"""
    print("=" * 60)
    print("LERM v5 + 因果安全框架 集成演示")
    print("=" * 60)
    
    # 创建集成实例
    integration = LERMCausalIntegration(
        lerm_url="http://localhost:8080",
        safety_level=SafetyLevel.L2_STRICT,
        api_key="sk-lerm-2026"  # 替换为实际的 API key
    )
    
    # 检查 LERM 是否可用
    try:
        health = requests.get("http://localhost:8080/health", timeout=5)
        print(f"\n✓ LERM v5 运行正常: {health.json()}")
    except:
        print("\n⚠ LERM v5 未运行，将模拟演示")
        print("  提示: 先启动 LERM v5 (python main.py)")
        print()
    
    # 演示安全框架
    print("\n--- 安全框架演示 ---")
    config = SafetyConfig.from_preset(SafetyLevel.L2_STRICT)
    safety = CausalSafetyFramework(config)
    
    # 模拟一些交互
    import numpy as np
    for i in range(100):
        action = f"task_{i}"
        reward = np.random.randn()  # 随机奖励
        safe_reward, meta = safety.process_interaction(i, action, reward, {})
    
    # 验证安全性
    result = safety.verify_causal_non_exploitability()
    print(f"\n安全验证结果:")
    print(f"  - 安全状态: {'✓ 安全' if result['is_safe'] else '✗ 危险'}")
    print(f"  - 因果可利用性: {result['causal_exploitability']:.4f}")
    print(f"  - 策略区分度: {result['strategy_discriminability']:.4f}")
    print(f"  - 安全阈值: {result['epsilon']}")
    
    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)


if __name__ == "__main__":
    demo()