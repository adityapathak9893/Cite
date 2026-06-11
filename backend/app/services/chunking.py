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
- List sections in the exact order they appear in the document
- For each section, return a short title (max 10 words) and a start_marker
- start_marker is the EXACT first 8-12 words of that section, copied character-for-character from the document text
- start_markers must be VERBATIM QUOTES, not paraphrases. Do not reword, fix typos, change casing or punctuation, or normalize whitespace within the quoted words — the marker will be located in the original text with an exact string search
- The first section's start_marker should be the very first words of the document
- Each section should cover roughly 200-3000 characters of the document. If a topic runs longer than 3000 characters, start a new section at a logical point within it; if a topic is shorter than 200 characters, fold it into the adjacent section that is most topically related
- Sections should start at paragraph or sentence boundaries — never mid-sentence

Respond with ONLY a JSON array, no other text:
[
  {"title": "Section title here", "start_marker": "exact first words of the section copied verbatim from the text"},
  {"title": "Next section title", "start_marker": "exact first words of the next section copied verbatim"},
  ...
]

Do NOT return character positions or offsets of any kind — only verbatim start_marker quotes."""

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


# ─── Deterministic markdown splitting ───

MARKDOWN_HEADING_RE = re.compile(r"^##\s", re.MULTILINE)
MARKDOWN_MIN_HEADINGS = 3


def _has_markdown_structure(text: str) -> bool:
    """True when the document has enough ## headings to split deterministically."""
    return len(MARKDOWN_HEADING_RE.findall(text)) >= MARKDOWN_MIN_HEADINGS


def _split_markdown_sections(text: str) -> list[dict]:
    """Split a markdown document at ## heading lines — no AI involved.

    Each section runs from its heading line to the character before the next
    heading; content before the first heading becomes a preamble section.
    Returns the same shape as AI detection: [{"title", "start", "end"}, ...]
    """
    heading_starts = [m.start() for m in MARKDOWN_HEADING_RE.finditer(text)]
    if not heading_starts:
        return []

    sections: list[dict] = []

    if heading_starts[0] > 0 and text[:heading_starts[0]].strip():
        sections.append({"title": "Preamble", "start": 0, "end": heading_starts[0]})

    for i, start in enumerate(heading_starts):
        end = heading_starts[i + 1] if i + 1 < len(heading_starts) else len(text)
        heading_line = text[start:end].split("\n", 1)[0]
        title = heading_line.lstrip("#").strip()[:80] or f"Section {i + 1}"
        sections.append({"title": title, "start": start, "end": end})

    sections = _merge_undersized_sections(sections)
    return _split_oversized_sections(sections, text)


def _merge_undersized_sections(sections: list[dict]) -> list[dict]:
    """Merge sections shorter than SECTION_MIN into their neighbor."""
    merged: list[dict] = []
    for section in sections:
        if merged and section["end"] - section["start"] < SECTION_MIN:
            merged[-1]["end"] = section["end"]
        else:
            merged.append(dict(section))

    # An undersized first section has no previous neighbor — fold it into the next
    if len(merged) > 1 and merged[0]["end"] - merged[0]["start"] < SECTION_MIN:
        merged[1] = {
            "title": merged[1]["title"],
            "start": merged[0]["start"],
            "end": merged[1]["end"],
        }
        merged = merged[1:]

    return merged


def _split_oversized_sections(sections: list[dict], text: str) -> list[dict]:
    """Split sections longer than SECTION_MAX at paragraph breaks (\\n\\n)."""
    result: list[dict] = []
    for section in sections:
        if section["end"] - section["start"] <= SECTION_MAX:
            result.append(section)
            continue
        spans = _paragraph_spans(text, section["start"], section["end"])
        for j, (start, end) in enumerate(spans):
            title = section["title"] if j == 0 else f"{section['title']} (part {j + 1})"
            result.append({"title": title, "start": start, "end": end})
    return result


def _paragraph_spans(text: str, start: int, end: int) -> list[tuple[int, int]]:
    """Cut [start, end) into spans of at most SECTION_MAX chars at \\n\\n breaks.

    Cuts only ever land on a paragraph break — a span with no break in range
    is left whole (slightly oversized) rather than severed mid-word.
    """
    spans: list[tuple[int, int]] = []
    cursor = start
    while end - cursor > SECTION_MAX:
        cut = text.rfind("\n\n", cursor + SECTION_MIN, cursor + SECTION_MAX)
        if cut == -1:
            cut = text.find("\n\n", cursor + SECTION_MAX, end)
        if cut == -1:
            break
        spans.append((cursor, cut))
        cursor = cut
    spans.append((cursor, end))
    return spans


# ─── Verbatim-marker boundary location ───


def _locate_marker_boundaries(text: str, sections: list[dict]) -> list[dict] | None:
    """Convert AI-returned verbatim start_markers into character boundaries.

    Each marker is located with an exact sequential string search — search_from
    advances past each located marker so duplicate text earlier in the document
    can never produce a false match. A marker that cannot be found is skipped
    (its span is absorbed by the previous section). Returns None when more than
    a third of markers fail, signalling the caller to abandon AI sectioning.
    """
    located: list[dict] = []
    failed = 0
    search_from = 0

    for i, section in enumerate(sections):
        marker = str(section.get("start_marker") or "").strip()
        title = section.get("title", f"Section {i + 1}")

        if not marker:
            failed += 1
            logger.warning("Section %d (%s) has empty start_marker, skipping boundary", i + 1, title)
            continue

        position = text.find(marker, search_from)
        if position == -1:
            failed += 1
            logger.warning(
                "Start marker not found in text, absorbing span into previous section: %r",
                marker[:120],
            )
            continue

        located.append({"title": title, "start": position})
        search_from = position + len(marker)

    if failed * 3 > len(sections):
        logger.warning(
            "%d of %d section markers failed to locate — abandoning AI sectioning, "
            "using fixed-size fallback chunking",
            failed, len(sections),
        )
        return None

    if not located:
        return None

    # First section absorbs any text before its marker (covers the whole document)
    located[0]["start"] = 0

    boundaries: list[dict] = []
    for i, item in enumerate(located):
        end = located[i + 1]["start"] if i + 1 < len(located) else len(text)
        boundaries.append({"title": item["title"], "start": item["start"], "end": end})

    return boundaries


# ─── AI-powered section detection ───


async def identify_sections(text: str) -> list[dict]:
    """Identify logical section boundaries in the document.

    Documents with markdown structure (3+ ## headings) are split
    deterministically with no AI call. Otherwise Claude returns verbatim
    start markers (never character positions — LLMs cannot count characters)
    which are located in the text by exact string search.

    Returns list of dicts: [{"title": "...", "start": int, "end": int}, ...]
    Returns [] on failure so the caller falls back to fixed-size chunking.
    """
    if _has_markdown_structure(text):
        sections = _split_markdown_sections(text)
        if sections:
            logger.info(
                "Markdown structure detected, split into %d sections deterministically (no AI call)",
                len(sections),
            )
            return sections

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

        ai_sections = json.loads(raw)

        if not isinstance(ai_sections, list) or len(ai_sections) == 0:
            logger.warning("AI returned empty/invalid sections, falling back")
            return []

        # Validate structure
        for s in ai_sections:
            if not isinstance(s, dict):
                logger.warning("AI returned malformed section: %s", s)
                return []

        # Markers are located within ai_text so boundaries never cross the
        # AI_CHAR_LIMIT cutoff — the remainder is handled heuristically below
        sections = _locate_marker_boundaries(ai_text, ai_sections)
        if sections is None:
            return []

        logger.info(
            "AI identified %d sections (%d boundaries located) in first %d chars",
            len(ai_sections), len(sections), len(ai_text),
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
