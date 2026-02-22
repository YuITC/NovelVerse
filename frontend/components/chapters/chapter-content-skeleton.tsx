import { Skeleton } from "@/components/ui/skeleton"

export function ChapterContentSkeleton() {
  return (
    <div className="mx-auto max-w-2xl space-y-4 py-8">
      <Skeleton className="h-8 w-2/3 mx-auto" />
      <Skeleton className="h-4 w-1/3 mx-auto" />
      <div className="space-y-3 pt-6">
        {Array.from({ length: 20 }).map((_, i) => (
          <Skeleton key={i} className={`h-4 ${i % 5 === 4 ? "w-2/3" : "w-full"}`} />
        ))}
      </div>
    </div>
  )
}
