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
    setActionFeedback(`🎨 Synthesizing on-demand visual for meme ${memeId}...`);
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
        setActionFeedback(`✓ Visual rendered successfully for meme ${memeId}!`);
      } else {
        setActionFeedback(`⚠️ Notice: ${data.error || "Rendering in progress"}`);
      }
    } catch (err: any) {
      setActionFeedback(`❌ Error rendering visual: ${err.message}`);
    } finally {
      setRenderingMemeId(null);
      setTimeout(() => setActionFeedback(null), 6000);
    }
  };

  const handleDraftPost = async (meme: any) => {
    setActionFeedback(`🚀 Staging post for: "${meme.vanna_angle.slice(0, 50)}..."`);
    try {
      const promptText = `Draft a humorous cultural crypto post: ${meme.vanna_angle}. Copy: ${meme.copy.replace(/\n/g, ' ')}`;
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directive: promptText })
      });
      const data = await res.json();
      if (data.success && data.result?.run_id) {
        setActionFeedback(`✓ Run ${data.result.run_id} launched! Navigating to Run Detail...`);
        vm.openRun(data.result.run_id);
      }
    } catch (err: any) {
      setActionFeedback(`❌ Error drafting meme post: ${err.message}`);
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
        setActionFeedback(`✓ Meme ${memeId} dismissed and logged to outcomes.jsonl`);
        setMemesData((prev: any) => ({
          ...prev,
          memes: prev.memes.filter((m: any) => m.id !== memeId)
        }));
      }
    } catch (err: any) {
      setActionFeedback(`❌ Error dismissing meme: ${err.message}`);
    }
  };

  const memes: any[] = memesData?.memes || [];

  return (
    <section className="vanna-section">
      {/* Banner */}
      <div className="vanna-banner">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "999px", background: "#FC5457", boxShadow: "0 0 10px #FC5457" }} />
            <span style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 700, color: "#FC5457", letterSpacing: "0.1em" }}>
              CULTURALLY GROUNDED CRYPTO & DEFI MEMES
            </span>
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#FFFFFF", marginTop: "6px" }}>
            Meme Engineering: Liquidation Pain & Gas Anxiety
          </h2>
          <p style={{ fontSize: "14px", color: "#A2A1A6", marginTop: "4px" }}>
            Separate pipeline with strict claim gating and honest risk evaluations. Zero competitor attacks, zero fabricated numbers, verified format freshness.
          </p>
        </div>

        {/* Global Risk Distribution & View Toggle */}
        <div style={{ display: "flex", gap: "14px", alignItems: "center", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>LOW RISK</div>
            <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 700, color: "#38EF7D" }}>
              {memesData?.low_risk_count || 0} Memes
            </div>
          </div>
          <div>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>MEDIUM RISK</div>
            <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 700, color: "#F5A623" }}>
              {memesData?.medium_risk_count || 0} Memes
            </div>
          </div>

          <button
            onClick={fetchMemes}
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              color: "#DFDFDF",
              padding: "8px 14px",
              borderRadius: "8px",
              fontFamily: MONO,
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
              whiteSpace: "nowrap"
            }}
          >
            🔄 Refresh
          </button>
          <button
            onClick={() => setShowAllVisuals(!showAllVisuals)}
            style={{
              background: showAllVisuals ? "rgba(112, 58, 230, 0.25)" : "rgba(255, 255, 255, 0.05)",
              border: `1px solid ${showAllVisuals ? "#703AE6" : "rgba(255, 255, 255, 0.1)"}`,
              color: showAllVisuals ? "#FFFFFF" : "#A2A1A6",
              padding: "8px 16px",
              borderRadius: "8px",
              fontFamily: MONO,
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
              whiteSpace: "nowrap"
            }}
          >
            {showAllVisuals ? "👁️ Hide Visuals (Fresh View)" : "🎨 Show Pre-Rendered Visuals"}
          </button>
        </div>
      </div>

      {actionFeedback && (
        <div style={{ fontFamily: MONO, fontSize: "12px", color: "#38EF7D", background: "rgba(56, 239, 125, 0.1)", padding: "12px 18px", borderRadius: "10px", border: "1px solid rgba(56, 239, 125, 0.3)" }}>
          {actionFeedback}
        </div>
      )}

      {/* Memes Cards Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 540px), 1fr))", gap: "18px" }}>
        {memes.map((m) => {
          const riskColor = m.risk === "LOW" ? "#38EF7D" : m.risk === "MEDIUM" ? "#F5A623" : "#FC5457";
          const renderedImg = renderedVisuals[m.id];

          return (
            <div
              key={m.id}
              style={{
                background: "#0C0716",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "16px",
                padding: "22px 24px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                gap: "14px",
                boxShadow: "0 8px 24px rgba(0,0,0,0.3)"
              }}
            >
              <div>
                {/* Header Strip */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px", flexWrap: "wrap" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                    <span style={{ fontFamily: MONO, fontSize: "10px", fontWeight: 800, color: "#A387FF", background: "rgba(112, 58, 230, 0.2)", padding: "2px 8px", borderRadius: "4px" }}>
                      {m.format}
                    </span>
                    <span style={{ fontFamily: MONO, fontSize: "10px", color: riskColor, background: `${riskColor}18`, border: `1px solid ${riskColor}40`, padding: "2px 8px", borderRadius: "4px" }}>
                      RISK: {m.risk}
                    </span>
                    <span style={{ fontFamily: MONO, fontSize: "10px", color: m.freshness === "in circulation" ? "#32EEE2" : "#8E85A8" }}>
                      ● {m.freshness}
                    </span>
                  </div>

                  <span style={{ fontFamily: MONO, fontSize: "11px", color: "#32EEE2", background: "rgba(50, 238, 226, 0.1)", padding: "3px 10px", borderRadius: "6px" }}>
                    Format: {m.reference}
                  </span>
                </div>

                {/* Vanna Angle */}
                <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#FFFFFF", marginTop: "12px" }}>
                  {m.vanna_angle}
                </h3>

                {/* Copy / Dialogue */}
                <div style={{ background: "rgba(0,0,0,0.4)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "12px 14px", marginTop: "10px", fontSize: "13px", color: "#DFDFDF", whiteSpace: "pre-line", lineHeight: 1.55 }}>
                  {m.copy}
                </div>

                {/* Risk Explanation */}
                <div style={{ fontSize: "11px", color: "#8E85A8", marginTop: "10px", lineHeight: 1.5 }}>
                  <strong style={{ color: riskColor }}>Risk Analysis:</strong> {m.risk_reason}
                </div>
              </div>

              {/* Inline Meme Visual Preview */}
              {(renderedVisuals[m.id] || (showAllVisuals ? m.visual_url : null)) && (
                <div style={{ borderRadius: "12px", overflow: "hidden", border: "1px solid rgba(255,255,255,0.12)", background: "#05010A", marginTop: "8px" }}>
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
                        div.style.color = "#8E85A8";
                        div.style.fontSize = "12px";
                        div.style.fontFamily = "JetBrains Mono, monospace";
                        div.innerHTML = "<div style='font-size: 20px; margin-bottom: 6px;'>🎨</div><div>Visual ready to synthesize. Click <strong>Render Visual</strong> below to generate with Gemini 3.1 Flash Image.</div>";
                        parent.appendChild(div);
                      }
                    }}
                  />
                </div>
              )}

              {/* Action Buttons */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "12px", marginTop: "8px" }}>
                <span style={{ fontFamily: MONO, fontSize: "11px", color: "#38EF7D" }}>
                  CLAIMS: {m.claims_gate}
                </span>

                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    onClick={() => handleRenderVisual(m.id)}
                    disabled={renderingMemeId === m.id}
                    style={{
                      background: "rgba(112, 58, 230, 0.2)",
                      border: "1px solid rgba(163, 135, 255, 0.3)",
                      color: "#A387FF",
                      padding: "6px 12px",
                      borderRadius: "6px",
                      fontFamily: MONO,
                      fontSize: "11px",
                      fontWeight: 700,
                      cursor: renderingMemeId === m.id ? "not-allowed" : "pointer"
                    }}
                  >
                    {renderingMemeId === m.id ? "⏳ Rendering..." : "🎨 Render Visual"}
                  </button>

                  <button
                    onClick={() => handleDraftPost(m)}
                    style={{
                      background: "linear-gradient(135deg, #FC5457, #703AE6)",
                      border: "none",
                      color: "#FFFFFF",
                      padding: "6px 14px",
                      borderRadius: "6px",
                      fontFamily: MONO,
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer"
                    }}
                  >
                    ⚡ Draft Post
                  </button>

                  <button
                    onClick={() => handleDismiss(m.id)}
                    style={{
                      background: "transparent",
                      border: "1px solid rgba(255,255,255,0.1)",
                      color: "#8E85A8",
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
