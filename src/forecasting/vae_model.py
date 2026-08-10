import torch
import numpy as np
import torch
import torch.nn as nn
from typing import Tuple

class MarketVAE(nn.Module):
    """
    Variational Autoencoder (VAE) for market state vectors.
    Learns representations and acts as a crisis monitor for the 300 raw features.
    """
    def __init__(self, input_dim: int = 300, hidden_dim: int = 128, latent_dim: int = 16):
        super(MarketVAE, self).__init__()

        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )

        # Store parameters for Trust-Region constraint
        self.prev_params = None

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Encodes the input into mu and logvar."""
        h = self.encoder(x)
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """Samples z = mu + eps * std."""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decodes latent variables back into reconstructed input."""
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass of the VAE."""
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        recon_x = self.decode(z)
        return recon_x, mu, logvar

    def compute_loss(
        self,
        recon_x: torch.Tensor,
        x: torch.Tensor,
        mu: torch.Tensor,
        logvar: torch.Tensor,
        beta: float = 1.0
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Computes the custom ELBO loss with Contrastive Latent Penalty.
        Overall_Loss = Reconstruction_Loss + beta * KLD + 0.1 * Loss_decorr
        """
        # For the anomaly detection to be highly sensitive to single-feature manipulation (tail risks),
        # we need to penalize maximum deviations heavily.
        mse = nn.functional.mse_loss(recon_x, x, reduction='none')
        recon_loss = mse.mean() + (mse ** 4).max(dim=-1)[0].mean() * 100.0

        # Kullback-Leibler Divergence
        kld = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp(), dim=-1).mean()

        # Contrastive Latent Penalty (Loss_decorr = sum_{j != k} (Cov(z_j, z_k) ** 2))
        # Batch size needs to be > 1 to compute covariance
        batch_size = mu.size(0)
        if batch_size > 1:
            mu_centered = mu - mu.mean(dim=0, keepdim=True)
            cov_mat = (mu_centered.t() @ mu_centered) / (batch_size - 1)
            # We want sum of off-diagonal elements squared
            diag = torch.diag(cov_mat)
            loss_decorr = torch.sum(cov_mat ** 2) - torch.sum(diag ** 2)
        else:
            loss_decorr = torch.tensor(0.0, device=mu.device)

        loss = recon_loss + beta * kld + 0.1 * loss_decorr
        return loss, recon_loss, kld, loss_decorr

    @staticmethod
    def get_beta(epoch: int, total_epochs: int, max_beta: float = 0.5) -> float:
        """
        Dynamic Beta-Annealing Scheduler.
        Linearly increases beta from 0.0 to 0.5 over the first 50% of epochs.
        """
        warmup_epochs = total_epochs / 2
        if epoch >= warmup_epochs:
            return max_beta
        return max_beta * (epoch / warmup_epochs)

    def save_trust_region_state(self):
        """Saves current parameters as theta_t for trust-region constraints."""
        self.prev_params = [p.clone().detach() for p in self.parameters()]

    def apply_trust_region_constraint(self, delta: float = 0.1):
        """
        Enforces Trust-Region Policy for Dual-Guided Loss (DGL).
        Bounds the update step-size: ||theta_{t+j} - theta_t||_2 <= delta
        This prevents prediction drift and chaotic loss shocks during frozen-dual epochs.
        """
        if self.prev_params is None:
            return

        with torch.no_grad():
            # Compute L2 distance between current params and previous params
            dist_sq = 0.0
            for p, prev_p in zip(self.parameters(), self.prev_params):
                dist_sq += torch.sum((p - prev_p) ** 2).item()

            dist = np.sqrt(dist_sq)

            # If distance exceeds delta, clip parameters back onto the delta-hypersphere
            if dist > delta:
                scale = delta / dist
                for p, prev_p in zip(self.parameters(), self.prev_params):
                    p.copy_(prev_p + scale * (p - prev_p))
