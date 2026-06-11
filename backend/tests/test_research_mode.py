import asyncio
import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("ENVIRONMENT", "testing")

from app.services import claude
from app.services.claude import (
    DOMAIN_PROFILE_FALLBACK,
    RESEARCH_TONE,
    build_system_prompt,
    parse_domain_context_from_response,
)


# ─── DOMAIN_CONTEXT parser ───


def test_domain_context_block_present() -> None:
    text = (
        "The main answer about AegisScore.\n\n"
        "---DOMAIN_CONTEXT---\n"
        "CVSS is an industry-standard scoring system.\n"
        "---END_DOMAIN_CONTEXT---"
    )
    clean_text, domain_context = parse_domain_context_from_response(text)
    assert clean_text == "The main answer about AegisScore."
    assert domain_context == "CVSS is an industry-standard scoring system."


def test_domain_context_block_absent() -> None:
    text = "Just a plain answer with no blocks."
    clean_text, domain_context = parse_domain_context_from_response(text)
    assert clean_text == text
    assert domain_context is None


def test_domain_context_missing_end_delimiter(caplog: pytest.LogCaptureFixture) -> None:
    text = (
        "Main answer.\n\n"
        "---DOMAIN_CONTEXT---\n"
        "Domain knowledge that never gets closed."
    )
    with caplog.at_level("WARNING"):
        clean_text, domain_context = parse_domain_context_from_response(text)
    assert clean_text == "Main answer."
    assert domain_context == "Domain knowledge that never gets closed."
    assert any("missing end delimiter" in record.message for record in caplog.records)


def test_domain_context_empty_block_treated_as_absent() -> None:
    text = "Main answer.\n\n---DOMAIN_CONTEXT---\n\n---END_DOMAIN_CONTEXT---"
    clean_text, domain_context = parse_domain_context_from_response(text)
    assert clean_text == "Main answer."
    assert domain_context is None


def test_domain_context_preserves_trailing_text() -> None:
    text = (
        "Main answer.\n\n"
        "---DOMAIN_CONTEXT---\n"
        "Domain knowledge.\n"
        "---END_DOMAIN_CONTEXT---\n\n"
        "Trailing text after the block."
    )
    clean_text, domain_context = parse_domain_context_from_response(text)
    assert domain_context == "Domain knowledge."
    assert "Main answer." in clean_text
    assert "Trailing text after the block." in clean_text


# ─── Strict-mode discard (stream_chat_response) ───


class _FakeStream:
    def __init__(self, text: str) -> None:
        self._text = text

    async def __aenter__(self) -> "_FakeStream":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    @property
    def text_stream(self):
        async def _generate():
            yield self._text

        return _generate()


def _fake_client(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        messages=SimpleNamespace(stream=lambda **kwargs: _FakeStream(text))
    )


RESPONSE_WITH_BLOCK = (
    "Main answer from the documents.\n\n"
    "---DOMAIN_CONTEXT---\n"
    "Broader industry context.\n"
    "---END_DOMAIN_CONTEXT---"
)


def _final_event(chat_mode: str, response_text: str, monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.setattr(claude, "_get_client", lambda: _fake_client(response_text))

    async def _collect() -> list[dict]:
        events = []
        async for event in claude.stream_chat_response(
            kb_name="Test KB",
            messages=[{"role": "user", "content": "question"}],
            chunks=[],
            context="some context",
            chat_mode=chat_mode,
        ):
            events.append(event)
        return events

    return asyncio.run(_collect())[-1]


def test_strict_mode_discards_domain_block(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level("WARNING"):
        final = _final_event("strict", RESPONSE_WITH_BLOCK, monkeypatch)
    assert final["done"] is True
    assert final["domain_context"] is None
    assert "---DOMAIN_CONTEXT---" not in final["full_response"]
    assert final["full_response"] == "Main answer from the documents."
    assert any("strict mode" in record.message for record in caplog.records)


def test_research_mode_keeps_domain_block(monkeypatch: pytest.MonkeyPatch) -> None:
    final = _final_event("research", RESPONSE_WITH_BLOCK, monkeypatch)
    assert final["domain_context"] == "Broader industry context."
    assert final["full_response"] == "Main answer from the documents."


# ─── Prompt builder ───


def test_strict_mode_prompt_unchanged() -> None:
    prompt = build_system_prompt("My KB", "the context", chat_mode="strict")
    assert "thoroughly read and understood all the documents" in prompt
    assert "The Five Postures" not in prompt
    assert "DOMAIN_CONTEXT" not in prompt
    assert prompt.endswith("Knowledge base: My KB\n\nthe context")


def test_strict_mode_ignores_domain_profile() -> None:
    without_profile = build_system_prompt("My KB", "ctx", chat_mode="strict")
    with_profile = build_system_prompt(
        "My KB", "ctx", chat_mode="strict", domain_profile="Cybersecurity ops."
    )
    assert without_profile == with_profile


def test_default_mode_is_strict() -> None:
    assert build_system_prompt("My KB", "ctx") == build_system_prompt(
        "My KB", "ctx", chat_mode="strict"
    )


def test_research_mode_interpolates_contract() -> None:
    profile = "These documents cover the AegisOps security platform."
    prompt = build_system_prompt(
        "AegisOps Docs", "the context", chat_mode="research", domain_profile=profile
    )
    assert 'knowledge assistant for "AegisOps Docs"' in prompt
    assert profile in prompt
    assert RESEARCH_TONE in prompt
    assert "The Five Postures" in prompt
    assert "---DOMAIN_CONTEXT---" in prompt
    assert prompt.endswith("Knowledge base: AegisOps Docs\n\nthe context")


def test_research_mode_null_profile_uses_fallback() -> None:
    prompt = build_system_prompt("Legacy KB", "ctx", chat_mode="research")
    assert DOMAIN_PROFILE_FALLBACK in prompt

    blank = build_system_prompt(
        "Legacy KB", "ctx", chat_mode="research", domain_profile="   "
    )
    assert DOMAIN_PROFILE_FALLBACK in blank


def test_research_mode_without_context() -> None:
    prompt = build_system_prompt("My KB", "", chat_mode="research")
    assert prompt.endswith("Knowledge base: My KB")
