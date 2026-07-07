"""Retrieval-only benchmark for hybrid search — NOT pytest-collected.

Embeds each benchmark query (same path as the backend) and calls
match_chunks_hybrid DIRECTLY against the eval KB — no generation, no chat
endpoint, no LLM nondeterminism. Asserts the expected section appears at
rank <= rank_threshold in the RRF-fused results, and prints, per query, the
expected section's fused rank, its RRF score, its per-channel (vector/FTS)
ranks, and the margin to the rank cutoff — so before/after is publishable.

Prerequisites:
  - Migration 002 (match_chunks_hybrid + the fts column) applied to the KB's DB.
  - backend/.env populated: SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY.

Usage:
    python run_retrieval_benchmark.py

Exit code 0 if every query passes, 1 otherwise.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env into the environment BEFORE importing app.config (whose
# Settings() reads from the environment), so this runs from any CWD.
BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env", override=False)

from app.config import settings  # noqa: E402
from app.services.embedding import embed_texts  # noqa: E402
from supabase import create_client  # noqa: E402

# Windows consoles default to cp1252; force utf-8 so section titles never crash a run.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EVAL_DIR = Path(__file__).resolve().parent
BENCHMARK_PATH = EVAL_DIR / "retrieval_benchmark.json"


def _rank_of_section(rows: list[dict], expected_section: int) -> tuple[int | None, dict | None]:
    """Return the 1-based fused rank (and row) of the expected chunk_index."""
    for position, row in enumerate(rows, start=1):
        if row.get("chunk_index") == expected_section:
            return position, row
    return None, None


def _run_query(supabase, kb_id: str, query: str, embedding: list[float]) -> list[dict]:
    """Call match_chunks_hybrid and return the fused rows in RRF order."""
    result = supabase.rpc(
        "match_chunks_hybrid",
        {"p_kb_id": kb_id, "p_query_embedding": embedding, "p_query_text": query},
    ).execute()
    return result.data or []


def _fmt_row(position: int, row: dict) -> str:
    meta = row.get("metadata") or {}
    return (
        f"    {position}. sec {str(row.get('chunk_index')):>2} | "
        f"rrf={row.get('rrf_score', 0):.5f} | "
        f"vec_rank={str(row.get('vector_rank')):>4} | "
        f"fts_rank={str(row.get('fts_rank')):>4} | "
        f"sim={row.get('similarity', 0):.3f} | {meta.get('title', '?')}"
    )


def evaluate(spec: dict) -> tuple[list[dict], bool]:
    kb_id = spec["kb_id"]
    threshold = spec.get("rank_threshold", 3)
    queries = spec["queries"]

    supabase = create_client(settings.supabase_url, settings.supabase_service_key)
    embeddings = asyncio.run(embed_texts([q["query"] for q in queries]))

    results: list[dict] = []
    all_pass = True

    for query_spec, embedding in zip(queries, embeddings):
        query = query_spec["query"]
        expected = query_spec["expected_section"]
        rows = _run_query(supabase, kb_id, query, embedding)
        rank, row = _rank_of_section(rows, expected)
        passed = rank is not None and rank <= threshold
        all_pass = all_pass and passed

        # Margin: how much RRF headroom the expected section has over the first
        # row that just misses the cutoff (positive => comfortably inside top-N).
        cutoff_row = rows[threshold] if len(rows) > threshold else None
        margin = None
        if row is not None and cutoff_row is not None:
            margin = row.get("rrf_score", 0) - cutoff_row.get("rrf_score", 0)

        results.append({
            "query": query,
            "expected_section": expected,
            "expected_title": query_spec.get("expected_title"),
            "note": query_spec.get("note"),
            "rank": rank,
            "passed": passed,
            "rrf_score": row.get("rrf_score") if row else None,
            "vector_rank": row.get("vector_rank") if row else None,
            "fts_rank": row.get("fts_rank") if row else None,
            "similarity": row.get("similarity") if row else None,
            "margin_to_cutoff": margin,
            "fused": [
                {
                    "chunk_index": r.get("chunk_index"),
                    "title": (r.get("metadata") or {}).get("title"),
                    "rrf_score": r.get("rrf_score"),
                    "vector_rank": r.get("vector_rank"),
                    "fts_rank": r.get("fts_rank"),
                    "similarity": r.get("similarity"),
                }
                for r in rows
            ],
        })

        status = "PASS" if passed else "FAIL"
        print(f"\n[{status}] {query}")
        print(
            f"    expected section {expected} "
            f"({query_spec.get('expected_title', '?')}) at rank "
            f"{rank if rank is not None else 'NOT RETRIEVED'} (cutoff <= {threshold})"
        )
        if row is not None:
            story = (
                f"    vector_rank={row.get('vector_rank')} fts_rank={row.get('fts_rank')} "
                f"-> fused_rank={rank} | rrf={row.get('rrf_score', 0):.5f}"
            )
            if margin is not None:
                story += f" | margin_to_cutoff={margin:+.5f}"
            print(story)
        print("    fused results:")
        for position, r in enumerate(rows, start=1):
            print(_fmt_row(position, r))

    return results, all_pass


def write_report(path: Path, spec: dict, results: list[dict], all_pass: bool) -> None:
    lines = ["# Hybrid Retrieval Benchmark", ""]
    lines.append(
        f"Benchmark: `{spec.get('benchmark')}` · KB: `{spec['kb_id']}` · "
        f"cutoff: rank <= {spec.get('rank_threshold', 3)}"
    )
    passed = sum(1 for r in results if r["passed"])
    lines.append(f"\n**{passed}/{len(results)} queries passed.** "
                 f"Overall: {'PASS' if all_pass else 'FAIL'}")
    lines.append("")
    lines.append("| Query | Expected | Rank | vec | fts | RRF | Margin | Result |")
    lines.append("|-------|----------|------|-----|-----|-----|--------|--------|")
    for r in results:
        rrf = f"{r['rrf_score']:.5f}" if r["rrf_score"] is not None else "-"
        margin = f"{r['margin_to_cutoff']:+.5f}" if r["margin_to_cutoff"] is not None else "-"
        lines.append(
            f"| {r['query']} | {r['expected_section']} | "
            f"{r['rank'] if r['rank'] is not None else 'MISS'} | "
            f"{r['vector_rank']} | {r['fts_rank']} | {rrf} | {margin} | "
            f"{'PASS' if r['passed'] else 'FAIL'} |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not BENCHMARK_PATH.exists():
        print(f"Benchmark spec not found: {BENCHMARK_PATH}")
        sys.exit(1)
    spec = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))

    results, all_pass = evaluate(spec)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = EVAL_DIR / f"retrieval_benchmark_report_{timestamp}.md"
    results_path = EVAL_DIR / f"retrieval_benchmark_results_{timestamp}.json"
    write_report(report_path, spec, results, all_pass)
    results_path.write_text(
        json.dumps({"benchmark": spec.get("benchmark"), "kb_id": spec["kb_id"],
                    "timestamp": timestamp, "all_pass": all_pass, "results": results},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    passed = sum(1 for r in results if r["passed"])
    print(f"\n{'=' * 60}")
    print(f"RESULT: {passed}/{len(results)} passed | overall {'PASS' if all_pass else 'FAIL'}")
    print(f"Report: {report_path}")
    print(f"Results: {results_path}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
