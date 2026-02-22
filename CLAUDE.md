# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NovelVerse is a Vietnamese Chinese web novel reading platform. The PRD is in `docs/PRD.md` (written in Vietnamese). Tech stack: FastAPI (Python) backend, Next.js (React) frontend, Supabase (PostgreSQL + Auth + Storage), Upstash Redis, with AI features in Phase 3 (Qdrant, Gemini API, ElevenLabs TTS).

## Development Commands

```bash
# Backend (from backend/)
uv sync                                    # Install dependencies
uv run uvicorn app.main:app --reload       # Start dev server (port 8000)
uv run pytest                              # Run tests
uv run pytest tests/test_auth.py -v        # Run single test file

# Frontend (from frontend/)
npm install                                # Install dependencies
npm run dev                                # Start dev server (port 3000)
npm run build                              # Production build
npm run lint                               # Lint

# Supabase (from project root, requires Docker Desktop)
npx supabase start                         # Start local Supabase
npx supabase stop                          # Stop local Supabase
npx supabase db reset                      # Reset DB and re-run migrations
npx supabase migration new <name>          # Create new migration
```

## Architecture

```
frontend/              # Next.js App Router (deployed to Vercel)
  app/                 # Pages and routes
  components/          # React components (shadcn/ui)
  lib/                 # Supabase client, API client, utilities
    supabase/client.ts # Browser Supabase client
    supabase/server.ts # Server-side Supabase client
    api.ts             # FastAPI fetch wrapper with JWT injection
  proxy.ts             # Next.js 16 proxy (was "middleware") — session refresh

backend/               # FastAPI (deployed to Railway)
  app/
    main.py            # FastAPI app entry point
    api/v1/            # Route handlers (/api/v1/*)
    core/              # Config, security, database connections
      config.py        # Pydantic Settings (env vars)
      database.py      # Supabase client (lazy init via get_supabase())
    models/            # Pydantic schemas for request/response
    services/          # Business logic layer
    workers/           # Crawl worker, notification worker
  tests/

supabase/
  migrations/          # PostgreSQL migration files
```

## Key Architecture Decisions

- **Auth**: Supabase OAuth (Google) on frontend, JWT verification middleware in FastAPI
- **Data security**: Row Level Security (RLS) policies at PostgreSQL level are the primary security layer
- **Soft deletes**: All important content uses `is_deleted` flag, never hard delete
- **Crawl pipeline**: URL → `crawl_queue` table → worker processes → Uploader review → publish
- **VIP early access**: Chapters use `publish_at` scheduling to gate VIP Pro/Max content. VIP is purchased with Linh Thạch (internal soft currency) — no external payment gateway.
- **Virtual economy**: Dual-currency system — Linh Thạch (soft, buy via bank deposit) and Tiên Thạch (withdrawable, earned via gifting). Fixed rates: 1 VND → 0.95 LT, 1 LT → 0.95 TT, 1 TT = 1 VND.
- **API convention**: RESTful at `/api/v1`, JWT Bearer in Authorization header
- **Three user roles**: `reader`, `uploader`, `admin`
- **Rate limiting**: Upstash Redis sliding window (100 req/min per user/IP)

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

19 PostgreSQL tables on Supabase. Key tables:

**Content**: `users` (extends `auth.users`), `novels` (with full-text search vector), `chapters` (dual scheduling: `publish_at` vs `published_at`), `comments` (unified for novel + chapter, 1-level reply), `reviews` (1-5 stars, one per user per novel)

**Crawl**: `crawl_sources`, `crawl_queue`

**VIP & Economy**: `vip_subscriptions` (Linh Thạch-based, no Stripe), `wallets` (LT + TT balances, auto-created per user), `transactions` (unified ledger — all balance changes logged), `deposit_requests` (bank transfer → LT, admin-confirmed), `shop_items` (10 items, seeded), `gift_logs` (LT spent → TT credited), `withdrawal_requests` (TT → VND, admin-processed)

**Moderation**: `reports`, `feedbacks`

**System**: `system_settings` (key-value store: VIP prices in LT, exchange rates, limits)

Phase 3 AI tables: `characters`, `chat_sessions`, `novel_embeddings`.

## External Services

- **Supabase**: DB, Auth, Storage, Realtime
- **Upstash Redis**: Rate limiting, leaderboard caching, daily votes, crawl job queue
- **Google Gemini API**: AI translation, chat with characters (Phase 3)
- **ElevenLabs**: AI TTS narration (Phase 3)
- **Qdrant Cloud**: Vector DB for RAG (Phase 3)
- **Resend / Supabase Email**: Notifications

## Economy API Routes (at /api/v1/)

| Route | Description |
|-------|-------------|
| `GET /economy/wallet` | User's LT + TT balances |
| `POST /economy/deposit` | Create bank deposit request (generates transfer code) |
| `GET /economy/shop` | List shop items (public) |
| `POST /economy/shop/{id}/purchase` | Buy item with LT |
| `POST /economy/shop/{id}/gift` | Gift item to uploader (LT → TT) |
| `POST /economy/withdrawal` | Uploader requests TT withdrawal |
| `GET /economy/transactions` | Paginated transaction ledger |
| `POST /vip/purchase` | Buy VIP Pro/Max with LT (instant) |
| `GET /admin/deposits` | Admin: list deposit requests |
| `PATCH /admin/deposits/{id}/confirm` | Admin: confirm deposit, credit LT |
| `GET /admin/withdrawals` | Admin: list withdrawal requests |
| `PATCH /admin/withdrawals/{id}/complete` | Admin: complete withdrawal, deduct TT |

## Development Phases

1. **Phase 1 (MVP)**: Core reading, crawl pipeline, comments/reviews, VIP system, virtual economy — **COMPLETE**
2. **Phase 2**: Advanced features — nominations, leaderboards, gifting/donations, notifications, CI/CD
3. **Phase 3**: AI features — chat with characters (RAG), AI narrator (TTS)

See `docs/DEVELOPMENT_PLAN.md` for the full milestone roadmap.
