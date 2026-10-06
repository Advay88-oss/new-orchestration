"use client";

import React, { useState, useEffect } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";
import { FeedbackBar } from "./FeedbackBar";
import { EmptyState, ViewSkeleton } from "@/components/States";
import { CompanyChip } from "@/components/CompanyChip";

const resolveMediaUrl = (url: string | null | undefined): string => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  if (url.startsWith("/api/")) return url;
  const filename = url.replace(/^\//, "");
  return `/api/media?file=${encodeURIComponent(filename)}`;
};

type ChannelId = "x" | "linkedin" | "reddit";

const CHANNELS: { id: ChannelId; label: string }[] = [
  { id: "x", label: "X" },
  { id: "linkedin", label: "LinkedIn" },
  { id: "reddit", label: "Reddit" },
];

export function RunDetail({ vm }: { vm: MissionVM }) {
  const [runData, setRunData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [channel, setChannel] = useState<ChannelId>("x");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch("/api/runs", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        if (d.runs && d.runs.length > 0) {
          const targetKey = (vm as any).runKey;
          const found = (targetKey ? d.runs.find((r: any) => r.run_id === targetKey) : null) || d.runs[0];
          setRunData(found);
        }
      })
      .catch((e) => console.warn("Error fetching run detail:", e))
      .finally(() => setLoading(false));
  }, [(vm as any).runKey]);

  if (!runData && loading) return <ViewSkeleton cards={2} media label="Loading the run" />;

  if (!runData && !loading) {
    return (
      <section className="vanna-section">
        <div className="vanna-card">
          <EmptyState compact icon="runs" title="This run is not available"
            body="It may still be starting, or it is outside the posts this view shows. Pick one from Posts." />
          <button
            onClick={vm.goRuns}
            style={{
              margin: "0 0 24px 76px",
              background: "var(--vn-cta)",
              color: "var(--vn-on-accent)",
              border: "none",
              borderRadius: "6px",
              padding: "8px 14px",
              fontSize: "13px",
              fontWeight: 500,
              cursor: "pointer"
            }}
          >
            Open Posts
          </button>
        </div>
      </section>
    );
  }

  const runId = runData?.run_id || "";
  const posts = runData?.posts ?? {};
  const xCopy: string | null = posts?.x?.copy ?? null;
  const xHook: string | null = posts?.x?.hook ?? null;
  const xParts: string[] = xCopy
    ? xCopy.split(/\n\s*\n/).map((s: string) => s.trim()).filter(Boolean)
    : [];
  const linkedinHook: string | null = posts?.linkedin?.hook ?? null;
  const linkedinCopy: string | null = posts?.linkedin?.copy ?? null;
  const redditHook: string | null = posts?.reddit?.hook ?? null;
  const redditCopy: string | null = posts?.reddit?.copy ?? null;

  const headline = (xHook && String(xHook).trim())
    || (runData?.title && runData.title !== runId ? String(runData.title) : "")
    || "Untitled post";

  const videoUrl = runData?.agent_outputs?.agent_09_video?.public_url || runData?.video || null;
  const visualUrl = runData?.agent_outputs?.agent_08_visual?.public_url || runData?.visual || null;

  const dispatched: boolean = runData?.dispatched === true;
  const status = dispatched
    ? { label: "Published", color: "var(--vn-ok)" }
    : runData?.publishable === true
      ? { label: "Ready for review", color: "var(--vn-warn)" }
      : runData?.blocked_reason || runData?.status === "review_blocked"
        ? { label: "Held for review", color: "var(--vn-warn)" }
        : { label: "Draft", color: "var(--vn-ink-muted)" };

  const active = channel === "x"
    ? { hook: xHook, parts: xParts, body: xCopy }
    : channel === "linkedin"
      ? { hook: linkedinHook, parts: [] as string[], body: linkedinCopy }
      : { hook: redditHook, parts: [] as string[], body: redditCopy };

  const copyText = [active.hook, active.parts.length ? active.parts.join("\n\n") : active.body]
    .filter(Boolean)
    .join("\n\n");

  const receipts: string[] = Array.isArray(runData?.agent_outputs?.agent_11_dispatch?.receipts)
    ? runData.agent_outputs.agent_11_dispatch.receipts
    : (Array.isArray(runData?.receipts) ? runData.receipts : []);

  const copyPost = async () => {
    if (!copyText) return;
    try {
      await navigator.clipboard.writeText(copyText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  return (
    <section className="vanna-section">
      <div className="vanna-banner">
        <div>
          <button
            onClick={vm.goRuns}
            style={{
              background: "var(--vn-hover)",
              border: "1px solid var(--vn-line-strong)",
              color: "var(--vn-accent-ink)",
              padding: "6px 14px",
              borderRadius: "8px",
              fontSize: "11px",
              fontFamily: MONO,
              fontWeight: 700,
              cursor: "pointer",
              marginBottom: "12px",
            }}
          >
            ← Posts
          </button>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            <span style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 700, color: status.color, letterSpacing: "0.06em" }}>
              {status.label}
            </span>
            <span style={{ fontFamily: MONO, fontSize: "11px", color: "var(--vn-ink-muted)" }}>{runId}</span>
            <CompanyChip company={runData?.company || "vanna"} size="md" />
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 700, color: "var(--vn-ink)", marginTop: "8px", maxWidth: "40rem", lineHeight: 1.35 }}>
            {headline}
          </h2>
        </div>
      </div>

      {runData?.run_id && (vm as any).canReview && (
        <FeedbackBar runId={runData.run_id}
                     draft={xCopy ? ((xHook ? xHook + "\n\n" : "") + xCopy) : undefined} />
      )}

      <div className="run-detail-split" style={{ display: "grid", gridTemplateColumns: "minmax(260px, 420px) minmax(0, 1fr)", gap: "28px", alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "16px", minWidth: 0 }}>
          <div style={{ borderRadius: "12px", overflow: "hidden", border: "1px solid var(--vn-line-strong)", background: "var(--vn-surface)" }}>
            <div style={{ fontFamily: MONO, fontSize: "10px", letterSpacing: "0.08em", color: "var(--vn-ink-muted)", padding: "8px 12px", borderBottom: "1px solid var(--vn-line)" }}>
              POSTER
            </div>
            {visualUrl ? (
              <img src={resolveMediaUrl(visualUrl)} alt={headline} style={{ width: "100%", height: "auto", display: "block", background: "#000" }} />
            ) : (
              <div style={{ padding: "48px 20px", textAlign: "center", color: "var(--vn-ink-muted)", fontFamily: MONO, fontSize: "12px" }}>
                No poster for this run
              </div>
            )}
          </div>
          {videoUrl ? (
            <div style={{ borderRadius: "12px", overflow: "hidden", border: "1px solid var(--vn-line-strong)", background: "var(--vn-surface)" }}>
              <div style={{ fontFamily: MONO, fontSize: "10px", letterSpacing: "0.08em", color: "var(--vn-ink-muted)", padding: "8px 12px", borderBottom: "1px solid var(--vn-line)" }}>
                VIDEO
              </div>
              <video src={resolveMediaUrl(videoUrl)} controls playsInline preload="metadata"
                     style={{ width: "100%", display: "block", background: "#000" }} />
            </div>
          ) : null}
        </div>

        <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: "12px", padding: "18px 20px", minWidth: 0 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
            <div style={{ display: "flex", gap: "6px" }}>
              {CHANNELS.map((c) => (
                <button
                  key={c.id}
                  onClick={() => { setChannel(c.id); setCopied(false); }}
                  style={{
                    background: channel === c.id ? "var(--vn-accent-soft)" : "transparent",
                    border: `1px solid ${channel === c.id ? "var(--vn-accent)" : "var(--vn-line)"}`,
                    color: channel === c.id ? "var(--vn-ink)" : "var(--vn-ink-muted)",
                    borderRadius: "999px",
                    padding: "6px 12px",
                    fontFamily: MONO,
                    fontSize: "11px",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  {c.label}
                </button>
              ))}
            </div>
            <button
              onClick={copyPost}
              disabled={!copyText}
              style={{
                background: "transparent",
                border: "1px solid var(--vn-line-strong)",
                color: "var(--vn-ink-body)",
                borderRadius: "8px",
                padding: "6px 12px",
                fontFamily: MONO,
                fontSize: "11px",
                cursor: copyText ? "pointer" : "default",
              }}
            >
              {copied ? "Copied" : "Copy"}
            </button>
          </div>

          {!copyText ? (
            <p style={{ margin: "18px 0 0", color: "var(--vn-ink-muted)", fontSize: "14px" }}>
              No {CHANNELS.find((c) => c.id === channel)?.label} copy in this run.
            </p>
          ) : (
            <div style={{ marginTop: "18px", display: "flex", flexDirection: "column", gap: "14px" }}>
              {active.hook && active.body && !String(active.body).startsWith(String(active.hook).slice(0, 40)) ? (
                <p style={{ margin: 0, fontSize: "17px", lineHeight: 1.45, fontWeight: 650, color: "var(--vn-ink)" }}>
                  {active.hook}
                </p>
              ) : null}
              {(active.parts.length ? active.parts : [active.body || active.hook || ""]).map((para, i) => (
                <p key={i} style={{ margin: 0, fontSize: "15px", lineHeight: 1.65, color: "var(--vn-ink)", whiteSpace: "pre-wrap" }}>
                  {para}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>

      <style>{`@media (max-width: 900px) { .run-detail-split { grid-template-columns: 1fr !important; } }`}</style>

      {receipts.length > 0 && (
        <div style={{ fontFamily: MONO, fontSize: "12px", color: "var(--vn-ink-muted)" }}>
          {receipts.map((url, idx) => (
            <a key={idx} href={url} target="_blank" rel="noreferrer" style={{ color: "var(--vn-accent-ink)" }}>{url}</a>
          ))}
        </div>
      )}
    </section>
  );
}
