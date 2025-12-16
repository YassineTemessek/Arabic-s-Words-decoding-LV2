param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

& $Python OpenAI/scripts/validate_processed.py data/processed/arabic/quran_lemmas_enriched.jsonl data/processed/arabic/word_root_map_filtered.jsonl data/processed/arabic/arabic_words_binary_roots.jsonl
& $Python OpenAI/scripts/export_binary_root_graph.py

