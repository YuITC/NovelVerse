"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import * as d3 from "d3";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { apiFetch } from "@/lib/api";
import { useUser } from "@/lib/hooks/use-user";
import { createClient } from "@/lib/supabase/client";
import type {
  ArcSummaryResponse,
  RelationshipGraphResponse,
  TimelineResponse,
} from "@/lib/types/ai";
import type { VipSubscription } from "@/lib/types/vip";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Tab = "graph" | "timeline" | "qa" | "arc";

interface StoryIntelligencePanelProps {
  novelId: string;
}

async function getAccessToken(): Promise<string | null> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

const VIP_BADGE = (
  <span className="ml-1.5 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-300 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-700">
    VIP Max
  </span>
);

export function StoryIntelligencePanel({ novelId }: StoryIntelligencePanelProps) {
  const { user, loading } = useUser();
  const [isVipMax, setIsVipMax] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("graph");

  // Graph state
  const [relationships, setRelationships] = useState<RelationshipGraphResponse | null>(null);
  const [graphLoaded, setGraphLoaded] = useState(false);
  const svgRef = useRef<SVGSVGElement>(null);

  // Timeline state
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [timelineLoaded, setTimelineLoaded] = useState(false);

  // Q&A state
  const [qaQuestion, setQaQuestion] = useState("");
  const [qaAnswer, setQaAnswer] = useState("");
  const [qaStreaming, setQaStreaming] = useState(false);
  const [qaError, setQaError] = useState<string | null>(null);

  // Arc summary state
  const [arcStart, setArcStart] = useState("1");
  const [arcEnd, setArcEnd] = useState("10");
  const [arcSummary, setArcSummary] = useState<ArcSummaryResponse | null>(null);
  const [arcLoading, setArcLoading] = useState(false);
  const [arcError, setArcError] = useState<string | null>(null);

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
      .catch(() => setIsVipMax(false));
  }, [user]);

  // Load graph on first tab open
  useEffect(() => {
    if (activeTab !== "graph" || graphLoaded || !isVipMax) return;
    setGraphLoaded(true);
    apiFetch<RelationshipGraphResponse>(`/ai/novels/${novelId}/relationships`)
      .then(setRelationships)
      .catch(() => setRelationships({ status: "failed", nodes: [], edges: [] }));
  }, [activeTab, graphLoaded, isVipMax, novelId]);

  // Load timeline on first tab open
  useEffect(() => {
    if (activeTab !== "timeline" || timelineLoaded || !isVipMax) return;
    setTimelineLoaded(true);
    apiFetch<TimelineResponse>(`/ai/novels/${novelId}/timeline`)
      .then(setTimeline)
      .catch(() => setTimeline({ status: "failed", events: [] }));
  }, [activeTab, timelineLoaded, isVipMax, novelId]);

  // Poll relationships while pending
  useEffect(() => {
    if (relationships?.status !== "pending") return;
    const id = setInterval(() => {
      apiFetch<RelationshipGraphResponse>(`/ai/novels/${novelId}/relationships`)
        .then((updated) => {
          setRelationships(updated);
          if (updated.status !== "pending") clearInterval(id);
        })
        .catch(() => clearInterval(id));
    }, 5000);
    return () => clearInterval(id);
  }, [relationships?.status, novelId]);

  // Poll timeline while pending
  useEffect(() => {
    if (timeline?.status !== "pending") return;
    const id = setInterval(() => {
      apiFetch<TimelineResponse>(`/ai/novels/${novelId}/timeline`)
        .then((updated) => {
          setTimeline(updated);
          if (updated.status !== "pending") clearInterval(id);
        })
        .catch(() => clearInterval(id));
    }, 5000);
    return () => clearInterval(id);
  }, [timeline?.status, novelId]);

  // D3 force-directed graph
  useEffect(() => {
    if (!svgRef.current || relationships?.status !== "ready") return;
    const { nodes, edges } = relationships;
    if (!nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const W = svgRef.current.clientWidth || 600;
    const H = 400;
    svg.attr("width", W).attr("height", H);

    const simNodes = nodes.map((n) => ({ ...n })) as any[];
    const simEdges = edges.map((e) => ({ ...e })) as any[];

    const sim = d3
      .forceSimulation(simNodes)
      .force("link", d3.forceLink(simEdges).id((d: any) => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(W / 2, H / 2));

    const link = svg
      .append("g")
      .selectAll("line")
      .data(simEdges)
      .join("line")
      .attr("stroke", "#94a3b8")
      .attr("stroke-opacity", 0.7)
      .attr("stroke-width", (d: any) => Math.sqrt(d.weight || 1));

    const node = svg
      .append("g")
      .selectAll("circle")
      .data(simNodes)
      .join("circle")
      .attr("r", 10)
      .attr("fill", "#6366f1")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5);

    const label = svg
      .append("g")
      .selectAll("text")
      .data(simNodes)
      .join("text")
      .text((d: any) => d.name)
      .attr("font-size", 11)
      .attr("fill", "currentColor")
      .attr("dx", 13)
      .attr("dy", 4);

    sim.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);
      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
      label.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y);
    });

    return () => {
      sim.stop();
    };
  }, [relationships]);

  async function handleQA() {
    const q = qaQuestion.trim();
    if (!q || qaStreaming) return;
    setQaStreaming(true);
    setQaAnswer("");
    setQaError(null);

    const token = await getAccessToken();
    if (!token) {
      setQaError("Bạn cần đăng nhập để sử dụng tính năng này.");
      setQaStreaming(false);
      return;
    }

    try {
      const resp = await fetch(`${API_URL}/api/v1/ai/novels/${novelId}/qa`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ question: q }),
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        setQaError((errData as { detail?: string }).detail || "Lỗi khi gọi AI.");
        return;
      }

      const reader = resp.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      let acc = "";
      let streamDone = false;
      while (!streamDone) {
        const { done, value } = await reader.read();
        if (done) break;
        const raw = decoder.decode(value, { stream: true });
        for (const line of raw.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          const tok = line.slice(6);
          if (tok === "[DONE]") { streamDone = true; break; }
          if (tok.startsWith("[ERROR]")) {
            setQaError(tok.slice("[ERROR] ".length) || "Lỗi AI.");
            streamDone = true;
            break;
          }
          acc += tok.replace(/\\n/g, "\n");
          setQaAnswer(acc);
        }
      }
    } catch {
      setQaError("Lỗi kết nối. Vui lòng thử lại.");
    } finally {
      setQaStreaming(false);
    }
  }

  async function handleArcSummary() {
    const start = parseInt(arcStart, 10);
    const end = parseInt(arcEnd, 10);
    if (!start || !end || start > end) {
      setArcError("Chương bắt đầu phải nhỏ hơn hoặc bằng chương kết thúc.");
      return;
    }
    setArcLoading(true);
    setArcError(null);
    setArcSummary(null);
    try {
      const result = await apiFetch<ArcSummaryResponse>(
        `/ai/novels/${novelId}/arc-summary?start_chapter=${start}&end_chapter=${end}`
      );
      setArcSummary(result);
    } catch (err: unknown) {
      setArcError(
        (err instanceof Error ? err.message : null) || "Không thể tạo tóm tắt."
      );
    } finally {
      setArcLoading(false);
    }
  }

  function retryRelationships() {
    setGraphLoaded(false);
    setRelationships(null);
  }

  function retryTimeline() {
    setTimelineLoaded(false);
    setTimeline(null);
  }

  if (loading) return null;

  // Guest: show login CTA
  if (!user) {
    return (
      <section className="rounded-lg border bg-card p-6 text-center space-y-3">
        <h2 className="text-lg font-semibold">Story Intelligence{VIP_BADGE}</h2>
        <p className="text-sm text-muted-foreground">
          Đăng nhập để sử dụng tính năng phân tích truyện AI.
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
        <h2 className="text-lg font-semibold">Story Intelligence{VIP_BADGE}</h2>
        <p className="text-sm text-muted-foreground">
          Tính năng phân tích truyện AI chỉ dành cho thành viên VIP Max. Nâng cấp để xem sơ đồ
          nhân vật, dòng thời gian, hỏi đáp AI và tóm tắt cung chương.
        </p>
        <Button asChild size="sm">
          <Link href="/vip">Nâng cấp VIP Max</Link>
        </Button>
      </section>
    );
  }

  const TABS: { key: Tab; label: string }[] = [
    { key: "graph", label: "Sơ đồ nhân vật" },
    { key: "timeline", label: "Dòng thời gian" },
    { key: "qa", label: "Hỏi đáp AI" },
    { key: "arc", label: "Tóm tắt cung chương" },
  ];

  return (
    <section className="rounded-lg border bg-card">
      {/* Header */}
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <h2 className="font-semibold text-sm">Story Intelligence</h2>
        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-300 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-700">
          VIP Max
        </span>
      </div>

      {/* Tab bar */}
      <div className="flex border-b overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`shrink-0 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors ${
              activeTab === t.key
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="p-4 min-h-[180px]">
        {/* ---------- Relationship Graph ---------- */}
        {activeTab === "graph" && (
          <div>
            {!relationships && (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            )}
            {relationships?.status === "pending" && (
              <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Đang phân tích nhân vật... (có thể mất vài phút)</span>
              </div>
            )}
            {relationships?.status === "ready" && relationships.nodes.length === 0 && (
              <p className="py-6 text-sm text-muted-foreground text-center">
                Chưa phát hiện mối quan hệ nhân vật nào trong truyện này.
              </p>
            )}
            {relationships?.status === "ready" && relationships.nodes.length > 0 && (
              <svg
                ref={svgRef}
                className="w-full rounded border"
                style={{ height: 400, display: "block" }}
              />
            )}
            {relationships?.status === "failed" && (
              <div className="flex items-center gap-3 py-4">
                <p className="text-sm text-destructive">Lỗi phân tích nhân vật.</p>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs"
                  onClick={retryRelationships}
                >
                  Thử lại
                </Button>
              </div>
            )}
          </div>
        )}

        {/* ---------- Story Timeline ---------- */}
        {activeTab === "timeline" && (
          <div>
            {!timeline && (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            )}
            {timeline?.status === "pending" && (
              <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Đang tạo dòng thời gian... (có thể mất vài phút)</span>
              </div>
            )}
            {timeline?.status === "ready" && timeline.events.length === 0 && (
              <p className="py-6 text-sm text-muted-foreground text-center">
                Chưa có sự kiện nào được trích xuất.
              </p>
            )}
            {timeline?.status === "ready" && timeline.events.length > 0 && (
              <ol className="space-y-3 max-h-[400px] overflow-y-auto">
                {timeline.events.map((ev) => (
                  <li key={ev.chapter_number} className="flex gap-3 items-start">
                    <span className="shrink-0 inline-flex items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-semibold h-6 min-w-[2.75rem] px-1.5">
                      Ch.{ev.chapter_number}
                    </span>
                    <p className="text-sm leading-snug pt-0.5">{ev.event_summary}</p>
                  </li>
                ))}
              </ol>
            )}
            {timeline?.status === "failed" && (
              <div className="flex items-center gap-3 py-4">
                <p className="text-sm text-destructive">Lỗi tạo dòng thời gian.</p>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs"
                  onClick={retryTimeline}
                >
                  Thử lại
                </Button>
              </div>
            )}
          </div>
        )}

        {/* ---------- Q&A ---------- */}
        {activeTab === "qa" && (
          <div className="space-y-3">
            <Textarea
              value={qaQuestion}
              onChange={(e) => setQaQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleQA();
                }
              }}
              placeholder="Đặt câu hỏi về truyện... (Enter để gửi, Shift+Enter xuống dòng)"
              className="resize-none text-sm h-20"
              disabled={qaStreaming}
            />
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                onClick={handleQA}
                disabled={!qaQuestion.trim() || qaStreaming}
              >
                {qaStreaming ? (
                  <>
                    <Loader2 className="h-3 w-3 animate-spin mr-1.5" />
                    Đang trả lời...
                  </>
                ) : (
                  "Hỏi AI"
                )}
              </Button>
              {qaError && <p className="text-xs text-destructive">{qaError}</p>}
            </div>
            {qaAnswer && (
              <div className="rounded-lg bg-muted p-3 text-sm leading-relaxed whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                {qaAnswer}
                {qaStreaming && (
                  <span className="ml-0.5 inline-block w-1.5 h-3.5 bg-current animate-pulse" />
                )}
              </div>
            )}
          </div>
        )}

        {/* ---------- Arc Summary ---------- */}
        {activeTab === "arc" && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-end gap-3">
              <div className="flex items-center gap-2">
                <label className="text-xs text-muted-foreground whitespace-nowrap">
                  Từ chương
                </label>
                <input
                  type="number"
                  min={1}
                  value={arcStart}
                  onChange={(e) => setArcStart(e.target.value)}
                  className="w-20 h-8 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-muted-foreground whitespace-nowrap">
                  đến chương
                </label>
                <input
                  type="number"
                  min={1}
                  value={arcEnd}
                  onChange={(e) => setArcEnd(e.target.value)}
                  className="w-20 h-8 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
              <Button size="sm" onClick={handleArcSummary} disabled={arcLoading}>
                {arcLoading ? (
                  <>
                    <Loader2 className="h-3 w-3 animate-spin mr-1.5" />
                    Đang tóm tắt...
                  </>
                ) : (
                  "Tóm tắt"
                )}
              </Button>
            </div>
            {arcError && <p className="text-xs text-destructive">{arcError}</p>}
            {arcSummary && (
              <div className="rounded-lg bg-muted p-3 text-sm leading-relaxed whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                <p className="text-xs font-semibold text-muted-foreground mb-2">
                  Tóm tắt chương {arcSummary.start_chapter}–{arcSummary.end_chapter}
                </p>
                {arcSummary.summary}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
