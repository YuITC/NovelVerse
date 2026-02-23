"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bell, BookOpen, Heart, MessageSquare, Gift } from "lucide-react";
import { useUser } from "@/lib/hooks/use-user";
import { useNotifications } from "@/lib/hooks/use-notifications";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import type { Notification } from "@/lib/types/notification";

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return "Vừa xong";
  if (diffMins < 60) return `${diffMins} phút trước`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} giờ trước`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) return `${diffDays} ngày trước`;
  return `${Math.floor(diffDays / 30)} tháng trước`;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  new_chapter: <BookOpen className="h-5 w-5 text-primary" />,
  reply_to_comment: <MessageSquare className="h-5 w-5 text-blue-500" />,
  comment_liked: <Heart className="h-5 w-5 text-red-500" />,
  gift_received: <Gift className="h-5 w-5 text-yellow-500" />,
};

function notificationMessage(notif: Notification): string {
  const p = notif.payload as Record<string, unknown>;
  switch (notif.type) {
    case "new_chapter":
      return `"${p.novel_title ?? "Truyện"}" vừa đăng chương ${p.chapter_number ?? "mới"}`;
    case "reply_to_comment":
      return `${p.replier_username ?? "Ai đó"} đã trả lời bình luận của bạn`;
    case "comment_liked":
      return `${p.liker_username ?? "Ai đó"} đã thích bình luận của bạn`;
    case "gift_received":
      return `Bạn nhận được "${p.item_name ?? "quà"}" từ người tặng`;
    default:
      return "Bạn có thông báo mới";
  }
}

export default function NotificationsPage() {
  const { user, loading: userLoading } = useUser();
  const { setUnreadCount } = useNotifications();
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    if (userLoading) return;
    if (!user) router.replace("/");
  }, [user, userLoading, router]);

  useEffect(() => {
    if (!user || userLoading) return;
    apiFetch<Notification[]>("/notifications?limit=50")
      .then(setNotifications)
      .catch(() => null);
  }, [user, userLoading]);

  async function handleMarkRead(id: string) {
    try {
      const updated = await apiFetch<Notification>(`/notifications/${id}/read`, { method: "PATCH" });
      setNotifications((prev) => prev.map((n) => (n.id === id ? updated : n)));
      setUnreadCount((c) => Math.max(c - 1, 0));
    } catch {
      // ignore
    }
  }

  async function handleMarkAllRead() {
    try {
      await apiFetch("/notifications/read-all", { method: "PATCH" });
      setNotifications((prev) => prev.map((n) => ({ ...n, read_at: new Date().toISOString() })));
      setUnreadCount(0);
    } catch {
      // ignore
    }
  }

  if (userLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-muted-foreground">Đang tải...</p>
      </div>
    );
  }

  const unreadNotifications = notifications.filter((n) => !n.read_at);

  return (
    <div className="container mx-auto max-w-2xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bell className="h-7 w-7" />
          <h1 className="text-2xl font-bold">Thông báo</h1>
          {unreadNotifications.length > 0 && (
            <span className="rounded-full bg-destructive px-2 py-0.5 text-xs font-bold text-destructive-foreground">
              {unreadNotifications.length}
            </span>
          )}
        </div>
        {unreadNotifications.length > 0 && (
          <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
            Đánh dấu tất cả đã đọc
          </Button>
        )}
      </div>

      {notifications.length === 0 ? (
        <div className="flex min-h-[200px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed">
          <Bell className="h-12 w-12 text-muted-foreground" />
          <p className="text-muted-foreground">Chưa có thông báo nào.</p>
          <Link href="/novels" className="text-sm text-primary underline-offset-4 hover:underline">
            Khám phá truyện
          </Link>
        </div>
      ) : (
        <div className="flex flex-col divide-y rounded-lg border">
          {notifications.map((notif) => (
            <button
              key={notif.id}
              className={`flex items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-muted/50 ${
                !notif.read_at ? "bg-primary/5" : ""
              }`}
              onClick={() => !notif.read_at && handleMarkRead(notif.id)}
            >
              <span className="mt-0.5 shrink-0">
                {TYPE_ICONS[notif.type] ?? <Bell className="h-5 w-5 text-muted-foreground" />}
              </span>
              <div className="min-w-0 flex-1">
                <p className={`text-sm ${!notif.read_at ? "font-medium" : "text-muted-foreground"}`}>
                  {notificationMessage(notif)}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {formatRelativeTime(notif.created_at)}
                </p>
              </div>
              {!notif.read_at && (
                <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-primary" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
