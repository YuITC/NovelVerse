"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

interface StatCard {
  label: string;
  value: string | number;
  href: string;
}

export default function AdminOverviewPage() {
  const [stats, setStats] = useState({
    users: "Đang tải...",
    novels: "Đang tải...",
    pendingReports: "Đang tải...",
    openFeedbacks: "Đang tải...",
  });

  useEffect(() => {
    // Fetch each count independently; failures show placeholder
    apiFetch<{ total: number } | unknown[]>("/admin/users?limit=1")
      .then((d) => {
        const count = Array.isArray(d) ? d.length : (d as { total: number }).total ?? "—";
        setStats((s) => ({ ...s, users: String(count) }));
      })
      .catch(() => setStats((s) => ({ ...s, users: "—" })));

    apiFetch<{ total: number } | unknown[]>("/novels?limit=1")
      .then((d) => {
        const count = Array.isArray(d) ? d.length : (d as { total: number }).total ?? "—";
        setStats((s) => ({ ...s, novels: String(count) }));
      })
      .catch(() => setStats((s) => ({ ...s, novels: "—" })));

    apiFetch<unknown[]>("/admin/reports?status=pending&limit=50")
      .then((d) => {
        const count = Array.isArray(d) ? d.length : "—";
        setStats((s) => ({ ...s, pendingReports: String(count) }));
      })
      .catch(() => setStats((s) => ({ ...s, pendingReports: "—" })));

    apiFetch<unknown[]>("/admin/feedbacks?status=open&limit=50")
      .then((d) => {
        const count = Array.isArray(d) ? d.length : "—";
        setStats((s) => ({ ...s, openFeedbacks: String(count) }));
      })
      .catch(() => setStats((s) => ({ ...s, openFeedbacks: "—" })));
  }, []);

  const cards: StatCard[] = [
    { label: "Người dùng", value: stats.users, href: "/admin/users" },
    { label: "Truyện", value: stats.novels, href: "/admin/novels" },
    { label: "Báo cáo chờ", value: stats.pendingReports, href: "/admin/reports" },
    { label: "Góp ý chờ", value: stats.openFeedbacks, href: "/admin/feedbacks" },
  ];

  return (
    <div className="container mx-auto px-6 py-8 space-y-8">
      <h1 className="text-2xl font-bold">Tổng quan</h1>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {cards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="rounded-lg border p-5 hover:border-primary transition-colors space-y-1"
          >
            <p className="text-sm text-muted-foreground">{card.label}</p>
            <p className="text-2xl font-bold">{card.value}</p>
          </Link>
        ))}
      </div>

      <div className="rounded-lg border p-5 space-y-3">
        <h2 className="font-semibold">Truy cập nhanh</h2>
        <div className="flex flex-wrap gap-2">
          {[
            { href: "/admin/users", label: "Quản lý người dùng" },
            { href: "/admin/novels", label: "Quản lý truyện" },
            { href: "/admin/reports", label: "Xử lý báo cáo" },
            { href: "/admin/feedbacks", label: "Xem góp ý" },
            { href: "/admin/tags", label: "Quản lý thẻ" },
            { href: "/admin/settings", label: "Cài đặt hệ thống" },
          ].map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-md border px-3 py-1.5 text-sm hover:bg-muted transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
