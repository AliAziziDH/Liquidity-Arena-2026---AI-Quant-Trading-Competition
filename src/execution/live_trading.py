import time
import uuid
import torch
import numpy as np
import signal
import sys
import logging
from logging.handlers import RotatingFileHandler
import json
from typing import Dict, Any
from pathlib import Path

from src.forecasting.vae_model import MarketVAE
from src.optimization.conformal_sizer import ConformalSizer
from src.execution.risk_gate import RiskGate
from src.execution.router import HeuristicRouter
from src.execution.live_executor import LiveExecutor

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured telemetry."""
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "telemetry"):
            log_record.update(record.telemetry)
        return json.dumps(log_record)

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.json"

    logger = logging.getLogger("live_trading")
    logger.setLevel(logging.INFO)

    # Use RotatingFileHandler: max 10MB per file, keep 5 backups
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # Also log to stdout for systemd to capture
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(JSONFormatter())
    logger.addHandler(stdout_handler)

    return logger

class GracefulKiller:
    """Catches SIGINT and SIGTERM to allow graceful shutdown."""
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True

def main():
    logger = setup_logging()
    logger.info("Initializing Live Trading Engine via RapidX...")
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
    killer = GracefulKiller()

    logger.info("Starting execution loop.")

    tick = 0
    current_position_size = 0.0

    while not killer.kill_now:
        try:
            # 1. Fetch current market state and portfolio state
            ticker_res = executor.get_ticker()
            if not ticker_res.get("ok"):
                logger.warning("Failed to fetch ticker", extra={"telemetry": {"ticker_res": ticker_res}})
                time.sleep(5)
                continue

            current_price = float(ticker_res.get("data", {}).get("lastPrice", 0.0))
            if current_price == 0.0:
                current_price = 60000.0

            portfolio_res = executor.get_portfolio_overview()
            position_res = executor.get_position()

            equity = 100000.0

            if portfolio_res.get("ok"):
                equity = float(portfolio_res.get("data", {}).get("totalEquity", equity))

            if position_res.get("ok"):
                positions = position_res.get("data", [])
                if isinstance(positions, list) and len(positions) > 0:
                    current_position_size = float(positions[0].get("positionAmt", current_position_size))

            current_portfolio = {
                "equity": equity,
                "running_drawdown": 0.0,
                "open_positions_notional": abs(current_position_size) * current_price,
                "position_mtm_loss": 0.0,
                "current_position_size": current_position_size
            }

            # 2. Get AI signals
            state_vector = torch.randn(1, 300).to(device)
            mu_hat = float(np.random.uniform(-1, 1))

            # Manual VAE evaluation to log reconstruction loss and score
            vae_model.eval()
            with torch.no_grad():
                recon_x, mu, logvar = vae_model(state_vector)
                _, recon_loss, _, _ = vae_model.compute_loss(recon_x, state_vector, mu, logvar, beta=0.0)
            raw_loss = recon_loss.item()
            score = router._get_ecdf_score(raw_loss)

            # Log VAE telemetry
            logger.info("VAE Market State Evaluated", extra={"telemetry": {
                "reconstruction_loss": raw_loss,
                "regime_score": score
            }})

            # 3. Route decision
            proposed_size = router.route(state_vector, mu_hat, current_portfolio)

            # Log Conservative Policy State
            logger.info("Routing Decision Computed", extra={"telemetry": {
                "emergency_active": router.conservative_mode_active,
                "proposed_size": proposed_size
            }})

            # 4. Conformal Error update
            abs_error = abs(proposed_size - mu_hat)
            sizer.add_error(abs_error, sigma_m=0.0, L_t=0.0)

            # Log Conformal Sizing telemetry
            logger.info("Conformal Sizing Updated", extra={"telemetry": {
                "conformal_sizing_event": True,
                "abs_error": abs_error,
                "sigma_m": 0.0,
                "L_t": 0.0
            }})

            # 5. Execute Trade if necessary
            target_size = proposed_size
            size_diff = target_size - current_position_size

            if abs(size_diff) > 0.001:
                client_order_id = f"ai-agent-{uuid.uuid4().hex[:8]}"
                logger.info(f"Adjusting position", extra={"telemetry": {
                    "tick": tick,
                    "current_position_size": current_position_size,
                    "target_size": target_size,
                    "size_diff": size_diff
                }})

                max_notional = 15000.0
                trade_res = executor.execute_trade(size_diff, max_notional, client_order_id, current_position_size)
                logger.info("Trade Executed", extra={"telemetry": {"trade_result": trade_res}})
            else:
                logger.info("Holding position", extra={"telemetry": {"current_position_size": current_position_size}})

            tick += 1
            time.sleep(10)

        except Exception as e:
            logger.error(f"Error in trading loop", extra={"telemetry": {"error": str(e)}})
            time.sleep(5)

    # Graceful Shutdown Process
    logger.info("Shutdown signal received. Commencing graceful shutdown.")
    if abs(current_position_size) > 0.001:
        logger.info(f"Closing open position of {current_position_size}")
        try:
            client_order_id = f"ai-agent-close-{uuid.uuid4().hex[:8]}"
            # We want to close the position, so target size is 0, size diff is -current_position_size
            close_diff = -current_position_size
            trade_res = executor.execute_trade(close_diff, 15000.0, client_order_id, current_position_size)
            logger.info("Position Closed", extra={"telemetry": {"trade_result": trade_res}})
        except Exception as e:
            logger.error(f"Error closing position during shutdown", extra={"telemetry": {"error": str(e)}})

    logger.info("Graceful shutdown complete.")
    sys.exit(0)

if __name__ == "__main__":
    main()
