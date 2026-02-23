"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { LibraryItem } from "@/lib/types/chapter";
import type { BookmarkedNovel } from "@/lib/types/social";
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

function NovelCard({
  href,
  coverUrl,
  title,
  novelId,
  sublabel,
  timestamp,
}: {
  href: string;
  coverUrl: string | null;
  title: string;
  novelId: string;
  sublabel: string;
  timestamp: string;
}) {
  return (
    <div className="group flex flex-col overflow-hidden rounded-lg border bg-card shadow-sm transition-shadow hover:shadow-md">
      <Link href={href} className="relative block aspect-[2/3] overflow-hidden bg-muted">
        {coverUrl ? (
          <Image
            src={coverUrl}
            alt={title}
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
      <div className="flex flex-col gap-1 p-3">
        <Link href={`/novels/${novelId}`} className="line-clamp-2 text-sm font-semibold leading-tight hover:text-primary">
          {title}
        </Link>
        <p className="mt-1 text-xs text-primary">
          <Link href={href}>{sublabel}</Link>
        </p>
        <p className="mt-1 text-xs text-muted-foreground">{formatRelativeTime(timestamp)}</p>
      </div>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex min-h-[200px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed">
      <BookOpen className="h-12 w-12 text-muted-foreground" />
      <p className="text-muted-foreground">{message}</p>
      <Link href="/novels" className="text-sm text-primary underline-offset-4 hover:underline">
        Khám phá truyện
      </Link>
    </div>
  );
}

export default function LibraryPage() {
  const { user, loading: userLoading } = useUser();
  const router = useRouter();

  const [library, setLibrary] = useState<LibraryItem[]>([]);
  const [bookmarks, setBookmarks] = useState<BookmarkedNovel[]>([]);
  const [activeTab, setActiveTab] = useState("reading");

  useEffect(() => {
    if (userLoading) return;
    if (!user) router.replace("/");
  }, [user, userLoading, router]);

  useEffect(() => {
    if (!user || userLoading) return;
    apiFetch<LibraryItem[]>("/users/me/library").then(setLibrary).catch(() => null);
  }, [user, userLoading]);

  useEffect(() => {
    if (!user || userLoading || activeTab !== "bookmarked") return;
    apiFetch<BookmarkedNovel[]>("/users/me/bookmarks").then(setBookmarks).catch(() => null);
  }, [user, userLoading, activeTab]);

  if (userLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-muted-foreground">Đang tải thư viện...</p>
      </div>
    );
  }

  const completedItems = library.filter((item) => item.novel?.status === "completed");

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="mb-6 text-3xl font-bold">Thư viện của tôi</h1>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-6">
          <TabsTrigger value="reading">Đang đọc ({library.length})</TabsTrigger>
          <TabsTrigger value="bookmarked">Đánh dấu ({bookmarks.length})</TabsTrigger>
          <TabsTrigger value="completed">Hoàn thành ({completedItems.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="reading">
          {library.length === 0 ? (
            <EmptyState message="Chưa đọc truyện nào. Hãy bắt đầu đọc!" />
          ) : (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
              {library.map((item) => {
                const novel = item.novel;
                if (!novel) return null;
                return (
                  <NovelCard
                    key={item.novel_id}
                    href={`/novels/${novel.id}/chapters/${item.last_chapter_read}`}
                    coverUrl={novel.cover_url}
                    title={novel.title}
                    novelId={novel.id}
                    sublabel={`Đang đọc chương ${item.last_chapter_read} / ${novel.total_chapters}`}
                    timestamp={item.updated_at}
                  />
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="bookmarked">
          {bookmarks.length === 0 ? (
            <EmptyState message="Chưa lưu truyện nào." />
          ) : (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
              {bookmarks.map((item) => {
                const novel = item.novel;
                if (!novel) return null;
                return (
                  <NovelCard
                    key={item.novel_id}
                    href={`/novels/${novel.id}`}
                    coverUrl={novel.cover_url}
                    title={novel.title}
                    novelId={novel.id}
                    sublabel={STATUS_LABELS[novel.status] ?? novel.status}
                    timestamp={item.added_at}
                  />
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="completed">
          {completedItems.length === 0 ? (
            <EmptyState message="Chưa đọc xong truyện nào." />
          ) : (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
              {completedItems.map((item) => {
                const novel = item.novel;
                if (!novel) return null;
                return (
                  <NovelCard
                    key={item.novel_id}
                    href={`/novels/${novel.id}/chapters/${item.last_chapter_read}`}
                    coverUrl={novel.cover_url}
                    title={novel.title}
                    novelId={novel.id}
                    sublabel={`Đã đọc ${item.last_chapter_read} / ${novel.total_chapters} chương`}
                    timestamp={item.updated_at}
                  />
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
