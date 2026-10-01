"""Reproduce every number, table and figure of the note.

Usage:  python run_all.py [--out ../results] [--reps 200]
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import platform
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cancellation_tau import (build_model, simulate, window_edge_values, decompose,  # noqa: E402
                              conformal_scores, conformal_pvalue, stat_D, stat_abs_mean,
                              analytic_null_guide, circular_shift_record,
                              restricted_signed_relation, power_mean_change)

CONFIG = {
    "master_seed": 20260930,
    "n_modules": 10,
    "n_chords": 6,
    "coupling": 0.5,
    "persist": 0.97,
    "bin_ticks": 10,
    "window_bins": 60,
    "n_cal": 39,
    "n_mon": 5,
    "alpha": 0.05,
    "reps": 200,
    "theta_table": 1.0,
    "gamma_grid": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
    "theta_grid": [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0],
    "pilot_windows": 2000,
    "timecourse_mon": 25,
}


def choose_rewired(model, B_exp):
    """Four concordant and four anti-concordant edges whose expected baselines
    cancel as closely as possible (lexicographically first minimiser)."""
    pos = [e for e in range(len(model.edges)) if model.polarity[e] > 0]
    neg = [e for e in range(len(model.edges)) if model.polarity[e] < 0]
    best = None
    for a in itertools.combinations(pos, 4):
        for b in itertools.combinations(neg, 4):
            val = abs(B_exp[list(a)].sum() + B_exp[list(b)].sum())
            if best is None or val < best[0] - 1e-15:
                best = (val, sorted(a + b))
    return np.array(best[1], int), float(best[0])


def all_pairs(N):
    iu = np.triu_indices(N, 1)
    return np.column_stack(iu)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    ap.add_argument("--reps", type=int, default=CONFIG["reps"])
    args = ap.parse_args()
    cfg = dict(CONFIG, reps=args.reps)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    t0 = time.time()

    model = build_model(seed=cfg["master_seed"], n_modules=cfg["n_modules"], n_chords=cfg["n_chords"],
                        coupling=cfg["coupling"], persist=cfg["persist"],
                        bin_ticks=cfg["bin_ticks"], window_bins=cfg["window_bins"])
    N = model.n_modules
    P = all_pairs(N)
    edge_key = {tuple(e): k for k, e in enumerate(P.tolist())}
    in_E = np.zeros(len(P), bool)
    e_idx = np.array([edge_key[tuple(e)] for e in model.edges.tolist()])
    in_E[e_idx] = True
    mE = len(model.edges)

    # pilot: expected baselines (used only to choose the balanced rewiring set)
    ss = np.random.SeedSequence(cfg["master_seed"])
    s_pilot, s_rep, s_tc = ss.spawn(3)
    Xp = simulate(model, cfg["pilot_windows"], np.random.default_rng(s_pilot))
    Vp, _ = window_edge_values(Xp, model.edges)
    B_exp = Vp.mean(axis=0)
    rewired, imbalance = choose_rewired(model, B_exp)

    conditions = [("none", 0.0, 0.0)]
    conditions += [("coherent", g, 0.0) for g in cfg["gamma_grid"] if g > 0]
    conditions += [("rewire", 0.0, th) for th in cfg["theta_grid"] if th > 0]

    rows = []
    null_rows = []
    surr_rows = []
    n_cal, n_mon, alpha = cfg["n_cal"], cfg["n_mon"], cfg["alpha"]
    crit_rank = int(np.ceil((1 - alpha) * (n_cal + 1)))  # order statistic giving the critical value
    guide_list = []
    rep_seeds = s_rep.spawn(cfg["reps"])
    max_id_err = 0.0
    max_min_err = 0.0
    max_R_excess = -np.inf

    def evaluate(cond, gamma, theta, rep, calP, monP):
        nonlocal max_id_err, max_min_err, max_R_excess
        calE = calP[:, in_E]
        B_P = calP.mean(axis=0)
        B_E = B_P[in_E]
        for w in range(monP.shape[0]):
            newP = monP[w]
            newE = newP[in_E]
            dE = newE - B_E
            dP = newP - B_P
            dec = decompose(dE)
            rel = restricted_signed_relation(dP, in_E)
            scD, sD = conformal_scores(calE, newE, stat_D)
            scE, sE = conformal_scores(calE, newE, stat_abs_mean)
            scP, sP = conformal_scores(calP, newP, stat_abs_mean)
            pD, pE, pP = (conformal_pvalue(scD, sD), conformal_pvalue(scE, sE), conformal_pvalue(scP, sP))
            qD = float(np.sort(scD)[crit_rank - 1])
            qE = float(np.sort(scE)[crit_rank - 1])
            max_id_err = max(max_id_err, abs(dec["D"] - dec["abs_dbar"] - dec["C"]),
                             abs(sD - dec["D"]))
            max_min_err = max(max_min_err, abs(dec["C"] - dec["C_minority"]))
            max_R_excess = max(max_R_excess, abs(rel["R"]) - rel["bound"])
            src = int(dec["argmax"])
            rows.append({
                "condition": cond, "gamma": gamma, "theta": theta, "rep": rep, "window": w,
                "dtau_s_P": rel["dbar_P"], "dbar_E": dec["dbar"], "abs_dbar_E": dec["abs_dbar"],
                "D": dec["D"], "C": dec["C"], "kappa": dec["kappa"],
                "D2": power_mean_change(dE, 2), "Dinf": power_mean_change(dE, np.inf),
                "p_D": pD, "p_E": pE, "p_P": pP, "q_D": qD, "q_E": qE,
                "alarm_D": int(pD <= alpha), "alarm_E": int(pE <= alpha), "alarm_P": int(pP <= alpha),
                "alarm_U": int(pD <= alpha / 2 or pE <= alpha / 2),
                "source_edge": src, "source_in_rewired": int(src in set(rewired.tolist())),
                "R": rel["R"], "R_bound": rel["bound"],
                **{f"delta_e{k}": float(dE[k]) for k in range(mE)},
            })

    for rep, sseq in enumerate(rep_seeds):
        s_cal, s_mon, s_ind, s_sur = sseq.spawn(4)
        cal = simulate(model, n_cal, np.random.default_rng(s_cal))
        calP, _ = window_edge_values(cal, P)
        for cond, gamma, theta in conditions:
            mon = simulate(model, n_mon, np.random.default_rng(s_mon), gamma=gamma,
                           rewire_edges=rewired if theta > 0 else None, theta=theta)
            monP, _ = window_edge_values(mon, P)
            evaluate(cond, gamma, theta, rep, calP, monP)
        # independent (rate-matched) null: calibration and monitoring both independent
        ind = simulate(model, n_cal + n_mon, np.random.default_rng(s_ind), independent=True)
        indP, _ = window_edge_values(ind, P)
        evaluate("independent", 0.0, 0.0, rep, indP[:n_cal], indP[n_cal:])
        if rep < 50:
            guide_list.append(analytic_null_guide(ind[:n_cal], model.edges, n_cal))
        # circular-shift surrogates of the coupled calibration record: no-dependence floor
        sur = circular_shift_record(cal, np.random.default_rng(s_sur), min_lag=model.window_bins)
        surP, _ = window_edge_values(sur, P)
        sE = surP[:, in_E]
        loo = (n_cal / (n_cal - 1.0)) * (sE - sE.mean(axis=0))
        for w in range(n_cal):
            d = decompose(loo[w])
            surr_rows.append({"rep": rep, "window": w, "D": d["D"], "abs_dbar_E": d["abs_dbar"],
                              "C": d["C"], "kappa": d["kappa"]})
        # baseline realism check: calibration mean |B_e| vs its surrogate
        null_rows.append({"rep": rep, "mean_abs_B_E": float(np.abs(calP[:, in_E].mean(0)).mean()),
                          "mean_abs_B_E_surrogate": float(np.abs(sE.mean(0)).mean()),
                          "tau_s_P_cal": float(calP.mean())})
        if (rep + 1) % 25 == 0:
            print(f"replicate {rep + 1}/{cfg['reps']}  ({time.time() - t0:.0f} s)", flush=True)

    import csv

    def write_csv(path, recs):
        with open(path, "w", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
            wr.writeheader()
            wr.writerows(recs)

    write_csv(os.path.join(out, "windows.csv"), rows)
    write_csv(os.path.join(out, "surrogate_windows.csv"), surr_rows)
    write_csv(os.path.join(out, "calibration_baselines.csv"), null_rows)

    # ---------------- summaries ----------------
    import pandas_free_summary as S  # local helper, no pandas dependency
    table, power = S.summarise(rows, cfg, mE, rewired)
    write_csv(os.path.join(out, "table1.csv"), table)
    write_csv(os.path.join(out, "power_curve.csv"), power)

    guide = {k: float(np.mean([g[k] for g in guide_list])) for k in guide_list[0]}
    ind_rows = [r for r in rows if r["condition"] == "independent"]
    none_rows = [r for r in rows if r["condition"] == "none"]
    nullcheck = {
        "analytic_guide_mean_over_50_reps": guide,
        "independent_empirical": {
            "mean_D": float(np.mean([r["D"] for r in ind_rows])),
            "sd_D": float(np.std([r["D"] for r in ind_rows])),
            "mean_abs_dbar_E": float(np.mean([r["abs_dbar_E"] for r in ind_rows])),
            "mean_kappa": float(np.mean([r["kappa"] for r in ind_rows])),
            "median_q_D": float(np.median([r["q_D"] for r in ind_rows])),
        },
        "circular_shift_surrogate": {
            "mean_D": float(np.mean([r["D"] for r in surr_rows]) * np.sqrt(((1 + 1 / n_cal) / (1 + 1 / (n_cal - 1))))),
            "mean_D_loo_raw": float(np.mean([r["D"] for r in surr_rows])),
            "mean_kappa": float(np.mean([r["kappa"] for r in surr_rows])),
        },
        "coupled_no_change": {
            "mean_D": float(np.mean([r["D"] for r in none_rows])),
            "mean_kappa": float(np.mean([r["kappa"] for r in none_rows])),
            "median_q_D": float(np.median([r["q_D"] for r in none_rows])),
        },
        "calibration_baselines": {
            "mean_abs_B_E": float(np.mean([r["mean_abs_B_E"] for r in null_rows])),
            "mean_abs_B_E_surrogate": float(np.mean([r["mean_abs_B_E_surrogate"] for r in null_rows])),
            "mean_tau_s_P_cal": float(np.mean([r["tau_s_P_cal"] for r in null_rows])),
        },
        "identity_checks": {
            "max_abs_error_D_eq_absdbar_plus_C_and_score": max_id_err,
            "max_abs_error_C_eq_minority_mass": max_min_err,
            "max_excess_R_over_bound": float(max_R_excess),
        },
    }
    with open(os.path.join(out, "null_and_identity_checks.json"), "w") as fh:
        json.dump(nullcheck, fh, indent=2)

    # time course for Fig. 1b (one realisation, balanced rewiring theta = 1)
    tc_seed_cal, tc_seed_mon = s_tc.spawn(2)
    tcal = simulate(model, n_cal, np.random.default_rng(tc_seed_cal))
    tmon = simulate(model, cfg["timecourse_mon"], np.random.default_rng(tc_seed_mon),
                    rewire_edges=rewired, theta=1.0)
    tcalE, _ = window_edge_values(tcal, model.edges)
    tmonE, _ = window_edge_values(tmon, model.edges)
    B = tcalE.mean(axis=0)
    loo = (n_cal / (n_cal - 1.0)) * (tcalE - B)
    tc = []
    for w in range(n_cal):
        d = decompose(loo[w])
        tc.append({"window": w - n_cal + 1, "phase": "calibration", "tau_s_E": float(tcalE[w].mean()),
                   "D": d["D"], "abs_dbar_E": d["abs_dbar"], "C": d["C"], "kappa": d["kappa"]})
    for w in range(cfg["timecourse_mon"]):
        d = decompose(tmonE[w] - B)
        tc.append({"window": w + 1, "phase": "monitoring", "tau_s_E": float(tmonE[w].mean()),
                   "D": d["D"], "abs_dbar_E": d["abs_dbar"], "C": d["C"], "kappa": d["kappa"]})
    write_csv(os.path.join(out, "timecourse.csv"), tc)
    locD = [r["D"] for r in tc if r["phase"] == "calibration"]
    locS = [abs(r["tau_s_E"] - float(B.mean())) * n_cal / (n_cal - 1) for r in tc if r["phase"] == "calibration"]
    tc_meta = {"B_mean": float(B.mean()), "q_D_cal": float(np.sort(locD)[crit_rank - 2]),
               "q_s_cal": float(np.sort(locS)[crit_rank - 2]),
               "note": "display thresholds: second-largest leave-one-out calibration score"}

    meta = {
        "config": cfg,
        "edges": model.edges.tolist(), "polarity": model.polarity.tolist(), "rates": model.rates.tolist(),
        "degree": model.degree.tolist(), "n_pairs": int(len(P)), "n_edges": int(mE),
        "expected_baseline_pilot": B_exp.tolist(), "rewired_edges": rewired.tolist(),
        "rewired_expected_imbalance": imbalance,
        "critical_rank": crit_rank, "timecourse": tc_meta,
        "python": platform.python_version(), "numpy": np.__version__,
        "runtime_s": round(time.time() - t0, 1),
    }
    with open(os.path.join(out, "run_metadata.json"), "w") as fh:
        json.dump(meta, fh, indent=2)
    print(json.dumps(nullcheck, indent=2))
    for r in table:
        print(r)
    import make_figure
    sys.argv = [sys.argv[0], "--res", out]
    make_figure.main()
    print(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
