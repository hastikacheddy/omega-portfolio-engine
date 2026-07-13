<div align="center">

# OMEGA Portfolio Engine

### Production-hardened hybrid portfolio construction with hard compliance gating

[![CI](https://github.com/hastikacheddy/omega-portfolio-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/hastikacheddy/omega-portfolio-engine/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.1.0-informational.svg)](CHANGELOG.md)

</div>

---

## Overview

The OMEGA Portfolio Engine is the production-hardened engine form of the
[WISER Vanguard Challenge research pipeline](https://github.com/hastikacheddy/wiser-vanguard-quantum):
**HRP decomposition → ADMM coordination → convex allocation**, with the
penalty-free quantum QAOA+ selection path exposed as a feature-flagged module
(default **OFF**) behind an exact classical fail-safe.

It packages the deployable classical spine as an installable library with a
governed API, a command-line interface, per-run audit manifests, a
walk-forward backtest harness, a test suite under continuous integration, and
model-governance documentation.

## Scope

Being precise about scope is part of the design.

| Delivered | Deliberately out of scope |
|---|---|
| Installable package with governed API + CLI | Execution / OMS integration |
| **Hard compliance gate** — never emits a book with a guardrail breach | Commercial risk model & point-in-time data feeds |
| Per-run **audit manifests** (input hashes, config, diagnostics) | Liquidity / ADV and tax-lot constraints |
| **Walk-forward** out-of-sample backtest (no look-ahead) | Multi-user service surface |
| pytest invariant suite + GitHub Actions CI | Independent model-validation sign-off |
| [MODEL_CARD.md](MODEL_CARD.md) governance documentation | — |

The right-hand column lists organizational deliverables, not repository
contents. See the model card's scope section for detail.

## Installation

Requires Python 3.10+.

```bash
pip install -e ".[quantum,test]"
pytest                                       # run the invariant suite
```

## Usage

### Command line

```bash
# One governed run on the committed 41-ETF snapshot (offline)
omega-engine run --source snapshot --k 12 --w-max 0.15 \
    --income-floor 0.02 --cvar-weight 5 --out runs/

# Out-of-sample walk-forward replay (quarterly rebalance)
omega-engine backtest --k 10 --rebalance 63

# Quantum selection path (experimental flag; exact fallback always armed)
omega-engine run --source synthetic --n 60 --k 15 --quantum
```

### Python API

```python
from omega_engine import ADMMConfig, PortfolioEngine
from omega_engine.market_snapshot import load_market_snapshot

engine = PortfolioEngine(
    config=ADMMConfig(income_floor=0.02, cvar_weight=5.0),
    quantum_enabled=False,          # classical spine — deployable today
    output_dir="runs/",
)

result = engine.run(load_market_snapshot(), k_total=12, w_max=0.15)
print(result.summary())             # raises EngineComplianceError on any breach
```

## Engine guarantees

Each guarantee is enforced in code and covered by the CI test suite.

1. **Zero-breach output or a raised exception** — weights are never returned
   with a hard-guardrail breach; the engine raises `EngineComplianceError`
   instead.
2. **Exactly-K selection** — enforced by circuit symmetry on the quantum path
   (measured statevector leakage ≈ 10⁻¹⁰) or by exact enumeration on the
   classical path.
3. **Full auditability** — every run emits a JSON manifest with input hashes,
   configuration, per-cluster ADMM diagnostics, the breach audit, and
   timings; deterministic under a fixed seed.
4. **Fail-safe** — any quantum-path failure degrades to the exact classical
   z-update, logged, without stalling the pipeline.

## Testing

```bash
pytest                                       # encoding, feasibility, engine, backtest
```

The suite verifies the Ising encoding against brute force, Hamming-weight
conservation of the ansatz, the engine compliance contract and manifest
emission, and a walk-forward backtest that must record zero breaches at every
rebalance. It runs on every push via [GitHub Actions](.github/workflows/ci.yml).

## Documentation

- **[MODEL_CARD.md](MODEL_CARD.md)** — purpose, assumptions, validation
  evidence, known limitations, and change management (governance-style).
- **[CHANGELOG.md](CHANGELOG.md)** — versioned release notes.

## Author

**hastikacheddy** — [github.com/hastikacheddy](https://github.com/hastikacheddy) · hastikacheddy06@gmail.com (solo submission)

Research repository (challenge submission with deck, formulation, dashboards,
and adversarial benchmark):
[wiser-vanguard-quantum](https://github.com/hastikacheddy/wiser-vanguard-quantum).

## Credits & attribution

**Data.** The committed ETF price snapshot
([`data/etf_prices.csv`](data/etf_prices.csv)) is daily adjusted closes
retrieved once from **Yahoo Finance** via the
[`yfinance`](https://github.com/ranaroussi/yfinance) library, for research
demonstration only.

**Open-source tools.**
[Qiskit](https://www.ibm.com/quantum/qiskit) / Qiskit Aer / Qiskit Algorithms ·
[CVXPY](https://www.cvxpy.org/) (Clarabel / OSQP / ECOS / SCS) ·
[NumPy](https://numpy.org/) · [SciPy](https://scipy.org/) ·
[pandas](https://pandas.pydata.org/).

**Methods.**
HRP — López de Prado (2016) ·
Dicke states — Bärtschi & Eidenbenz (arXiv:1904.07358) ·
ADMM — Boyd et al. (2011) ·
CVaR — Rockafellar & Uryasev (2000).

## License

Released under the [MIT License](LICENSE). Version 0.1.0 — see
[CHANGELOG.md](CHANGELOG.md).
