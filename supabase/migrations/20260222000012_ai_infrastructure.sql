-- ============================================================
-- Migration 012: AI Infrastructure
-- Phase 3: Vector storage + character extraction scaffolding
-- New tables: characters, novel_embeddings
-- Alters: novels (JSONB columns for M19 graph/timeline data)
-- ============================================================

-- ── Table: characters ────────────────────────────────────────
-- One row per named character discovered in a novel's chapters.
-- Populated asynchronously by character_service after each chapter publish.

CREATE TABLE public.characters (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    novel_id      UUID        NOT NULL REFERENCES public.novels(id) ON DELETE CASCADE,
    name          TEXT        NOT NULL,
    description   TEXT,
    traits        JSONB       NOT NULL DEFAULT '[]'::JSONB,
    first_chapter INTEGER,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (novel_id, name)
);

CREATE INDEX characters_novel_idx ON public.characters(novel_id);

ALTER TABLE public.characters ENABLE ROW LEVEL SECURITY;

CREATE POLICY "characters_public_read" ON public.characters
    FOR SELECT USING (TRUE);

-- ── Table: novel_embeddings ───────────────────────────────────
-- Maps each embedded text chunk to its Qdrant vector ID.
-- Populated asynchronously by embedding_service after each chapter publish.

CREATE TABLE public.novel_embeddings (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id      UUID        NOT NULL REFERENCES public.chapters(id) ON DELETE CASCADE,
    chunk_index     INTEGER     NOT NULL,
    content_preview TEXT        NOT NULL,
    vector_id       TEXT        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (chapter_id, chunk_index)
);

CREATE INDEX novel_embeddings_chapter_idx ON public.novel_embeddings(chapter_id);

ALTER TABLE public.novel_embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "embeddings_admin_read" ON public.novel_embeddings
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

-- ── Alter: novels — JSONB columns for M19 ────────────────────
ALTER TABLE public.novels
    ADD COLUMN IF NOT EXISTS relationship_graph JSONB,
    ADD COLUMN IF NOT EXISTS arc_timeline       JSONB;

-- ── Auto-update updated_at on characters ─────────────────────
-- update_updated_at() function already exists (defined in migration 002)
CREATE TRIGGER characters_updated_at
    BEFORE UPDATE ON public.characters
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
