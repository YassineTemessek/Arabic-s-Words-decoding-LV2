"""
Orchestrator to run LV2 ingestion scripts.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


INGEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = INGEST_DIR

CANONICAL_OUTPUTS: tuple[Path, ...] = (
    Path("data/processed/arabic/quran_lemmas_enriched.jsonl"),
    Path("data/processed/arabic/word_root_map_filtered.jsonl"),
    Path("data/processed/arabic/hf_roots.jsonl"),
    Path("data/processed/arabic/arabic_words_binary_roots.jsonl"),
)


@dataclass(frozen=True)
class Step:
    name: str
    tags: frozenset[str]
    cmd: list[str]
    required_all_inputs: tuple[Path, ...] = ()
    required_any_inputs: tuple[Path, ...] = ()
    outputs: tuple[Path, ...] = ()


def _iter_requested(items: Iterable[str]) -> set[str]:
    out: set[str] = set()
    for item in items:
        for part in str(item).split(","):
            part = part.strip()
            if part:
                out.add(part)
    return out


def _exists_any(paths: Iterable[Path]) -> bool:
    for p in paths:
        if p.exists():
            return True
    return False


def _file_stats(path: Path) -> dict[str, Any]:
    try:
        st = path.stat()
    except FileNotFoundError:
        return {"path": str(path), "exists": False}
    return {"path": str(path), "exists": True, "bytes": st.st_size}


def build_steps(*, python_exe: str, repo_root: Path, resources_dir: Path | None) -> list[Step]:
    data_raw = repo_root / "data" / "raw"
    data_processed = repo_root / "data" / "processed"

    word_root_map_csv = (resources_dir / "word_root_map.csv") if resources_dir else (data_raw / "arabic" / "word_root_map.csv")
    hf_roots_parquet = (
        resources_dir / "arabic_roots_hf" / "train-00000-of-00001.parquet"
        if resources_dir
        else data_raw / "arabic" / "arabic_roots_hf" / "train-00000-of-00001.parquet"
    )

    return [
        Step(
            name="arabic:ingest_quran_morphology",
            tags=frozenset({"arabic"}),
            cmd=[
                python_exe,
                str(SCRIPTS_DIR / "ingest_quran_morphology.py"),
                "--input",
                str(data_raw / "arabic" / "quran-morphology" / "quran-morphology.txt"),
                "--output",
                str(data_processed / "_intermediate" / "arabic" / "quran_lemmas.jsonl"),
            ],
            required_all_inputs=(data_raw / "arabic" / "quran-morphology" / "quran-morphology.txt",),
            outputs=(data_processed / "_intermediate" / "arabic" / "quran_lemmas.jsonl",),
        ),
        Step(
            name="arabic:enrich_quran_translit",
            tags=frozenset({"arabic"}),
            cmd=[
                python_exe,
                str(SCRIPTS_DIR / "enrich_quran_translit.py"),
                "--input",
                str(data_processed / "_intermediate" / "arabic" / "quran_lemmas.jsonl"),
                "--output",
                str(data_processed / "arabic" / "quran_lemmas_enriched.jsonl"),
            ],
            required_all_inputs=(data_processed / "_intermediate" / "arabic" / "quran_lemmas.jsonl",),
            outputs=(data_processed / "arabic" / "quran_lemmas_enriched.jsonl",),
        ),
        Step(
            name="arabic:ingest_word_root_map",
            tags=frozenset({"arabic"}),
            cmd=[
                python_exe,
                str(SCRIPTS_DIR / "ingest_arabic_word_root_map.py"),
                "--input",
                str(word_root_map_csv),
                "--output",
                str(data_processed / "_intermediate" / "arabic" / "word_root_map.jsonl"),
            ],
            required_any_inputs=(word_root_map_csv,),
            outputs=(data_processed / "_intermediate" / "arabic" / "word_root_map.jsonl",),
        ),
        Step(
            name="arabic:clean_word_root_map",
            tags=frozenset({"arabic"}),
            cmd=[python_exe, str(SCRIPTS_DIR / "clean_word_root_map.py")],
            required_all_inputs=(data_processed / "_intermediate" / "arabic" / "word_root_map.jsonl",),
            outputs=(data_processed / "arabic" / "word_root_map_filtered.jsonl",),
        ),
        Step(
            name="arabic:ingest_hf_roots",
            tags=frozenset({"arabic"}),
            cmd=[
                python_exe,
                str(SCRIPTS_DIR / "ingest_arabic_hf_roots.py"),
                "--input",
                str(hf_roots_parquet),
                "--output",
                str(data_processed / "arabic" / "hf_roots.jsonl"),
            ],
            required_any_inputs=(hf_roots_parquet,),
            outputs=(data_processed / "arabic" / "hf_roots.jsonl",),
        ),
        Step(
            name="arabic:build_binary_root_lexicon",
            tags=frozenset({"arabic"}),
            cmd=[
                python_exe,
                str(SCRIPTS_DIR / "build_arabic_binary_root_lexicon.py"),
                "--word-root-map",
                str(data_processed / "arabic" / "word_root_map_filtered.jsonl"),
                "--quran-lemmas",
                str(data_processed / "arabic" / "quran_lemmas_enriched.jsonl"),
                "--output",
                str(data_processed / "arabic" / "arabic_words_binary_roots.jsonl"),
            ],
            required_all_inputs=(
                data_processed / "arabic" / "word_root_map_filtered.jsonl",
                data_processed / "arabic" / "quran_lemmas_enriched.jsonl",
            ),
            outputs=(data_processed / "arabic" / "arabic_words_binary_roots.jsonl",),
        ),
    ]


def main() -> None:
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--only", action="append", default=[], help="Comma-separated list of step names or tags to run (e.g., arabic).")
    ap.add_argument("--list", action="store_true", help="List available steps and exit.")
    ap.add_argument("--skip-missing-inputs", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--require-inputs", action="store_true", help="Fail if any required inputs are missing.")
    ap.add_argument("--fail-fast", action="store_true", help="Stop at the first failed step.")
    ap.add_argument("--resources-dir", type=Path, default=None, help="External datasets folder (sets LC_RESOURCES_DIR for subprocesses).")
    ap.add_argument("--write-manifest", action=argparse.BooleanOptionalAction, default=True)
    args = ap.parse_args()

    python_exe = sys.executable
    requested = _iter_requested(args.only)
    resources_dir = Path(args.resources_dir) if args.resources_dir else None
    steps = build_steps(python_exe=python_exe, repo_root=REPO_ROOT, resources_dir=resources_dir)

    if args.list:
        for step in steps:
            tag_str = ", ".join(sorted(step.tags))
            print(f"- {step.name} ({tag_str})")
        return

    manifest: dict[str, Any] = {
        "type": "ingest_run",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "python": sys.version.replace("\n", " "),
        "python_executable": python_exe,
        "resources_dir": str(resources_dir) if resources_dir else None,
        "requested": sorted(requested),
        "steps": [],
        "outputs": [],
    }

    env = os.environ.copy()
    if resources_dir:
        env["LC_RESOURCES_DIR"] = str(resources_dir)

    skip_missing = bool(args.skip_missing_inputs) and (not bool(args.require_inputs))
    any_failed = False

    for step in steps:
        if requested and (step.name not in requested) and not (step.tags & requested):
            manifest["steps"].append({"name": step.name, "status": "skipped", "reason": "not_selected"})
            continue

        missing_all = [str(p) for p in step.required_all_inputs if not p.exists()]
        any_group_missing = bool(step.required_any_inputs) and (not _exists_any(step.required_any_inputs))
        missing_inputs: list[str] = missing_all[:]
        if any_group_missing:
            missing_inputs.extend(str(p) for p in step.required_any_inputs)

        if missing_inputs:
            if skip_missing:
                manifest["steps"].append({"name": step.name, "status": "skipped", "reason": "missing_inputs", "missing_inputs": missing_inputs})
                continue
            manifest["steps"].append({"name": step.name, "status": "failed", "reason": "missing_inputs", "missing_inputs": missing_inputs})
            any_failed = True
            if args.fail_fast:
                break
            continue

        print("Running:", " ".join(str(c) for c in step.cmd))
        start = time.time()
        proc = subprocess.run(step.cmd, cwd=str(REPO_ROOT), env=env, check=False)
        dur_s = round(time.time() - start, 3)
        status = "ok" if proc.returncode == 0 else "failed"
        manifest["steps"].append({"name": step.name, "status": status, "returncode": proc.returncode, "duration_s": dur_s, "cmd": step.cmd})
        if proc.returncode != 0:
            any_failed = True
            if args.fail_fast:
                break

    for out_path in CANONICAL_OUTPUTS:
        manifest["outputs"].append(_file_stats(REPO_ROOT / out_path))

    if args.write_manifest:
        out_dir = REPO_ROOT / "outputs" / "manifests"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"ingest_run_{ts}.json"
        out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Wrote manifest:", out_path)

    raise SystemExit(2 if any_failed else 0)


if __name__ == "__main__":
    main()
