"""
Walk-forward backtest harness (out-of-sample, no look-ahead).
=============================================================

Protocol
--------
At each rebalance date t (every ``rebalance_every`` trading days):

1. estimate (μ, Σ, …) from the trailing ``window`` days **ending at t**
   (same shrinkage recipe as the live snapshot loader — no tuning between
   backtest and production paths);
2. run the governed engine → compliant weights (compliance gate active:
   a breach at any rebalance aborts the backtest loudly);
3. hold the book until t + rebalance_every, accruing **realized**
   out-of-sample daily returns net of linear transaction costs paid at
   the rebalance.

Reported: realized annualized return / vol / Sharpe, max drawdown, average
one-way turnover, total costs paid, breaches (must be 0), per-rebalance log.

Scope honesty (also in MODEL_CARD.md): single-path historical replay on a
pre-committed ETF panel — a governance smoke test of the *pipeline contract*
under data it has never seen, NOT a statistical claim of alpha.  No
slippage model beyond linear costs, no borrow/liquidity limits, one seed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .data_gen import TRADING_DAYS_PER_YEAR
from .engine import PortfolioEngine
from .market_snapshot import SNAPSHOT_CSV, market_from_prices

logger = logging.getLogger("omega.backtest")

__all__ = ["BacktestReport", "walk_forward_backtest"]


@dataclass
class BacktestReport:
    """Realized out-of-sample results of one walk-forward replay."""
    realized_annual_return: float
    realized_annual_vol: float
    realized_sharpe: float
    max_drawdown: float
    avg_turnover_oneway: float
    total_costs: float
    n_rebalances: int
    total_breaches: int          # engine gate ⇒ always 0 or the run raised
    daily_returns: pd.Series = field(repr=False)
    rebalance_log: pd.DataFrame = field(repr=False)

    def summary(self) -> str:
        return (f"{self.n_rebalances} rebalances: realized return "
                f"{self.realized_annual_return:.2%}/yr, vol "
                f"{self.realized_annual_vol:.2%}, Sharpe "
                f"{self.realized_sharpe:.2f}, maxDD {self.max_drawdown:.2%}, "
                f"avg turnover {self.avg_turnover_oneway:.1%}, breaches "
                f"{self.total_breaches}")


def walk_forward_backtest(
    engine: PortfolioEngine,
    prices: pd.DataFrame | None = None,
    k_total: int = 12,
    w_max: float = 0.15,
    w_min: float = 0.02,
    window: int = 252,
    rebalance_every: int = 21,
    risk_free_rate: float = 0.03,
) -> BacktestReport:
    """Run the walk-forward protocol (see module docstring)."""
    if prices is None:
        prices = pd.read_csv(SNAPSHOT_CSV, index_col=0, parse_dates=True)
    rets = prices.pct_change().dropna(how="any")
    dates = rets.index
    if len(dates) < window + rebalance_every:
        raise ValueError("panel too short for the requested window")

    w = None
    daily: list[tuple] = []
    log_rows = []
    turnovers, costs_paid, breaches_total = [], 0.0, 0
    rebalance_points = range(window, len(dates), rebalance_every)

    for n_reb, t in enumerate(rebalance_points):
        est_prices = prices.iloc[t - window:t + 1]        # data up to t only
        md = market_from_prices(est_prices, risk_free_rate=risk_free_rate)
        if w is not None:                                  # carry real book
            md.w_prev[:] = w
        result = engine.run(md, k_total=k_total, w_max=w_max, w_min=w_min,
                            run_id=f"bt{n_reb:03d}")
        breaches_total += sum(0 if b.ok else 1 for b in result.breaches)
        w_new = result.weights
        turnover = float(np.abs(w_new - (w if w is not None else 0)).sum())
        cost = float(md.tc_linear @ np.abs(w_new - (w if w is not None else 0)))
        turnovers.append(turnover / 2.0)                   # one-way
        costs_paid += cost
        log_rows.append({"date": dates[t], "turnover_oneway": turnover / 2,
                         "cost": cost, "positions": result.metrics["num_positions"],
                         "expected_sharpe": result.metrics["sharpe_net"]})
        w = w_new
        # Hold out-of-sample until the next rebalance.
        hold = rets.iloc[t + 1: min(t + 1 + rebalance_every, len(dates))]
        port = hold.to_numpy() @ w
        if len(port):
            port[0] -= cost                                # pay costs at entry
        daily.extend(zip(hold.index, port))
        logger.info("rebalance %d @ %s: turnover %.1f%%, %s",
                    n_reb, dates[t].date(), 50 * turnover,
                    result.summary())

    series = pd.Series(dict(daily), name="portfolio_return").sort_index()
    ann_ret = float(series.mean() * TRADING_DAYS_PER_YEAR)
    ann_vol = float(series.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))
    curve = (1 + series).cumprod()
    mdd = float((1 - curve / curve.cummax()).max())
    return BacktestReport(
        realized_annual_return=ann_ret,
        realized_annual_vol=ann_vol,
        realized_sharpe=(ann_ret - risk_free_rate) / ann_vol if ann_vol > 0 else 0.0,
        max_drawdown=mdd,
        avg_turnover_oneway=float(np.mean(turnovers)),
        total_costs=costs_paid,
        n_rebalances=len(log_rows),
        total_breaches=breaches_total,
        daily_returns=series,
        rebalance_log=pd.DataFrame(log_rows),
    )
