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
