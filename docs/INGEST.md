# Ingest (LV2)

Ingest scripts live under `OpenAI/scripts/` and write processed outputs under `data/processed/`.

Canonical outputs and schema expectations are documented in `data/processed/README.md`.

## Inputs (where to put them)

This repo supports two equivalent layouts:

1) **Repo-local** under `data/raw/`:
   - `data/raw/arabic/quran-morphology/quran-morphology.txt`
   - `data/raw/arabic/word_root_map.csv`
   - `data/raw/arabic/arabic_roots_hf/train-00000-of-00001.parquet`

2) **External resources dir** (recommended for big files):
   - Set `LC_RESOURCES_DIR=C:\AI Projects\Resources` (or pass `--resources-dir` to `run_ingest_all.py`)
   - Place:
     - `%LC_RESOURCES_DIR%/word_root_map.csv`
     - `%LC_RESOURCES_DIR%/arabic_roots_hf/train-00000-of-00001.parquet`

`quran-morphology.txt` is expected under `data/raw/` (it is small enough to keep local), but you can also keep it externally and symlink/copy it in.

## Dependencies

- Most scripts (binary-root build + graph export) are **stdlib only**.
- The HF parquet ingest step needs: `pandas` + `pyarrow` (see `requirements-ingest.txt`).

## Graph exports (LV2)

After generating `data/processed/arabic/arabic_words_binary_roots.jsonl`, you can export a graph-friendly view:

- Nodes + edges CSVs: `python "OpenAI/scripts/export_binary_root_graph.py"`
