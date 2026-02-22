"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Tag, Novel } from "@/lib/types/novel";

export default function UploadPage() {
  const { user, loading } = useUser();
  const router = useRouter();

  const [tags, setTags] = useState<Tag[]>([]);
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [status, setStatus] = useState<"ongoing" | "completed" | "dropped">(
    "ongoing"
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/");
    }
  }, [user, loading, router]);

  useEffect(() => {
    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/v1/novels/tags`)
      .then((r) => r.json())
      .then((data: Tag[]) => setTags(data))
      .catch(() => {});
  }, []);

  function toggleTag(id: string) {
    setSelectedTagIds((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const form = e.currentTarget;
    const data = new FormData(form);

    const body = {
      title: data.get("title") as string,
      original_title: (data.get("original_title") as string) || undefined,
      author: data.get("author") as string,
      description: (data.get("description") as string) || undefined,
      cover_url: (data.get("cover_url") as string) || undefined,
      status,
      tag_ids: selectedTagIds,
    };

    try {
      setSubmitting(true);
      const novel = await apiFetch<Novel>("/novels", {
        method: "POST",
        body: JSON.stringify(body),
      });
      router.push(`/novels/${novel.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Có lỗi xảy ra.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-muted-foreground">Đang tải...</p>
      </div>
    );
  }

  if (!user) return null;

  const isCrawlUser = user.role === "uploader" || user.role === "admin";

  return (
    <div className="container mx-auto max-w-2xl px-4 py-10">
      <div className="mb-8 flex items-start justify-between gap-4">
        <h1 className="text-3xl font-bold">Đăng truyện mới</h1>
        {isCrawlUser && (
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button asChild variant="outline" size="sm">
              <Link href="/upload/crawl">Quản lý nguồn crawl</Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href="/upload/queue">Xem hàng đợi</Link>
            </Button>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="title">Tên truyện *</Label>
          <Input id="title" name="title" required placeholder="Nhập tên truyện..." />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="original_title">Tên gốc (tùy chọn)</Label>
          <Input
            id="original_title"
            name="original_title"
            placeholder="Tên tiếng Trung hoặc tên gốc..."
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="author">Tác giả *</Label>
          <Input id="author" name="author" required placeholder="Tên tác giả..." />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="status">Trạng thái</Label>
          <Select
            value={status}
            onValueChange={(v) =>
              setStatus(v as "ongoing" | "completed" | "dropped")
            }
          >
            <SelectTrigger id="status">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ongoing">Đang ra</SelectItem>
              <SelectItem value="completed">Hoàn thành</SelectItem>
              <SelectItem value="dropped">Tạm dừng</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="cover_url">URL ảnh bìa (tùy chọn)</Label>
          <Input
            id="cover_url"
            name="cover_url"
            type="url"
            placeholder="https://example.com/cover.jpg"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="description">Giới thiệu (tùy chọn)</Label>
          <Textarea
            id="description"
            name="description"
            rows={6}
            placeholder="Viết giới thiệu ngắn về truyện..."
          />
        </div>

        {tags.length > 0 && (
          <div className="space-y-2">
            <Label>Thể loại</Label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {tags.map((tag) => (
                <div key={tag.id} className="flex items-center gap-2">
                  <Checkbox
                    id={`tag-${tag.id}`}
                    checked={selectedTagIds.includes(tag.id)}
                    onCheckedChange={() => toggleTag(tag.id)}
                  />
                  <Label
                    htmlFor={`tag-${tag.id}`}
                    className="cursor-pointer font-normal"
                  >
                    {tag.name}
                  </Label>
                </div>
              ))}
            </div>
          </div>
        )}

        <Button type="submit" disabled={submitting} className="w-full">
          {submitting ? "Đang đăng..." : "Đăng truyện"}
        </Button>
      </form>
    </div>
  );
}
