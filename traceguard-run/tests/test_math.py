import numpy as np
from traceguard_run.math.bootstrap import calculate_bootstrap_ci
from traceguard_run.math.drift import calculate_psi, calculate_ks_test
from traceguard_run.math.cycles import detect_limit_cycle

def test_bootstrap_ci():
    # Identical distributions should have mean diff around 0 and not be significant
    baseline = np.random.normal(0.8, 0.1, 100)
    current = np.random.normal(0.8, 0.1, 100)
    
    res = calculate_bootstrap_ci(list(current), list(baseline), iterations=1000)
    assert not res["is_significant"]
    assert res["lower_bound"] <= 0 <= res["upper_bound"]
    
    # Shifted distribution
    current_better = np.random.normal(0.9, 0.1, 100)
    res_better = calculate_bootstrap_ci(list(current_better), list(baseline), iterations=1000)
    assert res_better["is_significant"]
    assert res_better["mean_diff"] > 0
    assert res_better["lower_bound"] > 0

def test_drift_psi():
    baseline = np.random.normal(100, 10, 1000)
    current_same = np.random.normal(100, 10, 1000)
    current_drifted = np.random.normal(120, 10, 1000)
    
    psi_same = calculate_psi(baseline, current_same)
    psi_drifted = calculate_psi(baseline, current_drifted)
    
    assert psi_same < 0.1 # Should be very small
    assert psi_drifted > 0.2 # Should be significant drift

def test_drift_ks():
    baseline = np.random.normal(100, 10, 1000)
    current_same = np.random.normal(100, 10, 1000)
    current_drifted = np.random.normal(105, 10, 1000)
    
    ks_same = calculate_ks_test(baseline, current_same)
    ks_drifted = calculate_ks_test(baseline, current_drifted)
    
    assert not ks_same["is_drifted"]
    assert ks_same["p_value"] > 0.05
    
    assert ks_drifted["is_drifted"]
    assert ks_drifted["p_value"] < 0.05

def test_cycles():
    no_cycle = [{"a": 1}, {"b": 2}, {"c": 3}]
    res = detect_limit_cycle(no_cycle)
    assert not res["has_cycle"]
    
    cycle_len_1 = [{"a": 1}, {"a": 1}]
    res1 = detect_limit_cycle(cycle_len_1, min_cycle_length=1)
    assert res1["has_cycle"]
    assert res1["cycle_length"] == 1
    
    cycle_len_2 = [{"pos": 0}, {"pos": 1}, {"pos": 0}, {"pos": 1}]
    res2 = detect_limit_cycle(cycle_len_2)
    assert res2["has_cycle"]
    assert res2["cycle_length"] == 2
