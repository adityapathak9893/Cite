import logging
import re

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    chunk_size: int = 2000,
    chunk_overlap: int = 200,
) -> list[dict]:
    """Split text into overlapping chunks.

    Strategy: split at paragraph breaks first, then sentence breaks,
    then word breaks. Each chunk is approximately 500 tokens (~2000 chars)
    with ~50 token overlap (~200 chars).
    """
    if not text or not text.strip():
        return []

    # Split into paragraphs (double newlines)
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if not paragraphs:
        return []

    # Build chunks by accumulating paragraphs up to chunk_size
    chunks: list[str] = []
    current_chunk = ""

    for para in paragraphs:
        # If a single paragraph exceeds chunk_size, split it further
        if len(para) > chunk_size:
            # Flush current chunk first
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            # Split long paragraph by sentences
            sub_chunks = _split_long_text(para, chunk_size)
            chunks.extend(sub_chunks)
            continue

        # Would adding this paragraph exceed chunk size?
        candidate = f"{current_chunk}\n\n{para}" if current_chunk else para
        if len(candidate) <= chunk_size:
            current_chunk = candidate
        else:
            # Save current chunk and start a new one
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    # Apply overlap: prepend tail of previous chunk to next chunk
    if chunk_overlap > 0 and len(chunks) > 1:
        overlapped: list[str] = [chunks[0]]
        for i in range(1, len(chunks)):
            prev = chunks[i - 1]
            overlap_text = prev[-chunk_overlap:] if len(prev) > chunk_overlap else prev
            # Find a word boundary in the overlap to avoid cutting mid-word
            space_idx = overlap_text.find(" ")
            if space_idx > 0:
                overlap_text = overlap_text[space_idx + 1:]
            overlapped.append(f"{overlap_text}\n\n{chunks[i]}")
        chunks = overlapped

    # Build result dicts, skip empty chunks
    result: list[dict] = []
    for idx, chunk in enumerate(chunks):
        content = chunk.strip()
        if content:
            result.append({
                "content": content,
                "chunk_index": idx,
                "metadata": {},
            })

    logger.info("Chunked text into %d chunks (size=%d, overlap=%d)", len(result), chunk_size, chunk_overlap)
    return result


def _split_long_text(text: str, chunk_size: int) -> list[str]:
    """Split text that exceeds chunk_size by sentences, then words."""
    # Try splitting by sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) > 1:
        return _accumulate(sentences, chunk_size, " ")

    # Fall back to word splitting
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
