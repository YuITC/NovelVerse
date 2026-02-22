"use client";
import { useEffect, useState } from "react";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import { CommentForm } from "./comment-form";
import { CommentItem } from "./comment-item";
import type { Comment } from "@/lib/types/comment";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface CommentSectionProps {
  novelId: string;
  chapterId?: string;
}

export function CommentSection({ novelId, chapterId }: CommentSectionProps) {
  const { user } = useUser();
  const [comments, setComments] = useState<Comment[]>([]);
  const [sort, setSort] = useState("newest");
  const [repliesMap, setRepliesMap] = useState<Record<string, Comment[]>>({});

  useEffect(() => {
    const params = new URLSearchParams({ sort, limit: "20" });
    apiFetch<Comment[]>(`/novels/${novelId}/comments?${params}`)
      .then((data) => {
        const topLevel = chapterId
          ? data.filter((c) => c.chapter_id === chapterId)
          : data.filter((c) => c.chapter_id === null);
        setComments(topLevel);
        // Load replies for each top-level comment
        topLevel.forEach((c) => {
          apiFetch<Comment[]>(`/comments/${c.id}/replies`).then((replies) => {
            setRepliesMap((prev) => ({ ...prev, [c.id]: replies }));
          }).catch(() => {});
        });
      })
      .catch(() => {});
  }, [novelId, chapterId, sort]);

  function handleNewComment(c: Comment) {
    setComments((prev) => [c, ...prev]);
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Bình luận ({comments.length})</h2>
        <Select value={sort} onValueChange={setSort}>
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="newest">Mới nhất</SelectItem>
            <SelectItem value="oldest">Cũ nhất</SelectItem>
            <SelectItem value="most_liked">Nhiều like</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {user ? (
        <div className="rounded-lg border p-4">
          <CommentForm
            novelId={novelId}
            chapterId={chapterId}
            onSuccess={handleNewComment}
            placeholder={chapterId ? "Bình luận về chương này..." : "Bình luận về truyện..."}
          />
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          <a href="/login" className="text-primary hover:underline">Đăng nhập</a> để bình luận.
        </p>
      )}

      <div className="space-y-3">
        {comments.map((c) => (
          <CommentItem
            key={c.id}
            comment={c}
            novelId={novelId}
            replies={repliesMap[c.id] ?? []}
          />
        ))}
        {comments.length === 0 && (
          <p className="text-center text-sm text-muted-foreground py-6">
            Chưa có bình luận nào.
          </p>
        )}
      </div>
    </section>
  );
}
