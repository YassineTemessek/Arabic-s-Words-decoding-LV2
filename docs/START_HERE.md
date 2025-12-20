# Start Here (LV2)

This repo is a **data pipeline** for Arabic decoding with a specific LV2 focus:

- Build processed Arabic tables that maximize coverage of Arabic words/lemmas with known roots.
- Derive a **binary root** key (2-letter nucleus) from the provided root so words can be regrouped into binary-root-centered clusters.
- Run clustering/regrouping experiments using methods that fit the purpose (heuristics, embeddings like SONAR/CANINE, and graph-based approaches).
- Export a **graph view** (nodes/edges) so relationships are easy to inspect visually and can support GraphRAG-style workflows.

Workflow:

1) Build/fetch canonical processed datasets in LV0 (data core).
2) Run LV2 clustering/regrouping and graph exports using those processed tables.

## Core commands

- Setup (optional): `powershell -ExecutionPolicy Bypass -File scripts/setup.ps1`
- LV0 (data core): `https://github.com/YassineTemessek/LinguisticDataCore-LV0`
- In LV0, the Arabic ingest produces a ready lexicon with `binary_root`: `data/processed/arabic/classical/arabic_words_binary_roots.jsonl`
- Cluster within each `binary_root` (discovery): `python "scripts/cluster/cluster_by_binary_root.py"`
- Export graph (nodes + edges): `python "scripts/graph/export_binary_root_graph.py" --input <binary_root_lexicon.jsonl>`
