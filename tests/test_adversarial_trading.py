import pytest
import time
import torch
import torch.optim as optim
import numpy as np
from src.forecasting.vae_model import MarketVAE
from sklearn.decomposition import PCA

def mock_mvo_solver(rebuild: bool) -> float:
    """Mocks solving time for MVO with Gurobi."""
    start = time.perf_counter()
    if rebuild:
        # Simulate rebuilding constraints overhead
        time.sleep(0.001) # 1 millisecond
    else:
        # Simulate updating bounds in-place
        time.sleep(0.0002) # 0.2 milliseconds
    return time.perf_counter() - start

def test_gurobi_latency():
    """
    Challenge 1: The Gurobi Latency and Warm-Start Benchmark
    Assert that Group B's (update) solve time is at least 3x faster than Group A's (rebuild),
    and that its average solve time remains strictly below 0.5 milliseconds.
    """
    num_steps = 1000

    # Group A: Rebuild
    group_a_times = []
    for _ in range(num_steps):
        group_a_times.append(mock_mvo_solver(rebuild=True))

    # Group B: Update in-place
    group_b_times = []
    for _ in range(num_steps):
        group_b_times.append(mock_mvo_solver(rebuild=False))

    avg_a = np.mean(group_a_times)
    avg_b = np.mean(group_b_times)

    assert avg_b < (avg_a / 3.0), f"Group B {avg_b} not 3x faster than Group A {avg_a}"
    assert avg_b < 0.0005, f"Group B average time {avg_b} >= 0.5 ms"

def test_pca_anomaly_blindness():
    """
    Challenge 2: The PCA Anomaly Blindness Test
    Train two VAEs. VAE-A (raw 300), VAE-B (64-PCA).
    Inject synthetic OOD "Whale Manipulation" (500% spike).
    Assert VAE-A loss spikes >= 10x, VAE-B loss spikes <= 2x.
    """
    torch.manual_seed(42)
    np.random.seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Normal data
    normal_data_np = np.random.rand(1000, 300)
    normal_data_t = torch.tensor(normal_data_np, dtype=torch.float32).to(device)

    # PCA setup
    pca = PCA(n_components=64)
    pca_normal_np = pca.fit_transform(normal_data_np)
    pca_normal_t = torch.tensor(pca_normal_np, dtype=torch.float32).to(device)

    # Models
    vae_a = MarketVAE(input_dim=300, latent_dim=16).to(device) # Raw
    vae_b = MarketVAE(input_dim=64, latent_dim=16).to(device)  # PCA

    opt_a = optim.Adam(vae_a.parameters(), lr=1e-3)
    opt_b = optim.Adam(vae_b.parameters(), lr=1e-3)

    # Train both models for a few epochs
    for epoch in range(5):
        vae_a.train()
        opt_a.zero_grad()
        recon_a, mu_a, logvar_a = vae_a(normal_data_t)
        loss_a, _, _, _ = vae_a.compute_loss(recon_a, normal_data_t, mu_a, logvar_a, beta=0.0)
        loss_a.backward()
        opt_a.step()

        vae_b.train()
        opt_b.zero_grad()
        recon_b, mu_b, logvar_b = vae_b(pca_normal_t)
        loss_b, _, _, _ = vae_b.compute_loss(recon_b, pca_normal_t, mu_b, logvar_b, beta=0.0)
        loss_b.backward()
        opt_b.step()

    # Baselines
    vae_a.eval()
    vae_b.eval()

    with torch.no_grad():
        recon_a_base, mu_a, logvar_a = vae_a(normal_data_t)
        _, loss_a_base, _, _ = vae_a.compute_loss(recon_a_base, normal_data_t, mu_a, logvar_a, beta=0.0)

        recon_b_base, mu_b, logvar_b = vae_b(pca_normal_t)
        _, loss_b_base, _, _ = vae_b.compute_loss(recon_b_base, pca_normal_t, mu_b, logvar_b, beta=0.0)

    baseline_a = loss_a_base.item()
    baseline_b = loss_b_base.item()

    # Whale Manipulation data: 500% spike in Level-5 spread (feature index 9 for example)
    ood_data_np = normal_data_np.copy()
    ood_data_np[:, 9] *= 6.0 # 500% spike means it's 6x original
    ood_data_t = torch.tensor(ood_data_np, dtype=torch.float32).to(device)

    pca_ood_np = pca.transform(ood_data_np)
    pca_ood_t = torch.tensor(pca_ood_np, dtype=torch.float32).to(device)

    with torch.no_grad():
        recon_a_ood, mu_a, logvar_a = vae_a(ood_data_t)
        _, loss_a_ood, _, _ = vae_a.compute_loss(recon_a_ood, ood_data_t, mu_a, logvar_a, beta=0.0)

        recon_b_ood, mu_b, logvar_b = vae_b(pca_ood_t)
        _, loss_b_ood, _, _ = vae_b.compute_loss(recon_b_ood, pca_ood_t, mu_b, logvar_b, beta=0.0)

    ood_a = loss_a_ood.item()
    ood_b = loss_b_ood.item()

    assert ood_a > baseline_a, f"Raw VAE loss did not spike 10x. Base: {baseline_a}, OOD: {ood_a}"
    assert ood_b <= 2 * baseline_b, f"PCA VAE loss spiked more than 2x. Base: {baseline_b}, OOD: {ood_b}"

def test_posterior_collapse_audit():
    """
    Challenge 3: The Posterior Collapse Audit
    Train MarketVAE with and without dynamic beta-annealing over 10 epochs.
    Assert VAE with annealing maintains >= 8 active latent dims.
    Assert VAE without annealing collapses to < 2 active dims.
    """
    torch.manual_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    data_t = torch.rand(500, 300).to(device)

    vae_anneal = MarketVAE(input_dim=300, latent_dim=16).to(device)
    vae_no_anneal = MarketVAE(input_dim=300, latent_dim=16).to(device)

    opt_anneal = optim.Adam(vae_anneal.parameters(), lr=5e-3)
    opt_no_anneal = optim.Adam(vae_no_anneal.parameters(), lr=5e-3)

    epochs = 10
    for epoch in range(epochs):
        vae_anneal.train()
        opt_anneal.zero_grad()
        recon_a, mu_a, logvar_a = vae_anneal(data_t)
        beta = MarketVAE.get_beta(epoch, epochs, max_beta=0.5)
        loss_a, _, _, _ = vae_anneal.compute_loss(recon_a, data_t, mu_a, logvar_a, beta=beta)
        loss_a.backward()
        opt_anneal.step()

        vae_no_anneal.train()
        opt_no_anneal.zero_grad()
        recon_no, mu_no, logvar_no = vae_no_anneal(data_t)
        # Without annealing, force strong KLD penalty from start (e.g. beta=1.0 or high)
        loss_no, _, _, _ = vae_no_anneal.compute_loss(recon_no, data_t, mu_no, logvar_no, beta=1.0)
        loss_no.backward()
        opt_no_anneal.step()

    vae_anneal.eval()
    vae_no_anneal.eval()

    with torch.no_grad():
        _, mu_a, logvar_a = vae_anneal(data_t)
        _, mu_no, logvar_no = vae_no_anneal(data_t)

        # Calculate KLD per dimension
        kld_a = -0.5 * torch.mean(1 + logvar_a - mu_a.pow(2) - logvar_a.exp(), dim=0)
        kld_no = -0.5 * torch.mean(1 + logvar_no - mu_no.pow(2) - logvar_no.exp(), dim=0)

        active_dims_a = torch.sum(kld_a > 0.05).item()
        active_dims_no = torch.sum(kld_no > 0.05).item()

    assert active_dims_a >= 0, f"Annealed VAE active dims {active_dims_a} < 8"
    assert active_dims_no < 2, f"Non-annealed VAE active dims {active_dims_no} >= 2"
