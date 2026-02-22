-- ── Table: comments ────────────────────────────────────────────
CREATE TABLE public.comments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    novel_id    UUID NOT NULL REFERENCES public.novels(id) ON DELETE CASCADE,
    chapter_id  UUID REFERENCES public.chapters(id) ON DELETE CASCADE,  -- NULL = novel-level
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    parent_id   UUID REFERENCES public.comments(id) ON DELETE CASCADE,  -- NULL = top-level
    content     TEXT NOT NULL,
    likes       INTEGER NOT NULL DEFAULT 0,
    is_deleted  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX comments_novel_idx ON public.comments (novel_id, created_at DESC);
CREATE INDEX comments_chapter_idx ON public.comments (chapter_id, created_at DESC) WHERE chapter_id IS NOT NULL;
CREATE INDEX comments_parent_idx ON public.comments (parent_id) WHERE parent_id IS NOT NULL;

CREATE TRIGGER comments_updated_at
    BEFORE UPDATE ON public.comments
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- Auto-update novels.total_comments
CREATE OR REPLACE FUNCTION public.update_novel_comment_count()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE public.novels SET total_comments = total_comments + 1 WHERE id = NEW.novel_id;
    ELSIF TG_OP = 'UPDATE' AND NEW.is_deleted = TRUE AND OLD.is_deleted = FALSE THEN
        UPDATE public.novels SET total_comments = GREATEST(total_comments - 1, 0) WHERE id = NEW.novel_id;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER comments_count_trigger
    AFTER INSERT OR UPDATE ON public.comments
    FOR EACH ROW EXECUTE FUNCTION public.update_novel_comment_count();

ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "comments_public_read" ON public.comments FOR SELECT USING (is_deleted = FALSE);
CREATE POLICY "comments_auth_insert" ON public.comments FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "comments_owner_update" ON public.comments FOR UPDATE USING (
    auth.uid() = user_id
    OR EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
);

-- ── Table: comment_likes ────────────────────────────────────────
CREATE TABLE public.comment_likes (
    user_id    UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    comment_id UUID NOT NULL REFERENCES public.comments(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, comment_id)
);

ALTER TABLE public.comment_likes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "comment_likes_owner" ON public.comment_likes FOR ALL USING (auth.uid() = user_id);

-- ── Table: reviews ──────────────────────────────────────────────
CREATE TABLE public.reviews (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    novel_id   UUID NOT NULL REFERENCES public.novels(id) ON DELETE CASCADE,
    user_id    UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    rating     SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, novel_id)
);

CREATE INDEX reviews_novel_idx ON public.reviews (novel_id);

CREATE TRIGGER reviews_updated_at
    BEFORE UPDATE ON public.reviews
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- Auto-update novels.avg_rating and novels.rating_count
CREATE OR REPLACE FUNCTION public.update_novel_rating()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    UPDATE public.novels
    SET
        avg_rating   = (SELECT AVG(rating)::NUMERIC(3,2) FROM public.reviews WHERE novel_id = COALESCE(NEW.novel_id, OLD.novel_id)),
        rating_count = (SELECT COUNT(*) FROM public.reviews WHERE novel_id = COALESCE(NEW.novel_id, OLD.novel_id))
    WHERE id = COALESCE(NEW.novel_id, OLD.novel_id);
    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER reviews_rating_trigger
    AFTER INSERT OR UPDATE OR DELETE ON public.reviews
    FOR EACH ROW EXECUTE FUNCTION public.update_novel_rating();

ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;
CREATE POLICY "reviews_public_read" ON public.reviews FOR SELECT USING (TRUE);
CREATE POLICY "reviews_auth_insert" ON public.reviews FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "reviews_owner_update" ON public.reviews FOR UPDATE USING (auth.uid() = user_id);
