# Weaverbit Cite — Frontend

React 19 + TypeScript + Vite 7 + Tailwind CSS v4 + shadcn/ui

## Quick Start

```bash
npm install
cp .env.example .env   # then fill in your Supabase URL, anon key, and API URL
npm run dev            # http://localhost:5173
```

## Tech

- **React 19** with TypeScript (strict mode)
- **Vite 7** for build and HMR
- **Tailwind CSS v4** — config via CSS `@theme inline` in `globals.css`, not `tailwind.config.ts`
- **shadcn/ui** (new-york style) for UI primitives
- **TanStack Query** for server state
- **React Router v7** with lazy-loaded pages
- **Supabase Auth** for authentication
- **Sonner** for toast notifications
- **Lucide React** for icons

## Dark Mode

Uses `[data-theme="dark"]` attribute on `<html>`, not `.dark` class. Theme is initialized via inline `<script>` in `index.html` before React hydrates to prevent FOUC.

## Fonts

- **General Sans** — body font, loaded via `@font-face` from Fontshare CDN
- **Instrument Serif** — display/headline font, loaded via Google Fonts
- **JetBrains Mono** — code/citation font, loaded via Google Fonts

## Project Structure

```
src/
├── components/
│   ├── ui/           shadcn/ui primitives (button, input, dialog, etc.)
│   ├── auth/         LoginForm, SignupForm, ProtectedRoute
│   ├── layout/       AppLayout, Sidebar, Header
│   ├── dashboard/    KB list, cards, create dialog
│   ├── documents/    Upload area, document list with status
│   └── chat/         Chat window, messages, citations, streaming
├── pages/            Landing, Login, Signup, Dashboard, KnowledgeBase
├── hooks/            useAuth, useKnowledgeBases, useDocuments, useChat
├── lib/              Supabase client, API client (fetch-based), utils
├── styles/           globals.css (@theme), fonts.css, animations.css
└── types/            TypeScript interfaces
```
