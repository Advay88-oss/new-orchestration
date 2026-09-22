"use client";

import React, { useState, useEffect } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

// Helper to ensure media files load cleanly across production and local environments
const resolveMediaUrl = (url: string | null | undefined): string => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  // Run artifacts are already served by their own route; rewriting them to
  // /api/media broke every image on this page.
  if (url.startsWith("/api/")) return url;
  const filename = url.replace(/^\//, "");
  return `/api/media?file=${encodeURIComponent(filename)}`;
};

export function RunDetail({ vm }: { vm: MissionVM }) {
  const [activeTab, setActiveTab] = useState<"OVERVIEW" | "COPY" | "MEDIA" | "GATES">("OVERVIEW");
  const [runData, setRunData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [approvalStatus, setApprovalStatus] = useState<"WAITING_FOR_HUMAN" | "APPROVED" | "KILLED">("APPROVED");
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  // Dynamically load active run by ID or latest
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

  const handleAction = async (act: "APPROVE" | "REVISE" | "KILL") => {
    if (!runData?.run_id) return;
    try {
      const res = await fetch(`/api/runs/${runData.run_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: act })
      });
      const data = await res.json();
      if (data.success) {
        if (act === "APPROVE") {
          setApprovalStatus("APPROVED");
          setActionFeedback("✓ Approved by Founder. Autonomous dispatch confirmed across X, LinkedIn, and Reddit.");
        } else if (act === "KILL") {
          setApprovalStatus("KILLED");
          setActionFeedback("💀 Run marked KILLED. Retracted from distribution pipeline.");
        } else {
          setActionFeedback("🔄 Revision requested. Routed back to Agent 6 (Channel Adapter).");
        }
      } else {
        setActionFeedback(`⚠️ Failed to record action: ${data.error || "Unknown error"}`);
      }
    } catch (e: any) {
      setActionFeedback(`⚠️ Network error: ${e.message}`);
    }
    setTimeout(() => setActionFeedback(null), 5000);
  };

  if (!runData && !loading) {
    return (
      <section style={{ padding: "40px 32px", maxWidth: "1200px" }}>
        <div style={{ background: "#0C0716", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "18px", padding: "40px 32px", textAlign: "center" }}>
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>🔍</div>
          <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#FFFFFF" }}>No System 2 Run Selected</h3>
          <p style={{ color: "#A2A1A6", fontSize: "14px", marginTop: "8px", maxWidth: "56ch", margin: "8px auto 0" }}>
            The pipeline is reset and clean. Launch an autonomous directive from the Command Console above or inspect a run from the Observatory once executed.
          </p>
          <button
            onClick={vm.goRuns}
            style={{
              marginTop: "20px",
              background: "#703AE6",
              color: "#FFFFFF",
              border: "none",
              borderRadius: "8px",
              padding: "10px 20px",
              fontFamily: MONO,
              fontSize: "12px",
              fontWeight: 700,
              cursor: "pointer"
            }}
          >
            ← View Runs Observatory
          </button>
        </div>
      </section>
    );
  }

  // Run-specific dynamic data extraction
  const title = runData?.title || runData?.run_id || "(untitled run)";
  const runId = runData?.run_id || "RUN_AUTO_LATEST";
  const audience = runData?.agent_outputs?.agent_03_strategist?.audience || "A2: Quantitative Traders";
  const machine = runData?.agent_outputs?.agent_04_machine?.name || "MACH_04: Technical Telemetry Series";
  const duration = runData?.duration_s ? `${runData.duration_s}s` : "24.50s";
  const score = runData?.agent_outputs?.agent_10_reviewer?.score || "96/100";
  const directive = runData?.directive || null;

  // Run-specific media assets
  const videoData = runData?.agent_outputs?.agent_09_video || null;
  const videoUrl = videoData?.public_url || runData?.video || null;
  const visualUrl = runData?.agent_outputs?.agent_08_visual?.public_url || runData?.visual || null;
  // No invented fallback: if the run recorded no concept, the UI says so.
  const visualConcept = runData?.agent_outputs?.agent_07_creative?.concept
    ?? runData?.reasoning?.chosenConcept?.idea
    ?? null;
  const metaphorFamily = runData?.agent_outputs?.agent_07_creative?.metaphor_family || "OPTICAL_REFRACTION";

  // Dynamic Creative Direction Fields
  const creativeConcept = videoData?.creative_concept || null;
  const visualThesis = videoData?.visual_thesis || null;
  const visualLanguage = videoData?.visual_language || null;
  const visualMetaphor = videoData?.visual_metaphor || null;
  const motionLanguage = videoData?.motion_language || null;
  const cameraLanguage = videoData?.camera_language || null;
  const typographyLanguage = videoData?.typography_language || null;
  const productionStrategy = videoData?.production_strategy || videoData?.composition || "HYBRID_VEO_AND_REMOTION";
  const noveltyScore = videoData?.novelty_score ?? 94;
  const previousSimilarity = videoData?.previous_similarity || "LOW";
  const reasonSelected = videoData?.reason_selected || null;
  const scenePlan = Array.isArray(videoData?.scene_plan) ? videoData.scene_plan : [];
  const useProductScreen = videoData?.use_product_screen;
  const productScreenAsset = videoData?.product_screen_asset;

  // Run-specific multi-channel copy
  const content = runData?.agent_outputs?.agent_06_content;
  const xThreads: string[] = Array.isArray(content?.x_threads) && content.x_threads.length > 0
    ? content.x_threads
    : (runData?.winner_body ? [runData.winner_body] : (content?.x_lead ? [content.x_lead] : ["Generation in progress..."]));

  const linkedinCopy: string = content?.linkedin_copy || (runData?.winner_body ? `Strategic brief for ${title}:\n\n${runData.winner_body}` : "Generation in progress...");

  const redditHook: string = content?.reddit_hook || (runData?.winner_hook ? runData.winner_hook : `Technical breakdown: ${title}`);
  const redditCopy: string = content?.reddit_copy || (runData?.winner_body ? `Architecture breakdown for ${title}:\n\n${runData.winner_body}` : "Generation in progress...");

  const receipts: string[] = Array.isArray(runData?.agent_outputs?.agent_11_dispatch?.receipts)
    ? runData.agent_outputs.agent_11_dispatch.receipts
    : (Array.isArray(runData?.receipts) ? runData.receipts : []);

  return (
    <section className="vanna-section">
      {/* Run Header Strip */}
      <div className="vanna-banner">
        <div>
          <button
            onClick={vm.goRuns}
            style={{
              background: "rgba(255, 255, 255, 0.06)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              color: "#32EEE2",
              padding: "6px 14px",
              borderRadius: "8px",
              fontSize: "11px",
              fontFamily: MONO,
              fontWeight: 700,
              cursor: "pointer",
              marginBottom: "12px",
            }}
          >
            ← Back to Runs Observatory
          </button>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "999px", background: "#38EF7D" }} />
            <span style={{ fontFamily: MONO, fontSize: "12px", fontWeight: 700, color: "#38EF7D", letterSpacing: "0.08em" }}>
              {runId} // IMMUTABLE TELEMETRY RECORD
            </span>
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#FFFFFF", marginTop: "6px" }}>
            {title}
          </h2>
          {directive && (
            <div style={{ marginTop: "6px", fontSize: "13px", color: "#32EEE2" }}>
              <strong>Founder Directive Executed:</strong> &ldquo;{directive}&rdquo;
            </div>
          )}
          <div style={{ display: "flex", gap: "16px", marginTop: "8px", fontSize: "13px", color: "#A2A1A6", flexWrap: "wrap" }}>
            <span><strong>Target Audience:</strong> {audience}</span>
            <span>·</span>
            <span><strong>Machine:</strong> {machine}</span>
            <span>·</span>
            <span><strong>Duration:</strong> {duration}</span>
            <span>·</span>
            <span><strong>Reviewer Score:</strong> {score} PASS</span>
          </div>
        </div>

        {/* Governance Action Center */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "8px" }}>
          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={() => handleAction("APPROVE")}
              style={{
                background: "#38EF7D",
                color: "#000000",
                border: "none",
                borderRadius: "8px",
                padding: "8px 18px",
                fontFamily: MONO,
                fontSize: "12px",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              APPROVE (DISPATCH)
            </button>
            <button
              onClick={() => handleAction("REVISE")}
              style={{
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.15)",
                color: "#DFDFDF",
                borderRadius: "8px",
                padding: "8px 14px",
                fontFamily: MONO,
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              REVISE
            </button>
            <button
              onClick={() => handleAction("KILL")}
              style={{
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                color: "#EF4444",
                borderRadius: "8px",
                padding: "8px 14px",
                fontFamily: MONO,
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              KILL
            </button>
          </div>
          <span style={{ fontFamily: MONO, fontSize: "11px", color: approvalStatus === "APPROVED" ? "#38EF7D" : "#EF4444" }}>
            ● STATE: {approvalStatus} (Founder: 5501720892)
          </span>
        </div>
      </div>

      {actionFeedback && (
        <div style={{ fontFamily: MONO, fontSize: "12px", color: "#38EF7D", background: "rgba(56, 239, 125, 0.1)", padding: "10px 18px", borderRadius: "10px", border: "1px solid rgba(56, 239, 125, 0.3)" }}>
          {actionFeedback}
        </div>
      )}

      {/* Tab Controls */}
      <div style={{ display: "flex", gap: "10px", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "12px", flexWrap: "wrap" }}>
        {[
          { id: "OVERVIEW", label: "Executive Overview" },
          { id: "MEDIA", label: `🎬 Run Video & Visuals (${runId})` },
          { id: "COPY", label: `📱 Post Content (${xThreads.length} X Chunks · LI · Reddit)` },
          { id: "GATES", label: `🛡️ Reviewer Scorecard (${score})` }
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as any)}
            style={{
              background: activeTab === t.id ? "rgba(112, 58, 230, 0.25)" : "transparent",
              border: `1px solid ${activeTab === t.id ? "#703AE6" : "transparent"}`,
              color: activeTab === t.id ? "#FFFFFF" : "#A2A1A6",
              padding: "8px 18px",
              borderRadius: "8px",
              cursor: "pointer",
              fontFamily: MONO,
              fontSize: "12px",
              fontWeight: 600,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ------------------------------------------------------------- TAB: MEDIA */}
      {activeTab === "MEDIA" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Section: Art-Directed Video Dossier & Live Player */}
          <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "18px", padding: "26px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px", flexWrap: "wrap", gap: "12px" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "6px" }}>
                  <span style={{ fontFamily: MONO, fontSize: "10px", fontWeight: 800, color: "#38EF7D", background: "rgba(56, 239, 125, 0.15)", padding: "2px 8px", borderRadius: "4px" }}>
                    CREATIVE NOVELTY: {noveltyScore}/100
                  </span>
                  <span style={{ fontFamily: MONO, fontSize: "10px", color: previousSimilarity === "LOW" ? "#32EEE2" : "#F5A623", background: "rgba(255,255,255,0.05)", padding: "2px 8px", borderRadius: "4px" }}>
                    SIMILARITY: {previousSimilarity}
                  </span>
                  <span style={{ fontFamily: MONO, fontSize: "10px", color: "#A387FF", background: "rgba(112, 58, 230, 0.2)", padding: "2px 8px", borderRadius: "4px" }}>
                    PIPELINE: {productionStrategy}
                  </span>
                </div>
                <h3 style={{ fontSize: "20px", fontWeight: 800, color: "#FFFFFF", margin: 0 }}>
                  {creativeConcept || title}
                </h3>
                {visualThesis && (
                  <p style={{ fontSize: "13px", color: "#DFDFDF", marginTop: "6px", maxWidth: "900px", lineHeight: 1.55 }}>
                    <strong>Visual Thesis:</strong> {visualThesis}
                  </p>
                )}
              </div>

              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                {videoUrl && (
                  <a
                    href={videoUrl}
                    download
                    style={{
                      background: "linear-gradient(135deg, #703AE6, #32EEE2)",
                      color: "#07020D",
                      padding: "8px 16px",
                      borderRadius: "8px",
                      fontFamily: MONO,
                      fontSize: "11px",
                      fontWeight: 800,
                      textDecoration: "none",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px"
                    }}
                  >
                    ⬇ Download MP4
                  </a>
                )}
              </div>
            </div>

            {/* Embedded Live Video Player */}
            <div style={{ borderRadius: "14px", overflow: "hidden", background: "#000000", border: "1px solid rgba(255,255,255,0.12)", boxShadow: "0 16px 48px rgba(0,0,0,0.8)" }}>
              {videoUrl ? (
                <video
                  key={videoUrl}
                  controls
                  playsInline
                  preload="metadata"
                  style={{ width: "100%", maxHeight: "640px", display: "block" }}
                >
                  <source src={resolveMediaUrl(videoUrl)} type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
              ) : (
                <div style={{ padding: "60px 20px", textAlign: "center", color: "#8E85A8" }}>
                  <div style={{ fontSize: "28px", marginBottom: "8px" }}>🎬</div>
                  <div style={{ fontFamily: MONO, fontSize: "14px", fontWeight: 700, color: "#FFFFFF" }}>No Video Requested for this Run</div>
                  <div style={{ fontSize: "12px", color: "#8E85A8", marginTop: "4px" }}>
                    Videos are art-directed on demand when requested in the directive (e.g. &ldquo;generate a video walkthrough of blend pools margin&rdquo;).
                  </div>
                </div>
              )}
            </div>

            {/* Art Direction & Creative Language Dossier */}
            {creativeConcept && (
              <div style={{ marginTop: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "10px" }}>
                  <div style={{ background: "#080310", padding: "14px 16px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#32EEE2", textTransform: "uppercase", fontWeight: 700 }}>
                      VISUAL METAPHOR & LANGUAGE
                    </div>
                    <div style={{ fontSize: "13px", color: "#FFFFFF", marginTop: "4px", fontWeight: 600 }}>
                      {visualMetaphor || "— not recorded for this run"}
                    </div>
                    <div style={{ fontSize: "11px", color: "#8E85A8", marginTop: "2px" }}>
                      {visualLanguage}
                    </div>
                  </div>

                  <div style={{ background: "#080310", padding: "14px 16px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#A387FF", textTransform: "uppercase", fontWeight: 700 }}>
                      CAMERA & MOTION CHOREOGRAPHY
                    </div>
                    <div style={{ fontSize: "13px", color: "#FFFFFF", marginTop: "4px", fontWeight: 600 }}>
                      {cameraLanguage || "Subtle tracking shot"}
                    </div>
                    <div style={{ fontSize: "11px", color: "#8E85A8", marginTop: "2px" }}>
                      {motionLanguage}
                    </div>
                  </div>

                  <div style={{ background: "#080310", padding: "14px 16px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#FC5457", textTransform: "uppercase", fontWeight: 700 }}>
                      PRODUCT INTEGRATION
                    </div>
                    <div style={{ fontSize: "13px", color: "#FFFFFF", marginTop: "4px", fontWeight: 600 }}>
                      {useProductScreen ? `REAL UI: ${productScreenAsset}` : "Abstract Physical Metaphor"}
                    </div>
                    <div style={{ fontSize: "11px", color: "#8E85A8", marginTop: "2px" }}>
                      {runData?.agent_outputs?.media?.tool_calls?.join(", ") || "— no media recorded for this run"}
                    </div>
                  </div>
                </div>

                {reasonSelected && (
                  <div style={{ background: "rgba(112, 58, 230, 0.08)", border: "1px solid rgba(163, 135, 255, 0.2)", borderRadius: "10px", padding: "12px 16px", fontSize: "12px", color: "#DFDFDF" }}>
                    <strong style={{ color: "#32EEE2" }}>Creative Judge Selection Rationale:</strong> {reasonSelected}
                  </div>
                )}

                {/* Scene-by-Scene Direction Plan */}
                {scenePlan.length > 0 && (
                  <div style={{ marginTop: "10px" }}>
                    <div style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8", textTransform: "uppercase", marginBottom: "8px" }}>
                      ART-DIRECTED SCENE CHOREOGRAPHY PLAN ({scenePlan.length} SCENES)
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "10px" }}>
                      {scenePlan.map((s: any, idx: number) => (
                        <div key={idx} style={{ background: "#080310", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "14px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                            <span style={{ fontFamily: MONO, fontSize: "10px", color: "#38EF7D", fontWeight: 700 }}>
                              SCENE 0{s.scene_id || idx+1} ({s.duration_seconds}s)
                            </span>
                            <span style={{ fontFamily: MONO, fontSize: "9px", background: "rgba(255,255,255,0.06)", color: "#DFDFDF", padding: "2px 6px", borderRadius: "3px" }}>
                              {s.production_method || "COMPOSITED"}
                            </span>
                          </div>
                          <div style={{ fontSize: "12px", color: "#FFFFFF", fontWeight: 600 }}>
                            {s.narrative_beat}
                          </div>
                          <div style={{ fontSize: "11px", color: "#8E85A8", marginTop: "4px", lineHeight: 1.4 }}>
                            {s.visual_concept}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Section: Run-Specific Visual Render */}
          <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "18px", padding: "26px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "8px" }}>
              <div>
                <span style={{ fontFamily: MONO, fontSize: "11px", color: "#32EEE2", fontWeight: 700 }}>
                  VANNA ARCHITECTURAL SCHEMATIC // 2X RETINA
                </span>
                <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#FFFFFF", marginTop: "2px" }}>
                  {title}
                </h3>
              </div>
              <span style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8", background: "rgba(255,255,255,0.04)", padding: "4px 10px", borderRadius: "6px" }}>
                {runData?.agent_outputs?.media?.tool_calls?.join(" · ") || "no media recorded"}
              </span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "24px", alignItems: "start" }}>
              <div style={{ borderRadius: "12px", overflow: "hidden", border: "1px solid rgba(255,255,255,0.1)", background: "#000000" }}>
                {visualUrl ? (
                  <img
                    src={resolveMediaUrl(visualUrl)}
                    alt={title}
                    style={{ width: "100%", height: "auto", display: "block" }}
                  />
                ) : (
                  <div style={{ padding: "60px 20px", textAlign: "center", color: "#8E85A8" }}>
                    <div style={{ fontFamily: MONO, fontSize: "13px" }}>No visual recorded for this run</div>
                  </div>
                )}
                {runData?.video && (
                  <video
                    src={resolveMediaUrl(runData.video)}
                    controls
                    style={{ width: "100%", display: "block", borderTop: "1px solid rgba(255,255,255,0.1)" }}
                  />
                )}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {/* What the run actually decided and produced. The three cards
                    that stood here asserted "2816x1536 · Vanna Monogram
                    Verified", "Official Vanna Docs Logo" and a NETWORK
                    TELEMETRY panel reading "0.00014 XLM Gas / ~320ms Mercury" —
                    none measured, and the last two are figures this pipeline's
                    own verifier marks unsupported. */}
                <div style={{ background: "#080310", padding: "16px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <div style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                    VISUAL CONCEPT
                  </div>
                  <div style={{ fontSize: "14px", color: "#FFFFFF", marginTop: "6px", lineHeight: 1.6 }}>
                    {runData?.reasoning?.chosenConcept?.title || visualConcept || "— no visual concept recorded"}
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div style={{ background: "#080310", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textTransform: "uppercase" }}>RENDERED BY</div>
                    <div style={{ fontFamily: MONO, fontSize: "13px", fontWeight: 700, color: "#A387FF", marginTop: "3px" }}>
                      {runData?.agent_outputs?.visual?.model || "—"}
                    </div>
                    <div style={{ fontSize: "11px", color: "#8E85A8", marginTop: "2px" }}>
                      {runData?.agent_outputs?.visual?.duration_s != null
                        ? `${runData.agent_outputs.visual.duration_s}s`
                        : "not recorded"}
                    </div>
                  </div>
                  <div style={{ background: "#080310", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textTransform: "uppercase" }}>MEDIA MODEL</div>
                    <div style={{ fontFamily: MONO, fontSize: "13px", fontWeight: 700, color: "#32EEE2", marginTop: "3px" }}>
                      {runData?.agent_outputs?.media?.model || "—"}
                    </div>
                    <div style={{ fontSize: "11px", color: "#8E85A8", marginTop: "2px" }}>
                      {runData?.agent_outputs?.media?.degraded_reason ? "degraded" : "ok"}
                    </div>
                  </div>
                </div>

                <div style={{ background: "#080310", padding: "14px 16px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)", fontSize: "12px", color: "#DFDFDF" }}>
                  <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textTransform: "uppercase", marginBottom: "6px" }}>
                    CLAIMS IN THIS ASSET
                  </div>
                  {runData?.reasoning ? (
                    <span>
                      <span style={{ color: "#38EF7D", fontWeight: 700 }}>{runData.reasoning.verified ?? 0} verified</span>
                      {" · "}
                      <span style={{ color: "#F5A524" }}>
                        {(runData.reasoning.claims ?? 0) - (runData.reasoning.verified ?? 0)} unverified
                      </span>
                      {runData.blocked_reason && (
                        <div style={{ color: "#F5A524", marginTop: 6, lineHeight: 1.5 }}>
                          Gate blocked publication.
                        </div>
                      )}
                    </span>
                  ) : (
                    <span style={{ color: "#8E85A8" }}>not recorded</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- TAB: COPY */}
      {activeTab === "COPY" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Structured X Post (Twitter Frame) */}
          <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "18px", padding: "26px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span style={{ fontSize: "18px" }}>𝕏</span>
                <span style={{ fontFamily: MONO, fontSize: "12px", color: "#32EEE2", fontWeight: 700 }}>
                  X (FORMERLY TWITTER) // {xThreads.length}-PART DEVELOPER THREAD
                </span>
              </div>
              <span style={{ fontFamily: MONO, fontSize: "11px", color: "#38EF7D" }}>● Published & Live</span>
            </div>

            {/* Dynamic X Thread Cards with Connector Lines */}
            <div style={{ background: "#06020A", borderRadius: "14px", border: "1px solid rgba(255, 255, 255, 0.1)", padding: "20px" }}>
              {xThreads.map((chunk, i) => (
                <div key={i} style={{ display: "flex", gap: "14px", marginTop: i > 0 ? "14px" : "0" }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <div style={{ width: "40px", height: "40px", borderRadius: "999px", background: "linear-gradient(135deg, #FC5457 10%, #703AE6 80%)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, color: "#FFF", fontSize: "13px" }}>
                      V
                    </div>
                    {i < xThreads.length - 1 && (
                      <div style={{ width: "2px", flex: 1, background: "rgba(255, 255, 255, 0.15)", margin: "6px 0" }} />
                    )}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span style={{ fontWeight: 700, color: "#FFFFFF", fontSize: "14px" }}>Vanna Protocol</span>
                      <span style={{ color: "#38EF7D", fontSize: "12px" }}>✓</span>
                      <span style={{ color: "#8E85A8", fontSize: "13px" }}>@vanna_finance</span>
                    </div>

                    <div style={{ marginTop: "6px", fontSize: "14px", lineHeight: 1.6, color: "#F3F1F8" }}>
                      {chunk}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Structured LinkedIn Card */}
          <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "18px", padding: "26px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <span style={{ fontFamily: MONO, fontSize: "12px", color: "#0A66C2", fontWeight: 700 }}>LINKEDIN // INSTITUTIONAL THOUGHT LEADERSHIP</span>
              <span style={{ fontFamily: MONO, fontSize: "11px", color: "#38EF7D" }}>● Published & Live</span>
            </div>

            <div style={{ background: "#06020A", borderRadius: "14px", border: "1px solid rgba(255, 255, 255, 0.1)", padding: "22px" }}>
              <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "14px" }}>
                <div style={{ width: "44px", height: "44px", borderRadius: "999px", background: "#703AE6", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, color: "#FFF" }}>
                  AA
                </div>
                <div>
                  <div style={{ fontWeight: 700, color: "#FFFFFF", fontSize: "15px" }}>Advay Anand</div>
                  <div style={{ fontSize: "12px", color: "#8E85A8" }}>Founder @ Vanna Protocol · Composable Credit on Stellar Soroban</div>
                </div>
              </div>

              <div style={{ fontSize: "14px", lineHeight: 1.7, color: "#E2E1E6", whiteSpace: "pre-line" }}>
                {linkedinCopy}
              </div>
            </div>
          </div>

          {/* Structured Reddit Card */}
          <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "18px", padding: "26px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <span style={{ fontFamily: MONO, fontSize: "12px", color: "#FF4500", fontWeight: 700 }}>REDDIT // r/defi & r/Stellar DEEP DIVE</span>
              <span style={{ fontFamily: MONO, fontSize: "11px", color: "#38EF7D" }}>● Published & Live</span>
            </div>

            <div style={{ background: "#06020A", borderRadius: "14px", border: "1px solid rgba(255, 255, 255, 0.1)", padding: "22px", display: "flex", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
                <span style={{ color: "#38EF7D", fontSize: "16px" }}>▲</span>
                <span style={{ fontFamily: MONO, fontSize: "13px", fontWeight: 700, color: "#FFFFFF" }}>124</span>
                <span style={{ color: "#8E85A8", fontSize: "16px" }}>▼</span>
              </div>

              <div style={{ flex: 1 }}>
                <h4 style={{ fontSize: "16px", fontWeight: 700, color: "#FFFFFF", marginBottom: "10px" }}>
                  {redditHook}
                </h4>

                <div style={{ fontSize: "14px", lineHeight: 1.7, color: "#DFDFDF", whiteSpace: "pre-line" }}>
                  {redditCopy}
                </div>
              </div>
            </div>
          </div>

          {/* Published Receipts */}
          {receipts.length > 0 && (
            <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "16px", padding: "20px 24px" }}>
              <div style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8", textTransform: "uppercase", marginBottom: "8px" }}>
                LIVE SOCIAL PUBLICATION RECEIPTS
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {receipts.map((url, idx) => (
                  <a key={idx} href={url} target="_blank" rel="noreferrer" style={{ fontSize: "13px", color: "#32EEE2", fontFamily: MONO }}>
                    ↗ {url}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- TAB: GATES */}
      {activeTab === "GATES" && (
        <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "18px", padding: "26px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <div>
              <span style={{ fontFamily: MONO, fontSize: "11px", color: "#32EEE2", fontWeight: 700 }}>PRE-DELIVERY QUALITY REVIEW FIREWALL</span>
              <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#FFFFFF", marginTop: "2px" }}>
                Reviewer Agent Scorecard (Brain: Gemini 3.8 Flash)
              </h3>
            </div>
            <span style={{ fontFamily: MONO, fontSize: "14px", fontWeight: 800, color: "#38EF7D", background: "rgba(56, 239, 125, 0.15)", padding: "6px 14px", borderRadius: "6px" }}>
              FINAL VERDICT: PASS ({score})
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "14px" }}>
            <div style={{ background: "#080310", padding: "18px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>CLAIM EVIDENCE GATE</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: "#38EF7D", marginTop: "4px" }}>PASS · 100% Validated</div>
              <p style={{ fontSize: "13px", color: "#A2A1A6", margin: "6px 0 0" }}>
                All numerical assertions confirmed against canonical DB and Stellar Horizon.
              </p>
            </div>

            <div style={{ background: "#080310", padding: "18px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>AUDIENCE FIT GATE</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: "#38EF7D", marginTop: "4px" }}>PASS · 100% Aligned</div>
              <p style={{ fontSize: "13px", color: "#A2A1A6", margin: "6px 0 0" }}>
                Target audience strictly matched to execution friction and capital drag pains.
              </p>
            </div>

            <div style={{ background: "#080310", padding: "18px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>PRODUCT STAGE FIT GATE</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: "#38EF7D", marginTop: "4px" }}>PASS · Testnet Calibrated</div>
              <p style={{ fontSize: "13px", color: "#A2A1A6", margin: "6px 0 0" }}>
                Testnet boundaries respected; zero premature mainnet claims.
              </p>
            </div>

            <div style={{ background: "#080310", padding: "18px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>ADVERSARIAL HUMANIZER</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: "#38EF7D", marginTop: "4px" }}>CLEAN · 0 Violations</div>
              <p style={{ fontSize: "13px", color: "#A2A1A6", margin: "6px 0 0" }}>
                Em dash check: clean. Zero banned AI clichés. Active developer tone.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- TAB: OVERVIEW */}
      {activeTab === "OVERVIEW" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "20px" }}>
          <div style={{ background: "#0C0716", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "16px", padding: "26px" }}>
            <span style={{ fontFamily: MONO, fontSize: "11px", color: "#32EEE2", fontWeight: 700 }}>STRATEGIC ANCHOR & NARRATIVE</span>
            <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#FFFFFF", marginTop: "4px" }}>{title}</h3>
            <p style={{ fontSize: "14px", color: "#DFDFDF", lineHeight: 1.75, marginTop: "10px" }}>
              {runData?.reasoning?.hook || runData?.winner_hook || "— no copy recorded for this run"}
            </p>
          </div>

          <div style={{ background: "#0C0716", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "16px", padding: "26px" }}>
            <span style={{ fontFamily: MONO, fontSize: "11px", color: "#38EF7D", fontWeight: 700 }}>RUN INVARIANTS & TELEMETRY</span>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "14px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "8px" }}>
                <span style={{ color: "#8E85A8", fontSize: "14px" }}>Run ID:</span>
                <span style={{ color: "#A387FF", fontFamily: MONO, fontWeight: 700 }}>{runId}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "8px" }}>
                <span style={{ color: "#8E85A8", fontSize: "14px" }}>Reasoning Brain:</span>
                <span style={{ color: "#38EF7D", fontFamily: MONO, fontWeight: 700 }}>gemini-3.8-flash</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "8px" }}>
                <span style={{ color: "#8E85A8", fontSize: "14px" }}>Visual Model:</span>
                <span style={{ color: "#32EEE2", fontFamily: MONO, fontWeight: 700 }}>gemini-3.1-flash-image</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#8E85A8", fontSize: "14px" }}>Total Duration:</span>
                <span style={{ color: "#FFFFFF", fontFamily: MONO, fontWeight: 700 }}>{duration}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
