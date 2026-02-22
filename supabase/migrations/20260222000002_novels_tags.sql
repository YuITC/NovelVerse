-- ENUM
CREATE TYPE novel_status AS ENUM ('ongoing', 'completed', 'dropped');

-- Enable unaccent for Vietnamese full-text search
CREATE EXTENSION IF NOT EXISTS unaccent;

-- novels table
CREATE TABLE public.novels (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT NOT NULL,
    original_title  TEXT,
    author          TEXT NOT NULL,
    description     TEXT,
    cover_url       TEXT,
    status          novel_status NOT NULL DEFAULT 'ongoing',
    uploader_id     UUID NOT NULL REFERENCES public.users(id),

    total_chapters  INTEGER NOT NULL DEFAULT 0,
    total_views     INTEGER NOT NULL DEFAULT 0,
    avg_rating      DECIMAL(3,2) NOT NULL DEFAULT 0,
    rating_count    INTEGER NOT NULL DEFAULT 0,
    total_comments  INTEGER NOT NULL DEFAULT 0,

    is_pinned       BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,

    search_vector   TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('simple', unaccent(coalesce(title, ''))), 'A') ||
        setweight(to_tsvector('simple', unaccent(coalesce(author, ''))), 'B') ||
        setweight(to_tsvector('simple', unaccent(coalesce(original_title, ''))), 'C')
    ) STORED,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX novels_search_idx ON public.novels USING GIN (search_vector);
CREATE INDEX novels_uploader_idx ON public.novels (uploader_id);
CREATE INDEX novels_updated_idx ON public.novels (updated_at DESC);
CREATE INDEX novels_pinned_idx ON public.novels (is_pinned) WHERE is_pinned = TRUE AND is_deleted = FALSE;

-- RLS for novels
ALTER TABLE public.novels ENABLE ROW LEVEL SECURITY;
CREATE POLICY "novels_public_read" ON public.novels FOR SELECT USING (is_deleted = FALSE);
CREATE POLICY "novels_uploader_insert" ON public.novels FOR INSERT WITH CHECK (auth.uid() = uploader_id);
CREATE POLICY "novels_owner_update" ON public.novels FOR UPDATE USING (auth.uid() = uploader_id OR EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'));

-- tags table
CREATE TABLE public.tags (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name    TEXT NOT NULL UNIQUE,
    slug    TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.tags ENABLE ROW LEVEL SECURITY;
CREATE POLICY "tags_public_read" ON public.tags FOR SELECT USING (TRUE);
CREATE POLICY "tags_admin_write" ON public.tags FOR ALL USING (EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'));

-- novel_tags junction
CREATE TABLE public.novel_tags (
    novel_id    UUID NOT NULL REFERENCES public.novels(id) ON DELETE CASCADE,
    tag_id      UUID NOT NULL REFERENCES public.tags(id) ON DELETE CASCADE,
    PRIMARY KEY (novel_id, tag_id)
);

ALTER TABLE public.novel_tags ENABLE ROW LEVEL SECURITY;
CREATE POLICY "novel_tags_public_read" ON public.novel_tags FOR SELECT USING (TRUE);
CREATE POLICY "novel_tags_owner_write" ON public.novel_tags FOR ALL USING (
    EXISTS (SELECT 1 FROM public.novels WHERE id = novel_id AND uploader_id = auth.uid())
    OR EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
);

-- Seed default tags (18 tags)
INSERT INTO public.tags (name, slug) VALUES
    ('Tu tiên', 'tu-tien'),
    ('Huyền huyễn', 'huyen-huyen'),
    ('Ngôn tình', 'ngon-tinh'),
    ('Kiếm hiệp', 'kiem-hiep'),
    ('Đô thị', 'do-thi'),
    ('Khoa huyễn', 'khoa-huyen'),
    ('Dị giới', 'di-gioi'),
    ('Lịch sử', 'lich-su'),
    ('Game', 'game'),
    ('Thể thao', 'the-thao'),
    ('Hào môn', 'hao-mon'),
    ('Trọng sinh', 'trong-sinh'),
    ('Xuyên không', 'xuyen-khong'),
    ('Học đường', 'hoc-duong'),
    ('Quân sự', 'quan-su'),
    ('Linh khí phục hưng', 'linh-khi-phuc-hung'),
    ('Hệ thống', 'he-thong'),
    ('Đam mỹ', 'dam-my');

-- Update trigger for novels.updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;

CREATE TRIGGER novels_updated_at
    BEFORE UPDATE ON public.novels
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
