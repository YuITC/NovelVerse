-- ── ENUMs ─────────────────────────────────────────────────────
CREATE TYPE crawl_status AS ENUM ('pending', 'crawled', 'translated', 'published', 'skipped');
CREATE TYPE translation_method_enum AS ENUM ('opencc', 'gemini', 'manual');

-- ── Table: crawl_sources ────────────────────────────────────────
-- One source per novel: the URL of the book's chapter listing on a partner site.
CREATE TABLE public.crawl_sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    novel_id        UUID NOT NULL REFERENCES public.novels(id) ON DELETE CASCADE,
    uploader_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    source_url      TEXT NOT NULL,    -- e.g. https://biquge.info/book/12345/
    last_chapter    INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (novel_id, source_url)
);

CREATE INDEX crawl_sources_uploader_idx ON public.crawl_sources (uploader_id);
CREATE INDEX crawl_sources_novel_idx ON public.crawl_sources (novel_id);

ALTER TABLE public.crawl_sources ENABLE ROW LEVEL SECURITY;
CREATE POLICY "crawl_sources_owner" ON public.crawl_sources
    FOR ALL USING (auth.uid() = uploader_id);

-- ── Table: crawl_queue ──────────────────────────────────────────
CREATE TABLE public.crawl_queue (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crawl_source_id     UUID NOT NULL REFERENCES public.crawl_sources(id) ON DELETE CASCADE,
    novel_id            UUID NOT NULL REFERENCES public.novels(id) ON DELETE CASCADE,
    chapter_number      INTEGER NOT NULL,
    raw_content         TEXT,
    translated_content  TEXT,
    translation_method  translation_method_enum,
    status              crawl_status NOT NULL DEFAULT 'pending',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (novel_id, chapter_number)
);

CREATE INDEX crawl_queue_source_idx ON public.crawl_queue (crawl_source_id, status);
CREATE INDEX crawl_queue_novel_idx ON public.crawl_queue (novel_id, chapter_number);

CREATE TRIGGER crawl_queue_updated_at
    BEFORE UPDATE ON public.crawl_queue
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

ALTER TABLE public.crawl_queue ENABLE ROW LEVEL SECURITY;
-- Uploader sees their own novel's queue items
CREATE POLICY "crawl_queue_owner" ON public.crawl_queue
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.crawl_sources cs
            WHERE cs.id = crawl_source_id AND cs.uploader_id = auth.uid()
        )
    );
