export interface AdminUser {
  id: string;
  username: string;
  role: "reader" | "uploader" | "admin";
  is_banned: boolean;
  ban_until: string | null;
  vip_tier: string;
  chapters_read: number;
  level: number;
  created_at: string;
}

export interface Report {
  id: string;
  reporter_id: string;
  target_type: "novel" | "chapter" | "comment" | "review" | "user";
  target_id: string;
  reason: string;
  status: "pending" | "resolved" | "dismissed";
  admin_note: string | null;
  created_at: string;
}

export interface Feedback {
  id: string;
  user_id: string | null;
  content: string;
  status: "open" | "reviewed" | "closed";
  admin_response: string | null;
  created_at: string;
}

export interface AdminDeposit {
  id: string;
  user_id: string;
  transfer_code: string;
  amount_vnd: number;
  lt_credited: number | null;
  status: "pending" | "completed" | "rejected";
  admin_note: string | null;
  confirmed_by: string | null;
  confirmed_at: string | null;
  created_at: string;
}

export interface AdminWithdrawal {
  id: string;
  user_id: string;
  tt_amount: number;
  vnd_amount: number;
  bank_info: {
    bank_name: string;
    account_number: string;
    account_holder: string;
  };
  status: "pending" | "completed" | "rejected";
  admin_note: string | null;
  processed_by: string | null;
  processed_at: string | null;
  created_at: string;
}
