"""Physics/encoding invariants — the claims the engine's guarantees rest on."""
import math

import numpy as np
import pytest
from qiskit.quantum_info import Statevector

from omega_engine.data_gen import generate_market_data
from omega_engine.hrp_clustering import mixer_spanning_tree
from omega_engine.quantum_z_step import (
    binary_objective, build_tree_qaoa_ansatz, dicke_state_circuit, qubo_to_ising,
)


def test_qubo_to_ising_exact_all_states():
    rng = np.random.default_rng(0)
    n = 5
    Q = rng.standard_normal((n, n))
    Q = 0.5 * (Q + Q.T)
    a = rng.standard_normal(n)
    h, J, off = qubo_to_ising(Q, a)
    for b in range(2**n):
        z = np.array([(b >> i) & 1 for i in range(n)])
        s = 1 - 2 * z
        ising = off + h @ s + sum(J[i, j] * s[i] * s[j]
                                  for i in range(n) for j in range(i + 1, n))
        assert abs(ising - binary_objective(z, Q, a)) < 1e-9


def test_dicke_state_uniform_over_shell():
    sv = Statevector(dicke_state_circuit(6, 2))
    probs = np.abs(sv.data) ** 2
    for b in range(64):
        expect = 1 / math.comb(6, 2) if bin(b).count("1") == 2 else 0.0
        assert probs[b] == pytest.approx(expect, abs=1e-10)


def test_ansatz_conserves_hamming_weight():
    md = generate_market_data(n_assets=7, n_sectors=3, seed=5)
    topo = mixer_spanning_tree(md.correlation(), 3)
    h, J, _ = qubo_to_ising(5.0 * md.sigma, -md.mu)
    qc = build_tree_qaoa_ansatz(h, J, 2, topo, reps=1, measure=False)
    rng = np.random.default_rng(1)
    bound = qc.assign_parameters(dict(zip(
        sorted(qc.parameters, key=lambda p: p.name),
        rng.uniform(-1.5, 1.5, len(qc.parameters)))))
    probs = np.abs(Statevector(bound).data) ** 2
    leak = sum(p for b, p in enumerate(probs) if bin(b).count("1") != 2)
    assert leak < 1e-10
