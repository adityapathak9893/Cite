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
        "You are a helpful document assistant. Answer questions using ONLY the document excerpts provided below.\n\n"
        "Rules:\n"
        "1. If an excerpt directly answers the question, cite it using [Source: filename, Section N] format\n"
        "2. ONLY cite excerpts that DIRECTLY contain information answering the question. "
        "Do not cite excerpts that are merely related to the topic.\n"
        "3. For each citation, briefly quote the specific phrase (under 20 words) that supports your answer\n"
        "4. If the answer is not found in any excerpt, say: "
        "'I don't have enough information in the uploaded documents to answer this question.'\n"
        "5. Do NOT make up information or use knowledge outside the provided excerpts\n"
        "6. It is better to cite 1 precise source than 5 vague ones\n"
        "7. If the question is about the overall document (e.g., 'what topics are covered?'), "
        "look for the Document Overview section first"
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
        metadata = chunk.get("metadata") or {}
        sources.append({
            "document_id": chunk.get("document_id", ""),
            "file_name": chunk.get("file_name", "Unknown"),
            "chunk_index": chunk.get("chunk_index", 0),
            "content": _extract_snippet(chunk.get("content", ""), user_query),
            "similarity": chunk.get("similarity", 0),
            "title": metadata.get("title", ""),
        })

    yield {
        "token": "",
        "done": True,
        "sources": sources,
        "full_response": full_response,
    }
