"""Build the note (DOCX) from its text, the results files and the reference list."""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from docxlib import Builder  # noqa: E402

RES = os.path.join(ROOT, "results")
OUT_DOCX = os.path.join(ROOT, "Padilla-Villanueva_cancellation-aware-tau_2026.docx")

TITLE = ("Cancellation-aware order coherence: an exact decomposition of absolute concordance "
         "change into signed Systemic Tau and a cancellation index")
SHORT = "Cancellation-aware order coherence"

# ------------------------------------------------------------------ results
table = list(csv.DictReader(open(os.path.join(RES, "table1.csv"))))
power = list(csv.DictReader(open(os.path.join(RES, "power_curve.csv"))))
chk = json.load(open(os.path.join(RES, "null_and_identity_checks.json")))
meta = json.load(open(os.path.join(RES, "run_metadata.json")))
cfg = meta["config"]
T = {r["scenario"][0]: {k: (float(v) if k != "scenario" else v) for k, v in r.items()} for r in table}


def f3(x):
    s = f"{x:.3f}"
    return s.replace("-", "−") if x < 0 else s


def f2(x):
    return f"{x:.2f}".replace("-", "−")


def pc(x):
    return f"{100 * x:.1f}%"


def pcn(x):
    return f"{100 * x:.1f}"


g = chk["analytic_guide_mean_over_50_reps"]
ind = chk["independent_empirical"]
sur = chk["circular_shift_surrogate"]
cb = chk["calibration_baselines"]
ids = chk["identity_checks"]
nW = int(T["a"]["n_windows"])
E = meta["n_edges"]
Npairs = meta["n_pairs"]
N = cfg["n_modules"]
ncal = cfg["n_cal"]
reps = cfg["reps"]
nmon = cfg["n_mon"]
gam = T["b"]["gamma"]
fa_coupled = [T["a"][k] for k in ("alarm_D_rate", "alarm_E_rate", "alarm_P_rate")]
fa_ind = [T["d"][k] for k in ("alarm_D_rate", "alarm_E_rate", "alarm_P_rate")]
max_err = max(ids["max_abs_error_D_eq_absdbar_plus_C_and_score"], ids["max_abs_error_C_eq_minority_mass"])
err_exp = f"{max_err:.0e}".split("e")
err_txt = f"${float(err_exp[0]):.0f}\\times 10^{{{int(err_exp[1])}}}$"
ci_half = 0.0
for r in table:
    for k in ("alarm_D", "alarm_E", "alarm_P", "alarm_U"):
        ci_half = max(ci_half, float(r[k + "_hi"]) - float(r[k + "_rate"]), float(r[k + "_rate"]) - float(r[k + "_lo"]))
eff_b = T["b"]["effect_mean_abs_expected_change"]
eff_c = T["c"]["effect_mean_abs_expected_change"]
coh_top = [r for r in power if r["scenario"] == "coherent"][-1]
dwell = 1.0 / (1.0 - cfg["persist"])
rates = meta["rates"]

# ------------------------------------------------------------------ references
REFS = {
    "PV2025Unveiling": "Padilla-Villanueva, J. Unveiling Systemic Tau: redefining the fabric of time, stability, and emergent order across complex chaotic systems in the age of interdisciplinary discovery. Preprint at https://doi.org/10.5281/zenodo.17127368 (2025).",
    "PV2026Theory": "Padilla-Villanueva, J. Systemic Tau and hierarchical ordinal conjunctions: a relational theory of critical transitions. Preprint at https://doi.org/10.5281/zenodo.21753560 (2026).",
    "PV2026Erratum": "Padilla-Villanueva, J. Systemic Tau and hierarchical ordinal conjunctions: a relational theory of critical transitions. Preprint, version with erratum at https://doi.org/10.5281/zenodo.22970130 (2026).",
    "Kendall1938": "Kendall, M. G. A new measure of rank correlation. *Biometrika* **30**, 81–93 (1938).",
    "Kendall1945": "Kendall, M. G. The treatment of ties in ranking problems. *Biometrika* **33**, 239–251 (1945).",
    "TRI": "Padilla-Villanueva, J. Systemic Tau as a homeostatic trigger for structural self-repair in event-driven networks. Companion manuscript (2026).",
    "Ashby1960": "Ashby, W. R. *Design for a Brain* (Springer Netherlands, 1960).",
    "Turrigiano2008": "Turrigiano, G. G. The self-tuning neuron: synaptic scaling of excitatory synapses. *Cell* **135**, 422–435 (2008).",
    "PV2026Software": "Padilla-Villanueva, J. Systemic Tau (Stable). Zenodo https://doi.org/10.5281/zenodo.22863378 (2026).",
    "Bandt2002": "Bandt, C. & Pompe, B. Permutation entropy: a natural complexity measure for time series. *Phys. Rev. Lett.* **88**, 174102 (2002).",
    "Bartlett1935": "Bartlett, M. S. Some aspects of the time-correlation problem in regard to tests of significance. *J. R. Stat. Soc.* **98**, 536–543 (1935).",
    "Leone1961": "Leone, F. C., Nelson, L. S. & Nottingham, R. B. The folded normal distribution. *Technometrics* **3**, 543–550 (1961).",
    "Vovk2005": "Vovk, V., Gammerman, A. & Shafer, G. *Algorithmic Learning in a Random World* (Springer, 2005).",
    "Theiler1992": "Theiler, J., Eubank, S., Longtin, A., Galdrikian, B. & Farmer, J. D. Testing for nonlinearity in time series: the method of surrogate data. *Physica D* **58**, 77–94 (1992).",
    "Schreiber2000": "Schreiber, T. & Schmitz, A. Surrogate time series. *Physica D* **142**, 346–382 (2000).",
    "Lancaster2018": "Lancaster, G., Iatsenko, D., Pidde, A., Ticcinelli, V. & Stefanovska, A. Surrogate data for hypothesis testing of physical systems. *Phys. Rep.* **748**, 1–60 (2018).",
    "Scheffer2009": "Scheffer, M. *et al.* Early-warning signals for critical transitions. *Nature* **461**, 53–59 (2009).",
}

# ------------------------------------------------------------------ equations
EQ = {
    "F": r"F_t(S,f)=\frac{1}{|S|}\sum_{p\in S} f\left(\tau_b^{(p)}(t),\,B_p\right),\qquad B_p=\frac{1}{n_{\mathrm{cal}}}\sum_{w=1}^{n_{\mathrm{cal}}} \tau_b^{(p)}(w)",
    "inst": r"\tau_{\mathrm{s}}(t)=F_t(P,\,x),\qquad D_E(t)=F_t\left(E,\,\left|x-B\right|\right),\qquad \bar{\Delta}_E(t)=F_t(E,\,x-B)=\tau_{\mathrm{s},E}(t)-\tau_{\mathrm{s},E}^{\mathrm{cal}}",
    "dec": r"D_E=\left|\bar{\Delta}_E\right|+C_E,\qquad C_E=\frac{2}{|E|}\sum_{e\in E^{-}}\left|\Delta_e\right|=\frac{2}{|E|}\min(S_+,S_-)\ge 0",
    "kappa": r"\kappa_E=\frac{C_E}{D_E}=\frac{2\min(S_+,S_-)}{S_+ + S_-}=1-\frac{\left|\bar{\Delta}_E\right|}{D_E}\in[0,1]",
    "PE": r"\bar{\Delta}_P=\rho\,\bar{\Delta}_E+(1-\rho)\,\bar{\Delta}_{P\setminus E},\qquad D_E=\left|\bar{\Delta}_P\right|+C_E+R,\qquad |R|\le(1-\rho)\left|\bar{\Delta}_{P\setminus E}-\bar{\Delta}_E\right|",
    "null": r"E_0[D_E]\approx\sqrt{\frac{2}{\pi}}\,\frac{1}{|E|}\sum_{e\in E}\sigma_e,\qquad E_0\left|\bar{\Delta}_E\right|\approx\sqrt{\frac{2}{\pi}}\,\frac{1}{|E|}\left(\sum_{e\in E}\sigma_e^2\right)^{1/2},\qquad \kappa_0\approx 1-\frac{\left(\sum_{e}\sigma_e^2\right)^{1/2}}{\sum_{e}\sigma_e}",
    "fold": r"E|\Delta_e|=\sigma\,h\!\left(\frac{\delta}{\sigma}\right),\qquad h(u)=\sqrt{\frac{2}{\pi}}\,\exp\!\left(-\frac{u^2}{2}\right)+u\left(2\Phi(u)-1\right)=\sqrt{\frac{2}{\pi}}\left(1+\frac{u^2}{2}\right)+O(u^4)",
    "rule": r"p_D(t)=\frac{1+\sum_{w=1}^{n_{\mathrm{cal}}}\mathrm{1}\left[s_w\ge D_E(t)\right]}{n_{\mathrm{cal}}+1},\qquad \text{alarm}\ \Leftrightarrow\ p_D(t)\le\alpha,\qquad e^{*}=\arg\max_{e\in E}\left|\Delta_e(t)\right|",
    "taub": r"\tau_b^{(ij)}=\frac{\sum_{k<l}\xi_i(k,l)\,\xi_j(k,l)}{\left(\sum_{k<l}\xi_i(k,l)^2\right)^{1/2}\left(\sum_{k<l}\xi_j(k,l)^2\right)^{1/2}},\qquad \xi_i(k,l)=\mathrm{sgn}\left(z_i(l)-z_i(k)\right)",
    "Spm": r"S_+=\sum_{e:\,\Delta_e>0}\Delta_e,\qquad S_-=\sum_{e:\,\Delta_e<0}\left|\Delta_e\right|,\qquad D_E=\frac{S_+ + S_-}{|E|},\qquad \bar{\Delta}_E=\frac{S_+ - S_-}{|E|}",
    "Dq": r"D_{E,q}=\left(\frac{1}{|E|}\sum_{e\in E}\left|\Delta_e\right|^q\right)^{1/q},\qquad D_E=D_{E,1}\le D_{E,2}\le D_{E,\infty}=\max_{e\in E}\left|\Delta_e\right|,\qquad D_{E,2}^2=\bar{\Delta}_E^2+s_E^2",
    "var": r"\mathrm{Var}_0\left[\tau_b\right]=\frac{V_S}{\left(n_W-a_1/2\right)\left(n_W-b_1/2\right)},\qquad n_W=\frac{W(W-1)}{2},",
    "VS": r"V_S=\frac{W(W-1)(2W+5)-a_3-b_3}{18}+\frac{a_2b_2}{9W(W-1)(W-2)}+\frac{a_1b_1}{2W(W-1)},",
    "sig": r"\sigma_e^2=\mathrm{Var}_0\left[\tau_b^{(e)}\right]\left(1+\frac{1}{n_{\mathrm{cal}}}\right)f_e,\qquad f_e=1+2\sum_{k=1}^{K} r_i(k)\,r_j(k)",
    "model": r"\lambda_i(t)=\min\left(1,\ \max\left(0,\ p_i\left(1+a\sum_{e\ni i}w_{ie}\,c_e(t)+\gamma\,g(t)\right)\right)\right)",
    "score": r"s_k=\frac{1}{|E|}\sum_{e\in E}\left|\tau_b^{(e)}(k)-\frac{1}{n_{\mathrm{cal}}}\sum_{v\ne k}\tau_b^{(e)}(v)\right|,\qquad k=1,\ldots,n_{\mathrm{cal}}+1",
}
ORDER = ["F", "inst", "dec", "kappa", "PE", "null", "fold", "rule", "taub", "Spm", "Dq", "var", "VS", "sig", "score", "model"]
NUM = {k: i + 1 for i, k in enumerate(ORDER)}


def eq(k):
    return f"({NUM[k]})"


# ------------------------------------------------------------------ document
b = Builder(os.path.join(HERE, "template_TRI_v2.docx"), REFS, SHORT)
b.par(TITLE, style="Title")
b.par("Johel Padilla-Villanueva, DrPH", style="Author")
b.par("Department of Environmental Health, Graduate School of Public Health, Medical Sciences Campus, "
      "University of Puerto Rico, San Juan, Puerto Rico, USA", style="Affiliation")
b.par("ORCID 0000-0002-5797-6931 · Correspondence: joel.padilla2@upr.edu", style="Affiliation",
      ppr_extra='<w:spacing w:after="240"/>')
b.par("Abstract", style="AbstractHead")
ABSTRACT = (
    "Systemic Tau ($\\tau_{\\mathrm{s}}$), the mean pairwise Kendall concordance of module activity on a common event index, "
    "is a signed average: concordance gained on some pairs can offset concordance lost on others, so structural change "
    "can pass unseen. A cancellation-immune alarm is the mean absolute change $D$ of pairwise concordance from its "
    "calibration baseline over a fixed edge set. Here we show that both statistics are instances of one averaging operator "
    "on the pairwise concordance matrix and that, on a common edge set, $D$ decomposes exactly into the absolute change of "
    "the signed mean plus a non-negative cancellation term equal to twice the minority-sign mass of edge changes. "
    "The resulting index $\\kappa\\in[0,1]$ is the fraction of total change that the signed mean cannot see. We derive "
    "bounds, invariances and the no-change behaviour of $D$ and $\\kappa$, neither of which is near zero without change, "
    "and give a conformal alarm rule with a finite-sample false-alarm guarantee. In synthetic event streams, balanced "
    f"rewiring left $\\tau_{{\\mathrm{{s}}}}$ at its false-alarm level while $D$ detected it in {pcn(T['c']['alarm_D_rate'])}% of windows."
)
b.par(ABSTRACT, style="Abstract")

b.par(
    "Systemic Tau ($\\tau_{\\mathrm{s}}$) summarizes the coordination of a multivariate system as the mean of pairwise "
    "concordances between the activity streams of its modules[[PV2025Unveiling,PV2026Theory,PV2026Erratum]], each "
    "computed as Kendall’s tie-corrected coefficient $\\tau_b$ on a common event index[[Kendall1938,Kendall1945]]. "
    "In the companion article[[TRI]] it serves as the essential variable of a regenerative controller, in the sense of "
    "Ashby’s ultrastable system[[Ashby1960]] and by analogy with the set points of homeostatic plasticity[[Turrigiano2008]]. "
    "A signed mean has a structural blind spot, however. Networks that compute contain concordant and anti-concordant "
    "relations side by side, and a change that raises concordance on some pairs while lowering it on others can leave "
    "$\\tau_{\\mathrm{s}}$ where it was. The companion article therefore makes the operative alarm a matrix statistic, the "
    "mean absolute change $D$ of pairwise concordance from its calibration baseline over the edges present at the end "
    "of calibration, and retains $\\tau_{\\mathrm{s}}$ as a signed control.")
b.par(
    "Two statistics raise three questions. How are they related? How much of the change registered by $D$ is invisible "
    "to the signed mean? And how should $D$ be thresholded, given that it is positive even when nothing has changed? "
    "Here we show that $\\tau_{\\mathrm{s}}$ and $D$ are two instances of one averaging operator on the pairwise "
    "concordance matrix; that on a common edge set $D$ decomposes exactly into the absolute change of the signed mean "
    "and a non-negative cancellation term; that the ratio of the two defines a cancellation index with a direct "
    "interpretation; and that the no-change behaviour of both quantities, which is far from zero, can be predicted and "
    "calibrated. A conformal rule gives the alarm a finite-sample false-alarm guarantee, and synthetic event streams "
    "illustrate each result.")

b.heading("One operator, two statistics")
b.par(
    "Let $\\tau_b^{(p)}(t)$ be the concordance of pair $p=(i,j)$ in the window ending at $t$ (Methods, equation "
    f"{eq('taub')}), let $P$ be the set of all $N(N-1)/2$ pairs of $N$ modules, and let the matrix $\\mathrm{{M}}(t)$ collect "
    "these values. Calibration on a reference period yields a baseline $B_p$ for each pair, the mean of "
    "$\\tau_b^{(p)}$ over $n_{\\mathrm{cal}}$ calibration windows, and a set of edges $E\\subseteq P$ fixed at the end of "
    "calibration. In the companion controller $E$ contains the pairs joined by a connection of the network, but nothing "
    "below depends on how $E$ is chosen, only on its being fixed before monitoring begins. For any set of pairs $S$ and "
    "any function $f$ of a current value $x$ and a baseline $B$, define")
b.equation(EQ["F"], NUM["F"])
b.par(
    "Systemic Tau and the operative alarm are two instances of $F$, as is the signed change on the edge set:",
    ppr_extra='<w:keepNext/>')
b.equation(EQ["inst"], NUM["inst"])
b.par(
    "where $\\tau_{\\mathrm{s},E}$ is the signed mean restricted to $E$ and $\\tau_{\\mathrm{s},E}^{\\mathrm{cal}}$ its "
    "calibration mean; the last equality holds because the baselines are calibration means and $F$ is linear in $f$. "
    "The instances differ in two choices only: the set of pairs, which determines which relations are monitored, and "
    "the function, which determines whether the sign of a change is retained. What they share is the pairwise matrix "
    "$\\mathrm{M}(t)$. Statistics of ordinal structure beyond pairs, which the theory of hierarchical ordinal "
    "conjunctions addresses[[PV2026Theory,PV2026Erratum]], are not in general functions of $\\mathrm{M}(t)$ and lie "
    "outside this operator.")

b.heading("An exact decomposition")
b.par(
    "Write $\\Delta_e(t)=\\tau_b^{(e)}(t)-B_e$ for the change on edge $e$, and let $S_+$ and $S_-$ be the total "
    "magnitudes of the positive and of the negative changes on $E$. Because the signed mean averages the same changes "
    "whose magnitudes $D_E$ averages,", ppr_extra='<w:keepNext/>')
b.equation(EQ["dec"], NUM["dec"])
b.par(
    "where $E^-$ is the set of edges whose change has the sign opposite to that of $\\bar{\\Delta}_E$ (Methods, "
    "Proposition 1). The first term is the part of the change that the signed control sees; the second, $C_E$, is the "
    "part it loses to cancellation, twice the mass of the minority sign. The triangle inequality guarantees "
    "$C_E\\ge 0$, and the cancellation index", ppr_extra='<w:keepNext/>')
b.equation(EQ["kappa"], NUM["kappa"])
b.par(
    "is the fraction of the total absolute change that is invisible to the signed mean. It is zero when all edges "
    "change in the same direction, in which case $D_E$ and $|\\bar{\\Delta}_E|$ coincide, and one when positive and "
    "negative changes balance exactly, in which case the signed control is blind however large $D_E$ may be. The pair "
    "$(|\\bar{\\Delta}_E|, C_E)$, or equivalently $(D_E,\\kappa_E)$, is therefore a two-coordinate description of the "
    "change with no free parameter: lines of constant $D_E$ are anti-diagonals of the $(|\\bar{\\Delta}_E|, C_E)$ plane, "
    "and the position along such a line is fixed by $\\kappa_E$ (Fig. 1a).")
b.par(
    "The decomposition also explains why scalar combinations of the two statistics are not used. A statistic such as "
    "$D-\\lambda|\\Delta\\tau_{\\mathrm{s}}|$, or a rule that fires on $D$ only while $\\tau_{\\mathrm{s}}$ stays within its "
    "band, subtracts from $D$ the coherent component that $D$ already contains. Such constructions suppress the alarm "
    "precisely when the change is global and obvious, and their weight has no calibration principle. Equation "
    f"{eq('dec')} makes them unnecessary: the information on which they draw is carried, without a weight, by the "
    "coordinates $(|\\bar{\\Delta}_E|, C_E)$.")
b.par(
    "The identity is exact when the signed control is computed on the same edge set as $D_E$. The Systemic Tau of the "
    "companion article averages over all pairs, of which $E$ is a subset of relative size $\\rho=|E|/|P|$. Its change "
    "from calibration, $\\bar{\\Delta}_P=\\tau_{\\mathrm{s}}(t)-\\tau_{\\mathrm{s}}^{\\mathrm{cal}}$, mixes the signed "
    "changes on and off the edge set, and the decomposition acquires a remainder:", ppr_extra='<w:keepNext/>')
b.equation(EQ["PE"], NUM["PE"])
b.par(
    "The remainder vanishes when $E=P$ and is bounded by the disagreement between the signed changes on and off $E$. "
    "The all-pairs $\\tau_{\\mathrm{s}}$ can therefore move while every monitored edge is unchanged, and it can stay still "
    "while the edge set cancels; we recommend reporting the edge-restricted control $\\tau_{\\mathrm{s},E}$, for which "
    f"equation {eq('dec')} holds exactly, alongside $\\tau_{{\\mathrm{{s}}}}$ over all pairs.")
b.par(
    "Because every $\\tau_b$ lies in $[-1,1]$, $0\\le|\\bar{\\Delta}_E|\\le D_E\\le 1+|E|^{-1}\\sum_e|B_e|\\le 2$ and "
    "$0\\le C_E\\le D_E$. Being rank-based, like ordinal-pattern measures[[Bandt2002]], all these quantities are "
    "invariant to strictly increasing transformations of any stream and to relabelling of modules. Only $D_E$ is also "
    "invariant to reversing the polarity of a module, for instance to the choice of which of two complementary codes "
    "counts as active: reversal negates every concordance involving that module, and with it the signs of its edge "
    "changes, which alters $|\\bar{\\Delta}_E|$, $C_E$ and $\\kappa_E$ but not their sum (Methods). The split between "
    "coherent and cancelled change is thus defined relative to the sign convention of each stream; $D_E$ is not.")

b.heading("Behaviour without change and a calibrated alarm")
b.par(
    "Neither $D_E$ nor $\\kappa_E$ is near zero when nothing has changed. Each $\\Delta_e$ then carries the estimation "
    "error of the current window and of the baseline, with a standard deviation $\\sigma_e$ that follows from Kendall’s "
    "null variance with ties[[Kendall1945]], the factor $1+1/n_{\\mathrm{cal}}$ for the baseline, and a correction "
    f"$f_e\\ge 1$ for serial correlation of the binned streams[[Bartlett1935]] (Methods, equations {eq('var')} and "
    f"{eq('sig')}). For approximately Gaussian errors that are uncorrelated across edges, as for mutually independent "
    "modules,", ppr_extra='<w:keepNext/>')
b.equation(EQ["null"], NUM["null"])
b.par(
    "and $\\kappa_0\\approx 1-|E|^{-1/2}$ when the $\\sigma_e$ are similar. The signed mean averages estimation noise "
    "away at the rate $|E|^{-1/2}$, whereas the mean absolute value does not, so that without change $\\kappa_E$ approaches "
    "one as the edge set grows. A large $\\kappa_E$ is evidence of cancellation only when $D_E$ itself exceeds its "
    "calibrated threshold. The same asymmetry governs sensitivity. For a coherent shift $\\delta$ on every edge with "
    "Gaussian error of standard deviation $\\sigma$, the expected absolute change is that of a folded normal "
    "variable[[Leone1961]],", ppr_extra='<w:keepNext/>')
b.equation(EQ["fold"], NUM["fold"])
b.par(
    "so that near the noise floor $D_E$ grows quadratically in $\\delta$ while the signed mean grows linearly, and for "
    "$\\delta$ small relative to $\\sigma$ the signed control detects coherent change earlier (Methods). $D_E$, by "
    "contrast, detects balanced change, which the signed control cannot detect at all, and responds most strongly to "
    "change concentrated on a few edges.")
b.par(
    "These properties determine the alarm rule. The threshold for $D_E$ must come from the no-change distribution of "
    "$D_E$ itself, not from zero and not from a band around $\\tau_{\\mathrm{s}}$. We use the calibration windows as a "
    "conformal reference[[Vovk2005]]: each calibration window $w$ receives a score $s_w$, its mean absolute deviation "
    f"from the mean of the other windows (Methods, equation {eq('score')}), and", ppr_extra='<w:keepNext/>')
b.equation(EQ["rule"], NUM["rule"])
b.par(
    "fires with probability at most $\\alpha$ when the windows are exchangeable, as they are for an unchanged stationary "
    "process with nearly independent windows (Methods). Each alarm is reported with its diagnostic pair "
    "$(|\\bar{\\Delta}_E|, C_E)$, or $(D_E,\\kappa_E)$, and with its source $e^*$, the edge that contributes most to "
    "$D_E$. No-dependence references, circular-shift surrogates[[Theiler1992,Schreiber2000,Lancaster2018]] and "
    "rate-matched independent streams, keep the role they have for $\\tau_{\\mathrm{s}}$[[TRI]]: they establish that the "
    "baselines differ from what independent streams would produce, and they supply the noise floor of equation "
    f"{eq('null')} against which $D_E$ and $\\kappa_E$ are read. Where weak coherent change must also be caught, the "
    "signed control on $E$ can be monitored with its own conformal band and the alarm raised when either p-value falls "
    "to $\\alpha/2$ or below, a union of two calibrated tests that keeps the false-alarm probability at most $\\alpha$ "
    "without introducing a weight.")

b.heading("Numerical illustration")
b.par(
    f"We simulated binned event streams from $N={N}$ modules whose firing probabilities are modulated by latent binary "
    f"states, one per edge of a fixed coupling graph with $|E|={E}$ edges among the {Npairs} pairs, half concordant and "
    f"half anti-concordant (Methods, equation {eq('model')}). Each replicate was calibrated on {ncal} windows and then "
    f"monitored for {'five' if nmon == 5 else nmon} windows under one of four conditions: no change; a coherent shift, "
    "produced by a common drive that raises every pairwise concordance; balanced rewiring, in which four concordant and "
    "four anti-concordant edges invert their polarity; and independent streams matched in rate and autocorrelation, "
    "used for calibration and monitoring alike. The calibrated baselines lay far from the no-dependence floor (mean "
    f"$|B_e|$ of {f3(cb['mean_abs_B_E'])} against {f3(cb['mean_abs_B_E_surrogate'])} for circular-shift surrogates).")
b.par(
    f"Table 1 and Fig. 1 summarize {reps} replicates. Without change, the three conformal alarms fired in "
    f"{pcn(min(fa_coupled))}–{pc(max(fa_coupled))} of windows in the coupled system and in "
    f"{pcn(min(fa_ind))}–{pc(max(fa_ind))} for independent streams, close to the nominal 5%. $D_E$ was far from zero "
    f"under both nulls: for independent streams its mean was {f3(ind['mean_D'])}, against {f3(g['ED0'])} predicted by "
    f"equation {eq('null')} and {f3(sur['mean_D'])} from circular-shift surrogates; without the serial-correlation "
    f"factor the prediction was {f3(g['ED0_perm_only'])}. The mean of $\\kappa_E$ was {f2(ind['mean_kappa'])} against "
    f"a predicted {f2(g['kappa0'])}. Balanced rewiring left both signed statistics at their false-alarm level "
    f"(alarms in {pc(T['c']['alarm_E_rate'])} of windows on $E$ and {pc(T['c']['alarm_P_rate'])} over all pairs), "
    f"whereas $D_E$ fired in {pc(T['c']['alarm_D_rate'])}, with $\\kappa_E={f2(T['c']['kappa_mean'])}$ (Fig. 1b); the "
    f"edge with the largest change was a rewired edge in {pc(T['c']['source_hit_rate'])} of these alarms, against 50% "
    "expected by chance. Coherent change of similar mean magnitude lay mostly in the signed component "
    f"($\\kappa_E={f2(T['b']['kappa_mean'])}$). It was detected by the signed control on $E$ in "
    f"{pc(T['b']['alarm_E_rate'])} of windows and by the all-pairs $\\tau_{{\\mathrm{{s}}}}$, whose non-edge pairs shared the "
    f"drive, in {pc(T['b']['alarm_P_rate'])}, but by $D_E$ in only {pc(T['b']['alarm_D_rate'])}. Across magnitudes "
    f"(Fig. 1c), $D_E$ dominated for balanced change and the signed control for weak coherent change, as equations "
    f"{eq('null')} and {eq('fold')} predict; the union rule detected {pc(T['b']['alarm_U_rate'])} of coherent and "
    f"{pc(T['c']['alarm_U_rate'])} of balanced windows.")

# ---- Figure 1
b.figure(os.path.join(RES, "fig1.png"), 6.5)
b.par(
    "**Fig. 1 | Decomposition of absolute concordance change in synthetic event streams.** **a**, Monitored windows "
    "(250 randomly chosen per condition) placed by their signed component $|\\bar{\\Delta}_E|$ and cancelled component "
    "$C_E$. Grey anti-diagonals are lines of constant $D_E=|\\bar{\\Delta}_E|+C_E$; the black line is the median conformal "
    "alarm threshold without change ($\\alpha=0.05$). Coherent change moves windows along the horizontal axis and "
    "balanced rewiring along the vertical axis; both null conditions lie near the origin with $C_E>|\\bar{\\Delta}_E|$. "
    "**b**, One realization of balanced rewiring. Top, the signed control $\\tau_{\\mathrm{s},E}$ with its calibration "
    "mean (dotted) and alarm band (shaded). Bottom, $D_E$ stacked as $|\\bar{\\Delta}_E|$ (blue) plus $C_E$ (orange), with "
    "its alarm threshold; calibration windows are shown against leave-one-out baselines. After the change (dashed line) "
    "the increase is carried almost entirely by $C_E$. **c**, Alarm rates of $D_E$ (solid) and of the signed control "
    "(dashed) against the mean absolute expected edge change, for coherent shifts of increasing strength and for "
    f"progressive polarity rewiring; each point summarizes {nW:,} windows ({reps} replicates × {nmon} windows); dotted "
    "line, $\\alpha$.", style="FigCap")

b.heading("Scope")
b.par(
    "The decomposition is an algebraic identity. It holds in every window and for every edge set, and it applies to any "
    "signed average of pairwise changes, whatever the association measure. Its statistical companions, the no-change "
    "predictions and the conformal rule, rest on approximations (Gaussian edge errors, weak correlation between edge "
    "errors, exchangeable windows) that the simulation supports but that must be checked in each application, which is "
    "why every threshold here is calibrated rather than fixed. The illustration is synthetic and small; it shows how the "
    "statistics behave when the ground truth is known and says nothing about any particular neural or artificial "
    "system. Nor does it establish when cancellation occurs in practice. Early-warning signals for critical "
    "transitions[[Scheffer2009]] are also read from system-level statistics, but whether balanced reorganization, and "
    "hence cancellation, accompanies such transitions is an empirical question that this note does not address. What "
    "the decomposition provides is an accounting: whenever $D_E$ raises an alarm, it states how much of the change the "
    "signed Systemic Tau would have seen and how much it would have missed.")

# ---- Table 1
b.par(
    "**Table 1 | Decomposition and alarm rates in four synthetic conditions.** Means over "
    f"{nW:,} monitored windows ({reps} replicates × {nmon} windows); $N={N}$ modules, $|E|={E}$ edges, {Npairs} pairs. "
    "$\\Delta\\tau_{\\mathrm{s}}$, change of $\\tau_{\\mathrm{s}}$ over all pairs; $\\bar{\\Delta}_E$, $D_E$, $C_E$, "
    "$\\kappa_E$, signed change, mean absolute change, cancelled component and cancellation index on $E$. Alarm rates "
    f"use conformal thresholds at $\\alpha=0.05$ from {ncal} calibration windows; the union rule fires when $D_E$ or the "
    "signed control on $E$ reaches $p\\le\\alpha/2$. Source, fraction of $D_E$ alarms whose largest edge change lies on a "
    f"rewired edge (chance 50%). Wilson 95% intervals of all rates are within ±{100 * ci_half:.1f} percentage points.",
    style="TabCap")


def row(key, label):
    r = T[key]
    src = pcn(r["source_hit_rate"]) if key == "c" else "—"
    return [label, f3(r["dtau_s_P_mean"]), f3(r["dbar_E_mean"]), f3(r["D_mean"]), f3(r["C_mean"]),
            f2(r["kappa_mean"]), pcn(r["alarm_D_rate"]), pcn(r["alarm_E_rate"]), pcn(r["alarm_P_rate"]),
            pcn(r["alarm_U_rate"]), src]


b.table(
    col_widths=[1640, 700, 700, 700, 700, 640, 720, 800, 800, 700, 700],
    header_rows=[
        [("", 1), ("Mean over windows", 5), ("Alarm rate (%)", 4), ("", 1)],
        [("Condition", 1), ("$\\Delta\\tau_{\\mathrm{s}}$", 1), ("$\\bar{\\Delta}_E$", 1), ("$D_E$", 1), ("$C_E$", 1),
         ("$\\kappa_E$", 1), ("$D_E$", 1), ("$\\tau_{\\mathrm{s},E}$", 1), ("$\\tau_{\\mathrm{s}}$, all pairs", 1),
         ("Union", 1), ("Source (%)", 1)],
    ],
    rows=[row("a", "No change"), row("b", f"Coherent shift ($\\gamma={gam:.1f}$)"),
          row("c", "Balanced rewiring"), row("d", "Independent null")],
)
b.par("", style="BodyText", ppr_extra='<w:spacing w:after="0"/>')


# ------------------------------------------------------------------ Methods
b.heading("Methods")
b.heading("Pairwise concordance and baselines", 2)
b.par(
    "Module $i$ contributes a binned activity stream $z_i(k)$ on a common discrete event index, for example event counts "
    "in bins of $b$ ticks. For bins $k<l$ of a window of $W$ bins, Kendall’s tie-corrected coefficient[[Kendall1945]] is "
    "the cosine between the sign vectors of two streams,", ppr_extra='<w:keepNext/>')
b.equation(EQ["taub"], NUM["taub"])
b.par(
    "which lies in $[-1,1]$. It is set to zero when either stream is constant in the window, and the fraction of such "
    "undefined pairs is reported; it was zero throughout the simulations. The baseline of pair $p$ is the mean of "
    f"$\\tau_b^{{(p)}}$ over the calibration windows (equation {eq('F')}); the mean, rather than a median, is what makes "
    "$\\bar{\\Delta}_E$ equal to the change of $\\tau_{\\mathrm{s},E}$ from its calibration mean. The edge set is fixed "
    "when calibration ends and is not updated during monitoring, so that edges lost after calibration remain monitored "
    "and edges gained are not.")
b.heading("Proposition 1", 2)
b.par(
    "For real changes $\\Delta_e$, $e\\in E$, with $S_+$ and $S_-$ defined by", ppr_extra='<w:keepNext/>')
b.equation(EQ["Spm"], NUM["Spm"])
b.par(
    "one has $D_E=|\\bar{\\Delta}_E|+C_E$ with $C_E=2\\min(S_+,S_-)/|E|\\ge 0$; $C_E$ equals $2/|E|$ times the total "
    "magnitude of the changes whose sign is opposite to that of $\\bar{\\Delta}_E$; and, if $D_E>0$, "
    "$\\kappa_E\\in[0,1]$, with $\\kappa_E=0$ if and only if no two changes have opposite signs and $\\kappa_E=1$ if and "
    "only if $\\bar{\\Delta}_E=0$.")
b.par(
    f"*Proof.* Splitting the sums over $E$ by the sign of $\\Delta_e$ gives equation {eq('Spm')}. For real $a,b\\ge 0$, "
    "$a+b-|a-b|=2\\min(a,b)$, so $C_E=D_E-|\\bar{\\Delta}_E|=2\\min(S_+,S_-)/|E|\\ge 0$. If $\\bar{\\Delta}_E>0$, then "
    "$S_+>S_-$ and $\\min(S_+,S_-)=S_-$, the total magnitude of the changes of sign opposite to $\\bar{\\Delta}_E$; the "
    "case $\\bar{\\Delta}_E<0$ is symmetric, and if $\\bar{\\Delta}_E=0$, then $S_+=S_-$ and $C_E=D_E$. Dividing by "
    "$D_E=(S_++S_-)/|E|>0$ gives $\\kappa_E=2\\min(S_+,S_-)/(S_++S_-)$, which lies in $[0,1]$ because "
    "$\\min(a,b)\\le(a+b)/2$, vanishes exactly when $S_+=0$ or $S_-=0$, and equals one exactly when $S_+=S_-$, that "
    "is, when $\\bar{\\Delta}_E=0$. ∎ The bounds stated in the main text follow from "
    "$|\\Delta_e|\\le|\\tau_b^{(e)}|+|B_e|\\le 1+|B_e|$. A unit test checks the identity, the minority-mass form and the "
    "bounds on 20,000 random vectors, including exactly balanced, one-signed and tie-heavy cases, and the simulation "
    f"checks them in every monitored window (largest absolute discrepancy {err_txt}).")
b.heading("All pairs versus the edge set", 2)
b.par(
    "Because $B_p$ is a calibration mean for every $p\\in P$, the change of the all-pairs Systemic Tau from its "
    "calibration mean is $\\bar{\\Delta}_P=|P|^{-1}\\sum_{p\\in P}\\Delta_p$. Splitting the sum over $E$ and "
    f"$P\\setminus E$ gives the first part of equation {eq('PE')}, and hence "
    "$\\bar{\\Delta}_P-\\bar{\\Delta}_E=(1-\\rho)(\\bar{\\Delta}_{P\\setminus E}-\\bar{\\Delta}_E)$. With "
    "$R=D_E-|\\bar{\\Delta}_P|-C_E=|\\bar{\\Delta}_E|-|\\bar{\\Delta}_P|$ by Proposition 1, the reverse triangle inequality "
    "gives $|R|\\le|\\bar{\\Delta}_E-\\bar{\\Delta}_P|$, which is the bound. It held in every simulated window.")
b.heading("Invariances and power means", 2)
b.par(
    "$\\tau_b$ depends on the streams only through the signs $\\xi_i(k,l)$, which strictly increasing transformations "
    "of $z_i$ leave unchanged and strictly decreasing ones negate. A decreasing transformation of module $i$ therefore "
    "negates $\\tau_b^{(ij)}$ in every window, hence $B_{ij}$ and $\\Delta_{ij}$, for every $j$; $|\\Delta_{ij}|$ is "
    "unchanged, so $D_E$ is invariant, whereas $\\bar{\\Delta}_E$, and with it $C_E$ and $\\kappa_E$, changes unless no "
    "edge of $E$ is incident to $i$ or the changes of those edges sum to zero. The mean absolute change is the case "
    "$q=1$ of the power means", ppr_extra='<w:keepNext/>')
b.equation(EQ["Dq"], NUM["Dq"])
b.par(
    "which do not decrease with $q$. The quadratic member decomposes into the squared signed change and the "
    "across-edge variance $s_E^2$ of the changes, a second-order analogue of Proposition 1; the limit $q\\to\\infty$ is "
    f"the largest single change, whose argument is the source $e^*$ of equation {eq('rule')}. Larger $q$ weights "
    "concentrated change more heavily, whereas $q=1$ keeps the decomposition additive on the scale of the changes "
    "themselves.")
b.heading("No-change behaviour", 2)
b.par(
    "Without change, $E[\\Delta_e]\\approx 0$, and when the monitored window does not overlap the calibration windows and "
    "windows are nearly uncorrelated, $\\mathrm{Var}(\\Delta_e)=\\mathrm{Var}(\\hat{\\tau}_b^{(e)})(1+1/n_{\\mathrm{cal}})$. "
    "For serially independent streams, the variance of $\\tau_b$ under independence, conditional on the ties in the "
    "window, is Kendall’s[[Kendall1945]]", ppr_extra='<w:keepNext/>')
b.equation(EQ["var"], NUM["var"])
b.par("with", ppr_extra='<w:keepNext/>')
b.equation(EQ["VS"], NUM["VS"])
b.par(
    "where $n_W$ is the number of bin pairs and the sums $a_1=\\sum_g t_g(t_g-1)$, $a_2=\\sum_g t_g(t_g-1)(t_g-2)$ and $a_3=\\sum_g t_g(t_g-1)(2t_g+5)$ run over the "
    "groups of $t_g$ tied values of $z_i$ in the window, and $b_1$, $b_2$, $b_3$ likewise for $z_j$. Without ties it "
    "reduces to $2(2W+5)/(9W(W-1))$[[Kendall1938]], and for binary streams, for which $\\tau_b$ is the $\\phi$ "
    "coefficient, to $1/(W-1)$. Serial correlation inflates the variance; following Bartlett[[Bartlett1935]], we use",
    ppr_extra='<w:keepNext/>')
b.equation(EQ["sig"], NUM["sig"])
b.par(
    "with lag-$k$ autocorrelations $r_i(k)$ of the binned streams estimated from the calibration record and $K=10$. The "
    f"unit tests compare equation {eq('var')} with 20,000 random permutations of tie-heavy count series and with the "
    "binary case. Because $\\hat{\\tau}_b$ is asymptotically normal, $|\\Delta_e|$ is approximately half-normal, with mean "
    "$(2/\\pi)^{1/2}\\sigma_e$ and variance $(1-2/\\pi)\\sigma_e^2$, which gives $E_0[D_E]$ in equation "
    f"{eq('null')} and $\\mathrm{{SD}}_0[D_E]\\approx((1-2/\\pi)\\sum_e\\sigma_e^2)^{{1/2}}/|E|$. For mutually independent "
    "modules the errors of distinct pairs are uncorrelated to first order: two pairs that share module $i$ also involve "
    "modules $j\\ne k$ whose sign processes are independent of each other and of $i$ and have zero mean for stationary, "
    "time-reversible streams. $\\bar{\\Delta}_E$ is then approximately normal with variance "
    "$\\sum_e\\sigma_e^2/|E|^2$, which gives $E_0|\\bar{\\Delta}_E|$, and the ratio of the two means gives $\\kappa_0$. By "
    "the Cauchy–Schwarz inequality $(\\sum_e\\sigma_e^2)^{1/2}/\\sum_e\\sigma_e\\ge|E|^{-1/2}$, with equality when all "
    "$\\sigma_e$ are equal, so $\\kappa_0\\le 1-|E|^{-1/2}$ to this order. When modules are coupled, errors of pairs that "
    "share a module are correlated, the variance of $\\bar{\\Delta}_E$ is larger and $\\kappa_E$ without change is lower "
    f"({f2(T['a']['kappa_mean'])} in the coupled simulation against {f2(T['d']['kappa_mean'])} for independent streams).")
b.heading("Sensitivity to coherent change", 2)
b.par(
    f"If $\\Delta_e\\sim N(\\delta,\\sigma^2)$ on every edge, $E|\\Delta_e|=\\sigma h(\\delta/\\sigma)$ with $h$ as in equation "
    f"{eq('fold')}; the expansion follows from $\\exp(-u^2/2)=1-u^2/2+O(u^4)$ and $2\\Phi(u)-1=2u\\phi(0)+O(u^3)$, with "
    "$\\phi(0)=(2\\pi)^{-1/2}$. The expected excess of $D_E$ over its no-change value is therefore "
    "$(2/\\pi)^{1/2}\\delta^2/(2\\sigma)$, against a null standard deviation $\\sigma(1-2/\\pi)^{1/2}|E|^{-1/2}$, whereas "
    "the signed change grows by $\\delta$ against a null standard deviation $\\sigma|E|^{-1/2}$. With $u=\\delta/\\sigma$, "
    "the standardized separations are $|E|^{1/2}u^2/(2(\\pi/2-1)^{1/2})$ for $D_E$ and $|E|^{1/2}u$ for the signed "
    "control, so the signed control separates weak coherent change better; the leading-order expressions cross at "
    "$u=2(\\pi/2-1)^{1/2}\\approx 1.51$. For balanced change the signed control has no separation at all.")
b.heading("Conformal alarm rule", 2)
b.par(
    "Let windows $1,\\ldots,n_{\\mathrm{cal}}$ be the calibration windows and window $n_{\\mathrm{cal}}+1$ the monitored "
    "one. Each of the $n_{\\mathrm{cal}}+1$ windows receives the score", ppr_extra='<w:keepNext/>')
b.equation(EQ["score"], NUM["score"])
b.par(
    "where $v$ runs over the other $n_{\\mathrm{cal}}$ windows, so that $s_{n_{\\mathrm{cal}}+1}=D_E(t)$ exactly. Each "
    "score is a symmetric function of the other windows; if the $n_{\\mathrm{cal}}+1$ window matrices are exchangeable, so "
    "are the scores, the rank of the monitored score among them is uniform, and the p-value of equation "
    f"{eq('rule')} satisfies $\\Pr(p_D\\le\\alpha)\\le\\alpha$[[Vovk2005]]. With $n_{{\\mathrm{{cal}}}}={ncal}$ and "
    "$\\alpha=0.05$, the alarm fires when $D_E(t)$ exceeds all but at most one calibration score. Replacing the mean "
    "absolute deviation by the absolute mean deviation gives the signed controls on $E$ and on $P$. Consecutive windows "
    "of a stationary process are only approximately exchangeable; in the simulations, latent states persisted for about "
    f"{dwell:.0f} ticks against windows of {cfg['window_bins'] * cfg['bin_ticks']} ticks, and the empirical false-alarm "
    "rates were within binomial error of $\\alpha$.")
b.heading("Simulation model and protocol", 2)
b.par("Module $i$ emits an event at tick $t$ with probability", ppr_extra='<w:keepNext/>')
b.equation(EQ["model"], NUM["model"])
b.par(
    "where each edge $e$ carries a latent state $c_e(t)\\in\\{-1,+1\\}$ that keeps its value from one tick to the next "
    f"with probability {cfg['persist']}, $g(t)$ is a common latent state of the same kind, $w_{{ie}}=1$ for the first "
    f"endpoint of $e$ and $w_{{je}}=s_e\\in\\{{-1,+1\\}}$ for the second, and $a={cfg['coupling']}$. The coupling graph is a "
    f"ring of {N} modules with {cfg['n_chords']} random chords ({E} edges, {E // 2} with $s_e=+1$ and {E - E // 2} with "
    f"$s_e=-1$); the base probabilities $p_i$ were drawn once from $U(0.08,0.20)$ (range {min(rates):.3f}–{max(rates):.3f}). "
    f"Events are counted in bins of {cfg['bin_ticks']} ticks, and windows contain {cfg['window_bins']} bins. Each "
    f"replicate draws {ncal} consecutive calibration windows, and each monitored condition draws {nmon} consecutive "
    "windows from a separate stretch of the process, with common random numbers across conditions. Balanced rewiring "
    "multiplies $w_{je}$ by $1-2\\theta$ on a set of four concordant and four anti-concordant edges ($\\theta=1$ in "
    f"Table 1), chosen in a {cfg['pilot_windows']:,}-window pilot as the combination whose expected baselines sum "
    "closest to zero. The coherent shift sets $\\gamma>0$; Table 1 uses $\\gamma="
    f"{gam:.1f}$, the value on the grid $0.1,0.2,\\ldots,0.7$ whose mean absolute expected edge change, the mean over "
    "edges of the absolute mean of $\\Delta_e$ over monitored windows, is closest to that of rewiring at $\\theta=1$ "
    f"({f3(eff_b)} against {f3(eff_c)}). The independent null drives each module by private copies of its latent "
    "states with the same weights, which preserves the marginal law and autocorrelation of each stream and removes all "
    "cross-dependence. Circular-shift surrogates rotate each module’s concatenated calibration record, except that of a "
    "reference module, by an independent lag of at least one window. Detection curves use $\\gamma\\in\\{0,0.1,\\ldots,0.7\\}$ "
    "and $\\theta\\in\\{0,0.125,\\ldots,1\\}$. All "
    f"random streams derive from one NumPy seed sequence (seed {cfg['master_seed']}), and the full configuration is "
    "written with the results.")

b.heading("Data and code availability")
b.par(
    "No experimental data were used. The Python package that implements the operator, the decomposition, the null "
    "guide, the conformal rule and the simulation, together with its unit tests and a script that regenerates every "
    "number in the text, Table 1 and Fig. 1 with a single command, is archived on Zenodo alongside this note, with the "
    "resulting CSV and JSON files. The $\\tau_b$ estimator follows the reference implementation of Systemic "
    "Tau[[PV2026Software]].")
b.heading("Acknowledgements")
b.par(
    "Large language model tools (DeepSeek; Grok) assisted in exploring the formulation and in editing; the author "
    "verified all derivations and takes full responsibility.")
b.heading("Author contributions")
b.par("J.P.-V. conceived the study, derived the results, wrote the code and wrote the manuscript.")
b.heading("Competing interests")
b.par("The author declares no competing interests.")
b.heading("References")
b.references(lambda s: s)

now = dt.datetime(2026, 9, 30, 12, 0, 0)
b.save(OUT_DOCX, {"title": TITLE, "author": "Johel Padilla-Villanueva", "subject": "Technical note",
                  "keywords": "Systemic Tau; Kendall tau-b; concordance; cancellation; change detection; "
                              "conformal calibration; surrogate data",
                  "comments": "", "created": now, "modified": now, "last_modified_by": "Johel Padilla-Villanueva"})

# replace the template's custom document properties by an empty set
tmp = OUT_DOCX + ".tmp"
with zipfile.ZipFile(OUT_DOCX) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "docProps/custom.xml":
            data = (b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    b'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" '
                    b'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"/>')
        zout.writestr(item, data)
os.replace(tmp, OUT_DOCX)
print("wrote", OUT_DOCX, "citations:", len(b.cites.order), "equations:", len(ORDER))
