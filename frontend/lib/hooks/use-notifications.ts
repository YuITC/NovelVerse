"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import type { UnreadCount } from "@/lib/types/notification";

const NOTIFICATION_LABELS: Record<string, string> = {
  new_chapter: "Chương mới vừa được đăng!",
  reply_to_comment: "Ai đó đã trả lời bình luận của bạn",
  comment_liked: "Bình luận của bạn nhận được lượt thích",
  gift_received: "Bạn vừa nhận được quà!",
};

export function useNotifications() {
  const { user } = useUser();
  const [unreadCount, setUnreadCount] = useState(0);

  // Fetch initial unread count
  useEffect(() => {
    if (!user) return;
    apiFetch<UnreadCount>("/notifications/unread-count")
      .then((data) => setUnreadCount(data.count))
      .catch(() => null);
  }, [user]);

  // Supabase Realtime subscription for new notifications
  useEffect(() => {
    if (!user) return;

    const supabase = createClient();
    const channel = supabase
      .channel("user-notifications")
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "notifications",
          filter: `user_id=eq.${user.id}`,
        },
        (payload) => {
          const notifType = (payload.new as { type?: string })?.type ?? "";
          const message = NOTIFICATION_LABELS[notifType] ?? "Thông báo mới";
          toast(message);
          setUnreadCount((c) => c + 1);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [user]);

  return { unreadCount, setUnreadCount };
}
