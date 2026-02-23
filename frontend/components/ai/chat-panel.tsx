"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useChat } from "@/lib/hooks/use-chat";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import type { Character } from "@/lib/types/ai";
import type { VipSubscription } from "@/lib/types/vip";

interface ChatPanelProps {
  novelId: string;
  characters: Character[];
}

export function ChatPanel({ novelId, characters }: ChatPanelProps) {
  const { user, loading } = useUser();
  const [isVipMax, setIsVipMax] = useState(false);
  const [selectedCharId, setSelectedCharId] = useState<string>(
    characters[0]?.id ?? ""
  );
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { session, messages, isStreaming, error, createSession, sendMessage, resetSession } =
    useChat(novelId, selectedCharId);

  // Check VIP Max status — only fires when user is present
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
      .catch(() => setIsVipMax(false));
  }, [user]);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Reset session when character changes
  useEffect(() => {
    resetSession();
  }, [selectedCharId, resetSession]);

  if (loading) return null;

  // Guest: show login CTA
  if (!user) {
    return (
      <section className="rounded-lg border bg-card p-6 text-center space-y-3">
        <h2 className="text-lg font-semibold">Chat with Characters</h2>
        <p className="text-sm text-muted-foreground">
          Đăng nhập để trải nghiệm tính năng chat với nhân vật (VIP Max).
        </p>
        <Button asChild size="sm">
          <Link href="/login">Đăng nhập</Link>
        </Button>
      </section>
    );
  }

  // Non-VIP Max: show upgrade CTA
  if (!isVipMax) {
    return (
      <section className="rounded-lg border bg-card p-6 text-center space-y-3">
        <h2 className="text-lg font-semibold">
          Chat with Characters{" "}
          <span className="ml-2 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-300 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-700">
            VIP Max
          </span>
        </h2>
        <p className="text-sm text-muted-foreground">
          Tính năng này chỉ dành cho thành viên VIP Max. Nâng cấp để trò chuyện
          trực tiếp với các nhân vật trong truyện nhờ công nghệ AI.
        </p>
        <Button asChild size="sm">
          <Link href="/vip">Nâng cấp VIP Max</Link>
        </Button>
      </section>
    );
  }

  if (characters.length === 0) {
    return (
      <section className="rounded-lg border bg-card p-6 text-center">
        <h2 className="text-lg font-semibold mb-2">Chat with Characters</h2>
        <p className="text-sm text-muted-foreground">
          Truyện chưa có nhân vật nào. Vui lòng quay lại sau khi có thêm chương.
        </p>
      </section>
    );
  }

  const selectedChar = characters.find((c) => c.id === selectedCharId);

  async function handleSend() {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    setInput("");
    if (!session) {
      await createSession();
    }
    await sendMessage(trimmed);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <section className="rounded-lg border bg-card flex flex-col h-[520px]">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="font-semibold text-sm">Chat with Characters</h2>
          <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-300 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-700">
            VIP Max
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={selectedCharId}
            onValueChange={(v) => setSelectedCharId(v)}
            disabled={isStreaming}
          >
            <SelectTrigger className="h-8 text-xs w-40">
              <SelectValue placeholder="Chọn nhân vật" />
            </SelectTrigger>
            <SelectContent>
              {characters.map((c) => (
                <SelectItem key={c.id} value={c.id} className="text-xs">
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {session && (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 text-xs"
              onClick={resetSession}
              disabled={isStreaming}
            >
              Chat mới
            </Button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && !session && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-2">
            <p className="text-sm text-muted-foreground">
              Bắt đầu cuộc trò chuyện với{" "}
              <span className="font-medium">{selectedChar?.name ?? "nhân vật"}</span>.
            </p>
            {selectedChar?.description && (
              <p className="text-xs text-muted-foreground max-w-sm">
                {selectedChar.description}
              </p>
            )}
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}
            >
              {msg.role === "assistant" && (
                <p className="text-xs font-semibold mb-1 opacity-70">
                  {selectedChar?.name ?? "Nhân vật"}
                </p>
              )}
              {msg.content}
              {msg.role === "assistant" && isStreaming && i === messages.length - 1 && (
                <span className="ml-0.5 inline-block w-1.5 h-3.5 bg-current animate-pulse" />
              )}
            </div>
          </div>
        ))}

        {error && (
          <p className="text-xs text-destructive text-center">{error}</p>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t p-3 flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={`Nhắn tin với ${selectedChar?.name ?? "nhân vật"}... (Enter để gửi)`}
          className="resize-none text-sm min-h-0 h-9 py-2"
          disabled={isStreaming}
          rows={1}
        />
        <Button
          size="sm"
          onClick={handleSend}
          disabled={!input.trim() || isStreaming}
          className="h-9 shrink-0"
        >
          Gửi
        </Button>
      </div>
    </section>
  );
}
