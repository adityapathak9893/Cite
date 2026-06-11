# Weaverbit Cite

AI-powered document Q&A platform. Upload your documents, ask questions, and get document-grounded answers with source citations — powered by RAG (Retrieval-Augmented Generation).

**Live:** [cite.weaverbit.com](https://cite.weaverbit.com)

## What It Does

Businesses upload their documents (PDF, TXT, Markdown). Their teams or customers chat with an AI about them, with clickable source citations. Each knowledge base runs in one of two chat modes:

- **Strict** — answers come only from the uploaded documents; questions the documents don't cover get a fallback message.
- **Research** — two-channel answers: the main answer stays grounded in the documents, while relevant domain knowledge beyond them appears in a separate, clearly labeled "Domain context" panel — never mixed into the document-grounded answer.

### Key Features

- **Intelligent Document Assistant** — AI synthesizes and explains documents conversationally, not just quoting text. Answers feel like talking to a colleague who has deeply read every document
- **Research Mode (two-channel answers)** — a behavioral contract separates what the documents say from what the field knows: document-grounded main answer, fenced domain-context panel for everything beyond. Per-KB switchable back to strict document-only mode
- **Domain Profiles & Suggested Questions** — after each upload, the KB's domain is profiled and 4–6 corpus-specific suggested questions are generated (real terms from your documents, not generic templates) and shown as chips on empty chats
- **Smart Chunking** — markdown documents are split deterministically at heading boundaries; unstructured documents use AI section detection via verbatim text markers (never character offsets), plus AI-generated summaries and keyword descriptions for better retrieval
- **Source Citations** — Citation chips appear below responses showing exactly which sections were used, without interrupting the answer text
- **Knowledge Bases** — Organize documents into separate collections with independent chat
- **Streaming Responses** — Real-time token-by-token AI responses via Server-Sent Events
- **Dark Mode** — Full light/dark theme support with system preference detection
- **Secure by Design** — All AI keys stay server-side; frontend only holds public Supabase anon key

An embeddable website widget is planned (Phase 6) but not yet built.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS v4, shadcn/ui |
| Backend | FastAPI, Python 3.13, Pydantic |
| Database | Supabase (PostgreSQL + pgvector + Auth + Storage) |
| Embeddings | OpenAI text-embedding-3-small (1536 dimensions) |
| AI Chat | Anthropic Claude (claude-sonnet-4-5-20250929) |
| Auth | Supabase Auth (email/password + Google OAuth) |
| Frontend Deploy | Vercel |
| Backend Deploy | Railway (Docker) |

## Project Structure

```
cite/
├── frontend/          React + TypeScript + Vite + Tailwind v4
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/        shadcn/ui primitives
│   │   │   ├── auth/      LoginForm, SignupForm, ProtectedRoute
│   │   │   ├── layout/    AppLayout, Sidebar, Header
│   │   │   ├── dashboard/ KB list, cards, create dialog
│   │   │   ├── documents/ Upload, list, processing status
│   │   │   └── chat/      Chat window, messages, citations, streaming
│   │   ├── pages/         Landing, Login, Signup, Dashboard, KnowledgeBase
│   │   ├── hooks/         useAuth, useKnowledgeBases, useDocuments, useChat
│   │   ├── lib/           Supabase client, API client, utils
│   │   ├── styles/        Design system (globals.css, fonts.css, animations.css)
│   │   └── types/         TypeScript interfaces
│   └── index.html
│
├── backend/           FastAPI + Python
│   ├── app/
│   │   ├── main.py        App entry, CORS, middleware
│   │   ├── config.py      Environment variable loading
│   │   ├── dependencies.py Auth middleware, error handling
│   │   ├── routers/       health, knowledge_bases, documents, chat
│   │   ├── services/      chunking, embedding, extraction, RAG + overview detection, KB profiles, Claude + block parsing
│   │   └── models/        Pydantic request/response schemas
│   ├── migrations/        SQL migrations (run in Supabase SQL Editor)
│   ├── tests/             unit tests + eval harness (tests/eval/)
│   ├── Dockerfile
│   └── requirements.txt
│
├── CLAUDE.md          Architecture spec (DB schema, API routes, RAG pipeline)
└── UX.md              Design system spec (colors, typography, components)
```

## Getting Started

### Prerequisites

- **Node.js** >= 20
- **Python** >= 3.13
- **Supabase** project (free tier works) with pgvector extension enabled
- **OpenAI** API key (for embeddings)
- **Anthropic** API key (for chat)

### 1. Clone the Repository

```bash
git clone https://github.com/AdiPathak97/cite.git
cd cite
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your actual keys (Supabase, OpenAI, Anthropic)

# Start the server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Verify with:

```bash
curl http://localhost:8000/health
# → {"status":"healthy","environment":"development"}
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your Supabase public URL, anon key, and backend API URL

# Start dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

### 4. Supabase Setup

Run the SQL schema in your Supabase SQL Editor to create:
- `knowledge_bases` table with RLS
- `documents` table with RLS
- `document_chunks` table with pgvector embeddings
- `conversations` and `messages` tables with RLS
- `match_chunks()` function for vector similarity search

See [CLAUDE.md](CLAUDE.md) for the full SQL schema.

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (secret — backend only) |
| `SUPABASE_JWT_SECRET` | JWT secret from Supabase dashboard |
| `OPENAI_API_KEY` | OpenAI API key for embeddings |
| `ANTHROPIC_API_KEY` | Anthropic API key for chat |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `ENVIRONMENT` | `development` or `production` |

### Frontend (`frontend/.env`)

| Variable | Description |
|----------|------------|
| `VITE_SUPABASE_URL` | Your Supabase project URL (public) |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key (public — respects RLS) |
| `VITE_API_URL` | Backend API URL (`http://localhost:8000` locally) |

> **Security:** The frontend only uses public Supabase keys. All secret keys (service role, OpenAI, Anthropic) stay on the backend.

## API Endpoints

```
GET    /health                                          Health check

# Knowledge Bases (authenticated)
GET    /api/v1/knowledge-bases                          List user's KBs
POST   /api/v1/knowledge-bases                          Create KB
GET    /api/v1/knowledge-bases/{id}                     Get single KB
PUT    /api/v1/knowledge-bases/{id}                     Update KB
DELETE /api/v1/knowledge-bases/{id}                     Delete KB

# Documents (authenticated)
POST   /api/v1/knowledge-bases/{kb_id}/documents        Upload document
GET    /api/v1/knowledge-bases/{kb_id}/documents         List documents
GET    /api/v1/knowledge-bases/{kb_id}/documents/{id}    Document status
DELETE /api/v1/knowledge-bases/{kb_id}/documents/{id}    Delete document

# Chat (authenticated)
POST   /api/v1/knowledge-bases/{kb_id}/chat             Send message (SSE stream)
GET    /api/v1/knowledge-bases/{kb_id}/conversations     List conversations
GET    /api/v1/conversations/{conv_id}/messages          Get messages

# Widget (Phase 6 — not yet implemented)
# POST   /api/v1/widget/{kb_id}/chat                    Public chat (rate-limited)
```

## How RAG Works

### Document Processing (at upload time)

1. **Upload** — User uploads a PDF/TXT/MD file
2. **Extract** — Backend extracts text from the document
3. **Chunk** — Markdown documents (3+ `##` headings) are split deterministically at heading boundaries (200-3000 chars, merge/split constraints). Unstructured documents use AI section detection that returns verbatim start-markers (the exact first words of each section), located in code by sequential string search — the model is never asked for character positions. Claude then generates a document summary (stored as chunk 0) and keyword-rich search descriptions per section. Falls back to fixed-size chunking if AI sectioning fails
4. **Embed** — Each chunk is embedded via OpenAI using combined text (search description + content) for better retrieval
5. **Store** — Chunks + vectors + metadata (title, summary flag, search description) stored in Supabase pgvector
6. **Profile** — The KB's domain profile and corpus-specific suggested questions are regenerated from all document summaries (also on document deletion)

### Chat (at query time)

7. **Query** — User asks a question, which is embedded using the same model
8. **Overview Detection** — Backend detects overview questions ("what is this about?", "summarize", etc.) and fetches document structure (summary + all section titles) in addition to vector search
9. **Search** — pgvector finds up to 8 candidates with similarity > 0.5 (retries at 0.3 if zero results), returns top 5
10. **Context Assembly** — Retrieved chunks framed as "Document Knowledge" (not "Excerpts") so Claude treats them as internalized knowledge. Overview questions also get document structure and summary
11. **Generate** — Mode-conditional: strict mode uses the document-expert prompt; research mode uses a behavioral contract that classifies each message (document question, domain question, conversational, off-topic, frustration) and keeps domain knowledge out of the document-grounded main answer. In research mode, zero-retrieval messages still go to the model (strict mode returns a fallback message instead). Responses end with a machine-parseable `---SOURCES---` block, optionally preceded in research mode by a `---DOMAIN_CONTEXT---` block
12. **Parse & Stream** — Response streamed token-by-token via SSE. Backend parses the SOURCES and DOMAIN_CONTEXT blocks after the stream completes, strips them from saved text, and returns parsed sources as citation chips plus the domain context for its fenced panel

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

An eval harness for research-mode behavior lives in `backend/tests/eval/` — `run_eval.py` (not pytest-collected) runs a 25-case set against a live knowledge base and writes timestamped JSON + markdown reports with automated structural checks.

## Deployment

### Frontend → Vercel

Connect the GitHub repo, set root directory to `frontend/`, add environment variables in the Vercel dashboard.

### Backend → Railway

Connect the GitHub repo, set root directory to `backend/`, Railway auto-detects the Dockerfile. Add environment variables in the Railway dashboard.

### Docker (Backend)

```bash
cd backend
docker build -t cite-backend .
docker run -p 8000:8000 --env-file .env cite-backend
```

## Build Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | Complete | Backend skeleton + Frontend skeleton + Auth |
| 2 | Complete | Knowledge Base CRUD |
| 3 | Complete | Document Upload + Smart Chunking |
| 4 | Complete | RAG Chat — Intelligent Document Assistant |
| 5 | Complete | Landing Page + Deploy (Vercel + Railway) |
| Research Mode | Complete | Two-channel answers, per-KB chat modes, domain profiles + suggested questions, eval harness |
| 6 | Planned | Embeddable Widget |
| 7 | Planned | Final Polish |

## License

Proprietary — Weaverbit LLC. All rights reserved.
