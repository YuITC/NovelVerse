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
import type { ChapterContent, ChapterListItem } from "@/lib/types/chapter";

type ChapterStatus = "draft" | "scheduled" | "published";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function EditChapterPage() {
  const { id, num } = useParams<{ id: string; num: string }>();
  const { user, loading: userLoading } = useUser();
  const router = useRouter();

  const [chapter, setChapter] = useState<ChapterContent | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [chapterLoading, setChapterLoading] = useState(true);
  const [status, setStatus] = useState<ChapterStatus>("draft");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!id || !num) return;
    fetch(`${API_URL}/api/v1/novels/${id}/chapters/${num}`, {
      cache: "no-store",
    })
      .then((r) => {
        if (r.status === 404) throw new Error("Không tìm thấy chương.");
        if (!r.ok) throw new Error("Lỗi khi tải chương.");
        return r.json() as Promise<ChapterContent>;
      })
      .then((data) => {
        setChapter(data);
        setStatus(data.status);
      })
      .catch((err) => {
        setFetchError(
          err instanceof Error ? err.message : "Có lỗi xảy ra."
        );
      })
      .finally(() => setChapterLoading(false));
  }, [id, num]);

  // Auth guard
  useEffect(() => {
    if (userLoading) return;
    if (!user) {
      router.replace(`/novels/${id}`);
    }
  }, [user, userLoading, router, id]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitError(null);

    const form = e.currentTarget;
    const data = new FormData(form);

    const title = (data.get("title") as string).trim() || null;
    const content = data.get("content") as string;
    const publishAt = data.get("publish_at") as string;

    const body: {
      title: string | null;
      content: string;
      status: ChapterStatus;
      publish_at?: string | null;
    } = {
      title,
      content,
      status,
      publish_at: status === "scheduled" && publishAt ? publishAt : null,
    };

    try {
      setSubmitting(true);
      await apiFetch<ChapterListItem>(`/novels/${id}/chapters/${num}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      });
      router.push(`/novels/${id}/chapters/${num}`);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Có lỗi xảy ra. Vui lòng thử lại."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (userLoading || chapterLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-muted-foreground">Đang tải...</p>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="container mx-auto max-w-2xl px-4 py-10">
        <p className="text-destructive">{fetchError}</p>
      </div>
    );
  }

  if (!chapter) return null;

  // Format datetime-local value from ISO string
  const publishAtValue = chapter.publish_at
    ? chapter.publish_at.slice(0, 16)
    : "";

  return (
    <div className="container mx-auto max-w-2xl px-4 py-10">
      <h1 className="mb-8 text-3xl font-bold">
        Chỉnh sửa chương {chapter.chapter_number}
      </h1>
      <form onSubmit={handleSubmit} className="space-y-6">
        {submitError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {submitError}
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="title">Tiêu đề chương (tùy chọn)</Label>
          <Input
            id="title"
            name="title"
            defaultValue={chapter.title ?? ""}
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
              defaultValue={publishAtValue}
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
            defaultValue={chapter.content}
            placeholder="Nhập nội dung chương tại đây..."
            className="font-mono text-sm"
          />
        </div>

        <div className="flex gap-3">
          <Button type="submit" disabled={submitting} className="flex-1">
            {submitting ? "Đang lưu..." : "Lưu thay đổi"}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push(`/novels/${id}/chapters/${num}`)}
          >
            Hủy
          </Button>
        </div>
      </form>
    </div>
  );
}
