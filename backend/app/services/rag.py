import logging

from supabase import Client

logger = logging.getLogger(__name__)

# Similarity thresholds — moderate first-pass, low fallback for small datasets.
# We fetch extra candidates then trim to MAX_RETURN for precision.
DEFAULT_THRESHOLD = 0.5
RETRY_THRESHOLD = 0.3
CANDIDATE_COUNT = 8   # fetch up to 8 from DB
MAX_RETURN = 5         # return top 5 to Claude (AI chunks are more precise)

# ─── Overview question detection ───

OVERVIEW_KEYWORDS = [
    "what is this", "what's this", "about this doc", "about this document",
    "summary", "summarize", "overview", "main topics", "key topics",
    "what should i know", "what do i need to know", "tell me about",
    "tell me what", "what does this cover", "what's covered", "key points",
    "highlights", "table of contents", "what are the sections",
    "what topics", "give me an overview", "walk me through",
    "what's in this", "what is in this", "brief me", "catch me up",
    # Coverage / absence phrasings — an absence claim ("X isn't covered") is
    # only groundable against the full document structure; retrieved chunks
    # cannot prove what other chunks lack. Route these through structure fetch.
    "not covered", "does it cover", "doesn't cover", "what's missing",
    "what is missing", "doesn't include", "not included",
    "what topics are absent", "not in this doc", "not in the document",
]


def is_overview_question(question: str) -> bool:
    """Detect whether the user is asking an overview/summary question."""
    question_lower = question.lower().strip()
    return any(keyword in question_lower for keyword in OVERVIEW_KEYWORDS)


# ─── Document structure for overview questions ───


def get_document_structure(supabase: Client, kb_id: str) -> dict:
    """Fetch summary chunk and all section titles for overview questions."""
    result = (
        supabase.table("document_chunks")
        .select("chunk_index, content, metadata")
        .eq("knowledge_base_id", kb_id)
        .order("chunk_index")
        .execute()
    )

    summary_content = None
    section_titles: list[dict] = []

    for chunk in (result.data or []):
        metadata = chunk.get("metadata") or {}

        if metadata.get("is_summary") is True:
            summary_content = chunk["content"]

        title = metadata.get("title", f"Section {chunk['chunk_index']}")
        if not metadata.get("is_summary"):
            section_titles.append({
                "index": chunk["chunk_index"],
                "title": title,
            })

    logger.info(
        "Document structure | kb_id=%s | has_summary=%s | sections=%d",
        kb_id, summary_content is not None, len(section_titles),
    )

    return {
        "summary": summary_content,
        "sections": section_titles,
    }


# ─── Context assembly ───


def build_context(
    chunks: list[dict],
    document_structure: dict | None = None,
    is_overview: bool = False,
) -> str:
    """Build the document context string for Claude.

    For overview questions: includes document structure + summary + relevant chunks.
    For specific questions: only relevant chunks.

    Labels chunks as 'Document Knowledge' (not 'Excerpts') so Claude treats them
    as knowledge it has internalized rather than text to quote.
    """
    context_parts: list[str] = []

    if is_overview and document_structure:
        # Add document structure overview
        if document_structure["sections"]:
            context_parts.append("--- Document Structure ---")
            context_parts.append("This document contains the following sections:")
            for section in document_structure["sections"]:
                context_parts.append(f"  {section['index']}. {section['title']}")
            context_parts.append("--- End Document Structure ---\n")

        # Add summary if available
        if document_structure.get("summary"):
            context_parts.append("--- Document Summary ---")
            context_parts.append(document_structure["summary"])
            context_parts.append("--- End Document Summary ---\n")

    if not chunks:
        return "\n".join(context_parts) if context_parts else ""

    # Add relevant chunks as knowledge context
    context_parts.append("--- Document Knowledge ---")
    context_parts.append(
        "The following sections from the knowledge base are relevant:\n"
    )

    for i, chunk in enumerate(chunks):
        metadata = chunk.get("metadata") or {}
        filename = chunk.get("file_name", "Unknown")
        title = metadata.get("title", f"Section {chunk.get('chunk_index', i)}")
        chunk_index = chunk.get("chunk_index", i)

        context_parts.append(f"[Section {chunk_index}] {filename} — \"{title}\"")
        context_parts.append(chunk.get("content", ""))
        context_parts.append("")  # blank line between sections

    context_parts.append("--- End Document Knowledge ---")

    return "\n".join(context_parts)


# ─── Vector search ───


def _call_match_chunks(
    supabase: Client,
    query_embedding: list[float],
    kb_id: str,
    match_count: int,
    threshold: float,
) -> list[dict]:
    """Call the match_chunks RPC, passing the embedding as a list (not a string).

    Supabase PostgREST expects JSON arrays for vector parameters.
    """
    result = supabase.rpc("match_chunks", {
        "query_embedding": query_embedding,
        "target_kb_id": kb_id,
        "match_count": match_count,
        "match_threshold": threshold,
    }).execute()

    return result.data or []


def search_similar_chunks(
    supabase: Client,
    query_embedding: list[float],
    kb_id: str,
    match_count: int = CANDIDATE_COUNT,
    threshold: float = DEFAULT_THRESHOLD,
) -> list[dict]:
    """Search for similar document chunks using the match_chunks PostgreSQL function.

    If fewer than 2 results above the threshold, retries with a lower threshold.
    Returns chunks with content, metadata, similarity, document_id, file_name, chunk_index.
    """
    logger.info(
        "Vector search | kb_id=%s | embedding_dims=%d | threshold=%.2f",
        kb_id, len(query_embedding), threshold,
    )

    # Sanity check: verify chunks exist for this KB
    count_result = (
        supabase.table("document_chunks")
        .select("id", count="exact")
        .eq("knowledge_base_id", kb_id)
        .limit(0)
        .execute()
    )
    total_chunks = count_result.count if count_result.count is not None else 0
    logger.info("Total chunks in KB | kb_id=%s | count=%d", kb_id, total_chunks)

    if total_chunks == 0:
        logger.info("No chunks stored for this KB | kb_id=%s", kb_id)
        return []

    chunks = _call_match_chunks(
        supabase, query_embedding, kb_id, match_count, threshold
    )

    logger.info(
        "match_chunks returned %d results at threshold=%.2f | kb_id=%s",
        len(chunks), threshold, kb_id,
    )

    # Only retry on zero results — don't dilute precision with low-similarity chunks
    if len(chunks) == 0 and threshold > RETRY_THRESHOLD:
        logger.info(
            "Retrying with threshold=%.2f | kb_id=%s", RETRY_THRESHOLD, kb_id
        )
        chunks = _call_match_chunks(
            supabase, query_embedding, kb_id, match_count, RETRY_THRESHOLD
        )
        logger.info(
            "Retry returned %d results | kb_id=%s", len(chunks), kb_id
        )

    if not chunks:
        logger.warning(
            "No similar chunks found even at threshold=%.2f | kb_id=%s | "
            "total_chunks_in_kb=%d — check IVFFlat index (lists may be too high for row count)",
            RETRY_THRESHOLD, kb_id, total_chunks,
        )
        return []

    # Fetch chunk_index (not returned by match_chunks) and file_name
    chunk_ids = [c["id"] for c in chunks]
    doc_ids = list({c["document_id"] for c in chunks})

    chunk_details = (
        supabase.table("document_chunks")
        .select("id, chunk_index, metadata")
        .in_("id", chunk_ids)
        .execute()
    )
    index_map = {d["id"]: d["chunk_index"] for d in (chunk_details.data or [])}
    metadata_map = {d["id"]: (d.get("metadata") or {}) for d in (chunk_details.data or [])}

    docs_result = (
        supabase.table("documents")
        .select("id, file_name")
        .in_("id", doc_ids)
        .execute()
    )
    name_map = {d["id"]: d["file_name"] for d in (docs_result.data or [])}

    for chunk in chunks:
        chunk["chunk_index"] = index_map.get(chunk["id"], 0)
        chunk["file_name"] = name_map.get(chunk["document_id"], "Unknown")
        chunk["metadata"] = metadata_map.get(chunk["id"], {})

    # Sort by similarity descending (should already be, but enforce it)
    chunks.sort(key=lambda c: c.get("similarity", 0), reverse=True)

    # Debug log: every candidate with score + content preview
    for i, c in enumerate(chunks):
        meta = c.get("metadata") or {}
        logger.info(
            "Chunk candidate %d | similarity=%.4f | file=%s | section=%d | title=%s | preview=%s | kb_id=%s",
            i + 1,
            c.get("similarity", 0),
            c.get("file_name", "?"),
            c.get("chunk_index", 0),
            meta.get("title", "?"),
            c.get("content", "")[:100].replace("\n", " "),
            kb_id,
        )

    # Trim to top MAX_RETURN chunks for precision
    chunks = chunks[:MAX_RETURN]

    logger.info(
        "Returning %d chunks (from %d candidates) | kb_id=%s | top=%.3f | bottom=%.3f",
        len(chunks), len(chunk_ids), kb_id,
        chunks[0].get("similarity", 0),
        chunks[-1].get("similarity", 0),
    )

    return chunks
