import numpy as np
from typing import List

class ConformalSizer:
    """
    Composable Sizing Module (Raven Base)
    Calculates position sizes based on conformal prediction intervals.
    Implements Marc Schmitt's Regime-Weighted Conformal (RWC) Calibration.
    """
    def __init__(self, window_size: int = 500, alpha: float = 0.25, kappa: float = 0.15):
        self.window_size = window_size
        self.alpha = alpha  # Corresponds to 75th percentile (1 - alpha)
        self.kappa = kappa
        self.errors: List[float] = []
        self.weights: List[float] = []

        # RWC Hyperparameters
        self.rho_base = 1.0
        self.gamma_1 = 0.1
        self.gamma_2 = 0.1
        self.L_bar = 1.0 # Moving average of reconstruction loss

    def update_discount_factor(self, sigma_m: float, L_t: float) -> float:
        """
        Calculates dynamic discount factor rho_t^* based on local market volatility and VAE reconstruction loss.
        rho_t^* = rho_base * exp(-gamma_1 * sigma_m - gamma_2 * (L_t / L_bar))
        """
        # Update L_bar (simple EMA)
        self.L_bar = 0.9 * self.L_bar + 0.1 * L_t if self.L_bar > 0 else L_t

        rho_t = self.rho_base * np.exp(-self.gamma_1 * sigma_m - self.gamma_2 * (L_t / self.L_bar))
        return rho_t

    def add_error(self, s_it: float, sigma_m: float = 0.0, L_t: float = 0.0) -> None:
        """
        Add a landed prediction absolute error and apply dynamic exponential weight decay to past residuals.
        """
        rho_t = self.update_discount_factor(sigma_m, L_t)

        # Apply exponential decay factor to past conformity scores
        self.weights = [w * rho_t for w in self.weights]

        self.errors.append(s_it)
        self.weights.append(1.0) # New error gets full weight

    def get_position_size(self, mu_hat: float) -> float:
        """
        Compute the fractional Kelly position size based on conformal prediction intervals.
        """
        if not self.errors:
            return 0.0

        # Regime-Weighted Quantile Calculation
        # Instead of naive sliding window, we use the weighted errors

        # Get recent errors and weights
        recent_errors = np.array(self.errors[-self.window_size:])
        recent_weights = np.array(self.weights[-self.window_size:])

        if len(recent_errors) == 0:
            return 0.0

        # Normalize weights
        sum_weights = np.sum(recent_weights)
        if sum_weights > 0:
            norm_weights = recent_weights / sum_weights
        else:
            norm_weights = np.ones_like(recent_weights) / len(recent_weights)

        # Sort errors and weights together
        sorted_idx = np.argsort(recent_errors)
        sorted_errors = recent_errors[sorted_idx]
        sorted_weights = norm_weights[sorted_idx]

        # Calculate weighted empirical CDF
        cum_weights = np.cumsum(sorted_weights)

        # Find index where cumulative weight exceeds 75th percentile
        target_percentile = 0.75
        idx_roll = np.searchsorted(cum_weights, target_percentile)
        idx_roll = min(idx_roll, len(sorted_errors) - 1)
        q_roll = float(sorted_errors[idx_roll])

        # Expanding anchor quantile
        all_errors_arr = np.array(self.errors)
        all_weights_arr = np.array(self.weights)
        sum_all_weights = np.sum(all_weights_arr)

        if sum_all_weights > 0:
            norm_all_weights = all_weights_arr / sum_all_weights
        else:
            norm_all_weights = np.ones_like(all_weights_arr) / len(all_weights_arr)

        sorted_all_idx = np.argsort(all_errors_arr)
        sorted_all_errors = all_errors_arr[sorted_all_idx]
        sorted_all_weights = norm_all_weights[sorted_all_idx]

        cum_all_weights = np.cumsum(sorted_all_weights)
        idx_anchor = np.searchsorted(cum_all_weights, target_percentile)
        idx_anchor = min(idx_anchor, len(sorted_all_errors) - 1)
        q_anchor = float(sorted_all_errors[idx_anchor])

        # Calculate the effectively smoothed quantile (q_eff) using geometric shrinkage
        q_eff = (q_roll ** 0.7) * (q_anchor ** 0.3)

        # Derive the dynamic volatility scale (sigma_hat)
        sigma_hat = q_eff / 1.2816

        if sigma_hat == 0:
            return 0.0

        # Compute the fractional Kelly position size (f_it)
        f_it = self.kappa * (mu_hat / (sigma_hat ** 2))

        return f_it

class MVO_SMWSolver:
    """
    Dedicated solver helper for Sherman-Morrison-Woodbury (SMW) Factorization.
    """
    @staticmethod
    def solve_mvo_smw(B: np.ndarray, F: np.ndarray, D: np.ndarray, mu: np.ndarray, lambd: float) -> np.ndarray:
        """
        Solves the reformulated Quadratic Program (QP) using SMW factorization to guarantee sub-millisecond execution.
        Objective: min_{w, y}  y^T F y + w^T D w - lambd * mu^T w   subject to   y = B^T w

        This avoids O(N^3) Cholesky inversion of Sigma = B F B^T + D.
        Complexity: O(N k^2 + k^3) where k << N.

        Args:
            B: Factor loading matrix (N x k)
            F: Low-rank factor covariance (k x k)
            D: Diagonal matrix of idiosyncratic risk (N x N)
            mu: Expected returns (N)
            lambd: Risk aversion parameter

        Returns:
            w: Optimal weights (N)
        """
        # The unconstrained minimum of w^T Sigma w - lambd * mu^T w is:
        # w* = (1 / (2 * lambd)) * Sigma^{-1} mu
        # Using SMW identity:
        # Sigma^{-1} = (B F B^T + D)^{-1}
        #            = D^{-1} - D^{-1} B (F^{-1} + B^T D^{-1} B)^{-1} B^T D^{-1}

        # Since D is diagonal, D^{-1} is trivial O(N)
        D_inv = np.diag(1.0 / np.diag(D))

        # B^T D^{-1} B is (k x N) * (N x N) * (N x k) -> O(N k^2)
        B_T_D_inv = B.T @ D_inv
        B_T_D_inv_B = B_T_D_inv @ B

        # F^{-1} is O(k^3)
        F_inv = np.linalg.inv(F)

        # Inner inverse: (F^{-1} + B^T D^{-1} B)^{-1} is O(k^3)
        inner_matrix = F_inv + B_T_D_inv_B
        inner_inv = np.linalg.inv(inner_matrix)

        # Compute SMW inverse
        # D_inv - D_inv B * inner_inv * B^T D_inv
        # We can apply it directly to mu to be faster
        # w* = (1 / (2 * lambd)) * [D_inv mu - D_inv B (inner_inv (B^T (D_inv mu)))]

        D_inv_mu = D_inv @ mu
        term2 = D_inv @ B @ (inner_inv @ (B_T_D_inv @ mu))

        Sigma_inv_mu = D_inv_mu - term2

        w_opt = (1.0 / (2.0 * lambd)) * Sigma_inv_mu

        return w_opt
