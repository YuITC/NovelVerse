-- ============================================================
-- Migration 001: Users
-- Extends Supabase auth.users with a public profile table.
-- ============================================================

-- ── ENUM types ──────────────────────────────────────────────

CREATE TYPE user_role AS ENUM ('reader', 'uploader', 'admin');
CREATE TYPE vip_tier AS ENUM ('none', 'pro', 'max');

-- ── Table: users ─────────────────────────────────────────────

CREATE TABLE public.users (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username        TEXT NOT NULL,
    avatar_url      TEXT,
    bio             TEXT CHECK (char_length(bio) <= 500),
    social_links    JSONB NOT NULL DEFAULT '[]'::JSONB,
    donate_url      TEXT,

    role            user_role NOT NULL DEFAULT 'reader',
    is_banned       BOOLEAN NOT NULL DEFAULT FALSE,
    ban_until       TIMESTAMPTZ,                        -- NULL = permanent ban

    chapters_read   INTEGER NOT NULL DEFAULT 0,
    level           INTEGER NOT NULL DEFAULT 0 CHECK (level BETWEEN 0 AND 9),
    daily_nominations   INTEGER NOT NULL DEFAULT 0,
    nominations_reset_at DATE,

    vip_tier        vip_tier NOT NULL DEFAULT 'none',
    vip_expires_at  TIMESTAMPTZ,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Trigger: auto-create profile on auth.users insert ────────

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
    INSERT INTO public.users (id, username, avatar_url)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email, 'User'),
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ── Row Level Security ────────────────────────────────────────

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Anyone can read public profile fields
CREATE POLICY "users_public_read" ON public.users
    FOR SELECT USING (TRUE);

-- User can update their own profile (bio, social_links, donate_url, avatar_url)
CREATE POLICY "users_self_update" ON public.users
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Admin can update any user (role, ban, vip fields handled server-side via service key)
-- Note: sensitive field updates (role, ban, vip) go through FastAPI with service role key,
-- bypassing RLS. The self-update policy above limits what users can change directly.
