# OMEGA Portfolio Engine

Production-hardened engine form of the WISER Vanguard Challenge research
pipeline ([wiser-vanguard-quantum](https://github.com/hastikacheddy/wiser-vanguard-quantum)):
HRP decomposition → ADMM coordination → convex allocation, with the
penalty-free quantum QAOA+ selection path as a **feature-flagged module
(default OFF)** behind an exact classical fail-safe.

## What "production-hardened" means here — and what it does not

**Delivered:** installable package with a governed API and CLI · **hard
compliance gate** (weights never leave the engine with a guardrail breach —
`EngineComplianceError` instead) · per-run **audit manifests** (input
hashes, config, per-cluster ADMM diagnostics, breach audit, timings) ·
**walk-forward out-of-sample backtest** harness sharing the live estimation
path (no look-ahead, costs paid at rebalance) · structured logging · pytest
invariant suite · GitHub Actions CI · [MODEL_CARD.md](MODEL_CARD.md)
governance documentation.

**Not delivered, deliberately not claimed:** execution/OMS integration,
commercial risk model and point-in-time data feeds, liquidity/ADV and
tax-lot constraints, multi-user service surface, independent model
validation sign-off. Those are organizational deliverables, not repo
contents — see the model card's scope section.

## Install & run

```bash
pip install -e ".[quantum,test]"
pytest                                   # invariant suite

# one governed run on the committed 41-ETF snapshot (offline):
omega-engine run --source snapshot --k 12 --w-max 0.15 \
    --income-floor 0.02 --cvar-weight 5 --out runs/

# out-of-sample walk-forward replay (quarterly):
omega-engine backtest --k 10 --rebalance 63

# quantum selection path (experimental flag; exact fallback always armed):
omega-engine run --source synthetic --n 60 --k 15 --quantum
```

## API

```python
from omega_engine import ADMMConfig, PortfolioEngine
from omega_engine.market_snapshot import load_market_snapshot

engine = PortfolioEngine(
    config=ADMMConfig(income_floor=0.02, cvar_weight=5.0),
    quantum_enabled=False,          # classical spine — deployable today
    output_dir="runs/",
)
result = engine.run(load_market_snapshot(), k_total=12, w_max=0.15)
print(result.summary())             # raises EngineComplianceError on breach
```

## Engine guarantees (CI-tested)

1. Zero-breach output or a raised exception — never a silently
   non-compliant book.
2. Exactly-K selection enforced by circuit symmetry (quantum path,
   measured leakage ~1e-10) or exact enumeration (classical path).
3. Full audit manifest per run; deterministic under a fixed seed.
4. Quantum failures degrade to the exact classical z-update, logged.

## Author

- **hastikacheddy** ([github.com/hastikacheddy](https://github.com/hastikacheddy)) — hastikacheddy06@gmail.com
- Solo submission.

Research repository (challenge submission with deck, formulation, dashboards,
and adversarial benchmark):
[wiser-vanguard-quantum](https://github.com/hastikacheddy/wiser-vanguard-quantum).

## Credits & attribution

**Data.** The committed ETF price snapshot ([data/etf_prices.csv](data/etf_prices.csv))
is daily adjusted closes retrieved once from **Yahoo Finance** via the
[`yfinance`](https://github.com/ranaroussi/yfinance) library, for research
demonstration only.

**Open-source tools.** [Qiskit](https://www.ibm.com/quantum/qiskit) /
Qiskit Aer / Qiskit Algorithms · [CVXPY](https://www.cvxpy.org/)
(Clarabel/OSQP/ECOS/SCS) · [NumPy](https://numpy.org/),
[SciPy](https://scipy.org/), [pandas](https://pandas.pydata.org/).

**Methods.** HRP — López de Prado (2016) · Dicke states — Bärtschi &
Eidenbenz (arXiv:1904.07358) · ADMM — Boyd et al. (2011) · CVaR —
Rockafellar & Uryasev (2000).

MIT license. Version 0.1.0 — see [CHANGELOG.md](CHANGELOG.md).
