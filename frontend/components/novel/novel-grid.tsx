import { NovelCard } from "@/components/novel/novel-card";
import type { NovelListItem } from "@/lib/types/novel";
import { cn } from "@/lib/utils";

interface NovelGridProps {
  novels: NovelListItem[];
  className?: string;
}

export function NovelGrid({ novels, className }: NovelGridProps) {
  if (novels.length === 0) {
    return (
      <div className="flex min-h-[200px] items-center justify-center rounded-lg border border-dashed">
        <p className="text-muted-foreground">Không có truyện nào.</p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6",
        className
      )}
    >
      {novels.map((novel) => (
        <NovelCard key={novel.id} novel={novel} />
      ))}
    </div>
  );
}
