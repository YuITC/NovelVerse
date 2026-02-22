"use client";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { apiFetch } from "@/lib/api";
import type { Feedback } from "@/lib/types/admin";

const STATUS_TABS = [
  { value: "all", label: "Tất cả" },
  { value: "open", label: "Chờ xử lý" },
  { value: "reviewed", label: "Đã xem" },
  { value: "closed", label: "Đã đóng" },
];

const STATUS_LABELS: Record<string, string> = {
  open: "Chờ xử lý",
  reviewed: "Đã xem",
  closed: "Đã đóng",
};

const STATUS_VARIANTS: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  open: "secondary",
  reviewed: "outline",
  closed: "default",
};

export default function AdminFeedbacksPage() {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(false);
  const [responseMap, setResponseMap] = useState<Record<string, string>>({});
  const [openResponse, setOpenResponse] = useState<string | null>(null);
  const [busy, setBusy] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setLoading(true);
    const qs = filter !== "all" ? `?status=${filter}` : "";
    apiFetch<Feedback[]>(`/admin/feedbacks${qs}`)
      .then(setFeedbacks)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filter]);

  async function handleRespond(id: string, newStatus: "reviewed" | "closed") {
    setBusy((b) => ({ ...b, [id]: true }));
    try {
      const updated = await apiFetch<Feedback>(`/admin/feedbacks/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          status: newStatus,
          admin_response: responseMap[id] ?? null,
        }),
      });
      setFeedbacks((prev) => prev.map((f) => (f.id === id ? updated : f)));
      setOpenResponse(null);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Lỗi cập nhật góp ý");
    } finally {
      setBusy((b) => ({ ...b, [id]: false }));
    }
  }

  const filtered = filter === "all" ? feedbacks : feedbacks.filter((f) => f.status === filter);

  return (
    <div className="container mx-auto px-6 py-8 space-y-6">
      <h1 className="text-2xl font-bold">Quản lý góp ý</h1>

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
        <p className="text-center text-muted-foreground py-12">Không có góp ý nào.</p>
      ) : (
        <div className="space-y-3">
          {filtered.map((f) => (
            <div key={f.id} className="rounded-lg border p-4 space-y-3">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="space-y-1 flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-muted-foreground">
                      #{f.id.slice(0, 8)}
                    </span>
                    <Badge variant={STATUS_VARIANTS[f.status] ?? "secondary"}>
                      {STATUS_LABELS[f.status] ?? f.status}
                    </Badge>
                  </div>
                  <p className="text-sm">{f.content}</p>
                  {f.admin_response && (
                    <p className="text-xs text-muted-foreground italic bg-muted rounded p-2">
                      Phản hồi: {f.admin_response}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    {new Date(f.created_at).toLocaleString("vi-VN")}
                    {f.user_id ? ` · User: ${f.user_id.slice(0, 8)}…` : " · Ẩn danh"}
                  </p>
                </div>
                {f.status !== "closed" && (
                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setOpenResponse(openResponse === f.id ? null : f.id)
                      }
                    >
                      Phản hồi
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={busy[f.id]}
                      onClick={() => handleRespond(f.id, "closed")}
                    >
                      Đóng
                    </Button>
                  </div>
                )}
              </div>

              {openResponse === f.id && (
                <div className="space-y-2">
                  <Textarea
                    placeholder="Nhập phản hồi của bạn..."
                    value={responseMap[f.id] ?? ""}
                    onChange={(e) =>
                      setResponseMap((m) => ({ ...m, [f.id]: e.target.value }))
                    }
                    rows={3}
                    className="text-sm"
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      disabled={busy[f.id]}
                      onClick={() => handleRespond(f.id, "reviewed")}
                    >
                      Gửi phản hồi
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setOpenResponse(null)}
                    >
                      Huỷ
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
