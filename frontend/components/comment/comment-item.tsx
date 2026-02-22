"use client";
import { useState } from "react";
import { Heart, Reply } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import { CommentForm } from "./comment-form";
import type { Comment } from "@/lib/types/comment";

interface CommentItemProps {
  comment: Comment;
  novelId: string;
  depth?: number;           // 0 = top-level, 1 = reply
  replies?: Comment[];      // pre-loaded replies for top-level
  onReplyAdded?: (c: Comment) => void;
}

export function CommentItem({ comment, novelId, depth = 0, replies = [], onReplyAdded }: CommentItemProps) {
  const { user } = useUser();
  const [likes, setLikes] = useState(comment.likes);
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [localReplies, setLocalReplies] = useState<Comment[]>(replies);

  async function handleLike() {
    if (!user) return;
    try {
      const updated = await apiFetch<Comment>(`/comments/${comment.id}/like`, { method: "POST" });
      setLikes(updated.likes);
    } catch {}
  }

  function handleReplySuccess(c: Comment) {
    setLocalReplies((prev) => [...prev, c]);
    setShowReplyForm(false);
    onReplyAdded?.(c);
  }

  return (
    <div className={depth > 0 ? "ml-8 border-l pl-4" : ""}>
      <div className="rounded-lg border p-3 space-y-2">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{comment.user_id.slice(0, 8)}…</span>
          <span>{new Date(comment.created_at).toLocaleDateString("vi-VN")}</span>
        </div>
        <p className="text-sm whitespace-pre-wrap">{comment.content}</p>
        <div className="flex items-center gap-3">
          <button
            onClick={handleLike}
            disabled={!user}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-red-500 transition-colors disabled:cursor-not-allowed"
          >
            <Heart className="h-3.5 w-3.5" />
            {likes}
          </button>
          {depth === 0 && user && (
            <button
              onClick={() => setShowReplyForm((v) => !v)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <Reply className="h-3.5 w-3.5" />
              Trả lời
            </button>
          )}
        </div>
      </div>

      {showReplyForm && (
        <div className="mt-2 ml-4">
          <CommentForm
            novelId={novelId}
            parentId={comment.id}
            onSuccess={handleReplySuccess}
            onCancel={() => setShowReplyForm(false)}
            placeholder="Viết câu trả lời..."
          />
        </div>
      )}

      {localReplies.length > 0 && (
        <div className="mt-2 space-y-2">
          {localReplies.map((r) => (
            <CommentItem key={r.id} comment={r} novelId={novelId} depth={1} />
          ))}
        </div>
      )}
    </div>
  );
}
