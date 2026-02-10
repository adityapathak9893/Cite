# Weaverbit Cite

AI-powered document Q&A platform with embeddable chat widget. Upload your documents, ask questions, and get answers with source citations — powered by RAG (Retrieval-Augmented Generation).

**Live:** [cite.weaverbit.com](https://cite.weaverbit.com)

## What It Does

Businesses upload their documents (PDF, TXT, Markdown). Their teams or customers chat with an AI that answers **only** from those documents, with clickable source citations. No hallucination — every answer is grounded in your uploaded content.

### Key Features

- **Document Q&A with Citations** — AI answers reference exact source documents and sections
- **Knowledge Bases** — Organize documents into separate collections with independent chat
- **Streaming Responses** — Real-time token-by-token AI responses via Server-Sent Events
- **Embeddable Widget** — Drop a `<script>` tag on any website to add document chat
- **Dark Mode** — Full light/dark theme support with system preference detection
- **Secure by Design** — All AI keys stay server-side; frontend only holds public Supabase anon key

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS v4, shadcn/ui |
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
│   │   ├── routers/       health, knowledge_bases, documents, chat, widget
│   │   ├── services/      chunking, embedding, extraction, RAG, Claude
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
- **Python** >= 3.11
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

# Widget (public)
POST   /api/v1/widget/{kb_id}/chat                      Public chat (rate-limited)
```

## How RAG Works

1. **Upload** — User uploads a PDF/TXT/MD file
2. **Extract** — Backend extracts text from the document
3. **Chunk** — Text is split into ~500-token chunks with 50-token overlap
4. **Embed** — Each chunk is converted to a 1536-dimension vector via OpenAI
5. **Store** — Chunks + vectors are stored in Supabase (pgvector)
6. **Query** — User asks a question, which is also embedded
7. **Search** — pgvector finds the top 5 most similar chunks (cosine similarity > 0.7)
8. **Generate** — Claude answers using only the retrieved chunks, citing sources
9. **Stream** — Response is streamed token-by-token via SSE to the frontend

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
| 2 | Not started | Knowledge Base CRUD |
| 3 | Not started | Document Upload + Processing |
| 4 | Not started | RAG Chat with Streaming |
| 5 | Not started | Landing Page + Polish + Deploy |
| 6 | Not started | Embeddable Widget |
| 7 | Not started | Final Polish |

## License

Proprietary — Weaverbit LLC. All rights reserved.
