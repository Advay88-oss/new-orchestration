"use client";

import React, { useState, useEffect } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

// Helper to resolve media file streaming cleanly
const resolveMediaUrl = (url: string | null | undefined): string => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  const filename = url.replace(/^\//, "");
  return `/api/media?file=${encodeURIComponent(filename)}`;
};

export function IdeasView({ vm }: { vm: MissionVM }) {
  const [ideasData, setIdeasData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>("ALL");
  const [onlyRunnable, setOnlyRunnable] = useState<boolean>(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [renderingIdeaId, setRenderingIdeaId] = useState<string | null>(null);
  const [renderedVisuals, setRenderedVisuals] = useState<Record<string, string>>({});

  const fetchIdeas = async () => {
    try {
      const res = await fetch("/api/panels/ideas", { cache: "no-store" });
      const data = await res.json();
      if (data.success) {
        setIdeasData(data);
      }
    } catch (e: any) {
      console.warn("Ideas fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIdeas();
    const itv = setInterval(fetchIdeas, 6000);
    return () => clearInterval(itv);
  }, []);

  const handleRenderVisual = async (ideaId: string) => {
    setRenderingIdeaId(ideaId);
    setActionFeedback(`Synthesizing on-demand 3D isometric visual for idea ${ideaId}...`);
    try {
      const res = await fetch("/api/panels/ideas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "render_visual", idea_id: ideaId })
      });
      const data = await res.json();
      if (data.success && data.visual_url) {
        setRenderedVisuals((prev) => ({ ...prev, [ideaId]: data.visual_url }));
        setActionFeedback(`Visual rendered successfully for idea ${ideaId}!`);
      } else {
        setActionFeedback(`Note: ${data.error || "Rendering in progress"}`);
      }
    } catch (err: any) {
      setActionFeedback(`Failed: rendering visual: ${err.message}`);
    } finally {
      setRenderingIdeaId(null);
      setTimeout(() => setActionFeedback(null), 6000);
    }
  };

  const handleDraftPost = async (idea: any) => {
    setActionFeedback(`Launching 13-agent run for: "${idea.hook.slice(0, 50)}..."`);
    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directive: idea.hook })
      });
      const data = await res.json();
      if (data.success && data.result?.run_id) {
        try {
          const stored = sessionStorage.getItem("vanna_session_runs");
          const list = stored ? JSON.parse(stored) : [];
          if (!list.includes(data.result.run_id)) {
            list.unshift(data.result.run_id);
            sessionStorage.setItem("vanna_session_runs", JSON.stringify(list));
            window.dispatchEvent(new Event("vanna_session_updated"));
          }
        } catch {}
        setActionFeedback(`Run ${data.result.run_id} launched! Navigating to Run Detail...`);
        vm.openRun(data.result.run_id);
      }
    } catch (err: any) {
      setActionFeedback(`Failed: drafting post: ${err.message}`);
    }
  };

  const handleDismiss = async (ideaId: string) => {
    const reason = prompt("Enter dismissal reason (e.g. 'Not relevant for current testnet milestone'):", "Dismissed by founder");
    if (reason === null) return;
    try {
      const res = await fetch("/api/panels/ideas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "dismiss", idea_id: ideaId, reason })
      });
      const data = await res.json();
      if (data.success) {
        setActionFeedback(`Idea ${ideaId} dismissed`);
        // Remove locally from state
        setIdeasData((prev: any) => ({
          ...prev,
          ideas: prev.ideas.filter((i: any) => i.id !== ideaId)
        }));
      }
    } catch (err: any) {
      setActionFeedback(`Failed: dismissing idea: ${err.message}`);
    }
  };

  const allIdeas: any[] = ideasData?.ideas || [];
  const filteredIdeas = allIdeas.filter((i) => {
    if (onlyRunnable && !i.runnable_today) return false;
    if (filterType !== "ALL" && i.type !== filterType) return false;
    return true;
  });

  const TYPES = ["ALL", "PROPOSED", "GTM_CYCLE"];

  return (
    <section className="vanna-section">
      {/* Banner */}
      <div className="vanna-banner">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "999px", background: "var(--vn-accent-ink)", boxShadow: "0 0 0 3px var(--vn-hover)" }} />
            <span style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 700, color: "var(--vn-accent-ink)", letterSpacing: "0.1em" }}>
              STRATEGIC GTM IDEAS OBSERVATORY
            </span>
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800, color: "var(--vn-ink)", marginTop: "6px" }}>
            Actionable Ideas Synthesized from Scraped Market Intelligence
          </h2>
          <p style={{ fontSize: "14px", color: "var(--vn-ink-muted)", marginTop: "4px" }}>
            Angles worth drafting, and the runs already made.
          </p>
        </div>

        {/* Global Counter */}
        <div style={{ display: "flex", gap: "16px" }}>
          <div>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "var(--vn-ink-muted)" }}>RUNNABLE TODAY</div>
            <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 700, color: "var(--vn-ok)" }}>
              {ideasData?.runnable_today_count || 0} Ideas
            </div>
          </div>
          <div>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "var(--vn-ink-muted)" }}>BLOCKED (MAINNET)</div>
            <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 700, color: "var(--vn-bad)" }}>
              {ideasData?.blocked_count || 0} Ideas
            </div>
          </div>
        </div>
      </div>

      {actionFeedback && (
        <div style={{ fontFamily: MONO, fontSize: "12px", color: "var(--vn-ok)", background: "var(--vn-ok-soft)", padding: "12px 18px", borderRadius: "8px", border: "1px solid var(--vn-ok-line)" }}>
          {actionFeedback}
        </div>
      )}

      {/* Filter Row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", borderBottom: "1px solid var(--vn-line)", paddingBottom: "14px" }}>
        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", alignItems: "center" }}>
          <button
            onClick={fetchIdeas}
            style={{
              background: "var(--vn-hover)",
              border: "1px solid var(--vn-line-strong)",
              color: "var(--vn-ink-body)",
              padding: "6px 14px",
              borderRadius: "8px",
              fontFamily: MONO,
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
              whiteSpace: "nowrap"
            }}
          >
            Refresh
          </button>
          {TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              style={{
                background: filterType === t ? "var(--vn-accent-soft)" : "var(--vn-hover)",
                border: `1px solid ${filterType === t ? "var(--vn-accent)" : "var(--vn-line-strong)"}`,
                color: filterType === t ? "var(--vn-ink)" : "var(--vn-ink-muted)",
                padding: "6px 14px",
                borderRadius: "8px",
                cursor: "pointer",
                fontFamily: MONO,
                fontSize: "11px",
                fontWeight: 700
              }}
            >
              {t}
            </button>
          ))}
        </div>

        <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontFamily: MONO, fontSize: "12px", color: "var(--vn-ink-body)" }}>
          <input
            type="checkbox"
            checked={onlyRunnable}
            onChange={(e) => setOnlyRunnable(e.target.checked)}
            style={{ cursor: "pointer", accentColor: "var(--vn-ok)" }}
          />
          Show Only Runnable Today (No Blocked Claims)
        </label>
      </div>

      {/* Ideas Cards Grid */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {filteredIdeas.map((idea) => {
          // PROPOSED is an angle nobody has drafted yet; GTM_CYCLE already ran.
          const typeColor =
            idea.type === "PROPOSED"
              ? "var(--vn-warn)"
              : idea.type === "GTM_CYCLE"
                ? "var(--vn-accent-ink)"
                : "var(--vn-accent-ink)";

          const renderedImg = renderedVisuals[idea.id];

          return (
            <div
              key={idea.id}
              style={{
                background: "var(--vn-surface)",
                border: `1px solid ${idea.runnable_today ? "var(--vn-line)" : "var(--vn-bad-line)"}`,
                borderRadius: "12px",
                padding: "var(--vn-card-pad)",
                display: "flex",
                flexDirection: "column",
                gap: "16px",
                boxShadow: "0 2px 8px rgba(17,17,17,0.04)"
              }}
            >
              {/* Header & Hook */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <span
                      style={{
                        fontFamily: MONO,
                        fontSize: "10px",
                        fontWeight: 800,
                        color: typeColor,
                        background: `${typeColor}18`,
                        border: `1px solid ${typeColor}40`,
                        padding: "2px 8px",
                        borderRadius: "6px"
                      }}
                    >
                      {idea.type}
                    </span>
                    <span style={{ fontFamily: MONO, fontSize: "11px", color: "var(--vn-ink-muted)" }}>{idea.id}</span>
                    <span style={{ fontFamily: MONO, fontSize: "10px", color: idea.runnable_today ? "var(--vn-ok)" : "var(--vn-bad)", background: idea.runnable_today ? "var(--vn-ok-soft)" : "var(--vn-bad-soft)", padding: "2px 8px", borderRadius: "4px" }}>
                      {idea.runnable_today ? "RUNNABLE TODAY" : "BLOCKED"}
                    </span>
                  </div>

                  {/* 3 Core Action Buttons */}
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
                    <button
                      onClick={() => handleRenderVisual(idea.id)}
                      disabled={renderingIdeaId === idea.id}
                      style={{
                        background: "var(--vn-accent-soft)",
                        border: "1px solid var(--vn-accent-line)",
                        color: "var(--vn-accent-ink)",
                        padding: "6px 14px",
                        borderRadius: "8px",
                        fontFamily: MONO,
                        fontSize: "11px",
                        fontWeight: 700,
                        cursor: renderingIdeaId === idea.id ? "not-allowed" : "pointer"
                      }}
                    >
                      {renderingIdeaId === idea.id ? "Rendering..." : "Render visual"}
                    </button>

                    <button
                      onClick={() => handleDraftPost(idea)}
                      style={{
                        background: "var(--vn-cta)",
                        border: "none",
                        color: "var(--vn-on-accent)",
                        padding: "6px 14px",
                        borderRadius: "8px",
                        fontFamily: MONO,
                        fontSize: "11px",
                        fontWeight: 800,
                        cursor: "pointer"
                      }}
                    >
                      Draft Post
                    </button>

                    <button
                      onClick={() => handleDismiss(idea.id)}
                      style={{
                        background: "var(--vn-hover)",
                        border: "1px solid var(--vn-line-strong)",
                        color: "var(--vn-ink-muted)",
                        padding: "6px 12px",
                        borderRadius: "8px",
                        fontFamily: MONO,
                        fontSize: "11px",
                        cursor: "pointer"
                      }}
                    >
                      Dismiss
                    </button>
                  </div>
                </div>

                <h3 style={{ fontSize: "17px", fontWeight: 700, color: "var(--vn-ink)", marginTop: "10px" }}>
                  {idea.hook}
                </h3>
                <p style={{ fontSize: "13px", color: "var(--vn-ink-body)", lineHeight: 1.5, marginTop: "4px" }}>
                  {idea.rationale}
                </p>
                {idea.blocked_by && (
                  <div style={{ fontSize: "12px", color: "var(--vn-bad)", background: "var(--vn-bad-soft)", padding: "8px 12px", borderRadius: "6px", marginTop: "8px" }}>
                    <strong>Blocker Notice:</strong> {idea.blocked_by}
                  </div>
                )}
              </div>

              {/* Creative direction — what to MAKE, not only what to say.
                  Present on PROPOSED entries; a finished run has the real
                  asset above instead. */}
              {(idea.visual_direction || idea.video_direction || idea.gtm_play) && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "12px" }}>
                  {[
                    ["VISUAL", idea.visual_direction, "var(--vn-accent-ink)"],
                    ["VIDEO", idea.video_direction, "var(--vn-accent-ink)"],
                    ["GTM PLAY", idea.gtm_play, "var(--vn-ok)"],
                  ].map(([label, text, tone]) =>
                    text ? (
                      <div key={label as string} style={{ background: "var(--vn-sunken)", border: `1px solid ${tone}26`, borderRadius: "8px", padding: "12px 14px" }}>
                        <div style={{ fontFamily: MONO, fontSize: "10px", color: tone as string, fontWeight: 700, letterSpacing: "0.06em" }}>
                          {label}
                        </div>
                        <div style={{ fontSize: "12px", color: "var(--vn-ink-body)", lineHeight: 1.55, marginTop: "5px" }}>
                          {text}
                        </div>
                      </div>
                    ) : null,
                  )}
                </div>
              )}

              {/* Rendered Visual Preview */}
              {(renderedImg || idea.visual_url) && (
                <div style={{ borderRadius: "8px", overflow: "hidden", border: "1px solid var(--vn-line-strong)", maxWidth: "560px", background: "var(--vn-sunken)" }}>
                  <img
                    src={resolveMediaUrl(renderedImg || idea.visual_url)}
                    alt={idea.hook}
                    style={{ width: "100%", height: "auto", display: "block" }}
                    onError={(e: any) => {
                      e.target.style.display = "none";
                      const parent = e.target.parentElement;
                      if (parent && !parent.querySelector(".fallback-notice")) {
                        const div = document.createElement("div");
                        div.className = "fallback-notice";
                        div.style.padding = "24px";
                        div.style.textAlign = "center";
                        div.style.color = "var(--vn-ink-muted)";
                        div.style.fontSize = "12px";
                        div.style.fontFamily = "JetBrains Mono, monospace";
                        div.innerHTML = "<div>3D Isometric schematic ready. Click <strong>Render Visual</strong> above to generate with Gemini 3.1 Flash Image.</div>";
                        parent.appendChild(div);
                      }
                    }}
                  />
                </div>
              )}

              {/* Provenance & Claims Footer */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px", background: "var(--vn-hover)", padding: "12px 14px", borderRadius: "8px", fontSize: "11px", fontFamily: MONO, color: "var(--vn-ink-muted)" }}>
                {idea.pattern_ref && (
                  <div>
                    <span style={{ color: "var(--vn-ink-body)" }}>PATTERN:</span> {idea.pattern_ref}
                  </div>
                )}
                {idea.audience_segment && (
                  <div>
                    <span style={{ color: "var(--vn-ink-body)" }}>AUDIENCE:</span> {idea.audience_segment}
                  </div>
                )}
                {idea.signal_headline && (
                  <div style={{ gridColumn: "1 / -1" }}>
                    <span style={{ color: "var(--vn-ink-body)" }}>FROM SIGNAL:</span> {idea.signal_headline}
                  </div>
                )}
                <div>
                  <span style={{ color: "var(--vn-ink-body)" }}>EFFORT:</span> {idea.effort} · CLAIMS:{" "}
                  <span style={{ color: idea.claims_gate === "PASS" ? "var(--vn-ok)" : idea.claims_gate === "UNCHECKED" ? "var(--vn-warn)" : "var(--vn-bad)" }}>
                    {idea.claims_gate}
                  </span>
                </div>
                {idea.pattern_source && (
                  <div>
                    <a href={idea.trend_link || "#"} target="_blank" rel="noreferrer" style={{ color: "var(--vn-accent-ink)", textDecoration: "none" }}>
                      Source Proof ↗
                    </a>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
