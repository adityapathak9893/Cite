import json
import logging
import re

from supabase import Client

from app.config import CLAUDE_MODEL
from app.services.claude import _get_client

logger = logging.getLogger(__name__)

SUMMARY_PREVIEW_LIMIT = 1500  # Max chars of each document summary sent to Claude

PROFILE_PROMPT_TEMPLATE = """\
You are profiling a knowledge base for an AI document assistant. Below are the summaries of every document currently in the knowledge base.

Produce a JSON object with exactly two fields:

1. "domain_profile" — 2-4 sentences covering: what these documents concern; the surrounding field they belong to; adjacent topics that count as in-domain. If the documents span multiple unrelated domains, say so explicitly and name each domain.

2. "suggested_questions" — an array of 4-6 questions a user might ask this knowledge base. Each question must be specific to THIS corpus and demonstrate the assistant's capability: reference actual names, terms, processes, metrics, or concepts that appear in the summaries (invent questions grounded in the summaries below — the shape should be like
"How is the X metric calculated?" or "What is the approval process for Y?",
where X and Y are real terms from these documents). Never use generic templates like "Summarize the key points", "What are the main topics?", or "Find important dates."

Document summaries:
{summaries_list}

Respond with ONLY a JSON object, no other text:
{{"domain_profile": "...", "suggested_questions": ["...", "..."]}}"""


async def generate_kb_profile(summaries: list[dict]) -> dict | None:
    """Generate a KB-level domain profile + suggested questions in a single Claude call.

    summaries: [{"file_name": "...", "summary": "..."}, ...]
    Returns {"domain_profile": str, "suggested_questions": [str, ...]} or None on failure
    (caller leaves previous values in place — mirrors the AI-chunking fallback philosophy).
    """
    lines = []
    for i, doc in enumerate(summaries):
        file_name = doc.get("file_name", f"Document {i + 1}")
        summary = doc.get("summary", "").strip()[:SUMMARY_PREVIEW_LIMIT]
        lines.append(f"{i + 1}. {file_name}:\n{summary}")

    summaries_list = "\n\n".join(lines)
    prompt = PROFILE_PROMPT_TEMPLATE.format(summaries_list=summaries_list)

    client = _get_client()

    try:
        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        profile = json.loads(raw)

        if (
            not isinstance(profile, dict)
            or not isinstance(profile.get("domain_profile"), str)
            or not profile["domain_profile"].strip()
            or not isinstance(profile.get("suggested_questions"), list)
            or not profile["suggested_questions"]
            or not all(isinstance(q, str) and q.strip() for q in profile["suggested_questions"])
        ):
            logger.warning("KB profile generation returned malformed JSON, keeping previous values")
            return None

        logger.info(
            "Generated KB profile (%d chars, %d suggested questions)",
            len(profile["domain_profile"]),
            len(profile["suggested_questions"]),
        )
        return {
            "domain_profile": profile["domain_profile"].strip(),
            "suggested_questions": [q.strip() for q in profile["suggested_questions"]],
        }

    except Exception as exc:
        logger.warning("KB profile generation failed (%s), keeping previous values", str(exc))
        return None


async def regenerate_kb_profile(supabase: Client, kb_id: str) -> None:
    """Regenerate the KB's domain profile + suggested questions from all document summaries.

    Never raises — a failure is logged and the KB's previous values stay in place,
    so document upload/deletion is never broken by profile generation.
    """
    try:
        # Chunk 0 of every document is its summary (or first chunk for fallback-chunked docs)
        result = (
            supabase.table("document_chunks")
            .select("content, metadata")
            .eq("knowledge_base_id", kb_id)
            .eq("chunk_index", 0)
            .execute()
        )
        rows = result.data or []

        if not rows:
            # No documents left — clear the profile rather than describe an empty KB
            supabase.table("knowledge_bases").update({
                "domain_profile": None,
                "suggested_questions": None,
            }).eq("id", kb_id).execute()
            logger.info("KB has no documents, cleared profile | kb_id=%s", kb_id)
            return

        summaries = [
            {
                "file_name": (row.get("metadata") or {}).get("file_name", ""),
                "summary": row.get("content", ""),
            }
            for row in rows
        ]

        profile = await generate_kb_profile(summaries)

        if profile is None:
            logger.warning("KB profile regeneration skipped (generation failed) | kb_id=%s", kb_id)
            return

        supabase.table("knowledge_bases").update({
            "domain_profile": profile["domain_profile"],
            "suggested_questions": profile["suggested_questions"],
        }).eq("id", kb_id).execute()

        logger.info(
            "KB profile updated | kb_id=%s | documents=%d",
            kb_id, len(summaries),
        )

    except Exception as exc:
        logger.warning(
            "KB profile regeneration failed (keeping previous values) | kb_id=%s | error=%s",
            kb_id, str(exc),
        )


async def regenerate_kb_profile_task(
    kb_id: str,
    supabase_url: str,
    supabase_key: str,
) -> None:
    """Background-task wrapper: creates its own Supabase client (mirrors process_document)."""
    from supabase import create_client

    supabase = create_client(supabase_url, supabase_key)
    await regenerate_kb_profile(supabase, kb_id)
