"""OMEGA Portfolio Engine — production-hardened hybrid portfolio construction.

Deployable classical spine (HRP decomposition, ADMM coordination, convex
allocation with hard compliance gating) with the quantum QAOA+ z-update as a
feature-flagged, fully-fallback-protected module.
"""

__version__ = "0.1.0"

from .admm_coordinator import ADMMConfig  # noqa: F401
from .engine import EngineComplianceError, EngineResult, PortfolioEngine  # noqa: F401
