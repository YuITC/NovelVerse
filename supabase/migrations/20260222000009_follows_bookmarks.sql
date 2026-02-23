-- Migration 009: Follows + Bookmarks

-- 1. follows table (reader → uploader)
CREATE TABLE public.follows (
    follower_id  UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    followee_id  UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (follower_id, followee_id),
    CHECK (follower_id != followee_id)
);

CREATE INDEX follows_followee_idx ON public.follows(followee_id);
CREATE INDEX follows_follower_idx ON public.follows(follower_id);

ALTER TABLE public.follows ENABLE ROW LEVEL SECURITY;
CREATE POLICY "follows_owner_read"  ON public.follows FOR SELECT USING (auth.uid() = follower_id);
CREATE POLICY "follows_owner_write" ON public.follows FOR ALL    USING (auth.uid() = follower_id);

-- 2. bookmarks table (user → novel)
CREATE TABLE public.bookmarks (
    user_id    UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    novel_id   UUID NOT NULL REFERENCES public.novels(id) ON DELETE CASCADE,
    added_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, novel_id)
);

CREATE INDEX bookmarks_user_idx ON public.bookmarks(user_id);

ALTER TABLE public.bookmarks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "bookmarks_owner" ON public.bookmarks FOR ALL USING (auth.uid() = user_id);

-- 3. Add follower_count denorm column to users
ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS follower_count INTEGER NOT NULL DEFAULT 0;
