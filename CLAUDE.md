# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NovelVerse is a Vietnamese Chinese web novel reading platform. The PRD is in `docs/PRD.md` (written in Vietnamese). Tech stack: FastAPI (Python) backend, Next.js (React) frontend, Supabase (PostgreSQL + Auth + Storage), Upstash Redis, with AI features in Phase 3 (Qdrant, Gemini API, ElevenLabs TTS).

## Planned Architecture

```
frontend/          # Next.js App Router (deployed to Vercel)
  app/             # Pages and routes
  components/      # React components
  lib/             # Supabase client, API client utilities

backend/           # FastAPI (deployed to Railway)
  app/
    api/           # Route handlers (/api/v1/*)
    core/          # Config, security, database connections
    models/        # Pydantic schemas for request/response
    services/      # Business logic layer
    workers/       # Crawl worker (24h cron), notification worker

supabase/
  migrations/      # PostgreSQL migration files

docker-compose.yml # Local dev environment
```

## Key Architecture Decisions

- **Auth**: Supabase OAuth (Google) on frontend, JWT verification middleware in FastAPI
- **Data security**: Row Level Security (RLS) policies at PostgreSQL level are the primary security layer
- **Soft deletes**: All important content uses `is_deleted` flag, never hard delete
- **Crawl pipeline**: URL → `crawl_queue` table → worker processes → Uploader review → publish
- **VIP early access**: Chapters use `publish_at` scheduling to gate VIP Pro/Max content
- **API convention**: RESTful at `/api/v1`, JWT Bearer in Authorization header
- **Three user roles**: `reader`, `uploader`, `admin`
- **Rate limiting**: Upstash Redis token bucket (100 req/min per user)

## Frontend Patterns

- Next.js App Router with SSG for homepage, ISR (60s revalidate) for novel pages
- Cursor-based pagination for long lists
- Supabase Realtime for live updates (comments, notifications)
- Next.js Image Optimization for all images

## Backend Patterns

- Python environment managed by `uv` (use `uv` for dependency management, virtual environments, and running scripts)
- Pydantic schemas for all request/response validation
- `bleach` for HTML sanitization of user content
- Async throughout (FastAPI async support)
- OpenCC for Han-Viet character conversion
- Crawl sources restricted to 6 whitelisted domains

## Database

14 PostgreSQL tables on Supabase. Key tables: `users` (extends `auth.users`), `novels` (with full-text search vector), `chapters` (dual scheduling: `publish_at` vs `published_at`), `comments` (unified for novel + chapter, 1-level reply), `reviews` (1-5 stars, one per user per novel), `nominations` (daily vote tracking), `vip_subscriptions`, `donations` (with commission calc).

Phase 3 AI tables: `characters`, `chat_sessions`, `novel_embeddings`.

## External Services

- **Supabase**: DB, Auth, Storage, Realtime
- **Upstash Redis**: Leaderboard caching, daily votes, crawl job queue
- **Stripe**: VIP subscriptions, donations, commission payouts
- **Google Gemini API**: AI translation, chat with characters (Phase 3)
- **ElevenLabs**: AI TTS narration (Phase 3)
- **Qdrant Cloud**: Vector DB for RAG (Phase 3)
- **Resend / Supabase Email**: Notifications

## Development Phases

1. **Phase 1 (MVP)**: Core reading, crawl pipeline, basic comments/reviews, VIP system
2. **Phase 2**: Advanced features — nominations, leaderboards, donations, notifications
3. **Phase 3**: AI features — chat with characters (RAG), AI narrator (TTS)
