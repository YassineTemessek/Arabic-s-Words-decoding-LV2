# Start Here (LV2)

This repo is a **data pipeline** for Arabic decoding with a specific LV2 focus:

- Build processed Arabic tables that maximize coverage of Arabic words/lemmas with known roots.
- Derive a **binary root** key (2-letter nucleus) from the provided root so words can be regrouped into binary-root-centered clusters.
- Run clustering/regrouping experiments using methods that fit the purpose (heuristics, embeddings like SONAR/CANINE, and graph-based approaches).
- Export a **graph view** (nodes/edges) so relationships are easy to inspect visually and can support GraphRAG-style workflows.

Workflow:

1) Put raw datasets under `data/raw/` (not committed).
2) Run ingest to create canonical processed JSONL under `data/processed/` (not committed).
3) Validate processed outputs before doing downstream work.

## Core commands

- Setup (optional): `powershell -ExecutionPolicy Bypass -File scripts/setup.ps1`
- Ingest (Arabic): `python "scripts/ingest/run_ingest_all.py" --only arabic`
- Ingest (Arabic, external resources dir): `python "scripts/ingest/run_ingest_all.py" --only arabic --resources-dir "C:/AI Projects/Resources" --require-inputs --fail-fast`
- Validate: `python "scripts/ingest/validate_processed.py" --all --require-files`
- Export graph (nodes + edges): `python "scripts/ingest/export_binary_root_graph.py"`
