import logging
import re
from collections.abc import AsyncGenerator
from functools import lru_cache

import anthropic

from app.config import get_settings

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"


@lru_cache(maxsize=1)
def _get_client() -> anthropic.AsyncAnthropic:
    settings = get_settings()
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


def build_system_prompt(kb_name: str, context: str) -> str:
    """Build the system prompt with KB instructions and document context."""
    base = (
        "You answer questions using ONLY the document excerpts below. "
        "Nothing else exists — no outside knowledge, no assumptions, no inference beyond what the text says.\n"
        "Cite every claim as [Source: filename, Section N].\n"
        "Only cite excerpts that DIRECTLY answer the question. Do not cite excerpts that are merely "
        "related to the topic. 1 precise source is better than 3 vague ones.\n"
        "For each citation, quote the specific sentence from the excerpt that supports your answer.\n"
        "If the answer is not in the excerpts, say only: "
        "'I don't have enough information in the uploaded documents to answer this question.'"
    )

    if context:
        return f"{base}\n\n{context}"
    return base


def build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into the document excerpts block."""
    if not chunks:
        return ""

    lines = ["--- Document Excerpts ---"]
    for i, chunk in enumerate(chunks, 1):
        file_name = chunk.get("file_name", "Unknown")
        chunk_index = chunk.get("chunk_index", i)
        content = chunk.get("content", "")
        lines.append(f"\n[{i}] From: {file_name} (Section {chunk_index})")
        lines.append(content)
    lines.append("\n--- End of Excerpts ---")

    return "\n".join(lines)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on . ! ? boundaries."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in parts if s.strip()]


def _extract_snippet(text: str, query: str, max_len: int = 100) -> str:
    """Extract the sentence from text that best matches the query by keyword overlap.

    Falls back to the first sentence if no good match is found.
    """
    text = text.strip()
    if not text:
        return ""

    sentences = _split_sentences(text)
    if not sentences:
        return text[:max_len]

    # Build query keywords (lowercase, skip short words)
    query_words = {w.lower() for w in query.split() if len(w) > 2}

    best_sentence = sentences[0]
    best_score = -1

    for sentence in sentences:
        words = {w.lower().strip(".,!?;:'\"") for w in sentence.split()}
        score = len(words & query_words)
        if score > best_score:
            best_score = score
            best_sentence = sentence

    # Truncate at word boundary if needed
    if len(best_sentence) <= max_len:
        return best_sentence
    truncated = best_sentence[:max_len].rsplit(" ", 1)[0]
    return truncated + "…"


async def stream_chat_response(
    kb_name: str,
    messages: list[dict],
    chunks: list[dict],
) -> AsyncGenerator[dict, None]:
    """Stream Claude's response token by token.

    Yields dicts:
      {"token": "...", "done": false}   — for each text delta
      {"token": "", "done": true, "sources": [...], "full_response": "..."}  — at end
    """
    context = build_context(chunks)
    system_prompt = build_system_prompt(kb_name, context)

    client = _get_client()

    full_response = ""

    try:
        async with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                full_response += text
                yield {"token": text, "done": False}

    except anthropic.APIError as exc:
        logger.error("Claude API error: %s", str(exc))
        error_msg = "I'm having trouble generating a response right now. Please try again."
        yield {"token": error_msg, "done": False}
        yield {"token": "", "done": True, "sources": [], "full_response": error_msg}
        return

    # Extract user query for keyword-matched snippet
    user_query = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_query = m.get("content", "")
            break

    # Build sources from the retrieved chunks
    sources = []
    for chunk in chunks:
        sources.append({
            "document_id": chunk.get("document_id", ""),
            "file_name": chunk.get("file_name", "Unknown"),
            "chunk_index": chunk.get("chunk_index", 0),
            "content": _extract_snippet(chunk.get("content", ""), user_query),
            "similarity": chunk.get("similarity", 0),
        })

    yield {
        "token": "",
        "done": True,
        "sources": sources,
        "full_response": full_response,
    }
