# Weaverbit Cite

AI-powered document Q&A platform with embeddable chat widget. Upload your documents, ask questions, and get answers with source citations — powered by RAG (Retrieval-Augmented Generation).

**Live:** [cite.weaverbit.com](https://cite.weaverbit.com)

## What It Does

Businesses upload their documents (PDF, TXT, Markdown). Their teams or customers chat with an AI that answers **only** from those documents, with clickable source citations. No hallucination — every answer is grounded in your uploaded content.

### Key Features

- **Intelligent Document Assistant** — AI synthesizes and explains documents conversationally, not just quoting text. Answers feel like talking to a colleague who has deeply read every document
- **AI-Powered Smart Chunking** — Claude identifies logical section boundaries during document processing, generates summaries and keyword descriptions for better retrieval
- **Source Citations** — Citation chips appear below responses showing exactly which sections were used, without interrupting the answer text
- **Knowledge Bases** — Organize documents into separate collections with independent chat
- **Streaming Responses** — Real-time token-by-token AI responses via Server-Sent Events
- **Embeddable Widget** — Drop a `<script>` tag on any website to add document chat
- **Dark Mode** — Full light/dark theme support with system preference detection
- **Secure by Design** — All AI keys stay server-side; frontend only holds public Supabase anon key

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
│   │   ├── services/      AI chunking, embedding, extraction, RAG + overview detection, Claude + SOURCES parsing
│   │   └── models/        Pydantic request/response schemas
│   ├── tests/
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
3. **AI Chunking** — Claude identifies logical section boundaries (200-3000 chars each), generates a document summary (stored as chunk 0), and creates keyword-rich search descriptions per section. Falls back to fixed-size chunking if AI fails
4. **Embed** — Each chunk is embedded via OpenAI using combined text (search description + content) for better retrieval
5. **Store** — Chunks + vectors + metadata (title, summary flag, search description) stored in Supabase pgvector

### Chat (at query time)

6. **Query** — User asks a question, which is embedded using the same model
7. **Overview Detection** — Backend detects overview questions ("what is this about?", "summarize", etc.) and fetches document structure (summary + all section titles) in addition to vector search
8. **Search** — pgvector finds up to 8 candidates with similarity > 0.5 (retries at 0.3 if zero results), returns top 5
9. **Context Assembly** — Retrieved chunks framed as "Document Knowledge" (not "Excerpts") so Claude treats them as internalized knowledge. Overview questions also get document structure and summary
10. **Generate** — Claude answers as an intelligent document expert: synthesizes across sections, explains concepts, uses formatting. Outputs a machine-parseable `---SOURCES---` block at the end listing cited sections
11. **Parse & Stream** — Response streamed token-by-token via SSE. Backend parses SOURCES block after stream completes, strips it from saved text, and returns parsed sources as citation chips

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

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
| 3 | Complete | Document Upload + AI-Powered Smart Chunking |
| 4 | Complete | RAG Chat — Intelligent Document Assistant |
| 5 | Complete | Landing Page + Deploy (Vercel + Railway) |
| 6 | Complete | Embeddable Widget |
| 7 | Complete | Final Polish |

## License

Proprietary — Weaverbit LLC. All rights reserved.
