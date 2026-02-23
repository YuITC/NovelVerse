-- Migration: M17 — Chat with Characters
-- Creates chat_sessions table for storing RAG chat history

CREATE TABLE public.chat_sessions (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    novel_id     UUID        NOT NULL REFERENCES public.novels(id) ON DELETE CASCADE,
    character_id UUID        NOT NULL REFERENCES public.characters(id) ON DELETE CASCADE,
    messages     JSONB       NOT NULL DEFAULT '[]'::JSONB,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX chat_sessions_user_idx  ON public.chat_sessions(user_id);
CREATE INDEX chat_sessions_novel_idx ON public.chat_sessions(novel_id);

ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;

-- Only the session owner can read or write their own sessions
CREATE POLICY "chat_sessions_owner" ON public.chat_sessions
    USING     (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());
