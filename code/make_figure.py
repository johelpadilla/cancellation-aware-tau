"""Figure 1 from the CSV/JSON outputs of run_all.py."""
from __future__ import annotations

import argparse
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

COL = {"none": "#8a8a8a", "coherent": "#2b5d9b", "rewire": "#d0632b", "independent": "#6a4c93"}
LAB = {"none": "No change", "coherent": "Coherent shift", "rewire": "Balanced rewiring",
       "independent": "Independent null"}


def _font():
    for name in ["Arial", "Liberation Sans", "Arimo", "Nimbus Sans", "DejaVu Sans"]:
        try:
            font_manager.findfont(name, fallback_to_default=False)
            return name
        except Exception:
            continue
    return "DejaVu Sans"


def read_csv(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default=os.path.join(HERE, "..", "results"))
    args = ap.parse_args()
    res = os.path.abspath(args.res)
    meta = json.load(open(os.path.join(res, "run_metadata.json")))
    table = read_csv(os.path.join(res, "table1.csv"))
    g_star = float(table[1]["gamma"])
    th_star = meta["config"]["theta_table"]
    rows = read_csv(os.path.join(res, "windows.csv"))
    power = read_csv(os.path.join(res, "power_curve.csv"))
    tc = read_csv(os.path.join(res, "timecourse.csv"))

    plt.rcParams.update({
        "font.family": _font(), "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7,
        "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.2,
        "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5, "axes.spines.top": False,
        "axes.spines.right": False, "mathtext.fontset": "dejavusans", "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })
    fig = plt.figure(figsize=(7.2, 2.55))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.0, 1.28, 1.0], height_ratios=[0.8, 1.6],
                          left=0.065, right=0.99, bottom=0.165, top=0.93, wspace=0.42, hspace=0.12)
    axA = fig.add_subplot(gs[:, 0])
    axB1 = fig.add_subplot(gs[0, 1])
    axB2 = fig.add_subplot(gs[1, 1], sharex=axB1)
    axC = fig.add_subplot(gs[:, 2])

    # ---- a: decomposition plane --------------------------------------------------
    sel = {"none": lambda r: r["condition"] == "none",
           "coherent": lambda r: r["condition"] == "coherent" and float(r["gamma"]) == g_star,
           "rewire": lambda r: r["condition"] == "rewire" and float(r["theta"]) == th_star,
           "independent": lambda r: r["condition"] == "independent"}
    rng = np.random.default_rng(1)
    lim = 0.26
    for Dv in np.arange(0.05, 0.51, 0.05):
        axA.plot([0, Dv], [Dv, 0], color="#d9d9d9", lw=0.5, zorder=0)
    qD = float(np.median([float(r["q_D"]) for r in rows if r["condition"] == "none"]))
    axA.plot([0, qD], [qD, 0], color="black", lw=0.9, zorder=3)
    for key in ["independent", "none", "coherent", "rewire"]:
        pts = [r for r in rows if sel[key](r)]
        idx = rng.choice(len(pts), size=min(250, len(pts)), replace=False)
        x = np.array([float(pts[i]["abs_dbar_E"]) for i in idx])
        y = np.array([float(pts[i]["C"]) for i in idx])
        axA.scatter(x, y, s=4, lw=0, alpha=0.55, color=COL[key], label=LAB[key], zorder=2)
    axA.set_xlim(0, lim)
    axA.set_ylim(0, lim)
    axA.set_aspect("equal")
    axA.set_xlabel(r"Signed component $|\bar{\Delta}_E|$")
    axA.set_ylabel(r"Cancelled component $C_E$")
    axA.set_xticks([0, 0.1, 0.2])
    axA.set_yticks([0, 0.1, 0.2])
    hA, lA = axA.get_legend_handles_labels()
    hA.append(Line2D([], [], color="black", lw=0.9))
    lA.append("Alarm threshold")
    leg = axA.legend(hA, lA, loc="upper right", frameon=False, handletextpad=0.3, borderaxespad=0.1,
                     markerscale=2.2, labelspacing=0.25, handlelength=1.2)
    for h in leg.legend_handles[:-1]:
        h.set_alpha(1)

    # ---- b: time course for one realisation of balanced rewiring -------------------
    w = np.array([int(r["window"]) for r in tc])
    ts = np.array([float(r["tau_s_E"]) for r in tc])
    ab = np.array([float(r["abs_dbar_E"]) for r in tc])
    C = np.array([float(r["C"]) for r in tc])
    D = np.array([float(r["D"]) for r in tc])
    Bm = meta["timecourse"]["B_mean"]
    qs = meta["timecourse"]["q_s_cal"]
    qd = meta["timecourse"]["q_D_cal"]
    axB1.axhspan(Bm - qs, Bm + qs, color="#e8eef6", lw=0)
    axB1.axhline(Bm, color="0.3", lw=0.7, ls=":")
    axB1.plot(w, ts, color="#2b5d9b", lw=0.8, marker="o", ms=1.6)
    axB1.axvline(0.5, color="black", lw=0.5, ls="--")
    axB1.set_ylabel(r"$\tau_{s,E}$")
    span = max(0.12, 1.08 * float(np.max(np.abs(np.asarray(ts) - Bm))))
    axB1.set_ylim(Bm - span, Bm + span)
    axB1.set_yticks([round(Bm - 0.1, 1), round(Bm, 1), round(Bm + 0.1, 1)])
    plt.setp(axB1.get_xticklabels(), visible=False)
    axB1.text(0.02, 1.0, "Calibration", fontsize=6, va="bottom", transform=axB1.transAxes)
    axB1.text(0.58, 1.0, "Monitoring", fontsize=6, va="bottom", transform=axB1.transAxes)
    axB2.bar(w, ab, width=0.8, color="#2b5d9b", lw=0, label=r"$|\bar{\Delta}_E|$")
    axB2.bar(w, C, width=0.8, bottom=ab, color="#e9a67a", lw=0, label=r"$C_E$")
    axB2.axhline(qd, color="black", lw=0.8)
    axB2.axvline(0.5, color="black", lw=0.5, ls="--")
    axB2.set_ylabel(r"$D_E=|\bar{\Delta}_E|+C_E$")
    axB2.set_xlabel("Window")
    axB2.set_xlim(w.min() - 1, w.max() + 1)
    axB2.set_ylim(0, max(0.24, D.max() * 1.08))
    axB2.legend(loc="upper left", frameon=False, ncol=2, handlelength=1.0, columnspacing=0.8,
                borderaxespad=0.1)

    # ---- c: detection curves ---------------------------------------------------------
    for scen, col in [("coherent", COL["coherent"]), ("balanced", COL["rewire"])]:
        pr = [r for r in power if r["scenario"] == scen]
        pr.sort(key=lambda r: float(r["magnitude"]))
        x = np.array([float(r["effect_mean_abs_expected_change"]) for r in pr])
        yD = np.array([float(r["alarm_D_rate"]) for r in pr])
        yE = np.array([float(r["alarm_E_rate"]) for r in pr])
        axC.plot(x, yD, color=col, lw=1.0, marker="o", ms=2.2)
        axC.plot(x, yE, color=col, lw=0.9, ls="--", marker="s", ms=2.0, mfc="white", mew=0.6)
    axC.axhline(meta["config"]["alpha"], color="#8a8a8a", lw=0.5, ls=":")
    axC.set_xlabel("Mean absolute expected edge change")
    axC.set_ylabel("Alarm rate")
    axC.set_ylim(-0.02, 1.02)
    axC.set_xlim(0, 0.19)
    handles = [Line2D([], [], color=COL["coherent"], lw=1.0, label="Coherent shift"),
               Line2D([], [], color=COL["rewire"], lw=1.0, label="Balanced rewiring"),
               Line2D([], [], color="black", lw=1.0, marker="o", ms=2.2, label=r"$D_E$ alarm"),
               Line2D([], [], color="black", lw=0.9, ls="--", marker="s", ms=2.0, mfc="white",
                      mew=0.6, label=r"Signed control $|\bar{\Delta}_E|$")]
    axC.legend(handles=handles, loc="lower right", frameon=False, handlelength=1.8,
               labelspacing=0.3, borderaxespad=0.1, bbox_to_anchor=(1.03, 0.11))

    for ax, lab in [(axA, "a"), (axB1, "b"), (axC, "c")]:
        ax.text(-0.30 if ax is not axB1 else -0.22, 1.08 if ax is not axB1 else 1.2, lab,
                transform=ax.transAxes, fontsize=8.5, fontweight="bold", va="top")
    out_png = os.path.join(res, "fig1.png")
    fig.savefig(out_png, dpi=600)
    fig.savefig(os.path.join(res, "fig1.pdf"))
    fig.savefig(os.path.join(res, "fig1.svg"))
    print("wrote", out_png)


if __name__ == "__main__":
    main()
