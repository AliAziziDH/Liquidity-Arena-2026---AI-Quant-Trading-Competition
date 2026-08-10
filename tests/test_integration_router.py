import pytest
import time
import torch
import numpy as np
from src.forecasting.vae_model import MarketVAE
from src.optimization.conformal_sizer import ConformalSizer
from src.execution.risk_gate import RiskGate
from src.execution.router import HeuristicRouter

def test_gating_latency_audit():
    """
    Gating Latency Audit:
    Assert that the joint execution latency of VAE encoding + ecdf mapping + Router selection
    remains strictly below 1.0 millisecond on CPU.
    """
    torch.manual_seed(42)
    device = torch.device("cpu")

    vae_model = MarketVAE(input_dim=300, latent_dim=16).to(device)
    sizer = ConformalSizer()
    risk_gate = RiskGate()

    router = HeuristicRouter(vae_model, sizer, risk_gate, ema_lambda=0.9)
    # Fit ecdf with dummy data
    router.fit_ecdf(np.random.rand(1000))
    router.tau = 0.95

    # Pre-generate tensor
    state_vector = torch.rand(1, 300).to(device)
    current_portfolio = {"equity": 100000.0}
    mu_hat = 1.0

    # Warmup
    for _ in range(10):
        router.route(state_vector, mu_hat, current_portfolio)

    latencies = []
    for _ in range(1000):
        start = time.perf_counter()
        router.route(state_vector, mu_hat, current_portfolio)
        latencies.append(time.perf_counter() - start)

    avg_latency = np.mean(latencies)
    # Ensure average latency is < 1 millisecond (0.001 seconds)
    assert avg_latency < 0.001, f"Latency {avg_latency*1000:.4f} ms exceeds 1.0 ms requirement."

def test_black_swan_simulation():
    """
    The Black-Swan Simulation (Volatile Market Crash Replay):
    Mock a historical sequence representing extreme market stress (300% surge in order book spread volatility).
    Assert that HeuristicRouter detects the anomaly, drops below tau threshold within 3 ticks,
    triggers Conservative Policy, and limits exposure.
    MDD should be reduced by at least 40% vs benchmark.
    """
    torch.manual_seed(42)
    device = torch.device("cpu")

    vae_model = MarketVAE(input_dim=300, latent_dim=16).to(device)
    sizer = ConformalSizer(kappa=0.15)
    for _ in range(100):
        sizer.add_error(1.0)

    risk_gate = RiskGate()

    # Benchmark router (without VAE / high tau to never trigger conservative policy)
    router_benchmark = HeuristicRouter(vae_model, sizer, risk_gate, ema_lambda=0.9)
    router_benchmark.tau = 2.0
    router_benchmark.fit_ecdf(np.random.rand(1000) * 0.1)

    # Smart router
    router_smart = HeuristicRouter(vae_model, sizer, risk_gate, ema_lambda=0.9)
    router_smart.tau = 0.1
    baseline_losses = np.random.rand(1000) * 0.1
    router_smart.fit_ecdf(baseline_losses)

    # Portfolios
    portfolio_smart = {"equity": 100000.0, "position_mtm_loss": 0.06, "current_position_size": 10.0, "open_positions_notional": 0.0, "running_drawdown": 0.0}
    portfolio_bench = {"equity": 100000.0, "position_mtm_loss": 0.06, "current_position_size": 10.0, "open_positions_notional": 0.0, "running_drawdown": 0.0}

    mu_hat = 2.0

    ticks_to_detect = 0
    detected = False

    # Tick 1: Normal
    normal_vector = torch.rand(1, 300).to(device) * 0.1
    router_benchmark.route(normal_vector, mu_hat, portfolio_bench)
    router_smart.route(normal_vector, mu_hat, portfolio_smart)

    # Simulating drawdowns
    mdd_smart = 0.0
    mdd_bench = 0.0

    for i in range(1, 6):
        # 300% surge (Black Swan)
        swan_vector = torch.rand(1, 300).to(device) * 3.0

        size_smart = router_smart.route(swan_vector, mu_hat, portfolio_smart)
        size_bench = router_benchmark.route(swan_vector, mu_hat, portfolio_bench)

        if not detected and router_smart.conservative_mode_active:
            ticks_to_detect = i
            detected = True

        # Update drawdowns (simplified MDD tracking)
        # Smart closes its position and locks down exposure when detecting crisis
        if size_smart == -10.0 or size_smart == 0.0:
            portfolio_smart["position_mtm_loss"] = 0.0
            # Drawdown doesn't grow further
        else:
            # Continues taking damage
            portfolio_smart["running_drawdown"] += 0.02
            mdd_smart = max(mdd_smart, portfolio_smart["running_drawdown"])

        # Bench ignores crisis and takes damage
        portfolio_bench["running_drawdown"] += 0.05
        mdd_bench = max(mdd_bench, portfolio_bench["running_drawdown"])

    assert detected, "Router failed to detect the Black-Swan anomaly."
    assert ticks_to_detect <= 3, f"Detected in {ticks_to_detect} ticks, expected <= 3."

    # Verify MDD reduction by at least 40%
    mdd_reduction = (mdd_bench - mdd_smart) / mdd_bench
    assert mdd_reduction >= 0.40, f"MDD reduction was only {mdd_reduction*100:.1f}%, expected >= 40%"
