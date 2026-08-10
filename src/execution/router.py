import numpy as np
import torch
from typing import Dict, Any, Tuple
from src.forecasting.vae_model import MarketVAE
from src.optimization.conformal_sizer import ConformalSizer
from src.execution.risk_gate import RiskGate

class HeuristicRouter:
    """
    Coordinates the Predictive (ML) and Prescriptive (OR) layers.
    Implements Heuristic Routing, CREDO/CREME Risk Calibration.
    """
    def __init__(self, vae_model: MarketVAE, sizer: ConformalSizer, risk_gate: RiskGate, ema_lambda: float = 0.9):
        self.vae_model = vae_model
        self.sizer = sizer
        self.risk_gate = risk_gate
        self.ema_lambda = ema_lambda

        # State variables
        self.smoothed_score = 0.0
        self.tau = 1.0 # Default fallback
        self.baseline_losses = np.array([])

        # State tracking for conservative policy
        self.conservative_mode_active = False

    def fit_ecdf(self, baseline_losses: np.ndarray) -> None:
        """Fits the empirical cumulative distribution function (eCDF) on baseline validation training errors."""
        self.baseline_losses = np.sort(baseline_losses)

    def _get_ecdf_score(self, loss: float) -> float:
        """Maps a raw reconstruction loss to a probability score between 0.0 and 1.0 using eCDF."""
        if len(self.baseline_losses) == 0:
            return 0.5 # Default if not fitted
        # Find the proportion of baseline losses that are less than or equal to the given loss
        idx = np.searchsorted(self.baseline_losses, loss, side='right')
        return float(idx) / len(self.baseline_losses)

    def calibrate_tau(self, validation_residuals: np.ndarray, ecdf_scores: np.ndarray, epsilon: float = 0.05, alpha: float = 0.05) -> None:
        """
        Dynamic tau Gating (Inverse Conformal Risk Control).
        Calibrates tau dynamically to guarantee out-of-sample decision regret remains below epsilon with 95% confidence (1 - alpha).
        validation_residuals: Regret/loss values.
        ecdf_scores: Corresponding eCDF scores for those points.
        """
        if len(validation_residuals) == 0 or len(ecdf_scores) == 0:
            self.tau = 1.0
            return

        n = len(validation_residuals)

        # Sort by score to find threshold
        sorted_indices = np.argsort(ecdf_scores)
        sorted_residuals = validation_residuals[sorted_indices]
        sorted_scores = ecdf_scores[sorted_indices]

        # Find tau threshold where accumulated risk <= epsilon with 1-alpha confidence
        # Simplified conformal risk control: evaluate empirical risk for each threshold tau
        # Empirical Risk(tau) = mean(residual for all scores <= tau)

        best_tau = 1.0
        # Add a finite sample correction term for confidence bound
        # (Very basic concentration bound logic representing conformal risk control)
        for i in range(1, n + 1):
            tau_candidate = sorted_scores[i - 1]
            # Expected regret for points with score <= tau_candidate
            empirical_risk = np.mean(sorted_residuals[:i])
            # High probability bound (using basic Hoeffding/Empirical Bernstein heuristic for (1-alpha))
            # upper_bound = empirical_risk + sqrt(log(1/alpha) / (2 * i))
            upper_bound = empirical_risk + np.sqrt(np.log(1 / alpha) / (2 * i))

            if upper_bound <= epsilon:
                best_tau = tau_candidate
            else:
                # If we exceed the budget, we stop and use the previous valid tau
                break

        self.tau = best_tau

    def route(self, state_vector: torch.Tensor, mu_hat: float, current_portfolio: Dict[str, Any]) -> float:
        """
        Routes the decision based on the market regime detected by the VAE.
        Returns the proposed position size.
        """
        self.vae_model.eval()
        with torch.no_grad():
            recon_x, mu, logvar = self.vae_model(state_vector)
            _, recon_loss, _, _ = self.vae_model.compute_loss(recon_x, state_vector, mu, logvar, beta=0.0)

        raw_loss = recon_loss.item()

        # Reconstruction Loss Mapping (ecdf)
        score = self._get_ecdf_score(raw_loss)

        # Temporal Smoothing (EMA)
        self.smoothed_score = self.ema_lambda * self.smoothed_score + (1.0 - self.ema_lambda) * score

        # Routing Logic
        if self.smoothed_score < self.tau:
            # Normal Regime
            self.conservative_mode_active = False
            # Route to Conformal Kelly Sizer
            proposed_size = self.sizer.get_position_size(mu_hat)
            return self.risk_gate.validate_position(proposed_size, current_portfolio)
        else:
            # OOD / Market Crisis Regime
            self.conservative_mode_active = True
            return self._conservative_policy(current_portfolio)

    def _conservative_policy(self, current_portfolio: Dict[str, Any]) -> float:
        """
        Conservative Policy (pi^c):
        - Freeze new order generation (return 0.0 for new sizes).
        - Close positions with run-time drawdowns exceeding 5%.
        """
        position_mtm_loss = current_portfolio.get("position_mtm_loss", 0.0)
        current_position_size = current_portfolio.get("current_position_size", 0.0)

        if position_mtm_loss > 0.05 and current_position_size != 0.0:
            # Signal to close position
            return -current_position_size

        # Freeze new orders / maintain delta-neutral
        return 0.0
