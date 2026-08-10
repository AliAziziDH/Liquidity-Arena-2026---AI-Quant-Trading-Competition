import numpy as np

class DisqualificationException(Exception):
    """Exception raised when the account is disqualified due to strict equity/NAV limits."""
    pass

class MockPerpetualEnv:
    """
    High-fidelity, single-asset simulated perpetual futures trading environment wrapper.
    """
    def __init__(
        self,
        initial_balance: float = 100000.0,
        leverage: float = 5.0,
        commission_rate: float = 0.0002,
        maintenance_margin_rate: float = 0.005,
    ):
        self.initial_balance = initial_balance
        self.wallet_balance = initial_balance
        self.leverage = leverage
        self.commission_rate = commission_rate
        self.maintenance_margin_rate = maintenance_margin_rate

        self.position_size = 0.0  # Base asset size, >0 for long, <0 for short
        self.entry_price = 0.0
        self.current_price = 0.0

    def set_leverage(self, leverage: float) -> None:
        """Update the leverage setting."""
        if leverage <= 0:
            raise ValueError("Leverage must be greater than 0.")
        self.leverage = leverage

    def update_price(self, price: float) -> None:
        """Update the current market price and check for disqualification."""
        if price <= 0:
            raise ValueError("Price must be greater than 0.")
        self.current_price = price
        self._check_disqualification()

    def get_unrealized_pnl(self, current_price: float = None) -> float:
        """Calculate the unrealized PnL based on the current market price."""
        if current_price is None:
            current_price = self.current_price

        if self.position_size == 0.0:
            return 0.0

        return self.position_size * (current_price - self.entry_price)

    def get_account_equity(self) -> float:
        """Calculate the current account equity (wallet balance + unrealized PnL)."""
        return self.wallet_balance + self.get_unrealized_pnl()

    def get_nav(self) -> float:
        """Calculate the Net Asset Value (NAV)."""
        return self.get_account_equity() / self.initial_balance

    def get_margin_balance(self) -> float:
        """Calculate the margin balance. In this context, it is equivalent to account equity."""
        return self.get_account_equity()

    def get_position_value(self, current_price: float = None) -> float:
        """Calculate the nominal value of the current position."""
        if current_price is None:
            current_price = self.current_price
        return abs(self.position_size) * current_price

    def get_initial_margin(self) -> float:
        """Calculate required initial margin for the current position based on leverage."""
        return self.get_position_value() / self.leverage

    def get_maintenance_margin(self) -> float:
        """Calculate the maintenance margin required to keep the position open."""
        return self.get_position_value() * self.maintenance_margin_rate

    def _check_disqualification(self) -> None:
        """
        Check if the account falls below disqualification thresholds.
        Raises DisqualificationException if Account Equity < 800 USDT or NAV < 0.8.
        """
        equity = self.get_account_equity()
        nav = self.get_nav()

        if equity < 800.0:
            raise DisqualificationException(f"Account Equity ({equity:.2f}) dropped below 800 USDT.")

        if nav < 0.8:
            raise DisqualificationException(f"NAV ({nav:.4f}) dropped below 0.8.")

    def execute_trade(self, size: float, price: float, slippage: float = 0.0) -> dict:
        """
        Execute a trade with a given size, price, and slippage.
        size > 0 for buying (long), size < 0 for selling (short).

        Standard order loss is reflected in execution price slippage and commission fees.
        """
        if size == 0.0:
            return {}

        execution_price = price + np.sign(size) * slippage
        trade_value = abs(size) * execution_price
        commission = trade_value * self.commission_rate
        slippage_loss = abs(size) * slippage

        self.wallet_balance -= commission
        realized_pnl = 0.0

        if self.position_size == 0.0:
            self.entry_price = execution_price
            self.position_size = size
        elif (self.position_size > 0 and size > 0) or (self.position_size < 0 and size < 0):
            # Adding to the same direction
            total_value = abs(self.position_size) * self.entry_price + abs(size) * execution_price
            self.position_size += size
            self.entry_price = total_value / abs(self.position_size)
        else:
            # Closing or reversing
            if abs(size) <= abs(self.position_size):
                # Partially or fully closing
                closed_size = abs(size)
                if self.position_size > 0:
                    realized_pnl = closed_size * (execution_price - self.entry_price)
                else:
                    realized_pnl = closed_size * (self.entry_price - execution_price)

                self.wallet_balance += realized_pnl
                self.position_size += size

                if self.position_size == 0.0:
                    self.entry_price = 0.0
            else:
                # Reversing position
                closed_size = abs(self.position_size)
                if self.position_size > 0:
                    realized_pnl = closed_size * (execution_price - self.entry_price)
                else:
                    realized_pnl = closed_size * (self.entry_price - execution_price)

                self.wallet_balance += realized_pnl

                # The remaining size opens a new position in the opposite direction
                remaining_size = size + self.position_size
                self.position_size = remaining_size
                self.entry_price = execution_price

        self.current_price = price
        self._check_disqualification()

        return {
            "execution_price": execution_price,
            "commission": commission,
            "slippage_loss": slippage_loss,
            "realized_pnl": realized_pnl,
            "new_position_size": self.position_size,
            "new_entry_price": self.entry_price
        }
