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
npx playwright test                        # Run E2E tests (requires built app)

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
- **Supabase Realtime subscription pattern**: `useNotifications` hook (`lib/hooks/use-notifications.ts`) subscribes to INSERT events on `notifications` filtered by `user_id`, increments unread badge, and shows toast; always unsubscribes on unmount
- **E2E testing**: Playwright at `frontend/e2e/`; config at `frontend/playwright.config.ts`; run with `npx playwright test` (requires `npm run build` first); two suites: `smoke.spec.ts` (public routes) and `phase2.spec.ts` (auth-guard and Phase 2 UI behavior)

## Backend Patterns

- Python environment managed by `uv` (use `uv` for dependency management, virtual environments, and running scripts)
- Pydantic schemas for all request/response validation
- `bleach` for HTML sanitization of user content
- Async throughout (FastAPI async support)
- OpenCC for Han-Viet character conversion
- Crawl sources restricted to 6 whitelisted domains
- **DB triggers (SECURITY DEFINER)**: Notification fanout — 4 triggers on `chapters`, `comments`, `comment_likes`, `gift_logs` auto-insert into `notifications` with JSONB payloads
- **Redis sorted sets**: Leaderboard periods (daily 48h TTL, weekly 14d TTL, monthly 60d TTL) in Upstash, with DB fallback on cache miss; see `services/nomination_service.py`
- **VIP tier quotas**: Nomination daily allowances enforced in service layer (reader: 3/day, VIP Pro: 5/day, VIP Max: 10/day); quota reset tracked via `nominations_reset_at` on `users`

## Database

23 PostgreSQL tables on Supabase. Key tables:

**Content**: `users` (extends `auth.users`), `novels` (with full-text search vector), `chapters` (dual scheduling: `publish_at` vs `published_at`), `comments` (unified for novel + chapter, 1-level reply), `reviews` (1-5 stars, one per user per novel)

**Crawl**: `crawl_sources`, `crawl_queue`

**VIP & Economy**: `vip_subscriptions` (Linh Thạch-based, no Stripe), `wallets` (LT + TT balances, auto-created per user), `transactions` (unified ledger — all balance changes logged), `deposit_requests` (bank transfer → LT, admin-confirmed), `shop_items` (10 items, seeded), `gift_logs` (LT spent → TT credited), `withdrawal_requests` (TT → VND, admin-processed)

**Moderation**: `reports`, `feedbacks`

**System**: `system_settings` (key-value store: VIP prices in LT, exchange rates, limits)

**Social & Community**: `follows` (follower_id → followee_id, uploaders only; denorm `follower_count` on `users`), `bookmarks` (user_id, novel_id), `nominations` (user_id, novel_id, period — daily/weekly/monthly; mirrored in Redis sorted sets; denorm `nomination_count` on `novels`), `notifications` (user_id, type enum, payload JSONB, read_at — populated by 4 DB triggers)

Phase 3 AI tables: `characters`, `chat_sessions`, `novel_embeddings`. M19 (Story Intelligence Dashboard) stores relationship graphs and timelines as JSONB columns on `novels` — no additional tables.

## External Services

- **Supabase**: DB, Auth, Storage, Realtime
- **Upstash Redis**: Rate limiting, leaderboard caching (sorted sets), daily nomination quotas, crawl job queue
- **Google Gemini API**: AI translation, chat with characters, story intelligence features (Phase 3)
- **ElevenLabs**: AI TTS narration (Phase 3)
- **Qdrant Cloud**: Vector DB for RAG (Phase 3)
- **Resend / Supabase Email**: Transactional notifications
- **NetworkX** *(Phase 3 M19)*: Python library for character relationship graph computation
- **D3.js** *(Phase 3 M19)*: Frontend force-directed graph visualization for the Story Intelligence Dashboard

## Social & Notification API Routes (at /api/v1/)

| Route                              | Description                                          |
| ---------------------------------- | ---------------------------------------------------- |
| `GET /users/{id}/follow`           | Get follow status for a user                         |
| `POST /users/{id}/follow`          | Toggle follow/unfollow an uploader                   |
| `GET /users/me/bookmarks`          | Paginated list of current user's bookmarked novels   |
| `GET /novels/{id}/bookmark`        | Get bookmark status for a novel                      |
| `POST /novels/{id}/bookmark`       | Toggle bookmark on a novel                           |
| `GET /novels/{id}/nominate`        | Get nomination status + remaining daily quota        |
| `POST /novels/{id}/nominate`       | Toggle nomination vote (quota enforced by VIP tier)  |
| `GET /novels/leaderboard`          | Leaderboard (`?period=daily\|weekly\|monthly`)       |
| `GET /notifications`               | Paginated notification list, unread-first            |
| `GET /notifications/unread-count`  | Unread badge count                                   |
| `PATCH /notifications/{id}/read`   | Mark single notification as read                     |
| `PATCH /notifications/read-all`    | Mark all notifications as read                       |

## Economy API Routes (at /api/v1/)

| Route                                    | Description                                           |
| ---------------------------------------- | ----------------------------------------------------- |
| `GET /economy/wallet`                    | User's LT + TT balances                               |
| `POST /economy/deposit`                  | Create bank deposit request (generates transfer code) |
| `GET /economy/shop`                      | List shop items (public)                              |
| `POST /economy/shop/{id}/purchase`       | Buy item with LT                                      |
| `POST /economy/shop/{id}/gift`           | Gift item to uploader (LT → TT)                       |
| `POST /economy/withdrawal`               | Uploader requests TT withdrawal                       |
| `GET /economy/transactions`              | Paginated transaction ledger                          |
| `POST /vip/purchase`                     | Buy VIP Pro/Max with LT (instant)                     |
| `GET /admin/deposits`                    | Admin: list deposit requests                          |
| `PATCH /admin/deposits/{id}/confirm`     | Admin: confirm deposit, credit LT                     |
| `GET /admin/withdrawals`                 | Admin: list withdrawal requests                       |
| `PATCH /admin/withdrawals/{id}/complete` | Admin: complete withdrawal, deduct TT                 |

## Chat API Routes (at /api/v1/) — Phase 3 M17

| Route                                        | Description                                           |
| -------------------------------------------- | ----------------------------------------------------- |
| `GET /chat/novels/{id}/characters`           | List characters for a novel (public)                  |
| `POST /chat/sessions`                        | Create chat session for a character (VIP Max only)    |
| `GET /chat/sessions?novel_id={id}`           | List current user's sessions for a novel              |
| `GET /chat/sessions/{id}`                    | Get session with full message history                 |
| `POST /chat/sessions/{id}/message`           | Send message — SSE streaming response (VIP Max only)  |

## Development Phases

1. **Phase 1 (MVP)**: Core reading, crawl pipeline, comments/reviews, VIP system, virtual economy — **COMPLETE**
2. **Phase 2**: Social features — follows/bookmarks, nominations/leaderboards, real-time notifications, CI/CD + E2E tests — **COMPLETE**
3. **Phase 3**: AI features — Vector infra (M16) ✅, Chat with Characters RAG (M17) ✅, AI Narrator TTS (M18), Story Intelligence Dashboard: relationship graph, timeline, Q&A, arc summaries (M19) — **IN PROGRESS**

See `docs/DEVELOPMENT_PLAN.md` for the full milestone roadmap.

See `docs/In-App Economy Specification.md` for the full economy specification.
