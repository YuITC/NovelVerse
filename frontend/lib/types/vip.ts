export interface VipSubscription {
  id: string;
  user_id: string;
  vip_tier: "pro" | "max";
  lt_spent: number | null;
  status: "active" | "cancelled" | "expired";
  starts_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface SystemSettings {
  vip_pro_price_lt: string;
  vip_max_price_lt: string;
  lt_per_vnd: string;
  tt_per_lt: string;
  vip_duration_days: string;
  min_deposit_vnd: string;
  site_name: string;
  [key: string]: string;
}
