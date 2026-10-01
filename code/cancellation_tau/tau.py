"""Kendall tau_b on a common binned event index, and its null variance with ties.

Streams are arrays of shape (N, W): N modules, W bins of a common event index
(for example, event counts per bin).  For a pair of streams, tau_b is the cosine
between their sign vectors  s_i[k, l] = sgn(z_i(l) - z_i(k)),  k < l,  which is
Kendall's tie-corrected coefficient.  A stream that is constant within the
window has a zero sign vector; tau_b is then undefined and is set to 0, and the
definedness mask is returned alongside the matrix.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np


@lru_cache(maxsize=16)
def _pair_index(W: int):
    return np.triu_indices(W, 1)


def sign_vectors(Z: np.ndarray) -> np.ndarray:
    Z = np.asarray(Z, dtype=float)
    k, l = _pair_index(Z.shape[1])
    return np.sign(Z[:, l] - Z[:, k])


def tau_b_matrix(Z: np.ndarray):
    """Pairwise Kendall tau_b matrix T (N x N) and boolean definedness mask."""
    S = sign_vectors(Z)
    G = S @ S.T
    nrm = np.sqrt(np.clip(np.diag(G), 0.0, None))
    den = np.outer(nrm, nrm)
    defined = den > 0
    T = np.zeros_like(G)
    np.divide(G, den, out=T, where=defined)
    np.fill_diagonal(T, 1.0)
    return T, defined


def _tie_sums(x: np.ndarray):
    _, t = np.unique(x, return_counts=True)
    t = t.astype(float)
    return (np.sum(t * (t - 1)), np.sum(t * (t - 1) * (t - 2)),
            np.sum(t * (t - 1) * (2 * t + 5)))


def null_var_tau_b(x, y) -> float:
    """Variance of tau_b under random permutation (independence), conditional on
    the tie structure of both streams (Kendall 1945).  Returns nan if undefined.

    Var(S) = [v0 - vt - vu]/18 + [sum t(t-1)(t-2)][sum u(u-1)(u-2)] / [9n(n-1)(n-2)]
             + [sum t(t-1)][sum u(u-1)] / [2n(n-1)],
    Var(tau_b) = Var(S) / [(n0 - n1)(n0 - n2)].
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = float(len(x))
    a1, a2, a3 = _tie_sums(x)
    b1, b2, b3 = _tie_sums(y)
    v0 = n * (n - 1) * (2 * n + 5)
    var_s = (v0 - a3 - b3) / 18.0
    var_s += a2 * b2 / (9.0 * n * (n - 1) * (n - 2))
    var_s += a1 * b1 / (2.0 * n * (n - 1))
    n0 = n * (n - 1) / 2.0
    den = (n0 - a1 / 2.0) * (n0 - b1 / 2.0)
    if den <= 0:
        return float("nan")
    return float(var_s / den)


def untied_null_var(W: int) -> float:
    """Kendall's classical null variance for untied series: 2(2W+5)/(9W(W-1))."""
    return 2.0 * (2 * W + 5) / (9.0 * W * (W - 1))


def autocorr(x: np.ndarray, max_lag: int) -> np.ndarray:
    """Sample autocorrelations r(1..max_lag) of a 1-D series (biased estimator)."""
    x = np.asarray(x, float) - np.mean(x)
    v = np.dot(x, x)
    if v == 0:
        return np.zeros(max_lag)
    n = len(x)
    return np.array([np.dot(x[:n - k], x[k:]) / v for k in range(1, max_lag + 1)])
