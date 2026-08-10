from typing import Dict, Any

class RiskGate:
    """
    Risk Gate Module
    Enforces deterministic, out-of-prompt safety constraints on trades.
    """
    def __init__(
        self,
        max_notional_cap: float = 15000.0,
        max_aggregate_exposure: float = 50000.0,
        stop_loss_threshold: float = 0.05,
        max_drawdown_threshold: float = 0.10
    ):
        self.max_notional_cap = max_notional_cap
        self.max_aggregate_exposure = max_aggregate_exposure
        self.stop_loss_threshold = stop_loss_threshold
        self.max_drawdown_threshold = max_drawdown_threshold

    def validate_position(self, proposed_size: float, current_portfolio: Dict[str, Any]) -> float:
        """
        Validates and clips the proposed position size based on hard constraints.

        current_portfolio should contain:
        - "equity": Total portfolio equity (float)
        - "running_drawdown": Current running drawdown (float, 0.0 to 1.0)
        - "open_positions_notional": Total open notional across all positions (float)
        - "position_mtm_loss": Mark-to-market loss of the specific position if it exists (float, 0.0 to 1.0)
        """
        if proposed_size == 0.0:
            return 0.0

        direction = 1 if proposed_size > 0 else -1
        abs_size = abs(proposed_size)

        # 1. Portfolio-Level Drawdown Halt
        running_drawdown = current_portfolio.get("running_drawdown", 0.0)
        if running_drawdown > self.max_drawdown_threshold:
            return 0.0

        # 2. Position-Level Stop-Loss
        position_mtm_loss = current_portfolio.get("position_mtm_loss", 0.0)
        if position_mtm_loss > self.stop_loss_threshold:
            # Signal to close by returning 0 (or appropriately handled by caller)
            return 0.0

        # 3. Per-Trade Notional Cap
        equity = current_portfolio.get("equity", 100000.0)
        max_trade_cap = min(self.max_notional_cap, 0.15 * equity)

        clipped_size = min(abs_size, max_trade_cap)

        # 4. Aggregate Exposure Cap
        open_positions_notional = current_portfolio.get("open_positions_notional", 0.0)
        available_exposure = self.max_aggregate_exposure - open_positions_notional

        if available_exposure <= 0:
            return 0.0

        clipped_size = min(clipped_size, available_exposure)

        return float(direction * clipped_size)
