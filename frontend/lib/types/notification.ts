export interface Notification {
  id: string;
  user_id: string;
  type: "new_chapter" | "reply_to_comment" | "comment_liked" | "gift_received";
  payload: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
}

export interface UnreadCount {
  count: number;
}
