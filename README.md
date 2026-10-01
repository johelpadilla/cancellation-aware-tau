# Cancellation-aware order coherence

Technical note and code by Johel Padilla-Villanueva
(ORCID [0000-0002-5797-6931](https://orcid.org/0000-0002-5797-6931)).

**Cancellation-aware order coherence: an exact decomposition of absolute concordance change into signed Systemic Tau and a cancellation index.**

| Path | Contents |
|---|---|
| `Padilla-Villanueva_cancellation-aware-tau_2026.pdf` | Note, 10 pages (CC BY 4.0) |
| `Padilla-Villanueva_cancellation-aware-tau_2026.docx` | Same note, Word with native equations |
| `code/` | Package `cancellation_tau` 1.0.0 (MIT) |
| `results/` | Table 1, Fig. 1 and the CSV/JSON written by `code/run_all.py` |
| `build/` | Document sources |

This note is a companion to the structural self-repair preprint
[10.5281/zenodo.23001549](https://doi.org/10.5281/zenodo.23001549).
It does not replace that article and it does not redefine Systemic Tau.
The code for that article is
[10.5281/zenodo.23001551](https://doi.org/10.5281/zenodo.23001551).

Zenodo: [10.5281/zenodo.23073069](https://doi.org/10.5281/zenodo.23073069)
(concept [10.5281/zenodo.23073068](https://doi.org/10.5281/zenodo.23073068)).
The PDF archived there is the rendered file in this repository. Its availability
section names Zenodo and does not print this record's DOI. LibreOffice on this
machine is an x86_64 binary, so the PDF was not regenerated after the DOI was reserved.

## Reproduce

From `code/`:

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q tests
.venv/bin/python run_all.py
```

`run_all.py` rewrites `results/`. The files shipped here were produced with
Python 3.13.5, NumPy 2.5.3 and seed `20260930`. A check on Python 3.12.13
reproduced Table 1, the identity checks and the other CSV and JSON files.
In `windows.csv`, 28 of 17,000 values in column `D2` differed by one unit in
the last place. Figure binaries depend on the renderer.
`results/run_metadata.json` records the interpreter that wrote each run, and
its `runtime_s` field changes on every run.

## Licence

Code: MIT (`LICENSE` and `code/LICENSE`).
Note text and figures: CC BY 4.0.
