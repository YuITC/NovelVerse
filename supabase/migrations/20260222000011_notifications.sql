-- ============================================================
-- Migration 011: Notifications
-- Phase 2 social feature: real-time event notifications
-- Notification types: new_chapter, reply_to_comment,
--                     comment_liked, gift_received
-- ============================================================

-- ── ENUM ─────────────────────────────────────────────────────

CREATE TYPE notification_type AS ENUM (
    'new_chapter',
    'reply_to_comment',
    'comment_liked',
    'gift_received'
);

-- ── Table: notifications ──────────────────────────────────────

CREATE TABLE public.notifications (
    id         UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID             NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    type       notification_type NOT NULL,
    payload    JSONB            NOT NULL DEFAULT '{}'::JSONB,
    read_at    TIMESTAMPTZ,                          -- NULL = unread
    created_at TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

-- Index for fast "unread count" and chronological listing per user
CREATE INDEX notifications_user_unread_idx ON public.notifications(user_id, read_at);
CREATE INDEX notifications_user_created_idx ON public.notifications(user_id, created_at DESC);

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- Users can only see (and manage) their own notifications
CREATE POLICY "notifications_owner" ON public.notifications
    FOR ALL USING (auth.uid() = user_id);

-- ── Trigger: new_chapter ──────────────────────────────────────
-- Fires after a chapter is published. Notifies all users who
-- have bookmarked the novel.

CREATE OR REPLACE FUNCTION public.notify_new_chapter()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
DECLARE
    v_novel_title TEXT;
BEGIN
    -- Only fire when chapter transitions to published
    IF NEW.status = 'published' AND NOT NEW.is_deleted THEN
        IF TG_OP = 'INSERT' OR OLD.status <> 'published' THEN
            -- Fetch novel title for the payload
            SELECT title INTO v_novel_title
            FROM public.novels
            WHERE id = NEW.novel_id;

            -- One notification per bookmarker
            INSERT INTO public.notifications (user_id, type, payload)
            SELECT
                b.user_id,
                'new_chapter',
                jsonb_build_object(
                    'novel_id',       NEW.novel_id,
                    'novel_title',    COALESCE(v_novel_title, ''),
                    'chapter_id',     NEW.id,
                    'chapter_number', NEW.chapter_number
                )
            FROM public.bookmarks b
            WHERE b.novel_id = NEW.novel_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER chapter_published_notification
    AFTER INSERT OR UPDATE OF status ON public.chapters
    FOR EACH ROW EXECUTE FUNCTION public.notify_new_chapter();

-- ── Trigger: reply_to_comment ─────────────────────────────────
-- Fires after a reply comment is inserted. Notifies the author
-- of the parent comment (unless replying to themselves).

CREATE OR REPLACE FUNCTION public.notify_reply_to_comment()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
DECLARE
    v_parent_author UUID;
    v_replier_username TEXT;
BEGIN
    IF NEW.parent_id IS NOT NULL AND NOT NEW.is_deleted THEN
        -- Get parent comment author
        SELECT user_id INTO v_parent_author
        FROM public.comments
        WHERE id = NEW.parent_id;

        -- Skip self-reply notifications
        IF v_parent_author IS NOT NULL AND v_parent_author <> NEW.user_id THEN
            SELECT username INTO v_replier_username
            FROM public.users
            WHERE id = NEW.user_id;

            INSERT INTO public.notifications (user_id, type, payload)
            VALUES (
                v_parent_author,
                'reply_to_comment',
                jsonb_build_object(
                    'comment_id',        NEW.id,
                    'novel_id',          NEW.novel_id,
                    'replier_username',  COALESCE(v_replier_username, 'Ai đó')
                )
            );
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER comment_reply_notification
    AFTER INSERT ON public.comments
    FOR EACH ROW EXECUTE FUNCTION public.notify_reply_to_comment();

-- ── Trigger: comment_liked ────────────────────────────────────
-- Fires after a comment_like is inserted. Notifies the comment
-- author (unless liking their own comment).

CREATE OR REPLACE FUNCTION public.notify_comment_liked()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
DECLARE
    v_comment_author UUID;
    v_liker_username TEXT;
BEGIN
    -- Get comment author
    SELECT user_id INTO v_comment_author
    FROM public.comments
    WHERE id = NEW.comment_id;

    -- Skip self-like notifications
    IF v_comment_author IS NOT NULL AND v_comment_author <> NEW.user_id THEN
        SELECT username INTO v_liker_username
        FROM public.users
        WHERE id = NEW.user_id;

        INSERT INTO public.notifications (user_id, type, payload)
        VALUES (
            v_comment_author,
            'comment_liked',
            jsonb_build_object(
                'comment_id',     NEW.comment_id,
                'liker_username', COALESCE(v_liker_username, 'Ai đó')
            )
        );
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER comment_liked_notification
    AFTER INSERT ON public.comment_likes
    FOR EACH ROW EXECUTE FUNCTION public.notify_comment_liked();

-- ── Trigger: gift_received ────────────────────────────────────
-- Fires after a gift_log is inserted. Notifies the receiver.

CREATE OR REPLACE FUNCTION public.notify_gift_received()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
DECLARE
    v_item_name TEXT;
BEGIN
    SELECT name INTO v_item_name
    FROM public.shop_items
    WHERE id = NEW.item_id;

    INSERT INTO public.notifications (user_id, type, payload)
    VALUES (
        NEW.receiver_id,
        'gift_received',
        jsonb_build_object(
            'sender_id',   NEW.sender_id,
            'item_name',   COALESCE(v_item_name, 'Quà'),
            'tt_credited', NEW.tt_credited
        )
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER gift_received_notification
    AFTER INSERT ON public.gift_logs
    FOR EACH ROW EXECUTE FUNCTION public.notify_gift_received();
