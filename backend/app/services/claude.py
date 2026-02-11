import logging
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

    # Build sources from the retrieved chunks
    sources = []
    for chunk in chunks:
        sources.append({
            "document_id": chunk.get("document_id", ""),
            "file_name": chunk.get("file_name", "Unknown"),
            "chunk_index": chunk.get("chunk_index", 0),
            "content": chunk.get("content", "")[:200],
            "similarity": chunk.get("similarity", 0),
        })

    yield {
        "token": "",
        "done": True,
        "sources": sources,
        "full_response": full_response,
    }
