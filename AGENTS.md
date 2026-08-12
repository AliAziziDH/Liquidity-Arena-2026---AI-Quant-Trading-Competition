# Jules Repository Configuration Blueprint

This repository is governed by the following strict agentic SDLC and operational conventions:

## 1. Mainline Development Pattern
Enforce a clean, decoupled execution pipeline for all operations:
`Project -> Task -> Stage -> Run -> Artifact/Evidence -> Gate -> Handoff/Done`

## 2. Fail-Closed Protocol Parsers
If incoming RapidX/MCP order schemas or market data payloads do not align with our predefined schemas, the system must abort immediately to prevent hazardous routing. Default to a fail-closed, secure posture.

## 3. Strict Separation of Concerns
Decouple all presentation layers (such as Streamlit or CLI UIs) and logging tools from our underlying analytical models, VAE logic, and mathematical Pyomo formulations. Mathematical business logic must remain completely independent of external utility scripts.

## 4. Semantic Success Audit
Never treat an `exit code zero` as semantic success. Automated tests must explicitly assert operational safety parameters:
- The portfolio must not undergo capital liquidation.
- The portfolio must not hit the hard disqualification threshold (`NAV < 0.8` or `cash < 800 USDT`) during backtest runs.

## 5. Review Gates
- Code changes must be validated by local tests (`pytest`) prior to merging or promoting any PR branch.
- Any changed dependencies make prior approvals stale. Re-validation is strictly required.

## 6. Architecture Highlights
- **Predictive VAE**: Monitors for Out-Of-Distribution (OOD) market states, computing KLD and reconstruction loss (ELBO).
- **Prescriptive Conformal Kelly Risk Gate**: Dynamically scales position sizing using conformal prediction error distributions.
