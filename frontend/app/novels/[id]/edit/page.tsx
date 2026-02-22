"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { Tag, Novel } from "@/lib/types/novel";

export default function EditNovelPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: userLoading } = useUser();
  const router = useRouter();
  const [novel, setNovel] = useState<Novel | null>(null);
  const [tags, setTags] = useState<Tag[]>([]);
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [status, setStatus] = useState<"ongoing" | "completed" | "dropped">("ongoing");
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [novelLoading, setNovelLoading] = useState(true);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    if (!id) return;
    Promise.all([
      fetch(`${apiUrl}/api/v1/novels/${id}`).then((r) => {
        if (r.status === 404) throw new Error("Không tìm thấy truyện.");
        if (!r.ok) throw new Error("Lỗi khi tải truyện.");
        return r.json() as Promise<Novel>;
      }),
      fetch(`${apiUrl}/api/v1/novels/tags`).then((r) => r.ok ? (r.json() as Promise<Tag[]>) : []),
    ])
      .then(([novelData, tagsData]) => {
        setNovel(novelData); setTags(tagsData);
        setStatus(novelData.status);
        setSelectedTagIds(novelData.tags.map((t) => t.id));
      })
      .catch((err) => { setFetchError(err instanceof Error ? err.message : "Có lỗi xảy ra."); })
      .finally(() => setNovelLoading(false));
  }, [id, apiUrl]);

  useEffect(() => {
    if (userLoading || novelLoading) return;
    if (!user) { router.replace("/"); return; }
    if (novel) {
      const isAdmin = (user.user_metadata)?.role === "admin";
      if (novel.uploader_id !== user.id && !isAdmin) { router.replace(`/novels/${id}`); }
    }
  }, [user, userLoading, novel, novelLoading, router, id]);

  function toggleTag(tagId: string) {
    setSelectedTagIds((prev) => prev.includes(tagId) ? prev.filter((t) => t !== tagId) : [...prev, tagId]);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); setSubmitError(null);
    const form = e.currentTarget; const data = new FormData(form);
    const body = {
      title: data.get("title"),
      original_title: data.get("original_title") || null,
      author: data.get("author"),
      description: data.get("description") || null,
      cover_url: data.get("cover_url") || null,
      status, tag_ids: selectedTagIds,
    };
    try {
      setSubmitting(true);
      await apiFetch<Novel>(`/novels/${id}`, { method: "PATCH", body: JSON.stringify(body) });
      router.push(`/novels/${id}`);
    } catch (err) { setSubmitError(err instanceof Error ? err.message : "Có lỗi xảy ra."); }
    finally { setSubmitting(false); }
  }

  if (userLoading || novelLoading) return <div className="flex min-h-[60vh] items-center justify-center"><p className="text-muted-foreground">Đang tải...</p></div>;
  if (fetchError) return <div className="container mx-auto max-w-2xl px-4 py-10"><p className="text-destructive">{fetchError}</p></div>;
  if (!novel) return null;

  return (
    <div className="container mx-auto max-w-2xl px-4 py-10">
      <h1 className="mb-8 text-3xl font-bold">Chỉnh sửa truyện</h1>
      <form onSubmit={handleSubmit} className="space-y-6">
        {submitError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{submitError}</div>}
        <div className="space-y-1.5">
          <Label htmlFor="title">Tên truyện *</Label>
          <Input id="title" name="title" required defaultValue={novel.title} placeholder="Nhập tên truyện..." />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="original_title">Tên gốc (tùy chọn)</Label>
          <Input id="original_title" name="original_title" defaultValue={novel.original_title ?? ""} placeholder="Tên tiếng Trung..." />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="author">Tác giả *</Label>
          <Input id="author" name="author" required defaultValue={novel.author} placeholder="Tên tác giả..." />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="status">Trạng thái</Label>
          <Select value={status} onValueChange={(v) => setStatus(v as "ongoing" | "completed" | "dropped")}>
            <SelectTrigger id="status"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="ongoing">Đang ra</SelectItem>
              <SelectItem value="completed">Hoàn thành</SelectItem>
              <SelectItem value="dropped">Tạm dừng</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="cover_url">URL ảnh bìa</Label>
          <Input id="cover_url" name="cover_url" type="url" defaultValue={novel.cover_url ?? ""} placeholder="https://example.com/cover.jpg" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="description">Giới thiệu</Label>
          <Textarea id="description" name="description" rows={6} defaultValue={novel.description ?? ""} placeholder="Viết giới thiệu..." />
        </div>
        {tags.length > 0 && (
          <div className="space-y-2">
            <Label>Thể loại</Label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {tags.map((tag) => (
                <div key={tag.id} className="flex items-center gap-2">
                  <Checkbox id={`tag-${tag.id}`} checked={selectedTagIds.includes(tag.id)} onCheckedChange={() => toggleTag(tag.id)} />
                  <Label htmlFor={`tag-${tag.id}`} className="cursor-pointer font-normal">{tag.name}</Label>
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="flex gap-3">
          <Button type="submit" disabled={submitting} className="flex-1">
            {submitting ? "Đang lưu..." : "Lưu thay đổi"}
          </Button>
          <Button type="button" variant="outline" onClick={() => router.push(`/novels/${id}`)}>Hủy</Button>
        </div>
      </form>
    </div>
  );
}
