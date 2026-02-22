-- vip_subscriptions table
CREATE TYPE payment_method_enum AS ENUM ('stripe', 'bank_transfer');
CREATE TYPE sub_status_enum AS ENUM ('pending', 'active', 'cancelled', 'expired');

CREATE TABLE public.vip_subscriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    vip_tier        vip_tier NOT NULL,  -- 'pro' or 'max' (reuse existing enum)
    payment_method  payment_method_enum NOT NULL,
    stripe_session_id TEXT,
    stripe_subscription_id TEXT,
    amount_paid     INTEGER NOT NULL DEFAULT 0,  -- in VND (bank) or cents (stripe)
    status          sub_status_enum NOT NULL DEFAULT 'pending',
    starts_at       TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    confirmed_by    UUID REFERENCES public.users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX vip_subscriptions_user_idx ON public.vip_subscriptions (user_id);
CREATE INDEX vip_subscriptions_status_idx ON public.vip_subscriptions (status);

ALTER TABLE public.vip_subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "vip_sub_own_read" ON public.vip_subscriptions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "vip_sub_insert" ON public.vip_subscriptions FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "vip_sub_admin" ON public.vip_subscriptions FOR ALL USING (
    EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
);

-- system_settings table
CREATE TABLE public.system_settings (
    key     TEXT PRIMARY KEY,
    value   JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.system_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "settings_public_read" ON public.system_settings FOR SELECT USING (TRUE);
CREATE POLICY "settings_admin_write" ON public.system_settings FOR ALL USING (
    EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
);

-- Seed default system settings
INSERT INTO public.system_settings (key, value) VALUES
    ('vip_pro_price_vnd', '99000'),
    ('vip_max_price_vnd', '199000'),
    ('vip_pro_price_usd_cents', '499'),
    ('vip_max_price_usd_cents', '999'),
    ('vip_duration_days', '30'),
    ('donation_commission_pct', '10'),
    ('site_name', '"NovelVerse"'),
    ('maintenance_mode', 'false');

-- Trigger for vip_subscriptions.updated_at
CREATE TRIGGER vip_sub_updated_at
    BEFORE UPDATE ON public.vip_subscriptions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
