"""
指标模块
=========
提供因果可利用性量化和阈值控制功能
"""

import os
import sys
import importlib.util


def _load_metric_module(module_name: str, file_path: str):
    """动态加载指标模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    return None


# 动态加载模块
_metrics_dir = os.path.dirname(__file__)

_exploitability_spec = importlib.util.spec_from_file_location(
    "exploitability",
    os.path.join(_metrics_dir, "exploitability.py")
)
if _exploitability_spec and _exploitability_spec.loader:
    _exploitability_module = importlib.util.module_from_spec(_exploitability_spec)
    sys.modules['exploitability'] = _exploitability_module
    _exploitability_spec.loader.exec_module(_exploitability_module)
    CausalExploitabilityMetric = _exploitability_module.CausalExploitabilityMetric
else:
    CausalExploitabilityMetric = None

_threshold_spec = importlib.util.spec_from_file_location(
    "threshold_controller",
    os.path.join(_metrics_dir, "threshold_controller.py")
)
if _threshold_spec and _threshold_spec.loader:
    _threshold_module = importlib.util.module_from_spec(_threshold_spec)
    sys.modules['threshold_controller'] = _threshold_module
    _threshold_spec.loader.exec_module(_threshold_module)
    AdaptiveThresholdController = _threshold_module.AdaptiveThresholdController
else:
    AdaptiveThresholdController = None

__all__ = ['CausalExploitabilityMetric', 'AdaptiveThresholdController']