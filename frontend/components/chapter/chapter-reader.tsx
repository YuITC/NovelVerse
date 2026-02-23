"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import type { ChapterContent } from "@/lib/types/chapter";
import { apiFetch } from "@/lib/api";

interface ReaderSettings {
  fontSize: number;
  bgColor: "white" | "sepia" | "dark";
}

const DEFAULT_SETTINGS: ReaderSettings = { fontSize: 18, bgColor: "white" };

const BG_CLASSES: Record<ReaderSettings["bgColor"], string> = {
  white: "bg-white text-gray-900",
  sepia: "bg-amber-50 text-gray-800",
  dark: "bg-gray-900 text-gray-100",
};

export function ChapterReader({
  chapter,
  novelId,
}: {
  chapter: ChapterContent;
  novelId: string;
}) {
  const [settings, setSettings] = useState<ReaderSettings>(() => {
    if (typeof window === "undefined") return DEFAULT_SETTINGS;
    const stored = localStorage.getItem("nv_reader_settings");
    if (stored) {
      try { return JSON.parse(stored) as ReaderSettings; } catch { /* ignore */ }
    }
    return DEFAULT_SETTINGS;
  });
  const [marked, setMarked] = useState(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const updateSettings = (patch: Partial<ReaderSettings>) => {
    const next = { ...settings, ...patch };
    setSettings(next);
    localStorage.setItem("nv_reader_settings", JSON.stringify(next));
  };

  // Auto-mark as read when user scrolls to bottom
  useEffect(() => {
    if (marked) return;
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !marked) {
          setMarked(true);
          apiFetch(`/novels/${novelId}/chapters/${chapter.chapter_number}/read`, {
            method: "POST",
          }).catch(() => {});
        }
      },
      { threshold: 0.5 }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [marked, novelId, chapter.chapter_number]);

  return (
    <div className={`min-h-screen transition-colors ${BG_CLASSES[settings.bgColor]}`}>
      {/* Settings bar */}
      <div className="sticky top-14 z-40 border-b bg-inherit px-4 py-2">
        <div className="container mx-auto flex items-center gap-4">
          <span className="text-sm text-muted-foreground">Cỡ chữ:</span>
          <button
            onClick={() =>
              updateSettings({ fontSize: Math.max(14, settings.fontSize - 1) })
            }
            className="rounded px-2 py-1 text-sm hover:bg-black/10"
            aria-label="Giảm cỡ chữ"
          >
            A-
          </button>
          <span className="text-sm">{settings.fontSize}px</span>
          <button
            onClick={() =>
              updateSettings({ fontSize: Math.min(24, settings.fontSize + 1) })
            }
            className="rounded px-2 py-1 text-sm hover:bg-black/10"
            aria-label="Tăng cỡ chữ"
          >
            A+
          </button>
          <span className="ml-4 text-sm text-muted-foreground">Nền:</span>
          {(["white", "sepia", "dark"] as const).map((c) => (
            <button
              key={c}
              onClick={() => updateSettings({ bgColor: c })}
              className={`h-6 w-6 rounded-full border-2 transition ${
                settings.bgColor === c ? "border-primary" : "border-transparent"
              }`}
              style={{
                background:
                  c === "white" ? "#fff" : c === "sepia" ? "#f5f0e8" : "#1a1a2e",
              }}
              aria-label={`Nền ${c}`}
            />
          ))}
        </div>
      </div>

      {/* Content */}
      <article
        className="container mx-auto max-w-2xl px-4 py-8 leading-relaxed"
        style={{ fontSize: `${settings.fontSize}px`, fontFamily: "Georgia, serif" }}
      >
        <div className="whitespace-pre-wrap">{chapter.content}</div>
      </article>

      {/* Sentinel for auto-read */}
      <div ref={sentinelRef} className="h-4" />

      {/* Navigation */}
      <nav className="container mx-auto flex items-center justify-between px-4 py-6">
        {chapter.prev_chapter != null ? (
          <Link
            href={`/novels/${novelId}/chapters/${chapter.prev_chapter}`}
            className="rounded-lg border px-4 py-2 text-sm hover:bg-muted"
          >
            ← Chương {chapter.prev_chapter}
          </Link>
        ) : (
          <div />
        )}
        <Link
          href={`/novels/${novelId}`}
          className="rounded-lg border px-4 py-2 text-sm hover:bg-muted"
        >
          Mục lục
        </Link>
        {chapter.next_chapter != null ? (
          <Link
            href={`/novels/${novelId}/chapters/${chapter.next_chapter}`}
            className="rounded-lg border px-4 py-2 text-sm hover:bg-muted"
          >
            Chương {chapter.next_chapter} →
          </Link>
        ) : (
          <div />
        )}
      </nav>
    </div>
  );
}
