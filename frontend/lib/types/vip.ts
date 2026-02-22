export interface VipSubscription {
  id: string;
  user_id: string;
  vip_tier: "pro" | "max";
  payment_method: "stripe" | "bank_transfer";
  status: "pending" | "active" | "cancelled" | "expired";
  starts_at: string | null;
  expires_at: string | null;
  amount_paid: number;
  created_at: string;
}

export interface SystemSettings {
  vip_pro_price_vnd: string;
  vip_max_price_vnd: string;
  vip_pro_price_usd_cents: string;
  vip_max_price_usd_cents: string;
  vip_duration_days: string;
  site_name: string;
  [key: string]: string;
}
