"use client";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import type { AdminUser } from "@/lib/types/admin";

const NAV_ITEMS = [
  { href: "/admin", label: "Tổng quan" },
  { href: "/admin/users", label: "Người dùng" },
  { href: "/admin/novels", label: "Truyện" },
  { href: "/admin/reports", label: "Báo cáo" },
  { href: "/admin/feedbacks", label: "Góp ý" },
  { href: "/admin/tags", label: "Thẻ" },
  { href: "/admin/settings", label: "Cài đặt" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    apiFetch<AdminUser>("/auth/me")
      .then((me) => {
        if (me.role !== "admin") {
          router.replace("/");
        } else {
          setChecking(false);
        }
      })
      .catch(() => {
        router.replace("/");
      });
  }, [router]);

  if (checking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">Đang kiểm tra quyền...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r bg-muted/30 flex flex-col py-6 px-3 gap-1">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-3 mb-3">
          Quản trị
        </p>
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/admin"
              ? pathname === "/admin"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-foreground hover:bg-muted"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
