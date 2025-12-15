# Start Here (LV2)

This repo is a **data pipeline** for Arabic decoding with a specific LV2 focus:

- Build processed Arabic tables that maximize coverage of Arabic words/lemmas with known roots.
- Derive a **binary root** key (2-letter nucleus) from the provided root so downstream algorithms can regroup word families under that nucleus.
- Export a **graph view** (nodes/edges) so relationships are easy to inspect visually and can later support GraphRAG-style workflows.

Workflow:

1) Put raw datasets under `data/raw/` (not committed).
2) Run ingest to create canonical processed JSONL under `data/processed/` (not committed).
3) Validate processed outputs before doing downstream work.

## Core commands

- Ingest (Arabic): `python "OpenAI/scripts/run_ingest_all.py" --only arabic`
- Ingest (Arabic, external resources dir): `python "OpenAI/scripts/run_ingest_all.py" --only arabic --resources-dir "C:/AI Projects/Resources" --require-inputs --fail-fast`
- Validate: `python "OpenAI/scripts/validate_processed.py" --all --require-files`
- Export graph (nodes + edges): `python "OpenAI/scripts/export_binary_root_graph.py"`
