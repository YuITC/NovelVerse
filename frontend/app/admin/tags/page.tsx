"use client";
import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/api";

interface Tag {
  id: string;
  name: string;
  slug: string;
  novel_count?: number;
}

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

export default function AdminTagsPage() {
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);
  const [newName, setNewName] = useState("");
  const [newSlug, setNewSlug] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState<Record<string, boolean>>({});

  function fetchTags() {
    setLoading(true);
    // Try admin endpoint first, fall back to public tags endpoint
    apiFetch<Tag[]>("/admin/tags")
      .catch(() => apiFetch<Tag[]>("/novels/tags"))
      .then(setTags)
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchTags();
  }, []);

  function handleNameChange(name: string) {
    setNewName(name);
    setNewSlug(toSlug(name));
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const tag = await apiFetch<Tag>("/admin/tags", {
        method: "POST",
        body: JSON.stringify({ name: newName.trim(), slug: newSlug.trim() }),
      });
      setTags((prev) => [tag, ...prev]);
      setNewName("");
      setNewSlug("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Lỗi khi thêm thẻ");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Xác nhận xoá thẻ này? Thẻ sẽ bị gỡ khỏi tất cả truyện.")) return;
    setDeleting((d) => ({ ...d, [id]: true }));
    try {
      await apiFetch(`/admin/tags/${id}`, { method: "DELETE" });
      setTags((prev) => prev.filter((t) => t.id !== id));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Lỗi khi xoá thẻ");
    } finally {
      setDeleting((d) => ({ ...d, [id]: false }));
    }
  }

  return (
    <div className="container mx-auto px-6 py-8 space-y-8">
      <h1 className="text-2xl font-bold">Quản lý thẻ</h1>

      {/* Add tag form */}
      <form onSubmit={handleAdd} className="rounded-lg border p-4 space-y-3">
        <h2 className="font-semibold">Thêm thẻ mới</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Tên thẻ</label>
            <Input
              placeholder="Ví dụ: Huyền Huyễn"
              value={newName}
              onChange={(e) => handleNameChange(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Slug (tự tạo)</label>
            <Input
              placeholder="huyen-huyen"
              value={newSlug}
              onChange={(e) => setNewSlug(e.target.value)}
              required
            />
          </div>
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" disabled={submitting} size="sm">
          {submitting ? "Đang thêm..." : "Thêm thẻ"}
        </Button>
      </form>

      {/* Tags list */}
      {loading ? (
        <p className="text-muted-foreground">Đang tải...</p>
      ) : tags.length === 0 ? (
        <p className="text-center text-muted-foreground py-12">Chưa có thẻ nào.</p>
      ) : (
        <div className="space-y-2">
          {tags.map((tag) => (
            <div
              key={tag.id}
              className="flex items-center justify-between rounded-lg border p-3 gap-3"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="font-medium">{tag.name}</span>
                <Badge variant="outline" className="text-xs font-mono">
                  {tag.slug}
                </Badge>
                {tag.novel_count !== undefined && (
                  <span className="text-xs text-muted-foreground">
                    {tag.novel_count} truyện
                  </span>
                )}
              </div>
              <Button
                size="sm"
                variant="destructive"
                disabled={deleting[tag.id]}
                onClick={() => handleDelete(tag.id)}
              >
                Xoá
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
