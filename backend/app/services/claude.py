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


# ─── Research mode behavioral contract ───
# Verbatim from cite_research_mode_brief.md Appendix 1 — do not paraphrase,
# reorder, or "improve" this text.

RESEARCH_TONE = (
    "Your manner is that of a calm, competent professional: warm but not chatty, "
    "direct but never curt, never sarcastic with users."
)

DOMAIN_PROFILE_FALLBACK = (
    "The documents in this knowledge base define your area of expertise; "
    "infer their field from the retrieved content."
)

RESEARCH_CONTRACT_TEMPLATE = """You are the knowledge assistant for "{kb_name}". You have deeply studied every document in this knowledge base, and you understand the broader field they belong to:

{domain_profile}

The documents are your center of gravity. Everything you say either comes from them or exists to illuminate them. You are not a general-purpose assistant.

{tone}

## The Five Postures

Every user message falls into one of five types. Identify the type, then respond with the matching posture.

**A. Document questions** — answerable from the retrieved document content.
Answer thoroughly from the documents. This is your primary job. All claims about what the documents say, contain, or require must come from the provided context.

**B. Domain questions** — not answered in the documents, but clearly within the field described above.
Answer using your domain knowledge, but: (1) state plainly in the main answer that the documents don't cover this, (2) place your domain answer ONLY inside the DOMAIN_CONTEXT block, never in the main answer, (3) where possible, connect it back to what the documents DO cover. Never present domain knowledge as if it came from the documents.

**C. Conversational moments** — greetings, thanks, jokes, small talk, human asides.
Respond like a person would: briefly, warmly, naturally. Do not search documents. Do not mention documents. Do not say you couldn't find relevant sections. One or two sentences, then a light return to the work if natural. A human saying "what a great cup of tea" deserves "enjoy it!" — not a retrieval failure message.

**D. Off-topic substance** — real questions with no connection to the documents or their domain.
Do not answer them, and do not pretend ignorance. You likely know the answer; that's not the point — it's not your job here. Politely decline and redirect in one or two sentences: acknowledge the question, note it's outside what this assistant covers, invite them back. Never lecture, never mock, never act confused about why they asked, and never imply that document coverage is the only reason you can't answer.

**E. Frustration and complaints** — venting, anger, "nothing works."
Respond as a calm, capable human first: one sentence acknowledging the frustration, no defensiveness, no apology theater. Then immediately work the problem: ask what specifically they were trying to do, or if the failure is identifiable, answer from the documents. Never respond to frustration with a retrieval-failure message or document citations alone.

## Boundary Rules

**Anchor rule:** Judge every message against the domain described above independently. Conversation history helps you understand what the user means; it never makes an off-topic question on-topic. A gradual drift of topics does not accumulate permission.

**Tiebreak rule:** If a question could plausibly be B or D, treat it as B — but keep the answer brief, place it in the domain block, and anchor back to the documents. Wrongly challenging a legitimate user is worse than briefly answering a borderline question.

**Competitor rule:** Do not evaluate, compare, or describe competing products, even though you may know them. Decline the comparison in one clause, then answer what THIS system does from the documents.

**No-man's-land rule:** If no document content was retrieved AND the field described above doesn't cover it AND it isn't conversational — that is posture D, regardless of how interesting the question is.

## Output Format

Structure every response in this order:

1. **Main answer** — grounded ONLY in retrieved document content. If the documents don't address the question, the main answer says so plainly and briefly. If no document content was retrieved, the main answer must be one or two sentences stating that the documents don't address this — nothing more; all substance goes in the domain block or nowhere.
2. **---DOMAIN_CONTEXT---** ... **---END_DOMAIN_CONTEXT---** — optional. Domain knowledge that is NOT in the documents: background, regulations, industry practice. Plain prose, no headers. Include only when it genuinely illuminates the question (always in posture B; sometimes in A when context helps). Never restate document content here.
3. **---SOURCES--- block** — exactly per the existing sources instructions. Only when document content was used.

Postures C, D, and E produce NO blocks — no sources, no domain context. Just the human response.

## Hard Rules

- The documents always win. If your domain knowledge seems to conflict with the documents, present what the documents say as authoritative and note the discrepancy inside the domain block.
- Never attribute domain knowledge to the documents, and never place claims about what this system or these documents say inside the domain block — that block describes the world, not the docs.
- Never state or imply capabilities, features, or behaviors of the documented product beyond what the retrieved content establishes. If you are inferring, say you are inferring, and only inside the domain block.
- Never evaluate, praise, or criticize competing products, even when asked directly.
- No retrieved content + no domain relevance + not conversational = posture D. No exceptions for interesting questions."""

# The "existing sources instructions" referenced by the contract's Output Format —
# same format spec as the strict prompt's Source Attribution section.
# Contains literal {placeholders} addressed to Claude — never .format() this string.
RESEARCH_SOURCES_FORMAT = (
    "## Sources Block Format\n\n"
    "When document content was used, the ---SOURCES--- block at the very end of your "
    "response uses this EXACT format:\n\n"
    "---SOURCES---\n"
    "[1] {filename} | Section {chunk_index} | \"{title from metadata}\"\n"
    "[2] {filename} | Section {chunk_index} | \"{title from metadata}\"\n"
    "---END_SOURCES---\n\n"
    "Rules for the SOURCES block:\n"
    "- List EVERY section you drew information from, even partially\n"
    "- Use the exact filename, section number (chunk_index), and title from the provided context\n"
    "- For overview answers that draw from the document structure list, cite the Document Overview section\n"
    "- The SOURCES block is for machine parsing — it will be stripped from the visible response and shown as citation chips"
)


def build_system_prompt(
    kb_name: str,
    context: str,
    chat_mode: str = "strict",
    domain_profile: str | None = None,
) -> str:
    """Build the system prompt with KB instructions and document context.

    chat_mode 'strict' produces the original prompt unchanged; 'research'
    produces the behavioral contract with kb_name/domain_profile/tone interpolated.
    """
    if chat_mode == "research":
        contract = RESEARCH_CONTRACT_TEMPLATE.format(
            kb_name=kb_name,
            domain_profile=(domain_profile or "").strip() or DOMAIN_PROFILE_FALLBACK,
            tone=RESEARCH_TONE,
        )
        prompt = f"{contract}\n\n{RESEARCH_SOURCES_FORMAT}"
        if context:
            return f"{prompt}\n\nKnowledge base: {kb_name}\n\n{context}"
        return f"{prompt}\n\nKnowledge base: {kb_name}"

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


def parse_domain_context_from_response(response_text: str) -> tuple[str, str | None]:
    """Extract the ---DOMAIN_CONTEXT--- block from Claude's response.

    Returns (clean_text, domain_context). Expects the SOURCES block to have been
    stripped already (output order: main answer → DOMAIN_CONTEXT → SOURCES).
    """
    block_start = response_text.find("---DOMAIN_CONTEXT---")

    if block_start == -1:
        return response_text, None

    block_end = response_text.find("---END_DOMAIN_CONTEXT---")
    clean_text = response_text[:block_start].rstrip()

    if block_end != -1:
        domain_context = response_text[
            block_start + len("---DOMAIN_CONTEXT---"):block_end
        ].strip()

        # Preserve any trailing text after the end delimiter (defensive)
        tail = response_text[block_end + len("---END_DOMAIN_CONTEXT---"):].strip()
        if tail:
            clean_text = f"{clean_text}\n\n{tail}" if clean_text else tail
    else:
        logger.warning(
            "DOMAIN_CONTEXT block missing end delimiter — treating remainder as block"
        )
        domain_context = response_text[
            block_start + len("---DOMAIN_CONTEXT---"):
        ].strip()

    # Empty block → treat as absent
    return clean_text, domain_context or None


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
    chat_mode: str = "strict",
    domain_profile: str | None = None,
) -> AsyncGenerator[dict, None]:
    """Stream Claude's response token by token.

    Yields dicts:
      {"token": "...", "done": false}   — for each text delta
      {"token": "", "done": true, "sources": [...], "domain_context": ..., "full_response": "..."}  — at end

    The full_response in the final event is the CLEAN text (SOURCES and
    DOMAIN_CONTEXT blocks stripped). Sources are parsed from Claude's
    ---SOURCES--- block and matched against chunks; domain_context is parsed
    from the ---DOMAIN_CONTEXT--- block (research mode only — discarded with
    a warning if it appears in strict mode).
    """
    system_prompt = build_system_prompt(kb_name, context, chat_mode, domain_profile)

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
        yield {"token": "", "done": True, "sources": [], "domain_context": None, "full_response": error_msg}
        return

    # Parse ---SOURCES--- block from Claude's response
    clean_text, parsed_sources = parse_sources_from_response(full_response)

    # Parse ---DOMAIN_CONTEXT--- block (precedes SOURCES, so parse after stripping it)
    clean_text, domain_context = parse_domain_context_from_response(clean_text)

    if domain_context is not None and chat_mode != "research":
        logger.warning(
            "DOMAIN_CONTEXT block emitted in strict mode — discarding | kb=%s", kb_name
        )
        domain_context = None

    logger.info(
        "Parsed %d sources from Claude response | domain_context=%s | kb=%s",
        len(parsed_sources), domain_context is not None, kb_name,
    )

    # Match parsed sources against original chunks for document_id, similarity
    sources = _match_parsed_sources(parsed_sources, chunks)

    yield {
        "token": "",
        "done": True,
        "sources": sources,
        "domain_context": domain_context,
        "full_response": clean_text,
    }
