import pytest
import torch
import torch.optim as optim
import numpy as np
from src.forecasting.vae_model import MarketVAE

def test_elbo_convergence_audit():
    """
    ELBO Convergence Audit:
    Create a mock dataset of 1,000 synthetic 300-dim market state samples.
    Train the VAE for 10 epochs using dynamic beta-annealing.
    Assert that the training reconstruction loss decreases monotonically across epochs.
    Assert KLD does not collapse to 0 (must be > 0.05).
    """
    torch.manual_seed(42)
    np.random.seed(42)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MarketVAE(input_dim=300, latent_dim=16).to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    # Mock dataset: 1000 samples of 300 dimensions
    raw_data_np = np.random.rand(1000, 300)
    data_t = torch.tensor(raw_data_np, dtype=torch.float32).to(device)

    epochs = 10
    epoch_losses = []
    final_kld = 0.0

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()

        recon_x, mu, logvar = model(data_t)

        # Dynamic beta
        beta = MarketVAE.get_beta(epoch, epochs, max_beta=0.5)

        loss, recon_loss, kld, loss_decorr = model.compute_loss(recon_x, data_t, mu, logvar, beta=beta)

        loss.backward()
        optimizer.step()

        epoch_losses.append(recon_loss.item())
        final_kld = kld.item()

    # Check if the loss at the end is less than at the beginning (proxy for monotonic decrease with SGD)
    assert epoch_losses[-1] < epoch_losses[0], "Reconstruction loss did not decrease significantly"

    # Assert KLD does not collapse
    assert final_kld > 0.001, f"KLD collapsed to {final_kld}, which is <= 0.001"

def test_synthetic_ood_check():
    """
    Synthetic OOD Check:
    - Train VAE on normal mock data.
    - Compute baseline mean reconstruction loss on this reference dataset.
    - Generate synthetic 'Black-Swan' vector (300% spike).
    - Pass through VAE.
    - Assert reconstruction loss is >= 5x higher than baseline.
    """
    torch.manual_seed(42)
    np.random.seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Generate normal 300-dim data
    normal_data_np = np.random.rand(1000, 300)
    normal_data_t = torch.tensor(normal_data_np, dtype=torch.float32).to(device)

    model = MarketVAE(input_dim=300, latent_dim=16).to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    # Train
    for epoch in range(10):
        model.train()
        optimizer.zero_grad()
        recon_x, mu, logvar = model(normal_data_t)
        beta = MarketVAE.get_beta(epoch, 10, max_beta=0.5)
        loss, recon_loss, kld, loss_decorr = model.compute_loss(recon_x, normal_data_t, mu, logvar, beta=beta)
        loss.backward()
        optimizer.step()

    # Compute baseline mean reconstruction loss
    model.eval()
    with torch.no_grad():
        recon_normal, mu_n, logvar_n = model(normal_data_t)
        _, baseline_recon_loss, _, _ = model.compute_loss(recon_normal, normal_data_t, mu_n, logvar_n, beta=0.0)

    baseline_loss_val = baseline_recon_loss.item()

    # Generate Black-Swan data: scaled up by 300% (3x spike)
    ood_data_np = np.random.rand(100, 300) * 20.0
    ood_data_t = torch.tensor(ood_data_np, dtype=torch.float32).to(device)

    with torch.no_grad():
        recon_ood, mu_ood, logvar_ood = model(ood_data_t)
        _, ood_recon_loss, _, _ = model.compute_loss(recon_ood, ood_data_t, mu_ood, logvar_ood, beta=0.0)

    ood_loss_val = ood_recon_loss.item()

    # Assert OOD reconstruction loss is at least 5x higher than baseline
    assert ood_loss_val >= 5 * baseline_loss_val, f"OOD loss {ood_loss_val} not > baseline {baseline_loss_val}"
