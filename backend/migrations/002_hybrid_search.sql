-- Migration 002: Hybrid search (Postgres FTS + pgvector, fused with RRF)
-- Run in the Supabase SQL Editor.
--
-- Why: vector-only retrieval is keyword-blind. Production/eval evidence
-- (grounded-02): the query "schedule a weekly vulnerability scan" never
-- retrieved the section literally titled "Scan Scheduling" — the lexical signal
-- was invisible to embeddings. This adds a Postgres full-text-search channel and
-- fuses it with the vector channel via Reciprocal Rank Fusion (RRF).
--
-- Design decisions (hybrid-search sprint brief, approved 2026-07-07):
--   D1  per-KB language config (this migration adds the column; default 'english'
--       so stemming maps "scheduling"->"schedule", "scans"->"scan").
--   D2  vector top-20 @ similarity floor 0.3; FTS top-10 by ts_rank; RRF k=60;
--       final top-5. Zero-retrieval = BOTH channels empty.
--   D4  generated tsvector over title + content + search_description; GIN index;
--       new RPC match_chunks_hybrid.
--
-- Rollback: the base `match_chunks` RPC is intentionally left untouched — reverting
-- rag.py's call sites restores vector-only retrieval with no schema change needed.
-- The `language` and `fts` columns and this RPC are additive and can stay in place.
--
-- Idempotent where practical (IF NOT EXISTS / CREATE OR REPLACE). Adding the STORED
-- generated `fts` column rewrites document_chunks once and backfills every existing
-- chunk — no re-chunk/re-embed required (unlike the embeddings, FTS is free for
-- documents already indexed).

-- ── D1: per-KB language config ──────────────────────────────────────────────
-- Used on the QUERY side (to_tsquery/websearch_to_tsquery) in match_chunks_hybrid.
-- KNOWN LIMITATION: the doc-side `fts` column below is fixed at 'english' (a STORED
-- generated column cannot reference another table's column, and to_tsvector is only
-- IMMUTABLE with a literal config). So a non-English KB (e.g. Hindi/Devanagari, or
-- mojibake from legacy-font extraction) gets an English stemmer on the document side
-- and its FTS contributes ~nothing — hybrid silently degrades to vector-only for
-- that KB. Acceptable now; multilingual is Proposed, not Approved. Because language
-- is a per-KB column, fixing this later is a data update + a doc-side re-index, not
-- a re-design.
alter table knowledge_bases
  add column if not exists language text not null default 'english';

-- ── D4: generated tsvector over title + content + search_description ─────────
-- Title is the keyword goldmine (e.g. "Scan Scheduling") and MUST be indexed.
-- title and search_description live in the metadata jsonb; content is a column.
-- to_tsvector('english', ...) with a literal config is IMMUTABLE, so it is valid
-- in a STORED generated column; the jsonb ->> operator and || are immutable too.
alter table document_chunks
  add column if not exists fts tsvector
  generated always as (
    to_tsvector(
      'english',
      coalesce(metadata ->> 'title', '') || ' ' ||
      coalesce(content, '') || ' ' ||
      coalesce(metadata ->> 'search_description', '')
    )
  ) stored;

-- GIN index for fast @@ lookups on the tsvector.
create index if not exists document_chunks_fts_idx
  on document_chunks using gin (fts);

-- ── D2/D4: hybrid retrieval RPC ─────────────────────────────────────────────
-- Runs a vector channel and an FTS channel independently, ranks each, and fuses
-- the ranks with RRF (score = sum over channels of 1/(k + rank)). Returns the
-- top p_final_limit fused rows, plus per-channel ranks and the RRF score so the
-- retrieval benchmark can publish rank + margin.
--
-- NOTE (approved 2026-07-07, D2 refinement): the FTS channel uses OR-of-stems, not
-- websearch_to_tsquery's AND-of-all-terms. Schema recon showed AND is too strict for
-- keyword recall — the flagship query "schedule a weekly vulnerability scan" would
-- drop the "Scan Scheduling" section purely because that section never contains the
-- word "vulnerability". We reuse websearch_to_tsquery's stemming/parsing, then swap
-- its `&` operators for `|`; ts_rank then orders full-term matches above partial ones.
create or replace function match_chunks_hybrid(
  p_kb_id uuid,
  p_query_embedding vector(1536),
  p_query_text text,
  p_vector_limit int default 20,
  p_vector_floor float default 0.3,
  p_fts_limit int default 10,
  p_rrf_k int default 60,
  p_final_limit int default 5
)
returns table (
  id uuid,
  document_id uuid,
  chunk_index int,
  content text,
  metadata jsonb,
  similarity float,
  vector_rank int,
  fts_rank int,
  rrf_score float
)
language sql
stable
as $$
  with q as (
    -- Build the OR-recall FTS query once for this KB's language config.
    -- Language resolution is defensive: an unknown/invalid config name would make
    -- ::regconfig raise and take down the whole RPC, so we look the name up in
    -- pg_ts_config and fall back to 'english' (D1: a non-English KB degrades to
    -- vector-only — it must never crash chat). We reuse websearch_to_tsquery's
    -- stemming/sanitizing (it never errors on arbitrary input), render it to
    -- text, and swap its AND operators (' & ') for OR (' | '); phrase operators
    -- (' <-> ') are left intact, and a rare user '-term' becomes '| !term'
    -- (harmless — ts_rank + the top-10 cap + the vector channel bound any
    -- over-match). nullif('', ...) maps an all-stopword query (e.g. "tell me
    -- more") to NULL: an empty/NULL tsquery matches nothing, so the FTS channel
    -- is simply empty and the vector channel decides.
    select
      nullif(
        replace(
          websearch_to_tsquery(
            coalesce(
              (select cfgname from pg_ts_config where cfgname = kb.language),
              'english'
            )::regconfig,
            p_query_text
          )::text,
          ' & ', ' | '
        ),
        ''
      )::tsquery as fts_query
    from knowledge_bases kb
    where kb.id = p_kb_id
  ),
  vec as (
    -- Vector channel: top-N by cosine distance, above the similarity floor.
    -- id tiebreaks keep both the LIMIT membership and the rank deterministic.
    select ranked.id, row_number() over (order by ranked.dist, ranked.id) as r
    from (
      select dc.id, (dc.embedding <=> p_query_embedding) as dist
      from document_chunks dc
      where dc.knowledge_base_id = p_kb_id
        and 1 - (dc.embedding <=> p_query_embedding) >= p_vector_floor
      order by dc.embedding <=> p_query_embedding, dc.id
      limit p_vector_limit
    ) ranked
  ),
  fts as (
    -- FTS channel: top-N by ts_rank against the OR-recall query.
    -- ts_rank ties are common; the id tiebreaks make membership + rank stable.
    select ranked.id, row_number() over (order by ranked.rank desc, ranked.id) as r
    from (
      select dc.id, ts_rank(dc.fts, (select fts_query from q)) as rank
      from document_chunks dc
      where dc.knowledge_base_id = p_kb_id
        and dc.fts @@ (select fts_query from q)
      order by ts_rank(dc.fts, (select fts_query from q)) desc, dc.id
      limit p_fts_limit
    ) ranked
  ),
  candidates as (
    -- Union of the two channels' ids drives the final join, so we resolve full
    -- rows for only the (<= vector_limit + fts_limit) fused candidates.
    select id from vec
    union
    select id from fts
  )
  select
    dc.id,
    dc.document_id,
    dc.chunk_index,
    dc.content,
    dc.metadata,
    (1 - (dc.embedding <=> p_query_embedding))::float as similarity,
    vec.r::int as vector_rank,
    fts.r::int as fts_rank,
    (
      coalesce(1.0 / (p_rrf_k + vec.r), 0) +
      coalesce(1.0 / (p_rrf_k + fts.r), 0)
    )::float as rrf_score
  from candidates c
    join document_chunks dc on dc.id = c.id
    left join vec on vec.id = dc.id
    left join fts on fts.id = dc.id
  -- RRF ties are common by construction (a vector-only and an FTS-only candidate
  -- at the same channel rank score identically). Break ties by cosine similarity,
  -- then by id, so top-5 membership and the benchmark's published ranks are stable.
  order by rrf_score desc, similarity desc nulls last, dc.chunk_index, dc.id
  limit p_final_limit;
$$;
