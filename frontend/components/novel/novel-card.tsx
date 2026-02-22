import Image from "next/image";
import Link from "next/link";
import { Star, BookOpen } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { NovelListItem } from "@/lib/types/novel";

const STATUS_LABELS: Record<NovelListItem["status"], string> = {
  ongoing: "Đang ra",
  completed: "Hoàn thành",
  dropped: "Tạm dừng",
};

const STATUS_VARIANTS: Record<
  NovelListItem["status"],
  "default" | "secondary" | "outline"
> = {
  ongoing: "default",
  completed: "secondary",
  dropped: "outline",
};

interface NovelCardProps {
  novel: NovelListItem;
}

export function NovelCard({ novel }: NovelCardProps) {
  const statusLabel = STATUS_LABELS[novel.status];
  const statusVariant = STATUS_VARIANTS[novel.status];

  return (
    <Link href={`/novels/${novel.id}`} className="group block">
      <div className="overflow-hidden rounded-lg border bg-card transition-shadow hover:shadow-md">
        {/* Cover */}
        <div className="relative aspect-[2/3] bg-muted">
          {novel.cover_url ? (
            <Image
              src={novel.cover_url}
              alt={novel.title}
              fill
              className="object-cover transition-transform duration-300 group-hover:scale-105"
              sizes="(max-width: 640px) 50vw, (max-width: 768px) 33vw, (max-width: 1024px) 25vw, (max-width: 1280px) 20vw, 16vw"
            />
          ) : (
            <div className="flex h-full items-center justify-center bg-gradient-to-br from-primary/20 to-primary/5">
              <span className="text-4xl">📖</span>
            </div>
          )}
          <Badge
            className="absolute right-2 top-2 text-xs"
            variant={statusVariant}
          >
            {statusLabel}
          </Badge>
        </div>

        {/* Info */}
        <div className="p-3">
          <h3 className="line-clamp-2 font-semibold leading-snug group-hover:text-primary">
            {novel.title}
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">{novel.author}</p>

          {/* Tags */}
          {novel.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {novel.tags.slice(0, 2).map((tag) => (
                <Badge key={tag.id} variant="outline" className="text-xs px-1.5 py-0">
                  {tag.name}
                </Badge>
              ))}
            </div>
          )}

          {/* Stats */}
          <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <BookOpen className="h-3 w-3" />
              {novel.total_chapters.toLocaleString("vi-VN")}
            </span>
            <span className="flex items-center gap-1">
              <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
              {novel.avg_rating > 0 ? novel.avg_rating.toFixed(1) : "—"}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
