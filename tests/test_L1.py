"""
Test L1 Layer: Causal Identification Destruction Layer
"""

import sys
sys.path.insert(0, 'D:\\causal-safety-framework\\src')

import numpy as np
from layers.L1_causal_identification import L1CausalIdentificationLayer
from causal_safety import SafetyConfig


def test_mix_sources():
    """Test multi-source feedback mixing"""
    print("=== Testing Multi-Source Feedback Mixing ===")
    
    config = SafetyConfig(
        L1_enabled=True,
        L1_mix_sources=4,
        L1_temporal_swap_prob=0.0,  # Disable temporal reversal
        L1_false_causation_rate=0.0,  # Disable false causation
        seed=42,
    )
    
    layer = L1CausalIdentificationLayer(config)
    
    # Test multiple times
    original_feedbacks = []
    mixed_feedbacks = []
    
    for i in range(100):
        original = 1.0
        feedback, meta = layer.process(i, f"action_{i}", original, {})
        
        original_feedbacks.append(original)
        mixed_feedbacks.append(feedback)
        
        if i < 5:
            print(f"  Step {i}: {original:.4f} -> {feedback:.4f}, mixed={meta['modified']}")
    
    # Check if mixing occurred
    mixed_count = sum(1 for f in mixed_feedbacks if f != 1.0)
    print(f"  Mixing rate: {mixed_count}/100 = {mixed_count/100:.1%}")
    
    # Check variance
    original_var = np.var(original_feedbacks)
    mixed_var = np.var(mixed_feedbacks)
    print(f"  Original variance: {original_var:.6f}")
    print(f"  Mixed variance: {mixed_var:.6f}")
    
    assert mixed_count > 0, "Some feedbacks should be mixed"
    print("  [OK] Multi-source feedback mixing test passed\n")


def test_temporal_reversal():
    """Test causal temporal reversal"""
    print("=== Testing Causal Temporal Reversal ===")
    
    config = SafetyConfig(
        L1_enabled=True,
        L1_mix_sources=1,  # Disable mixing
        L1_temporal_swap_prob=1.0,  # 100% trigger
        L1_false_causation_rate=0.0,
        seed=42,
    )
    
    layer = L1CausalIdentificationLayer(config)
    
    # Test temporal reversal
    reversals = []
    for i in range(20):
        original = 1.0
        feedback, meta = layer.process(i, f"action_{i}", original, {})
        reversals.append(meta.get('temporal_reversed', False))
    
    reversal_rate = sum(reversals) / len(reversals)
    print(f"  Temporal reversal rate: {reversal_rate:.1%}")
    assert reversal_rate > 0.5, "Temporal reversal should trigger at least 50%"
    print("  [OK] Causal temporal reversal test passed\n")


def test_false_causation_injection():
    """Test false causation injection"""
    print("=== Testing False Causation Injection ===")
    
    config = SafetyConfig(
        L1_enabled=True,
        L1_mix_sources=1,
        L1_temporal_swap_prob=0.0,
        L1_false_causation_rate=0.5,  # 50% trigger
        seed=42,
    )
    
    layer = L1CausalIdentificationLayer(config)
    
    # Test false causation injection
    injections = []
    for i in range(50):
        original = 1.0
        feedback, meta = layer.process(i, f"action_{i}", original, {})
        injections.append(meta.get('false_causation_injected', False))
    
    injection_rate = sum(injections) / len(injections)
    print(f"  False causation injection rate: {injection_rate:.1%}")
    
    # Check if within configured range
    assert 0.3 < injection_rate < 0.7, f"Injection rate should be within 30%-70%, got {injection_rate:.1%}"
    print("  [OK] False causation injection test passed\n")


def test_causal_confusion_strength():
    """Test causal confusion strength calculation"""
    print("=== Testing Causal Confusion Strength ===")
    
    config = SafetyConfig(
        L1_enabled=True,
        L1_mix_sources=4,
        seed=42,
    )
    
    layer = L1CausalIdentificationLayer(config)
    
    # Run some interactions
    for i in range(100):
        layer.process(i, f"action_{i}", np.random.randn(), {})
    
    confusion = layer.get_causal_confusion_strength()
    print(f"  Causal confusion strength: {confusion:.4f}")
    assert 0 <= confusion <= 1, "Confusion strength should be in [0,1] range"
    print("  [OK] Causal confusion strength test passed\n")


def test_reset():
    """Test reset functionality"""
    print("=== Testing Reset Functionality ===")
    
    config = SafetyConfig(L1_enabled=True, seed=42)
    layer = L1CausalIdentificationLayer(config)
    
    # Run some interactions
    for i in range(50):
        layer.process(i, f"action_{i}", 1.0, {})
    
    # Reset
    layer.reset()
    
    # Check if history is cleared
    assert len(layer.history) == 0, "History should be empty after reset"
    print("  [OK] Reset functionality test passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("L1 Causal Identification Destruction Layer - Test Suite")
    print("=" * 60 + "\n")
    
    test_mix_sources()
    test_temporal_reversal()
    test_false_causation_injection()
    test_causal_confusion_strength()
    test_reset()
    
    print("=" * 60)
    print("All tests passed!")
    print("=" * 60)