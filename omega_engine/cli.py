"""Command-line surface:  python -m omega_engine {run|backtest} ...

Examples
--------
  python -m omega_engine run --source snapshot --k 12 --w-max 0.15 \\
      --income-floor 0.02 --cvar-weight 5 --out runs/
  python -m omega_engine backtest --k 12 --rebalance 21 --window 252
"""

from __future__ import annotations

import argparse
import logging
import sys

from .admm_coordinator import ADMMConfig
from .backtest import walk_forward_backtest
from .data_gen import generate_market_data
from .engine import PortfolioEngine
from .market_snapshot import load_market_snapshot


def _config_from(args: argparse.Namespace) -> ADMMConfig:
    return ADMMConfig(
        risk_aversion=args.risk_aversion,
        return_weight=args.growth,
        income_floor=args.income_floor if args.income_floor > 0 else None,
        cvar_weight=args.cvar_weight,
        cost_multiplier=args.cost_multiplier,
        seed=args.seed,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-engine")
    parser.add_argument("--log", default="INFO")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def _common(p):
        p.add_argument("--k", type=int, default=12)
        p.add_argument("--w-max", type=float, default=0.15)
        p.add_argument("--w-min", type=float, default=0.02)
        p.add_argument("--risk-aversion", type=float, default=5.0)
        p.add_argument("--growth", type=float, default=1.0)
        p.add_argument("--income-floor", type=float, default=0.0)
        p.add_argument("--cvar-weight", type=float, default=0.0)
        p.add_argument("--cost-multiplier", type=float, default=1.0)
        p.add_argument("--seed", type=int, default=7)
        p.add_argument("--quantum", action="store_true",
                       help="enable the QAOA+ z-update path (experimental)")

    p_run = sub.add_parser("run", help="construct one compliant book")
    _common(p_run)
    p_run.add_argument("--source", choices=["snapshot", "synthetic"],
                       default="snapshot")
    p_run.add_argument("--n", type=int, default=100,
                       help="universe size (synthetic only)")
    p_run.add_argument("--out", default=None, help="manifest output directory")

    p_bt = sub.add_parser("backtest", help="walk-forward historical replay")
    _common(p_bt)
    p_bt.add_argument("--window", type=int, default=252)
    p_bt.add_argument("--rebalance", type=int, default=21)

    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log.upper(),
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    engine = PortfolioEngine(config=_config_from(args),
                             quantum_enabled=args.quantum,
                             output_dir=getattr(args, "out", None))

    if args.cmd == "run":
        md = (load_market_snapshot() if args.source == "snapshot"
              else generate_market_data(n_assets=args.n, seed=args.seed))
        result = engine.run(md, k_total=args.k, w_max=args.w_max,
                            w_min=args.w_min)
        print(result.summary())
        if result.manifest_path:
            print(f"manifest: {result.manifest_path}")
        return 0

    report = walk_forward_backtest(engine, k_total=args.k, w_max=args.w_max,
                                   w_min=args.w_min, window=args.window,
                                   rebalance_every=args.rebalance)
    print(report.summary())
    return 0 if report.total_breaches == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
