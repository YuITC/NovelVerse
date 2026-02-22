import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";
import { Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChapterReader } from "@/components/chapter/chapter-reader";
import type { ChapterContent } from "@/lib/types/chapter";

export const revalidate = 0;

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchChapter(
  novelId: string,
  num: string
): Promise<ChapterContent | null> {
  try {
    const res = await fetch(
      `${API_URL}/api/v1/novels/${novelId}/chapters/${num}`,
      { cache: "no-store" }
    );
    if (res.status === 404) return null;
    if (res.status === 403) throw new Error("vip_required");
    if (!res.ok) throw new Error("fetch_error");
    return res.json() as Promise<ChapterContent>;
  } catch (e) {
    throw e;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string; num: string }>;
}): Promise<Metadata> {
  const { id, num } = await params;
  try {
    const chapter = await fetchChapter(id, num);
    return {
      title: chapter
        ? `Chương ${chapter.chapter_number}${
            chapter.title ? `: ${chapter.title}` : ""
          } — ${chapter.novel_title}`
        : "Chương không tìm thấy",
    };
  } catch {
    return { title: "Đọc chương" };
  }
}

export default async function ChapterPage({
  params,
}: {
  params: Promise<{ id: string; num: string }>;
}) {
  const { id, num } = await params;

  let chapter: ChapterContent | null;
  let vipRequired = false;

  try {
    chapter = await fetchChapter(id, num);
  } catch (err) {
    if (err instanceof Error && err.message === "vip_required") {
      vipRequired = true;
      chapter = null;
    } else {
      throw err;
    }
  }

  if (vipRequired) {
    return (
      <div className="flex min-h-[70vh] flex-col items-center justify-center gap-6 px-4 text-center">
        <Lock className="h-16 w-16 text-yellow-500" />
        <h1 className="text-2xl font-bold">Nội dung VIP</h1>
        <p className="max-w-md text-muted-foreground">
          Nội dung này chỉ dành cho VIP Pro/Max. Nâng cấp tài khoản để đọc sớm
          hơn.
        </p>
        <div className="flex gap-3">
          <Button asChild>
            <Link href="/vip">Nâng cấp VIP</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href={`/novels/${id}`}>Quay lại mục lục</Link>
          </Button>
        </div>
      </div>
    );
  }

  if (!chapter) {
    notFound();
  }

  return (
    <div>
      {/* Page header — Server-rendered */}
      <div className="border-b bg-background px-4 py-4">
        <div className="container mx-auto max-w-2xl">
          <Link
            href={`/novels/${id}`}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← {chapter.novel_title ?? "Mục lục"}
          </Link>
          <h1 className="mt-1 text-xl font-bold leading-snug">
            Chương {chapter.chapter_number}
            {chapter.title ? `: ${chapter.title}` : ""}
          </h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {chapter.word_count.toLocaleString("vi-VN")} chữ
          </p>
        </div>
      </div>

      {/* Client-rendered reader (settings + content + nav) */}
      <ChapterReader chapter={chapter} novelId={id} />
    </div>
  );
}
