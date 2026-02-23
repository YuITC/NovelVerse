import { notFound } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import type { Metadata } from "next";
import { Star, Eye, BookOpen, MessageSquare, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChapterList } from "@/components/chapter/chapter-list";
import { ReviewSection } from "@/components/review/review-section";
import { CommentSection } from "@/components/comment/comment-section";
import { ChatPanel } from "@/components/ai/chat-panel";
import { StoryIntelligencePanel } from "@/components/ai/story-intelligence-panel";
import { BookmarkButton } from "@/components/social/bookmark-button";
import { FollowButton } from "@/components/social/follow-button";
import { NominateButton } from "@/components/social/nominate-button";
import type { Novel } from "@/lib/types/novel";
import type { CharacterListResponse } from "@/lib/types/ai";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STATUS_LABELS: Record<Novel["status"], string> = {
  ongoing: "Đang ra",
  completed: "Hoàn thành",
  dropped: "Tạm dừng",
};

const STATUS_VARIANTS: Record<
  Novel["status"],
  "default" | "secondary" | "outline"
> = {
  ongoing: "default",
  completed: "secondary",
  dropped: "outline",
};

async function fetchNovel(id: string): Promise<Novel> {
  const res = await fetch(`${API_URL}/api/v1/novels/${id}`, {
    next: { revalidate: 60 },
  });
  if (res.status === 404) notFound();
  if (!res.ok) throw new Error(`Failed to fetch novel: ${res.status}`);
  return res.json();
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const novel = await fetchNovel(id).catch(() => null);
  return {
    title: novel?.title ?? "Không tìm thấy truyện",
    description: novel?.description
      ?.replace(/<[^>]+>/g, "")
      .slice(0, 160),
    openGraph: {
      images: novel?.cover_url ? [novel.cover_url] : [],
    },
  };
}

export default async function NovelDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const novel = await fetchNovel(id);

  // Fetch characters for Chat panel (public endpoint — no auth needed)
  const characterData = await fetch(
    `${API_URL}/api/v1/chat/novels/${id}/characters`,
    { next: { revalidate: 60 } }
  )
    .then((r) => (r.ok ? (r.json() as Promise<CharacterListResponse>) : null))
    .catch(() => null);
  const characters = characterData?.items ?? [];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Top section: cover + info */}
      <div className="flex flex-col gap-8 md:flex-row">
        {/* Cover */}
        <div className="mx-auto w-48 shrink-0 md:mx-0 md:w-56">
          <div className="relative aspect-[2/3] overflow-hidden rounded-lg border shadow-md">
            {novel.cover_url ? (
              <Image
                src={novel.cover_url}
                alt={novel.title}
                fill
                className="object-cover"
                sizes="(max-width: 768px) 192px, 224px"
                priority
              />
            ) : (
              <div className="flex h-full items-center justify-center bg-gradient-to-br from-primary/20 to-primary/5">
                <span className="text-6xl">📖</span>
              </div>
            )}
          </div>
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <h1 className="text-3xl font-bold leading-tight">{novel.title}</h1>
          {novel.original_title && (
            <p className="mt-1 text-base text-muted-foreground">
              {novel.original_title}
            </p>
          )}

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Badge variant={STATUS_VARIANTS[novel.status]}>
              {STATUS_LABELS[novel.status]}
            </Badge>
            {novel.tags.map((tag) => (
              <Link key={tag.id} href={`/novels?tag=${tag.slug}`}>
                <Badge variant="outline" className="cursor-pointer hover:bg-muted">
                  {tag.name}
                </Badge>
              </Link>
            ))}
          </div>

          {/* Meta */}
          <dl className="mt-4 space-y-2 text-sm">
            <div className="flex gap-2">
              <dt className="font-semibold text-muted-foreground">Tác giả:</dt>
              <dd>{novel.author}</dd>
            </div>
            {novel.uploader && (
              <div className="flex items-center gap-2">
                <dt className="font-semibold text-muted-foreground">Người đăng:</dt>
                <dd className="flex items-center gap-1.5">
                  {novel.uploader.avatar_url ? (
                    <Image
                      src={novel.uploader.avatar_url}
                      alt={novel.uploader.username}
                      width={20}
                      height={20}
                      className="rounded-full"
                    />
                  ) : (
                    <User className="h-4 w-4 text-muted-foreground" />
                  )}
                  {novel.uploader.username}
                  <FollowButton followeeId={novel.uploader.id} />
                </dd>
              </div>
            )}
          </dl>

          {/* Stats bar */}
          <div className="mt-5 flex flex-wrap gap-6 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <BookOpen className="h-4 w-4" />
              <strong className="text-foreground">
                {novel.total_chapters.toLocaleString("vi-VN")}
              </strong>{" "}
              chương
            </span>
            <span className="flex items-center gap-1.5">
              <Eye className="h-4 w-4" />
              <strong className="text-foreground">
                {novel.total_views.toLocaleString("vi-VN")}
              </strong>{" "}
              lượt xem
            </span>
            <span className="flex items-center gap-1.5">
              <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
              <strong className="text-foreground">
                {novel.avg_rating > 0 ? novel.avg_rating.toFixed(1) : "—"}
              </strong>
              {novel.rating_count > 0 && (
                <span>({novel.rating_count.toLocaleString("vi-VN")} đánh giá)</span>
              )}
            </span>
            <span className="flex items-center gap-1.5">
              <MessageSquare className="h-4 w-4" />
              <strong className="text-foreground">
                {novel.total_comments.toLocaleString("vi-VN")}
              </strong>{" "}
              bình luận
            </span>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <BookmarkButton novelId={novel.id} />
            <NominateButton novelId={novel.id} />
            <Button asChild size="lg" variant="outline">
              <Link href={`/novels/${novel.id}/edit`}>Chỉnh sửa</Link>
            </Button>
          </div>
        </div>
      </div>

      {/* Description */}
      {novel.description && (
        <section className="mt-8">
          <h2 className="mb-3 text-xl font-bold">Giới thiệu</h2>
          <div
            className="prose prose-sm max-w-none text-foreground"
            dangerouslySetInnerHTML={{ __html: novel.description }}
          />
        </section>
      )}

      {/* Chat with Characters (VIP Max) */}
      <div className="mt-10">
        <ChatPanel novelId={novel.id} characters={characters} />
      </div>

      {/* Story Intelligence Dashboard (VIP Max) */}
      <div className="mt-10">
        <StoryIntelligencePanel novelId={novel.id} />
      </div>

      {/* Chapter list */}
      <section className="mt-10">
        <h2 className="mb-4 text-xl font-bold">Danh sách chương</h2>
        <ChapterList novelId={novel.id} />
      </section>

      {/* Reviews */}
      <div className="mt-10">
        <ReviewSection
          novelId={novel.id}
          avgRating={novel.avg_rating}
          ratingCount={novel.rating_count}
        />
      </div>

      {/* Comments */}
      <div className="mt-10">
        <CommentSection novelId={novel.id} />
      </div>
    </div>
  );
}
