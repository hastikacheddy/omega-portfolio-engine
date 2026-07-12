"""Engine contract: compliance gate, manifests, goals."""
import json

import numpy as np

from omega_engine import ADMMConfig, PortfolioEngine
from omega_engine.data_gen import generate_market_data
from omega_engine.metrics import total_breaches


def test_run_zero_breaches_and_manifest(tmp_path):
    md = generate_market_data(n_assets=30, n_sectors=5, seed=7)
    engine = PortfolioEngine(config=ADMMConfig(max_iter=5, seed=7),
                             output_dir=tmp_path)
    result = engine.run(md, k_total=8, w_max=0.20, w_min=0.02)
    assert total_breaches(result.breaches) == 0
    assert int(result.support.sum()) == 8
    assert abs(result.weights.sum() - 1.0) < 1e-6
    manifest = json.loads((tmp_path / f"{result.run_id}.manifest.json")
                          .read_text(encoding="utf-8"))
    assert manifest["hard_breaches"] == 0
    assert manifest["inputs"]["sha_mu"] and manifest["inputs"]["sha_sigma"]
    assert len(manifest["clusters"]) >= 1
    assert (tmp_path / f"{result.run_id}.weights.csv").exists()


def test_goals_active_income_and_cvar():
    md = generate_market_data(n_assets=30, n_sectors=5, seed=7)
    cfg = ADMMConfig(max_iter=5, seed=7, income_floor=0.02, cvar_weight=8.0)
    engine = PortfolioEngine(config=cfg)
    result = engine.run(md, k_total=8, w_max=0.20, w_min=0.02)
    assert total_breaches(result.breaches) == 0
    if not result.manifest["income_floor_relaxed"]:
        assert result.metrics["portfolio_yield"] >= 0.02 - 1e-6


def test_quantum_flag_smoke():
    md = generate_market_data(n_assets=12, n_sectors=3, seed=3)
    cfg = ADMMConfig(max_iter=3, quantum_last_n=1, reps=1, shots=256,
                     cobyla_maxiter=8, seed=3)
    engine = PortfolioEngine(config=cfg, quantum_enabled=True)
    result = engine.run(md, k_total=4, w_max=0.4, w_min=0.02)
    methods = [m for c in result.manifest["clusters"] for m in c["z_methods"]]
    assert any(m.startswith("qaoa") for m in methods)
    assert total_breaches(result.breaches) == 0
