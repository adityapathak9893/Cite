import logging

from supabase import Client

logger = logging.getLogger(__name__)

# Similarity thresholds — kept low because:
# 1. Small datasets produce lower cosine similarity scores overall
# 2. The IVFFlat index with too many lists can miss results
# 3. Better to send marginal chunks to Claude and let it decide relevance
#    than to filter them out and return "I don't have enough information"
DEFAULT_THRESHOLD = 0.2
RETRY_THRESHOLD = 0.0


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
    match_count: int = 5,
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

    # If fewer than 2 results, retry with lower threshold
    if len(chunks) < 2 and threshold > RETRY_THRESHOLD:
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

    # Log similarity scores for debugging
    similarities = [c.get("similarity", 0) for c in chunks]
    logger.info(
        "Similarity scores | kb_id=%s | scores=%s",
        kb_id, [round(s, 3) for s in similarities],
    )

    # Fetch chunk_index (not returned by match_chunks) and file_name
    chunk_ids = [c["id"] for c in chunks]
    doc_ids = list({c["document_id"] for c in chunks})

    chunk_details = (
        supabase.table("document_chunks")
        .select("id, chunk_index")
        .in_("id", chunk_ids)
        .execute()
    )
    index_map = {d["id"]: d["chunk_index"] for d in (chunk_details.data or [])}

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

    logger.info(
        "Found %d similar chunks | kb_id=%s | top_similarity=%.3f",
        len(chunks), kb_id, chunks[0].get("similarity", 0),
    )

    return chunks
