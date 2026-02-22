"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import type { LibraryItem } from "@/lib/types/chapter";
import { BookOpen } from "lucide-react";

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "Hôm nay";
  if (diffDays === 1) return "Hôm qua";
  if (diffDays < 30) return `${diffDays} ngày trước`;
  const diffMonths = Math.floor(diffDays / 30);
  if (diffMonths < 12) return `${diffMonths} tháng trước`;
  return `${Math.floor(diffMonths / 12)} năm trước`;
}

const STATUS_LABELS: Record<string, string> = {
  ongoing: "Đang ra",
  completed: "Hoàn thành",
  dropped: "Tạm dừng",
};

export default function LibraryPage() {
  const { user, loading: userLoading } = useUser();
  const router = useRouter();
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Auth guard
  useEffect(() => {
    if (userLoading) return;
    if (!user) {
      router.replace("/");
    }
  }, [user, userLoading, router]);

  useEffect(() => {
    if (userLoading || !user) return;
    apiFetch<LibraryItem[]>("/users/me/library")
      .then((data) => setItems(data))
      .catch((err) => {
        setError(
          err instanceof Error ? err.message : "Không thể tải thư viện."
        );
      })
      .finally(() => setLoading(false));
  }, [user, userLoading]);

  if (userLoading || loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-muted-foreground">Đang tải thư viện...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-10">
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="mb-6 text-3xl font-bold">Thư viện của tôi</h1>

      {items.length === 0 ? (
        <div className="flex min-h-[200px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed">
          <BookOpen className="h-12 w-12 text-muted-foreground" />
          <p className="text-muted-foreground">
            Thư viện trống. Hãy bắt đầu đọc truyện!
          </p>
          <Link
            href="/novels"
            className="text-sm text-primary underline-offset-4 hover:underline"
          >
            Khám phá truyện
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {items.map((item) => {
            const novel = item.novel;
            if (!novel) return null;

            return (
              <div
                key={item.novel_id}
                className="group flex flex-col overflow-hidden rounded-lg border bg-card shadow-sm transition-shadow hover:shadow-md"
              >
                {/* Cover */}
                <Link
                  href={`/novels/${novel.id}/chapters/${item.last_chapter_read}`}
                  className="relative block aspect-[2/3] overflow-hidden bg-muted"
                >
                  {novel.cover_url ? (
                    <Image
                      src={novel.cover_url}
                      alt={novel.title}
                      fill
                      className="object-cover transition-transform group-hover:scale-105"
                      sizes="(max-width: 640px) 50vw, (max-width: 768px) 33vw, (max-width: 1024px) 25vw, 20vw"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center bg-gradient-to-br from-primary/20 to-primary/5">
                      <span className="text-4xl">📖</span>
                    </div>
                  )}
                </Link>

                {/* Info */}
                <div className="flex flex-col gap-1 p-3">
                  <Link
                    href={`/novels/${novel.id}`}
                    className="line-clamp-2 text-sm font-semibold leading-tight hover:text-primary"
                  >
                    {novel.title}
                  </Link>

                  <p className="text-xs text-muted-foreground">
                    {STATUS_LABELS[novel.status] ?? novel.status}
                  </p>

                  <Link
                    href={`/novels/${novel.id}/chapters/${item.last_chapter_read}`}
                    className="mt-1 text-xs text-primary hover:underline"
                  >
                    Đang đọc chương {item.last_chapter_read} /{" "}
                    {novel.total_chapters}
                  </Link>

                  <p className="mt-1 text-xs text-muted-foreground">
                    {formatRelativeTime(item.updated_at)}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
