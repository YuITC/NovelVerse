-- M18: AI Narrator — chapter_narrations table + Supabase Storage bucket

-- Cache table for ElevenLabs-generated chapter audio
CREATE TABLE public.chapter_narrations (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID        NOT NULL REFERENCES public.chapters(id) ON DELETE CASCADE,
    status     TEXT        NOT NULL DEFAULT 'pending'
                           CHECK (status IN ('pending', 'ready', 'failed')),
    audio_url  TEXT,                          -- populated when status = 'ready'
    voice_id   TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(chapter_id)
);

CREATE INDEX chapter_narrations_chapter_idx ON public.chapter_narrations(chapter_id);

ALTER TABLE public.chapter_narrations ENABLE ROW LEVEL SECURITY;

-- Anyone can read narration status/audio_url (audio files are public)
CREATE POLICY "narrations_read" ON public.chapter_narrations
    FOR SELECT USING (true);

-- Supabase Storage bucket for MP3 audio files (public read)
INSERT INTO storage.buckets (id, name, public)
VALUES ('chapter-narrations', 'chapter-narrations', true)
ON CONFLICT DO NOTHING;

-- Public read policy for storage objects in this bucket
CREATE POLICY "narrations_storage_read" ON storage.objects
    FOR SELECT USING (bucket_id = 'chapter-narrations');
