# 📄 AGENTS.md: Repository Standards & Capabilities

This repository contains the official codebase for the **Liquidity Arena 2026 AI Quant Trading Competition (Track A - Logic Frontier)** operating under the Model Context Protocol (MCP) and RapidX environment.

The platform implements a **Hybrid AI-OR Decision Intelligence Engine** combining Machine Learning predictive forecasting with operations research deterministic risk gating and position sizing.

## 🎯 System Architecture & Separation of Concerns (SoC)

To prevent technical debt, look-ahead leakage, and code injection, the codebase strictly enforces a modular design pattern:

1. **`src/forecasting/vae_model.py` (ML Predictive Layer):**
   - Implements the continuous VAE and the **STORM VQ-VAE** (Vector Quantized) anomaly detection model.
   - Computes Evidence Lower Bound (ELBO) and reconstruction loss on 300-dimensional Market State Vectors.
   - Acts as our Crisis Detector. It is strictly mathematical and decoupled from execution or visualization.

2. **`src/optimization/conformal_sizer.py` (OR Prescriptive Sizing):**
   - Computes rolling conformal quantiles \(\hat{\sigma}_{i,t}\) over prediction errors and applies the fractional Kelly sizing formula:
     \[f_{i,t} = \kappa \cdot \frac{\hat{\mu}_{i,t}}{\hat{\sigma}_{i,t}^2}\]
   - Restricts sizing dynamically via "Leverage Slashing" as uncertainty expands.

3. **`src/execution/router.py` & `src/execution/live_executor.py` (Routing & RapidX API Layer):**
   - `router.py`: Smooths the Empirical Cumulative Distribution Function (ECDF) reconstruction loss using an EMA score. Gating activates the Conservative Policy (position close) if the score falls below threshold \(\tau\).
   - `live_executor.py`: Translates target weights into compliant live orders and interacts with the **RapidX MCP server (Spec 2026-07-28)**.

4. **`app.py` (Streamlit Presentation Layer):**
   - Professional dark-themed financial UI visualising the Conformal Kelly Sizer (What-If simulator), STORM VQ-VAE reconstruction loss, and real-time Heuristic Router. Decoupled from backend loops.

5. **`diagnostic_run.py` (Diagnostic Simulation):**
   - Walks forward over validation ticks to assert system PnL, Maximum Drawdown (MDD), and final Net Asset Value (NAV).

## ⚡ Environment & Setup Instructions

To run the repository and active CLI/Streamlit services:
\`\`\`bash
# Setup python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run our Streamlit Decision Cockpit
streamlit run app.py
\`\`\`

## 🔌 Stateless MCP 2.0 & Token Economy Directives
This repository conforms to the Model Context Protocol. Do not flood context windows with verbose schemas.
Execute tools inside the VM sandboxed environment.
Use explicit, stateless resource handles (such as dataset_id or session_handle).

## 🧪 Testing & Self-Correction Loop
Jules operates on an edit-test-repair loop. You must run the pytest suite before submitting any Pull Request:
\`\`\`bash
pytest
\`\`\`
Our testing gates enforce strict mathematical invariants:
* Sizing Ablation Test: Spiking confidence interval width by 200% must reduce position sizes by exactly 75% under quadratic scaling (\( 1/\sigma^2 \)).
* SMW Complexity Audit: Verifies the Sherman-Morrison-Woodbury inversion speedup (≥10× faster than standard np.linalg.inv for N=1000).
* STORM Anomaly Test: Injecting a 400% spread spike must yield a STORM VQ-VAE reconstruction loss spike of ≥6× relative to baseline, while standard VAE remains ≤2×.
