# Guía para Grok Builder: depósito en Zenodo de la nota técnica

**Nota:** *Cancellation-aware order coherence: an exact decomposition of absolute concordance change into signed
Systemic Tau and a cancellation index* — Johel Padilla-Villanueva, DrPH (ORCID 0000-0002-5797-6931).

> **Regla principal:** no publicar nada sin el OK explícito de Johel. Se puede preparar el borrador del depósito,
> pero **no se debe pulsar "Publish"** hasta que Johel lo apruebe por escrito en la conversación.

## 1. Verificar los archivos

En `/workspace/technical-note-cancellation/` deben estar:

| Archivo o carpeta | Contenido |
|---|---|
| `Padilla-Villanueva_cancellation-aware-tau_2026.pdf` | Nota (10 páginas, US Letter) |
| `Padilla-Villanueva_cancellation-aware-tau_2026.docx` | Versión Word (ecuaciones nativas OMML) |
| `code/` | Paquete `cancellation_tau`, `run_all.py`, `make_figure.py`, `pandas_free_summary.py`, `tests/`, `requirements.txt`, `README.md` |
| `results/` | CSV/JSON y `fig1.png/pdf/svg` usados en la Tabla 1 y la Fig. 1 |
| `build/` | Fuentes del documento (`build_note.py`, `docxlib.py`, `texmath.py`), `render.sh`, plantilla, fuentes y referencias verificadas |
| `png/` | Renders de cada página (control visual) |
| `zenodo_metadata_NOT_UPLOADED.json` | Metadatos propuestos |

Comprobación rápida:

```bash
cd /workspace/technical-note-cancellation
pdfinfo Padilla-Villanueva_cancellation-aware-tau_2026.pdf | grep Pages     # Pages: 10
python3 -c "import json; json.load(open('zenodo_metadata_NOT_UPLOADED.json')); print('JSON ok')"
```

## 2. Ejecutar las pruebas y reproducir los resultados

```bash
cd /workspace/technical-note-cancellation/code
python3 -m venv ../.venv && ../.venv/bin/pip install -r requirements.txt   # si el venv no existe
../.venv/bin/python -m pytest -q tests        # esperado: 11 passed
../.venv/bin/python run_all.py                # ~20 s; reescribe ../results/
```

Valores esperados en `results/table1.csv` (200 réplicas × 5 ventanas):

| Condición | tasa de alarma D | control con signo en E | τs, todos los pares |
|---|---|---|---|
| Sin cambio | 0.051 | 0.051 | 0.044 |
| Desplazamiento coherente (γ = 0.5) | 0.486 | 0.842 | 0.991 |
| Recableado balanceado | 0.950 | 0.036 | 0.049 |
| Nulo independiente | 0.051 | 0.057 | 0.046 |

Salvo el campo `runtime_s` de `run_metadata.json`, los CSV/JSON deben quedar idénticos (semilla 20260930).
Si algún valor cambia, **detenerse** e informar a Johel antes de seguir.

(Opcional) Regenerar el PDF: `bash ../build/render.sh` (requiere LibreOffice con el módulo Math y poppler-utils).

## 3. Preparar el ZIP del código

Desde `/workspace/technical-note-cancellation/`, crear `cancellation_tau_code_v1.0.0.zip` con `code/` y
`results/`, sin `.venv`, `__pycache__` ni `.pytest_cache` (zip no está instalado; usar Python):

```bash
cd /workspace/technical-note-cancellation
python3 - <<'PY'
import os, zipfile
skip = {".venv", "__pycache__", ".pytest_cache"}
with zipfile.ZipFile("cancellation_tau_code_v1.0.0.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for top in ("code", "results"):
        for root, dirs, files in os.walk(top):
            dirs[:] = [d for d in dirs if d not in skip]
            for f in files:
                z.write(os.path.join(root, f))
print("ok")
PY
```

## 4. Crear el depósito en Zenodo (como borrador)

1. Entrar en https://zenodo.org con la cuenta de Johel (ORCID 0000-0002-5797-6931).
2. **New upload.** Subir:
   - `Padilla-Villanueva_cancellation-aware-tau_2026.pdf`
   - `cancellation_tau_code_v1.0.0.zip`
3. Copiar los metadatos de `zenodo_metadata_NOT_UPLOADED.json`:
   - Resource type: *Publication → Technical note*
   - Title, Creator (nombre, afiliación, ORCID), Description (resumen), Keywords
   - License: **CC BY 4.0** para la nota (confirmada por Johel); el código va con licencia MIT (confirmada)
   - Related works: los cuatro DOI (10.5281/zenodo.17127368, .21753560, .22970130, .22863378) con relación
     *References*
   - Notes: dejar el texto del JSON (artículo compañero sin DOI y declaración de uso de IA)
4. Pulsar **Save** (borrador). **No pulsar Publish.**
5. Si se usa la API REST en vez de la web: crear el depósito con `POST /api/deposit/depositions`, subir los
   archivos al *bucket* y hacer `PUT` de los metadatos. **No llamar a** `/actions/publish`.

## 5. Antes de publicar: pedir el OK de Johel

Enviar a Johel un resumen con: enlace al borrador, lista de archivos subidos, licencia elegida y los puntos
abiertos del JSON (`pending_author_decisions`). Publicar **solo** si Johel responde con una aprobación
explícita (p. ej., «publícalo»).

## 6. Después de publicar (solo con OK)

- Anotar el DOI asignado (formato `10.5281/zenodo.NNNNNNNN`) y el enlace del registro.
- Informar a Johel del DOI y del enlace.
- Si Johel lo pide, añadir el DOI a la sección *Data and code availability* de la nota y regenerar el PDF con
  `build/render.sh`. Eso sería una nueva versión del depósito, no una modificación silenciosa.

## Qué NO hacer

- No publicar, compartir ni enviar nada sin la aprobación explícita de Johel.
- No modificar los números de la nota a mano: todo sale de `code/run_all.py`.
- No subir `.venv`, cachés ni archivos temporales.
