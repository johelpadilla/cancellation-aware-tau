#!/usr/bin/env bash
# Build the note: results -> DOCX -> PDF -> page PNGs.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
PY="${PY:-$ROOT/.venv/bin/python}"
NAME=Padilla-Villanueva_cancellation-aware-tau_2026
cd "$HERE"
"$PY" build_note.py
export FONTCONFIG_FILE="$HERE/fonts.conf"
soffice -env:UserInstallation=file:///tmp/lo-note-cancel --headless --convert-to pdf \
  --outdir "$ROOT" "$ROOT/$NAME.docx" >/dev/null 2>&1
pdfinfo "$ROOT/$NAME.pdf" | grep -E "Pages|Page size"
rm -f "$ROOT"/png/page-*.png
pdftoppm -r 110 -png "$ROOT/$NAME.pdf" "$ROOT/png/page"
ls "$ROOT/png"
