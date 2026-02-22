import Link from "next/link";
import { Lock, BookPlus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ChapterListItem } from "@/lib/types/chapter";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STATUS_LABELS: Record<"draft" | "scheduled", string> = {
  draft: "Bản nháp",
  scheduled: "Lên lịch",
};

const STATUS_VARIANTS: Record<"draft" | "scheduled", "outline" | "secondary"> = {
  draft: "outline",
  scheduled: "secondary",
};

interface ChapterListProps {
  novelId: string;
  uploaderView?: boolean;
}

export async function ChapterList({ novelId, uploaderView = false }: ChapterListProps) {
  const res = await fetch(`${API_URL}/api/v1/novels/${novelId}/chapters`, {
    next: { revalidate: 60 },
  });
  const chapters: ChapterListItem[] = res.ok ? await res.json() : [];

  const now = new Date();

  return (
    <div>
      {uploaderView && (
        <div className="mb-4 flex justify-end">
          <Button asChild size="sm">
            <Link href={`/novels/${novelId}/chapters/new`}>
              <BookPlus className="mr-2 h-4 w-4" />
              Thêm chương
            </Link>
          </Button>
        </div>
      )}

      {chapters.length === 0 ? (
        <div className="flex min-h-[120px] items-center justify-center rounded-lg border border-dashed">
          <p className="text-muted-foreground">Chưa có chương nào.</p>
        </div>
      ) : (
        <div className="divide-y rounded-lg border">
          {chapters.map((chapter) => {
            const isVipLocked =
              chapter.publish_at != null &&
              new Date(chapter.publish_at) > now;

            return (
              <Link
                key={chapter.id}
                href={`/novels/${novelId}/chapters/${chapter.chapter_number}`}
                className="flex items-center justify-between px-4 py-3 text-sm transition-colors hover:bg-muted/50"
              >
                <div className="flex min-w-0 items-center gap-2">
                  {isVipLocked && (
                    <Lock className="h-3.5 w-3.5 shrink-0 text-yellow-500" />
                  )}
                  <span className="truncate font-medium">
                    Chương {chapter.chapter_number}
                    {chapter.title ? `: ${chapter.title}` : ""}
                  </span>
                  {chapter.status !== "published" && (
                    <Badge
                      variant={STATUS_VARIANTS[chapter.status]}
                      className="shrink-0"
                    >
                      {STATUS_LABELS[chapter.status]}
                    </Badge>
                  )}
                </div>
                <span className="ml-4 shrink-0 text-muted-foreground">
                  {chapter.word_count.toLocaleString("vi-VN")} chữ
                </span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
