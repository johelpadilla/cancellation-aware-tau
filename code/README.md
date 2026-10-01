# cancellation_tau

Code for the technical note *Cancellation-aware order coherence: an exact decomposition of absolute
concordance change into signed Systemic Tau and a cancellation index* (J. Padilla-Villanueva, 2026).

## Contents

| Path | Purpose |
|---|---|
| `cancellation_tau/tau.py` | Kendall tau-b matrix of binned streams; tie-conditional null variance (Kendall 1945); autocorrelation |
| `cancellation_tau/decomposition.py` | Operator F(S, f); decomposition D = abs(mean change) + C; cancellation index kappa; power means D_q; all-pairs vs edge-set relation |
| `cancellation_tau/calibration.py` | Window statistics; full-conformal scores and p-values; analytic no-change guide (with Bartlett factor); circular-shift surrogates |
| `cancellation_tau/simulate.py` | Synthetic binned event streams with latent edge states (no change, coherent shift, balanced rewiring, independent null) |
| `run_all.py` | Regenerates every number, Table 1 and Fig. 1 (writes `../results/`) |
| `pandas_free_summary.py` | Table 1 summaries (means, Wilson intervals) |
| `make_figure.py` | Fig. 1 (PNG 600 dpi, PDF, SVG) from `../results/` |
| `tests/test_decomposition.py` | Unit tests (identity, bounds, invariances, null variance, conformal false-alarm rate, simulator) |

## Reproduce

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q tests      # 11 tests
.venv/bin/python run_all.py               # about 20 s; writes ../results/*
```

All random streams derive from a single NumPy `SeedSequence` (seed 20260930); the configuration is written to
`../results/run_metadata.json`. Re-running produces identical CSV/JSON outputs (only the `runtime_s` field of
`run_metadata.json` changes).

## Outputs (`../results/`)

- `table1.csv` — per-condition means, SDs, alarm rates with Wilson 95% intervals, source-attribution rate
- `power_curve.csv` — alarm rates against effect size (Fig. 1c)
- `windows.csv`, `surrogate_windows.csv` — per-window statistics (D, signed change, C, kappa, p-values)
- `calibration_baselines.csv` — edge baselines of coupled and surrogate calibrations
- `timecourse.csv` — single realization shown in Fig. 1b
- `null_and_identity_checks.json` — analytic vs empirical no-change values; identity and bound checks
- `run_metadata.json`, `run_log.txt` — configuration and log
- `fig1.png`, `fig1.pdf`, `fig1.svg`

## Scope

The data are synthetic. The simulations illustrate the behaviour of the statistics when the ground truth is
known; they make no claim about any particular neural or artificial system.

## Licence

Code: MIT. Note text and figures: CC BY 4.0.
