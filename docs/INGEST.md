# Ingest (LV2)

Ingest scripts live under `OpenAI/scripts/` and write processed outputs under `data/processed/`.

Canonical outputs and schema expectations are documented in `data/processed/README.md`.

## Graph exports (LV2)

After generating `data/processed/arabic/arabic_words_binary_roots.jsonl`, you can export a graph-friendly view:

- Nodes + edges CSVs: `python "OpenAI/scripts/export_binary_root_graph.py"`

