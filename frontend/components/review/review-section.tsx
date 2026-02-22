"use client";
import { useEffect, useState } from "react";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import { StarRating } from "./star-rating";
import { ReviewForm } from "./review-form";
import type { Review } from "@/lib/types/comment";

interface ReviewSectionProps {
  novelId: string;
  avgRating: number;
  ratingCount: number;
}

export function ReviewSection({ novelId, avgRating, ratingCount }: ReviewSectionProps) {
  const { user } = useUser();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [myReview, setMyReview] = useState<Review | null>(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    apiFetch<Review[]>(`/novels/${novelId}/reviews?limit=10`).then(setReviews).catch(() => {});
  }, [novelId]);

  useEffect(() => {
    if (user) {
      const mine = reviews.find((r) => r.user_id === user.id) ?? null;
      setMyReview(mine);
    }
  }, [user, reviews]);

  function handleReviewSuccess(r: Review) {
    setReviews((prev) => {
      const filtered = prev.filter((x) => x.id !== r.id);
      return [r, ...filtered];
    });
    setMyReview(r);
    setShowForm(false);
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center gap-3">
        <h2 className="text-xl font-bold">Đánh giá</h2>
        {ratingCount > 0 && (
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <StarRating value={Math.round(avgRating)} size="sm" />
            <span>{avgRating.toFixed(1)} ({ratingCount} đánh giá)</span>
          </div>
        )}
      </div>

      {user && !showForm && (
        <button
          onClick={() => setShowForm(true)}
          className="text-sm text-primary underline-offset-4 hover:underline"
        >
          {myReview ? "Sửa đánh giá của bạn" : "Viết đánh giá"}
        </button>
      )}

      {showForm && (
        <div className="rounded-lg border p-4">
          <ReviewForm
            novelId={novelId}
            existing={myReview ?? undefined}
            onSuccess={handleReviewSuccess}
          />
        </div>
      )}

      <div className="space-y-3">
        {reviews.map((r) => (
          <div key={r.id} className="rounded-lg border p-4 space-y-2">
            <div className="flex items-center gap-2">
              <StarRating value={r.rating} size="sm" />
              <span className="text-xs text-muted-foreground">
                {new Date(r.created_at).toLocaleDateString("vi-VN")}
              </span>
            </div>
            <p className="text-sm">{r.content}</p>
          </div>
        ))}
        {reviews.length === 0 && (
          <p className="text-center text-sm text-muted-foreground py-4">
            Chưa có đánh giá nào. Hãy là người đầu tiên!
          </p>
        )}
      </div>
    </section>
  );
}
