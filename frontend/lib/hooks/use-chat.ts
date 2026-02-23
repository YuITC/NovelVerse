"use client";

import { useCallback, useState } from "react";

import { createClient } from "@/lib/supabase/client";
import type { ChatMessage, ChatSession } from "@/lib/types/ai";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAccessToken(): Promise<string | null> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

export function useChat(novelId: string, characterId: string) {
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createSession = useCallback(async () => {
    setError(null);
    const token = await getAccessToken();
    if (!token) {
      setError("Bạn cần đăng nhập để sử dụng tính năng này.");
      return;
    }

    const resp = await fetch(`${API_URL}/api/v1/chat/sessions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ novel_id: novelId, character_id: characterId }),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      setError(err.detail || "Không thể tạo phiên chat.");
      return;
    }

    const newSession: ChatSession = await resp.json();
    setSession(newSession);
    setMessages(newSession.messages ?? []);
    return newSession;
  }, [novelId, characterId]);

  const sendMessage = useCallback(
    async (content: string, sessionOverride?: ChatSession) => {
      const activeSession = sessionOverride ?? session;
      if (!activeSession || isStreaming) return;
      setError(null);

      const token = await getAccessToken();
      if (!token) {
        setError("Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.");
        return;
      }

      // Append user message immediately
      const userMsg: ChatMessage = {
        role: "user",
        content,
        created_at: new Date().toISOString(),
      };
      const assistantPlaceholder: ChatMessage = {
        role: "assistant",
        content: "",
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg, assistantPlaceholder]);
      setIsStreaming(true);

      try {
        const resp = await fetch(
          `${API_URL}/api/v1/chat/sessions/${activeSession.id}/message`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ content }),
          }
        );

        if (!resp.ok) {
          const errData = await resp.json().catch(() => ({}));
          setError(errData.detail || "Lỗi khi gửi tin nhắn.");
          // Remove placeholder on error
          setMessages((prev) => prev.slice(0, -1));
          return;
        }

        const reader = resp.body?.getReader();
        const decoder = new TextDecoder();
        if (!reader) return;

        let fullText = "";
        let streamDone = false;

        while (!streamDone) {
          const { done, value } = await reader.read();
          if (done) break;

          const raw = decoder.decode(value, { stream: true });
          // Parse SSE lines: "data: <token>\n\n"
          const lines = raw.split("\n");
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const token = line.slice("data: ".length);
            if (token === "[DONE]") { streamDone = true; break; }
            if (token.startsWith("[ERROR]")) {
              setError(token.slice("[ERROR] ".length));
              streamDone = true;
              break;
            }
            // Unescape newlines encoded in SSE
            const decoded = token.replace(/\\n/g, "\n");
            fullText += decoded;
            // Update assistant placeholder in real-time
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: fullText,
              };
              return updated;
            });
          }
        }
      } catch {
        setError("Lỗi kết nối. Vui lòng thử lại.");
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsStreaming(false);
      }
    },
    [session, isStreaming]
  );

  const resetSession = useCallback(() => {
    setSession(null);
    setMessages([]);
    setError(null);
  }, []);

  return {
    session,
    messages,
    isStreaming,
    error,
    createSession,
    sendMessage,
    resetSession,
  };
}
