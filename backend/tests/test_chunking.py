import asyncio
import json
import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("ENVIRONMENT", "testing")

from app.services import chunking
from app.services.chunking import (
    SECTION_MAX,
    SECTION_MIN,
    _locate_marker_boundaries,
    _split_markdown_sections,
    chunk_document,
    identify_sections,
)


def _paragraph(sentence: str, target_length: int) -> str:
    """Repeat a sentence until the paragraph reaches at least target_length characters."""
    repeats = (target_length // (len(sentence) + 1)) + 1
    return " ".join([sentence] * repeats)


def _fake_client(response_text: str) -> SimpleNamespace:
    async def create(**kwargs):
        return SimpleNamespace(content=[SimpleNamespace(text=response_text)])

    return SimpleNamespace(messages=SimpleNamespace(create=create))


# ─── (a) Markdown documents split deterministically at headings ───


def _markdown_doc() -> str:
    body = _paragraph("This paragraph holds enough policy detail to clear the size floor.", 300)
    parts = [_paragraph("Preamble text introducing the document before any heading appears.", 300)]
    for i in range(1, 6):
        parts.append(f"## Heading {i}\n\n{body}")
    return "\n\n".join(parts)


def test_markdown_doc_splits_exactly_at_headings(monkeypatch: pytest.MonkeyPatch) -> None:
    text = _markdown_doc()

    def _no_ai_allowed():
        raise AssertionError("Claude must not be called for markdown-structured documents")

    monkeypatch.setattr(chunking, "_get_client", _no_ai_allowed)

    sections = asyncio.run(identify_sections(text))

    assert len(sections) == 6  # preamble + 5 headings
    assert sections[0]["title"] == "Preamble"
    assert sections[0]["start"] == 0

    for i, section in enumerate(sections):
        content = text[section["start"]:section["end"]]
        if i == 0:
            assert not content.lstrip().startswith("##")
        else:
            assert content.startswith("## "), f"section {i} does not start at a heading"
            assert section["title"] == f"Heading {i}"

    # No gaps, no overlaps, no mid-word seams: sections tile the document exactly
    assert sections[-1]["end"] == len(text)
    for prev, nxt in zip(sections, sections[1:]):
        assert prev["end"] == nxt["start"]


# ─── (b) Size constraints: merge undersized, split oversized ───


def test_undersized_sections_merge_into_neighbor() -> None:
    body = _paragraph("Standard section content that easily exceeds the minimum length floor.", 400)
    text = f"## First\n\n{body}\n\n## Tiny\n\nShort.\n\n## Third\n\n{body}"

    sections = _split_markdown_sections(text)

    assert all(s["end"] - s["start"] >= SECTION_MIN for s in sections)
    # The tiny section was absorbed by its previous neighbor
    titles = [s["title"] for s in sections]
    assert "Tiny" not in titles
    first = next(s for s in sections if s["title"] == "First")
    assert "## Tiny" in text[first["start"]:first["end"]]


def test_oversized_sections_split_at_paragraph_breaks() -> None:
    paragraph = _paragraph("Each paragraph in this giant section carries real sentence content.", 800)
    giant = "\n\n".join([paragraph] * 8)  # well over SECTION_MAX
    body = _paragraph("A normal-sized section used as a control alongside the giant one.", 400)
    text = f"## Normal\n\n{body}\n\n## Giant\n\n{giant}\n\n## Closing\n\n{body}"

    sections = _split_markdown_sections(text)

    assert all(s["end"] - s["start"] <= SECTION_MAX for s in sections)
    giant_parts = [s for s in sections if s["title"].startswith("Giant")]
    assert len(giant_parts) > 1

    # Every split lands on a paragraph break — continuation parts begin with \n\n,
    # so no chunk can start or end mid-word
    for part in giant_parts[1:]:
        assert text[part["start"]:part["start"] + 2] == "\n\n"


# ─── (c) Sequential marker search survives duplicate text ───


def test_marker_located_correctly_when_similar_text_appears_twice() -> None:
    text = (
        "Intro section. Refund policy applies to all orders as we will explain in "
        "detail later in this document, with conditions.\n\n"
        "Refund policy applies to all orders placed through the online store. "
        "Returns require a receipt and the original packaging to be accepted."
    )
    sections = [
        {"title": "Introduction", "start_marker": "Intro section. Refund policy applies"},
        {"title": "Refund Policy", "start_marker": "Refund policy applies to all orders"},
    ]

    boundaries = _locate_marker_boundaries(text, sections)

    assert boundaries is not None
    assert len(boundaries) == 2
    # The duplicate at position 15 (inside the intro) must be skipped:
    # the second boundary lands on the second paragraph, not the early echo
    expected = text.index("Refund policy applies to all orders placed")
    assert boundaries[1]["start"] == expected
    assert boundaries[0]["end"] == boundaries[1]["start"]
    assert boundaries[1]["end"] == len(text)


# ─── (d) Unfindable marker → warning, span absorbed by previous section ───


def test_unfindable_marker_logs_warning_and_absorbs_span(
    caplog: pytest.LogCaptureFixture,
) -> None:
    text = (
        "Alpha section begins here with its full content about onboarding steps.\n\n"
        "Beta section begins here with details about quarterly review procedures.\n\n"
        "Gamma section begins here covering the escalation and dismissal process."
    )
    sections = [
        {"title": "Alpha", "start_marker": "Alpha section begins here"},
        {"title": "Beta", "start_marker": "THIS MARKER DOES NOT EXIST ANYWHERE"},
        {"title": "Gamma", "start_marker": "Gamma section begins here"},
    ]

    with caplog.at_level("WARNING"):
        boundaries = _locate_marker_boundaries(text, sections)

    assert boundaries is not None
    assert len(boundaries) == 2
    assert [b["title"] for b in boundaries] == ["Alpha", "Gamma"]
    # Alpha absorbed Beta's span: it runs all the way to Gamma's located marker
    assert boundaries[0]["end"] == text.index("Gamma section begins here")
    assert "THIS MARKER DOES NOT EXIST ANYWHERE" in caplog.text


# ─── (e) More than a third of markers failing → fixed-size fallback ───


def test_majority_marker_failure_returns_none(caplog: pytest.LogCaptureFixture) -> None:
    text = "Alpha section begins here with content.\n\nMore content follows in this text."
    sections = [
        {"title": "Alpha", "start_marker": "Alpha section begins here"},
        {"title": "Beta", "start_marker": "NOT PRESENT IN THE DOCUMENT AT ALL"},
        {"title": "Gamma", "start_marker": "ALSO COMPLETELY ABSENT FROM THE TEXT"},
    ]

    with caplog.at_level("WARNING"):
        boundaries = _locate_marker_boundaries(text, sections)

    assert boundaries is None
    assert "abandoning AI sectioning" in caplog.text


def test_marker_failures_trigger_fixed_size_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Plain prose, no markdown headings, long enough to skip the short-doc path
    text = "\n\n".join(
        _paragraph(f"Paragraph {i} describes operational procedure number {i} in depth.", 300)
        for i in range(6)
    )
    assert len(text) >= 500

    ai_response = json.dumps([
        {"title": "One", "start_marker": "Paragraph 0 describes operational procedure"},
        {"title": "Two", "start_marker": "HALLUCINATED MARKER NOT IN THE DOCUMENT"},
        {"title": "Three", "start_marker": "ANOTHER PARAPHRASED MARKER THAT WILL NOT MATCH"},
    ])
    monkeypatch.setattr(chunking, "_get_client", lambda: _fake_client(ai_response))

    chunks = asyncio.run(chunk_document(text, "test.txt"))

    # Fixed-size fallback output: no summary chunk, generic section titles
    assert len(chunks) > 0
    assert all(c["metadata"]["is_summary"] is False for c in chunks)
    assert all(c["metadata"]["title"].startswith("Section ") for c in chunks)
    assert all(c["metadata"]["file_name"] == "test.txt" for c in chunks)
