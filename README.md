# Arabic's Words decoding (LV2)

LV2 is a focused **Arabic ingest + decoding** workspace designed to support **biconsonantal (2-letter) root** analysis.

Core LV2 idea:

- Standard Arabic roots are typically 3 (or 4) letters.
- LV2 assumes many 3-letter roots can be grouped under a deeper **binary nucleus** (the first “real” 2 radicals), with later letters shaping nuance.
- The goal of this level is to build a wide-coverage Arabic word list with root metadata so a later algorithm can regroup words by **binary root**.

## Graph view (planned)

LV2 also aims to produce a **graph-friendly representation** of Arabic word relationships so they can later be explored visually and/or fed into a GraphRAG-style system.

The intended graph primitives are:

- Nodes: `lemma`, `root`, `binary_root`
- Edges: `lemma -> root`, `root -> binary_root`, plus optional derived links (shared pattern, shared semantic cluster, etc.)

## Repo policy (important)

- Large datasets under `data/raw/` and generated tables under `data/processed/` are **not committed by default** (see `.gitignore`).
- Small, versioned reference assets can live under `resources/`.

## Quickstart (PowerShell)

- Setup (optional): `powershell -ExecutionPolicy Bypass -File scripts/setup.ps1`
- Ingest Arabic tables: `python "OpenAI/scripts/run_ingest_all.py" --only arabic`
- Validate canonical outputs: `python "OpenAI/scripts/validate_processed.py" --all`
- Smoke (committed processed + graph export): `powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1`

If you keep big inputs outside the repo, pass `--resources-dir "C:/AI Projects/Resources"` to `run_ingest_all.py`.
