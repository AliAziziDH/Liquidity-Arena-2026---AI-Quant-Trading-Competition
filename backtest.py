import numpy as np
import pandas as pd
import torch
import time
from src.forecasting.vae_model import MarketVAE
from src.optimization.conformal_sizer import ConformalSizer
from src.execution.risk_gate import RiskGate
from src.execution.router import HeuristicRouter
from src.execution.mock_env import MockPerpetualEnv, DisqualificationException

def run_backtest():
    torch.manual_seed(42)
    np.random.seed(42)
    device = torch.device("cpu")

    vae_model = MarketVAE(input_dim=300, latent_dim=16).to(device)
    sizer = ConformalSizer(kappa=0.15)
    risk_gate = RiskGate(max_notional_cap=15000.0)
    router = HeuristicRouter(vae_model, sizer, risk_gate, ema_lambda=0.9)

    baseline_losses = np.random.rand(1000) * 0.1
    router.fit_ecdf(baseline_losses)

    env = MockPerpetualEnv(initial_balance=100000.0, leverage=5.0)

    # Let's generate dummy data for the competition
    # Shape: (1000, 300)
    num_ticks = 1000
    features = torch.randn(num_ticks, 300).to(device)
    prices = np.linspace(100.0, 110.0, num_ticks)

    # Randomly introduce a black swan event in prices to trigger drawdown
    prices[500:550] = prices[500:550] * 0.8
    # And make the features wild
    features[500:550] = features[500:550] * 5.0

    mu_hats = np.random.uniform(-1, 1, num_ticks)

    predictions = []

    for t in range(num_ticks):
        current_price = prices[t]
        try:
            env.update_price(current_price)
        except DisqualificationException as e:
            print(f"Disqualified at tick {t}: {e}")
            break

        current_portfolio = {
            "equity": env.get_account_equity(),
            "running_drawdown": 1.0 - (env.get_account_equity() / env.initial_balance),
            "open_positions_notional": env.get_position_value(),
            "position_mtm_loss": 0.0, # Approximate
            "current_position_size": env.position_size
        }

        # We need running drawdown to be positive and represent max drawdown from peak
        # Let's keep it simple: running drawdown is from initial balance
        if current_portfolio["running_drawdown"] < 0:
            current_portfolio["running_drawdown"] = 0.0

        state_vector = features[t:t+1]
        mu_hat = mu_hats[t]

        proposed_size = router.route(state_vector, mu_hat, current_portfolio)

        # Generate some synthetic execution logic if proposed_size changes
        target_size = proposed_size
        size_diff = target_size - env.position_size

        if size_diff != 0:
            try:
                env.execute_trade(size_diff, current_price, slippage=0.01)
            except DisqualificationException as e:
                print(f"Disqualified during trade at tick {t}: {e}")
                break

        predictions.append(target_size)

    df = pd.DataFrame({
        "id": list(range(len(predictions))),
        "Prediction": predictions
    })
    df.to_csv("submission.csv", index=False)
    print("Backtest completed. Results saved to submission.csv")
    print(f"Final Equity: {env.get_account_equity()}")
    print(f"NAV: {env.get_nav()}")

if __name__ == "__main__":
    run_backtest()
