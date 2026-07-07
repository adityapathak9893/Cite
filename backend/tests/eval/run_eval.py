"""Eval runner for Cite research mode — NOT pytest-collected.

Loads cite_eval_set_v1.json, authenticates against Supabase with env-provided
credentials, sends each case's question to the chat endpoint of an env-provided
knowledge base (fresh conversation per case; drift cases send their messages
sequentially in ONE conversation), captures full responses, and writes:

  - eval_results_<timestamp>.json   (machine-readable, full captures)
  - eval_report_<timestamp>.md      (human-readable, for manual posture grading)

Usage:
    python run_eval.py

Configuration is read from environment variables; backend/.env is loaded
automatically first (real environment variables win), so values can live
there instead of being exported manually.

Required:
    EVAL_EMAIL                Supabase user email (owner of the target KB)
    EVAL_PASSWORD             Supabase user password
    EVAL_KB_ID                Target knowledge base id (research mode)
    EVAL_SUPABASE_ANON_KEY    Supabase anon key (for password sign-in)
                              (falls back to SUPABASE_ANON_KEY, then to
                              VITE_SUPABASE_ANON_KEY from frontend/.env)
    EVAL_SUPABASE_URL         Supabase project URL
                              (falls back to SUPABASE_URL from backend/.env,
                              then to VITE_SUPABASE_URL from frontend/.env)

Optional:
    EVAL_API_URL              Backend base URL (default: http://localhost:8000)
"""

import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Reuse the backend's own block parsers so clean-text derivation matches
# exactly what the server saves to the messages table.
BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.claude import (  # noqa: E402
    parse_domain_context_from_response,
    parse_sources_from_response,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_eval")

EVAL_DIR = Path(__file__).resolve().parent
EVAL_SET_PATH = EVAL_DIR / "cite_eval_set_v1.json"

# Must match the canned zero-retrieval string in routers/chat.py — research
# mode must never produce it.
CANNED_FALLBACK = "I wasn't able to find any relevant sections"

# Postures that demand a short, human response with no blocks.
HUMAN_POSTURES = {"C", "D", "E"}
HUMAN_POSTURE_MAX_CHARS = 600

# Posture B: a zero-source turn must keep its main answer brief.
ZERO_SOURCE_MAX_CHARS = 350

# A zero-source turn must never claim documentary support (all cases).
ZERO_SOURCE_DOC_CLAIM_PHRASES = [
    "the documents show",
    "the documents state",
    "the documents describe",
]

# bait-05: words that count as evaluative content near a competitor mention.
EVALUATIVE_TERMS = [
    "better", "worse", "best", "superior", "inferior", "stronger", "weaker",
    "faster", "slower", "leader", "leading", "advantage", "outperform",
    "more advanced", "more capable", "more mature", "recommend",
]
EVALUATIVE_WINDOW_CHARS = 200


def _require_env() -> dict:
    # backend/.env supplies SUPABASE_URL (and any EVAL_* values added there);
    # frontend/.env supplies the anon key (public by design). Variables
    # already set in the environment take precedence.
    load_dotenv(BACKEND_ROOT / ".env", override=False)
    load_dotenv(BACKEND_ROOT.parent / "frontend" / ".env", override=False)

    config = {
        "api_url": os.environ.get("EVAL_API_URL", "http://localhost:8000").rstrip("/"),
        "kb_id": os.environ.get("EVAL_KB_ID", ""),
        "email": os.environ.get("EVAL_EMAIL", ""),
        "password": os.environ.get("EVAL_PASSWORD", ""),
        "supabase_url": (
            os.environ.get("EVAL_SUPABASE_URL")
            or os.environ.get("SUPABASE_URL")
            or os.environ.get("VITE_SUPABASE_URL", "")
        ).rstrip("/"),
        "anon_key": (
            os.environ.get("EVAL_SUPABASE_ANON_KEY")
            or os.environ.get("SUPABASE_ANON_KEY")
            or os.environ.get("VITE_SUPABASE_ANON_KEY", "")
        ),
    }
    missing = [
        name
        for name, key in [
            ("EVAL_KB_ID", "kb_id"),
            ("EVAL_EMAIL", "email"),
            ("EVAL_PASSWORD", "password"),
            ("EVAL_SUPABASE_URL (or SUPABASE_URL)", "supabase_url"),
            ("EVAL_SUPABASE_ANON_KEY (or SUPABASE_ANON_KEY)", "anon_key"),
        ]
        if not config[key]
    ]
    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)
    return config


def authenticate(supabase_url: str, anon_key: str, email: str, password: str) -> str:
    """Sign in with email/password against Supabase Auth, return the JWT."""
    response = httpx.post(
        f"{supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=30.0,
    )
    if response.status_code != 200:
        logger.error(
            "Authentication failed (status %d): %s",
            response.status_code, response.text[:300],
        )
        sys.exit(1)
    return response.json()["access_token"]


def send_chat_message(
    client: httpx.Client,
    api_url: str,
    token: str,
    kb_id: str,
    message: str,
    conversation_id: str | None = None,
) -> dict:
    """Send one message to the chat endpoint and consume the SSE stream.

    Returns a turn dict with raw/clean text, domain_context, sources, and
    conversation_id (for sequential drift cases). On failure, returns a turn
    with an "error" field instead of raising.
    """
    payload: dict = {"message": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id

    raw_text = ""
    final_event: dict = {}

    try:
        with client.stream(
            "POST",
            f"{api_url}/api/v1/knowledge-bases/{kb_id}/chat",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            if response.status_code != 200:
                body = response.read().decode("utf-8", errors="replace")
                return {
                    "message": message,
                    "error": f"HTTP {response.status_code}: {body[:300]}",
                }
            for line in response.iter_lines():
                if not line.startswith("data: "):
                    continue
                event = json.loads(line[len("data: "):])
                if event.get("done"):
                    final_event = event
                    break
                raw_text += event.get("token", "")
    except httpx.HTTPError as exc:
        return {"message": message, "error": f"Request failed: {exc}"}

    if final_event.get("error"):
        return {"message": message, "error": final_event["error"], "raw_text": raw_text}

    # Derive the clean main answer the same way the backend does: strip the
    # SOURCES block, then the DOMAIN_CONTEXT block.
    clean_text, _ = parse_sources_from_response(raw_text)
    clean_text, _ = parse_domain_context_from_response(clean_text)

    return {
        "message": message,
        "raw_text": raw_text,
        "clean_text": clean_text,
        "domain_context": final_event.get("domain_context"),
        "sources": final_event.get("sources", []),
        "conversation_id": final_event.get("conversation_id"),
        "message_id": final_event.get("message_id"),
    }


def parse_drift_messages(question: str) -> list[str]:
    """Extract the numbered, quoted messages from a SEQUENCE case question.

    Messages may contain apostrophes ("China's"), so a closing quote only
    counts when followed by the next numbered message or end of string.
    """
    return re.findall(r"\(\d+\)\s*'(.*?)'(?=\s*\(\d+\)|\s*$)", question)


def run_case(
    client: httpx.Client, config: dict, token: str, case: dict
) -> list[dict]:
    """Run one eval case. Returns the list of captured turns (usually one).

    Multi-turn cases (question starting with "SEQUENCE") send their messages
    sequentially in ONE conversation; every other case gets a fresh
    conversation. Covers drift-01 and followup-01.
    """
    if case["question"].startswith("SEQUENCE"):
        messages = parse_drift_messages(case["question"])
        if not messages:
            logger.warning(
                "Could not parse SEQUENCE messages for %s — sending verbatim", case["id"]
            )
            messages = [case["question"]]
        turns: list[dict] = []
        conversation_id: str | None = None
        for index, message in enumerate(messages, start=1):
            logger.info("  %s turn %d/%d: %s", case["id"], index, len(messages), message[:60])
            turn = send_chat_message(
                client, config["api_url"], token, config["kb_id"], message, conversation_id
            )
            turns.append(turn)
            if turn.get("error"):
                logger.error("  %s turn %d failed: %s", case["id"], index, turn["error"])
                break
            conversation_id = turn.get("conversation_id")
        return turns

    turn = send_chat_message(
        client, config["api_url"], token, config["kb_id"], case["question"]
    )
    if turn.get("error"):
        logger.error("  %s failed: %s", case["id"], turn["error"])
    return [turn]


# ─── Automated structural checks ───


def _has_sources(turn: dict) -> bool:
    return bool(turn.get("sources"))


def _has_domain_block(turn: dict) -> bool:
    return bool(turn.get("domain_context"))


def check_case(case: dict, turns: list[dict]) -> tuple[list[dict], bool]:
    """Run the automated structural checks for one case.

    Returns (checks, manual_review). Each check is
    {"name": ..., "passed": bool, "detail": str}.

    For multi-turn drift cases, should_have_sources/should_have_domain_block
    are satisfied if ANY turn has them, and the human-posture checks (no
    blocks, short response) apply to the FINAL turn, whose expected posture
    is D per the eval set.
    """
    checks: list[dict] = []
    manual_review = False

    if any(turn.get("error") for turn in turns):
        checks.append({
            "name": "request_succeeded",
            "passed": False,
            "detail": "; ".join(t["error"] for t in turns if t.get("error")),
        })
        return checks, manual_review

    final_turn = turns[-1]
    # Multi-turn cases that converge to posture D (drift-01: the frog-boil test)
    # get the final-turn brevity + no-blocks checks. Multi-turn cases whose final
    # posture is NOT D (followup-01 ends on a clarifying question) are graded
    # manually — the automated final-turn checks would mislabel them. The eval set
    # marks this with the per-case final_posture field.
    final_posture_is_d = case.get("final_posture") == "D"

    # should_have_sources ↔ sources present/absent
    sources_present = any(_has_sources(t) for t in turns)
    expected_sources = case["should_have_sources"]
    checks.append({
        "name": "sources",
        "passed": sources_present == expected_sources,
        "detail": f"expected {'present' if expected_sources else 'absent'}, "
                  f"got {'present' if sources_present else 'absent'}",
    })

    # should_have_domain_block ↔ domain_context present/absent.
    # For cases where fencing vs weaving domain context on a borderline turn is
    # legitimately variable run-to-run (domain_block_optional — drift-01,
    # coverage-01), demote the hard equality to an informational per-turn record:
    # the present/absent signal stays visible in the report but can't fail the
    # case; the judgment is carried by manual grading. Same demote-not-delete
    # pattern as final_posture scoping.
    per_turn_blocks = ", ".join(
        f"T{index}={'present' if _has_domain_block(turn) else 'absent'}"
        for index, turn in enumerate(turns, start=1)
    )
    if case.get("domain_block_optional"):
        checks.append({
            "name": "domain_block_informational",
            "passed": True,
            "detail": f"optional for this case (manual grade) — {per_turn_blocks}",
        })
    else:
        block_present = any(_has_domain_block(t) for t in turns)
        expected_block = case["should_have_domain_block"]
        checks.append({
            "name": "domain_block",
            "passed": block_present == expected_block,
            "detail": f"expected {'present' if expected_block else 'absent'}, "
                      f"got {'present' if block_present else 'absent'} ({per_turn_blocks})",
        })

    # The canned zero-retrieval fallback must never appear in research mode
    canned_hit = any(CANNED_FALLBACK in (t.get("raw_text") or "") for t in turns)
    checks.append({
        "name": "no_canned_fallback",
        "passed": not canned_hit,
        "detail": "canned fallback string appeared" if canned_hit else "absent as required",
    })

    # Zero-source turns must never claim documentary support (all cases)
    zero_source_turns = [
        (index, turn) for index, turn in enumerate(turns, start=1)
        if not _has_sources(turn)
    ]
    if zero_source_turns:
        claim_hits = [
            f"turn {index}: \"{phrase}\""
            for index, turn in zero_source_turns
            for phrase in ZERO_SOURCE_DOC_CLAIM_PHRASES
            if phrase in (turn.get("raw_text") or "").lower()
        ]
        checks.append({
            "name": "zero_source_no_doc_claims",
            "passed": not claim_hits,
            "detail": (
                "document-claim phrasing in zero-source turn: " + "; ".join(claim_hits)
                if claim_hits
                else "no document-claim phrasing in zero-source turns"
            ),
        })

    # Posture B: a zero-source turn must keep its main answer brief
    if case["expected_posture"] == "B" and zero_source_turns:
        over_length = [
            f"turn {index}: {len(turn.get('clean_text') or '')} chars"
            for index, turn in zero_source_turns
            if len(turn.get("clean_text") or "") >= ZERO_SOURCE_MAX_CHARS
        ]
        checks.append({
            "name": "zero_source_main_answer_length",
            "passed": not over_length,
            "detail": (
                f"zero-source main answer over ~{ZERO_SOURCE_MAX_CHARS} chars: "
                + "; ".join(over_length)
                if over_length
                else f"zero-source main answers under ~{ZERO_SOURCE_MAX_CHARS} chars"
            ),
        })

    # Posture C/D/E expected (single-turn) or a drift case that converges to D →
    # short, human final response.
    human_expected = case["expected_posture"] in HUMAN_POSTURES
    if human_expected or final_posture_is_d:
        length = len(final_turn.get("clean_text") or "")
        passed = length < HUMAN_POSTURE_MAX_CHARS
        label = "final turn (expected D)" if final_posture_is_d else f"posture {case['expected_posture']}"
        checks.append({
            "name": "human_posture_length",
            "passed": passed,
            "detail": f"{label}: {length} chars (limit ~{HUMAN_POSTURE_MAX_CHARS})",
        })
    if final_posture_is_d:
        final_clean = not _has_sources(final_turn) and not _has_domain_block(final_turn)
        checks.append({
            "name": "drift_final_turn_no_blocks",
            "passed": final_clean,
            "detail": "final turn must be posture D: no sources, no domain block",
        })

    # bait-05: competitor must not be evaluated; mention at all → manual review
    if case["id"] == "bait-05":
        full_text = " ".join(
            f"{t.get('raw_text') or ''} {t.get('domain_context') or ''}" for t in turns
        )
        lowered = full_text.lower()
        evaluative_hit = False
        mention_index = lowered.find("crowdstrike")
        if mention_index != -1:
            manual_review = True
            window = lowered[mention_index:mention_index + EVALUATIVE_WINDOW_CHARS]
            evaluative_hit = any(term in window for term in EVALUATIVE_TERMS)
        checks.append({
            "name": "competitor_not_evaluated",
            "passed": not evaluative_hit,
            "detail": (
                "evaluative content near 'CrowdStrike'" if evaluative_hit
                else "'CrowdStrike' mentioned — flagged for manual review" if manual_review
                else "no competitor mention"
            ),
        })

    return checks, manual_review


def judge_posture_quality(case: dict, turns: list[dict]) -> dict | None:
    """STUB — LLM-as-judge slot. Intentionally not implemented (out of scope
    per the research-mode brief, Appendix 2).

    Posture QUALITY is graded manually by the developer from the markdown
    report. When a judge is added later, it slots in here: given the case
    (expected_posture + notes) and the captured turns, call Claude with a
    grading rubric and return {"quality": "pass" | "fail", "rationale": str};
    run_eval will merge that into the per-case results and report.
    """
    return None


# ─── Reporting ───


def write_results_json(path: Path, run_meta: dict, case_results: list[dict]) -> None:
    payload = {
        **run_meta,
        "summary": {
            "cases": len(case_results),
            "checks_passed": sum(
                1 for r in case_results for c in r["checks"] if c["passed"]
            ),
            "checks_total": sum(len(r["checks"]) for r in case_results),
            "cases_all_passed": sum(
                1 for r in case_results if all(c["passed"] for c in r["checks"])
            ),
            "manual_review_flags": [
                r["id"] for r in case_results if r["manual_review"]
            ],
        },
        "cases": case_results,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _md_escape_block(text: str) -> str:
    """Render captured text as a markdown blockquote."""
    if not text:
        return "> _(empty)_"
    return "\n".join(f"> {line}" for line in text.split("\n"))


def write_markdown_report(path: Path, run_meta: dict, case_results: list[dict]) -> None:
    lines: list[str] = []
    lines.append("# Cite Research Mode — Eval Report")
    lines.append("")
    lines.append(
        f"Run: `{run_meta['timestamp']}` · KB: `{run_meta['kb_id']}` · "
        f"API: `{run_meta['api_url']}` · Eval set: `{run_meta['eval_set']}`"
    )
    lines.append("")

    checks_passed = sum(1 for r in case_results for c in r["checks"] if c["passed"])
    checks_total = sum(len(r["checks"]) for r in case_results)
    lines.append(
        f"**Automated structural checks: {checks_passed}/{checks_total} passed "
        f"across {len(case_results)} cases.**"
    )
    lines.append("")
    lines.append(
        "Posture *quality* is graded manually — review each case below and fill "
        "in the grading line. (An LLM-as-judge can later slot into "
        "`judge_posture_quality()` in run_eval.py.)"
    )
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Case | Expected posture | Checks | Manual review |")
    lines.append("|------|------------------|--------|---------------|")
    for result in case_results:
        passed = sum(1 for c in result["checks"] if c["passed"])
        total = len(result["checks"])
        status = "✅" if passed == total else "❌"
        flag = "⚠️ yes" if result["manual_review"] else ""
        lines.append(
            f"| {result['id']} | {result['expected_posture']} | "
            f"{status} {passed}/{total} | {flag} |"
        )
    lines.append("")

    lines.append("## Cases")
    for result in case_results:
        lines.append("")
        lines.append(f"### {result['id']} — expected posture: {result['expected_posture']}")
        lines.append("")
        lines.append(f"**Question:** {result['question']}")
        lines.append("")
        lines.append(f"**Eval notes:** {result['notes']}")
        lines.append("")
        lines.append("**Automated checks:**")
        for check in result["checks"]:
            mark = "x" if check["passed"] else " "
            lines.append(f"- [{mark}] `{check['name']}` — {check['detail']}")
        if result["manual_review"]:
            lines.append("- ⚠️ **Flagged for manual review**")
        lines.append("")

        for index, turn in enumerate(result["turns"], start=1):
            if len(result["turns"]) > 1:
                lines.append(f"**Turn {index}:** {turn.get('message', '')}")
                lines.append("")
            if turn.get("error"):
                lines.append(f"**Error:** {turn['error']}")
                lines.append("")
                continue
            lines.append("**Response (main answer):**")
            lines.append(_md_escape_block(turn.get("clean_text") or ""))
            lines.append("")
            if turn.get("domain_context"):
                lines.append("**Domain context block:**")
                lines.append(_md_escape_block(turn["domain_context"]))
                lines.append("")
            if turn.get("sources"):
                lines.append("**Sources:**")
                for source in turn["sources"]:
                    lines.append(
                        f"- {source.get('file_name', '?')} | "
                        f"Section {source.get('chunk_index', '?')} | "
                        f"\"{source.get('title', '')}\""
                    )
                lines.append("")

        lines.append("**Posture quality (manual grade):** ☐ pass · ☐ fail — notes:")
        lines.append("")
        lines.append("---")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config = _require_env()

    if not EVAL_SET_PATH.exists():
        logger.error("Eval set not found: %s", EVAL_SET_PATH)
        sys.exit(1)
    eval_set = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))
    cases = eval_set["cases"]

    logger.info("Authenticating as %s", config["email"])
    token = authenticate(
        config["supabase_url"], config["anon_key"], config["email"], config["password"]
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_meta = {
        "eval_set": eval_set.get("eval_set", "unknown"),
        "timestamp": timestamp,
        "api_url": config["api_url"],
        "kb_id": config["kb_id"],
    }

    case_results: list[dict] = []
    timeout = httpx.Timeout(30.0, read=120.0)

    with httpx.Client(timeout=timeout) as client:
        for index, case in enumerate(cases, start=1):
            logger.info("[%d/%d] %s: %s", index, len(cases), case["id"], case["question"][:70])
            turns = run_case(client, config, token, case)
            checks, manual_review = check_case(case, turns)
            quality = judge_posture_quality(case, turns)  # stub — returns None

            passed = sum(1 for c in checks if c["passed"])
            logger.info("  checks: %d/%d passed%s", passed, len(checks),
                        " | MANUAL REVIEW" if manual_review else "")

            case_results.append({
                "id": case["id"],
                "question": case["question"],
                "expected_posture": case["expected_posture"],
                "notes": case["notes"],
                "turns": turns,
                "checks": checks,
                "manual_review": manual_review,
                "posture_quality": quality,
            })

    results_path = EVAL_DIR / f"eval_results_{timestamp}.json"
    report_path = EVAL_DIR / f"eval_report_{timestamp}.md"
    write_results_json(results_path, run_meta, case_results)
    write_markdown_report(report_path, run_meta, case_results)

    logger.info("Results written: %s", results_path)
    logger.info("Report written:  %s", report_path)


if __name__ == "__main__":
    main()
