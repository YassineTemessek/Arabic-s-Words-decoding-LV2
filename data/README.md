# Data folder (LV2)

This project uses large datasets under `data/`. They are intentionally **not committed** by default (see `.gitignore`).

## `data/raw/` (inputs)

Expected inputs (examples):

- `data/raw/arabic/quran-morphology/quran-morphology.txt`

If you keep datasets outside this repo, set `LC_RESOURCES_DIR` or pass `--resources-dir` to `OpenAI/scripts/run_ingest_all.py`.

## `data/processed/` (outputs)

Generated, machine-readable JSONL outputs consumed by downstream tooling.

