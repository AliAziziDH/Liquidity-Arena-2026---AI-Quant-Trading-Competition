import streamlit as st
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt

# Import the actual conformal sizer from the mathematical base
from src.optimization.conformal_sizer import ConformalSizer

st.set_page_config(
    page_title="Decision Intelligence Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛡️ Decision Intelligence Dashboard")
st.markdown("Visual Control Center demonstrating mathematical safety and risk gating.")

tab1, tab2, tab3 = st.tabs([
    "📊 Conformal Kelly Sizer",
    "🚨 VAE Anomaly Shield",
    "⚡ Risk Router Live Cabin"
])

with tab1:
    st.header("Conformal Kelly Position Sizer (What-If Simulator)")
    st.markdown("Interactive demonstration of Leverage Slashing as conformal uncertainty increases.")

    col1, col2, col3 = st.columns(3)

    with col1:
        mu_hat = st.slider(
            r"Expected Return ($\hat{\mu}_t$)",
            min_value=-0.05,
            max_value=0.05,
            value=0.01,
            step=0.001,
            format="%.3f"
        )
    with col2:
        sigma_hat = st.slider(
            r"Conformal Width ($\hat{\sigma}_t$)",
            min_value=0.01,
            max_value=0.30,
            value=0.05,
            step=0.01,
            format="%.2f"
        )
    with col3:
        kappa = st.slider(
            r"Kelly Shrinkage ($\kappa$)",
            min_value=0.05,
            max_value=0.50,
            value=0.15,
            step=0.01,
            format="%.2f"
        )

    # Calculate position size dynamically
    if sigma_hat == 0:
        pos_size = 0.0
    else:
        pos_size = kappa * (mu_hat / (sigma_hat ** 2))

    st.metric(label=r"Target Position Size ($f_{i,t}$)", value=f"{pos_size:.4f}")

    # Plot quadratic scaling curve
    sigmas = np.linspace(0.01, 0.30, 100)
    sizes = kappa * (mu_hat / (sigmas ** 2))

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#1F2937')
    ax.plot(sigmas, sizes, color="#00FF66", linewidth=2)
    ax.scatter(sigma_hat, pos_size, color="#FF3366", s=100, zorder=5, label="Current State")
    ax.set_xlabel(r"Conformal Width ($\hat{\sigma}_t$)", color="white")
    ax.set_ylabel("Position Size", color="white")
    ax.set_title("Leverage Slashing Curve", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color('#1F2937')
    ax.grid(color="#0E1117", alpha=0.5)
    ax.legend()

    st.pyplot(fig)


with tab2:
    st.header("VAE OOD Crisis Detector (Anomaly Shield)")
    st.markdown("Simulation of the STORM VQ-VAE Anomaly Paradox vs. Standard Continuous VAE.")

    inject = st.button("Inject 400% Spread Spike", type="primary")

    # Mock parameters
    baseline_loss = 0.02

    if inject:
        # Simulate spike
        vq_vae_loss = baseline_loss * 6.5 # >= 6x spike
        cont_vae_loss = baseline_loss * 1.8 # <= 2x spike
        state = "CRISIS DETECTED"
        color = "#FF3366"
    else:
        # Normal
        vq_vae_loss = baseline_loss * 1.1
        cont_vae_loss = baseline_loss * 1.05
        state = "NORMAL REGIME"
        color = "#00FF66"

    st.subheader(f"Current State: {state}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("STORM VQ-VAE Reconstruction Loss", f"{vq_vae_loss:.4f}", delta=f"{(vq_vae_loss - baseline_loss):.4f}" if inject else None, delta_color="inverse")
    with col2:
        st.metric("Standard Continuous VAE Loss", f"{cont_vae_loss:.4f}", delta=f"{(cont_vae_loss - baseline_loss):.4f}" if inject else None, delta_color="inverse")

    # Bar chart comparison
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    fig2.patch.set_facecolor('#0E1117')
    ax2.set_facecolor('#1F2937')

    models = ['STORM VQ-VAE', 'Continuous VAE']
    losses = [vq_vae_loss, cont_vae_loss]
    colors = [color, "#A0AEC0"]

    ax2.bar(models, losses, color=colors)
    ax2.set_ylabel("Reconstruction Loss", color="white")
    ax2.set_title("Anomaly Amplifier Effect", color="white")
    ax2.tick_params(colors="white")
    ax2.axhline(y=baseline_loss, color="white", linestyle="--", label="Baseline")
    for spine in ax2.spines.values():
        spine.set_color('#1F2937')
    ax2.legend()

    st.pyplot(fig2)


with tab3:
    st.header("Heuristic Risk Router & Live Cabin")
    st.markdown(r"Live streaming simulation of EMA score dropping below risk threshold $\tau$.")

    start_live = st.button("Start Live Feed")

    chart_placeholder = st.empty()
    status_placeholder = st.empty()

    tau = 0.50

    if start_live:
        scores = []
        thresholds = []

        # Initialize high (normal regime)
        current_score = 0.85

        for i in range(100):
            # Introduce crisis halfway through
            if i > 50:
                current_score -= np.random.uniform(0.01, 0.08) # Rapid drop
            else:
                current_score += np.random.uniform(-0.02, 0.02) # Stable noise
                current_score = min(0.99, max(0.01, current_score))

            scores.append(current_score)
            thresholds.append(tau)

            df = pd.DataFrame({
                r'Smoothed EMA Score ($Re^{iu}$)': scores,
                r'Risk Threshold ($\tau$)': thresholds
            })

            # Simple line chart using Streamlit native chart for dynamic updates
            chart_placeholder.line_chart(df, color=["#00FF66", "#FF3366"])

            if current_score < tau:
                status_placeholder.error("🚨 CONSERVATIVE POLICY ACTIVATED: Score dropped below threshold! Hard exit guard initiated (NAV >= 0.8, Cash >= 800 USDT locked).")
            else:
                status_placeholder.success("✅ NORMAL REGIME: Continuing optimized sizing.")

            time.sleep(0.1)
