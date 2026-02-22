-- Migration 008: Virtual Economy System

-- 1. Alter vip_subscriptions: drop Stripe-specific columns
ALTER TABLE vip_subscriptions
    DROP COLUMN IF EXISTS stripe_session_id,
    DROP COLUMN IF EXISTS stripe_subscription_id,
    DROP COLUMN IF EXISTS confirmed_by,
    DROP COLUMN IF EXISTS payment_method;

-- Rename amount_paid to lt_spent (now stores Linh Thach amount)
ALTER TABLE vip_subscriptions RENAME COLUMN amount_paid TO lt_spent;
ALTER TABLE vip_subscriptions ALTER COLUMN lt_spent TYPE NUMERIC(14,2) USING lt_spent::NUMERIC(14,2);

-- Drop payment_method_enum (no longer used)
DROP TYPE IF EXISTS payment_method_enum;

-- 2. Update system_settings: replace Stripe-era prices with LT prices
DELETE FROM system_settings WHERE key IN (
    'vip_pro_price_vnd',
    'vip_max_price_vnd',
    'vip_pro_price_usd_cents',
    'vip_max_price_usd_cents',
    'donation_commission_pct'
);

INSERT INTO system_settings (key, value) VALUES
    ('vip_pro_price_lt',        '50000'),
    ('vip_max_price_lt',        '100000'),
    ('lt_per_vnd',              '0.95'),
    ('tt_per_lt',               '0.95'),
    ('vnd_per_tt',              '1'),
    ('min_deposit_vnd',         '5000'),
    ('min_withdrawal_vnd',      '5000'),
    ('max_withdrawals_per_month', '2')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- 3. wallets table
CREATE TABLE wallets (
    user_id     UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    linh_thach  NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (linh_thach >= 0),
    tien_thach  NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (tien_thach >= 0),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER wallets_updated_at
    BEFORE UPDATE ON wallets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "wallets_owner_read" ON wallets FOR SELECT USING (auth.uid() = user_id);
-- writes only via service role (no direct user writes)

-- Auto-create wallet when user is created
CREATE OR REPLACE FUNCTION create_wallet_for_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO wallets (user_id) VALUES (NEW.id) ON CONFLICT DO NOTHING;
    RETURN NEW;
END;
$$;

CREATE TRIGGER auto_create_wallet
    AFTER INSERT ON users
    FOR EACH ROW EXECUTE FUNCTION create_wallet_for_new_user();

-- 4. transactions table (unified ledger)
CREATE TABLE transactions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    currency_type       TEXT NOT NULL CHECK (currency_type IN ('linh_thach', 'tien_thach')),
    amount              NUMERIC(14,2) NOT NULL,
    balance_after       NUMERIC(14,2) NOT NULL,
    exchange_rate       NUMERIC(8,4),
    transaction_type    TEXT NOT NULL CHECK (transaction_type IN (
                            'deposit', 'vip_purchase', 'item_purchase',
                            'gift_sent', 'gift_received', 'withdrawal')),
    status              TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('completed', 'pending', 'failed', 'rejected')),
    related_entity_type TEXT,
    related_entity_id   UUID,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX transactions_user_id_idx ON transactions(user_id);
CREATE INDEX transactions_created_at_idx ON transactions(created_at DESC);

ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "transactions_owner_read" ON transactions FOR SELECT USING (auth.uid() = user_id);

-- 5. deposit_requests table
CREATE TABLE deposit_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transfer_code   TEXT UNIQUE NOT NULL,
    amount_vnd      INTEGER NOT NULL CHECK (amount_vnd >= 5000),
    lt_credited     NUMERIC(14,2),
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'rejected')),
    admin_note      TEXT,
    confirmed_by    UUID REFERENCES users(id),
    confirmed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER deposit_requests_updated_at
    BEFORE UPDATE ON deposit_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

ALTER TABLE deposit_requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY "deposit_requests_owner_read" ON deposit_requests FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "deposit_requests_owner_insert" ON deposit_requests FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "deposit_requests_admin_all" ON deposit_requests FOR ALL USING (
    EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
);

-- 6. shop_items table
CREATE TABLE shop_items (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    price_lt    NUMERIC(14,2) NOT NULL CHECK (price_lt > 0),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE shop_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "shop_items_public_read" ON shop_items FOR SELECT USING (is_active = TRUE);
CREATE POLICY "shop_items_admin_all" ON shop_items FOR ALL USING (
    EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
);

-- Seed shop items (all 10 from spec)
INSERT INTO shop_items (name, price_lt, sort_order) VALUES
    ('Tẩy Tủy Dịch',    1000,   1),
    ('Trúc Cơ Đan',    5000,   2),
    ('Dung Đan Quyết',    10000,   3),
    ('Khai Anh Pháp',    20000,   4),
    ('Dưỡng Thần Hương',    30000,   5),
    ('Hư Không Thạch',    40000,   6),
    ('Đạo Nguyên Châu',    50000,   7),
    ('Đại Đạo Bia',    70000,   8),
    ('Độ Kiếp Phù',    100000,   9),
    ('Chân Tiên Lệnh',    200000,   10);

-- 7. gift_logs table
CREATE TABLE gift_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id         UUID NOT NULL REFERENCES shop_items(id),
    lt_spent        NUMERIC(14,2) NOT NULL,
    tt_credited     NUMERIC(14,2) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX gift_logs_sender_idx ON gift_logs(sender_id);
CREATE INDEX gift_logs_receiver_idx ON gift_logs(receiver_id);

ALTER TABLE gift_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "gift_logs_sender_read" ON gift_logs FOR SELECT USING (auth.uid() = sender_id);
CREATE POLICY "gift_logs_receiver_read" ON gift_logs FOR SELECT USING (auth.uid() = receiver_id);

-- 8. withdrawal_requests table
CREATE TABLE withdrawal_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tt_amount       NUMERIC(14,2) NOT NULL CHECK (tt_amount >= 5000),
    vnd_amount      NUMERIC(14,2) NOT NULL,
    bank_info       JSONB NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'rejected')),
    admin_note      TEXT,
    processed_by    UUID REFERENCES users(id),
    processed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX withdrawal_requests_user_id_idx ON withdrawal_requests(user_id);
CREATE INDEX withdrawal_requests_status_idx ON withdrawal_requests(status);

CREATE TRIGGER withdrawal_requests_updated_at
    BEFORE UPDATE ON withdrawal_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

ALTER TABLE withdrawal_requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY "withdrawal_requests_owner_read" ON withdrawal_requests FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "withdrawal_requests_owner_insert" ON withdrawal_requests FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "withdrawal_requests_admin_all" ON withdrawal_requests FOR ALL USING (
    EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
);
