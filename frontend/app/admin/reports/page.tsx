"use client";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { apiFetch } from "@/lib/api";
import type { Report } from "@/lib/types/admin";

const STATUS_TABS = [
  { value: "all", label: "Tất cả" },
  { value: "pending", label: "Chờ xử lý" },
  { value: "resolved", label: "Đã giải quyết" },
  { value: "dismissed", label: "Đã từ chối" },
];

const STATUS_LABELS: Record<string, string> = {
  pending: "Chờ xử lý",
  resolved: "Đã giải quyết",
  dismissed: "Đã từ chối",
};

const STATUS_VARIANTS: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  pending: "secondary",
  resolved: "default",
  dismissed: "destructive",
};

const TARGET_LABELS: Record<string, string> = {
  novel: "Truyện",
  chapter: "Chương",
  comment: "Bình luận",
  review: "Đánh giá",
  user: "Người dùng",
};

export default function AdminReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(false);
  const [noteMap, setNoteMap] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<Record<string, boolean>>({});
  const [openNote, setOpenNote] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    const qs = filter !== "all" ? `?status=${filter}` : "";
    apiFetch<Report[]>(`/admin/reports${qs}`)
      .then(setReports)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filter]);

  async function handleAction(id: string, status: "resolved" | "dismissed") {
    setBusy((b) => ({ ...b, [id]: true }));
    try {
      const updated = await apiFetch<Report>(`/admin/reports/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status, admin_note: noteMap[id] ?? null }),
      });
      setReports((prev) => prev.map((r) => (r.id === id ? updated : r)));
      setOpenNote(null);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Lỗi cập nhật báo cáo");
    } finally {
      setBusy((b) => ({ ...b, [id]: false }));
    }
  }

  const filtered = filter === "all" ? reports : reports.filter((r) => r.status === filter);

  return (
    <div className="container mx-auto px-6 py-8 space-y-6">
      <h1 className="text-2xl font-bold">Quản lý báo cáo</h1>

      {/* Filter tabs */}
      <div className="flex flex-wrap gap-2">
        {STATUS_TABS.map((tab) => (
          <Button
            key={tab.value}
            variant={filter === tab.value ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(tab.value)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {loading ? (
        <p className="text-muted-foreground">Đang tải...</p>
      ) : filtered.length === 0 ? (
        <p className="text-center text-muted-foreground py-12">Không có báo cáo nào.</p>
      ) : (
        <div className="space-y-3">
          {filtered.map((r) => (
            <div key={r.id} className="rounded-lg border p-4 space-y-3">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-mono text-muted-foreground">
                      #{r.id.slice(0, 8)}
                    </span>
                    <Badge variant="outline">{TARGET_LABELS[r.target_type] ?? r.target_type}</Badge>
                    <Badge variant={STATUS_VARIANTS[r.status] ?? "secondary"}>
                      {STATUS_LABELS[r.status] ?? r.status}
                    </Badge>
                  </div>
                  <p className="text-sm font-medium line-clamp-2">{r.reason}</p>
                  {r.admin_note && (
                    <p className="text-xs text-muted-foreground italic">Ghi chú: {r.admin_note}</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    {new Date(r.created_at).toLocaleString("vi-VN")}
                  </p>
                </div>
                {r.status === "pending" && (
                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setOpenNote(openNote === r.id ? null : r.id)}
                    >
                      Ghi chú
                    </Button>
                    <Button
                      size="sm"
                      disabled={busy[r.id]}
                      onClick={() => handleAction(r.id, "resolved")}
                    >
                      Giải quyết
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      disabled={busy[r.id]}
                      onClick={() => handleAction(r.id, "dismissed")}
                    >
                      Từ chối
                    </Button>
                  </div>
                )}
              </div>
              {openNote === r.id && (
                <Textarea
                  placeholder="Ghi chú của quản trị viên (không bắt buộc)"
                  value={noteMap[r.id] ?? ""}
                  onChange={(e) =>
                    setNoteMap((m) => ({ ...m, [r.id]: e.target.value }))
                  }
                  rows={2}
                  className="text-sm"
                />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
