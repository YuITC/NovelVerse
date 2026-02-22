import { Skeleton } from "@/components/ui/skeleton";

export function NovelCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-lg border bg-card">
      {/* Cover skeleton */}
      <div className="relative aspect-[2/3] bg-muted">
        <Skeleton className="h-full w-full" />
      </div>

      {/* Info skeleton */}
      <div className="p-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="mt-1 h-4 w-2/3" />
        <Skeleton className="mt-1 h-3 w-1/2" />

        {/* Tags skeleton */}
        <div className="mt-2 flex gap-1">
          <Skeleton className="h-4 w-10" />
          <Skeleton className="h-4 w-12" />
        </div>

        {/* Stats skeleton */}
        <div className="mt-2 flex items-center justify-between">
          <Skeleton className="h-3 w-10" />
          <Skeleton className="h-3 w-8" />
        </div>
      </div>
    </div>
  );
}

export function NovelGridSkeleton({ count = 12 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
      {Array.from({ length: count }).map((_, i) => (
        <NovelCardSkeleton key={i} />
      ))}
    </div>
  );
}
