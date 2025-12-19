# Arabic's Words decoding (LV2)

LV2 is a focused **Arabic ingest + decoding** workspace designed to support **biconsonantal (2-letter) root** analysis.

Core LV2 idea:

- Standard Arabic roots are typically 3 (or 4) letters.
- LV2 assumes many 3-letter roots can be grouped under a deeper **binary nucleus** (the first “real” 2 radicals), with later letters shaping nuance.
- The goal of this level is to build a wide-coverage Arabic word list with root metadata, then **regroup words into binary-root-centered clusters** using algorithms that fit the purpose (heuristics, SONAR/CANINE embeddings, and/or graph-based methods).

## Graph view (planned)

LV2 also aims to produce a **graph-friendly representation** of Arabic word relationships so they can be explored visually and/or fed into a GraphRAG-style system (within-group links and cross-group links scored by distance/similarity).

The intended graph primitives are:

- Nodes: `lemma`, `root`, `binary_root`
- Edges: `lemma -> root`, `root -> binary_root`, plus optional derived links (shared pattern, shared semantic cluster, etc.)

## Repo policy (important)

- Large datasets under `data/raw/` and generated tables under `data/processed/` are **not committed by default** (see `.gitignore`).
- Small, versioned reference assets can live under `resources/`.

## Quickstart (PowerShell)

- Setup (optional): `powershell -ExecutionPolicy Bypass -File scripts/setup.ps1`
- Get canonical processed Arabic tables from LV0 (data core), then run LV2 clustering/graph scripts in this repo.
- Graph export (nodes + edges): `python "scripts/graph/export_binary_root_graph.py" --input <binary_root_lexicon.jsonl>`

LV0 repo: `https://github.com/YassineTemessek/LinguisticDataCore-LV0`
