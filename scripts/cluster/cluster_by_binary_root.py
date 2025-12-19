"""
Discovery clustering for Arabic based on LV0-provided `binary_root`.

Purpose (LV2 discovery):
  - Group words by `binary_root`
  - Within each group, produce coarse subclusters using lightweight similarities
    (no heavy model downloads required).

Inputs (default):
  - data/processed/arabic/arabic_words_binary_roots.jsonl

Outputs (default):
  - outputs/clusters/binary_root_lemma_clusters.jsonl
  - outputs/clusters/binary_root_similarity_edges.csv

Notes:
  - This is discovery-first and intentionally simple. Later we can replace
    similarity functions with embedding-based ones (SONAR/CANINE) while keeping
    the same output contracts.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


AR_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
WS_RE = re.compile(r"\s+")


def strip_arabic_diacritics(text: str) -> str:
    return AR_DIACRITICS_RE.sub("", text or "")


def norm_text(text: str) -> str:
    text = (text or "").strip()
    text = WS_RE.sub(" ", text)
    return text


def char_ngrams(text: str, *, n: int = 2) -> set[str]:
    text = strip_arabic_diacritics(norm_text(text))
    text = text.replace(" ", "")
    if len(text) < n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(0, len(text) - n + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return float(inter) / float(union) if union else 0.0


def token_set(text: str) -> set[str]:
    text = norm_text(text).lower()
    if not text:
        return set()
    return {t for t in re.split(r"[^0-9a-zA-Z\u0600-\u06FF]+", text) if t}


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


@dataclass(frozen=True)
class LemmaRow:
    lemma: str
    language: str
    script: str
    stage: str
    source: str
    root_norm: str
    binary_root: str
    translit: str
    ipa: str
    gloss: str


class DSU:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1


def cluster_indices(sim_matrix: list[list[float]], *, threshold: float) -> list[int]:
    n = len(sim_matrix)
    dsu = DSU(n)
    for i in range(n):
        for j in range(i + 1, n):
            if sim_matrix[i][j] >= threshold:
                dsu.union(i, j)
    roots = [dsu.find(i) for i in range(n)]
    # map root -> compact cluster id
    root_to_cluster: dict[int, int] = {}
    next_id = 0
    out: list[int] = []
    for r in roots:
        cid = root_to_cluster.get(r)
        if cid is None:
            cid = next_id
            root_to_cluster[r] = cid
            next_id += 1
        out.append(cid)
    return out


def build_similarity(rows: list[LemmaRow]) -> tuple[list[list[float]], list[list[float]]]:
    # form: char bigram jaccard on lemma (Arabic script)
    # meaning: token jaccard on gloss (or empty)
    form_feats = [char_ngrams(r.lemma, n=2) for r in rows]
    meaning_feats = [token_set(r.gloss) for r in rows]

    n = len(rows)
    form_sim = [[0.0] * n for _ in range(n)]
    meaning_sim = [[0.0] * n for _ in range(n)]
    for i in range(n):
        form_sim[i][i] = 1.0
        meaning_sim[i][i] = 1.0
        for j in range(i + 1, n):
            fs = jaccard(form_feats[i], form_feats[j])
            ms = jaccard(meaning_feats[i], meaning_feats[j])
            form_sim[i][j] = form_sim[j][i] = fs
            meaning_sim[i][j] = meaning_sim[j][i] = ms
    return form_sim, meaning_sim


def main() -> None:
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--input", type=Path, default=Path("data/processed/arabic/arabic_words_binary_roots.jsonl"))
    ap.add_argument("--out-dir", type=Path, default=Path("outputs/clusters"))
    ap.add_argument("--form-threshold", type=float, default=0.55, help="Within-binary_root threshold for form subclusters.")
    ap.add_argument("--meaning-threshold", type=float, default=0.35, help="Within-binary_root threshold for meaning subclusters (requires gloss/definition).")
    ap.add_argument("--max-group", type=int, default=400, help="Skip similarity+subclustering for very large binary_root groups.")
    args = ap.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Missing input: {args.input}")

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    clusters_out = out_dir / "binary_root_lemma_clusters.jsonl"
    edges_out = out_dir / "binary_root_similarity_edges.csv"

    groups: dict[str, list[LemmaRow]] = defaultdict(list)
    total_in = 0
    for rec in iter_jsonl(args.input):
        total_in += 1
        br = str(rec.get("binary_root") or "").strip()
        if not br:
            continue
        groups[br].append(
            LemmaRow(
                lemma=str(rec.get("lemma") or "").strip(),
                language=str(rec.get("language") or "").strip(),
                script=str(rec.get("script") or "").strip(),
                stage=str(rec.get("stage") or "").strip(),
                source=str(rec.get("source") or "").strip(),
                root_norm=str(rec.get("root_norm") or rec.get("root") or "").strip(),
                binary_root=br,
                translit=str(rec.get("translit") or "").strip(),
                ipa=str(rec.get("ipa") or rec.get("ipa_raw") or "").strip(),
                gloss=str(rec.get("gloss_plain") or rec.get("gloss") or rec.get("definition") or "").strip(),
            )
        )

    edge_fieldnames = ["binary_root", "src_lemma", "dst_lemma", "form_sim", "meaning_sim"]
    wrote_rows = 0
    wrote_edges = 0

    with clusters_out.open("w", encoding="utf-8") as out_f, edges_out.open("w", encoding="utf-8", newline="") as edges_f:
        edges_w = csv.DictWriter(edges_f, fieldnames=edge_fieldnames)
        edges_w.writeheader()

        for br, rows in sorted(groups.items(), key=lambda kv: (kv[0], len(kv[1]))):
            if not rows:
                continue
            if len(rows) > int(args.max_group):
                # emit rows without subclusters for huge groups (discovery safety)
                for r in rows:
                    out_f.write(
                        json.dumps(
                            {
                                "binary_root": br,
                                "lemma": r.lemma,
                                "root_norm": r.root_norm,
                                "form_cluster": None,
                                "meaning_cluster": None,
                                "language": r.language,
                                "stage": r.stage,
                                "script": r.script,
                                "source": r.source,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    wrote_rows += 1
                continue

            form_sim, meaning_sim = build_similarity(rows)
            form_clusters = cluster_indices(form_sim, threshold=float(args.form_threshold))
            meaning_clusters = cluster_indices(meaning_sim, threshold=float(args.meaning_threshold))

            # Emit per-lemma cluster assignments
            for idx, r in enumerate(rows):
                out_f.write(
                    json.dumps(
                        {
                            "binary_root": br,
                            "lemma": r.lemma,
                            "root_norm": r.root_norm,
                            "form_cluster": int(form_clusters[idx]),
                            "meaning_cluster": int(meaning_clusters[idx]),
                            "language": r.language,
                            "stage": r.stage,
                            "script": r.script,
                            "source": r.source,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                wrote_rows += 1

            # Emit similarity edges for inspection (all pairs)
            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    edges_w.writerow(
                        {
                            "binary_root": br,
                            "src_lemma": rows[i].lemma,
                            "dst_lemma": rows[j].lemma,
                            "form_sim": f"{form_sim[i][j]:.6f}",
                            "meaning_sim": f"{meaning_sim[i][j]:.6f}",
                        }
                    )
                    wrote_edges += 1

    print(f"Read {total_in} rows, grouped into {len(groups)} binary_root buckets.")
    print(f"Wrote clusters: {clusters_out} (rows={wrote_rows})")
    print(f"Wrote edges:    {edges_out} (edges={wrote_edges})")


if __name__ == "__main__":
    main()

