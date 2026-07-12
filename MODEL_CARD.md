# Model Card — OMEGA Portfolio Engine v0.1.0

Governance-style documentation: what this model is, what it assumes, what
was validated, and where it must not be used. Written in the spirit of
model-risk-management practice (SR 11-7-class documentation).

## Purpose & scope
Constructs a long-only, exactly-K-name multi-asset portfolio under hard
guardrails (budget, box with minimum position, asset-class caps, optional
income floor) and soft goals (growth, drawdown-control CVaR penalty, cost
sensitivity), via HRP decomposition + ADMM coordination + convex allocation,
with an optional (feature-flagged, default OFF) quantum QAOA+ selection path
that has an exact classical fail-safe.

**In scope:** research, prototyping, decision support, hardware-readiness
evaluation. **Out of scope:** unsupervised management of real capital. The
engine has no execution integration, no independent model validation
sign-off, and the input estimates below are demonstration-grade.

## Inputs & assumptions
- Expected returns μ are an INPUT assumption (per the underlying problem
  statement). The bundled estimators (synthetic factor model; 50%-shrunk
  trailing means on the ETF snapshot) are placeholders for a governed
  forecast process.
- Covariance: exact factor covariance (synthetic) or constant-correlation-
  shrunk sample covariance (snapshot). Production use requires a maintained
  commercial-grade risk model.
- Linear transaction costs only; no market impact, borrow, liquidity/ADV,
  tax-lot, or tracking-error modeling.

## Guarantees (enforced, tested in CI)
1. **Compliance gate:** weights never leave the engine with a hard-guardrail
   breach (`EngineComplianceError` otherwise). Backtest replays inherit it.
2. **Cardinality by symmetry:** the quantum path cannot emit an off-mandate
   selection — every circuit gate conserves Hamming weight (tested to
   ~1e-10 statevector leakage); the classical path enumerates the feasible
   shell exactly.
3. **Auditability:** every run emits a manifest with input hashes, config,
   per-cluster diagnostics, full breach audit, and timings.
4. **Fail-safe:** any quantum-path failure falls back to exact classical
   enumeration with a logged warning; the pipeline never stalls on it.

## Validation evidence (v0.1.0)
- Ising encodings verified against brute force over all basis states.
- Approximation ratio 1.0000 vs certified exhaustive optima at tested sizes.
- Forecast-robustness: ±20% μ perturbations → 0 breaches in all trials,
  graceful Sharpe decay, ~93% selection stability (research repo).
- Walk-forward replay on the committed ETF panel: 0 breaches at every
  out-of-sample rebalance (CI test).

## Known limitations & failure modes
- The backtest is a single-path historical replay — a pipeline-contract
  smoke test, not a statistical claim of performance.
- μ estimates from short windows favor low-vol assets (books can look
  defensive); this is an estimation artifact, documented, not tuned away.
- ADMM with a nonconvex (binary) block is a principled heuristic (Boyd §9):
  residual decay is measured and logged per run, not guaranteed a priori.
- Quantum path adds no quality over exact enumeration at cluster sizes
  ≤ 20; its value is architectural (decomposability + hardware readiness).
- Snapshot data ships at repo root (`data/`); wheel installs must pass an
  explicit CSV path.

## Change management
Semantic versioning; CHANGELOG.md; CI must be green (invariant tests above)
before merge to main.
