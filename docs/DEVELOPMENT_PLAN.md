# NovelVerse — Development Plan

> Living document. Last updated: 2026-02-22.
> Phase 1 MVP is complete (8 milestones, 135 backend tests, 25+ frontend routes).

---

## Current Status

| Phase | Status | Milestones |
|-------|--------|------------|
| Phase 1 MVP | ✅ Complete | M0–M8 |
| Phase 1 Patch: Economy | 🔄 In progress | M9–M11 |
| Phase 2: Social Features | 🔜 Planned | M12–M15 |
| Phase 3: AI Features | 🔜 Planned | M16–M18 |

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

### Milestone 12 — Follows + Bookmarks

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

### Milestone 13 — Nominations + Leaderboards

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

### Milestone 14 — Real-time Notifications

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

### Milestone 15 — CI/CD + Quality

**15.1 — GitHub Actions**
- `.github/workflows/backend.yml`: lint (ruff), type check (mypy), pytest on PR
- `.github/workflows/frontend.yml`: `npm run build`, `npm run lint` on PR
- Auto-deploy: push to `main` → Railway (backend) + Vercel (frontend)

**15.2 — Code quality**
- Add `ruff` linting config to `pyproject.toml`
- Add `mypy` type checking
- Playwright E2E tests for critical user journeys (reader, uploader, admin)

---

## Phase 3: AI Features

~8-12 weeks. Requires Qdrant Cloud, Gemini API key, ElevenLabs API key.

### Milestone 16 — Vector Infrastructure

**16.1 — New tables**
- `characters` (novel_id, name, description, traits JSONB)
- `novel_embeddings` (chapter_id, chunk_index, content_preview, vector_id)

**16.2 — Embedding pipeline**
- Trigger on chapter publish → chunk content → embed via Gemini `text-embedding-004`
- Store vector IDs in `novel_embeddings`, vectors in Qdrant collection per novel

**16.3 — Character extraction**
- Background job: parse chapters for character mentions → populate `characters` table

---

### Milestone 17 — Chat with Characters (RAG)

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

### Milestone 18 — AI Narrator (TTS)

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
| `20260222000009_follows_bookmarks.sql` | *(Phase 2)* follows, bookmarks |
| `20260222000010_nominations.sql` | *(Phase 2)* nominations |
| `20260222000011_notifications.sql` | *(Phase 2)* notifications |
