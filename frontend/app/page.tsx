import Link from "next/link";
import { NovelGrid } from "@/components/novel/novel-grid";
import { Button } from "@/components/ui/button";
import type { NovelListItem } from "@/lib/types/novel";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchNovelList(path: string): Promise<NovelListItem[]> {
  try {
    const res = await fetch(`${API_URL}/api/v1${path}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const [featured, recentlyUpdated, recentlyCompleted] = await Promise.all([
    fetchNovelList("/novels/featured"),
    fetchNovelList("/novels/recently-updated?limit=12"),
    fetchNovelList("/novels/recently-completed?limit=12"),
  ]);

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary/10 via-background to-secondary/10 py-20 text-center">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
            NovelVerse
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
            Nền tảng đọc tiểu thuyết mạng Trung Quốc hàng đầu bằng tiếng Việt.
            Hàng ngàn bộ truyện hay, cập nhật mỗi ngày.
          </p>
          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Button asChild size="lg">
              <Link href="/novels">Khám phá truyện</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/upload">Đăng truyện</Link>
            </Button>
          </div>
        </div>
      </section>

      <div className="container mx-auto space-y-12 px-4 py-12">
        {/* Featured Novels */}
        {featured.length > 0 && (
          <section>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold">Truyện nổi bật</h2>
              <Button asChild variant="ghost" size="sm">
                <Link href="/novels">Xem tất cả</Link>
              </Button>
            </div>
            <NovelGrid novels={featured} />
          </section>
        )}

        {/* Recently Updated */}
        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-bold">Mới cập nhật</h2>
            <Button asChild variant="ghost" size="sm">
              <Link href="/novels?sort=updated_at">Xem tất cả</Link>
            </Button>
          </div>
          <NovelGrid novels={recentlyUpdated} />
          {recentlyUpdated.length === 0 && (
            <p className="text-center text-muted-foreground">
              Chưa có truyện nào. Hãy quay lại sau!
            </p>
          )}
        </section>

        {/* Recently Completed */}
        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-bold">Truyện đã hoàn thành</h2>
            <Button asChild variant="ghost" size="sm">
              <Link href="/novels?status=completed">Xem tất cả</Link>
            </Button>
          </div>
          <NovelGrid novels={recentlyCompleted} />
          {recentlyCompleted.length === 0 && (
            <p className="text-center text-muted-foreground">
              Chưa có truyện hoàn thành nào.
            </p>
          )}
        </section>
      </div>
    </div>
  );
}
