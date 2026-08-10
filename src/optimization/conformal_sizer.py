import numpy as np
from typing import List

class ConformalSizer:
    """
    Composable Sizing Module (Raven Base)
    Calculates position sizes based on conformal prediction intervals.
    """
    def __init__(self, window_size: int = 500, alpha: float = 0.25, kappa: float = 0.15):
        self.window_size = window_size
        self.alpha = alpha  # Corresponds to 75th percentile (1 - alpha)
        self.kappa = kappa
        self.errors: List[float] = []

    def add_error(self, s_it: float) -> None:
        """Add a landed prediction absolute error."""
        self.errors.append(s_it)

    def get_position_size(self, mu_hat: float) -> float:
        """
        Compute the fractional Kelly position size based on conformal prediction intervals.
        """
        if not self.errors:
            return 0.0

        # Rolling window of the last W=500 landed prediction absolute errors
        rolling_errors = self.errors[-self.window_size:]

        # Compute the rolling (1 - alpha) empirical quantile (q_roll) where alpha = 0.25 (the 75th percentile).
        q_roll = float(np.percentile(rolling_errors, 75))

        # Compute expanding anchor quantile (q_anchor) over all historical errors
        q_anchor = float(np.percentile(self.errors, 75))

        # Calculate the effectively smoothed quantile (q_eff) using geometric shrinkage
        q_eff = (q_roll ** 0.7) * (q_anchor ** 0.3)

        # Derive the dynamic volatility scale (sigma_hat)
        sigma_hat = q_eff / 1.2816

        if sigma_hat == 0:
            return 0.0

        # Compute the fractional Kelly position size (f_it)
        f_it = self.kappa * (mu_hat / (sigma_hat ** 2))

        return f_it
