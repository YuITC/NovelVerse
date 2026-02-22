"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/api";
import type { NovelListItem, NovelListResponse } from "@/lib/types/novel";

const STATUS_LABELS: Record<string, string> = {
  ongoing: "Đang ra",
  completed: "Hoàn thành",
  dropped: "Dừng",
};

const STATUS_VARIANTS: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  ongoing: "default",
  completed: "secondary",
  dropped: "destructive",
};

export default function AdminNovelsPage() {
  const [novels, setNovels] = useState<NovelListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setLoading(true);
    apiFetch<NovelListResponse | NovelListItem[]>("/novels?limit=50")
      .then((data) => {
        if (Array.isArray(data)) {
          setNovels(data);
        } else {
          setNovels((data as NovelListResponse).items ?? []);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function togglePin(novel: NovelListItem) {
    const action = novel.is_pinned ? "unpin" : "pin";
    setBusy((b) => ({ ...b, [novel.id]: true }));
    try {
      await apiFetch(`/admin/novels/${novel.id}/${action}`, { method: "POST" });
      setNovels((prev) =>
        prev.map((n) =>
          n.id === novel.id ? { ...n, is_pinned: !n.is_pinned } : n
        )
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Lỗi thao tác");
    } finally {
      setBusy((b) => ({ ...b, [novel.id]: false }));
    }
  }

  async function handleDelete(id: string, title: string) {
    if (
      !confirm(
        `Xác nhận xoá truyện "${title}"?\n\nHành động này không thể hoàn tác.`
      )
    )
      return;
    setBusy((b) => ({ ...b, [id]: true }));
    try {
      await apiFetch(`/admin/novels/${id}`, { method: "DELETE" });
      setNovels((prev) => prev.filter((n) => n.id !== id));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Lỗi khi xoá truyện");
    } finally {
      setBusy((b) => ({ ...b, [id]: false }));
    }
  }

  return (
    <div className="container mx-auto px-6 py-8 space-y-6">
      <h1 className="text-2xl font-bold">Quản lý truyện</h1>

      {loading ? (
        <p className="text-muted-foreground">Đang tải...</p>
      ) : novels.length === 0 ? (
        <p className="text-center text-muted-foreground py-12">Không có truyện nào.</p>
      ) : (
        <div className="rounded-lg border overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Tên truyện</th>
                <th className="px-4 py-3 text-left font-medium">Tác giả</th>
                <th className="px-4 py-3 text-left font-medium">Trạng thái</th>
                <th className="px-4 py-3 text-left font-medium">Số chương</th>
                <th className="px-4 py-3 text-left font-medium">Ghim</th>
                <th className="px-4 py-3 text-left font-medium">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {novels.map((novel) => (
                <tr key={novel.id} className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3">
                    <Link
                      href={`/novels/${novel.id}`}
                      className="font-medium hover:underline line-clamp-1 max-w-[200px] block"
                    >
                      {novel.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{novel.author}</td>
                  <td className="px-4 py-3">
                    <Badge variant={STATUS_VARIANTS[novel.status] ?? "secondary"}>
                      {STATUS_LABELS[novel.status] ?? novel.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {novel.total_chapters}
                  </td>
                  <td className="px-4 py-3">
                    {novel.is_pinned ? (
                      <Badge variant="default">Ghim</Badge>
                    ) : (
                      <span className="text-muted-foreground text-xs">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={busy[novel.id]}
                        onClick={() => togglePin(novel)}
                      >
                        {novel.is_pinned ? "Bỏ ghim" : "Ghim"}
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        disabled={busy[novel.id]}
                        onClick={() => handleDelete(novel.id, novel.title)}
                      >
                        Xoá
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
