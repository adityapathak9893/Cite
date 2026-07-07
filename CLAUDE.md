# CLAUDE.md — Weaverbit Cite

## Project Overview

**Product:** Weaverbit Cite — an AI-powered document Q&A platform (embeddable chat widget planned, Phase 6).
**What it does:** Businesses upload their documents. Their teams (or customers) chat with an AI about them in one of two per-KB chat modes, with source citations:
- **strict** — answers come ONLY from the documents; zero retrieval gets a canned fallback message.
- **research** — document-anchored: the main answer is grounded ONLY in the documents, and domain knowledge beyond them appears in a clearly labeled, visually fenced "Domain context" block. Governed by a behavioral contract (see Prompt Assembly).
**Domain:** cite.weaverbit.com
**Owner:** Aditya (Weaverbit LLC)

## Architecture

### Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React 19 + TypeScript + Vite 7 | Owner's core expertise (9 years React) |
| Styling | Tailwind CSS v4 + shadcn/ui | Fast, consistent, professional UI |
| Backend | FastAPI (Python 3.13) | Industry standard for AI backends |
| Database | Supabase (PostgreSQL) | Auth + DB + Storage in one service |
| Vector Store | Supabase pgvector extension | Vectors in same DB, no extra service |
| Embeddings | OpenAI text-embedding-3-small (1536 dims) | Industry standard, cheap, fast |
| AI Chat | Anthropic Claude API (claude-sonnet-4-5-20250929) | High quality, streaming support |
| Auth | Supabase Auth (email/password + Google OAuth) | Built-in, no custom auth needed |
| File Storage | Supabase Storage | Same platform, simple integration |
| Frontend Deploy | Vercel | Best for React/Vite, free tier |
| Backend Deploy | Railway | Best for Docker/FastAPI, cheap |
| CI/CD | GitHub Actions (planned) | Lint + test + deploy on push to main |

### Monorepo Structure

```
cite/
├── CLAUDE.md                  (this file)
├── README.md
├── UX.md                     (design system spec)
│
├── frontend/
│   ├── index.html             (fonts, theme init script, OG tags)
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts         (React + Tailwind CSS v4 plugin)
│   ├── eslint.config.js
│   ├── tailwind.config.ts     (exists but NOT used — Tailwind v4 uses CSS @theme)
│   ├── components.json        (shadcn/ui config — new-york style)
│   ├── .env.example           (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL)
│   └── src/
│       ├── main.tsx
│       ├── App.tsx            (BrowserRouter + lazy-loaded routes)
│       ├── lib/
│       │   ├── supabase.ts    (Supabase client init)
│       │   ├── api.ts         (fetch-based API client with auth headers)
│       │   └── utils.ts       (cn() helper — clsx + tailwind-merge)
│       ├── hooks/
│       │   ├── useAuth.ts     (login, signup, logout, session)
│       │   ├── useKnowledgeBases.ts
│       │   ├── useDocuments.ts (polling while processing)
│       │   └── useChat.ts     (streaming SSE, conversations, messages)
│       ├── components/
│       │   ├── ui/            (shadcn/ui — button, input, textarea, label, card, dialog, theme-toggle, sonner)
│       │   ├── layout/
│       │   │   ├── AppLayout.tsx      (sidebar + main content outlet)
│       │   │   ├── Sidebar.tsx        (logo, nav, theme toggle, user area, mobile hamburger)
│       │   │   └── Header.tsx
│       │   ├── auth/
│       │   │   ├── LoginForm.tsx
│       │   │   ├── SignupForm.tsx
│       │   │   └── ProtectedRoute.tsx
│       │   ├── dashboard/
│       │   │   ├── KnowledgeBaseList.tsx  (grid + skeleton loading)
│       │   │   ├── KnowledgeBaseCard.tsx  (card + delete confirmation)
│       │   │   └── CreateKBDialog.tsx
│       │   ├── documents/
│       │   │   ├── DocumentUpload.tsx  (drag-and-drop upload area)
│       │   │   └── DocumentList.tsx    (list with status badges, delete, inline items)
│       │   └── chat/
│       │       ├── ChatWindow.tsx      (main chat container + conversation selector)
│       │       ├── MessageBubble.tsx   (user vs assistant styling + Markdown rendering)
│       │       ├── SourceCitation.tsx  (clickable source references)
│       │       ├── DomainContextPanel.tsx (fenced research-mode domain knowledge panel)
│       │       ├── ChatInput.tsx       (auto-height textarea + send button)
│       │       ├── StreamingIndicator.tsx (3-dot pulsing animation)
│       │       └── SuggestionChips.tsx (KB suggested_questions, hardcoded fallback on null)
│       ├── pages/
│       │   ├── Landing.tsx            (full marketing page — hero, features, how-it-works, CTA, footer)
│       │   ├── Login.tsx
│       │   ├── Signup.tsx
│       │   ├── Dashboard.tsx
│       │   └── KnowledgeBase.tsx      (single KB view — documents + chat, mobile tabs)
│       ├── styles/
│       │   ├── globals.css            (Tailwind v4 @theme, light/dark CSS variables, base resets)
│       │   ├── fonts.css              (General Sans @font-face from Fontshare)
│       │   └── animations.css         (keyframes for cursor-blink, dot-pulse, etc.)
│       └── types/
│           └── index.ts               (TypeScript interfaces for all entities)
│
├── backend/
│   ├── Dockerfile             (Python 3.13-slim)
│   ├── requirements.txt
│   ├── .env.example           (SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            (FastAPI app, CORS, lifespan, middleware)
│   │   ├── config.py          (pydantic Settings, env var loading, logging setup)
│   │   ├── dependencies.py    (get_current_user, get_supabase, AppException handler)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── health.py      (GET /health — basic health check)
│   │   │   ├── knowledge_bases.py  (CRUD for knowledge bases)
│   │   │   ├── documents.py   (upload, validate, process in background)
│   │   │   └── chat.py        (RAG query + streaming response + conversations)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── chunking.py    (markdown-first + verbatim-marker document chunking)
│   │   │   ├── embedding.py   (OpenAI embedding API calls via httpx)
│   │   │   ├── extraction.py  (PDF/TXT/MD text extraction)
│   │   │   ├── rag.py         (vector search + overview detection + context assembly)
│   │   │   ├── kb_profile.py  (KB domain profile + suggested questions generation)
│   │   │   └── claude.py      (Claude API streaming + mode-conditional prompts + SOURCES/DOMAIN_CONTEXT parsing)
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schemas.py     (Pydantic request/response models)
│   ├── migrations/
│   │   ├── 001_research_mode.sql  (domain_profile, suggested_questions, chat_mode, domain_context)
│   │   └── 002_hybrid_search.sql  (language col, generated fts tsvector + GIN, match_chunks_hybrid RPC)
│   └── tests/
│       ├── __init__.py
│       ├── test_health.py
│       ├── test_research_mode.py  (DOMAIN_CONTEXT parser + prompt builder unit tests)
│       ├── test_chunking.py       (markdown splitting + marker location unit tests)
│       ├── test_rag.py            (overview / coverage-question detection unit tests)
│       ├── test_eval_checks.py    (run_eval.check_case posture-D scoping unit tests)
│       └── eval/
│           ├── run_eval.py                  (eval runner — not pytest-collected)
│           ├── cite_eval_set_v1.json        (27-case eval set)
│           ├── run_retrieval_benchmark.py   (retrieval-only benchmark runner — not pytest-collected)
│           └── retrieval_benchmark.json     (hybrid-search retrieval benchmark: query → expected section)
│
│── (PLANNED — Not yet created) ──
│
├── .github/                   (Phase 5 — CI/CD workflows)
│   └── workflows/
│       ├── frontend.yml
│       └── backend.yml
│
└── widget/                    (Phase 6 — embeddable widget source)
    ├── widget.ts
    ├── widget.css
    └── build.sh
```

## Database Schema

### Supabase SQL (run in SQL Editor during setup)

```sql
-- Enable pgvector
create extension if not exists vector;

-- Knowledge bases
-- (domain_profile, suggested_questions, chat_mode were added by migration 001;
--  language was added by backend/migrations/002_hybrid_search.sql; all included
--  here for fresh setups)
create table knowledge_bases (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  name text not null,
  description text,
  is_public boolean default false,
  domain_profile text,                -- AI-generated 2-4 sentence corpus domain description
  suggested_questions jsonb,          -- AI-generated array of corpus-specific question strings
  language text not null default 'english',  -- FTS text-search config (migration 002)
  chat_mode text not null default 'research'
    check (chat_mode in ('strict', 'research')),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Row Level Security
alter table knowledge_bases enable row level security;
create policy "Users can CRUD their own KBs"
  on knowledge_bases for all
  using (auth.uid() = user_id);

-- Documents
create table documents (
  id uuid default gen_random_uuid() primary key,
  knowledge_base_id uuid references knowledge_bases(id) on delete cascade not null,
  user_id uuid references auth.users(id) on delete cascade not null,
  file_name text not null,
  file_path text not null,
  file_size integer,
  mime_type text,
  status text default 'uploading' check (status in ('uploading', 'processing', 'ready', 'failed')),
  error_message text,
  chunk_count integer default 0,
  created_at timestamptz default now()
);

alter table documents enable row level security;
create policy "Users can CRUD their own documents"
  on documents for all
  using (auth.uid() = user_id);

-- Document chunks with vector embeddings
create table document_chunks (
  id uuid default gen_random_uuid() primary key,
  document_id uuid references documents(id) on delete cascade not null,
  knowledge_base_id uuid references knowledge_bases(id) on delete cascade not null,
  content text not null,
  embedding vector(1536),
  chunk_index integer not null,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

-- CRITICAL: Vector similarity search index
create index on document_chunks
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- Hybrid search (backend/migrations/002_hybrid_search.sql; included here for fresh setups):
-- a generated tsvector over title + content + search_description, plus a GIN index.
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
create index if not exists document_chunks_fts_idx on document_chunks using gin (fts);

-- No RLS on chunks — accessed through backend service role only

-- Conversations
create table conversations (
  id uuid default gen_random_uuid() primary key,
  knowledge_base_id uuid references knowledge_bases(id) on delete cascade not null,
  user_id uuid references auth.users(id) on delete set null,
  title text,
  is_widget boolean default false,
  share_token uuid default gen_random_uuid(),
  created_at timestamptz default now()
);

alter table conversations enable row level security;
create policy "Users can CRUD their own conversations"
  on conversations for all
  using (auth.uid() = user_id);
create policy "Public conversations via share token"
  on conversations for select
  using (is_widget = true);

-- Messages
-- (domain_context was added by backend/migrations/001_research_mode.sql)
create table messages (
  id uuid default gen_random_uuid() primary key,
  conversation_id uuid references conversations(id) on delete cascade not null,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  sources jsonb default '[]'::jsonb,
  domain_context text,                -- research mode: parsed DOMAIN_CONTEXT block (null otherwise)
  created_at timestamptz default now()
);

alter table messages enable row level security;
create policy "Users can access messages in their conversations"
  on messages for all
  using (
    conversation_id in (
      select id from conversations where user_id = auth.uid()
    )
  );
create policy "Widget messages are public"
  on messages for select
  using (
    conversation_id in (
      select id from conversations where is_widget = true
    )
  );

-- Function for vector similarity search.
-- NOTE: live retrieval now uses match_chunks_hybrid (vector + FTS, RRF-fused) from
-- backend/migrations/002_hybrid_search.sql. This match_chunks RPC is retained
-- untouched as the rollback path — see that migration for the hybrid RPC body.
create or replace function match_chunks(
  query_embedding vector(1536),
  target_kb_id uuid,
  match_count int default 5,
  match_threshold float default 0.7
)
returns table (
  id uuid,
  document_id uuid,
  content text,
  metadata jsonb,
  similarity float
)
language sql stable
as $$
  select
    document_chunks.id,
    document_chunks.document_id,
    document_chunks.content,
    document_chunks.metadata,
    1 - (document_chunks.embedding <=> query_embedding) as similarity
  from document_chunks
  where document_chunks.knowledge_base_id = target_kb_id
    and 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
  order by document_chunks.embedding <=> query_embedding
  limit match_count;
$$;
```

## API Routes

### Backend Endpoints

```
GET    /health                          → Health check

# Knowledge Bases (requires auth)
GET    /api/v1/knowledge-bases          → List user's KBs
POST   /api/v1/knowledge-bases          → Create KB
GET    /api/v1/knowledge-bases/{id}     → Get single KB
PUT    /api/v1/knowledge-bases/{id}     → Update KB
DELETE /api/v1/knowledge-bases/{id}     → Delete KB

# Documents (requires auth)
POST   /api/v1/knowledge-bases/{kb_id}/documents          → Upload document
GET    /api/v1/knowledge-bases/{kb_id}/documents           → List documents
GET    /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}  → Get document status
DELETE /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}  → Delete document

# Chat (requires auth)
POST   /api/v1/knowledge-bases/{kb_id}/chat                → Send message, get streaming response
GET    /api/v1/knowledge-bases/{kb_id}/conversations        → List conversations
GET    /api/v1/conversations/{conv_id}/messages             → Get messages in conversation

# Widget (Phase 6 — NOT YET IMPLEMENTED)
# POST   /api/v1/widget/{kb_id}/chat     → Public chat endpoint for embedded widget
```

### Auth Flow

1. Frontend uses Supabase Auth SDK for login/signup (email + Google OAuth)
2. Supabase returns a JWT access token
3. Frontend sends this JWT in `Authorization: Bearer <token>` header to FastAPI
4. FastAPI verifies the JWT by calling Supabase's `auth.getUser(token)` using the service role key
5. If valid, extracts `user_id` and passes to route handlers via dependency injection

## RAG Pipeline Details

### Chunking Strategy

```
3-step chunking pipeline during document processing (chunking.py).
Root principle: never ask an LLM for character positions (LLMs cannot count
characters — position-based chunking caused mid-word seams in production);
ask it for verbatim text that code can locate.

Step 1 — Section Detection (identify_sections):

  Markdown documents (deterministic, runs first — NO AI boundary call):
  - If the text contains 3+ lines matching ^##\s, sections are split in code
    at those heading lines. Each section = its heading line through the
    character before the next heading; content before the first heading
    becomes a "Preamble" section. Section titles come from the heading text.
  - 200-3000 char size constraints: undersized sections merge into their
    neighbor; oversized sections split at paragraph breaks (\n\n) — cuts
    only ever land on a paragraph break, never mid-word.

  Unstructured documents (AI section detection with verbatim start-markers):
  - Claude returns, per section, a title + start_marker: the exact verbatim
    first 8-12 words of the section, copied character-for-character. The
    model is NEVER asked for character positions.
  - Python locates each boundary with text.find(start_marker, search_from),
    where search_from advances past each located marker — sequential search
    prevents duplicate-text false matches. Each section runs from its marker
    to the next located marker; the last runs to end of text (or the 30k cutoff).
  - Marker failure handling: unfound marker → warning logged with the marker
    text, boundary skipped, span absorbed by the previous section. More than
    one-third of markers failing → AI sectioning abandoned for the document,
    fixed-size fallback chunker used (with a log entry).
  - For docs > 30,000 chars: section detection covers the first 30k, heuristic
    splits the rest (double-newlines and heading patterns, keeps API costs low)
  - Falls back to fixed-size chunking (2000 chars, 200 overlap) if AI fails

Step 2 — Document Summary (generate_summary) — unchanged:
- Claude generates a 150-200 word overview from section titles + previews
- Stored as chunk_index 0 with metadata: {"is_summary": true, "title": "Document Overview"}
- Answers meta-questions like "What is this document about?"
- Fallback: concatenates section titles

Step 3 — Search Descriptions (generate_chunk_descriptions) — unchanged:
- Single Claude call generates keyword-rich one-line descriptions per section
- Stored in metadata: {"search_description": "anti-bribery FCPA corruption gift policy"}
- Used to improve embedding quality (see Embedding section below)
- Fallback: uses section titles

Steps 2-3 run identically on code-derived (markdown) and AI-derived sections.

Each chunk stores:
  content, chunk_index, metadata {title, is_summary, search_description, file_name}
```

### KB Domain Profile + Suggested Questions (kb_profile.py)

```
After every successful document processing AND on document deletion,
regenerate_kb_profile runs (background task, mirrors process_document):
- One Claude call receives the chunk-0 summaries of ALL documents in the KB
- Returns JSON: {"domain_profile": "2-4 sentences on what the corpus concerns,
  its field, adjacent in-domain topics", "suggested_questions": [4-6 strings]}
- Suggested questions must be corpus-specific (reference real names/terms/metrics
  from the summaries) — never generic templates like "Summarize the key points"
- Both fields stored on the knowledge_bases row
- Deleting the last document clears both fields (don't describe an empty KB)
- Failure handling mirrors the AI-chunking fallback philosophy: log a warning,
  keep previous values, never fail the upload
- domain_profile feeds the research-mode prompt; suggested_questions feed the
  frontend suggestion chips
```

### Embedding

```
- Model: text-embedding-3-small
- Dimensions: 1536
- Batch size: 100 chunks per API call (OpenAI supports batching)
- Cost: ~$0.02 per million tokens (negligible)
- IMPORTANT: Embeddings are generated from COMBINED text:
  "{search_description}\n\n{content}"
  This captures both keyword descriptions and full content in the vector.
  The content field in document_chunks stores the ORIGINAL section text only.
```

### Retrieval

```
Overview Question Detection (rag.py — is_overview_question):
- 25+ keyword patterns detect summary/overview questions
  ("what is this about?", "summarize", "tell me what I need to know", "walk me through", etc.)
- Overview questions trigger document structure fetch in addition to hybrid retrieval

Document Structure Fetch (rag.py — get_document_structure):
- For overview questions only: queries document_chunks table for the KB
- Extracts the summary chunk (metadata.is_summary = true) and all section titles
- Returns {summary: "...", sections: [{index, title}, ...]}

Hybrid Retrieval (rag.py — search_similar_chunks → match_chunks_hybrid RPC, migration 002):
- Embed the user question (same model), then one RPC runs two channels and fuses them:
  - Vector channel: top-20 candidates above cosine-similarity floor 0.3
  - FTS channel: Postgres full-text search over a generated tsvector column (title +
    content + search_description), top-10 by ts_rank. OR-of-stems matching (not
    websearch AND) so "schedule a weekly vulnerability scan" still finds the "Scan
    Scheduling" section even though that section never contains the word "vulnerability"
  - Fuse with Reciprocal Rank Fusion (k=60); return the top-5 fused chunks in RRF order
- The RPC returns chunk_index + metadata + per-channel ranks + rrf_score; rag.py enriches
  only file_name and preserves the fused order (no re-sort by similarity)
- Per-KB knowledge_bases.language (default 'english') applies to the FTS query side; the
  doc-side generated tsvector is fixed at 'english' (known limitation: non-English KBs
  degrade to vector-only). The old vector-only 0.5/0.3 two-step was removed
- The base match_chunks RPC is retained untouched as the rollback path (revert rag.py
  call sites; no schema change needed)

Context Assembly (rag.py — build_context):
- Labels chunks as "Document Knowledge" (not "Excerpts") so Claude treats content
  as internalized knowledge rather than text to parrot back
- For OVERVIEW questions: Document Structure + Document Summary + Document Knowledge
- For SPECIFIC questions: Document Knowledge only
- Each chunk labeled: [Section {chunk_index}] {filename} — "{title}"

No-Chunks Handling (zero retrieval — mode-dependent):
- Zero retrieval now means BOTH the vector AND the FTS channel came back empty
- Overview questions ALWAYS go to Claude (even with zero retrieval) because
  they have document structure context
- STRICT mode: specific questions with zero retrieval get the fixed canned
  fallback message ("I wasn't able to find any relevant sections...") WITHOUT
  calling Claude
- RESEARCH mode: zero-retrieval messages always go to Claude with the behavioral
  contract, conversation history, and a context block stating "No document content
  was retrieved for this message." The contract's postures C/D/E handle
  conversational, off-topic, and frustrated messages; its zero-retrieval Hard Rule
  requires the main answer to be at most two sentences, with all substance in the
  domain block. The canned string must never appear in research mode
```

### Prompt Assembly

```
System prompt (claude.py — build_system_prompt) is MODE-CONDITIONAL on
knowledge_bases.chat_mode:

STRICT mode — original conversational expert persona, byte-for-byte unchanged:
- "You have thoroughly read and understood all the documents in this knowledge
  base. You are a knowledgeable, helpful expert."
- Instructs Claude to synthesize, explain, and educate — not just quote text
- For overview questions: cover all major topics comprehensively
- For specific questions: give thorough answers with context and implications
- No inline citations: Claude must NOT use [Source: ...] in the response text
- Graceful no-answer: "The documents don't appear to cover that topic..." instead
  of robotic "I don't have enough information in the uploaded documents"

RESEARCH mode — the Behavioral Contract (claude.py — RESEARCH_CONTRACT_TEMPLATE):
- Five postures: A document questions / B domain questions / C conversational
  moments / D off-topic substance / E frustration and complaints
- Boundary rules: anchor (history never makes off-topic on-topic), tiebreak
  (B-vs-D ambiguity → brief B), competitor (never evaluate competing products),
  no-man's-land (no retrieval + no domain relevance + not conversational = D)
- Output format: main answer (grounded ONLY in retrieved content) → optional
  ---DOMAIN_CONTEXT--- block → optional ---SOURCES--- block; postures C/D/E
  produce NO blocks
- Hard Rules, including the zero-retrieval rule: when no document content was
  retrieved, the main answer is at most two sentences — everything else goes
  in the domain block or is omitted
- Interpolates {kb_name}, {domain_profile} (DOMAIN_PROFILE_FALLBACK when the KB
  has no profile yet), and {tone} (hardcoded RESEARCH_TONE)
- The full contract text lives in backend/app/services/claude.py
  (RESEARCH_CONTRACT_TEMPLATE); its source spec is cite_research_mode_brief.md
  Appendix 1. Do NOT paraphrase or duplicate it here

Source Attribution (end-of-response SOURCES block):
- Claude outputs a machine-parseable block at the end of every response:
  ---SOURCES---
  [1] filename.pdf | Section 5 | "Section Title Here"
  [2] filename.pdf | Section 2 | "Another Title"
  ---END_SOURCES---
- Backend parses this block (claude.py — parse_sources_from_response)
- Parsed sources are matched against original chunks for document_id, similarity
- Clean text (SOURCES block stripped) is saved to the messages table
- Frontend strips SOURCES block during streaming and from saved messages

Domain Context (research-mode DOMAIN_CONTEXT block):
- Research-mode output order: main answer → optional ---DOMAIN_CONTEXT--- ...
  ---END_DOMAIN_CONTEXT--- → optional ---SOURCES--- block (unchanged format)
- Backend parses it (claude.py — parse_domain_context_from_response, mirrors the
  SOURCES parser) AFTER stripping the SOURCES block; the block is stripped from
  the saved message text and stored in messages.domain_context
- Robustness: missing end delimiter → remainder treated as the block + warning;
  block emitted in strict mode → stripped and discarded with a warning;
  empty block → treated as absent
- Delivered to the client in the final SSE event alongside sources
- Frontend renders it (DomainContextPanel — "Domain context — beyond your
  documents") as a visually fenced panel below the main answer and above the
  citation chips, after streaming completes

Context (injected after system prompt):
"Knowledge base: {kb_name}

--- Document Structure ---          (overview questions only)
This document contains the following sections:
  1. Section Title
  2. Another Section
--- End Document Structure ---

--- Document Summary ---            (overview questions only)
{AI-generated 150-200 word summary}
--- End Document Summary ---

--- Document Knowledge ---
The following sections from the knowledge base are relevant:

[Section {chunk_index}] {filename} — "{title}"
{chunk_content}

[Section {chunk_index}] {filename} — "{title}"
{chunk_content}
--- End Document Knowledge ---"

User message:
"{user's question}"
```

### Streaming

```
- Use Anthropic Python SDK with streaming
- FastAPI StreamingResponse with text/event-stream content type
- Frontend uses fetch with ReadableStream
- Each streamed chunk is sent as SSE: data: {"token": "...", "done": false}
- Claude's response includes the optional ---DOMAIN_CONTEXT--- block (research mode)
  followed by the ---SOURCES--- block at the end (both streamed as normal tokens)
- Backend parses both blocks after stream completes, returns clean text + parsed
  sources + domain_context
- Final SSE event: data: {"token": "", "done": true, "sources": [...],
  "domain_context": "..." | null, "full_response": "..."}
  (full_response is clean text with BOTH blocks stripped — this is what gets saved to DB)
- Frontend strips both blocks from display during streaming (handles partial markers)
- Frontend also strips SOURCES block from cached content before adding to query cache
- Citation chips rendered from parsed sources (not from raw chunks) — only shows what Claude cited
```

## Coding Conventions

### Python (Backend)

- Python 3.13+
- Use type hints on ALL function signatures
- Pydantic models for ALL request/response schemas
- Async functions for all route handlers and service calls
- Use `httpx` for async HTTP calls (not requests)
- Use `python-multipart` for file uploads
- Error handling: raise HTTPException with meaningful status codes and messages
- Logging: use Python `logging` module, structured JSON logs
- Environment variables via pydantic `BaseSettings` in config.py
- NEVER hardcode API keys, URLs, or secrets

### TypeScript (Frontend)

- Strict TypeScript — no `any` types
- Functional components only — no class components
- Custom hooks for all data fetching and state logic
- All API entities defined as TypeScript interfaces in `types/index.ts`
- Use TanStack Query (React Query) for server state management
- Use Zustand for minimal client state if needed
- **Tailwind CSS v4** for all styling — config via CSS `@theme inline` in `globals.css`, NOT `tailwind.config.ts`
- Dark mode uses `@custom-variant dark (&:is([data-theme="dark"] *))` — NOT `.dark` class
- Additional CSS files for Tailwind v4 bootstrap: `globals.css`, `fonts.css`, `animations.css`
- shadcn/ui (new-york style) for UI components — do not build custom buttons, inputs, cards, dialogs
- Responsive design — mobile-first approach
- Loading states and error states for EVERY async operation
- Lazy-loaded pages via `React.lazy()` + `Suspense` for code splitting
- Fetch-based API client (no axios) with AbortController for cancellation
- Sonner for toast notifications

### General

- All environment variables in .env files (never committed)
- .env.example files with placeholder values (always committed)
- No console.log in production code — use proper logging
- Meaningful variable and function names — no abbreviations
- Comments only when WHY is not obvious from the code

## Security Rules (Non-Negotiable)

### Frontend (PUBLIC — assume attackers can read every line)
- NEVER store API keys, secrets, or service role keys in frontend code
- ONLY two env vars allowed in frontend: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY (these are PUBLIC by design)
- ALL business logic runs on the backend — frontend is a thin UI layer
- Frontend NEVER talks to OpenAI or Anthropic directly — always through backend
- Frontend NEVER uses the Supabase service role key — only the anon key with RLS
- No sensitive data in localStorage except the Supabase auth token (handled by Supabase SDK automatically)
- All API calls from frontend go to YOUR backend (FastAPI), which then talks to third-party services
- NEVER expose internal IDs, database structure, or error internals to the browser console

### Backend (PRIVATE — runs on your server)
- All secrets loaded from environment variables via pydantic BaseSettings — NEVER hardcoded
- Supabase service role key stays on backend ONLY
- OpenAI API key stays on backend ONLY
- Anthropic API key stays on backend ONLY
- All user input is validated with Pydantic models before processing
- All file uploads are validated: check mime type, file size, file extension on backend (don't trust frontend validation)
- Rate limiting on all public endpoints (especially the widget chat endpoint)
- CORS restricted to specific origins — not wildcard * (except widget endpoint which needs broader access)
- SQL injection prevention: NEVER construct SQL strings manually — always use parameterized queries or Supabase client methods
- JWT verification on EVERY protected endpoint — no exceptions

### Data Flow (How it works securely)
```
1. User logs in → Supabase Auth gives them a JWT (frontend)
2. User uploads a doc → Frontend sends file + JWT to FastAPI backend
3. Backend verifies JWT with Supabase → extracts user_id
4. Backend validates file (size, type, extension, user limits)
5. Backend processes file → calls OpenAI for embeddings → stores in Supabase
6. User asks a question → Frontend sends question + JWT to FastAPI backend
7. Backend verifies JWT → does vector search → calls Claude API → streams response back
8. Frontend NEVER touches OpenAI or Claude directly
```

### .env Files
- .env files are NEVER committed to git — added to .gitignore on first commit
- .env.example files (with placeholder values only) ARE committed — so other devs know what's needed
- Production secrets are set as environment variables in Railway/Vercel dashboards — never in files

## Error Handling Standards

### Backend Error Response Format
ALL error responses follow this exact structure — no exceptions:
```json
{
  "error": {
    "code": "DOCUMENT_TOO_LARGE",
    "message": "File size exceeds the 50MB limit.",
    "status": 413
  }
}
```

### Backend Error Rules
- NEVER return raw Python tracebacks to the frontend — always wrap in clean HTTPException
- Use specific error codes that the frontend can programmatically handle:
  - `AUTH_TOKEN_MISSING` (401) — No Authorization header
  - `AUTH_TOKEN_INVALID` (401) — JWT verification failed
  - `AUTH_TOKEN_EXPIRED` (401) — JWT has expired
  - `FORBIDDEN` (403) — User doesn't own this resource
  - `RESOURCE_NOT_FOUND` (404) — KB, document, or conversation not found
  - `VALIDATION_ERROR` (422) — Request body/params failed Pydantic validation
  - `FILE_TOO_LARGE` (413) — Exceeds 50MB
  - `FILE_TYPE_NOT_ALLOWED` (415) — Invalid mime type or extension
  - `KB_LIMIT_REACHED` (429) — Max 10 knowledge bases
  - `DOCUMENT_LIMIT_REACHED` (429) — Max 50 documents per KB
  - `RATE_LIMITED` (429) — Too many requests (widget endpoint)
  - `PROCESSING_FAILED` (500) — Document chunking/embedding failed
  - `AI_SERVICE_ERROR` (502) — OpenAI or Claude API call failed
  - `INTERNAL_ERROR` (500) — Unexpected server error
- Log full error details (with traceback) to server logs — but send only the safe error object to client
- All external API calls (OpenAI, Claude, Supabase) wrapped in try/except with proper fallback messages
- Include a `request_id` (UUID) in every error response for debugging — log the same ID server-side

### Frontend Error Handling Rules
- NEVER show raw error objects, stack traces, or API response bodies to users
- Every API call has exactly three states handled: loading, success, error — no exceptions
- Error handling by status code:
  - `401` → Clear auth state, redirect to login page automatically
  - `403` → Toast: "You don't have permission to access this resource."
  - `404` → Toast: "This resource doesn't exist." or dedicated 404 page
  - `413` → Toast: "This file is too large. Maximum size is 50MB."
  - `415` → Toast: "This file type is not supported. Please upload PDF, TXT, or MD files."
  - `422` → Show inline validation errors next to the relevant form fields
  - `429` → Toast: "Too many requests. Please wait a moment and try again."
  - `500/502` → Toast: "Something went wrong on our end. Please try again."
  - Network error / timeout → Toast: "Unable to connect. Please check your internet and try again."
- Timeout configuration:
  - Regular API calls: 30 seconds
  - Document upload + processing: 120 seconds
  - Chat streaming: 60 seconds for first token, then keep alive
- NEVER swallow errors silently — always show feedback to the user

## Git Workflow

### Branch Strategy
- Main branch: `master` — always deployable, protected
- Development branches named by phase: `phase-1/auth-skeleton`, `phase-2/kb-crud`, etc.
- Feature branches off phase branches if needed: `phase-3/fix-upload-validation`
- Merge to master only when a phase is complete and tested

### Commit Messages (Conventional Commits)
```
feat: add document upload endpoint
fix: handle empty PDF extraction gracefully
chore: update dependencies
style: apply UX.md color tokens to sidebar
refactor: extract auth middleware into dependency
docs: update README with setup instructions
test: add health check endpoint test
```

### .gitignore (Required from first commit)
```gitignore
# Dependencies
node_modules/
__pycache__/
*.pyc
venv/
.venv/
.npm-global/

# Environment variables — NEVER commit these
.env
.env.local
.env.development
.env.production
.env.*.local

# Build outputs
dist/
build/
.next/
*.egg-info/

# IDE and editor files
.vscode/settings.json
.vscode/launch.json
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
Thumbs.db
ehthumbs.db
Desktop.ini

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Test coverage
coverage/
htmlcov/
.pytest_cache/

# Secrets file (your local reference)
secrets.txt
```

## Testing Strategy

### What to test (Phase 1 onward)
- Backend: Health check endpoint returns 200
- Backend: Auth middleware rejects requests without JWT (returns 401)
- Backend: Auth middleware rejects invalid/expired JWTs (returns 401)
- Backend: Auth middleware extracts correct user_id from valid JWT
- Backend: CORS headers are set correctly for allowed origins
- Backend: Protected endpoints return 401 without auth, not 500
- Backend: Error responses match the standard format defined above
- Backend: DOMAIN_CONTEXT parser — present / absent / missing end delimiter /
  strict-mode discard (tests/test_research_mode.py)
- Backend: prompt builder — mode switching, null-profile fallback, strict prompt
  unchanged (tests/test_research_mode.py)
- Backend: chunking — markdown splitting at headings, 200/3000 merge/split
  constraints, sequential marker location with duplicate text, unfindable-marker
  absorption, >1/3-failure fallback (tests/test_chunking.py)

### Eval harness (backend/tests/eval/)
- `run_eval.py` — a script, NOT pytest-collected. Loads the 27-case
  `cite_eval_set_v1.json`, authenticates with env-provided credentials, sends each
  case's question to the chat endpoint of an env-provided research-mode KB (fresh
  conversation per case; the drift case sends its messages sequentially in ONE
  conversation), and captures full responses
- Automated structural checks per case:
  - sources presence/absence matches `should_have_sources`
  - domain-block presence/absence matches `should_have_domain_block`
  - the canned zero-retrieval fallback string never appears
  - human-posture length (expected posture C/D/E → response under ~600 chars)
  - competitor rule (bait-05: no evaluative content near a competitor mention;
    any mention flags manual review)
  - drift final turn must be posture D — no sources, no domain block (only for cases
    with final_posture=D, e.g. drift-01; multi-turn cases ending in a clarification
    such as followup-01 are exempt and carried by manual grading)
  - zero-source brevity (posture B: zero-source main answer under ~350 chars)
  - zero-source non-attribution (no "the documents show/state/describe" in any
    zero-source turn)
- Writes timestamped reports: `eval_results_<timestamp>.json` (machine-readable)
  + `eval_report_<timestamp>.md` (human-readable)
- Posture *quality* is graded manually from the markdown report;
  `judge_posture_quality()` is a clearly marked LLM-as-judge stub

### Known Limitations
- Zero-retrieval questions with high intrinsic interest may produce an overlong
  main answer; the Hard Rule reduces but does not eliminate this (observed in
  eval case bait-07 across multiple runs).
- No false attribution to documents has been observed across 4 eval runs.
- Vector-only retrieval missed keyword-exact sections (eval case grounded-02:
  "schedule" query failed to retrieve the Scan Scheduling section three times) —
  remediated by hybrid search (migration 002: pgvector + Postgres FTS fused with RRF),
  guarded by the retrieval benchmark (tests/eval/retrieval_benchmark.json).

### What NOT to spend time on now
- Unit tests for every utility function — only test critical paths
- E2E browser tests (Cypress/Playwright — overkill for a portfolio project)
- Load testing / stress testing
- Snapshot tests

### How to run tests
```bash
cd backend
python -m pytest tests/ -v
```

## Performance Guidelines

### Frontend
- Lazy load all route components — don't bundle everything into one JS file
  ```typescript
  const Dashboard = lazy(() => import('./pages/Dashboard'));
  const KnowledgeBase = lazy(() => import('./pages/KnowledgeBase'));
  ```
- Images: use WebP format, lazy loading with `loading="lazy"` attribute
- Fonts: preload the primary body font (General Sans) in `<head>`, use `font-display: swap`
- No unnecessary re-renders — use React.memo on expensive components, useMemo/useCallback where appropriate
- Chat messages: virtualize the message list if conversation exceeds 100 messages (react-window or @tanstack/react-virtual)
- Bundle size budget: < 200KB initial JS (gzipped) — check with `npx vite-bundle-visualizer`
- Debounce search inputs (300ms) — never fire API calls on every keystroke

### Backend
- Document processing (chunking + embedding) MUST be async — don't block the upload response
  - Upload endpoint returns immediately with `{ status: "processing", document_id: "..." }`
  - Processing happens in background (FastAPI BackgroundTasks)
  - Frontend polls status endpoint every 2 seconds
- Use connection pooling for Supabase (built into the Python client via httpx)
- Embedding API calls: batch chunks (up to 100 per call) — NEVER send one chunk at a time
- Chat streaming: first token should appear within 2 seconds of user sending message
- Database queries: always filter by knowledge_base_id AND user_id — never scan full tables
- Add database indexes from day one (already defined in schema for vector similarity search)

## File Upload Validation (Backend)

### Allowed Files
```
Mime types:
  - application/pdf
  - text/plain
  - text/markdown

Extensions:
  - .pdf, .txt, .md

Max file size: 50MB per file
Max files per knowledge base: 50
Max knowledge bases per user: 10
Max total storage per user: 500MB
```

### Validation Order (Every upload goes through ALL steps)
```
1. Check file size FIRST (reject before reading content — prevents memory abuse)
2. Check file extension against whitelist
3. Check mime type against whitelist (read file header bytes — don't trust Content-Type header)
4. Check user's knowledge base count hasn't exceeded limit (10)
5. Check this KB's document count hasn't exceeded limit (50)
6. Check user's total storage hasn't exceeded limit (500MB)
7. Only THEN proceed with upload to Supabase Storage
8. Only THEN start background processing (chunk + embed)
```

### Rejection Responses
- File too large → 413 with `FILE_TOO_LARGE`
- Wrong type → 415 with `FILE_TYPE_NOT_ALLOWED`
- Limits hit → 429 with `KB_LIMIT_REACHED` or `DOCUMENT_LIMIT_REACHED`
- Each rejection includes a clear human-readable message explaining the limit

## Logging Standards

### Backend Logging
- Use Python's built-in `logging` module — no third-party logging libraries
- Logger per module: `logger = logging.getLogger(__name__)`
- Log format: `[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s`

### Log Levels
```
INFO:    Request received, document processing started/completed, user login/logout,
         KB created/deleted, chat message sent — normal business operations
WARNING: Rate limit approaching, slow API response (>5s), retry attempts,
         deprecated feature usage
ERROR:   Failed API calls (OpenAI, Claude, Supabase), processing failures,
         auth verification failures, unhandled exceptions
DEBUG:   Full request/response bodies, SQL queries, embedding vectors —
         development only, NEVER in production
```

### What to NEVER Log
- API keys or tokens (OpenAI, Anthropic, Supabase)
- User passwords or auth credentials
- Full JWT tokens (log only last 8 characters for debugging: `...abc12345`)
- File contents or document text
- Personal user data (email, name) — use user_id only
- Embedding vectors (they're huge and meaningless in logs)

### What to ALWAYS Log
- `user_id` performing the action
- `knowledge_base_id` and `document_id` being accessed
- Action performed (upload, process, query, delete)
- Duration of expensive operations (embedding calls, Claude calls, processing)
- Error codes and safe error messages (not stack traces in production)
- `request_id` for correlating logs across a single request lifecycle


## Build Phases

### Phase 1: Skeleton + Auth (Day 1-2)

**Backend:**
- Initialize FastAPI project with proper structure
- Set up config.py with all environment variables
- Create health check endpoint
- Implement Supabase JWT auth middleware/dependency
- Set up CORS for local dev (localhost:5173 → localhost:8000)
- Create Dockerfile
- Verify: `GET /health` returns 200, auth dependency rejects invalid tokens

**Frontend:**
- Initialize React + TypeScript + Vite project
- Install and configure Tailwind CSS + shadcn/ui
- Set up Supabase client
- Build Login and Signup pages with Supabase Auth
- Build ProtectedRoute component
- Build minimal AppLayout with sidebar placeholder
- Set up React Router with routes: / (landing), /login, /signup, /dashboard (protected)
- Verify: User can sign up, log in, see protected dashboard page, log out

**Integration test:**
- Frontend sends authenticated request to backend
- Backend verifies JWT and returns user info
- Full auth flow works end-to-end

### Phase 2: Knowledge Base CRUD (Day 3-4)

**Backend:**
- CRUD routes for knowledge_bases table
- Pydantic schemas for KB create/update/response
- All routes require authenticated user
- Users can only access their own KBs (enforced in queries AND by RLS)

**Frontend:**
- Dashboard page shows list of user's knowledge bases as cards
- "Create Knowledge Base" dialog (name + description)
- Each KB card shows name, description, document count, created date
- Click KB card → navigates to single KB view page
- Delete KB with confirmation dialog

### Phase 3: Document Upload + Processing (Day 4-6)

**Backend:**
- Upload endpoint: receives file, stores in Supabase Storage, creates document record with status "uploading"
- Processing pipeline (triggered after upload):
  1. Extract text (PyPDF2 for PDF, plain read for .txt/.md)
  2. Smart chunking: markdown docs (3+ ## headings) split deterministically in code;
     unstructured docs use AI section detection via verbatim start-markers →
     generate summary → generate search descriptions
     (falls back to fixed-size 2000-char chunks if AI sectioning fails)
  3. Generate embeddings via OpenAI API (combined search_description + content for each chunk)
  4. Store chunks + embeddings in document_chunks table (content stores original text, not combined)
  5. Update document status to "ready" (or "failed" with error_message)
  6. Regenerate the KB domain profile + suggested questions (kb_profile.py) from all
     documents' chunk-0 summaries; also triggered on document deletion. Failure is
     logged and previous values kept — never fails the upload
  - Note: up to 4 Claude API calls per document during processing (section detection —
    skipped for markdown docs, summary, descriptions, KB profile)
- Status endpoint: returns current document processing status
- Delete endpoint: removes document, chunks, and storage file

**Frontend:**
- KB detail page with two panels: Documents (left) + Chat (right, placeholder for now)
- Drag-and-drop upload area (accept .pdf, .txt, .md)
- Document list showing name, status badge (uploading/processing/ready/failed), chunk count
- Poll document status every 2 seconds while processing
- Delete document button

### Phase 4: RAG Chat — Intelligent Document Assistant (Day 6-8)

**Backend:**
- Chat endpoint: receives message + knowledge_base_id
  1. Create or continue conversation
  2. Embed the user's question
  3. Detect overview questions (is_overview_question) and fetch document structure if needed
  4. Call match_chunks() to find relevant document chunks
  5. Assemble context as "Document Knowledge" (overview gets structure + summary too)
  6. Stream Claude's response back via SSE (conversational expert persona)
  7. Parse ---SOURCES--- block from Claude's response to extract cited sections
  8. Save clean text (SOURCES stripped) + parsed sources to database
- Conversation history: include last 5 messages as context for follow-up questions
- Source matching: parsed sources matched against original chunks for document_id, similarity
- Overview questions always go to Claude (even with 0 vector results) — they have structure context

**Frontend:**
- Chat panel in KB detail page
- Message list with user and assistant bubbles
- Streaming text display (tokens appear in real-time)
- SOURCES block stripped during streaming (partial marker detection prevents flash)
- Citation chips at bottom of assistant messages show section title (not content preview)
- Fallback to content preview for old messages without title field
- Chat input with send button and Enter key support
- Conversation list in sidebar (within KB view)
- "New conversation" button
- Auto-scroll to bottom on new messages
- Loading indicator while waiting for first token

### Phase 5: Landing Page + Polish + Deploy (Day 9-10)

**Frontend (DONE):**
- ✅ Landing page implemented as single `pages/Landing.tsx`:
  - Hero with headline, subheadline, CTA buttons
  - "How it works" section (3 steps: Upload → Ask → Get cited answers)
  - Features section with alternating layout
  - Footer with logo + links
  - Scroll-triggered reveal animations via IntersectionObserver
  - Mobile-responsive with hamburger menu
- ✅ Toast notifications via Sonner
- ✅ Loading skeletons for KB list
- ⬜ Error boundaries and fallback UI (remaining polish)
- ⬜ Comprehensive responsive design audit (remaining polish)

**Deployment (DONE):**
- ✅ Frontend deployed to Vercel at cite.weaverbit.com
- ✅ Backend deployed to Railway
- ⬜ CI/CD via GitHub Actions (`.github/workflows/`) — not yet set up

### Research Mode (Phases A–F) — COMPLETE (June 2026)

Implemented per cite_research_mode_brief.md, eval-verified across four runs:

- **A — Migration:** `backend/migrations/001_research_mode.sql` (domain_profile,
  suggested_questions, chat_mode on knowledge_bases; domain_context on messages)
- **B — KB profile generation:** `kb_profile.py` — domain profile + corpus-specific
  suggested questions regenerated on every document processing/deletion
- **C — Backend chat:** mode-conditional system prompt (strict unchanged; research
  uses the behavioral contract), research-mode zero-retrieval path goes to Claude,
  DOMAIN_CONTEXT parsing/storage/SSE delivery
- **D — Frontend:** DomainContextPanel below answers, suggested-question chips from
  the KB row, extended TypeScript types
- **E — Eval harness:** `backend/tests/eval/run_eval.py` + 27-case set, plus parser
  and prompt-builder unit tests
- **F — Documentation sync:** this document and README.md updated to match reality

### Phase 6: Embeddable Widget (Day 11-13)

**Widget architecture:**
- Single JavaScript file (~15KB minified): `widget.js`
- Loaded via script tag with data attributes:
  ```html
  <script src="https://cite.weaverbit.com/widget.js"
          data-kb="kb-uuid-here"
          data-theme="light"
          data-position="bottom-right"
          data-title="Ask our docs">
  </script>
  ```
- Creates an iframe (for style isolation) with a floating chat button
- Click button → expands chat window
- Chat hits the public `/api/v1/widget/{kb_id}/chat` endpoint (no auth required)
- Rate limiting: 20 messages per hour per IP per KB (to prevent abuse)

**Backend addition:**
- Public widget chat endpoint (no auth)
- Rate limiting middleware for widget endpoint
- CORS configured to allow any origin (widget can be on any website)

**Frontend addition:**
- Widget Configurator page in dashboard (per KB)
- Shows embed code snippet user can copy
- Theme customization (light/dark, accent color)
- Preview of how widget looks

### Phase 7: Final Polish (Day 14)

- Test all flows end-to-end in production
- Fix any bugs found during testing
- Add README.md with project description, tech stack, setup instructions
- Screenshot the deployed product for Upwork portfolio
- Record a 2-minute demo video (Loom) for Upwork profile
- SHIP IT

## Environment Variables

### Frontend (.env)
```
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbG...
VITE_API_URL=http://localhost:8000  (production: https://api-cite.weaverbit.com)
```

### Backend (.env)
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbG...
SUPABASE_JWT_SECRET=your-jwt-secret
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
CORS_ORIGINS=http://localhost:5173,https://cite.weaverbit.com
ENVIRONMENT=development
```

## Commands

### Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev  # starts on localhost:5173
```

### Docker (Backend)
```bash
cd backend
docker build -t cite-backend .
docker run -p 8000:8000 --env-file .env cite-backend
```

## Important Notes

- NEVER use Supabase service key in frontend code — it has admin access
- ALWAYS use the anon key in frontend — it respects Row Level Security
- The widget endpoint will be PUBLIC (Phase 6, pending) — implement rate limiting before deploy
- Streaming responses use Server-Sent Events (SSE), not WebSockets
- For PDF extraction, use PyPDF2 (simple, reliable) — not heavy libraries like pdfplumber
- Document chunking: markdown docs (3+ ## headings) are split deterministically in code at heading boundaries; unstructured docs use AI section detection that returns verbatim start-markers located via sequential text.find — the model is never asked for character positions. Falls back to fixed-size chunking if AI sectioning fails or >1/3 of markers can't be located
- Embeddings are generated from combined text (search_description + content), but only original content is stored in document_chunks
- Existing documents must be deleted and re-uploaded to benefit from new chunking — old chunks are not auto-migrated
- The ivfflat index on embeddings requires at least ~100 rows to be effective. For small datasets during development, it still works but may not be as fast
- All dates are stored and returned in UTC (timestamptz)
- Chat is per-KB mode-conditional (knowledge_bases.chat_mode): 'strict' is the original document-only persona; 'research' (default for new KBs) uses the behavioral contract in claude.py — doc-grounded main answer plus an optional clearly-labeled domain-context block
- Chat uses an intelligent assistant persona — Claude synthesizes and explains, not just quotes. No inline citations; sources appear as chips below the response
- Claude outputs ---SOURCES--- block at end of response (research mode may precede it with a ---DOMAIN_CONTEXT--- block); backend parses both, strips both, saves clean text + domain_context to DB. Frontend also strips them during streaming as a safety net
- KB domain profile + suggested questions (kb_profile.py) regenerate on every document processing/deletion; suggestion chips read knowledge_bases.suggested_questions and fall back to the hardcoded set when null
- Overview questions ("what is this about?", "summarize", etc.) get document structure + summary context in addition to hybrid retrieval results, so Claude can give comprehensive overviews
- Citation chips show section title (from Claude's parsed sources) instead of content preview. Old messages without title fall back to content preview
- Sources shown to the user are only the sections Claude actually cited, not all retrieved chunks
- **Tailwind v4**: Config is in CSS (`globals.css` via `@theme inline`), NOT in `tailwind.config.ts`. The `tailwind.config.ts` file exists but is unused
- **Dark mode**: Uses `[data-theme="dark"]` attribute, NOT `.dark` class. Custom variant: `@custom-variant dark (&:is([data-theme="dark"] *))`
- **Fonts**: General Sans loaded via `@font-face` from Fontshare CDN in `fonts.css`; Instrument Serif + JetBrains Mono loaded via Google Fonts `<link>` in `index.html`
- **React version**: Actually React 19.2.0 (not React 18 as originally planned)
- **Conversation history**: Backend includes last 6 messages (not 5) as context for follow-up questions
- **Backend has no `supabase.py` service** — Supabase client is created directly in `dependencies.py`
- **Backend has no `widget.py` router yet** — widget endpoint is Phase 6 (pending)
- **Frontend has no separate `MessageList.tsx`, `DocumentItem.tsx`, or `ProcessingStatus.tsx`** — these are handled inline within `ChatWindow.tsx` and `DocumentList.tsx`
- **Landing page** is a single `pages/Landing.tsx` file, not split into `components/landing/` subcomponents
