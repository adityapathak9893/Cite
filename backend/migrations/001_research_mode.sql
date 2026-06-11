-- Migration 001: Research Mode (Phase A)
-- Run in the Supabase SQL Editor.
-- Adds KB-level domain profile, suggested questions, and chat mode,
-- plus per-message domain context. All columns are nullable or defaulted,
-- so existing rows need no backfill.

-- Knowledge bases: domain profile (2-4 sentence description of the corpus domain)
alter table knowledge_bases
  add column if not exists domain_profile text;

-- Knowledge bases: AI-generated suggested questions (array of strings)
alter table knowledge_bases
  add column if not exists suggested_questions jsonb;

-- Knowledge bases: chat mode — 'strict' (document-only) or 'research' (document-anchored)
alter table knowledge_bases
  add column if not exists chat_mode text not null default 'research'
  check (chat_mode in ('strict', 'research'));

-- Messages: domain context block parsed from research-mode responses
alter table messages
  add column if not exists domain_context text;
