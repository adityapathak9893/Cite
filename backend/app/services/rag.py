import logging

from supabase import Client

logger = logging.getLogger(__name__)

# Hybrid retrieval (migration 002) fuses a pgvector channel and a Postgres FTS
# channel with Reciprocal Rank Fusion. The tuning knobs — vector top-20 @ floor
# 0.3, FTS top-10, RRF k=60, final top-5 — live in the match_chunks_hybrid RPC
# signature (single source of truth); this module just calls it. The old
# 0.5/0.3 two-step vector-only path was removed with the same migration.

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


# ─── Hybrid search (vector + FTS, RRF-fused) ───


def search_similar_chunks(
    supabase: Client,
    query_embedding: list[float],
    query_text: str,
    kb_id: str,
) -> list[dict]:
    """Retrieve the most relevant chunks via the match_chunks_hybrid RPC.

    Runs a pgvector channel and a Postgres FTS channel and fuses their rankings
    with Reciprocal Rank Fusion (migration 002). Zero retrieval means BOTH
    channels came back empty. Returns the fused top chunks in RRF order (best
    first), each with content, metadata, similarity, document_id, chunk_index,
    plus the per-channel ranks and rrf_score, enriched with file_name.
    """
    logger.info(
        "Hybrid search | kb_id=%s | embedding_dims=%d | query=%s",
        kb_id, len(query_embedding), query_text[:100],
    )

    # Sanity check: verify chunks exist for this KB (cheap guard + useful log).
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

    # The embedding goes over the wire as a JSON array (PostgREST casts to vector).
    # Tuning params default in the RPC signature; we pass only the query inputs.
    result = supabase.rpc("match_chunks_hybrid", {
        "p_kb_id": kb_id,
        "p_query_embedding": query_embedding,
        "p_query_text": query_text,
    }).execute()
    chunks = result.data or []

    if not chunks:
        logger.warning(
            "Zero retrieval — both vector and FTS channels empty | kb_id=%s | "
            "total_chunks_in_kb=%d",
            kb_id, total_chunks,
        )
        return []

    # The RPC returns chunk_index + metadata; only file_name needs a lookup.
    doc_ids = list({c["document_id"] for c in chunks})
    docs_result = (
        supabase.table("documents")
        .select("id, file_name")
        .in_("id", doc_ids)
        .execute()
    )
    name_map = {d["id"]: d["file_name"] for d in (docs_result.data or [])}
    for chunk in chunks:
        chunk["file_name"] = name_map.get(chunk["document_id"], "Unknown")

    # Preserve the RPC's fused (rrf_score) order — do NOT re-sort by similarity,
    # which would undo the ranking that lifts keyword-matched sections.
    for i, c in enumerate(chunks):
        meta = c.get("metadata") or {}
        logger.info(
            "Hybrid candidate %d | rrf=%.5f | vec_rank=%s | fts_rank=%s | "
            "sim=%.4f | file=%s | section=%s | title=%s | preview=%s | kb_id=%s",
            i + 1,
            c.get("rrf_score") or 0,
            c.get("vector_rank"),
            c.get("fts_rank"),
            c.get("similarity") or 0,
            c.get("file_name", "?"),
            c.get("chunk_index"),
            meta.get("title", "?"),
            c.get("content", "")[:100].replace("\n", " "),
            kb_id,
        )

    logger.info(
        "Returning %d fused chunks | kb_id=%s | top_rrf=%.5f | bottom_rrf=%.5f",
        len(chunks), kb_id,
        chunks[0].get("rrf_score") or 0,
        chunks[-1].get("rrf_score") or 0,
    )

    return chunks
