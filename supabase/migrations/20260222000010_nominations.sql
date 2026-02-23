-- ============================================================
-- Migration 010: Nominations
-- Phase 2 social feature: daily novel nominations + leaderboards
-- Note: users.daily_nominations and users.nominations_reset_at
--       already exist (migration 001, lines 27-28).
-- ============================================================

-- ── Table: nominations ───────────────────────────────────────
-- One row per (user, novel, day). Composite PK prevents double-voting.

CREATE TABLE public.nominations (
    user_id    UUID    NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    novel_id   UUID    NOT NULL REFERENCES public.novels(id) ON DELETE CASCADE,
    period     DATE    NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, novel_id, period)
);

CREATE INDEX nominations_novel_period_idx ON public.nominations(novel_id, period);

ALTER TABLE public.nominations ENABLE ROW LEVEL SECURITY;

-- Users can manage their own nominations; anyone can read (for leaderboard aggregation)
CREATE POLICY "nominations_owner_write" ON public.nominations
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "nominations_public_read" ON public.nominations
    FOR SELECT USING (TRUE);

-- ── Denormalized counter on novels ───────────────────────────
-- Tracks all-time total nominations for display on novel cards.

ALTER TABLE public.novels
    ADD COLUMN IF NOT EXISTS nomination_count INTEGER NOT NULL DEFAULT 0;
