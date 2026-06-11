import json
import logging
import re
from collections.abc import AsyncGenerator

import anthropic

from app.config import CLAUDE_MODEL, get_settings
from app.services.claude import _get_client

logger = logging.getLogger(__name__)

# Limits for AI section detection
AI_CHAR_LIMIT = 30_000  # Only send first 30k chars to Claude for section detection
MIN_DOC_LENGTH = 500     # Documents shorter than this become a single chunk
SECTION_MIN = 200        # Minimum section length
SECTION_MAX = 3000       # Maximum section length

SECTION_DETECTION_PROMPT = """\
You are a document structure analyzer. Your job is to identify the logical sections in the document text provided.

Rules:
- Identify every distinct section, subsection, and topic boundary
- A "section" is a self-contained unit about ONE topic (a policy, a procedure, a definition, etc.)
- Return the EXACT start and end character positions for each section
- Each section should be between 200-3000 characters. If a section is longer than 3000 characters, split it into logical sub-sections
- If a section is shorter than 200 characters, merge it with the adjacent section that is most topically related
- Preserve complete paragraphs — never split mid-paragraph
- Include a short title (max 10 words) describing what each section is about

Respond with ONLY a JSON array, no other text:
[
  {"title": "Section title here", "start": 0, "end": 1523},
  {"title": "Next section title", "start": 1524, "end": 3201},
  ...
]

The character positions must be exact — they will be used to slice the original text. The end of one section should be the start of the next (no gaps, no overlaps)."""

SUMMARY_PROMPT_TEMPLATE = """\
Below are the sections found in a document. Write a comprehensive 150-200 word summary of what this document covers. List ALL the main topics. This summary will be used to answer questions like "What is this document about?" and "What topics are covered?"

Sections:
{sections_list}"""

DESCRIPTIONS_PROMPT_TEMPLATE = """\
For each section below, write a one-line search description (max 100 characters) that someone would use to find this section. Focus on specific keywords, not generic descriptions.

Sections:
{sections_list}

Respond with ONLY a JSON array of descriptions in the same order:
["description 1", "description 2", ...]"""


# ─── AI-powered section detection ───


async def identify_sections(text: str) -> list[dict]:
    """Use Claude to identify logical section boundaries in the document.

    Returns list of dicts: [{"title": "...", "start": int, "end": int}, ...]
    Falls back to heuristic chunking on failure.
    """
    client = _get_client()

    # For large documents, only send first AI_CHAR_LIMIT chars to Claude
    ai_text = text[:AI_CHAR_LIMIT] if len(text) > AI_CHAR_LIMIT else text

    try:
        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=SECTION_DETECTION_PROMPT,
            messages=[{"role": "user", "content": ai_text}],
        )

        raw = response.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        sections = json.loads(raw)

        if not isinstance(sections, list) or len(sections) == 0:
            logger.warning("AI returned empty/invalid sections, falling back")
            return []

        # Validate structure
        for s in sections:
            if not isinstance(s, dict) or "start" not in s or "end" not in s:
                logger.warning("AI returned malformed section: %s", s)
                return []

        logger.info(
            "AI identified %d sections in first %d chars",
            len(sections), len(ai_text),
        )

        # If document is longer than what we sent to Claude, handle the remainder
        if len(text) > AI_CHAR_LIMIT:
            remainder_sections = _heuristic_sections(
                text[AI_CHAR_LIMIT:], offset=AI_CHAR_LIMIT
            )
            sections.extend(remainder_sections)
            logger.info(
                "Added %d heuristic sections for remaining %d chars",
                len(remainder_sections), len(text) - AI_CHAR_LIMIT,
            )

        return sections

    except (json.JSONDecodeError, anthropic.APIError, IndexError, KeyError) as exc:
        logger.warning("AI section detection failed (%s), falling back", str(exc))
        return []
    except Exception as exc:
        logger.warning("Unexpected error in section detection (%s), falling back", str(exc))
        return []


def _heuristic_sections(text: str, offset: int = 0) -> list[dict]:
    """Split text into sections using heuristic rules (double-newlines, headings).

    Used for the tail of large documents and as the fallback when AI fails.
    """
    if not text.strip():
        return []

    # Split at double-newlines or heading patterns
    # Heading patterns: lines starting with numbers like "4.2", all-caps lines
    pattern = r"\n\s*\n"
    parts = re.split(pattern, text)

    sections: list[dict] = []
    current_start = 0
    current_text = ""
    current_title = ""

    for part in parts:
        part = part.strip()
        if not part:
            current_start += 2  # account for \n\n
            continue

        # Detect if this part starts with a heading-like pattern
        heading_match = re.match(
            r"^(\d+[\.\d]*\s+.{3,80}|[A-Z][A-Z\s&\-]{5,80})$",
            part.split("\n")[0].strip(),
        )
        part_title = heading_match.group(0).strip()[:80] if heading_match else ""

        candidate = f"{current_text}\n\n{part}" if current_text else part

        if len(candidate) > SECTION_MAX and current_text:
            # Flush current section
            end_pos = offset + text.find(current_text) + len(current_text)
            start_pos = end_pos - len(current_text)
            sections.append({
                "title": current_title or f"Section {len(sections) + 1}",
                "start": start_pos,
                "end": end_pos,
            })
            current_text = part
            current_title = part_title
        else:
            if not current_title and part_title:
                current_title = part_title
            current_text = candidate

    # Flush remaining
    if current_text.strip():
        end_pos = offset + len(text)
        start_pos = end_pos - len(current_text)
        sections.append({
            "title": current_title or f"Section {len(sections) + 1}",
            "start": start_pos,
            "end": end_pos,
        })

    return sections


# ─── Document summary generation ───


async def generate_summary(sections: list[dict], text: str) -> str:
    """Generate a comprehensive document overview using Claude.

    Falls back to a simple title concatenation if AI fails.
    """
    titles = [s.get("title", f"Section {i+1}") for i, s in enumerate(sections)]

    # Build section list with previews
    lines = []
    for i, section in enumerate(sections):
        title = section.get("title", f"Section {i+1}")
        start = section.get("start", 0)
        end = section.get("end", 0)
        preview = text[start:end][:100].replace("\n", " ").strip()
        lines.append(f"{i+1}. {title} — \"{preview}...\"")

    sections_list = "\n".join(lines)
    prompt = SUMMARY_PROMPT_TEMPLATE.format(sections_list=sections_list)

    client = _get_client()

    try:
        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response.content[0].text.strip()
        logger.info("Generated document summary (%d chars)", len(summary))
        return summary

    except Exception as exc:
        logger.warning("Summary generation failed (%s), using fallback", str(exc))
        return f"This document covers: {', '.join(titles)}."


# ─── Per-chunk search descriptions ───


async def generate_chunk_descriptions(sections: list[dict], text: str) -> list[str]:
    """Generate search-friendly descriptions for each section in a single Claude call.

    Falls back to section titles if AI fails.
    """
    titles = [s.get("title", f"Section {i+1}") for i, s in enumerate(sections)]

    # Build section list with previews
    lines = []
    for i, section in enumerate(sections):
        title = section.get("title", f"Section {i+1}")
        start = section.get("start", 0)
        end = section.get("end", 0)
        preview = text[start:end][:150].replace("\n", " ").strip()
        lines.append(f'{i+1}. "{title}" — "{preview}..."')

    sections_list = "\n".join(lines)
    prompt = DESCRIPTIONS_PROMPT_TEMPLATE.format(sections_list=sections_list)

    client = _get_client()

    try:
        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        descriptions = json.loads(raw)

        if isinstance(descriptions, list) and len(descriptions) == len(sections):
            logger.info("Generated %d chunk descriptions", len(descriptions))
            return descriptions

        logger.warning(
            "Description count mismatch (got %d, expected %d), using titles",
            len(descriptions) if isinstance(descriptions, list) else 0,
            len(sections),
        )
        return titles

    except Exception as exc:
        logger.warning("Chunk description generation failed (%s), using titles", str(exc))
        return titles


# ─── Main chunking function ───


async def chunk_document(text: str, file_name: str) -> list[dict]:
    """Intelligently chunk a document using AI-powered section detection.

    Returns list of dicts:
    [
        {
            "content": "full chunk text...",
            "chunk_index": 0,
            "metadata": {
                "title": "Document Overview",
                "is_summary": true,
                "search_description": "Overview of all topics in the document",
                "file_name": "Agreement.pdf"
            }
        },
        ...
    ]
    """
    if not text or not text.strip():
        return []

    text = text.strip()

    # Very short documents → single chunk
    if len(text) < MIN_DOC_LENGTH:
        logger.info("Short document (%d chars), returning as single chunk", len(text))
        return [{
            "content": text,
            "chunk_index": 0,
            "metadata": {
                "title": "Full Document",
                "is_summary": False,
                "search_description": file_name,
                "file_name": file_name,
            },
        }]

    # Step 1: AI section detection
    sections = await identify_sections(text)

    if not sections:
        # Fallback to dumb chunking
        logger.info("Using fallback chunking for %s", file_name)
        return _fallback_chunk(text, file_name)

    logger.info(
        "AI chunking | file=%s | sections=%d | titles=%s",
        file_name,
        len(sections),
        [s.get("title", "?") for s in sections],
    )

    # Step 2: Generate document summary
    summary = await generate_summary(sections, text)

    # Step 3: Generate search descriptions for each section
    descriptions = await generate_chunk_descriptions(sections, text)

    # Build chunks
    chunks: list[dict] = []

    # Chunk 0: Document overview
    chunks.append({
        "content": summary,
        "chunk_index": 0,
        "metadata": {
            "title": "Document Overview",
            "is_summary": True,
            "search_description": "Overview of all topics in the document",
            "file_name": file_name,
        },
    })

    # Remaining chunks: one per section
    for i, section in enumerate(sections):
        start = section.get("start", 0)
        end = section.get("end", len(text))
        content = text[start:end].strip()

        if not content:
            continue

        title = section.get("title", f"Section {i + 1}")
        description = descriptions[i] if i < len(descriptions) else title

        chunks.append({
            "content": content,
            "chunk_index": i + 1,  # 0 is reserved for summary
            "metadata": {
                "title": title,
                "is_summary": False,
                "search_description": description,
                "file_name": file_name,
            },
        })

    logger.info(
        "Chunked %s into %d chunks (1 summary + %d sections)",
        file_name, len(chunks), len(chunks) - 1,
    )

    return chunks


# ─── Fallback: dumb fixed-size chunking ───


def _fallback_chunk(
    text: str,
    file_name: str,
    chunk_size: int = 2000,
    chunk_overlap: int = 200,
) -> list[dict]:
    """Original fixed-size chunking as fallback when AI fails."""
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if not paragraphs:
        return []

    raw_chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(para) > chunk_size:
            if current:
                raw_chunks.append(current)
                current = ""
            raw_chunks.extend(_split_long_text(para, chunk_size))
            continue

        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                raw_chunks.append(current)
            current = para

    if current:
        raw_chunks.append(current)

    # Apply overlap
    if chunk_overlap > 0 and len(raw_chunks) > 1:
        overlapped: list[str] = [raw_chunks[0]]
        for i in range(1, len(raw_chunks)):
            prev = raw_chunks[i - 1]
            overlap = prev[-chunk_overlap:] if len(prev) > chunk_overlap else prev
            space_idx = overlap.find(" ")
            if space_idx > 0:
                overlap = overlap[space_idx + 1:]
            overlapped.append(f"{overlap}\n\n{raw_chunks[i]}")
        raw_chunks = overlapped

    result: list[dict] = []
    for idx, chunk in enumerate(raw_chunks):
        content = chunk.strip()
        if content:
            result.append({
                "content": content,
                "chunk_index": idx,
                "metadata": {
                    "title": f"Section {idx + 1}",
                    "is_summary": False,
                    "search_description": file_name,
                    "file_name": file_name,
                },
            })

    logger.info("Fallback chunking: %d chunks (size=%d, overlap=%d)", len(result), chunk_size, chunk_overlap)
    return result


def _split_long_text(text: str, chunk_size: int) -> list[str]:
    """Split text that exceeds chunk_size by sentences, then words."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) > 1:
        return _accumulate(sentences, chunk_size, " ")
    words = text.split()
    return _accumulate(words, chunk_size, " ")


def _accumulate(parts: list[str], max_size: int, joiner: str) -> list[str]:
    """Accumulate parts into chunks not exceeding max_size."""
    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = f"{current}{joiner}{part}" if current else part
        if len(candidate) <= max_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks
