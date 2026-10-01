"""Summary statistics for Table 1 and the detection curves (no pandas needed)."""
from __future__ import annotations

import numpy as np


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (float(c - h), float(c + h))


def _summ(sel, mE, rewired, label):
    arr = lambda k: np.array([r[k] for r in sel], float)  # noqa: E731
    n = len(sel)
    out = {"scenario": label, "n_windows": n}
    for k in ["dtau_s_P", "dbar_E", "D", "C", "kappa", "q_D"]:
        v = arr(k)
        out[f"{k}_mean"] = float(np.nanmean(v))
        out[f"{k}_sd"] = float(np.nanstd(v))
    for k in ["alarm_D", "alarm_E", "alarm_P", "alarm_U"]:
        kk = int(arr(k).sum())
        lo, hi = wilson(kk, n)
        out[f"{k}_rate"] = kk / n
        out[f"{k}_lo"] = lo
        out[f"{k}_hi"] = hi
    alarms = [r for r in sel if r["alarm_D"]]
    out["source_hit_rate"] = (float(np.mean([r["source_in_rewired"] for r in alarms]))
                              if alarms else float("nan"))
    out["n_alarms_D"] = len(alarms)
    D = np.array([[r[f"delta_e{e}"] for e in range(mE)] for r in sel])
    out["effect_mean_abs_expected_change"] = float(np.mean(np.abs(D.mean(axis=0))))
    return out


def summarise(rows, cfg, mE, rewired):
    by = {}
    for r in rows:
        by.setdefault((r["condition"], r["gamma"], r["theta"]), []).append(r)
    rew = _summ(by[("rewire", 0.0, cfg["theta_table"])], mE, rewired, "c_balanced_rewiring")
    # coherent drive for the table: the grid value whose mean absolute expected edge
    # change is closest to that of the balanced rewiring (matched effect size)
    cands = [(abs(_summ(by[("coherent", g, 0.0)], mE, rewired, "")["effect_mean_abs_expected_change"]
                  - rew["effect_mean_abs_expected_change"]), g) for g in cfg["gamma_grid"] if g > 0]
    g_star = min(cands)[1]
    coh = _summ(by[("coherent", g_star, 0.0)], mE, rewired, "b_coherent_shift")
    coh["gamma"] = g_star
    table = [
        _summ(by[("none", 0.0, 0.0)], mE, rewired, "a_no_change"),
        coh,
        rew,
        _summ(by[("independent", 0.0, 0.0)], mE, rewired, "d_independent_null"),
    ]
    for t in table:
        t.setdefault("gamma", 0.0)
    power = []
    for g in cfg["gamma_grid"]:
        key = ("none", 0.0, 0.0) if g == 0 else ("coherent", g, 0.0)
        s = _summ(by[key], mE, rewired, "coherent")
        s["magnitude"] = g
        power.append(s)
    for th in cfg["theta_grid"]:
        key = ("none", 0.0, 0.0) if th == 0 else ("rewire", 0.0, th)
        s = _summ(by[key], mE, rewired, "balanced")
        s["magnitude"] = th
        power.append(s)
    return table, power
