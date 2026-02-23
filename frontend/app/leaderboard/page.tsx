"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Star, Trophy } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import type { LeaderboardResponse, LeaderboardEntry } from "@/lib/types/social";

const PERIOD_LABELS: Record<string, string> = {
  daily: "Hôm nay",
  weekly: "Tuần này",
  monthly: "Tháng này",
};

const RANK_COLORS: Record<number, string> = {
  1: "bg-yellow-400 text-yellow-900",
  2: "bg-gray-300 text-gray-800",
  3: "bg-amber-600 text-amber-50",
};

function RankBadge({ rank }: { rank: number }) {
  const cls = RANK_COLORS[rank] ?? "bg-muted text-muted-foreground";
  return (
    <span className={`inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${cls}`}>
      {rank}
    </span>
  );
}

function LeaderboardCard({ entry }: { entry: LeaderboardEntry }) {
  const novel = entry.novel;
  if (!novel) return null;

  return (
    <div className="flex items-center gap-4 rounded-lg border bg-card p-3 transition-shadow hover:shadow-md">
      <RankBadge rank={entry.rank} />

      {/* Cover */}
      <Link href={`/novels/${novel.id}`} className="relative h-16 w-11 shrink-0 overflow-hidden rounded">
        {novel.cover_url ? (
          <Image
            src={novel.cover_url}
            alt={novel.title}
            fill
            className="object-cover"
            sizes="44px"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-primary/20 to-primary/5 text-xl">
            📖
          </div>
        )}
      </Link>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <Link
          href={`/novels/${novel.id}`}
          className="line-clamp-1 font-semibold hover:text-primary"
        >
          {novel.title}
        </Link>
        <p className="mt-0.5 line-clamp-1 text-sm text-muted-foreground">{novel.author}</p>
        <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
            {novel.avg_rating > 0 ? novel.avg_rating.toFixed(1) : "—"}
          </span>
          <span>{novel.total_chapters.toLocaleString("vi-VN")} chương</span>
        </div>
      </div>

      {/* Score */}
      <Badge variant="secondary" className="shrink-0 gap-1">
        <Trophy className="h-3 w-3" />
        {entry.score.toLocaleString("vi-VN")}
      </Badge>
    </div>
  );
}

function EmptyLeaderboard() {
  return (
    <div className="flex min-h-[200px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed">
      <Trophy className="h-12 w-12 text-muted-foreground" />
      <p className="text-muted-foreground">Chưa có đề cử nào trong kỳ này.</p>
      <Link href="/novels" className="text-sm text-primary underline-offset-4 hover:underline">
        Khám phá truyện để đề cử
      </Link>
    </div>
  );
}

export default function LeaderboardPage() {
  const [activeTab, setActiveTab] = useState("daily");
  // undefined = not yet fetched; [] = fetched but empty; [...] = fetched with entries
  const [data, setData] = useState<Record<string, LeaderboardEntry[]>>({});

  useEffect(() => {
    if (activeTab in data) return; // already fetched
    apiFetch<LeaderboardResponse>(`/novels/leaderboard?period=${activeTab}`)
      .then((res) => setData((prev) => ({ ...prev, [activeTab]: res.entries })))
      .catch(() => setData((prev) => ({ ...prev, [activeTab]: [] })));
  }, [activeTab, data]);

  const isLoading = !(activeTab in data);
  const entries = data[activeTab] ?? [];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center gap-3">
        <Trophy className="h-8 w-8 text-yellow-400" />
        <h1 className="text-3xl font-bold">Bảng xếp hạng</h1>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-6">
          {Object.entries(PERIOD_LABELS).map(([period, label]) => (
            <TabsTrigger key={period} value={period}>
              {label}
            </TabsTrigger>
          ))}
        </TabsList>

        {Object.keys(PERIOD_LABELS).map((period) => (
          <TabsContent key={period} value={period}>
            {isLoading ? (
              <p className="py-12 text-center text-muted-foreground">Đang tải...</p>
            ) : entries.length === 0 ? (
              <EmptyLeaderboard />
            ) : (
              <div className="flex flex-col gap-2">
                {entries.map((entry) => (
                  <LeaderboardCard key={entry.novel_id} entry={entry} />
                ))}
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
