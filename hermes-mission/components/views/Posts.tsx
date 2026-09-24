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
              publishedUrl: p.canonical_url ?? null,
              dispatched: Boolean(p.canonical_url),
              publishedAt: p.published_at ? new Date(p.published_at).toLocaleString() : null,
              impressions: perf?.impressions?.status === "MEASURED" ? perf.impressions.raw_value : null,
              clicks: perf?.clicks?.status === "MEASURED" ? perf.clicks.raw_value : null,
              conversions: perf?.deployments?.status === "MEASURED" ? perf.deployments.raw_value : (perf?.conversions?.status === "MEASURED" ? perf.conversions.raw_value : null),
            });
          }
        }

        // Posts from runs.
        //
        // This read `r.agent_outputs.agent_06_content.{x_threads,
        // linkedin_copy,reddit_copy}` — a shape the API has never emitted.
        // `agent_outputs` is keyed by agent id and holds metadata; the copy
        // A06 wrote lives under `r.posts.<channel>.{hook,copy}`. So `content`
        // was always undefined, the loop collected nothing, and the view
        // rendered "No Multi-Channel Posts Published Yet" over finished work.
        if (Array.isArray(data.runs)) {
          for (const r of data.runs) {
            const rp = r.posts;
            if (!rp) continue;

            // A11 does not dispatch unprompted, so a receipt exists only if it
            // really published. No placeholder profile URLs: an undispatched
            // post has no link, and inventing one implied it was live.
            const receipts: string[] = Array.isArray(r.agent_outputs?.A11_dispatch_worker?.outputs)
              ? r.agent_outputs.A11_dispatch_worker.outputs.filter((u: string) => /^https?:\/\//.test(u))
              : [];
            const at = r.started ? new Date(r.started * 1000).toLocaleString() : null;

            const CHANNELS: Array<[string, string, string]> = [
              ["x", "X", "X"],
              ["linkedin", "LinkedIn", "LI"],
              ["reddit", "Reddit", "RD"],
            ];

            CHANNELS.forEach(([key, platform, prefix], idx) => {
              const post = rp[key];
              if (!post?.copy) return;
              const id = `${prefix}-${r.run_id}`;
              const perf = perfMap.get(id) || perfMap.get(`PERF-${id}`);
              collected.push({
                id,
                platform,
                title: post.hook || r.title,
                leadCopy: post.copy,
                fullThread: key === "x"
                  ? String(post.copy).split(/\n\s*\n/).map((s: string) => s.trim()).filter(Boolean)
                  : undefined,
                publishedUrl: receipts[idx] ?? null,
                dispatched: r.dispatched === true,
                publishedAt: at,
                impressions: perf?.impressions?.status === "MEASURED" ? perf.impressions.raw_value : null,
                clicks: perf?.clicks?.status === "MEASURED" ? perf.clicks.raw_value : null,
                conversions: perf?.deployments?.status === "MEASURED"
                  ? perf.deployments.raw_value
                  : (perf?.conversions?.status === "MEASURED" ? perf.conversions.raw_value : null),
              });
            });
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
            <span style={{ width: "10px", height: "10px", borderRadius: "999px", background: posts.length > 0 ? "#4ADE9B" : "#7B7590" }} />
            <span style={{ fontFamily: MONO, fontSize: "12px", fontWeight: 700, color: posts.length > 0 ? "#4ADE9B" : "#7B7590", letterSpacing: "0.08em" }}>
              MULTI-CHANNEL SOCIAL FEED // {posts.length > 0
                ? `${posts.length} DRAFTED · ${posts.filter((p) => p.dispatched).length} PUBLISHED`
                : "STANDBY (0 ARTIFACTS)"}
            </span>
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#FFFFFF", marginTop: "6px" }}>
            Draft Library — every post the agents wrote
          </h2>
          <p style={{ fontSize: "14px", color: "#7B7590", marginTop: "4px" }}>
            Every X, LinkedIn and Reddit draft the agents wrote, across all runs.
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
                color: platformFilter === plat ? "#FFFFFF" : "#7B7590",
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
            <p style={{ color: "#7B7590", fontSize: "13px", maxWidth: "480px", margin: 0, lineHeight: 1.5 }}>
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
                    color: post.platform === "X" ? "#A98CFF" : (post.platform === "LinkedIn" ? "#A98CFF" : "#FF5722"),
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    padding: "4px 10px",
                    borderRadius: "6px"
                  }}
                >
                  {post.platform}
                </span>
                {/* "Published" is a claim only a dispatch receipt supports. */}
                <span style={{ fontSize: "12px", color: post.dispatched ? "#4ADE9B" : "#7B7590" }}>
                  {post.dispatched ? "Published" : "Drafted"}
                  {post.publishedAt ? `: ${post.publishedAt}` : ""}
                </span>
              </div>

              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  onClick={() => handleCopy(post.id, post.fullThread ? post.fullThread.join("\n\n") : post.leadCopy)}
                  style={{
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.12)",
                    color: copiedId === post.id ? "#4ADE9B" : "#B8B3C6",
                    padding: "6px 12px",
                    borderRadius: "6px",
                    fontSize: "11px",
                    fontFamily: MONO,
                    cursor: "pointer"
                  }}
                >
                  {copiedId === post.id ? "✓ Copied!" : "Copy Post"}
                </button>
                {post.publishedUrl && (
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
                )}
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
              <span style={{ color: "#7B7590" }}>
                Impressions: <strong style={{ color: post.impressions != null ? "#FFFFFF" : "#7B7590" }}>
                  {post.impressions != null ? post.impressions.toLocaleString() : "Pending Telemetry Sync (NULL ≠ 0)"}
                </strong>
              </span>
              <span style={{ color: "#7B7590" }}>
                Clicks: <strong style={{ color: post.clicks != null ? "#A98CFF" : "#7B7590" }}>
                  {post.clicks != null ? post.clicks.toLocaleString() : "Pending Sync"}
                </strong>
              </span>
              <span style={{ color: "#7B7590" }}>
                Sandbox Deployments: <strong style={{ color: post.conversions != null ? "#4ADE9B" : "#7B7590" }}>
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
