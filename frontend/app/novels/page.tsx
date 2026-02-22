import Link from "next/link";
import { NovelGrid } from "@/components/novel/novel-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Tag, NovelListResponse } from "@/lib/types/novel";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchTags(): Promise<Tag[]> {
  try {
    const res = await fetch(`${API_URL}/api/v1/novels/tags`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

async function fetchNovels(params: URLSearchParams): Promise<NovelListResponse> {
  try {
    const res = await fetch(
      `${API_URL}/api/v1/novels?${params.toString()}`,
      { next: { revalidate: 60 } }
    );
    if (!res.ok) return { items: [], next_cursor: null };
    return res.json();
  } catch {
    return { items: [], next_cursor: null };
  }
}

const STATUS_OPTIONS = [
  { label: "Tất cả", value: "" },
  { label: "Đang ra", value: "ongoing" },
  { label: "Hoàn thành", value: "completed" },
  { label: "Tạm dừng", value: "dropped" },
];

const SORT_OPTIONS = [
  { label: "Mới cập nhật", value: "updated_at" },
  { label: "Lượt xem", value: "total_views" },
  { label: "Đánh giá", value: "avg_rating" },
];

interface BrowsePageProps {
  searchParams: Promise<{
    q?: string;
    tag?: string;
    status?: string;
    sort?: string;
    cursor?: string;
  }>;
}

export default async function BrowsePage({ searchParams }: BrowsePageProps) {
  const params = await searchParams;
  const { q = "", tag = "", status = "", sort = "updated_at", cursor = "" } = params;

  const queryParams = new URLSearchParams();
  if (q) queryParams.set("q", q);
  if (tag) queryParams.set("tag", tag);
  if (status) queryParams.set("status", status);
  if (sort) queryParams.set("sort", sort);
  if (cursor) queryParams.set("cursor", cursor);
  queryParams.set("limit", "20");

  const [tags, { items: novels, next_cursor }] = await Promise.all([
    fetchTags(),
    fetchNovels(queryParams),
  ]);

  function buildUrl(overrides: Record<string, string>) {
    const merged: Record<string, string> = { q, tag, status, sort };
    Object.assign(merged, overrides);
    // Remove empty values and cursor when filters change
    const url = new URLSearchParams();
    Object.entries(merged).forEach(([k, v]) => {
      if (v) url.set(k, v);
    });
    return `/novels?${url.toString()}`;
  }

  const loadMoreUrl = (() => {
    const url = new URLSearchParams();
    if (q) url.set("q", q);
    if (tag) url.set("tag", tag);
    if (status) url.set("status", status);
    if (sort) url.set("sort", sort);
    if (next_cursor) url.set("cursor", next_cursor);
    return `/novels?${url.toString()}`;
  })();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col gap-8 lg:flex-row">
        {/* Sidebar */}
        <aside className="w-full shrink-0 lg:w-56">
          {/* Status filter */}
          <div className="mb-6">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Trạng thái
            </h3>
            <ul className="space-y-1">
              {STATUS_OPTIONS.map((opt) => (
                <li key={opt.value}>
                  <Link
                    href={buildUrl({ status: opt.value, cursor: "" })}
                    className={`block rounded px-2 py-1 text-sm transition-colors hover:bg-muted ${
                      status === opt.value
                        ? "bg-primary text-primary-foreground hover:bg-primary/90"
                        : ""
                    }`}
                  >
                    {opt.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Sort */}
          <div className="mb-6">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Sắp xếp
            </h3>
            <ul className="space-y-1">
              {SORT_OPTIONS.map((opt) => (
                <li key={opt.value}>
                  <Link
                    href={buildUrl({ sort: opt.value, cursor: "" })}
                    className={`block rounded px-2 py-1 text-sm transition-colors hover:bg-muted ${
                      sort === opt.value
                        ? "bg-primary text-primary-foreground hover:bg-primary/90"
                        : ""
                    }`}
                  >
                    {opt.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Tags */}
          {tags.length > 0 && (
            <div>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                Thể loại
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {tags.map((t) => (
                  <Link
                    key={t.id}
                    href={buildUrl({ tag: tag === t.slug ? "" : t.slug, cursor: "" })}
                  >
                    <Badge
                      variant={tag === t.slug ? "default" : "outline"}
                      className="cursor-pointer text-xs"
                    >
                      {t.name}
                    </Badge>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-2xl font-bold">
              {q ? `Kết quả tìm kiếm: "${q}"` : "Danh sách truyện"}
            </h1>
          </div>

          <NovelGrid novels={novels} />

          {/* Load more */}
          {next_cursor && (
            <div className="mt-8 flex justify-center">
              <Button asChild variant="outline">
                <Link href={loadMoreUrl}>Tải thêm truyện</Link>
              </Button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
