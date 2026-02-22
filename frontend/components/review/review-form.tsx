"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { StarRating } from "./star-rating";
import { apiFetch } from "@/lib/api";
import type { Review } from "@/lib/types/comment";

interface ReviewFormProps {
  novelId: string;
  existing?: Review;              // pre-fill for edit
  onSuccess: (r: Review) => void;
}

export function ReviewForm({ novelId, existing, onSuccess }: ReviewFormProps) {
  const [rating, setRating] = useState(existing?.rating ?? 0);
  const [content, setContent] = useState(existing?.content ?? "");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!rating) { setError("Vui lòng chọn số sao."); return; }
    if (content.trim().split(/\s+/).length < 10) {
      setError("Đánh giá phải có ít nhất 10 từ.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const method = existing ? "PATCH" : "POST";
      const path = existing ? `/novels/${novelId}/reviews/me` : `/novels/${novelId}/reviews`;
      const result = await apiFetch<Review>(path, {
        method,
        body: JSON.stringify({ rating, content }),
      });
      onSuccess(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg.includes("409") ? "Bạn đã đánh giá truyện này rồi." : msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <StarRating value={rating} onChange={setRating} size="lg" />
      <Textarea
        placeholder="Chia sẻ cảm nhận của bạn (ít nhất 10 từ)..."
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={4}
      />
      {error && <p className="text-sm text-destructive">{error}</p>}
      <Button type="submit" disabled={loading} size="sm">
        {loading ? "Đang gửi..." : existing ? "Cập nhật đánh giá" : "Gửi đánh giá"}
      </Button>
    </form>
  );
}
