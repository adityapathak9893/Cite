import asyncio
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

OPENAI_EMBEDDING_URL = "https://api.openai.com/v1/embeddings"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
BATCH_SIZE = 100
MAX_RETRIES = 3


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using OpenAI API.

    Batches up to 100 texts per API call. Retries with exponential backoff.
    Uses httpx async client directly (not the openai SDK).
    """
    if not texts:
        return []

    settings = get_settings()
    all_embeddings: list[list[float]] = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        for batch_start in range(0, len(texts), BATCH_SIZE):
            batch = texts[batch_start:batch_start + BATCH_SIZE]
            embeddings = await _embed_batch(client, batch, settings.openai_api_key)
            all_embeddings.extend(embeddings)

    logger.info("Generated %d embeddings", len(all_embeddings))
    return all_embeddings


async def _embed_batch(
    client: httpx.AsyncClient,
    texts: list[str],
    api_key: str,
) -> list[list[float]]:
    """Embed a single batch with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.post(
                OPENAI_EMBEDDING_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": EMBEDDING_MODEL,
                    "input": texts,
                    "dimensions": EMBEDDING_DIMENSIONS,
                },
            )

            if response.status_code == 429:
                # Rate limited — wait and retry
                wait_time = 2 ** (attempt + 1)
                logger.warning(
                    "OpenAI rate limit hit, retrying in %ds (attempt %d/%d)",
                    wait_time, attempt + 1, MAX_RETRIES,
                )
                await asyncio.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()

            # Sort by index to ensure correct order
            sorted_data = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in sorted_data]

        except httpx.HTTPStatusError as exc:
            if attempt == MAX_RETRIES - 1:
                logger.error("OpenAI embedding failed after %d retries: %s", MAX_RETRIES, str(exc))
                raise
            wait_time = 2 ** (attempt + 1)
            logger.warning("OpenAI embedding error, retrying in %ds: %s", wait_time, str(exc))
            await asyncio.sleep(wait_time)

    raise RuntimeError("Embedding failed after all retries")
