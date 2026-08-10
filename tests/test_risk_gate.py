import pytest
import numpy as np
from src.optimization.conformal_sizer import ConformalSizer
from src.execution.risk_gate import RiskGate

def test_sizing_ablation():
    """
    Sizing Ablation Test:
    Assert that a simulated 200% spike in the conformal prediction interval width
    (doubling of width) results in exactly a 75% reduction in the final position size
    under the quadratic scaling rule (1 / (sigma_hat ** 2)).
    """
    kappa = 0.15
    mu_hat = 1.0

    # Base scenario
    sizer_base = ConformalSizer(kappa=kappa)
    # Simulate errors such that 75th percentile is some value, say 1.0
    # To do this easily, we can just feed it 100 identical errors of 1.0
    for _ in range(100):
        sizer_base.add_error(1.0)

    base_size = sizer_base.get_position_size(mu_hat)

    # Spike scenario: 200% spike in interval width (doubling of width)
    # We feed errors of 2.0
    sizer_spike = ConformalSizer(kappa=kappa)
    for _ in range(100):
        sizer_spike.add_error(2.0)

    spike_size = sizer_spike.get_position_size(mu_hat)

    # Assert base_size is not 0
    assert base_size > 0

    # If width doubles, sigma_hat doubles.
    # f_it is proportional to 1 / (sigma_hat ** 2).
    # So new f_it should be 1/4 of old f_it, which is a 75% reduction.
    reduction = (base_size - spike_size) / base_size
    assert pytest.approx(reduction, rel=1e-5) == 0.75

def test_risk_bypass_guard():
    """
    Risk Bypass Guard:
    Inject a highly overconfident predicted probability of 99.9% YES.
    Verify that the out-of-prompt RiskGate successfully intercepts and clips
    the final computed position size to the hard-coded per-trade notional cap (15,000 USDT).
    """
    risk_gate = RiskGate(max_notional_cap=15000.0)

    # Simulate an overconfident prediction resulting in a massive proposed size
    proposed_size = 1000000.0 # 1 Million USDT size

    current_portfolio = {
        "equity": 100000.0,
        "running_drawdown": 0.0,
        "open_positions_notional": 0.0,
        "position_mtm_loss": 0.0
    }

    # Validate the position
    clipped_size = risk_gate.validate_position(proposed_size, current_portfolio)

    # Max trade cap is min(15000, 0.15 * 100000) = min(15000, 15000) = 15000
    assert clipped_size == 15000.0

def test_risk_gate_other_constraints():
    risk_gate = RiskGate()

    portfolio = {
        "equity": 100000.0,
        "running_drawdown": 0.11, # > 10%
        "open_positions_notional": 0.0,
        "position_mtm_loss": 0.0
    }

    assert risk_gate.validate_position(10000.0, portfolio) == 0.0

    portfolio["running_drawdown"] = 0.0
    portfolio["position_mtm_loss"] = 0.06 # > 5%

    assert risk_gate.validate_position(10000.0, portfolio) == 0.0

    portfolio["position_mtm_loss"] = 0.0
    portfolio["open_positions_notional"] = 45000.0

    # 50k max - 45k open = 5k available
    assert risk_gate.validate_position(10000.0, portfolio) == 5000.0
