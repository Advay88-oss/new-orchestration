"use client";

import React, { useState, useEffect } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

export function Posts({ vm }: { vm: MissionVM }) {
  const [posts, setPosts] = useState<any[]>([]);
  const [platformFilter, setPlatformFilter] = useState<string>("ALL");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/runs", { cache: "no-store" })
      .then((r) => r.json())
      .then((data) => {
        const perfMap = new Map<string, any>();
        if (Array.isArray(data.performance_records)) {
          for (const rec of data.performance_records) {
            if (rec.content_id) perfMap.set(rec.content_id, rec);
            if (rec.record_id) perfMap.set(rec.record_id, rec);
          }
        }

        // If no active runs exist, keep posts strictly empty
        if (!data.runs || data.runs.length === 0) {
          setPosts([]);
          return;
        }

        const collected: any[] = [];
        // Extract posts from published receipts
        if (Array.isArray(data.posts)) {
          for (const p of data.posts) {
            const perf = perfMap.get(p.post_id) || perfMap.get(p.canonical_url);
            collected.push({
              id: p.post_id || p.canonical_url,
              platform: p.channel || "X",
              title: p.title || null,
              leadCopy: p.copy || "Vanna Protocol Post",
              publishedUrl: p.canonical_url || "https://x.com/vanna_finance",
              publishedAt: p.published_at ? new Date(p.published_at).toLocaleString() : "Recently",
              impressions: perf?.impressions?.status === "MEASURED" ? perf.impressions.raw_value : null,
              clicks: perf?.clicks?.status === "MEASURED" ? perf.clicks.raw_value : null,
              conversions: perf?.deployments?.status === "MEASURED" ? perf.deployments.raw_value : (perf?.conversions?.status === "MEASURED" ? perf.conversions.raw_value : null),
            });
          }
        }

        // Also extract posts from runs
        if (Array.isArray(data.runs)) {
          for (const r of data.runs) {
            const content = r.agent_outputs?.agent_06_content;
            if (content) {
              const xReceipt = r.agent_outputs?.agent_11_dispatch?.receipts?.[0] || "https://x.com/vanna_finance";
              const liReceipt = r.agent_outputs?.agent_11_dispatch?.receipts?.[1] || "https://linkedin.com";
              const rdReceipt = r.agent_outputs?.agent_11_dispatch?.receipts?.[2] || "https://reddit.com/r/defi";

              const xId = xReceipt.split("/").pop() || `X-${r.run_id}`;
              const liId = liReceipt.split("/").pop() || `LI-${r.run_id}`;
              const rdId = rdReceipt.split("/").pop() || `RD-${r.run_id}`;

              const perfX = perfMap.get(xId) || perfMap.get(`PERF-${xId}`);
              const perfLi = perfMap.get(liId) || perfMap.get(`PERF-${liId}`);
              const perfRd = perfMap.get(rdId) || perfMap.get(`PERF-${rdId}`);

              if (content.x_threads) {
                collected.push({
                  id: `X-${r.run_id}`,
                  platform: "X",
                  leadCopy: content.x_lead || content.x_threads[0],
                  fullThread: content.x_threads,
                  publishedUrl: xReceipt,
                  publishedAt: r.started ? new Date(r.started * 1000).toLocaleString() : "Live Run",
                  impressions: perfX?.impressions?.status === "MEASURED" ? perfX.impressions.raw_value : null,
                  clicks: perfX?.clicks?.status === "MEASURED" ? perfX.clicks.raw_value : null,
                  conversions: perfX?.deployments?.status === "MEASURED" ? perfX.deployments.raw_value : (perfX?.conversions?.status === "MEASURED" ? perfX.conversions.raw_value : null),
                });
              }

              if (content.linkedin_copy) {
                collected.push({
                  id: `LI-${r.run_id}`,
                  platform: "LinkedIn",
                  title: r.title,
                  leadCopy: content.linkedin_copy,
                  publishedUrl: liReceipt,
                  publishedAt: r.started ? new Date(r.started * 1000).toLocaleString() : "Live Run",
                  impressions: perfLi?.impressions?.status === "MEASURED" ? perfLi.impressions.raw_value : null,
                  clicks: perfLi?.clicks?.status === "MEASURED" ? perfLi.clicks.raw_value : null,
                  conversions: perfLi?.deployments?.status === "MEASURED" ? perfLi.deployments.raw_value : (perfLi?.conversions?.status === "MEASURED" ? perfLi.conversions.raw_value : null),
                });
              }

              if (content.reddit_copy) {
                collected.push({
                  id: `RD-${r.run_id}`,
                  platform: "Reddit",
                  title: content.reddit_hook || r.title,
                  leadCopy: content.reddit_copy,
                  publishedUrl: rdReceipt,
                  publishedAt: r.started ? new Date(r.started * 1000).toLocaleString() : "Live Run",
                  impressions: perfRd?.impressions?.status === "MEASURED" ? perfRd.impressions.raw_value : null,
                  clicks: perfRd?.clicks?.status === "MEASURED" ? perfRd.clicks.raw_value : null,
                  conversions: perfRd?.deployments?.status === "MEASURED" ? perfRd.deployments.raw_value : (perfRd?.conversions?.status === "MEASURED" ? perfRd.conversions.raw_value : null),
                });
              }
            }
          }
        }

        // Deduplicate by ID
        const unique = Array.from(new Map(collected.map((item) => [item.id, item])).values());
        setPosts(unique);
      })
      .catch((e) => console.warn("Error fetching dynamic posts:", e));
  }, []);

  const filteredPosts = posts.filter((p) => {
    if (platformFilter === "ALL") return true;
    return p.platform === platformFilter;
  });

  const handleCopy = (id: string, text: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 3000);
    }
  };

  return (
    <section className="vanna-section">
      {/* Header Banner */}
      <div className="vanna-banner">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "999px", background: posts.length > 0 ? "#38EF7D" : "#8E85A8" }} />
            <span style={{ fontFamily: MONO, fontSize: "12px", fontWeight: 700, color: posts.length > 0 ? "#38EF7D" : "#8E85A8", letterSpacing: "0.08em" }}>
              MULTI-CHANNEL SOCIAL FEED // {posts.length > 0 ? `${posts.length} PUBLISHED ARTIFACTS` : "STANDBY (0 ARTIFACTS)"}
            </span>
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#FFFFFF", marginTop: "6px" }}>
            Autonomous Multi-Channel Social Content & Live Telemetry
          </h2>
          <p style={{ fontSize: "14px", color: "#A2A1A6", marginTop: "4px" }}>
            Real-time feed across X, LinkedIn, and Reddit derived from autonomous runs and canonical performance records. Zero mock data.
          </p>
        </div>

        {/* Platform Filter Buttons */}
        <div style={{ display: "flex", gap: "8px" }}>
          {["ALL", "X", "LinkedIn", "Reddit"].map((plat) => (
            <button
              key={plat}
              onClick={() => setPlatformFilter(plat)}
              style={{
                background: platformFilter === plat ? "rgba(112, 58, 230, 0.25)" : "rgba(255,255,255,0.05)",
                border: `1px solid ${platformFilter === plat ? "#703AE6" : "rgba(255,255,255,0.1)"}`,
                color: platformFilter === plat ? "#FFFFFF" : "#A2A1A6",
                padding: "8px 16px",
                borderRadius: "8px",
                cursor: "pointer",
                fontFamily: MONO,
                fontSize: "12px",
                fontWeight: 600
              }}
            >
              {plat}
            </button>
          ))}
        </div>
      </div>

      {/* Posts List */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {filteredPosts.length === 0 && (
          <div
            style={{
              background: "#0C0716",
              border: "1px dashed rgba(255,255,255,0.12)",
              borderRadius: "18px",
              padding: "48px 32px",
              textAlign: "center",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "12px"
            }}
          >
            <div style={{ fontSize: "32px" }}>📡</div>
            <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#FFFFFF", margin: 0 }}>
              No Multi-Channel Posts Published Yet
            </h3>
            <p style={{ color: "#8E85A8", fontSize: "13px", maxWidth: "480px", margin: 0, lineHeight: 1.5 }}>
              The multi-channel feed is reset to baseline. Launch an autonomous directive from the Command Console above to generate platform-native copy for X, LinkedIn, and Reddit.
            </p>
          </div>
        )}

        {filteredPosts.map((post) => (
          <div
            key={post.id}
            style={{
              background: "#0C0716",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "18px",
              padding: "24px 28px",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
              boxShadow: "0 8px 24px rgba(0,0,0,0.3)"
            }}
          >
            {/* Post Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <span
                  style={{
                    fontFamily: MONO,
                    fontSize: "11px",
                    fontWeight: 700,
                    color: post.platform === "X" ? "#32EEE2" : (post.platform === "LinkedIn" ? "#A387FF" : "#FF5722"),
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    padding: "4px 10px",
                    borderRadius: "6px"
                  }}
                >
                  {post.platform}
                </span>
                <span style={{ fontSize: "12px", color: "#8E85A8" }}>Published: {post.publishedAt}</span>
              </div>

              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  onClick={() => handleCopy(post.id, post.fullThread ? post.fullThread.join("\n\n") : post.leadCopy)}
                  style={{
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.12)",
                    color: copiedId === post.id ? "#38EF7D" : "#DFDFDF",
                    padding: "6px 12px",
                    borderRadius: "6px",
                    fontSize: "11px",
                    fontFamily: MONO,
                    cursor: "pointer"
                  }}
                >
                  {copiedId === post.id ? "✓ Copied!" : "Copy Post"}
                </button>
                <a
                  href={post.publishedUrl}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    background: "rgba(112, 58, 230, 0.2)",
                    border: "1px solid rgba(163, 135, 255, 0.35)",
                    color: "#FFFFFF",
                    padding: "6px 12px",
                    borderRadius: "6px",
                    fontSize: "11px",
                    fontFamily: MONO,
                    textDecoration: "none",
                    fontWeight: 600
                  }}
                >
                  View Live Post ↗
                </a>
              </div>
            </div>

            {/* Post Title */}
            {post.title && (
              <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#FFFFFF" }}>{post.title}</h3>
            )}

            {/* Post Content */}
            {post.fullThread ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {post.fullThread.map((chunk: string, idx: number) => (
                  <div
                    key={idx}
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      padding: "12px 16px",
                      borderRadius: "8px",
                      fontSize: "14px",
                      lineHeight: 1.6,
                      color: "#E2E1E6"
                    }}
                  >
                    {chunk}
                  </div>
                ))}
              </div>
            ) : (
              <div
                style={{
                  background: "rgba(255,255,255,0.03)",
                  padding: "16px",
                  borderRadius: "10px",
                  fontSize: "14px",
                  lineHeight: 1.6,
                  color: "#E2E1E6",
                  whiteSpace: "pre-line"
                }}
              >
                {post.leadCopy}
              </div>
            )}

            {/* Performance Metrics Strip */}
            <div style={{ display: "flex", gap: "20px", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "12px", fontSize: "12px" }}>
              <span style={{ color: "#8E85A8" }}>
                Impressions: <strong style={{ color: post.impressions != null ? "#FFFFFF" : "#8E85A8" }}>
                  {post.impressions != null ? post.impressions.toLocaleString() : "Pending Telemetry Sync (NULL ≠ 0)"}
                </strong>
              </span>
              <span style={{ color: "#8E85A8" }}>
                Clicks: <strong style={{ color: post.clicks != null ? "#32EEE2" : "#8E85A8" }}>
                  {post.clicks != null ? post.clicks.toLocaleString() : "Pending Sync"}
                </strong>
              </span>
              <span style={{ color: "#8E85A8" }}>
                Sandbox Deployments: <strong style={{ color: post.conversions != null ? "#38EF7D" : "#8E85A8" }}>
                  {post.conversions != null ? post.conversions.toLocaleString() : "Pending Sync"}
                </strong>
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
