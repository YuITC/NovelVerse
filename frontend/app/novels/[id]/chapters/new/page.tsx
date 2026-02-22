"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { ChapterListItem } from "@/lib/types/chapter";

type ChapterStatus = "draft" | "scheduled" | "published";

export default function NewChapterPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: userLoading } = useUser();
  const router = useRouter();

  const [status, setStatus] = useState<ChapterStatus>("draft");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Auth guard: only uploader or admin
  useEffect(() => {
    if (userLoading) return;
    if (!user) {
      router.replace(`/novels/${id}`);
      return;
    }
    const role = (user.user_metadata as { role?: string })?.role;
    if (role !== "uploader" && role !== "admin") {
      router.replace(`/novels/${id}`);
    }
  }, [user, userLoading, router, id]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitError(null);

    const form = e.currentTarget;
    const data = new FormData(form);

    const chapterNumber = Number(data.get("chapter_number"));
    const title = (data.get("title") as string).trim() || null;
    const content = data.get("content") as string;
    const publishAt = data.get("publish_at") as string;

    const body: {
      chapter_number: number;
      title: string | null;
      content: string;
      status: ChapterStatus;
      publish_at?: string | null;
    } = {
      chapter_number: chapterNumber,
      title,
      content,
      status,
      publish_at: status === "scheduled" && publishAt ? publishAt : null,
    };

    try {
      setSubmitting(true);
      const newChapter = await apiFetch<ChapterListItem>(
        `/novels/${id}/chapters`,
        { method: "POST", body: JSON.stringify(body) }
      );
      router.push(`/novels/${id}/chapters/${newChapter.chapter_number}`);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Có lỗi xảy ra. Vui lòng thử lại."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (userLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-muted-foreground">Đang tải...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-2xl px-4 py-10">
      <h1 className="mb-8 text-3xl font-bold">Thêm chương mới</h1>
      <form onSubmit={handleSubmit} className="space-y-6">
        {submitError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {submitError}
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="chapter_number">Số chương *</Label>
          <Input
            id="chapter_number"
            name="chapter_number"
            type="number"
            min={1}
            required
            placeholder="1"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="title">Tiêu đề chương (tùy chọn)</Label>
          <Input
            id="title"
            name="title"
            placeholder="Nhập tiêu đề chương..."
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="status">Trạng thái</Label>
          <Select
            value={status}
            onValueChange={(v) => setStatus(v as ChapterStatus)}
          >
            <SelectTrigger id="status">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="draft">Bản nháp</SelectItem>
              <SelectItem value="scheduled">Lên lịch</SelectItem>
              <SelectItem value="published">Đã xuất bản</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {status === "scheduled" && (
          <div className="space-y-1.5">
            <Label htmlFor="publish_at">Thời gian xuất bản</Label>
            <Input
              id="publish_at"
              name="publish_at"
              type="datetime-local"
              required={status === "scheduled"}
            />
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="content">Nội dung chương *</Label>
          <Textarea
            id="content"
            name="content"
            required
            rows={20}
            placeholder="Nhập nội dung chương tại đây..."
            className="font-mono text-sm"
          />
        </div>

        <div className="flex gap-3">
          <Button type="submit" disabled={submitting} className="flex-1">
            {submitting ? "Đang lưu..." : "Đăng chương"}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push(`/novels/${id}`)}
          >
            Hủy
          </Button>
        </div>
      </form>
    </div>
  );
}
