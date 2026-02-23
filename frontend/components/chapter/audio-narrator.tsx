"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ChevronDown, ChevronUp, Loader2, Square, Volume2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { useUser } from "@/lib/hooks/use-user";
import type { ChapterContent } from "@/lib/types/chapter";
import type { ChapterNarration } from "@/lib/types/ai";
import type { VipSubscription } from "@/lib/types/vip";

interface AudioNarratorProps {
  chapter: ChapterContent;
  onHighlight: (lineIndex: number | null) => void;
}

const SPEEDS = [0.75, 1, 1.5, 2] as const;

export function AudioNarrator({ chapter, onHighlight }: AudioNarratorProps) {
  const { user, loading } = useUser();
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState<"web-speech" | "elevenlabs">("web-speech");

  // Web Speech state
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState<number>(1);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // ElevenLabs state
  const [narration, setNarration] = useState<ChapterNarration | null>(null);
  const [isRequesting, setIsRequesting] = useState(false);
  const [elevenError, setElevenError] = useState<string | null>(null);
  const [isVipMax, setIsVipMax] = useState(false);

  // Pre-compute line offsets for Web Speech boundary → line index mapping
  const lines = useMemo(() => chapter.content.split("\n"), [chapter.content]);
  const lineOffsets = useMemo(() => {
    const offsets: number[] = [];
    let off = 0;
    for (const line of lines) {
      offsets.push(off);
      off += line.length + 1; // +1 for \n
    }
    return offsets;
  }, [lines]);

  // Check VIP Max status
  useEffect(() => {
    if (!user) return;
    apiFetch<VipSubscription[]>("/vip/me")
      .then((subs) => {
        const active = subs.find(
          (s) =>
            s.status === "active" &&
            s.vip_tier === "max" &&
            s.expires_at &&
            new Date(s.expires_at) > new Date()
        );
        setIsVipMax(!!active);
      })
      .catch(() => {});
  }, [user]);

  // On mount / chapter change: try to load cached narration
  useEffect(() => {
    if (!user) return;
    apiFetch<ChapterNarration>(`/tts/chapters/${chapter.id}`)
      .then(setNarration)
      .catch(() => {}); // 404 = not yet generated
  }, [chapter.id, user]);

  // Poll while pending
  useEffect(() => {
    if (narration?.status !== "pending") return;
    const id = setInterval(async () => {
      try {
        const updated = await apiFetch<ChapterNarration>(
          `/tts/chapters/${chapter.id}`
        );
        setNarration(updated);
        if (updated.status !== "pending") clearInterval(id);
      } catch {
        clearInterval(id);
      }
    }, 3000);
    return () => clearInterval(id);
  }, [narration?.status, chapter.id]);

  // Stop Web Speech on unmount or chapter change
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined") {
        window.speechSynthesis?.cancel();
      }
    };
  }, [chapter.id]);

  // ---------------------------------------------------------------------------
  // Web Speech handlers
  // ---------------------------------------------------------------------------

  const playWebSpeech = useCallback(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();

    const utt = new SpeechSynthesisUtterance(chapter.content);
    utt.lang = "vi-VN";
    utt.rate = speed;

    utt.onboundary = (e) => {
      // Find last line whose start offset ≤ e.charIndex
      let idx = 0;
      for (let j = lineOffsets.length - 1; j >= 0; j--) {
        if (lineOffsets[j] <= e.charIndex) {
          idx = j;
          break;
        }
      }
      onHighlight(idx);
    };

    utt.onend = () => {
      setIsPlaying(false);
      onHighlight(null);
    };

    utt.onerror = () => {
      setIsPlaying(false);
      onHighlight(null);
    };

    utteranceRef.current = utt;
    window.speechSynthesis.speak(utt);
    setIsPlaying(true);
  }, [chapter.content, speed, lineOffsets, onHighlight]);

  const stopWebSpeech = useCallback(() => {
    window.speechSynthesis?.cancel();
    setIsPlaying(false);
    onHighlight(null);
  }, [onHighlight]);

  // ---------------------------------------------------------------------------
  // ElevenLabs handlers
  // ---------------------------------------------------------------------------

  async function requestGeneration() {
    setIsRequesting(true);
    setElevenError(null);
    try {
      const result = await apiFetch<ChapterNarration>(
        `/tts/chapters/${chapter.id}`,
        { method: "POST" }
      );
      setNarration(result);
    } catch {
      setElevenError("Không thể tạo audio. Vui lòng thử lại.");
    } finally {
      setIsRequesting(false);
    }
  }

  async function retryGeneration() {
    setNarration(null);
    await requestGeneration();
  }

  if (loading) return null;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="sticky top-[calc(theme(spacing.14)+2.5rem)] z-30 border-b bg-inherit">
      {/* Collapsed toggle row */}
      <div className="container mx-auto max-w-2xl px-4">
        <button
          onClick={() => setIsOpen((o) => !o)}
          className="flex w-full items-center gap-2 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          aria-expanded={isOpen}
        >
          <Volume2 className="h-4 w-4 shrink-0" />
          <span className="font-medium">Nghe truyện</span>
          {isOpen ? (
            <ChevronUp className="ml-auto h-4 w-4" />
          ) : (
            <ChevronDown className="ml-auto h-4 w-4" />
          )}
        </button>
      </div>

      {/* Expanded panel */}
      {isOpen && (
        <div className="container mx-auto max-w-2xl px-4 pb-3">
          {/* Mode tabs */}
          <div className="mb-3 flex gap-1 rounded-lg border p-1 text-xs w-fit">
            <button
              onClick={() => setMode("web-speech")}
              className={`rounded px-3 py-1 transition-colors ${
                mode === "web-speech"
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              }`}
            >
              Miễn phí
            </button>
            <button
              onClick={() => setMode("elevenlabs")}
              className={`flex items-center gap-1 rounded px-3 py-1 transition-colors ${
                mode === "elevenlabs"
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              }`}
            >
              AI Voice
              <span className="inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold bg-purple-100 text-purple-800 border border-purple-300 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-700">
                VIP Max
              </span>
            </button>
          </div>

          {/* Free mode (Web Speech API) */}
          {mode === "web-speech" && (
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                {!isPlaying ? (
                  <Button size="sm" className="h-8" onClick={playWebSpeech}>
                    ▶ Phát
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-8"
                    onClick={stopWebSpeech}
                  >
                    <Square className="h-3 w-3 mr-1" />
                    Dừng
                  </Button>
                )}
              </div>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <span>Tốc độ:</span>
                {SPEEDS.map((s) => (
                  <button
                    key={s}
                    onClick={() => {
                      setSpeed(s);
                      if (isPlaying) {
                        // Restart with new speed
                        window.speechSynthesis?.cancel();
                        setIsPlaying(false);
                        onHighlight(null);
                      }
                    }}
                    className={`rounded px-2 py-0.5 transition-colors ${
                      speed === s
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-muted"
                    }`}
                  >
                    {s}x
                  </button>
                ))}
              </div>
              {isPlaying && (
                <p className="text-xs text-muted-foreground ml-auto">
                  Đang phát...
                </p>
              )}
            </div>
          )}

          {/* ElevenLabs mode */}
          {mode === "elevenlabs" && (
            <div>
              {/* Non-VIP Max gate */}
              {!user && (
                <div className="text-center py-2 space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Đăng nhập để sử dụng tính năng AI Voice.
                  </p>
                  <Button asChild size="sm">
                    <Link href="/login">Đăng nhập</Link>
                  </Button>
                </div>
              )}

              {user && !isVipMax && (
                <div className="text-center py-2 space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Tính năng AI Voice dành riêng cho VIP Max.
                  </p>
                  <Button asChild size="sm">
                    <Link href="/vip">Nâng cấp VIP Max</Link>
                  </Button>
                </div>
              )}

              {user && isVipMax && (
                <div>
                  {/* Not yet generated */}
                  {!narration && !isRequesting && (
                    <div className="flex items-center gap-3">
                      <Button size="sm" className="h-8" onClick={requestGeneration}>
                        ✨ Tạo audio AI
                      </Button>
                      <p className="text-xs text-muted-foreground">
                        Tạo giọng đọc AI chất lượng cao cho chương này.
                      </p>
                    </div>
                  )}

                  {/* Requesting / pending */}
                  {(isRequesting || narration?.status === "pending") && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Đang tạo audio... (có thể mất vài phút)</span>
                    </div>
                  )}

                  {/* Ready */}
                  {narration?.status === "ready" && narration.audio_url && (
                    <div className="space-y-2">
                      <audio
                        src={narration.audio_url}
                        controls
                        className="w-full h-10"
                      />
                    </div>
                  )}

                  {/* Failed */}
                  {narration?.status === "failed" && (
                    <div className="flex items-center gap-3">
                      <p className="text-xs text-destructive">
                        {elevenError ?? "Lỗi tạo audio."}
                      </p>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 text-xs"
                        onClick={retryGeneration}
                        disabled={isRequesting}
                      >
                        Thử lại
                      </Button>
                    </div>
                  )}

                  {/* Request error (API rejected) */}
                  {!narration && elevenError && (
                    <div className="flex items-center gap-3">
                      <p className="text-xs text-destructive">{elevenError}</p>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 text-xs"
                        onClick={requestGeneration}
                        disabled={isRequesting}
                      >
                        Thử lại
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
