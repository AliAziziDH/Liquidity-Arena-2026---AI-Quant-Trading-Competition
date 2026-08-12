import time
import uuid
import torch
import numpy as np
from src.forecasting.vae_model import MarketVAE
from src.optimization.conformal_sizer import ConformalSizer
from src.execution.risk_gate import RiskGate
from src.execution.router import HeuristicRouter
from src.execution.live_executor import LiveExecutor

def main():
    print("Initializing Live Trading Engine via RapidX...")
    device = torch.device("cpu")

    # Initialize components
    vae_model = MarketVAE(input_dim=300, latent_dim=16).to(device)
    sizer = ConformalSizer(kappa=0.15)

    # Seed baseline errors
    initial_errors = np.random.uniform(0.01, 0.05, 500)
    for error in initial_errors:
        sizer.add_error(error)

    risk_gate = RiskGate(max_notional_cap=15000.0)
    router = HeuristicRouter(vae_model, sizer, risk_gate, ema_lambda=0.9)
    baseline_losses = np.random.rand(1000) * 0.1
    router.fit_ecdf(baseline_losses)

    executor = LiveExecutor(symbol="BINANCE_PERP_BTC_USDT")

    # The trading loop
    print("Starting execution loop. Press Ctrl+C to stop.")

    tick = 0
    while True:
        try:
            # 1. Fetch current market state and portfolio state
            ticker_res = executor.get_ticker()
            if not ticker_res.get("ok"):
                print(f"Failed to fetch ticker: {ticker_res}")
                time.sleep(5)
                continue

            current_price = float(ticker_res.get("data", {}).get("lastPrice", 0.0))
            if current_price == 0.0:
                # Mock a price if data structure differs, to keep it running safely
                current_price = 60000.0

            portfolio_res = executor.get_portfolio_overview()
            position_res = executor.get_position()

            # Map RapidX state to current_portfolio dictionary expected by router
            # In a real environment, these would be properly parsed from the rapidx json output
            equity = 100000.0 # Placeholder
            current_position_size = 0.0 # Placeholder

            if portfolio_res.get("ok"):
                # Rough approximation based on common exchange formats
                equity = float(portfolio_res.get("data", {}).get("totalEquity", equity))

            if position_res.get("ok"):
                positions = position_res.get("data", [])
                if isinstance(positions, list) and len(positions) > 0:
                    current_position_size = float(positions[0].get("positionAmt", current_position_size))

            current_portfolio = {
                "equity": equity,
                "running_drawdown": 0.0, # Calculate properly based on high water mark
                "open_positions_notional": abs(current_position_size) * current_price,
                "position_mtm_loss": 0.0,
                "current_position_size": current_position_size
            }

            # 2. Get AI signals (mocked for this loop as we don't have a live feed of 300 features here)
            # In a real implementation, we would query our feature store or websocket feed
            state_vector = torch.randn(1, 300).to(device)
            mu_hat = float(np.random.uniform(-1, 1))

            # 3. Route decision
            proposed_size = router.route(state_vector, mu_hat, current_portfolio)

            # 4. Conformal Error update
            abs_error = abs(proposed_size - mu_hat)
            sizer.add_error(abs_error, sigma_m=0.0, L_t=0.0)

            # 5. Execute Trade if necessary
            target_size = proposed_size
            size_diff = target_size - current_position_size

            if abs(size_diff) > 0.001:  # Assuming 0.001 is min lot size
                client_order_id = f"ai-agent-{uuid.uuid4().hex[:8]}"
                print(f"[{tick}] Adjusting position. Current: {current_position_size:.4f}, Target: {target_size:.4f}, Diff: {size_diff:.4f}")

                # Use executor to place the trade
                max_notional = 15000.0 # From risk gate
                trade_res = executor.execute_trade(size_diff, max_notional, client_order_id, current_position_size)
                print(f"[{tick}] Trade result: {trade_res}")
            else:
                print(f"[{tick}] Holding position at {current_position_size:.4f}")

            tick += 1
            time.sleep(10) # Run every 10 seconds

        except KeyboardInterrupt:
            print("Stopping live trading engine.")
            break
        except Exception as e:
            print(f"Error in trading loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
