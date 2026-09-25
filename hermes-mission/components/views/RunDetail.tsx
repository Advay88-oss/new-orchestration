"use client";

import React, { useState, useEffect } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";
import { FeedbackBar } from "./FeedbackBar";

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
  // Waiting, not approved. Defaulting to APPROVED told the founder a run had
  // cleared review before they had seen it — including runs the firewall
  // blocked and never delivered to anyone.
  const [approvalStatus, setApprovalStatus] = useState<"WAITING_FOR_HUMAN" | "APPROVED" | "KILLED">("WAITING_FOR_HUMAN");
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


  if (!runData && !loading) {
    return (
      <section style={{ padding: "40px 32px", maxWidth: "1200px" }}>
        <div style={{ background: "#0C0716", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "18px", padding: "40px 32px", textAlign: "center" }}>
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>🔍</div>
          <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#FFFFFF" }}>No System 2 Run Selected</h3>
          <p style={{ color: "#7B7590", fontSize: "14px", marginTop: "8px", maxWidth: "56ch", margin: "8px auto 0" }}>
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
  // These read `agent_outputs.agent_03_strategist` / `agent_04_machine`, keys
  // the API does not emit, so every run showed the same two typed strings.
  // A03 records the audience and A04 the machine; both are on the run.
  const audience = runData?.reasoning?.audience ?? "—";
  const machine = runData?.machine ?? runData?.reasoning?.playbook ?? "—";
  const duration = runData?.duration_s ? `${runData.duration_s}s` : "—";
  
  const directive = runData?.directive || null;

  // Run-specific media assets
  const videoData = runData?.agent_outputs?.agent_09_video || null;
  const videoUrl = videoData?.public_url || runData?.video || null;
  const visualUrl = runData?.agent_outputs?.agent_08_visual?.public_url || runData?.visual || null;
  // No invented fallback: if the run recorded no concept, the UI says so.
  // The 13-agent summary records these as top-level fields; the keys this
  // read first belong to the retired core/ pipeline and are never set now,
  // which is why every run said "no visual concept recorded".
  const visualConcept = runData?.visual_concept
    ?? runData?.agent_outputs?.agent_07_creative?.concept
    ?? runData?.reasoning?.chosenConcept?.idea
    ?? null;
  // The image is composed by an archetype renderer under A07; A08's model is
  // only involved when the archetype asks it for a background.
  const visualAgent = runData?.agent_outputs?.A08_visual_synthesis
    ?? runData?.agent_outputs?.visual ?? null;
  const directorAgent = runData?.agent_outputs?.A07_creative_director ?? null;
  const mediaModels: string[] = (runData?.models_used ?? []).filter(
    (m: string) => /image|veo|imagen|banana/i.test(m));
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
  const noveltyScore = videoData?.novelty_score ?? null;
  const previousSimilarity = videoData?.previous_similarity || "LOW";
  const reasonSelected = videoData?.reason_selected || null;
  const scenePlan = Array.isArray(videoData?.scene_plan) ? videoData.scene_plan : [];
  const useProductScreen = videoData?.use_product_screen;
  const productScreenAsset = videoData?.product_screen_asset;

  // Run-specific multi-channel copy.
  //
  // A06 writes this and always has. It was read from
  // `agent_outputs.agent_06_content.{x_threads,linkedin_copy,reddit_copy}` —
  // a key namespace the API has never emitted (`agent_outputs` is keyed by
  // agent id, e.g. `A06_channel_adapter`, and holds metadata, not text). So
  // every chain fell through to the literal "Generation in progress…" while
  // three finished posts sat in the same payload under `posts`.
  const posts = runData?.posts ?? {};
  const xCopy: string | null = posts?.x?.copy ?? null;
  const xHook: string | null = posts?.x?.hook ?? null;
  // The X post is one body; splitting on blank lines gives the thread as A06
  // actually wrote it rather than inventing tweet boundaries.
  const xThreads: string[] = xCopy
    ? xCopy.split(/\n\s*\n/).map((s: string) => s.trim()).filter(Boolean)
    : [];

  const linkedinHook: string | null = posts?.linkedin?.hook ?? null;
  const linkedinCopy: string | null = posts?.linkedin?.copy ?? null;
  const redditHook: string | null = posts?.reddit?.hook ?? null;
  const redditCopy: string | null = posts?.reddit?.copy ?? null;

  // The judge's real output. `creative_review` holds one entry per rendered
  // asset plus a copy verdict; A10's firewall records blocked claims
  // separately. Neither produces a numeric score, so none is displayed.
  const review = runData?.creative_review ?? null;
  const overallVerdict: string | null =
    review?.overall ?? runData?.creative_verdict ?? null;
  const copyVerdict: string | null = review?.copy_verdict ?? null;
  const copyCritique: string | null = review?.copy_critique ?? null;
  const assetVerdicts: any[] = Array.isArray(review?.assets)
    ? review.assets
    : Object.entries(review ?? {})
        .filter(([, v]: [string, any]) => v && typeof v === "object" && v.verdict)
        .map(([k, v]: [string, any]) => ({ asset: k, ...v }));
  const blockedClaims: any[] = Array.isArray(runData?.review_notes?.blocked_claims)
    ? runData.review_notes.blocked_claims
    : [];

  const verdictTone = (v: string | null) =>
    v === "SHIP" ? "#4ADE9B" : v === "REVISE" ? "#F5A524" : v === "REJECT" ? "#F0666B" : "#7B7590";

  // Nothing here is published until A11 dispatches, and A11 does not run
  // unprompted. The three cards used to assert "Published & Live" from a
  // literal, on runs the reviewer firewall had blocked.
  const dispatched: boolean = runData?.dispatched === true;
  const channelState = dispatched
    ? { label: "● Published & Live", color: "#4ADE9B" }
    : runData?.publishable === true
      ? { label: "○ Approved · awaiting dispatch", color: "#F5A524" }
      : { label: "○ Draft · not published", color: "#7B7590" };

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
              color: "#A98CFF",
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
            <span style={{ width: "10px", height: "10px", borderRadius: "999px", background: "#4ADE9B" }} />
            <span style={{ fontFamily: MONO, fontSize: "12px", fontWeight: 700, color: "#4ADE9B", letterSpacing: "0.08em" }}>
              {runId} // IMMUTABLE TELEMETRY RECORD
            </span>
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#FFFFFF", marginTop: "6px" }}>
            {title}
          </h2>
          {directive && (
            <div style={{ marginTop: "6px", fontSize: "13px", color: "#A98CFF" }}>
              <strong>Founder Directive Executed:</strong> &ldquo;{directive}&rdquo;
            </div>
          )}
          <div style={{ display: "flex", gap: "16px", marginTop: "8px", fontSize: "13px", color: "#7B7590", flexWrap: "wrap" }}>
            <span><strong>Target Audience:</strong> {audience}</span>
            <span>·</span>
            <span><strong>Machine:</strong> {machine}</span>
            <span>·</span>
            <span><strong>Duration:</strong> {duration}</span>
            <span>·</span>
            <span><strong>Review:</strong> {overallVerdict ?? "not reviewed"}</span>
          </div>
        </div>

        {/* The Approve/Revise/Kill buttons that sat here posted to
            /api/runs/[id], which has no POST handler, so every click failed —
            while the approve button promised "dispatch". The FeedbackBar
            below the header replaces them and records, never publishes. */}
      </div>

      {actionFeedback && (
        <div style={{ fontFamily: MONO, fontSize: "12px", color: "#4ADE9B", background: "rgba(56, 239, 125, 0.1)", padding: "10px 18px", borderRadius: "10px", border: "1px solid rgba(56, 239, 125, 0.3)" }}>
          {actionFeedback}
        </div>
      )}

      {/* The founder's decision: the reward the learning loop records. */}
      {runData?.run_id && <FeedbackBar runId={runData.run_id} />}

      {/* Tab Controls */}
      <div style={{ display: "flex", gap: "10px", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "12px", flexWrap: "wrap" }}>
        {[
          { id: "OVERVIEW", label: "Executive Overview" },
          { id: "MEDIA", label: `🎬 Run Video & Visuals (${runId})` },
          { id: "COPY", label: `📱 Post Content (${xThreads.length} X Chunks · LI · Reddit)` },
          { id: "GATES", label: `🛡️ Review${overallVerdict ? ` (${overallVerdict})` : ""}` }
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id as any)}
            style={{
              background: activeTab === t.id ? "rgba(112, 58, 230, 0.25)" : "transparent",
              border: `1px solid ${activeTab === t.id ? "#703AE6" : "transparent"}`,
              color: activeTab === t.id ? "#FFFFFF" : "#7B7590",
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
                  <span style={{ fontFamily: MONO, fontSize: "10px", fontWeight: 800, color: "#4ADE9B", background: "rgba(56, 239, 125, 0.15)", padding: "2px 8px", borderRadius: "4px" }}>
                    CREATIVE NOVELTY: {noveltyScore}/100
                  </span>
                  <span style={{ fontFamily: MONO, fontSize: "10px", color: previousSimilarity === "LOW" ? "#A98CFF" : "#F5A623", background: "rgba(255,255,255,0.05)", padding: "2px 8px", borderRadius: "4px" }}>
                    SIMILARITY: {previousSimilarity}
                  </span>
                  <span style={{ fontFamily: MONO, fontSize: "10px", color: "#A98CFF", background: "rgba(112, 58, 230, 0.2)", padding: "2px 8px", borderRadius: "4px" }}>
                    PIPELINE: {productionStrategy}
                  </span>
                </div>
                <h3 style={{ fontSize: "20px", fontWeight: 800, color: "#FFFFFF", margin: 0 }}>
                  {creativeConcept || title}
                </h3>
                {visualThesis && (
                  <p style={{ fontSize: "13px", color: "#B8B3C6", marginTop: "6px", maxWidth: "900px", lineHeight: 1.55 }}>
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
                      background: "linear-gradient(135deg, #703AE6, #A98CFF)",
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
                <div style={{ padding: "60px 20px", textAlign: "center", color: "#7B7590" }}>
                  <div style={{ fontSize: "28px", marginBottom: "8px" }}>🎬</div>
                  <div style={{ fontFamily: MONO, fontSize: "14px", fontWeight: 700, color: "#FFFFFF" }}>No Video Requested for this Run</div>
                  <div style={{ fontSize: "12px", color: "#7B7590", marginTop: "4px" }}>
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
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#A98CFF", textTransform: "uppercase", fontWeight: 700 }}>
                      VISUAL METAPHOR & LANGUAGE
                    </div>
                    <div style={{ fontSize: "13px", color: "#FFFFFF", marginTop: "4px", fontWeight: 600 }}>
                      {visualMetaphor || "— not recorded for this run"}
                    </div>
                    <div style={{ fontSize: "11px", color: "#7B7590", marginTop: "2px" }}>
                      {visualLanguage}
                    </div>
                  </div>

                  <div style={{ background: "#080310", padding: "14px 16px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#A98CFF", textTransform: "uppercase", fontWeight: 700 }}>
                      CAMERA & MOTION CHOREOGRAPHY
                    </div>
                    <div style={{ fontSize: "13px", color: "#FFFFFF", marginTop: "4px", fontWeight: 600 }}>
                      {cameraLanguage || "Subtle tracking shot"}
                    </div>
                    <div style={{ fontSize: "11px", color: "#7B7590", marginTop: "2px" }}>
                      {motionLanguage}
                    </div>
                  </div>

                  <div style={{ background: "#080310", padding: "14px 16px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#F0666B", textTransform: "uppercase", fontWeight: 700 }}>
                      PRODUCT INTEGRATION
                    </div>
                    <div style={{ fontSize: "13px", color: "#FFFFFF", marginTop: "4px", fontWeight: 600 }}>
                      {useProductScreen ? `REAL UI: ${productScreenAsset}` : "Abstract Physical Metaphor"}
                    </div>
                    <div style={{ fontSize: "11px", color: "#7B7590", marginTop: "2px" }}>
                      {runData?.agent_outputs?.media?.tool_calls?.join(", ") || "— no media recorded for this run"}
                    </div>
                  </div>
                </div>

                {reasonSelected && (
                  <div style={{ background: "rgba(112, 58, 230, 0.08)", border: "1px solid rgba(163, 135, 255, 0.2)", borderRadius: "10px", padding: "12px 16px", fontSize: "12px", color: "#B8B3C6" }}>
                    <strong style={{ color: "#A98CFF" }}>Creative Judge Selection Rationale:</strong> {reasonSelected}
                  </div>
                )}

                {/* Scene-by-Scene Direction Plan */}
                {scenePlan.length > 0 && (
                  <div style={{ marginTop: "10px" }}>
                    <div style={{ fontFamily: MONO, fontSize: "11px", color: "#7B7590", textTransform: "uppercase", marginBottom: "8px" }}>
                      ART-DIRECTED SCENE CHOREOGRAPHY PLAN ({scenePlan.length} SCENES)
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "10px" }}>
                      {scenePlan.map((s: any, idx: number) => (
                        <div key={idx} style={{ background: "#080310", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "14px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                            <span style={{ fontFamily: MONO, fontSize: "10px", color: "#4ADE9B", fontWeight: 700 }}>
                              SCENE 0{s.scene_id || idx+1} ({s.duration_seconds}s)
                            </span>
                            <span style={{ fontFamily: MONO, fontSize: "9px", background: "rgba(255,255,255,0.06)", color: "#B8B3C6", padding: "2px 6px", borderRadius: "3px" }}>
                              {s.production_method || "COMPOSITED"}
                            </span>
                          </div>
                          <div style={{ fontSize: "12px", color: "#FFFFFF", fontWeight: 600 }}>
                            {s.narrative_beat}
                          </div>
                          <div style={{ fontSize: "11px", color: "#7B7590", marginTop: "4px", lineHeight: 1.4 }}>
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
                <span style={{ fontFamily: MONO, fontSize: "11px", color: "#A98CFF", fontWeight: 700 }}>
                  VANNA ARCHITECTURAL SCHEMATIC // 2X RETINA
                </span>
                <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#FFFFFF", marginTop: "2px" }}>
                  {title}
                </h3>
              </div>
              <span style={{ fontFamily: MONO, fontSize: "11px", color: "#7B7590", background: "rgba(255,255,255,0.04)", padding: "4px 10px", borderRadius: "6px" }}>
                {mediaModels.length
                  ? mediaModels.join(" · ")
                  : runData?.visual_archetype
                    ? "typeset in code · no image model"
                    : "no media recorded"}
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
                  <div style={{ padding: "60px 20px", textAlign: "center", color: "#7B7590" }}>
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
                {/* The Motion Director's own work: the brief the image model
                    drew from and the beat-by-beat build Veo was given. These
                    were hand-written for the first liked video; an agent writes
                    them now, from the founder's record. */}
                {runData?.source === "studio" && (
                  <div style={{ background: "rgba(112,58,230,0.12)", padding: "10px 14px", borderRadius: "10px", border: "1px solid rgba(112,58,230,0.35)", fontSize: "12px", color: "#CFC8E0" }}>
                    <span style={{ fontFamily: MONO, fontWeight: 700, color: "#A98CFF" }}>STUDIO</span> — made in the creative studio, outside a full cycle: only the visual and video agents ran.
                  </div>
                )}
                {(runData?.poster_brief || runData?.motion_plan || runData?.visual_review) && (
                  <div style={{ background: "#080310", padding: "16px", borderRadius: "10px", border: "1px solid rgba(112,58,230,0.35)" }}>
                    <div style={{ fontFamily: MONO, fontSize: "11px", color: "#A98CFF", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 700 }}>
                      MOTION DIRECTOR
                    </div>
                    {runData?.poster_brief && (
                      <>
                        <div style={{ fontFamily: MONO, fontSize: "10px", color: "#7B7590", marginTop: "10px" }}>POSTER BRIEF</div>
                        <div style={{ fontSize: "12px", color: "#E6E1F0", marginTop: "4px", lineHeight: 1.55, whiteSpace: "pre-wrap" }}>
                          {runData.poster_brief}
                        </div>
                      </>
                    )}
                    {runData?.motion_plan && (
                      <>
                        <div style={{ fontFamily: MONO, fontSize: "10px", color: "#7B7590", marginTop: "12px" }}>
                          MOTION PLAN · {runData.video_mode === "veo_build" ? "Veo 3.1 builds the poster from the empty ground" : runData.video_mode || "—"}
                        </div>
                        <div style={{ fontSize: "12px", color: "#E6E1F0", marginTop: "4px", lineHeight: 1.55, whiteSpace: "pre-wrap" }}>
                          {runData.motion_plan}
                        </div>
                      </>
                    )}
                    {runData?.visual_review?.verdict && (
                      <div style={{ fontSize: "12px", color: "#B8B3C6", marginTop: "10px", lineHeight: 1.5 }}>
                        <span style={{ fontFamily: MONO, fontWeight: 700, color: runData.visual_review.verdict === "SHIP" ? "#4ADE9B" : runData.visual_review.verdict === "REVISE" ? "#F5A524" : "#F0666B" }}>
                          POSTER {runData.visual_review.verdict}
                        </span>
                        {runData.visual_review.fix ? ` — ${runData.visual_review.fix}` : ""}
                      </div>
                    )}
                    {runData?.video_review?.verdict && (
                      <div style={{ fontSize: "12px", color: "#B8B3C6", marginTop: "10px", lineHeight: 1.5 }}>
                        <span style={{ fontFamily: MONO, fontWeight: 700, color: runData.video_review.verdict === "SHIP" ? "#4ADE9B" : runData.video_review.verdict === "REVISE" ? "#F5A524" : "#F0666B" }}>
                          VIDEO {runData.video_review.verdict}
                        </span>
                        {runData.video_review.critique ? ` — ${runData.video_review.critique}` : ""}
                      </div>
                    )}
                  </div>
                )}

                <div style={{ background: "#080310", padding: "16px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <div style={{ fontFamily: MONO, fontSize: "11px", color: "#7B7590", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                    VISUAL CONCEPT
                  </div>
                  <div style={{ fontSize: "14px", color: "#FFFFFF", marginTop: "6px", lineHeight: 1.6 }}>
                    {runData?.reasoning?.chosenConcept?.title || visualConcept || "— no visual concept recorded"}
                  </div>
                  {runData?.visual_archetype && (
                    <div style={{ fontSize: "12px", color: "#B8B3C6", marginTop: "10px", lineHeight: 1.5 }}>
                      <span style={{ fontFamily: MONO, color: "#A98CFF", fontWeight: 700 }}>{runData.visual_archetype}</span>
                      {runData.visual_why ? ` — ${runData.visual_why}` : ""}
                    </div>
                  )}
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div style={{ background: "#080310", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#7B7590", textTransform: "uppercase" }}>RENDERED BY</div>
                    <div style={{ fontFamily: MONO, fontSize: "13px", fontWeight: 700, color: "#A98CFF", marginTop: "3px" }}>
                      {runData?.visual_archetype || visualAgent?.model || "—"}
                    </div>
                    <div style={{ fontSize: "11px", color: "#7B7590", marginTop: "2px" }}>
                      {directorAgent
                        ? `A07 creative director · ${directorAgent.status}`
                        : visualAgent?.duration_s != null
                          ? `${visualAgent.duration_s}s`
                          : "not recorded"}
                    </div>
                  </div>
                  <div style={{ background: "#080310", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#7B7590", textTransform: "uppercase" }}>MEDIA MODEL</div>
                    <div style={{ fontFamily: MONO, fontSize: "13px", fontWeight: 700, color: "#A98CFF", marginTop: "3px" }}>
                      {mediaModels[0] || (runData?.visual_archetype ? "none" : "—")}
                    </div>
                    <div style={{ fontSize: "11px", color: "#7B7590", marginTop: "2px" }}>
                      {mediaModels.length
                        ? "background only — every word is typeset"
                        : runData?.visual_archetype ? "typeset layout" : "not recorded"}
                    </div>
                  </div>
                </div>

                <div style={{ background: "#080310", padding: "14px 16px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)", fontSize: "12px", color: "#B8B3C6" }}>
                  <div style={{ fontFamily: MONO, fontSize: "10px", color: "#7B7590", textTransform: "uppercase", marginBottom: "6px" }}>
                    CLAIMS IN THIS ASSET
                  </div>
                  {runData?.reasoning ? (
                    <span>
                      <span style={{ color: "#4ADE9B", fontWeight: 700 }}>{runData.reasoning.verified ?? 0} verified</span>
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
                    <span style={{ color: "#7B7590" }}>not recorded</span>
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
                <span style={{ fontFamily: MONO, fontSize: "12px", color: "#A98CFF", fontWeight: 700 }}>
                  X (FORMERLY TWITTER) // {xThreads.length}-PART DEVELOPER THREAD
                </span>
              </div>
              <span style={{ fontFamily: MONO, fontSize: "11px", color: channelState.color }}>
                {channelState.label}
              </span>
            </div>

            {/* Dynamic X Thread Cards with Connector Lines */}
            <div style={{ background: "#080310", borderRadius: "14px", border: "1px solid rgba(255, 255, 255, 0.1)", padding: "20px" }}>
              {xThreads.map((chunk, i) => (
                <div key={i} style={{ display: "flex", gap: "14px", marginTop: i > 0 ? "14px" : "0" }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <div style={{ width: "40px", height: "40px", borderRadius: "999px", background: "#703AE6", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, color: "#FFF", fontSize: "13px" }}>
                      V
                    </div>
                    {i < xThreads.length - 1 && (
                      <div style={{ width: "2px", flex: 1, background: "rgba(255, 255, 255, 0.15)", margin: "6px 0" }} />
                    )}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span style={{ fontWeight: 700, color: "#FFFFFF", fontSize: "14px" }}>Vanna Protocol</span>
                      <span style={{ color: "#4ADE9B", fontSize: "12px" }}>✓</span>
                      <span style={{ color: "#7B7590", fontSize: "13px" }}>@vanna_finance</span>
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
              <span style={{ fontFamily: MONO, fontSize: "11px", color: channelState.color }}>
                {channelState.label}
              </span>
            </div>

            <div style={{ background: "#080310", borderRadius: "14px", border: "1px solid rgba(255, 255, 255, 0.1)", padding: "22px" }}>
              <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "14px" }}>
                <div style={{ width: "44px", height: "44px", borderRadius: "999px", background: "#703AE6", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, color: "#FFF" }}>
                  AA
                </div>
                <div>
                  <div style={{ fontWeight: 700, color: "#FFFFFF", fontSize: "15px" }}>Advay Anand</div>
                  <div style={{ fontSize: "12px", color: "#7B7590" }}>Founder @ Vanna Protocol · Composable Credit on Stellar Soroban</div>
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
              <span style={{ fontFamily: MONO, fontSize: "11px", color: channelState.color }}>
                {channelState.label}
              </span>
            </div>

            <div style={{ background: "#080310", borderRadius: "14px", border: "1px solid rgba(255, 255, 255, 0.1)", padding: "22px", display: "flex", gap: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
                <span style={{ color: "#4ADE9B", fontSize: "16px" }}>▲</span>
                <span style={{ fontFamily: MONO, fontSize: "13px", fontWeight: 700, color: "#4A4A4A" }}>
                  {/* No score exists: the post was never submitted. */}—
                </span>
                <span style={{ color: "#7B7590", fontSize: "16px" }}>▼</span>
              </div>

              <div style={{ flex: 1 }}>
                <h4 style={{ fontSize: "16px", fontWeight: 700, color: "#FFFFFF", marginBottom: "10px" }}>
                  {redditHook}
                </h4>

                <div style={{ fontSize: "14px", lineHeight: 1.7, color: "#B8B3C6", whiteSpace: "pre-line" }}>
                  {redditCopy}
                </div>
              </div>
            </div>
          </div>

          {/* Published Receipts */}
          {receipts.length > 0 && (
            <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "16px", padding: "20px 24px" }}>
              <div style={{ fontFamily: MONO, fontSize: "11px", color: "#7B7590", textTransform: "uppercase", marginBottom: "8px" }}>
                LIVE SOCIAL PUBLICATION RECEIPTS
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {receipts.map((url, idx) => (
                  <a key={idx} href={url} target="_blank" rel="noreferrer" style={{ fontSize: "13px", color: "#A98CFF", fontFamily: MONO }}>
                    ↗ {url}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- TAB: GATES */}
      {/*
        This tab used to render four PASS cards and a 96/100 verdict from
        string literals — no props, no state, no run data. They could not
        render as FAIL. On this very run the judge returned REJECT: the meme
        carried garbled baked-in text, and the copy implied mainnet. The card
        reading "zero premature mainnet claims" sat directly over it.

        Everything below is the judge's own output: `creative_review` from
        `pipeline/gtm_os/creative_judge.py` and `review_notes` from the A10
        firewall. The judge records enum verdicts and prose critiques, not
        scores, so no score is shown.
      */}
      {activeTab === "GATES" && (
        <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "18px", padding: "26px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "12px" }}>
            <div>
              <span style={{ fontFamily: MONO, fontSize: "11px", color: "#A98CFF", fontWeight: 700 }}>PRE-DELIVERY REVIEW FIREWALL</span>
              <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#FFFFFF", marginTop: "2px" }}>
                What the judge actually returned
              </h3>
            </div>
            <span style={{ fontFamily: MONO, fontSize: "14px", fontWeight: 800, color: verdictTone(overallVerdict), background: `${verdictTone(overallVerdict)}22`, padding: "6px 14px", borderRadius: "6px" }}>
              {overallVerdict ? `VERDICT: ${overallVerdict}` : "NOT REVIEWED"}
            </span>
          </div>

          {assetVerdicts.length === 0 && blockedClaims.length === 0 && !overallVerdict && (
            <p style={{ fontSize: "14px", color: "#7B7590", margin: 0 }}>
              This run recorded no review. A07 judges the rendered assets and A10 checks
              the claims; neither left anything in this run&apos;s journal.
            </p>
          )}

          {assetVerdicts.length > 0 && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px" }}>
              {assetVerdicts.map((a: any) => (
                <div key={a.asset} style={{ background: "#080310", padding: "18px", borderRadius: "12px", border: `1px solid ${verdictTone(a.verdict)}33` }}>
                  <div style={{ fontFamily: MONO, fontSize: "10px", color: "#7B7590", textTransform: "uppercase" }}>{a.asset}</div>
                  <div style={{ fontSize: "18px", fontWeight: 700, color: verdictTone(a.verdict), marginTop: "4px" }}>{a.verdict}</div>
                  {a.critique && (
                    <p style={{ fontSize: "13px", color: "#7B7590", margin: "8px 0 0", lineHeight: 1.6 }}>{a.critique}</p>
                  )}
                  {a.fix && (
                    <p style={{ fontSize: "12px", color: "#F5A524", margin: "8px 0 0", lineHeight: 1.6 }}>
                      <strong>Fix:</strong> {a.fix}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* A10's claim firewall, which is a separate check from the creative judge. */}
          <div style={{ marginTop: "18px", background: "#080310", padding: "18px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "#7B7590" }}>CLAIM FIREWALL (A10)</div>
            <div style={{ fontSize: "18px", fontWeight: 700, marginTop: "4px", color: blockedClaims.length ? "#F0666B" : runData?.review_notes ? "#4ADE9B" : "#7B7590" }}>
              {blockedClaims.length
                ? `${blockedClaims.length} claim${blockedClaims.length === 1 ? "" : "s"} blocked`
                : // The firewall ran and blocked nothing. A run can still be
                  // blocked overall — this one was, by the creative judge —
                  // so the two results are reported separately.
                  runData?.review_notes
                  ? "no claims blocked"
                  : "not recorded"}
            </div>
            {blockedClaims.length > 0 && (
              <ul style={{ margin: "8px 0 0", paddingLeft: "18px", color: "#7B7590", fontSize: "13px", lineHeight: 1.7 }}>
                {blockedClaims.map((c: any, i: number) => (
                  <li key={i}>{typeof c === "string" ? c : JSON.stringify(c)}</li>
                ))}
              </ul>
            )}
            {runData?.blocked_reason && (
              <p style={{ fontSize: "13px", color: "#F0666B", margin: "8px 0 0" }}>{runData.blocked_reason}</p>
            )}
          </div>

          {copyVerdict && (
            <div style={{ marginTop: "14px", background: "#080310", padding: "18px", borderRadius: "12px", border: `1px solid ${verdictTone(copyVerdict)}33` }}>
              <div style={{ fontFamily: MONO, fontSize: "10px", color: "#7B7590" }}>COPY</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: verdictTone(copyVerdict), marginTop: "4px" }}>{copyVerdict}</div>
              {copyCritique && (
                <p style={{ fontSize: "13px", color: "#7B7590", margin: "8px 0 0", lineHeight: 1.6 }}>{copyCritique}</p>
              )}
            </div>
          )}

          {/* Delivery is the terminus. Saying a run passed means nothing if no
              human ever received it. */}
          <div style={{ marginTop: "14px", fontFamily: MONO, fontSize: "12px", color: "#7B7590" }}>
            DELIVERED TO REVIEWER: {runData?.dispatched === true ? "yes" : "no"}
            {runData?.dispatch_detail ? ` · ${runData.dispatch_detail}` : ""}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- TAB: OVERVIEW */}
      {activeTab === "OVERVIEW" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "20px" }}>
          <div style={{ background: "#0C0716", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "16px", padding: "26px" }}>
            <span style={{ fontFamily: MONO, fontSize: "11px", color: "#A98CFF", fontWeight: 700 }}>STRATEGIC ANCHOR & NARRATIVE</span>
            <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#FFFFFF", marginTop: "4px" }}>{title}</h3>
            <p style={{ fontSize: "14px", color: "#B8B3C6", lineHeight: 1.75, marginTop: "10px" }}>
              {runData?.reasoning?.hook || runData?.winner_hook || "— no copy recorded for this run"}
            </p>
          </div>

          <div style={{ background: "#0C0716", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "16px", padding: "26px" }}>
            <span style={{ fontFamily: MONO, fontSize: "11px", color: "#4ADE9B", fontWeight: 700 }}>RUN INVARIANTS & TELEMETRY</span>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "14px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "8px" }}>
                <span style={{ color: "#7B7590", fontSize: "14px" }}>Run ID:</span>
                <span style={{ color: "#A98CFF", fontFamily: MONO, fontWeight: 700 }}>{runId}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "8px" }}>
                <span style={{ color: "#7B7590", fontSize: "14px" }}>Reasoning Brain:</span>
                <span style={{ color: "#4ADE9B", fontFamily: MONO, fontWeight: 700 }}>gemini-3.8-flash</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "8px" }}>
                <span style={{ color: "#7B7590", fontSize: "14px" }}>Visual Model:</span>
                <span style={{ color: "#A98CFF", fontFamily: MONO, fontWeight: 700 }}>gemini-3.1-flash-image</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#7B7590", fontSize: "14px" }}>Total Duration:</span>
                <span style={{ color: "#FFFFFF", fontFamily: MONO, fontWeight: 700 }}>{duration}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
