import itertools
import os
import sys

import numpy as np
import pytest
from scipy import stats

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cancellation_tau import (decompose, operator_F, identity, abs_change, signed_change,  # noqa: E402
                              power_mean_change, restricted_signed_relation, tau_b_matrix,
                              null_var_tau_b, conformal_scores, conformal_pvalue, stat_D,
                              build_model, simulate, circular_shift_record)


def _random_changes(rng, m):
    kind = rng.integers(0, 4)
    if kind == 0:
        return rng.uniform(-2, 2, m)
    if kind == 1:
        return np.abs(rng.normal(0, 0.3, m))              # all changes non-negative
    if kind == 2:
        x = rng.uniform(0, 1, m // 2)
        return np.concatenate([x, -x])                    # exact balance
    return np.round(rng.normal(0, 0.2, m), 1)             # many zeros and ties


def test_exact_identity_many_vectors():
    rng = np.random.default_rng(1)
    for _ in range(20000):
        m = int(rng.integers(2, 60))
        d = _random_changes(rng, m)
        r = decompose(d)
        assert r["D"] == pytest.approx(r["abs_dbar"] + r["C"], abs=1e-12)
        assert r["C"] == pytest.approx(r["C_minority"], abs=1e-12)
        sp, sm = r["S_plus"], r["S_minus"]
        assert r["D"] == pytest.approx((sp + sm) / d.size, abs=1e-12)
        assert r["abs_dbar"] == pytest.approx(abs(sp - sm) / d.size, abs=1e-12)
        assert r["C"] == pytest.approx(2 * min(sp, sm) / d.size, abs=1e-12)
        assert r["C"] >= -1e-15 and r["C"] <= r["D"] + 1e-15
        if r["D"] > 0:
            assert -1e-12 <= r["kappa"] <= 1 + 1e-12
            assert r["kappa"] == pytest.approx(1 - r["abs_dbar"] / r["D"], abs=1e-12)


def test_kappa_extremes():
    assert decompose(np.array([0.1, 0.3, 0.0, 0.2]))["kappa"] == pytest.approx(0.0)
    assert decompose(np.array([0.1, -0.1, 0.4, -0.4]))["kappa"] == pytest.approx(1.0)
    assert decompose(np.array([-0.5, -0.1]))["C"] == pytest.approx(0.0)


def test_bounds_from_tau_range():
    rng = np.random.default_rng(2)
    for _ in range(2000):
        x = rng.uniform(-1, 1, 30)
        B = rng.uniform(-1, 1, 30)
        r = decompose(x - B)
        assert 0 <= r["D"] <= 2
        assert r["D"] <= 1 + np.mean(np.abs(B)) + 1e-12


def test_operator_instances_match_direct_computation():
    rng = np.random.default_rng(3)
    Z = rng.poisson(1.0, size=(8, 40)).astype(float)
    T, _ = tau_b_matrix(Z)
    iu = np.triu_indices(8, 1)
    vals = T[iu]
    B = rng.uniform(-0.3, 0.3, vals.size)
    assert operator_F(vals, B, identity) == pytest.approx(vals.mean())
    E = rng.random(vals.size) < 0.4
    assert operator_F(vals[E], B[E], abs_change) == pytest.approx(np.mean(np.abs(vals[E] - B[E])))
    assert operator_F(vals[E], B[E], signed_change) == pytest.approx(vals[E].mean() - B[E].mean())


def test_tau_b_matches_scipy_with_ties():
    rng = np.random.default_rng(4)
    for _ in range(50):
        Z = rng.poisson(0.8, size=(4, 35)).astype(float)
        T, d = tau_b_matrix(Z)
        for i, j in itertools.combinations(range(4), 2):
            if d[i, j]:
                ref = stats.kendalltau(Z[i], Z[j], variant="b").statistic
                assert T[i, j] == pytest.approx(ref, abs=1e-12)


def test_invariance_to_monotone_transforms_and_polarity():
    rng = np.random.default_rng(5)
    Z = rng.poisson(1.2, size=(6, 50)).astype(float)
    Z2 = rng.poisson(1.2, size=(6, 50)).astype(float)
    T1, _ = tau_b_matrix(Z)
    T2, _ = tau_b_matrix(Z2)
    # strictly increasing transform of one stream: nothing changes
    Zi = Z.copy(); Zi[2] = np.exp(Zi[2]) + 3 * Zi[2]
    Ti, _ = tau_b_matrix(Zi)
    assert np.allclose(Ti, T1)
    # polarity flip of module 2 in both windows: D invariant, signed mean not
    Zf, Z2f = Z.copy(), Z2.copy()
    Zf[2] *= -1; Z2f[2] *= -1
    Tf1, _ = tau_b_matrix(Zf)
    Tf2, _ = tau_b_matrix(Z2f)
    iu = np.triu_indices(6, 1)
    d = T2[iu] - T1[iu]
    df = Tf2[iu] - Tf1[iu]
    assert decompose(df)["D"] == pytest.approx(decompose(d)["D"])
    assert not np.isclose(decompose(df)["dbar"], decompose(d)["dbar"])


def test_power_means_and_quadratic_identity():
    rng = np.random.default_rng(6)
    d = rng.normal(0.05, 0.2, 40)
    qs = [1, 1.5, 2, 3, 8]
    vals = [power_mean_change(d, q) for q in qs] + [power_mean_change(d, np.inf)]
    assert all(a <= b + 1e-12 for a, b in zip(vals, vals[1:]))
    assert power_mean_change(d, 2) ** 2 == pytest.approx(d.mean() ** 2 + d.var())


def test_restricted_relation_and_bound():
    rng = np.random.default_rng(7)
    for _ in range(5000):
        n = int(rng.integers(3, 50))
        dP = rng.normal(rng.normal(0, 0.1), 0.2, n)
        inE = rng.random(n) < rng.uniform(0.1, 0.9)
        if inE.sum() == 0:
            inE[0] = True
        r = restricted_signed_relation(dP, inE)
        assert abs(r["mix_identity_error"]) < 1e-12
        assert abs(r["R"]) <= r["bound"] + 1e-12
    r = restricted_signed_relation(rng.normal(0, 1, 10), np.ones(10, bool))
    assert abs(r["R"]) < 1e-12


def test_null_variance_with_ties_against_permutation():
    rng = np.random.default_rng(8)
    x = rng.poisson(0.9, 40).astype(float)
    y = rng.poisson(1.6, 40).astype(float)
    v = null_var_tau_b(x, y)
    sims = np.array([stats.kendalltau(x, rng.permutation(y), variant="b").statistic
                     for _ in range(20000)])
    assert np.var(sims) == pytest.approx(v, rel=0.05)
    xb = (rng.random(60) < 0.3).astype(float)
    yb = (rng.random(60) < 0.5).astype(float)
    assert null_var_tau_b(xb, yb) == pytest.approx(1.0 / 59, rel=1e-9)


def test_conformal_rule_false_alarm_rate():
    rng = np.random.default_rng(9)
    n, m, alpha, fires = 39, 12, 0.05, 0
    trials = 4000
    for _ in range(trials):
        cal = rng.normal(0, 1, (n, m))
        new = rng.normal(0, 1, m)
        sc, s = conformal_scores(cal, new, stat_D)
        fires += conformal_pvalue(sc, s) <= alpha
    assert fires / trials <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / trials)
    assert fires / trials >= alpha - 3 * np.sqrt(alpha * (1 - alpha) / trials)


def test_simulator_polarity_and_surrogate_marginals():
    model = build_model()
    rng = np.random.default_rng(10)
    X = simulate(model, 60, rng)
    from cancellation_tau import window_edge_values
    V, _ = window_edge_values(X, model.edges)
    B = V.mean(axis=0)
    assert np.all(np.sign(B) == model.polarity)
    S = circular_shift_record(X, rng, min_lag=model.window_bins)
    for i in range(model.n_modules):
        assert np.array_equal(np.sort(S[:, i, :].ravel()), np.sort(X[:, i, :].ravel()))
