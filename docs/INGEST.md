# Ingest (LV0)

LV2 does not own ingest anymore.

Raw → processed canonical datasets live in LV0 (data core):

- `https://github.com/YassineTemessek/LinguisticDataCore-LV0`

LV2 consumes processed datasets (for example, a binary-root lexicon JSONL) and focuses on clustering/regrouping + graph exports.

## Graph exports (LV2)

Given an Arabic binary-root lexicon JSONL, export a graph-friendly view:

- Nodes + edges CSVs: `python "scripts/graph/export_binary_root_graph.py" --input <binary_root_lexicon.jsonl>`
