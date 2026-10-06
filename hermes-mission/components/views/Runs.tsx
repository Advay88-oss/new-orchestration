"use client";

import React, { useState, useEffect } from "react";
import { CompanyFilter } from "@/components/CompanyChip";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";
import { EmptyState, SkeletonRows } from "@/components/States";
import { sinceLabel, useViewer } from "@/lib/useViewer";

function postHeadline(r: any): string {
  const brief = String(r.poster_brief || "");
  const match = brief.match(/Headline:\s*([^\n]+)/);
  if (match) return match[1].replace(/\s*\(gradient word:.*\)\s*$/, "").trim();
  const hook = r.posts?.x?.hook || r.reasoning?.hook;
  if (hook) return String(hook);
  if (r.title && r.title !== r.run_id) return String(r.title);
  return "Untitled post";
}

function dayLabel(r: any): string {
  if (!r.started) return "Undated";
  return new Date(r.started * 1000).toLocaleDateString(undefined, {
    weekday: "short", day: "numeric", month: "short", year: "numeric",
  });
}

function groupByDay(rows: any[]): { day: string; items: any[] }[] {
  const groups: { day: string; items: any[] }[] = [];
  for (const r of rows) {
    const day = dayLabel(r);
    const last = groups[groups.length - 1];
    if (last && last.day === day) last.items.push(r);
    else groups.push({ day, items: [r] });
  }
  return groups;
}

export function Runs({ vm }: { vm: MissionVM }) {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [company, setCompany] = useState<string>("all");
  const [sessionScope, setSessionScope] = useState<"SESSION" | "GLOBAL">("GLOBAL");
  const [showEmpty, setShowEmpty] = useState(false);
  const [sessionRunIds, setSessionRunIds] = useState<string[]>([]);

  const viewer = useViewer();

  const syncSessionRuns = () => {
    try {
      const stored = sessionStorage.getItem("vanna_session_runs");
      if (stored) {
        setSessionRunIds(JSON.parse(stored));
      } else {
        setSessionRunIds([]);
      }
    } catch {}
  };

  const fetchRuns = async () => {
    try {
      const res = await fetch("/api/runs", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.runs)) {
          setRuns(data.runs);
        }
      }
    } catch (e) {
      console.warn("Error fetching runs:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    syncSessionRuns();
    const handleUpdate = () => syncSessionRuns();
    window.addEventListener("vanna_session_updated", handleUpdate);
    return () => window.removeEventListener("vanna_session_updated", handleUpdate);
  }, []);

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(fetchRuns, 5000);
    return () => clearInterval(interval);
  }, []);


  // A run that recorded no model call and no agent reasoning did not run.
  // Both conditions, not either: a deterministic-only run would have agents
  // that reasoned, and a run that died inside its first model call has calls.
  // A run that produced a visual or a video started, whatever its journal
  // says — studio runs made outside a cycle have assets and no call log.
  const neverStarted = (r: any) =>
    (r.agents_that_reasoned ?? 0) === 0 && (r.spend?.calls ?? 0) === 0
    && !r.visual && !r.video;

  const targetPool = sessionScope === "SESSION"
    ? runs.filter((r) => sessionRunIds.includes(r.run_id))
    : runs;

  const filteredRuns = targetPool.filter((r) => {
    const headline = postHeadline(r);
    const copy = [r.posts?.x?.copy, r.posts?.linkedin?.copy, r.posts?.reddit?.copy].filter(Boolean).join(" ");
    const q = searchQuery.toLowerCase();
    const matchesSearch = !q
      || headline.toLowerCase().includes(q)
      || copy.toLowerCase().includes(q)
      || String(r.run_id || "").toLowerCase().includes(q)
      || String(r.reasoning?.audience || "").toLowerCase().includes(q);

    const matchesStatus =
      statusFilter === "ALL" ||
      (statusFilter === "POSTED" && r.dispatched === true) ||
      (statusFilter === "READY" && r.publishable === true) ||
      (statusFilter === "HELD" && (Boolean(r.blocked_reason) || r.status === "review_blocked"));

    const matchesCompany = company === "all" || (r.company || "vanna") === company;

    return matchesSearch && matchesStatus && matchesCompany && (showEmpty || !neverStarted(r));
  });

  const emptyCount = targetPool.filter(neverStarted).length;
  const readyCount = targetPool.filter((r) => r.publishable === true).length;
  const heldCount = targetPool.filter((r) => r.blocked_reason || r.status === "review_blocked").length;

  return (
    <section className="vanna-section">
      <div className="vanna-banner">
        <div style={{ display: "flex", alignItems: "center", gap: "32px", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: "11px", color: "var(--vn-ink-faint)" }}>Posts</div>
            <div style={{ fontFamily: MONO, fontSize: "27px", fontWeight: 600, color: "var(--vn-ink)", letterSpacing: "-0.02em" }}>{targetPool.filter((r) => r.has_post === true).length}</div>
          </div>
          <div>
            <div style={{ fontSize: "11px", color: "var(--vn-ink-faint)" }}>Ready for review</div>
            <div style={{ fontFamily: MONO, fontSize: "27px", fontWeight: 600, color: "var(--vn-ok)", letterSpacing: "-0.02em" }}>{readyCount}</div>
          </div>
          <div>
            <div style={{ fontSize: "11px", color: "var(--vn-ink-faint)" }}>Held</div>
            <div style={{ fontFamily: MONO, fontSize: "27px", fontWeight: 600, color: "var(--vn-warn)", letterSpacing: "-0.02em" }}>{heldCount}</div>
          </div>
        </div>
      </div>

      {/* Search Bar & Action Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: "12px", alignItems: "center", flex: "1 1 420px" }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by the headline, the post line, or the run id"
            style={{
              flex: 1,
              background: "var(--vn-surface)",
              border: "1px solid var(--vn-line-strong)",
              borderRadius: "8px",
              padding: "10px 18px",
              color: "var(--vn-ink)",
              fontSize: "13px",
              outline: "none"
            }}
          />
          {/* A third "Launch Run" sat here, beside the search box, with one
              in the page header and one in the command console above. Three
              buttons that fire the same POST is three chances to fire it
              twice. The header's is the one that stays. */}
        </div>

        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          {/* Scope Toggle: Fresh Session vs Global History */}
          <div style={{ display: "flex", gap: "4px", background: "var(--vn-hover)", padding: "4px", borderRadius: "8px", border: "1px solid var(--vn-line)" }}>
            <button
              onClick={() => setSessionScope("SESSION")}
              style={{
                background: sessionScope === "SESSION" ? "var(--vn-hover)" : "transparent",
                border: `1px solid ${sessionScope === "SESSION" ? "var(--vn-line-strong)" : "transparent"}`,
                color: sessionScope === "SESSION" ? "var(--vn-ink)" : "var(--vn-ink-muted)",
                padding: "8px 14px",
                borderRadius: "8px",
                fontSize: "12px",
                fontWeight: 500,
                cursor: "pointer"
              }}
            >
              Fresh Session ({sessionRunIds.length})
            </button>
            <button
              onClick={() => setSessionScope("GLOBAL")}
              style={{
                background: sessionScope === "GLOBAL" ? "var(--vn-hover)" : "transparent",
                border: `1px solid ${sessionScope === "GLOBAL" ? "var(--vn-line-strong)" : "transparent"}`,
                color: sessionScope === "GLOBAL" ? "var(--vn-ink)" : "var(--vn-ink-muted)",
                padding: "8px 14px",
                borderRadius: "8px",
                fontSize: "12px",
                fontWeight: 500,
                cursor: "pointer"
              }}
            >
              All posts
            </button>
            {sessionRunIds.length > 0 && (
              <button
                onClick={() => {
                  sessionStorage.removeItem("vanna_session_runs");
                  setSessionRunIds([]);
                  window.dispatchEvent(new Event("vanna_session_updated"));
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--vn-ink-muted)",
                  padding: "6px 8px",
                  borderRadius: "6px",
                  fontFamily: MONO,
                  fontSize: "10px",
                  cursor: "pointer"
                }}
                title="Wipe this tab's session back to clean 0-state"
              >
                Reset
              </button>
            )}
          </div>

          <CompanyFilter companies={targetPool.map((r) => r.company || "vanna")} value={company} onChange={setCompany} />

          {emptyCount > 0 && (
            <button
              onClick={() => setShowEmpty((v) => !v)}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--vn-ink-muted)",
                padding: "8px 4px",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              {showEmpty ? "Hide" : "Show"} {emptyCount} with no post
            </button>
          )}
          {[
            { id: "ALL", label: "All" },
            { id: "READY", label: "Ready" },
            { id: "HELD", label: "Held" },
            { id: "POSTED", label: "Posted" },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setStatusFilter(t.id)}
              style={{
                background: statusFilter === t.id ? "var(--vn-hover)" : "transparent",
                border: `1px solid ${statusFilter === t.id ? "var(--vn-line-strong)" : "transparent"}`,
                color: statusFilter === t.id ? "var(--vn-ink)" : "var(--vn-ink-muted)",
                padding: "8px 14px",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "12px",
                fontWeight: 500
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {filteredRuns.length === 0 ? (
        loading ? (
          <SkeletonRows rows={4} cols={1} />
        ) : runs.length > 0 ? (
          <EmptyState icon="search" title="No posts match these filters"
            body="Clear the search, or switch to Global Archive and All." />
        ) : viewer && !viewer.owner ? (
          <EmptyState icon="runs" title="No new posts since you opened this page"
            body={<>This view starts at {sinceLabel(viewer.since)}. Each post the pipeline finishes from now on appears here, with its line, visual and review.</>} />
        ) : (
          <EmptyState icon="runs" title="No posts yet"
            body="Tell the Assistant to make a post. It lands here, with its headline, its line and its visual." />
        )
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {groupByDay(filteredRuns).map((group) => (
          <div key={group.day} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ fontFamily: MONO, fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", color: "var(--vn-ink-muted)" }}>
              {group.day}
            </div>
          {group.items.map((r, i) => {
            const headline = neverStarted(r) ? "No post from this run" : postHeadline(r);
            const status = r.dispatched === true
              ? { label: "Posted", tone: "var(--vn-ok)" }
              : r.publishable === true
                ? { label: "Ready for review", tone: "var(--vn-ok)" }
                : r.blocked_reason || r.status === "review_blocked"
                  ? { label: "Held", tone: "var(--vn-warn)" }
                  : r.status === "aborted" || r.status === "failed"
                    ? { label: "Stopped", tone: "var(--vn-bad)" }
                    : r.status === "running"
                      ? { label: "In progress", tone: "var(--vn-accent-ink)" }
                      : neverStarted(r) || r.status === "NO_ACTION" || r.status === "KILL"
                        ? { label: "No post", tone: "var(--vn-ink-muted)" }
                        : { label: "Waiting", tone: "var(--vn-ink-muted)" };
            return (
              <article
                key={r.run_id || i}
                className="post-card"
                onClick={() => { if (r.run_id) vm.openRun(r.run_id); }}
              >
                <div className="post-visual">
                  {r.visual ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={r.visual} alt="" />
                  ) : (
                    <span style={{ fontFamily: MONO, fontSize: 10, color: "var(--vn-ink-faint)" }}>—</span>
                  )}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0 }}>
                  <span style={{
                    flex: "0 0 auto",
                    fontFamily: MONO, fontSize: 10, fontWeight: 700, letterSpacing: "0.04em",
                    color: status.tone,
                  }}>{status.label}</span>
                  <h3 style={{
                    margin: 0, minWidth: 0, fontWeight: 500,
                    fontSize: 15, lineHeight: 1.35, color: "var(--vn-ink)",
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                  }}>{headline}</h3>
                </div>
              </article>
            );
          })}
          </div>
          ))}
        </div>
      )}
    </section>
  );
}
