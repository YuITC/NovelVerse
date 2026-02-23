"use client";

import Link from "next/link";
import { Bell } from "lucide-react";
import { useUser } from "@/lib/hooks/use-user";
import { useNotifications } from "@/lib/hooks/use-notifications";

export function NotificationBell() {
  const { user } = useUser();
  const { unreadCount } = useNotifications();

  if (!user) return null;

  return (
    <Link
      href="/notifications"
      className="relative inline-flex items-center text-muted-foreground transition-colors hover:text-foreground"
      aria-label={`Thông báo${unreadCount > 0 ? ` (${unreadCount} chưa đọc)` : ""}`}
    >
      <Bell className="h-5 w-5" />
      {unreadCount > 0 && (
        <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-0.5 text-[10px] font-bold text-destructive-foreground">
          {unreadCount > 99 ? "99+" : unreadCount}
        </span>
      )}
    </Link>
  );
}
