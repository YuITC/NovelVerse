"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { apiFetch } from "@/lib/api";
import type { Comment } from "@/lib/types/comment";

interface CommentFormProps {
  novelId: string;
  chapterId?: string;
  parentId?: string;
  onSuccess: (c: Comment) => void;
  onCancel?: () => void;
  placeholder?: string;
}

export function CommentForm({
  novelId, chapterId, parentId, onSuccess, onCancel, placeholder
}: CommentFormProps) {
  const [content, setContent] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) { setError("Vui lòng nhập nội dung."); return; }
    setLoading(true);
    setError("");
    try {
      const result = await apiFetch<Comment>(`/novels/${novelId}/comments`, {
        method: "POST",
        body: JSON.stringify({ content, chapter_id: chapterId ?? null, parent_id: parentId ?? null }),
      });
      setContent("");
      onSuccess(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <Textarea
        placeholder={placeholder ?? "Viết bình luận..."}
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={3}
      />
      {error && <p className="text-sm text-destructive">{error}</p>}
      <div className="flex gap-2">
        <Button type="submit" disabled={loading} size="sm">
          {loading ? "Đang gửi..." : "Gửi"}
        </Button>
        {onCancel && (
          <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
            Huỷ
          </Button>
        )}
      </div>
    </form>
  );
}
