-- reports
CREATE TYPE report_target_type AS ENUM ('novel', 'chapter', 'comment', 'review', 'user');
CREATE TYPE report_status AS ENUM ('pending', 'resolved', 'dismissed');

CREATE TABLE public.reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    target_type     report_target_type NOT NULL,
    target_id       UUID NOT NULL,
    reason          TEXT NOT NULL,
    status          report_status NOT NULL DEFAULT 'pending',
    admin_note      TEXT,
    resolved_by     UUID REFERENCES public.users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX reports_status_idx ON public.reports (status);
CREATE INDEX reports_reporter_idx ON public.reports (reporter_id);

ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "reports_own_insert" ON public.reports FOR INSERT WITH CHECK (auth.uid() = reporter_id);
CREATE POLICY "reports_own_read" ON public.reports FOR SELECT USING (auth.uid() = reporter_id);
CREATE POLICY "reports_admin_all" ON public.reports FOR ALL USING (
    EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
);

-- feedbacks
CREATE TYPE feedback_status AS ENUM ('open', 'reviewed', 'closed');

CREATE TABLE public.feedbacks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES public.users(id) ON DELETE SET NULL,
    content         TEXT NOT NULL,
    status          feedback_status NOT NULL DEFAULT 'open',
    admin_response  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX feedbacks_status_idx ON public.feedbacks (status);

ALTER TABLE public.feedbacks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "feedbacks_insert" ON public.feedbacks FOR INSERT WITH CHECK (TRUE);  -- allow anon
CREATE POLICY "feedbacks_own_read" ON public.feedbacks FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "feedbacks_admin_all" ON public.feedbacks FOR ALL USING (
    EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
);

-- triggers
CREATE TRIGGER reports_updated_at
    BEFORE UPDATE ON public.reports
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE TRIGGER feedbacks_updated_at
    BEFORE UPDATE ON public.feedbacks
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
