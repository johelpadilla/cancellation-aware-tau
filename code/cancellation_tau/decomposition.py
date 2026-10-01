"""Pairwise-matrix operator F(S, f) and the cancellation decomposition.

Notation (per window t):
    tau_b(p, t)  pairwise concordance of pair p = (i, j)
    B_p          calibration baseline of pair p (mean over calibration windows)
    Delta_e      tau_b(e, t) - B_e for e in a fixed edge set E

    F(S, f)      = mean_{p in S} f(tau_b(p, t), B_p)
    tau_s        = F(P, (x, B) -> x)            signed Systemic Tau, all pairs P
    D_E          = F(E, (x, B) -> |x - B|)      mean absolute change on E
    dbar_E       = F(E, (x, B) -> x - B)        signed mean change on E
    C_E          = D_E - |dbar_E| = (2/|E|) * min(S+, S-)
    kappa_E      = C_E / D_E                     cancellation fraction in [0, 1]
"""
from __future__ import annotations

import numpy as np


def operator_F(values: np.ndarray, baseline: np.ndarray, f) -> float:
    """F(S, f): mean over the pairs of S of f(tau_b(p), B_p).

    `values` and `baseline` are 1-D arrays already restricted to S."""
    values = np.asarray(values, float)
    baseline = np.asarray(baseline, float)
    return float(np.mean(f(values, baseline)))


def identity(x, B):
    return x


def signed_change(x, B):
    return x - B


def abs_change(x, B):
    return np.abs(x - B)


def decompose(delta: np.ndarray) -> dict:
    """Exact decomposition of the mean absolute change of a vector of edge changes.

    Returns D, dbar, abs_dbar, C, kappa, S_plus, S_minus, C_minority, argmax.
    C is computed as D - |dbar|; C_minority = (2/|E|) * sum of |Delta_e| over the
    edges whose change has the sign opposite to dbar (the two agree exactly)."""
    d = np.asarray(delta, float).ravel()
    m = d.size
    if m == 0:
        raise ValueError("empty edge set")
    s_plus = float(d[d > 0].sum())
    s_minus = float(-d[d < 0].sum())
    D = float(np.abs(d).mean())
    dbar = float(d.mean())
    C = D - abs(dbar)
    if dbar > 0:
        minority = s_minus
    elif dbar < 0:
        minority = s_plus
    else:
        minority = s_plus  # s_plus == s_minus
    C_min = 2.0 * minority / m
    kappa = C / D if D > 0 else float("nan")
    return {"D": D, "dbar": dbar, "abs_dbar": abs(dbar), "C": C,
            "C_minority": C_min, "kappa": kappa, "S_plus": s_plus,
            "S_minus": s_minus, "argmax": int(np.argmax(np.abs(d)))}


def power_mean_change(delta: np.ndarray, q: float) -> float:
    """D_q = (mean |Delta_e|^q)^(1/q); q = inf gives max |Delta_e|."""
    a = np.abs(np.asarray(delta, float))
    if np.isinf(q):
        return float(a.max())
    return float(np.mean(a ** q) ** (1.0 / q))


def restricted_signed_relation(delta_P: np.ndarray, in_E: np.ndarray) -> dict:
    """Relation between the signed change on all pairs P and the decomposition on E.

    dbar_P = rho * dbar_E + (1 - rho) * dbar_{P\\E},  rho = |E|/|P|, and
    D_E = |dbar_P| + C_E + R  with  |R| <= (1 - rho) |dbar_{P\\E} - dbar_E|."""
    delta_P = np.asarray(delta_P, float)
    in_E = np.asarray(in_E, bool)
    dE = delta_P[in_E]
    dN = delta_P[~in_E]
    rho = in_E.mean()
    dec = decompose(dE)
    dbar_P = float(delta_P.mean())
    dbar_N = float(dN.mean()) if dN.size else 0.0
    R = dec["D"] - abs(dbar_P) - dec["C"]
    bound = (1 - rho) * abs(dbar_N - dec["dbar"])
    return {"rho": float(rho), "dbar_P": dbar_P, "dbar_E": dec["dbar"],
            "dbar_notE": dbar_N, "R": float(R), "bound": float(bound),
            "mix_identity_error": float(dbar_P - (rho * dec["dbar"] + (1 - rho) * dbar_N))}
