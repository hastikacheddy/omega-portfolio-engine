"""Walk-forward backtest smoke: out-of-sample replay, zero breaches."""
import numpy as np

from omega_engine import ADMMConfig, PortfolioEngine
from omega_engine.backtest import walk_forward_backtest


def test_walk_forward_snapshot():
    engine = PortfolioEngine(config=ADMMConfig(max_iter=4, seed=7))
    report = walk_forward_backtest(engine, k_total=10, w_max=0.15,
                                   w_min=0.02, window=252,
                                   rebalance_every=63)   # quarterly, fast
    assert report.n_rebalances >= 3
    assert report.total_breaches == 0
    assert np.isfinite(report.realized_sharpe)
    assert 0 <= report.max_drawdown < 0.60
    assert (report.rebalance_log["positions"] == 10).all()
