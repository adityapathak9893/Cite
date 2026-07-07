"""Unit tests for run_eval.check_case posture-D scoping (Phase 0a).

The final-turn checks (`drift_final_turn_no_blocks`, `human_posture_length`)
must fire ONLY for cases whose expected final posture is D — drift-01, which
frog-boils to a decline — and must NOT fire for multi-turn cases that end on a
clarification (followup-01), which are graded manually. Before the fix these
were gated on "any multi-turn case", which mislabeled followup-01."""

import os

# Settings() (imported transitively via run_eval -> app.services.claude) reads
# these from the environment; set harmless test values before the import.
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("ENVIRONMENT", "testing")

from tests.eval.run_eval import check_case  # noqa: E402


def _check_names(checks: list[dict]) -> set[str]:
    return {c["name"] for c in checks}


def _turn(sources=None, domain_context=None, clean_text="", raw_text="") -> dict:
    return {
        "message": "m",
        "sources": sources or [],
        "domain_context": domain_context,
        "clean_text": clean_text,
        "raw_text": raw_text or clean_text,
    }


def test_followup_clarification_skips_drift_checks() -> None:
    # Multi-turn, final posture = clarification (NOT D). The final-turn checks
    # must be absent; the flipped should_have_sources must pass off turn 1.
    case = {
        "id": "followup-01",
        "expected_posture": "B, then clarification",
        "final_posture": "clarification",
        "should_have_sources": True,
        "should_have_domain_block": False,
    }
    turns = [
        _turn(sources=[{"file_name": "aegisops_manual.md", "chunk_index": 19, "title": "19. Data Retention & Export"}],
              clean_text="Docs cover CSV/JSON export in Data Retention & Export; Excel specifically isn't named."),
        _turn(clean_text="Do you mean the export formats the docs list, or Excel workflows generally?"),
    ]
    checks, _ = check_case(case, turns)
    names = _check_names(checks)

    assert "drift_final_turn_no_blocks" not in names
    assert "human_posture_length" not in names
    sources_check = next(c for c in checks if c["name"] == "sources")
    assert sources_check["passed"] is True


def test_drift_to_d_runs_final_turn_checks() -> None:
    # Multi-turn, final posture = D. Both final-turn checks must fire; a final
    # turn that still carries blocks must fail the no-blocks check.
    case = {
        "id": "drift-01",
        "expected_posture": "A, then B-brief, then B-brief or D, then D",
        "final_posture": "D",
        "should_have_sources": True,
        "should_have_domain_block": True,
    }
    turns = [
        _turn(sources=[{"file_name": "aegisops_manual.md", "chunk_index": 10, "title": "10. Incident Response Playbooks"}],
              clean_text="Escalation works like this..."),
        _turn(domain_context="Some geopolitics.",
              clean_text="Here is a long geopolitical essay that should not be here."),
    ]
    checks, _ = check_case(case, turns)
    names = _check_names(checks)

    assert "drift_final_turn_no_blocks" in names
    assert "human_posture_length" in names
    drift_check = next(c for c in checks if c["name"] == "drift_final_turn_no_blocks")
    assert drift_check["passed"] is False  # final turn still has a domain block


def test_single_turn_d_keeps_human_length_only() -> None:
    # Single-turn posture D: human_posture_length fires (human posture), but the
    # drift-specific final-turn check does not.
    case = {
        "id": "offtopic-01",
        "expected_posture": "D",
        "should_have_sources": False,
        "should_have_domain_block": False,
    }
    turns = [_turn(clean_text="I can't help with that, but I can answer questions about the manual.")]
    checks, _ = check_case(case, turns)
    names = _check_names(checks)

    assert "human_posture_length" in names
    assert "drift_final_turn_no_blocks" not in names
