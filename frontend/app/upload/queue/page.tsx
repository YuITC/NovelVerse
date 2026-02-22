"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import type { CrawlQueueItem } from "@/lib/types/crawl";

const STATUS_LABELS: Record<string, string> = {
  pending: "Chờ",
  crawled: "Đã crawl",
  translated: "Đã dịch",
  published: "Đã đăng",
  skipped: "Bỏ qua",
};

const STATUS_VARIANTS: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  pending: "secondary",
  crawled: "outline",
  translated: "default",
  published: "secondary",
  skipped: "destructive",
};

export default function CrawlQueuePage() {
  const { user, loading } = useUser();
  const [items, setItems] = useState<CrawlQueueItem[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [busy, setBusy] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!loading && user && (user.role === "uploader" || user.role === "admin")) {
      apiFetch<CrawlQueueItem[]>("/crawl/queue?limit=50").then(setItems).catch(() => {});
    }
  }, [user, loading]);

  if (loading) return <div className="container mx-auto px-4 py-8">Đang tải...</div>;
  if (!user || (user.role !== "uploader" && user.role !== "admin")) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <p className="text-muted-foreground mb-4">Bạn không có quyền truy cập trang này.</p>
        <Button asChild variant="outline"><Link href="/">Về trang chủ</Link></Button>
      </div>
    );
  }

  const filtered = filter === "all" ? items : items.filter((i) => i.status === filter);

  async function doAction(itemId: string, action: "translate-opencc" | "translate-gemini" | "publish" | "skip") {
    setBusy((b) => ({ ...b, [itemId]: true }));
    try {
      if (action === "translate-opencc" || action === "translate-gemini") {
        const method = action === "translate-opencc" ? "opencc" : "gemini";
        const updated = await apiFetch<CrawlQueueItem>(`/crawl/queue/${itemId}/translate`, {
          method: "POST",
          body: JSON.stringify({ method }),
        });
        setItems((prev) => prev.map((i) => (i.id === itemId ? updated : i)));
      } else if (action === "publish") {
        await apiFetch(`/crawl/queue/${itemId}/publish`, { method: "POST" });
        setItems((prev) => prev.map((i) => i.id === itemId ? { ...i, status: "published" as const } : i));
      } else if (action === "skip") {
        await apiFetch(`/crawl/queue/${itemId}`, { method: "DELETE" });
        setItems((prev) => prev.map((i) => i.id === itemId ? { ...i, status: "skipped" as const } : i));
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : "Có lỗi xảy ra");
    } finally {
      setBusy((b) => ({ ...b, [itemId]: false }));
    }
  }

  const statuses = ["all", "crawled", "translated", "published", "skipped"];

  return (
    <div className="container mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Hàng đợi crawl</h1>
        <Button asChild variant="outline" size="sm">
          <Link href="/upload/crawl">← Quản lý nguồn</Link>
        </Button>
      </div>

      {/* Status filter */}
      <div className="flex flex-wrap gap-2">
        {statuses.map((s) => (
          <Button
            key={s}
            variant={filter === s ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(s)}
          >
            {s === "all" ? "Tất cả" : STATUS_LABELS[s]}
            {" "}({s === "all" ? items.length : items.filter((i) => i.status === s).length})
          </Button>
        ))}
      </div>

      {/* Queue items */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">Không có mục nào.</p>
        ) : (
          filtered.map((item) => (
            <div key={item.id} className="rounded-lg border p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-sm">
                    Chương {item.chapter_number} · Novel {item.novel_id.slice(0, 8)}…
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(item.created_at).toLocaleString("vi-VN")}
                    {item.translation_method && ` · Dịch bằng: ${item.translation_method}`}
                  </p>
                </div>
                <Badge variant={STATUS_VARIANTS[item.status] ?? "secondary"}>
                  {STATUS_LABELS[item.status] ?? item.status}
                </Badge>
              </div>

              {item.translated_content && (
                <p className="text-xs text-muted-foreground bg-muted rounded p-2 line-clamp-3">
                  {item.translated_content.slice(0, 200)}…
                </p>
              )}

              {(item.status === "crawled" || item.status === "translated") && (
                <div className="flex flex-wrap gap-2">
                  {item.status === "crawled" && (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={busy[item.id]}
                        onClick={() => doAction(item.id, "translate-opencc")}
                      >
                        Dịch OpenCC
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={busy[item.id]}
                        onClick={() => doAction(item.id, "translate-gemini")}
                      >
                        Dịch Gemini
                      </Button>
                    </>
                  )}
                  {item.status === "translated" && (
                    <Button
                      size="sm"
                      disabled={busy[item.id]}
                      onClick={() => doAction(item.id, "publish")}
                    >
                      Đăng chương
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={busy[item.id]}
                    onClick={() => doAction(item.id, "skip")}
                  >
                    Bỏ qua
                  </Button>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
