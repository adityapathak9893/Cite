import logging
import re
from collections.abc import AsyncGenerator
from functools import lru_cache

import anthropic

from app.config import CLAUDE_MODEL, get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client() -> anthropic.AsyncAnthropic:
    settings = get_settings()
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


def build_system_prompt(kb_name: str, context: str) -> str:
    """Build the system prompt with KB instructions and document context."""
    base = (
        "You have thoroughly read and understood all the documents in this knowledge base. "
        "You are a knowledgeable, helpful expert on these documents.\n\n"
        "Guidelines:\n"
        "- Answer naturally and conversationally, as a colleague who has deeply studied these documents would.\n"
        "- Synthesize information across multiple sections when it gives a better, more complete answer.\n"
        "- For overview questions (\"what is this about?\", \"summarize this\", \"what should I know?\"), "
        "provide a comprehensive, well-structured response that demonstrates deep understanding of the entire document. "
        "Cover all major topics.\n"
        "- For specific questions, give thorough answers with relevant context. "
        "Explain what things mean and why they matter, don't just state facts.\n"
        "- Always ground your answers in the actual document content — never invent facts that aren't in the provided context.\n"
        "- If the question truly cannot be answered from the provided context, say so naturally like: "
        "\"The documents don't appear to cover that topic. Based on what's available, the closest related information is...\" "
        "— NOT a robotic disclaimer like \"I don't have enough information in the uploaded documents.\"\n"
        "- Do NOT use inline citations like [Source: ...] in your answer text. "
        "Your response should flow naturally without any citation markers interrupting the text.\n"
        "- Write in a warm, professional tone. Educate the user. Enhance their understanding. "
        "Don't just point at text — explain it.\n"
        "- Use formatting (bold, bullet points, headers) when it helps organize complex information, but keep it natural.\n\n"
        "CRITICAL — Source Attribution:\n"
        "At the very end of your response, after your complete answer, add a sources block in this EXACT format:\n\n"
        "---SOURCES---\n"
        "[1] {filename} | Section {chunk_index} | \"{title from metadata}\"\n"
        "[2] {filename} | Section {chunk_index} | \"{title from metadata}\"\n"
        "---END_SOURCES---\n\n"
        "Rules for the SOURCES block:\n"
        "- List EVERY section you drew information from, even partially\n"
        "- The SOURCES block must ALWAYS be present when you use information from the context\n"
        "- Use the exact filename, section number (chunk_index), and title from the provided context\n"
        "- For overview answers that draw from the document structure list, cite the Document Overview section\n"
        "- The SOURCES block is for machine parsing — it will be stripped from the visible response and shown as citation chips"
    )

    if context:
        return f"{base}\n\nKnowledge base: {kb_name}\n\n{context}"
    return f"{base}\n\nKnowledge base: {kb_name}"


def parse_sources_from_response(response_text: str) -> tuple[str, list[dict]]:
    """Extract and parse the ---SOURCES--- block from Claude's response.

    Returns (clean_text, parsed_sources).
    """
    sources: list[dict] = []
    clean_text = response_text

    sources_start = response_text.find("---SOURCES---")
    sources_end = response_text.find("---END_SOURCES---")

    if sources_start != -1 and sources_end != -1:
        clean_text = response_text[:sources_start].rstrip()

        sources_block = response_text[
            sources_start + len("---SOURCES---"):sources_end
        ].strip()

        for line in sources_block.split("\n"):
            line = line.strip()
            if not line or not line.startswith("["):
                continue
            try:
                # Parse: [1] filename.pdf | Section 5 | "Title Here"
                content = line.split("]", 1)[1].strip()
                parts = [p.strip() for p in content.split("|")]
                if len(parts) >= 3:
                    filename = parts[0]
                    section_str = parts[1]  # "Section 5"
                    section_num = (
                        int("".join(filter(str.isdigit, section_str)))
                        if any(c.isdigit() for c in section_str)
                        else 0
                    )
                    title = parts[2].strip('"').strip("'")

                    sources.append({
                        "file_name": filename,
                        "chunk_index": section_num,
                        "title": title,
                    })
            except (ValueError, IndexError):
                continue

    return clean_text, sources


def _match_parsed_sources(
    parsed_sources: list[dict],
    chunks: list[dict],
) -> list[dict]:
    """Match Claude's parsed sources against original chunks to fill in document_id, similarity.

    Falls back to parsed source data if no chunk match found.
    """
    # Build lookup: (file_name, chunk_index) → chunk
    chunk_lookup: dict[tuple[str, int], dict] = {}
    for chunk in chunks:
        key = (chunk.get("file_name", ""), chunk.get("chunk_index", 0))
        chunk_lookup[key] = chunk

    matched: list[dict] = []
    seen: set[tuple[str, int]] = set()

    for src in parsed_sources:
        key = (src["file_name"], src["chunk_index"])
        if key in seen:
            continue
        seen.add(key)

        chunk = chunk_lookup.get(key)
        if chunk:
            matched.append({
                "document_id": chunk.get("document_id", ""),
                "file_name": src["file_name"],
                "chunk_index": src["chunk_index"],
                "content": "",
                "similarity": chunk.get("similarity", 0),
                "title": src.get("title", ""),
            })
        else:
            matched.append({
                "document_id": "",
                "file_name": src["file_name"],
                "chunk_index": src["chunk_index"],
                "content": "",
                "similarity": 0,
                "title": src.get("title", ""),
            })

    return matched


async def stream_chat_response(
    kb_name: str,
    messages: list[dict],
    chunks: list[dict],
    context: str,
) -> AsyncGenerator[dict, None]:
    """Stream Claude's response token by token.

    Yields dicts:
      {"token": "...", "done": false}   — for each text delta
      {"token": "", "done": true, "sources": [...], "full_response": "..."}  — at end

    The full_response in the final event is the CLEAN text (SOURCES block stripped).
    Sources are parsed from Claude's ---SOURCES--- block and matched against chunks.
    """
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

    # Parse ---SOURCES--- block from Claude's response
    clean_text, parsed_sources = parse_sources_from_response(full_response)

    logger.info(
        "Parsed %d sources from Claude response | kb=%s",
        len(parsed_sources), kb_name,
    )

    # Match parsed sources against original chunks for document_id, similarity
    sources = _match_parsed_sources(parsed_sources, chunks)

    yield {
        "token": "",
        "done": True,
        "sources": sources,
        "full_response": clean_text,
    }
