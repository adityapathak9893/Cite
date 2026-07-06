import os

import pytest

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("ENVIRONMENT", "testing")

from app.services.rag import is_overview_question


# ─── Overview detection: coverage / absence phrasings ───


@pytest.mark.parametrize(
    "question",
    [
        "Tell me something which is not covered in this doc?",
        "Does it cover incident response?",
        "This doesn't cover pricing, right?",
        "What's missing from this manual?",
        "What is missing here?",
        "This doesn't include SSO configuration.",
        "Is anything not included in the guide?",
        "What topics are absent from the manual?",
        "Is that not in this doc?",
        "Is disaster recovery not in the document?",
    ],
)
def test_coverage_questions_are_overview(question: str) -> None:
    # Absence claims are only groundable via document structure, so coverage
    # phrasings must trigger the structure fetch.
    assert is_overview_question(question) is True


# ─── Overview detection: existing behaviour preserved ───


@pytest.mark.parametrize(
    "question",
    ["What is this about?", "Summarize this document"],
)
def test_existing_overview_phrasings_still_detected(question: str) -> None:
    assert is_overview_question(question) is True


def test_specific_question_is_not_overview() -> None:
    assert is_overview_question("How do I schedule a scan?") is False
