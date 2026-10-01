"""Calibration of the alarm: window matrices, baselines, conformal thresholds,
and the analytical no-dependence guide for D and kappa."""
from __future__ import annotations

import numpy as np

from .tau import tau_b_matrix, null_var_tau_b, autocorr


def window_edge_values(counts: np.ndarray, pairs: np.ndarray):
    """tau_b of the given pairs for every window.  counts: (n_windows, N, W)."""
    out = np.empty((counts.shape[0], len(pairs)))
    undef = np.empty(counts.shape[0])
    iu = (pairs[:, 0], pairs[:, 1])
    for w in range(counts.shape[0]):
        T, d = tau_b_matrix(counts[w])
        out[w] = T[iu]
        undef[w] = 1.0 - d[iu].mean()
    return out, undef


def conformal_scores(cal: np.ndarray, new: np.ndarray, stat) -> tuple[np.ndarray, float]:
    """Full-conformal scores for a monitored window.

    cal: (n, m) calibration window values; new: (m,) monitored window.
    For each of the n + 1 windows the baseline is the mean of the other n; the
    score is stat(values - baseline).  For the monitored window this baseline is
    exactly the calibration baseline B.  Returns (calibration scores, new score)."""
    allw = np.vstack([cal, new[None, :]])
    n1 = allw.shape[0]
    tot = allw.sum(axis=0)
    base = (tot[None, :] - allw) / (n1 - 1)
    sc = np.array([stat(allw[k] - base[k]) for k in range(n1)])
    return sc[:-1], float(sc[-1])


def conformal_pvalue(cal_scores: np.ndarray, new_score: float) -> float:
    return (1.0 + np.sum(cal_scores >= new_score)) / (len(cal_scores) + 1.0)


def stat_D(delta):
    return float(np.mean(np.abs(delta)))


def stat_abs_mean(delta):
    return float(abs(np.mean(delta)))


def analytic_null_guide(cal_counts: np.ndarray, pairs: np.ndarray, n_cal: int,
                        max_lag: int = 10) -> dict:
    """No-dependence guide for D and kappa.

    Per edge: sigma_e^2 = mean over calibration windows of the tie-conditional
    permutation variance of tau_b, inflated by the Bartlett-type factor
    f_e = 1 + 2 sum_k r_i(k) r_j(k) for serial correlation of the binned streams.
    The monitored change has variance sigma_e^2 (1 + 1/n_cal).  Then
        E0[D]      ~ sqrt(2/pi) * mean_e sigma_Delta,e
        E0|dbar|   ~ sqrt(2/pi) * sqrt(sum_e sigma_Delta,e^2) / |E|
        kappa0     ~ 1 - sqrt(sum sigma^2) / sum sigma   (~ 1 - |E|^-1/2)."""
    nW, N, W = cal_counts.shape
    v = np.zeros(len(pairs))
    for w in range(nW):
        for k, (i, j) in enumerate(pairs):
            vv = null_var_tau_b(cal_counts[w, i], cal_counts[w, j])
            v[k] += 0.0 if np.isnan(vv) else vv
    v /= nW
    series = np.transpose(cal_counts, (1, 0, 2)).reshape(N, nW * W)
    r = np.array([autocorr(series[i], max_lag) for i in range(N)])
    f = np.array([1.0 + 2.0 * np.dot(r[i], r[j]) for i, j in pairs])
    sig_perm = np.sqrt(v)
    sig_delta = np.sqrt(v * f * (1.0 + 1.0 / n_cal))
    sig_delta_perm = np.sqrt(v * (1.0 + 1.0 / n_cal))
    c = np.sqrt(2.0 / np.pi)
    m = len(pairs)
    ED = c * sig_delta.mean()
    Edbar = c * np.sqrt(np.sum(sig_delta ** 2)) / m
    sdD = np.sqrt((1 - 2 / np.pi) * np.sum(sig_delta ** 2)) / m
    return {"sigma_perm_mean": float(sig_perm.mean()),
            "inflation_mean": float(f.mean()),
            "ED0_perm_only": float(c * sig_delta_perm.mean()),
            "ED0": float(ED), "sdD0": float(sdD), "Eabs_dbar0": float(Edbar),
            "kappa0": float(1.0 - np.sqrt(np.sum(sig_delta ** 2)) / np.sum(sig_delta)),
            "kappa0_homog": float(1.0 - 1.0 / np.sqrt(m))}


def circular_shift_record(counts: np.ndarray, rng, min_lag: int) -> np.ndarray:
    """Circular-shift surrogate of a multi-window record.

    counts: (n_windows, N, W).  The record of each module (concatenated over
    windows) is rotated by an independent lag in [min_lag, L - min_lag] (module 0
    is kept fixed).  Marginals and cyclic autocorrelation are preserved and
    cross-module alignment is destroyed."""
    nW, N, W = counts.shape
    rec = np.transpose(counts, (1, 0, 2)).reshape(N, nW * W).copy()
    L = nW * W
    for i in range(1, N):
        rec[i] = np.roll(rec[i], int(rng.integers(min_lag, L - min_lag + 1)))
    return np.transpose(rec.reshape(N, nW, W), (1, 0, 2))
