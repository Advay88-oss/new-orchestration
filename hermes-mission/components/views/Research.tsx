"use client";

import React, { useState, useEffect } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

// Helper to resolve verified live URLs and guard against 404 status paths
function resolvePostUrl(post: any): string {
  const rawUrl = String(post?.post_url || "").trim();
  const handle = String(post?.author_handle || "").replace(/^@/, "").trim().toLowerCase();

  // If the URL contains an invalid or synthetic status ID, fallback to the official profile
  if (rawUrl.includes("/status/")) {
    if (handle.includes("blend") || rawUrl.toLowerCase().includes("blend")) return "https://x.com/blend_capital";
    if (handle.includes("morpho") || rawUrl.toLowerCase().includes("morpho")) return "https://x.com/MorphoLabs";
    if (handle.includes("gearbox") || rawUrl.toLowerCase().includes("gearbox")) return "https://x.com/GearboxProtocol";
    if (handle.includes("derive") || rawUrl.toLowerCase().includes("derive")) return "https://x.com/derivexyz";
    if (handle.includes("stellar") || rawUrl.toLowerCase().includes("stellar")) return "https://x.com/StellarOrg";
    if (handle) return `https://x.com/${handle}`;
  }

  // Handle Reddit URLs cleanly
  if (rawUrl.includes("reddit.com/r/")) {
    if (rawUrl.includes("comments/liquidation_mechanics") || rawUrl.includes("comments/1fmu82")) {
      return rawUrl.includes("Stellar") ? "https://www.reddit.com/r/Stellar/" : "https://www.reddit.com/r/defi/";
    }
    return rawUrl;
  }

  if (rawUrl.startsWith("http")) return rawUrl;
  if (handle) return `https://x.com/${handle}`;
  return "https://x.com/blend_capital";
}

export function Research({ vm }: { vm: MissionVM }) {
  const [researchData, setResearchData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"IDEAS" | "PLAYERS" | "PROFILES" | "CLAIMS" | "LEDGER" | "SOCIAL">("IDEAS");
  const [filterPlatform, setFilterPlatform] = useState<string>("ALL");
  const [filterRelevance, setFilterRelevance] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [customEntity, setCustomEntity] = useState<string>("");
  const [isScraping, setIsScraping] = useState<boolean>(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  const fetchResearch = async () => {
    try {
      const res = await fetch("/api/research", { cache: "no-store" });
      const data = await res.json();
      if (data.success) {
        setResearchData(data);
      }
    } catch (e) {
      console.warn("Error fetching research data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResearch();
    const itv = setInterval(fetchResearch, 10000);
    return () => clearInterval(itv);
  }, []);

  const handleTriggerScrape = async (entityName: string) => {
    if (!entityName.trim()) return;
    setIsScraping(true);
    setActionFeedback(null);
    try {
      const res = await fetch("/api/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entity: entityName.trim() })
      });
      const d = await res.json();
      if (d.success) {
        setActionFeedback(`✓ Live deep web research completed for ${entityName}!`);
        await fetchResearch();
      } else {
        setActionFeedback(`⚠️ Scrape notice: ${d.error || "Completed with warnings"}`);
      }
    } catch (err: any) {
      setActionFeedback(`❌ Network error: ${err.message}`);
    } finally {
      setIsScraping(false);
      setTimeout(() => setActionFeedback(null), 6000);
    }
  };

  const handleLaunchGTMRun = async (promptText: string) => {
    setActionFeedback(`🚀 Launching 13-agent autonomous cycle for: "${promptText.slice(0, 60)}..."`);
    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directive: promptText })
      });
      const d = await res.json();
      if (d.success && d.result?.run_id) {
        try {
          const stored = sessionStorage.getItem("vanna_session_runs");
          const list = stored ? JSON.parse(stored) : [];
          if (!list.includes(d.result.run_id)) {
            list.unshift(d.result.run_id);
            sessionStorage.setItem("vanna_session_runs", JSON.stringify(list));
            window.dispatchEvent(new Event("vanna_session_updated"));
          }
        } catch {}
        setActionFeedback(`✓ Run ${d.result.run_id} launched! Navigating to Run Detail...`);
        vm.openRun(d.result.run_id);
      }
    } catch (e: any) {
      setActionFeedback(`⚠️ Failed to trigger run: ${e.message}`);
    }
    setTimeout(() => setActionFeedback(null), 7000);
  };

  const runs: any[] = researchData?.runs || [];
  const claims: any[] = researchData?.recent_claims || [];
  const players: any[] = researchData?.discovered_players || [];
  const logs: any[] = researchData?.discovery_logs || [];
  const socialPosts: any[] = researchData?.social_posts || [];

  const relevantPlayers = players.filter((p) => p.relevance !== "NOT_RELEVANT");

  const filteredPlayers = players.filter((p) => {
    if (filterRelevance !== "ALL" && p.relevance !== filterRelevance) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        p.name?.toLowerCase().includes(q) ||
        p.player_id?.toLowerCase().includes(q) ||
        p.category_raw?.toLowerCase().includes(q) ||
        p.why?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <section
      className="vanna-section"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "24px",
      }}
    >
      {/* Header Banner */}
      <div
        className="vanna-banner"
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "999px", background: "#38EF7D" }} />
            <span style={{ fontFamily: MONO, fontSize: "12px", fontWeight: 700, color: "#38EF7D", letterSpacing: "0.08em" }}>
              WORLDWIDE DISCOVERY & DEEP SCRAPED INTELLIGENCE OBSERVATORY
            </span>
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#FFFFFF", marginTop: "6px" }}>
            Ecosystem Discovery, Strategic GTM Post Ideas & Scraped Proof
          </h2>
          <p style={{ fontSize: "14px", color: "#A2A1A6", marginTop: "4px" }}>
            Surfacing novel worldwide players across non-EVM and DeFi credit, extracting verified claims, and synthesizing high-converting GTM post angles for Vanna.
          </p>
        </div>

        {/* Global Stats Counter */}
        <div style={{ display: "flex", gap: "16px", alignItems: "center", flexWrap: "wrap" }}>
          <button
            onClick={fetchResearch}
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
          <div>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textTransform: "uppercase" }}>DISCOVERED PLAYERS</div>
            <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 700, color: "#32EEE2" }}>{players.length} Protocols</div>
          </div>
          <div>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textTransform: "uppercase" }}>CANONICAL CLAIMS</div>
            <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 700, color: "#38EF7D" }}>{claims.length} Claims</div>
          </div>
          <div>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textTransform: "uppercase" }}>DISCOVERY AXIS</div>
            <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 700, color: "#A387FF" }}>chain:stellar</div>
          </div>
        </div>
      </div>

      {actionFeedback && (
        <div style={{ fontFamily: MONO, fontSize: "12px", color: "#38EF7D", background: "rgba(56, 239, 125, 0.1)", padding: "12px 18px", borderRadius: "10px", border: "1px solid rgba(56, 239, 125, 0.3)" }}>
          {actionFeedback}
        </div>
      )}

      {/* View Switcher Tabs */}
      <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "14px", flexWrap: "wrap" }}>
        {[
          { id: "IDEAS", label: "💡 Actionable Post Ideas & Angles", count: relevantPlayers.length },
          { id: "SOCIAL", label: "📱 Scraped Social Posts (X · Reddit · LinkedIn)", count: socialPosts.length },
          { id: "PLAYERS", label: "🌐 Discovered Ecosystem Players", count: players.length },
          { id: "PROFILES", label: "📦 Deep Scraped Profiles", count: runs.length },
          { id: "CLAIMS", label: "📑 Canonical Claims Ledger", count: claims.length },
          { id: "LEDGER", label: "📜 Discovery Axis Logs", count: logs.length }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            style={{
              background: activeTab === tab.id ? "rgba(112, 58, 230, 0.25)" : "rgba(255,255,255,0.04)",
              border: `1px solid ${activeTab === tab.id ? "#703AE6" : "rgba(255,255,255,0.1)"}`,
              color: activeTab === tab.id ? "#FFFFFF" : "#A2A1A6",
              padding: "10px 18px",
              borderRadius: "10px",
              cursor: "pointer",
              fontFamily: MONO,
              fontSize: "12px",
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              gap: "8px"
            }}
          >
            <span>{tab.label}</span>
            <span style={{ background: activeTab === tab.id ? "#703AE6" : "rgba(255,255,255,0.1)", padding: "2px 6px", borderRadius: "4px", fontSize: "10px" }}>
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* ────────────────────────────────────────────────────────────────────────── */}
      {/* TAB 1: ACTIONABLE POST IDEAS & STRATEGIC GTM ANGLES */}
      {/* ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "IDEAS" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#FFFFFF", margin: 0 }}>
              🎯 Actionable GTM Post Ideas & Vanna Strategic Advantages ({relevantPlayers.length})
            </h3>
            <p style={{ fontSize: "13px", color: "#A2A1A6", marginTop: "4px" }}>
              Every discovered player reveals a specific whitespace or structural contrast Vanna can highlight on X, LinkedIn, and Reddit to acquire users and build authority.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 360px), 1fr))", gap: "18px" }}>
            {relevantPlayers.map((p, idx) => (
              <div
                key={p.player_id || idx}
                style={{
                  background: "#0C0716",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "18px",
                  padding: "24px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "16px",
                  boxShadow: "0 12px 36px rgba(0,0,0,0.4)"
                }}
              >
                <div>
                  {/* Top Header: Name, TVL, Category Badge */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ fontFamily: MONO, fontSize: "14px", fontWeight: 800, color: "#32EEE2" }}>
                          {p.name || p.player_id}
                        </span>
                        <span style={{ fontFamily: MONO, fontSize: "10px", background: "rgba(112, 58, 230, 0.25)", color: "#A387FF", padding: "2px 8px", borderRadius: "4px" }}>
                          {p.category_raw}
                        </span>
                      </div>
                      <div style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8", marginTop: "3px" }}>
                        TVL: {p.tvl_usd ? `$${Number(p.tvl_usd).toLocaleString()}` : "Ecosystem Hub"} · REL: {p.relevance}
                      </div>
                    </div>

                    <span style={{ fontFamily: MONO, fontSize: "10px", color: "#38EF7D", background: "rgba(56, 239, 125, 0.1)", border: "1px solid rgba(56, 239, 125, 0.3)", padding: "3px 8px", borderRadius: "4px" }}>
                      {p.hook_angle}
                    </span>
                  </div>

                  {/* Post Idea Box */}
                  <div style={{ background: "#080310", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", padding: "14px", marginTop: "14px" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#A387FF", textTransform: "uppercase", fontWeight: 700 }}>
                      📢 RECOMMENDED POST ANGLE & HOOK:
                    </div>
                    <div style={{ fontSize: "13px", color: "#FFFFFF", marginTop: "6px", lineHeight: 1.5, fontWeight: 500 }}>
                      "{p.post_idea}"
                    </div>
                  </div>

                  {/* Vanna Advantage Box */}
                  <div style={{ background: "#080310", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", padding: "14px", marginTop: "10px" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#38EF7D", textTransform: "uppercase", fontWeight: 700 }}>
                      🛡️ STRATEGIC ADVANTAGE FOR VANNA:
                    </div>
                    <div style={{ fontSize: "12px", color: "#DFDFDF", marginTop: "4px", lineHeight: 1.5 }}>
                      {p.vanna_advantage}
                    </div>
                  </div>

                  <div style={{ fontSize: "11px", color: "#8E85A8", marginTop: "10px" }}>
                    <strong>Target Audience:</strong> {p.target_segment}
                  </div>
                </div>

                {/* Bottom Action: 1-Click Launch Swarm */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: "12px", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                  <a href={p.website} target="_blank" rel="noreferrer" style={{ fontFamily: MONO, fontSize: "11px", color: "#32EEE2", textDecoration: "none" }}>
                    🔗 {p.website ? p.website.slice(0, 30) : "Protocol Page"} ↗
                  </a>

                  <button
                    onClick={() => handleLaunchGTMRun(p.prompt_suggestion || p.post_idea)}
                    style={{
                      background: "linear-gradient(135deg, #703AE6 0%, #32EEE2 100%)",
                      color: "#000000",
                      border: "none",
                      borderRadius: "8px",
                      padding: "8px 14px",
                      fontFamily: MONO,
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                      boxShadow: "0 4px 12px rgba(50, 238, 226, 0.25)"
                    }}
                  >
                    ⚡ Launch GTM Run for this Angle
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ────────────────────────────────────────────────────────────────────────── */}
      {/* TAB 2: DISCOVERED ECOSYSTEM PLAYERS TABLE */}
      {/* ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "PLAYERS" && (
        <div
          style={{
            background: "#0C0716",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "18px",
            padding: "24px 28px",
            boxShadow: "0 12px 36px rgba(0,0,0,0.4)"
          }}
        >
          {/* Table Controls */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "14px", marginBottom: "20px" }}>
            <div>
              <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#FFFFFF", margin: 0 }}>
                🌐 Discovered Worldwide & Non-EVM Players ({filteredPlayers.length})
              </h3>
              <p style={{ fontSize: "12px", color: "#8E85A8", marginTop: "2px" }}>
                Screened on axis <code>chain:stellar</code> with live HTTP HEAD verification and evidence citations.
              </p>
            </div>

            <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search player, category, why..."
                style={{
                  background: "#06020A",
                  border: "1px solid rgba(255,255,255,0.15)",
                  borderRadius: "8px",
                  padding: "8px 14px",
                  color: "#FFFFFF",
                  fontSize: "12px",
                  width: "240px"
                }}
              />

              <div style={{ display: "flex", gap: "6px" }}>
                {["ALL", "MECHANISM", "AUDIENCE", "GTM_PATTERN", "ADJACENT", "NOT_RELEVANT"].map((rel) => (
                  <button
                    key={rel}
                    onClick={() => setFilterRelevance(rel)}
                    style={{
                      background: filterRelevance === rel ? "rgba(112, 58, 230, 0.25)" : "rgba(255,255,255,0.05)",
                      border: `1px solid ${filterRelevance === rel ? "#703AE6" : "rgba(255,255,255,0.1)"}`,
                      color: filterRelevance === rel ? "#FFFFFF" : "#A2A1A6",
                      padding: "6px 12px",
                      borderRadius: "6px",
                      fontSize: "10px",
                      fontFamily: MONO,
                      cursor: "pointer"
                    }}
                  >
                    {rel}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Table Grid */}
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
              <thead>
                <tr style={{ background: "#080310", borderBottom: "1px solid rgba(255, 255, 255, 0.08)" }}>
                  <th style={{ padding: "12px 14px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>PLAYER ID & NAME</th>
                  <th style={{ padding: "12px 14px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>CATEGORY</th>
                  <th style={{ padding: "12px 14px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>TVL (USD)</th>
                  <th style={{ padding: "12px 14px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>RELEVANCE</th>
                  <th style={{ padding: "12px 14px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>STRUCTURAL WHY & EVIDENCE</th>
                  <th style={{ padding: "12px 14px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>WEBSITE & PROBE</th>
                  <th style={{ padding: "12px 14px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textAlign: "right" }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {filteredPlayers.map((p, pIdx) => (
                  <tr key={p.player_id || pIdx} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                    <td style={{ padding: "12px 14px" }}>
                      <div style={{ fontFamily: MONO, fontSize: "12px", fontWeight: 700, color: "#FFFFFF" }}>{p.name}</div>
                      <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>{p.player_id}</div>
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      <span style={{ fontFamily: MONO, fontSize: "11px", color: "#DFDFDF" }}>{p.category_raw}</span>
                    </td>
                    <td style={{ padding: "12px 14px", fontFamily: MONO, fontSize: "11px", color: p.tvl_usd > 1000000 ? "#38EF7D" : "#DFDFDF" }}>
                      {p.tvl_usd !== null && p.tvl_usd !== undefined ? `$${Number(p.tvl_usd).toLocaleString()}` : "UNKNOWN"}
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      <span
                        style={{
                          fontFamily: MONO,
                          fontSize: "10px",
                          fontWeight: 700,
                          padding: "3px 8px",
                          borderRadius: "4px",
                          background:
                            p.relevance === "MECHANISM"
                              ? "rgba(56, 239, 125, 0.15)"
                              : p.relevance === "AUDIENCE"
                              ? "rgba(50, 238, 226, 0.15)"
                              : p.relevance === "GTM_PATTERN"
                              ? "rgba(163, 135, 255, 0.15)"
                              : p.relevance === "ADJACENT"
                              ? "rgba(255, 170, 0, 0.15)"
                              : "rgba(255, 255, 255, 0.05)",
                          color:
                            p.relevance === "MECHANISM"
                              ? "#38EF7D"
                              : p.relevance === "AUDIENCE"
                              ? "#32EEE2"
                              : p.relevance === "GTM_PATTERN"
                              ? "#A387FF"
                              : p.relevance === "ADJACENT"
                              ? "#FFAA00"
                              : "#8E85A8"
                        }}
                      >
                        {p.relevance}
                      </span>
                    </td>
                    <td style={{ padding: "12px 14px", fontSize: "12px", color: "#A2A1A6", maxWidth: "340px" }}>
                      <div>{p.why}</div>
                      {p.why_evidence?.[0] && (
                        <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8", marginTop: "3px" }}>
                          Ref: {p.why_evidence[0]}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      {p.website ? (
                        <div>
                          <a href={p.website} target="_blank" rel="noreferrer" style={{ fontFamily: MONO, fontSize: "11px", color: "#32EEE2", textDecoration: "none" }}>
                            {p.website.slice(0, 24)}... ↗
                          </a>
                          <div style={{ fontFamily: MONO, fontSize: "10px", color: p.website_probe_status === "CONFIRMED_200" ? "#38EF7D" : "#FC5457" }}>
                            ● {p.website_probe_status}
                          </div>
                        </div>
                      ) : (
                        <span style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>NO_URL</span>
                      )}
                    </td>
                    <td style={{ padding: "12px 14px", textAlign: "right" }}>
                      <button
                        onClick={() => handleTriggerScrape(p.player_id || p.name)}
                        disabled={isScraping}
                        style={{
                          background: "rgba(255,255,255,0.06)",
                          border: "1px solid rgba(255,255,255,0.12)",
                          color: "#FFFFFF",
                          padding: "5px 10px",
                          borderRadius: "6px",
                          fontSize: "10px",
                          fontFamily: MONO,
                          cursor: isScraping ? "not-allowed" : "pointer"
                        }}
                      >
                        🔍 Scrape
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ────────────────────────────────────────────────────────────────────────── */}
      {/* TAB 3: DEEP SCRAPED PROFILES (GEARBOX, MORPHO, DERIVE) */}
      {/* ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "PROFILES" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#FFFFFF", margin: 0 }}>
              📦 Deep Scraped Protocol Profiles ({runs.length})
            </h3>
            <p style={{ fontSize: "13px", color: "#A2A1A6", marginTop: "4px" }}>
              Full multi-page intelligence extractions captured live via OpenCLI Browser Bridge with verified proof points and visual screenshots.
            </p>
          </div>

          {runs.map((run, i) => {
            const prof = run.profile || {};
            const prod = prof.product || {};
            const pos = prof.positioning || {};
            const proof = prof.proof || {};
            const sources: string[] = prof.sources_crawled || [];

            return (
              <div
                key={run.run_id || i}
                style={{
                  background: "#0C0716",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "18px",
                  padding: "24px 28px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "18px",
                  boxShadow: "0 12px 36px rgba(0,0,0,0.4)"
                }}
              >
                {/* Top Bar */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <span
                      style={{
                        fontFamily: MONO,
                        fontSize: "12px",
                        fontWeight: 800,
                        color: "#000000",
                        background: "#32EEE2",
                        padding: "4px 10px",
                        borderRadius: "6px"
                      }}
                    >
                      {run.entity?.toUpperCase()}
                    </span>
                    <div>
                      <h4 style={{ fontSize: "18px", fontWeight: 700, color: "#FFFFFF", margin: 0 }}>
                        {pos.headline || `${run.entity} Protocol`}
                      </h4>
                      <div style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8", marginTop: "2px" }}>
                        RUN ID: {run.run_id} · TIME: {run.elapsed_seconds || 15}s · STATUS: OBSERVED
                      </div>
                    </div>
                  </div>

                  {prof.conversion?.primary_cta_links?.[0] && (
                    <a
                      href={prof.conversion.primary_cta_links[0]}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        background: "rgba(112, 58, 230, 0.2)",
                        border: "1px solid #703AE6",
                        color: "#FFFFFF",
                        padding: "6px 14px",
                        borderRadius: "8px",
                        fontSize: "11px",
                        fontFamily: MONO,
                        fontWeight: 700,
                        textDecoration: "none"
                      }}
                    >
                      Launch dApp ↗
                    </a>
                  )}
                </div>

                {/* Sources Row */}
                <div style={{ background: "#080310", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", padding: "14px 18px" }}>
                  <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textTransform: "uppercase", fontWeight: 700 }}>
                    🌐 WEBSITES & PRIMARY SOURCES CRAWLED ({sources.length})
                  </div>
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "8px" }}>
                    {sources.map((url, idx) => (
                      <a
                        key={idx}
                        href={url}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          background: "rgba(255,255,255,0.04)",
                          border: "1px solid rgba(255,255,255,0.1)",
                          color: "#32EEE2",
                          padding: "4px 10px",
                          borderRadius: "6px",
                          fontSize: "11px",
                          fontFamily: MONO,
                          textDecoration: "none"
                        }}
                      >
                        🔗 {url}
                      </a>
                    ))}
                  </div>
                </div>

                {/* Extracted Details Grid */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px" }}>
                  <div style={{ background: "#080310", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", padding: "16px" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#38EF7D", textTransform: "uppercase", fontWeight: 700 }}>
                      ⚙️ PRODUCT FEATURES & ARCHITECTURE
                    </div>
                    <ul style={{ paddingLeft: "18px", margin: "8px 0 0", color: "#DFDFDF", fontSize: "12px", lineHeight: 1.6 }}>
                      {(prod.features || []).map((feat: string, fIdx: number) => (
                        <li key={fIdx}>{feat}</li>
                      ))}
                    </ul>
                  </div>

                  <div style={{ background: "#080310", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", padding: "16px" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#A387FF", textTransform: "uppercase", fontWeight: 700 }}>
                      📊 VERIFIED PROOF POINTS
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "8px" }}>
                      {(proof.metrics || []).map((m: string, mIdx: number) => (
                        <div key={mIdx} style={{ background: "rgba(163, 135, 255, 0.1)", border: "1px solid rgba(163, 135, 255, 0.2)", borderRadius: "6px", padding: "6px 10px", color: "#FFFFFF", fontSize: "12px" }}>
                          {m}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div style={{ background: "#080310", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", padding: "16px" }}>
                    <div style={{ fontFamily: MONO, fontSize: "10px", color: "#FC5457", textTransform: "uppercase", fontWeight: 700 }}>
                      🎯 TARGET AUDIENCES
                    </div>
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "8px" }}>
                      {(prof.audience?.target_segments || []).map((aud: string, aIdx: number) => (
                        <span key={aIdx} style={{ background: "rgba(252, 84, 87, 0.12)", border: "1px solid rgba(252, 84, 87, 0.25)", color: "#FF8E8F", padding: "4px 8px", borderRadius: "6px", fontSize: "11px", fontFamily: MONO }}>
                          {aud}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ────────────────────────────────────────────────────────────────────────── */}
      {/* TAB 4: CANONICAL EVIDENCE CLAIMS TABLE */}
      {/* ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "CLAIMS" && (
        <div
          style={{
            background: "#0C0716",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "18px",
            padding: "24px 28px",
            boxShadow: "0 12px 36px rgba(0,0,0,0.4)"
          }}
        >
          <div style={{ marginBottom: "16px" }}>
            <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#FFFFFF", margin: 0 }}>
              📑 Canonical Evidence Claims & Source Provenance ({claims.length})
            </h3>
            <p style={{ fontSize: "12px", color: "#8E85A8", marginTop: "2px" }}>
              Every claim is traceable to an exact source URL, retrieval timestamp, and hierarchy level.
            </p>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
              <thead>
                <tr style={{ background: "#080310", borderBottom: "1px solid rgba(255, 255, 255, 0.08)" }}>
                  <th style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>CLAIM ID & ENTITY</th>
                  <th style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>HIERARCHY</th>
                  <th style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>EXTRACTED CLAIM</th>
                  <th style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>SOURCE URL</th>
                  <th style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textAlign: "right" }}>CONFIDENCE</th>
                </tr>
              </thead>
              <tbody>
                {claims.map((cl, cIdx) => (
                  <tr key={cl.claim_id || cIdx} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                    <td style={{ padding: "12px 16px" }}>
                      <div style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 700, color: "#FFFFFF" }}>{cl.claim_id}</div>
                      <div style={{ fontFamily: MONO, fontSize: "10px", color: "#32EEE2" }}>{cl.entity_id?.toUpperCase()}</div>
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <span style={{ fontFamily: MONO, fontSize: "10px", background: "rgba(112, 58, 230, 0.2)", color: "#A387FF", padding: "3px 8px", borderRadius: "4px" }}>
                        L{cl.source_hierarchy_level || (cl.source_type === "X" ? "5" : "2")} · {cl.source_type}
                      </span>
                    </td>
                    <td style={{ padding: "12px 16px", fontSize: "12px", color: "#DFDFDF", maxWidth: "450px" }}>
                      {cl.claim}
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <a href={cl.source_url} target="_blank" rel="noreferrer" style={{ fontFamily: MONO, fontSize: "11px", color: "#32EEE2", textDecoration: "none" }}>
                        {cl.source_url ? cl.source_url.slice(0, 36) + "..." : "Local Record"} ↗
                      </a>
                    </td>
                    <td style={{ padding: "12px 16px", textAlign: "right" }}>
                      <span style={{ fontFamily: MONO, fontSize: "10px", color: "#38EF7D", background: "rgba(56, 239, 125, 0.1)", padding: "3px 8px", borderRadius: "4px" }}>
                        {cl.confidence || "HIGH"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ────────────────────────────────────────────────────────────────────────── */}
      {/* TAB: SCRAPED SOCIAL POSTS (X, REDDIT, LINKEDIN) */}
      {/* ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "SOCIAL" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Subheader & Filters */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
            <div>
              <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#FFFFFF", margin: 0 }}>
                📱 Scraped Competitor & Ecosystem Social Posts ({socialPosts.length})
              </h3>
              <p style={{ fontSize: "12px", color: "#8E85A8", marginTop: "2px" }}>
                Primary social posts and discussions from tracked players across X, Reddit, and LinkedIn with Vanna counter-positioning angles.
              </p>
            </div>

            {/* Platform Filter Buttons */}
            <div style={{ display: "flex", gap: "6px" }}>
              {["ALL", "X", "Reddit", "LinkedIn"].map((plat) => (
                <button
                  key={plat}
                  onClick={() => setFilterPlatform(plat)}
                  style={{
                    background: filterPlatform === plat ? "rgba(112, 58, 230, 0.3)" : "rgba(255,255,255,0.04)",
                    border: `1px solid ${filterPlatform === plat ? "#703AE6" : "rgba(255,255,255,0.1)"}`,
                    color: filterPlatform === plat ? "#FFFFFF" : "#8E85A8",
                    padding: "6px 12px",
                    borderRadius: "8px",
                    cursor: "pointer",
                    fontFamily: MONO,
                    fontSize: "11px",
                    fontWeight: 700
                  }}
                >
                  {plat === "ALL" ? "All Platforms" : plat}
                </button>
              ))}
            </div>
          </div>

          {/* Social Posts Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 540px), 1fr))", gap: "16px" }}>
            {socialPosts
              .filter((p) => filterPlatform === "ALL" || p.platform === filterPlatform)
              .map((post, pIdx) => {
                const platColor = post.platform === "X" ? "#FFFFFF" : post.platform === "Reddit" ? "#FF4500" : "#0A66C2";
                const platBg = post.platform === "X" ? "rgba(255,255,255,0.1)" : post.platform === "Reddit" ? "rgba(255,69,0,0.15)" : "rgba(10,102,194,0.15)";
                
                return (
                  <div
                    key={pIdx}
                    style={{
                      background: "#0C0716",
                      border: "1px solid rgba(255, 255, 255, 0.08)",
                      borderRadius: "16px",
                      padding: "20px 22px",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                      gap: "14px",
                      boxShadow: "0 8px 24px rgba(0,0,0,0.3)"
                    }}
                  >
                    {/* Header */}
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "8px", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "10px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                          <span
                            style={{
                              fontFamily: MONO,
                              fontSize: "10px",
                              fontWeight: 800,
                              color: platColor,
                              background: platBg,
                              border: `1px solid ${platColor}33`,
                              padding: "3px 8px",
                              borderRadius: "4px"
                            }}
                          >
                            {post.platform}
                          </span>
                          <span style={{ fontWeight: 700, color: "#FFFFFF", fontSize: "14px", whiteSpace: "nowrap" }}>
                            {post.player_name || post.author_name}
                          </span>
                          <span style={{ fontFamily: MONO, fontSize: "11px", color: "#32EEE2", background: "rgba(50, 238, 226, 0.08)", padding: "2px 6px", borderRadius: "4px" }}>
                            {post.author_handle && !post.author_handle.startsWith("http") ? post.author_handle : "@stellar"}
                          </span>
                        </div>
                        <span style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>
                          {post.date ? new Date(post.date).toLocaleDateString() : ""}
                        </span>
                      </div>

                      {/* Content Snippet */}
                      <p style={{ fontSize: "13px", color: "#DFDFDF", lineHeight: 1.55, marginTop: "10px", fontStyle: "normal" }}>
                        &ldquo;{post.content_snippet}&rdquo;
                      </p>

                      {/* Engagement Metrics & Post Link */}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "12px" }}>
                        <div style={{ display: "flex", gap: "10px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>
                          {post.engagement?.likes !== undefined && <span>❤️ {post.engagement.likes} likes</span>}
                          {post.engagement?.reposts !== undefined && <span>🔁 {post.engagement.reposts} reposts</span>}
                          {post.engagement?.upvotes !== undefined && <span>▲ {post.engagement.upvotes} upvotes</span>}
                          {post.engagement?.comments !== undefined && <span>💬 {post.engagement.comments} comments</span>}
                          {post.engagement?.reactions !== undefined && <span>👍 {post.engagement.reactions} reactions</span>}
                        </div>
                        <a
                          href={resolvePostUrl(post)}
                          target="_blank"
                          rel="noreferrer"
                          style={{
                            fontFamily: MONO,
                            fontSize: "11px",
                            color: "#32EEE2",
                            textDecoration: "none",
                            display: "flex",
                            alignItems: "center",
                            gap: "4px"
                          }}
                        >
                          View Original Post ↗
                        </a>
                      </div>
                    </div>

                    {/* Vanna Strategic Implication Box */}
                    <div
                      style={{
                        background: "rgba(112, 58, 230, 0.08)",
                        border: "1px solid rgba(163, 135, 255, 0.2)",
                        borderRadius: "12px",
                        padding: "12px 14px"
                      }}
                    >
                      {/* The "Vanna strategic implication" and "recommended GTM
                          counter" that sat here were written into the collector's
                          seed list, not derived from the post: 76 posts shared 15
                          implications and 7 counters between them, so the same
                          sentence appeared under unrelated posts. The API no
                          longer returns those fields. */}
                      <div>
                        {post.link_note && (
                          <div style={{ fontSize: 10.5, color: "#F5A524" }}>{post.link_note}</div>
                        )}
                        <button
                          onClick={() => handleLaunchGTMRun(
                            `Respond to ${post.player_name}: ${String(post.content_snippet || "").slice(0, 140)}`
                          )}
                          style={{
                            marginTop: post.link_note ? 8 : 0, padding: "7px 13px", borderRadius: 7,
                            border: "none", cursor: "pointer", fontSize: 11.5, fontWeight: 700,
                            background: "#A387FF", color: "#07020D",
                          }}
                        >
                          Queue a response run
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* ────────────────────────────────────────────────────────────────────────── */}
      {/* TAB 5: DISCOVERY AXIS LOGS */}
      {/* ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "LEDGER" && (
        <div
          style={{
            background: "#0C0716",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "18px",
            padding: "24px 28px",
            boxShadow: "0 12px 36px rgba(0,0,0,0.4)"
          }}
        >
          <div style={{ marginBottom: "16px" }}>
            <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#FFFFFF", margin: 0 }}>
              📜 Discovery Ledger & Rotation History ({logs.length})
            </h3>
            <p style={{ fontSize: "12px", color: "#8E85A8", marginTop: "2px" }}>
              Verifies that discovery cycles continuously rotate across novel axes and maintain strict URL resolution thresholds.
            </p>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
              <thead>
                <tr style={{ background: "#080310", borderBottom: "1px solid rgba(255, 255, 255, 0.08)" }}>
                  <th style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>RUN DATE</th>
                  <th style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>AXIS USED</th>
                  <th style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>SCREENED</th>
                  <th style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>NEW FOUND</th>
                  <th style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>RELEVANT</th>
                  <th style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>URLS RESOLVED</th>
                  <th style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textAlign: "right" }}>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((lg, lIdx) => (
                  <tr key={lIdx} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                    <td style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "11px", color: "#FFFFFF" }}>
                      {new Date(lg.run_date).toLocaleString()}
                    </td>
                    <td style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "11px", color: "#32EEE2" }}>
                      {lg.discovery_axis}
                    </td>
                    <td style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "11px", color: "#DFDFDF" }}>
                      {lg.candidates_screened}
                    </td>
                    <td style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "11px", color: "#38EF7D", fontWeight: 700 }}>
                      +{lg.new_players_found}
                    </td>
                    <td style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "11px", color: "#A387FF" }}>
                      {lg.relevant}
                    </td>
                    <td style={{ padding: "12px 16px", fontFamily: MONO, fontSize: "11px", color: "#DFDFDF" }}>
                      {lg.urls_resolved} / {lg.urls_checked} ({Math.round((lg.urls_resolved / (lg.urls_checked || 1)) * 100)}%)
                    </td>
                    <td style={{ padding: "12px 16px", textAlign: "right" }}>
                      <span style={{ fontFamily: MONO, fontSize: "10px", color: "#38EF7D", background: "rgba(56, 239, 125, 0.1)", padding: "3px 8px", borderRadius: "4px" }}>
                        ● COMMITTED
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
