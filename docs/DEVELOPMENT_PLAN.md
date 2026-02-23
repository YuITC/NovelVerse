# NovelVerse — Development Plan

> Living document. Last updated: 2026-02-23.
> Phase 1 MVP and Phase 2 Social Features are complete (15 milestones, 160+ backend tests, 30+ frontend routes/components).
> Phase 3 AI: M16 (vector infra), M17 (Chat with Characters), M18 (AI Narrator TTS), and M19 (Story Intelligence Dashboard) complete. 286 backend tests passing.

---

## Current Status

| Phase | Status | Milestones |
|-------|--------|------------|
| Phase 1 MVP | ✅ Complete | M0–M8 |
| Phase 1 Patch: Economy | ✅ Complete | M9–M11 |
| Phase 2: Social Features | ✅ Complete | M12–M15 |
| Phase 3: AI Features | ✅ Complete | M16–M19 |

---

## Phase 1 Patch: Virtual Economy System

Replaces Stripe with a dual-currency in-app economy (Linh Thạch / Tiên Thạch).
See `docs/In-App Economy Specification.md` for the full spec.

### Milestone 9 — Backend Economy (DB + Services + Tests)

**9.1 — Migration `20260222000008_economy.sql`**
- Alter `vip_subscriptions`: drop Stripe columns (`stripe_session_id`, `stripe_subscription_id`, `payment_method`, `confirmed_by`), rename `amount_paid` → `lt_spent`
- Drop `payment_method_enum`
- Update `system_settings`: remove Stripe prices, add `vip_pro_price_lt=50000`, `vip_max_price_lt=100000`, exchange rates, deposit/withdrawal limits
- New tables: `wallets`, `transactions`, `deposit_requests`, `shop_items` (seeded), `gift_logs`, `withdrawal_requests`
- Trigger: auto-create wallet on user insert

**9.2 — Backend rewrites**
- Remove `stripe` dep (`uv remove stripe`), remove Stripe config fields
- Rewrite `models/vip.py` → `VipPurchaseRequest`, updated `VipSubscriptionPublic`
- Rewrite `services/vip_service.py` → `purchase_vip()` (atomic LT deduction)
- Rewrite `api/v1/vip.py` → `POST /vip/purchase`, keep `GET /vip/me` and `GET /settings`

**9.3 — New economy service**
- `models/economy.py` — all economy Pydantic schemas
- `services/economy_service.py` — wallet, deposit, shop, gift, withdrawal logic
- `api/v1/economy.py` — all economy API endpoints
- Admin endpoints in `api/v1/admin.py`: deposit confirm/reject, withdrawal complete/reject

**9.4 — Tests**
- Rewrite `tests/test_vip.py` (remove Stripe mocks)
- New `tests/test_economy.py` (wallet, deposit, shop, gift, withdrawal flows)
- Target: 160+ tests passing

**Verify:** `uv run pytest -q` all pass. Key flows: deposit → LT credited, VIP purchase → LT deducted, gift → TT credited, withdrawal → TT deducted on completion only.

---

### Milestone 10 — Frontend Economy (Wallet, Shop, VIP Rewrite)

**10.1 — Types**
- Update `lib/types/vip.ts` (remove Stripe fields, add `lt_spent`)
- Create `lib/types/economy.ts` (Wallet, Transaction, DepositRequest, ShopItem, GiftLog, WithdrawalRequest)

**10.2 — New pages**
- `app/wallet/page.tsx` — LT + TT balances, recent transactions, quick links
- `app/wallet/deposit/page.tsx` — preset amounts, transfer code display, deposit history
- `app/wallet/withdraw/page.tsx` — uploader-only, TT → VND request form, history
- `app/shop/page.tsx` — 10 items grid, buy + gift flows, wallet balance display

**10.3 — Updated pages**
- Rewrite `app/vip/page.tsx` — LT-based purchase, wallet balance, deposit CTA
- Update `app/vip/success/page.tsx` → redirect to `/vip`

**10.4 — Components**
- `components/economy/wallet-badge.tsx` — compact LT balance in navbar

**10.5 — Navbar + admin sidebar updates**
- Remove VIP link from navbar; add "Ví" wallet link for authenticated users
- Add `admin/deposits` and `admin/withdrawals` to admin layout sidebar

**Verify:** `npm run build` clean. Routes include `/wallet`, `/wallet/deposit`, `/wallet/withdraw`, `/shop`.

---

### Milestone 11 — Admin Economy Management

**11.1 — Admin deposit management**
- `app/admin/deposits/page.tsx` — table of deposit requests, confirm with VND input, reject
- Filter tabs: Chờ xử lý / Đã xác nhận / Đã từ chối

**11.2 — Admin withdrawal management**
- `app/admin/withdrawals/page.tsx` — table of withdrawal requests with bank details, complete/reject
- Filter tabs: Chờ xử lý / Đã hoàn tất / Đã từ chối

**11.3 — Types**
- Add `AdminDeposit`, `AdminWithdrawal` to `lib/types/admin.ts`

**Verify:** Admin can confirm a deposit, user's LT balance increases. Admin can complete a withdrawal, uploader's TT balance decreases.

---

## Phase 2: Advanced Social Features

~6-8 weeks. Builds on Phase 1 economy system (gifting is the donation mechanism).

### Milestone 12 — Follows + Bookmarks ✅ Complete

**12.1 — Migration `009_follows_bookmarks.sql`**
- `follows` table (follower_id, followee_id — for users/uploaders)
- `bookmarks` table (user_id, novel_id, added_at)

**12.2 — API**
- `POST /users/{id}/follow`, `DELETE /users/{id}/follow`
- `POST /novels/{id}/bookmark`, `DELETE /novels/{id}/bookmark`
- `GET /users/me/bookmarks` — bookmarked novels with reading progress

**12.3 — Frontend**
- Follow button on uploader profiles
- Bookmark button on novel detail pages
- `app/library/page.tsx` enhancements — tabs: Reading / Bookmarked / Completed

---

### Milestone 13 — Nominations + Leaderboards ✅ Complete

**13.1 — Migration `010_nominations.sql`**
- `nominations` table (user_id, novel_id, vote_count, nominated_at) with daily reset logic
- Users have `daily_nominations` field in `users` table (already present)

**13.2 — Redis-backed leaderboards**
- Daily vote counts in Upstash Redis sorted set (`leaderboard:daily`)
- Weekly/monthly aggregation via cron or on-read computation
- `GET /novels/leaderboard?period=daily|weekly|monthly`
- `POST /novels/{id}/nominate` — decrement daily_nominations, push to Redis

**13.3 — Frontend**
- Leaderboard page `app/leaderboard/page.tsx` — tabs for daily/weekly/monthly
- Nominate button on novel cards/detail pages

---

### Milestone 14 — Real-time Notifications ✅ Complete

**14.1 — Migration `011_notifications.sql`**
- `notifications` table (user_id, type, payload JSONB, read_at, created_at)
- Types: `new_chapter`, `reply_to_comment`, `comment_liked`, `gift_received`, `vip_expiring`

**14.2 — Triggers**
- DB trigger on `chapters` insert → notify novel bookmarkers
- DB trigger on `comments` insert (reply) → notify parent comment author
- DB trigger on `gift_logs` insert → notify receiver

**14.3 — API + Realtime**
- `GET /notifications` — paginated, unread-first
- `PATCH /notifications/{id}/read`, `PATCH /notifications/read-all`
- Supabase Realtime subscription on `notifications` table (frontend)

**14.4 — Frontend**
- Notification bell in navbar with unread count badge
- `app/notifications/page.tsx` — full notification list
- Toast notifications for real-time events

---

### Milestone 15 — CI/CD + Quality ✅ Complete

**15.1 — GitHub Actions**
- `.github/workflows/backend.yml`: ruff lint → mypy type check → pytest on PR
- `.github/workflows/frontend.yml`: npm lint → build → Playwright E2E on PR
- Auto-deploy: not automated (deploy manually to Railway/Vercel)

**15.2 — Code quality**
- `ruff` linting + `mypy` type checking in `pyproject.toml` dev deps
- Playwright E2E: `frontend/e2e/smoke.spec.ts` (5 tests) + `frontend/e2e/phase2.spec.ts` (6 tests)
- Covers: public routes, leaderboard tab-switching, auth-guard redirects, notification bell visibility

---

## Phase 3: AI Features

~10-14 weeks. Requires Qdrant Cloud, Gemini API key, ElevenLabs API key.

### Milestone 16 — Vector Infrastructure ✅ Complete

**16.1 — New tables**
- `characters` (novel_id, name, description, traits JSONB)
- `novel_embeddings` (chapter_id, chunk_index, content_preview, vector_id)

**16.2 — Embedding pipeline**
- Trigger on chapter publish → chunk content → embed via Gemini `text-embedding-004`
- Store vector IDs in `novel_embeddings`, vectors in Qdrant collection per novel

**16.3 — Character extraction**
- Background job: parse chapters for character mentions → populate `characters` table

---

### Milestone 17 — Chat with Characters (RAG) ✅ Complete

**17.1 — New tables**
- `chat_sessions` (user_id, novel_id, character_id, messages JSONB array, created_at)

**17.2 — RAG pipeline**
- `POST /chat/sessions` — create session for a character in a novel
- `POST /chat/sessions/{id}/message` — user sends message:
  1. Embed query
  2. Qdrant similarity search (filtered to novel + chapters user has read)
  3. Build context from top-k chunks
  4. Gemini chat with character persona prompt + context
  5. Return response (streaming via SSE)

**17.3 — Frontend**
- Chat panel on novel detail page (expandable)
- Character selector (from `characters` list)
- Streaming message display

---

### Milestone 18 — AI Narrator (TTS) ✅ Complete

**18.1 — Two modes**
- **Mode 1 (Free)**: Web Speech API — `window.speechSynthesis` for Vietnamese TTS, no cost
- **Mode 2 (Premium, VIP only)**: ElevenLabs API — high-quality Vietnamese voice, cached per chapter

**18.2 — Backend**
- `POST /chapters/{id}/tts` — check VIP tier, call ElevenLabs, cache audio URL in Supabase Storage
- `GET /chapters/{id}/tts` — return cached audio URL or trigger generation

**18.3 — Frontend**
- Audio player bar on chapter reading page
- Auto-highlight text as audio plays (Web Speech API `boundary` event)
- VIP gate for ElevenLabs mode

---

### Milestone 19 — Story Intelligence Dashboard ✅ Complete

**Access:** VIP Max tier only
**Dependencies:** M16 (vector infrastructure + character extraction), M17 (novel_embeddings populated)
**New backend dep:** `networkx` (relationship graph computation)
**New frontend dep:** `d3` (graph visualization)

**19.1 — Relationship Graph**
- Extract character/entity co-mentions from chapter embeddings via Gemini structured output
- Build weighted graph using NetworkX; store adjacency data as JSONB on `novels` table
- `GET /ai/novels/{id}/relationships` → `{ nodes: [{id, name}], edges: [{source, target, weight}] }`
- Frontend: D3.js force-directed graph on novel detail page (VIP Max gate)

**19.2 — Story Timeline**
- Extract key plot events per chapter using Gemini structured output
- Store events list as JSONB (no new table needed)
- `GET /ai/novels/{id}/timeline` → ordered list of `{ chapter_number, event_summary }`
- Frontend: Vertical timeline component on novel detail page (VIP Max gate)

**19.3 — Full-Context Q&A**
- Stateless — no session management (unlike M17 chat which uses `chat_sessions`)
- Full RAG without chapter-access filtering (user sees spoilers — suitable for VIP Max)
- `POST /ai/novels/{id}/qa` body `{ question: string }`:
  1. Embed question via Gemini `text-embedding-004`
  2. Qdrant similarity search over full novel (no chapter filter)
  3. Build context from top-k chunks
  4. Gemini generates answer
- Frontend: Q&A input + answer panel on novel detail page (VIP Max gate)

**19.4 — Arc Summaries**
- `GET /ai/novels/{id}/arc-summary?start_chapter=X&end_chapter=Y`
- Batch Gemini calls to summarize the given chapter range; cache JSON result in Supabase Storage
- Frontend: Chapter-range picker with summary display (VIP Max gate)

**Verify:** VIP Max subscriber sees all 4 dashboard panels on novel detail page. VIP Pro and reader tier see an upgrade CTA. API endpoints return 403 for non-VIP-Max callers.

---

## Testing Strategy

| Scope | Tool | When |
|-------|------|------|
| API integration | pytest + httpx TestClient | Every milestone — all PRs |
| Auth + RLS | Direct Supabase queries | Every migration |
| Frontend build | `npm run build` | Every frontend change |
| E2E (Phase 2+) | Playwright | Before releases |
| Load testing | locust | Before production launch |

**Priority:** Security and financial correctness first — wallet balance, transaction logging, and withdrawal flows must have comprehensive test coverage.

---

## Migration Index

| File | Contents |
|------|----------|
| `20260222000001_users.sql` | users, user_role, vip_tier enums |
| `20260222000002_novels_tags.sql` | novels, tags, novel_tags, FTS |
| `20260222000003_chapters_reading.sql` | chapters, reading_progress, VIP RLS |
| `20260222000004_comments_reviews.sql` | comments, comment_likes, reviews |
| `20260222000005_crawl.sql` | crawl_sources, crawl_queue |
| `20260222000006_vip.sql` | vip_subscriptions (original), system_settings |
| `20260222000007_reports_feedbacks.sql` | reports, feedbacks |
| `20260222000008_economy.sql` | wallets, transactions, deposit_requests, shop_items, gift_logs, withdrawal_requests; alters vip_subscriptions |
| `20260222000009_follows_bookmarks.sql` | follows, bookmarks |
| `20260222000010_nominations.sql` | nominations |
| `20260222000011_notifications.sql` | notifications |
| `20260222000012_ai_infrastructure.sql` | characters, novel_embeddings; relationship_graph + arc_timeline JSONB on novels |
| `20260222000013_chat_sessions.sql` | chat_sessions (RAG chat history, owner RLS) |
| `20260222000014_chapter_narrations.sql` | chapter_narrations (ElevenLabs audio cache, public read RLS); chapter-narrations Storage bucket |
| `20260222000015_arc_summaries_storage.sql` | arc-summaries Storage bucket (private, authenticated read); caches Gemini arc summaries |
