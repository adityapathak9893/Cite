# CLAUDE.md — Weaverbit Cite

## Project Overview

**Product:** Weaverbit Cite — an AI-powered document Q&A platform with embeddable chat widget.
**What it does:** Businesses upload their documents. Their teams (or customers) chat with an AI that answers ONLY from those documents, with source citations.
**Domain:** cite.weaverbit.com
**Owner:** Aditya (Weaverbit LLC)

## Architecture

### Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React 18 + TypeScript + Vite | Owner's core expertise (9 years React) |
| Styling | Tailwind CSS + shadcn/ui | Fast, consistent, professional UI |
| Backend | FastAPI (Python 3.11+) | Industry standard for AI backends |
| Database | Supabase (PostgreSQL) | Auth + DB + Storage in one service |
| Vector Store | Supabase pgvector extension | Vectors in same DB, no extra service |
| Embeddings | OpenAI text-embedding-3-small (1536 dims) | Industry standard, cheap, fast |
| AI Chat | Anthropic Claude API (claude-sonnet-4-5-20250929) | High quality, streaming support |
| Auth | Supabase Auth (email/password + Google OAuth) | Built-in, no custom auth needed |
| File Storage | Supabase Storage | Same platform, simple integration |
| Frontend Deploy | Vercel | Best for React/Vite, free tier |
| Backend Deploy | Railway | Best for Docker/FastAPI, cheap |
| CI/CD | GitHub Actions | Lint + test + deploy on push to main |

### Monorepo Structure

```
cite/
├── CLAUDE.md                  (this file)
├── README.md
├── .github/
│   └── workflows/
│       ├── frontend.yml       (lint + build + deploy frontend)
│       └── backend.yml        (lint + test + deploy backend)
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── components.json        (shadcn/ui config)
│   ├── .env.example           (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL)
│   ├── public/
│   │   └── widget.js          (embeddable chat widget — Phase 6)
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── lib/
│       │   ├── supabase.ts    (Supabase client init)
│       │   ├── api.ts         (axios/fetch wrapper for backend calls)
│       │   └── utils.ts       (helpers)
│       ├── hooks/
│       │   ├── useAuth.ts     (login, signup, logout, session)
│       │   ├── useKnowledgeBases.ts
│       │   ├── useDocuments.ts
│       │   └── useChat.ts     (send message, receive stream)
│       ├── components/
│       │   ├── ui/            (shadcn/ui components — button, input, card, etc.)
│       │   ├── layout/
│       │   │   ├── AppLayout.tsx      (sidebar + main content)
│       │   │   ├── Sidebar.tsx
│       │   │   └── Header.tsx
│       │   ├── auth/
│       │   │   ├── LoginForm.tsx
│       │   │   ├── SignupForm.tsx
│       │   │   └── ProtectedRoute.tsx
│       │   ├── dashboard/
│       │   │   ├── KnowledgeBaseList.tsx
│       │   │   ├── KnowledgeBaseCard.tsx
│       │   │   └── CreateKBDialog.tsx
│       │   ├── documents/
│       │   │   ├── DocumentUpload.tsx  (drag-and-drop upload area)
│       │   │   ├── DocumentList.tsx
│       │   │   ├── DocumentItem.tsx    (shows name, status, chunk count)
│       │   │   └── ProcessingStatus.tsx
│       │   ├── chat/
│       │   │   ├── ChatWindow.tsx      (main chat container)
│       │   │   ├── MessageList.tsx
│       │   │   ├── MessageBubble.tsx   (user vs assistant styling)
│       │   │   ├── SourceCitation.tsx  (clickable source references)
│       │   │   ├── ChatInput.tsx       (text input + send button)
│       │   │   └── StreamingIndicator.tsx
│       │   ├── landing/
│       │   │   ├── LandingPage.tsx
│       │   │   ├── Hero.tsx
│       │   │   ├── Features.tsx
│       │   │   └── CTA.tsx
│       │   └── widget/
│       │       └── WidgetConfigurator.tsx (generates embed code for users)
│       ├── pages/
│       │   ├── Landing.tsx
│       │   ├── Login.tsx
│       │   ├── Signup.tsx
│       │   ├── Dashboard.tsx
│       │   ├── KnowledgeBase.tsx       (single KB view — documents + chat)
│       │   └── SharedChat.tsx          (public shareable chat page)
│       └── types/
│           └── index.ts               (TypeScript interfaces for all entities)
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example           (SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            (FastAPI app, CORS, lifespan, middleware)
│   │   ├── config.py          (pydantic Settings, env var loading)
│   │   ├── dependencies.py    (get_current_user, get_supabase, etc.)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── health.py      (GET /health — basic health check)
│   │   │   ├── knowledge_bases.py  (CRUD for knowledge bases)
│   │   │   ├── documents.py   (upload, process, status)
│   │   │   ├── chat.py        (RAG query + streaming response)
│   │   │   └── widget.py      (public chat endpoint for embedded widget — no auth)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── supabase.py    (Supabase client wrapper)
│   │   │   ├── chunking.py    (AI-powered intelligent document chunking)
│   │   │   ├── embedding.py   (OpenAI embedding API calls)
│   │   │   ├── extraction.py  (PDF/TXT text extraction)
│   │   │   ├── rag.py         (vector search + prompt assembly)
│   │   │   └── claude.py      (Claude API streaming calls)
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schemas.py     (Pydantic request/response models)
│   └── tests/
│       ├── __init__.py
│       ├── test_health.py
│       └── test_rag.py
│
└── widget/                    (Phase 6 — embeddable widget source)
    ├── widget.ts              (TypeScript source for the widget)
    ├── widget.css             (minimal widget styles)
    └── build.sh               (compiles to frontend/public/widget.js)
```

## Database Schema

### Supabase SQL (run in SQL Editor during setup)

```sql
-- Enable pgvector
create extension if not exists vector;

-- Knowledge bases
create table knowledge_bases (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  name text not null,
  description text,
  is_public boolean default false,
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
create table messages (
  id uuid default gen_random_uuid() primary key,
  conversation_id uuid references conversations(id) on delete cascade not null,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  sources jsonb default '[]'::jsonb,
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

-- Function for vector similarity search
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

# Widget (public — no auth, uses KB id + optional rate limiting)
POST   /api/v1/widget/{kb_id}/chat     → Public chat endpoint for embedded widget
```

### Auth Flow

1. Frontend uses Supabase Auth SDK for login/signup (email + Google OAuth)
2. Supabase returns a JWT access token
3. Frontend sends this JWT in `Authorization: Bearer <token>` header to FastAPI
4. FastAPI verifies the JWT by calling Supabase's `auth.getUser(token)` using the service role key
5. If valid, extracts `user_id` and passes to route handlers via dependency injection

## RAG Pipeline Details

### Chunking Strategy (AI-Powered)

```
3-step intelligent chunking pipeline using Claude during document processing:

Step 1 — AI Section Detection (identify_sections):
- Sends document text to Claude to identify logical section boundaries
- Each section: title + start/end character positions (200-3000 chars each)
- For docs > 30,000 chars: AI analyzes first 30k, heuristic splits the rest
  (splits at double-newlines and heading patterns to keep API costs low)
- Falls back to fixed-size chunking (2000 chars, 200 overlap) if AI fails

Step 2 — Document Summary (generate_summary):
- Claude generates a 150-200 word overview from section titles + previews
- Stored as chunk_index 0 with metadata: {"is_summary": true, "title": "Document Overview"}
- Answers meta-questions like "What is this document about?"
- Fallback: concatenates section titles

Step 3 — Search Descriptions (generate_chunk_descriptions):
- Single Claude call generates keyword-rich one-line descriptions per section
- Stored in metadata: {"search_description": "anti-bribery FCPA corruption gift policy"}
- Used to improve embedding quality (see Embedding section below)
- Fallback: uses section titles

Each chunk stores:
  content, chunk_index, metadata {title, is_summary, search_description, file_name}
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
- Convert user question to embedding using same model
- Call match_chunks() PostgreSQL function
- Fetch up to 8 candidates with similarity > 0.5
- If zero results, retry with threshold 0.3
- Enrich chunks with chunk_index, file_name, and metadata from document_chunks
- Return top 5 chunks sorted by similarity (highest first)
```

### Prompt Assembly

```
System prompt:
"You are a helpful document assistant. Answer questions using ONLY the document excerpts provided below.

Rules:
1. If an excerpt directly answers the question, cite it using [Source: filename, Section N] format
2. ONLY cite excerpts that DIRECTLY contain information answering the question
3. For each citation, briefly quote the specific phrase (under 20 words) that supports your answer
4. If the answer is not found in any excerpt, say:
   'I don't have enough information in the uploaded documents to answer this question.'
5. Do NOT make up information or use knowledge outside the provided excerpts
6. It is better to cite 1 precise source than 5 vague ones
7. If the question is about the overall document, look for the Document Overview section first"

Context (injected):
"--- Document Excerpts ---
[1] From: {filename} (Section {chunk_index})
{chunk_content}

[2] From: {filename} (Section {chunk_index})
{chunk_content}

... (up to 5 chunks)
--- End of Excerpts ---"

User message:
"{user's question}"
```

### Streaming

```
- Use Anthropic Python SDK with streaming
- FastAPI StreamingResponse with text/event-stream content type
- Frontend uses EventSource or fetch with ReadableStream
- Each streamed chunk is sent as SSE: data: {"token": "...", "done": false}
- Final message includes sources: data: {"token": "", "done": true, "sources": [...]}
```

## Coding Conventions

### Python (Backend)

- Python 3.11+
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
- Tailwind CSS for all styling — no CSS files except for widget
- shadcn/ui for all UI components — do not build custom buttons, inputs, cards, dialogs
- Responsive design — mobile-first approach
- Loading states and error states for EVERY async operation

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

### Backend (PRIVATE — runs on your server)
- All secrets loaded from environment variables via pydantic BaseSettings — NEVER hardcoded
- Supabase service role key stays on backend ONLY
- OpenAI API key stays on backend ONLY
- Anthropic API key stays on backend ONLY
- All user input is validated with Pydantic models before processing
- All file uploads are validated: check mime type, file size, file extension on backend (don't trust frontend validation)
- Rate limiting on all public endpoints (especially the widget chat endpoint)
- CORS restricted to specific origins — not wildcard * (except widget endpoint)

### Data Flow (How it works securely)
1. User logs in → Supabase Auth gives them a JWT (frontend)
2. User uploads a doc → Frontend sends file + JWT to FastAPI backend
3. Backend verifies JWT with Supabase → extracts user_id
4. Backend processes file → calls OpenAI for embeddings → stores in Supabase
5. User asks a question → Frontend sends question + JWT to FastAPI backend
6. Backend verifies JWT → does vector search → calls Claude API → streams response back
7. Frontend NEVER touches OpenAI or Claude directly

### .env Files
- .env files are NEVER committed to git — add to .gitignore immediately
- .env.example files (with placeholder values) ARE committed — so other devs know what's needed

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
- Main branch: `main` — always deployable, protected
- Development branches named by phase: `phase-1/auth-skeleton`, `phase-2/kb-crud`, etc.
- Feature branches off phase branches if needed: `phase-3/fix-upload-validation`
- Merge to main only when a phase is complete and tested

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
  2. AI-powered chunking: Claude identifies sections → generates summary → generates search descriptions
     (falls back to fixed-size 2000-char chunks if AI fails)
  3. Generate embeddings via OpenAI API (combined search_description + content for each chunk)
  4. Store chunks + embeddings in document_chunks table (content stores original text, not combined)
  5. Update document status to "ready" (or "failed" with error_message)
  - Note: 3 Claude API calls per document during processing (section detection, summary, descriptions)
- Status endpoint: returns current document processing status
- Delete endpoint: removes document, chunks, and storage file

**Frontend:**
- KB detail page with two panels: Documents (left) + Chat (right, placeholder for now)
- Drag-and-drop upload area (accept .pdf, .txt, .md)
- Document list showing name, status badge (uploading/processing/ready/failed), chunk count
- Poll document status every 2 seconds while processing
- Delete document button

### Phase 4: RAG Chat (Day 6-8)

**Backend:**
- Chat endpoint: receives message + knowledge_base_id
  1. Create or continue conversation
  2. Embed the user's question
  3. Call match_chunks() to find relevant document chunks
  4. Assemble prompt with system instructions + chunks + question
  5. Stream Claude's response back via SSE
  6. After streaming complete, save message + sources to database
- Conversation history: include last 5 messages as context for follow-up questions
- Source extraction: parse Claude's citations and map to actual document/chunk IDs

**Frontend:**
- Chat panel in KB detail page
- Message list with user and assistant bubbles
- Streaming text display (tokens appear in real-time)
- Source citations at bottom of assistant messages (clickable, show source text)
- Chat input with send button and Enter key support
- Conversation list in sidebar (within KB view)
- "New conversation" button
- Auto-scroll to bottom on new messages
- Loading indicator while waiting for first token

### Phase 5: Landing Page + Polish + Deploy (Day 9-10)

**Frontend:**
- Landing page at cite.weaverbit.com:
  - Hero: "Your documents, instantly searchable. AI answers with citations."
  - How it works: 3 steps (Upload → Ask → Get cited answers)
  - Feature highlights: Source citations, embeddable widget, secure
  - CTA: "Get Started Free" → signup
- Error boundaries and fallback UI
- Toast notifications for success/error actions
- Responsive design check (mobile + tablet + desktop)
- Loading skeletons for all async content

**Deployment:**
- Frontend → Vercel (connect GitHub repo, set env vars)
- Backend → Railway (connect GitHub repo, use Dockerfile, set env vars)
- Configure cite.weaverbit.com DNS: frontend subdomain → Vercel
- Configure api-cite.weaverbit.com: backend subdomain → Railway
- Verify everything works in production

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
- The widget endpoint is PUBLIC — implement rate limiting before deploy
- Streaming responses use Server-Sent Events (SSE), not WebSockets
- For PDF extraction, use PyPDF2 (simple, reliable) — not heavy libraries like pdfplumber
- Document chunking uses AI (Claude) to identify logical sections — falls back to fixed-size if AI fails
- Embeddings are generated from combined text (search_description + content), but only original content is stored in document_chunks
- Existing documents must be deleted and re-uploaded to benefit from new chunking — old chunks are not auto-migrated
- The ivfflat index on embeddings requires at least ~100 rows to be effective. For small datasets during development, it still works but may not be as fast
- All dates are stored and returned in UTC (timestamptz)
