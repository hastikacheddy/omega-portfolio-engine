"""
Engine facade: one governed entry point around the pipeline.
============================================================

Production behaviors enforced here (not in the research dashboard):

* **Compliance gate** — a run that produces ANY hard-guardrail breach raises
  :class:`EngineComplianceError` instead of returning weights.  The engine
  can be wrong about quality; it is never allowed to emit a non-compliant
  book.  (By construction this should be unreachable — the gate exists so
  that a future regression fails loudly, not silently.)
* **Quantum is feature-flagged, default OFF.**  At today's cluster sizes
  (≤ 20 assets) the exact classical z-update is the same argmin, faster.
  ``quantum_enabled=True`` exercises the QAOA+ path (with its automatic
  classical fail-safe) — the deployment posture for when sub-problem sizes
  cross the enumeration wall (~30+ assets) or a QPU backend is attached.
* **Audit manifest** — every run emits a JSON manifest: engine/config
  versions, SHA-256 hashes of the inputs (μ, Σ, previous book), per-cluster
  ADMM diagnostics, the full breach audit, metrics, and timings.  If
  ``output_dir`` is set, the manifest and weights are persisted per run_id.
* **Structured logging** via the ``omega.engine`` logger.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
import platform
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import admm_coordinator as _admm
from .admm_coordinator import ADMMConfig, solve_universe
from .hrp_clustering import build_cluster_plan
from .metrics import (
    compute_metrics, constraint_breach_audit, max_drawdown, scenario_cvar,
    total_breaches,
)

logger = logging.getLogger("omega.engine")

__all__ = ["PortfolioEngine", "EngineResult", "EngineComplianceError"]


class EngineComplianceError(RuntimeError):
    """Raised when a produced book fails the hard-guardrail audit.

    Production contract: no weights leave the engine with breaches > 0."""


def _sha(arr: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()[:16]


@dataclass
class EngineResult:
    """Weights + full audit trail for one governed run."""
    run_id: str
    weights: np.ndarray
    support: np.ndarray
    metrics: dict
    breaches: list
    manifest: dict
    elapsed_s: float
    manifest_path: str | None = None

    def summary(self) -> str:
        m = self.metrics
        return (f"run {self.run_id}: {m['num_positions']} positions, "
                f"Sharpe(net)={m['sharpe_net']:.2f}, vol={m['volatility']:.2%}, "
                f"breaches=0, {self.elapsed_s:.1f}s")


class PortfolioEngine:
    """Governed portfolio construction engine (see module docstring)."""

    def __init__(
        self,
        config: ADMMConfig | None = None,
        quantum_enabled: bool = False,
        output_dir: str | Path | None = None,
        cluster_max_size: int = 20,
    ) -> None:
        cfg = config or ADMMConfig()
        if not quantum_enabled:
            cfg = dataclasses.replace(cfg, quantum_last_n=0)
        self.config = cfg
        self.quantum_enabled = quantum_enabled
        self.cluster_max_size = cluster_max_size
        self.output_dir = Path(output_dir) if output_dir else None

    def run(self, md, k_total: int, w_max: float = 0.10, w_min: float = 0.01,
            run_id: str | None = None) -> EngineResult:
        """Construct one compliant book from a market object.

        ``md`` is any :class:`omega_engine.data_gen.OmegaMarketData`
        (synthetic, snapshot, or built from a live risk model upstream).
        Raises :class:`EngineComplianceError` on any hard breach.
        """
        run_id = run_id or uuid.uuid4().hex[:12]
        t0 = time.perf_counter()
        logger.info("run %s: N=%d K=%d quantum=%s", run_id, md.n_assets,
                    k_total, self.quantum_enabled)

        plan = build_cluster_plan(md.sigma, corr=md.correlation(),
                                  max_size=self.cluster_max_size)
        scen = md.scenario_matrix() if self.config.cvar_weight > 0 else None
        res = solve_universe(md, plan, k_total=k_total, w_max_global=w_max,
                             w_min_global=w_min, config=self.config,
                             scenario_matrix=scen)

        metrics = compute_metrics(res.weights, md.mu, md.sigma,
                                  md.risk_free_rate, md.tc_linear, md.w_prev,
                                  yields=md.asset_yields)
        metrics["max_drawdown_sim"] = max_drawdown(res.weights, md.returns)
        metrics["scenario_cvar"] = scenario_cvar(
            res.weights, md.scenario_matrix(), self.config.cvar_alpha)
        breaches = constraint_breach_audit(
            res.weights, k_target=k_total, w_max=w_max,
            sectors=md.sectors, sector_cap=self.config.sector_cap,
            yields=md.asset_yields,
            income_floor=(None if res.income_floor_relaxed
                          else self.config.income_floor))
        n_breach = total_breaches(breaches)
        elapsed = time.perf_counter() - t0

        manifest = {
            "run_id": run_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "engine_version": __import__("omega_engine").__version__,
            "python": platform.python_version(),
            "quantum_enabled": self.quantum_enabled,
            "config": dataclasses.asdict(self.config),
            "inputs": {"n_assets": md.n_assets, "k_total": k_total,
                       "w_max": w_max, "w_min": w_min,
                       "sha_mu": _sha(md.mu), "sha_sigma": _sha(md.sigma),
                       "sha_w_prev": _sha(md.w_prev), "data_seed": md.seed},
            "clusters": [{"id": cs.cluster_id, "size": len(cs.asset_idx),
                          "k": cs.k, "iterations": cs.iterations,
                          "converged": cs.converged,
                          "fallbacks": cs.fallbacks,
                          "z_methods": cs.z_methods,
                          "final_primal_residual": cs.primal_residuals[-1],
                          } for cs in res.cluster_solutions],
            "income_floor_relaxed": res.income_floor_relaxed,
            "breach_audit": [dataclasses.asdict(b) for b in breaches],
            "hard_breaches": n_breach,
            "metrics": {k: (None if isinstance(v, float) and np.isnan(v) else v)
                        for k, v in metrics.items()},
            "elapsed_s": round(elapsed, 3),
        }

        if n_breach > 0:  # unreachable by construction; loud if regressed
            logger.error("run %s FAILED compliance gate: %d breaches",
                         run_id, n_breach)
            raise EngineComplianceError(
                f"run {run_id}: {n_breach} hard-guardrail breach(es) — "
                f"weights withheld. Audit: "
                + "; ".join(f"{b.name}={b.value:.4f} vs {b.bound:.4f}"
                            for b in breaches if not b.ok))

        manifest_path = None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = self.output_dir / f"{run_id}.manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2),
                                     encoding="utf-8")
            np.savetxt(self.output_dir / f"{run_id}.weights.csv",
                       np.column_stack([np.arange(md.n_assets), res.weights]),
                       delimiter=",", header="asset_index,weight", fmt="%.10g",
                       comments="")
            logger.info("run %s persisted to %s", run_id, manifest_path)

        return EngineResult(run_id=run_id, weights=res.weights,
                            support=res.support, metrics=metrics,
                            breaches=breaches, manifest=manifest,
                            elapsed_s=elapsed,
                            manifest_path=str(manifest_path) if manifest_path else None)
