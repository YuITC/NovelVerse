-- ── ENUM ─────────────────────────────────────────────────────
CREATE TYPE chapter_status AS ENUM ('draft', 'scheduled', 'published');

-- ── Table: chapters ───────────────────────────────────────────
CREATE TABLE public.chapters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    novel_id        UUID NOT NULL REFERENCES public.novels(id) ON DELETE CASCADE,
    chapter_number  INTEGER NOT NULL,
    title           TEXT,
    content         TEXT NOT NULL DEFAULT '',
    word_count      INTEGER NOT NULL DEFAULT 0,
    status          chapter_status NOT NULL DEFAULT 'draft',
    publish_at      TIMESTAMPTZ,    -- future public date (VIP reads before this)
    published_at    TIMESTAMPTZ,    -- when it was actually published
    views           INTEGER NOT NULL DEFAULT 0,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (novel_id, chapter_number)
);

CREATE INDEX chapters_novel_num_idx ON public.chapters (novel_id, chapter_number);
CREATE INDEX chapters_novel_status_idx ON public.chapters (novel_id, status, publish_at);

-- ── Triggers: keep novels.total_chapters and novels.updated_at in sync ──
CREATE OR REPLACE FUNCTION public.update_novel_chapter_count()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.status = 'published' AND NOT NEW.is_deleted THEN
        UPDATE public.novels SET total_chapters = total_chapters + 1, updated_at = NOW()
        WHERE id = NEW.novel_id;
    ELSIF TG_OP = 'UPDATE' THEN
        -- Recalculate to stay accurate
        UPDATE public.novels
        SET total_chapters = (
            SELECT COUNT(*) FROM public.chapters
            WHERE novel_id = NEW.novel_id AND status = 'published' AND is_deleted = FALSE
        ),
        updated_at = NOW()
        WHERE id = NEW.novel_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE public.novels
        SET total_chapters = (
            SELECT COUNT(*) FROM public.chapters
            WHERE novel_id = OLD.novel_id AND status = 'published' AND is_deleted = FALSE
        )
        WHERE id = OLD.novel_id;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER chapters_count_trigger
    AFTER INSERT OR UPDATE OR DELETE ON public.chapters
    FOR EACH ROW EXECUTE FUNCTION public.update_novel_chapter_count();

CREATE TRIGGER chapters_updated_at
    BEFORE UPDATE ON public.chapters
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- ── RLS for chapters ──────────────────────────────────────────
ALTER TABLE public.chapters ENABLE ROW LEVEL SECURITY;

-- Public read policy with VIP gating:
-- A chapter is readable if:
--   1. status = 'published' AND (publish_at IS NULL OR publish_at <= now())  → everyone
--   2. status = 'published' AND publish_at > now() AND user is VIP pro/max   → early access
--   3. user is the novel's uploader                                           → always
--   4. user is admin                                                          → always
CREATE POLICY "chapters_read" ON public.chapters FOR SELECT USING (
    is_deleted = FALSE AND (
        -- Published and past or no public date → everyone
        (status = 'published' AND (publish_at IS NULL OR publish_at <= NOW()))
        -- Published but scheduled → VIP early access
        OR (status = 'published' AND publish_at > NOW() AND EXISTS (
            SELECT 1 FROM public.users
            WHERE id = auth.uid() AND vip_tier IN ('pro', 'max')
        ))
        -- Novel owner can always read
        OR EXISTS (
            SELECT 1 FROM public.novels
            WHERE id = chapters.novel_id AND uploader_id = auth.uid()
        )
        -- Admin can always read
        OR EXISTS (
            SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'
        )
    )
);

CREATE POLICY "chapters_owner_write" ON public.chapters FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM public.novels WHERE id = novel_id AND uploader_id = auth.uid())
);
CREATE POLICY "chapters_owner_update" ON public.chapters FOR UPDATE USING (
    EXISTS (SELECT 1 FROM public.novels WHERE id = novel_id AND uploader_id = auth.uid())
    OR EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
);

-- ── Table: reading_progress ───────────────────────────────────
CREATE TABLE public.reading_progress (
    user_id             UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    novel_id            UUID NOT NULL REFERENCES public.novels(id) ON DELETE CASCADE,
    last_chapter_read   INTEGER NOT NULL DEFAULT 0,
    chapters_read_list  INTEGER[] NOT NULL DEFAULT '{}',
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, novel_id)
);

CREATE INDEX reading_progress_user_idx ON public.reading_progress (user_id);

ALTER TABLE public.reading_progress ENABLE ROW LEVEL SECURITY;
CREATE POLICY "reading_progress_owner" ON public.reading_progress
    FOR ALL USING (auth.uid() = user_id);
