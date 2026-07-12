# Changelog

## 0.1.0 — 2026-07-12

Initial engine release, hardened from the WISER Vanguard Challenge research
pipeline (wiser-vanguard-quantum).

- `PortfolioEngine` governed facade: compliance gate (zero-breach or raise),
  audit manifests with input hashes and per-cluster ADMM diagnostics,
  structured logging, quantum path feature-flagged (default OFF) with exact
  classical fail-safe.
- Walk-forward out-of-sample backtest harness (shared estimation path,
  costs at rebalance, compliance gate active per rebalance).
- CLI (`omega-engine run|backtest`) and `python -m omega_engine`.
- Committed offline 41-ETF multi-asset snapshot (data/etf_prices.csv).
- Pytest invariant suite (encoding exactness, Hamming-weight conservation,
  engine contract, backtest smoke) + GitHub Actions CI.
- MODEL_CARD.md governance documentation with explicit scope limits.
