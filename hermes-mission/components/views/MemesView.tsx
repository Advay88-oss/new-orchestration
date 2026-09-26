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

export function MemesView({ vm }: { vm: MissionVM }) {
  const [memesData, setMemesData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAllVisuals, setShowAllVisuals] = useState(true);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [renderingMemeId, setRenderingMemeId] = useState<string | null>(null);
  const [renderedVisuals, setRenderedVisuals] = useState<Record<string, string>>({});

  const fetchMemes = async () => {
    try {
      const res = await fetch("/api/panels/memes", { cache: "no-store" });
      const data = await res.json();
      if (data.success) {
        setMemesData(data);
      }
    } catch (e: any) {
      console.warn("Memes fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemes();
    try {
      const stored = sessionStorage.getItem("vanna_rendered_memes");
      if (stored) {
        setRenderedVisuals(JSON.parse(stored));
      }
    } catch {}
    const itv = setInterval(fetchMemes, 6000);
    return () => clearInterval(itv);
  }, []);

  const handleRenderVisual = async (memeId: string) => {
    setRenderingMemeId(memeId);
    setActionFeedback(`Synthesizing on-demand visual for meme ${memeId}...`);
    try {
      const res = await fetch("/api/panels/memes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "render_visual", meme_id: memeId })
      });
      const data = await res.json();
      if (data.success && data.visual_url) {
        setRenderedVisuals((prev) => {
          const updated = { ...prev, [memeId]: data.visual_url };
          try {
            sessionStorage.setItem("vanna_rendered_memes", JSON.stringify(updated));
          } catch {}
          return updated;
        });
        setActionFeedback(`Visual rendered successfully for meme ${memeId}!`);
      } else {
        setActionFeedback(`Note: ${data.error || "Rendering in progress"}`);
      }
    } catch (err: any) {
      setActionFeedback(`Failed: rendering visual: ${err.message}`);
    } finally {
      setRenderingMemeId(null);
      setTimeout(() => setActionFeedback(null), 6000);
    }
  };

  const handleDraftPost = async (meme: any) => {
    setActionFeedback(`Staging post for: "${meme.vanna_angle.slice(0, 50)}..."`);
    try {
      const promptText = `Draft a humorous cultural crypto post: ${meme.vanna_angle}. Copy: ${meme.copy.replace(/\n/g, ' ')}`;
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directive: promptText })
      });
      const data = await res.json();
      if (data.success && data.result?.run_id) {
        setActionFeedback(`Run ${data.result.run_id} launched! Navigating to Run Detail...`);
        vm.openRun(data.result.run_id);
      }
    } catch (err: any) {
      setActionFeedback(`Failed: drafting meme post: ${err.message}`);
    }
  };

  const handleDismiss = async (memeId: string) => {
    const reason = prompt("Enter dismissal reason (e.g. 'Format feels fading', 'Too edgy'):", "Dismissed by founder");
    if (reason === null) return;
    try {
      const res = await fetch("/api/panels/memes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "dismiss", meme_id: memeId, reason })
      });
      const data = await res.json();
      if (data.success) {
        setActionFeedback(`Meme ${memeId} dismissed`);
        setMemesData((prev: any) => ({
          ...prev,
          memes: prev.memes.filter((m: any) => m.id !== memeId)
        }));
      }
    } catch (err: any) {
      setActionFeedback(`Failed: dismissing meme: ${err.message}`);
    }
  };

  const memes: any[] = memesData?.memes || [];

  return (
    <section className="vanna-section">
      {/* Banner */}
      <div className="vanna-banner">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "999px", background: "var(--vn-bad)", boxShadow: "0 0 0 3px var(--vn-hover)" }} />
            <span style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 700, color: "var(--vn-bad)", letterSpacing: "0.1em" }}>
              CULTURALLY GROUNDED CRYPTO & DEFI MEMES
            </span>
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800, color: "var(--vn-ink)", marginTop: "6px" }}>
            Meme Engineering: Liquidation Pain & Gas Anxiety
          </h2>
          <p style={{ fontSize: "14px", color: "var(--vn-ink-muted)", marginTop: "4px" }}>
            Separate pipeline with strict claim gating and honest risk evaluations. Zero competitor attacks, zero fabricated numbers, verified format freshness.
          </p>
        </div>

        {/* Global Risk Distribution & View Toggle */}
        <div style={{ display: "flex", gap: "14px", alignItems: "center", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "var(--vn-ink-muted)" }}>LOW RISK</div>
            <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 700, color: "var(--vn-ok)" }}>
              {memesData?.low_risk_count || 0} Memes
            </div>
          </div>
          <div>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "var(--vn-ink-muted)" }}>MEDIUM RISK</div>
            <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 700, color: "var(--vn-warn)" }}>
              {memesData?.medium_risk_count || 0} Memes
            </div>
          </div>

          <button
            onClick={fetchMemes}
            style={{
              background: "var(--vn-hover)",
              border: "1px solid var(--vn-line-strong)",
              color: "var(--vn-ink-body)",
              padding: "8px 14px",
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
          <button
            onClick={() => setShowAllVisuals(!showAllVisuals)}
            style={{
              background: showAllVisuals ? "var(--vn-accent-soft)" : "var(--vn-hover)",
              border: `1px solid ${showAllVisuals ? "var(--vn-accent)" : "var(--vn-line-strong)"}`,
              color: showAllVisuals ? "var(--vn-ink)" : "var(--vn-ink-muted)",
              padding: "8px 16px",
              borderRadius: "8px",
              fontFamily: MONO,
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
              whiteSpace: "nowrap"
            }}
          >
            {showAllVisuals ? "Hide visuals" : "Show pre-rendered visuals"}
          </button>
        </div>
      </div>

      {actionFeedback && (
        <div style={{ fontFamily: MONO, fontSize: "12px", color: "var(--vn-ok)", background: "var(--vn-ok-soft)", padding: "12px 18px", borderRadius: "10px", border: "1px solid var(--vn-ok-line)" }}>
          {actionFeedback}
        </div>
      )}

      {/* Memes Cards Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 540px), 1fr))", gap: "18px" }}>
        {memes.map((m) => {
          const riskColor = m.risk === "LOW" ? "var(--vn-ok)" : m.risk === "MEDIUM" ? "var(--vn-warn)" : "var(--vn-bad)";
          const renderedImg = renderedVisuals[m.id];

          return (
            <div
              key={m.id}
              style={{
                background: "var(--vn-surface)",
                border: "1px solid var(--vn-line)",
                borderRadius: "16px",
                padding: "22px 24px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                gap: "14px",
                boxShadow: "0 2px 8px rgba(17,17,17,0.04)"
              }}
            >
              <div>
                {/* Header Strip */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px", flexWrap: "wrap" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                    <span style={{ fontFamily: MONO, fontSize: "10px", fontWeight: 800, color: "var(--vn-accent-ink)", background: "var(--vn-accent-soft)", padding: "2px 8px", borderRadius: "4px" }}>
                      {m.format}
                    </span>
                    <span style={{ fontFamily: MONO, fontSize: "10px", color: riskColor, background: `${riskColor}18`, border: `1px solid ${riskColor}40`, padding: "2px 8px", borderRadius: "4px" }}>
                      RISK: {m.risk}
                    </span>
                    <span style={{ fontFamily: MONO, fontSize: "10px", color: m.freshness === "in circulation" ? "var(--vn-accent-ink)" : "var(--vn-ink-muted)" }}>
                      ● {m.freshness}
                    </span>
                  </div>

                  <span style={{ fontFamily: MONO, fontSize: "11px", color: "var(--vn-accent-ink)", background: "var(--vn-accent-soft)", padding: "3px 10px", borderRadius: "6px" }}>
                    Format: {m.reference}
                  </span>
                </div>

                {/* Vanna Angle */}
                <h3 style={{ fontSize: "16px", fontWeight: 700, color: "var(--vn-ink)", marginTop: "12px" }}>
                  {m.vanna_angle}
                </h3>

                {/* Copy / Dialogue */}
                <div style={{ background: "var(--vn-sunken)", border: "1px solid var(--vn-line)", borderRadius: "10px", padding: "12px 14px", marginTop: "10px", fontSize: "13px", color: "var(--vn-ink-body)", whiteSpace: "pre-line", lineHeight: 1.55 }}>
                  {m.copy}
                </div>

                {/* Risk Explanation */}
                <div style={{ fontSize: "11px", color: "var(--vn-ink-muted)", marginTop: "10px", lineHeight: 1.5 }}>
                  <strong style={{ color: riskColor }}>Risk Analysis:</strong> {m.risk_reason}
                </div>
              </div>

              {/* Inline Meme Visual Preview */}
              {(renderedVisuals[m.id] || (showAllVisuals ? m.visual_url : null)) && (
                <div style={{ borderRadius: "12px", overflow: "hidden", border: "1px solid var(--vn-line-strong)", background: "var(--vn-sunken)", marginTop: "8px" }}>
                  <img
                    src={resolveMediaUrl(renderedVisuals[m.id] || m.visual_url)}
                    alt={m.vanna_angle}
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
                        div.innerHTML = "<div>Visual ready to synthesize. Click <strong>Render Visual</strong> below to generate with Gemini 3.1 Flash Image.</div>";
                        parent.appendChild(div);
                      }
                    }}
                  />
                </div>
              )}

              {/* Action Buttons */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid var(--vn-line)", paddingTop: "12px", marginTop: "8px" }}>
                <span style={{ fontFamily: MONO, fontSize: "11px", color: "var(--vn-ok)" }}>
                  CLAIMS: {m.claims_gate}
                </span>

                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    onClick={() => handleRenderVisual(m.id)}
                    disabled={renderingMemeId === m.id}
                    style={{
                      background: "var(--vn-accent-soft)",
                      border: "1px solid var(--vn-accent-line)",
                      color: "var(--vn-accent-ink)",
                      padding: "6px 12px",
                      borderRadius: "6px",
                      fontFamily: MONO,
                      fontSize: "11px",
                      fontWeight: 700,
                      cursor: renderingMemeId === m.id ? "not-allowed" : "pointer"
                    }}
                  >
                    {renderingMemeId === m.id ? "Rendering..." : "Render visual"}
                  </button>

                  <button
                    onClick={() => handleDraftPost(m)}
                    style={{
                      background: "var(--vn-cta)",
                      border: "none",
                      color: "var(--vn-on-accent)",
                      padding: "6px 14px",
                      borderRadius: "6px",
                      fontFamily: MONO,
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer"
                    }}
                  >
                    Draft Post
                  </button>

                  <button
                    onClick={() => handleDismiss(m.id)}
                    style={{
                      background: "transparent",
                      border: "1px solid var(--vn-line-strong)",
                      color: "var(--vn-ink-muted)",
                      padding: "6px 10px",
                      borderRadius: "6px",
                      fontFamily: MONO,
                      fontSize: "11px",
                      cursor: "pointer"
                    }}
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
