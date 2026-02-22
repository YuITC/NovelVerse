"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import type { CrawlSource } from "@/lib/types/crawl";

export default function CrawlSourcesPage() {
  const { user, loading } = useUser();
  const router = useRouter();
  const [sources, setSources] = useState<CrawlSource[]>([]);
  const [novelId, setNovelId] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user && (user.role === "uploader" || user.role === "admin")) {
      apiFetch<CrawlSource[]>("/crawl/sources").then(setSources).catch(() => {});
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

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const source = await apiFetch<CrawlSource>("/crawl/sources", {
        method: "POST",
        body: JSON.stringify({ novel_id: novelId.trim(), source_url: sourceUrl.trim() }),
      });
      setSources((prev) => [source, ...prev]);
      setNovelId("");
      setSourceUrl("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Lỗi khi thêm nguồn");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Xác nhận xoá nguồn này?")) return;
    try {
      await apiFetch(`/crawl/sources/${id}`, { method: "DELETE" });
      setSources((prev) => prev.filter((s) => s.id !== id));
    } catch {}
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Quản lý nguồn crawl</h1>
        <Button asChild variant="outline" size="sm">
          <Link href="/upload/queue">Xem hàng đợi →</Link>
        </Button>
      </div>

      {/* Add source form */}
      <form onSubmit={handleAdd} className="rounded-lg border p-4 space-y-3">
        <h2 className="font-semibold">Thêm nguồn mới</h2>
        <p className="text-sm text-muted-foreground">
          Tên miền được phép: biquge.info, biquge.tv, xbiquge.la, uukanshu.com, 69shu.com, 23us.so
        </p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Input
            placeholder="Novel ID (UUID)"
            value={novelId}
            onChange={(e) => setNovelId(e.target.value)}
            required
          />
          <Input
            placeholder="URL nguồn (https://biquge.info/book/12345/)"
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
            required
          />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" disabled={submitting} size="sm">
          {submitting ? "Đang thêm..." : "Thêm nguồn"}
        </Button>
      </form>

      {/* Sources list */}
      <div className="space-y-2">
        {sources.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">Chưa có nguồn crawl nào.</p>
        ) : (
          sources.map((s) => (
            <div key={s.id} className="flex items-center justify-between rounded-lg border p-3 gap-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate">{s.source_url}</p>
                <p className="text-xs text-muted-foreground">
                  Novel: {s.novel_id.slice(0, 8)}… · Chương đã crawl: {s.last_chapter}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge variant={s.is_active ? "default" : "secondary"}>
                  {s.is_active ? "Đang hoạt động" : "Tạm dừng"}
                </Badge>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDelete(s.id)}
                >
                  Xoá
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
