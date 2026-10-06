"use client";

import React, { useState, useEffect } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";
import { EmptyState, SkeletonCard } from "@/components/States";
import { OpsCard } from "@/components/views/OpsCard";

/** What a founder needs to see. The job id stays the key the scheduler runs. */
const PLAIN: Record<string, { title: string; does: string; lands: string; look?: "runs" | "trace" | "plays" | "research" }> = {
  gtm_cycle: {
    title: "Writes a post",
    does: "The agents write a post on the gap you tell them. They pick the subject, write it, and make the image. It stops for you. Nothing is published.",
    lands: "Post History",
    look: "runs",
  },
  brain_watch: {
    title: "Listens in public",
    does: "Reads what is being said about the company on X, Reddit, news, and the web. This is the scrape. It does not write a post.",
    lands: "The brand brain. The next post can use it. There is no separate page for the raw scrape.",
  },
  github_commits: {
    title: "Reads our GitHub",
    does: "Pulls the product pages (Solana and Stellar) into the brain every 6 hours, and new commits every hour. A post may use a figure only when that page states it.",
    lands: "The brand brain, on the page it came from.",
  },
  notion_sync: {
    title: "Syncs Notion",
    does: "Once a day, copies connected Notion pages into the brain so a post can use what you already wrote there.",
    lands: "The brand brain, and your Notion workspace.",
  },
  metrics_collect: {
    title: "Reads what a published post did",
    does: "After you publish a post, this looks up engagement about two days later. Until something is published, it has nothing to read.",
    lands: "Learning",
  },
  research_collect: {
    title: "Collects research",
    does: "Reads live headlines from news, Reddit, Telegram and docs. It does not write the post. The next post is allowed to use this list.",
    lands: "Scraped Intelligence, then the next post in Post History.",
    look: "research",
  },
  ops_watch: {
    title: "Checks the machine is healthy",
    does: "Once an hour. If a job fails, you get one Telegram note. The spend for today is the card above.",
    lands: "This page, and Telegram when something breaks.",
  },
};

const STATUS_WORD: Record<string, string> = {
  RUNNING: "Working now",
  COMPLETED: "Done",
  IDLE: "Waiting",
  FAILED: "Failed",
  DISABLED_AUTO_BACKOFF: "Paused after failures",
  STOPPED: "Stopped",
};

export function SchedulerView({ vm }: { vm: MissionVM }) {
  const [schedulerData, setSchedulerData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [runningJob, setRunningJob] = useState<string | null>(null);
  const [tell, setTell] = useState("");

  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/scheduler", { cache: "no-store" });
      const data = await res.json();
      if (data.success) setSchedulerData(data);
    } catch (e: any) {
      console.warn("Scheduler fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const itv = setInterval(fetchStatus, 4000);
    return () => clearInterval(itv);
  }, []);

  const handleRunNow = async (jobName: string) => {
    setRunningJob(jobName);
    const name = PLAIN[jobName]?.title || jobName;
    setActionFeedback(`${name} is starting.`);
    try {
      const res = await fetch("/api/scheduler", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "run_now", job: jobName }),
      });
      const data = await res.json();
      setActionFeedback(data.success ? `${name} is running. This page follows it.` : `Note: ${data.error || "Skipped, or already running."}`);
      await fetchStatus();
    } catch (err: any) {
      setActionFeedback(`Failed: ${err.message}`);
    } finally {
      setRunningJob(null);
    }
  };

  const handleTell = async () => {
    const text = tell.trim();
    if (!text) return;
    setActionFeedback("Telling the agents.");
    try {
      const res = await fetch("/api/scheduler", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "tell", text }),
      });
      const data = await res.json();
      setActionFeedback(data.success ? (data.message || "Done.") : (data.error || "That did not stick."));
      if (data.success) setTell("");
      await fetchStatus();
    } catch (err: any) {
      setActionFeedback(err.message);
    }
  };

  const jobs = (schedulerData?.jobs || []).filter((j: any) => j.enabled !== false);
  const post = jobs.find((j: any) => j.job === "gtm_cycle");
  const latest = (vm.runRows || [])[0] as { headline?: string; label?: string; outcomeLabel?: string; open?: () => void } | undefined;

  const openLook = (look?: "runs" | "trace" | "plays" | "research") => {
    if (look === "runs") vm.goRuns();
    else if (look === "trace") vm.goTrace();
    else if (look === "plays") vm.goVannaPlays();
    else if (look === "research") vm.goResearch();
  };

  return (
    <section className="vanna-section">
      <div className="vanna-banner">
        <div>
          <div style={{ fontFamily: MONO, fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: "var(--vn-ok)" }}>
            ON ITS OWN
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: "var(--vn-ink)", margin: "6px 0 0" }}>
            The clock writes a post, then waits for you
          </h2>
          <p style={{ fontSize: 14, color: "var(--vn-ink-muted)", marginTop: 6, maxWidth: 640, lineHeight: 1.5 }}>
            Listening and GitHub go into the brain. Every 6 hours that reading becomes one post in Post History.
            You approve it. Nothing publishes by itself.
          </p>
        </div>
        <div style={{ background: "var(--vn-ok-soft)", border: "1px solid var(--vn-ok-line)", borderRadius: 8, padding: "10px 16px" }}>
          <div style={{ fontFamily: MONO, fontSize: 10, color: "var(--vn-ink-muted)" }}>ON THE CLOCK</div>
          <div style={{ fontFamily: MONO, fontSize: 14, fontWeight: 700, color: "var(--vn-ok)", marginTop: 2 }}>
            {jobs.length} jobs
          </div>
        </div>
      </div>

      {latest?.headline ? (
        <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: "14px 16px", display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontFamily: MONO, fontSize: 10.5, letterSpacing: 0.6, color: "var(--vn-ink-muted)" }}>LATEST POST</div>
            <div style={{ fontSize: 15, fontWeight: 650, marginTop: 4, color: "var(--vn-ink)" }}>{latest.headline}</div>
            <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", marginTop: 4 }}>{latest.outcomeLabel || "Held for review"}</div>
          </div>
          <button onClick={() => (latest.open ? latest.open() : vm.goRuns())} style={{ background: "var(--vn-cta)", color: "var(--vn-on-accent)", border: "none", borderRadius: 8, padding: "8px 14px", fontSize: 12.5, fontWeight: 700, cursor: "pointer" }}>
            Open the post
          </button>
        </div>
      ) : null}

      <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: "16px 18px" }}>
        <div style={{ fontFamily: MONO, fontSize: 10.5, letterSpacing: 0.6, color: "var(--vn-ink-muted)" }}>TELL THE AGENTS</div>
        <p style={{ margin: "6px 0 12px", fontSize: 14, lineHeight: 1.5, color: "var(--vn-ink-body)" }}>
          {post?.paused
            ? "Posts are stopped."
            : "A post every " + (post?.interval || "2h") + "."}
          {" "}Say the gap you want, or say stop. You can say the same thing in Assistant.
        </p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input value={tell} onChange={(e) => setTell(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleTell()}
                 placeholder="A post every 2 hours, or stop"
                 style={{ flex: "1 1 240px", background: "var(--vn-sunken)", border: "1px solid var(--vn-line)", borderRadius: 8, padding: "9px 12px", color: "var(--vn-ink)", fontSize: 14 }} />
          <button onClick={handleTell} disabled={!tell.trim()}
                  style={{ background: "var(--vn-accent)", color: "#fff", border: "none", borderRadius: 8, padding: "9px 16px", fontWeight: 600, cursor: "pointer" }}>
            Tell them
          </button>
        </div>
      </div>

      {actionFeedback && (
        <div style={{ fontSize: 13, color: actionFeedback.startsWith("Failed") ? "var(--vn-bad)" : "var(--vn-ink)", background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 8, padding: "10px 14px" }}>
          {actionFeedback}
        </div>
      )}

      <OpsCard />

      {loading && jobs.length === 0 && <><SkeletonCard lines={2} /><SkeletonCard lines={2} /></>}
      {!loading && jobs.length === 0 && (
        <EmptyState icon="runs" title="The clock is not reachable" body="Jobs are read from the scheduler on the machine that runs the pipeline." />
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {jobs.map((j: any) => {
          const plain = PLAIN[j.job] || { title: j.job, does: j.description, lands: "See the description." };
          const word = STATUS_WORD[j.status] || j.status;
          const statusColor = j.status === "RUNNING" ? "var(--vn-accent-ink)" : j.status === "FAILED" || j.status === "DISABLED_AUTO_BACKOFF" ? "var(--vn-bad)" : j.status === "COMPLETED" ? "var(--vn-ok)" : "var(--vn-ink-muted)";
          return (
            <article key={j.job} style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: "16px 18px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", flexWrap: "wrap" }}>
                <div style={{ maxWidth: 720 }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "baseline", flexWrap: "wrap" }}>
                    <h3 style={{ margin: 0, fontSize: 16 }}>{plain.title}</h3>
                    <span style={{ fontFamily: MONO, fontSize: 11, color: statusColor }}>{word}</span>
                  </div>
                  <p style={{ margin: "6px 0 0", fontSize: 13.5, lineHeight: 1.5, color: "var(--vn-ink-body)" }}>{plain.does}</p>
                  <p style={{ margin: "8px 0 0", fontSize: 13, color: "var(--vn-ink)" }}>
                    <span style={{ color: "var(--vn-ink-muted)" }}>Stored in </span>{plain.lands}
                  </p>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  {plain.look && (
                    <button onClick={() => openLook(plain.look)} style={{ background: "transparent", border: "1px solid var(--vn-line-strong)", color: "var(--vn-ink)", borderRadius: 8, padding: "8px 12px", fontSize: 12, cursor: "pointer" }}>
                      Open
                    </button>
                  )}
                  <button
                    onClick={() => handleRunNow(j.job)}
                    disabled={runningJob === j.job || j.status === "RUNNING"}
                    style={{ background: "var(--vn-cta)", color: "var(--vn-on-accent)", border: "none", borderRadius: 8, padding: "8px 12px", fontSize: 12, fontWeight: 700, cursor: "pointer" }}
                  >
                    {runningJob === j.job || j.status === "RUNNING" ? "Running" : "Run now"}
                  </button>
                </div>
              </div>
              {j.job === "gtm_cycle" && (
                <div style={{ marginTop: 10, fontSize: 13, color: "var(--vn-ink)" }}>
                  {j.paused ? "Stopped, until you say start." : "Every " + j.interval + "."}
                </div>
              )}
              {j.consecutive_failures > 0 ? (
                <div style={{ marginTop: 8, fontFamily: MONO, fontSize: 12, color: "var(--vn-bad)" }}>{j.consecutive_failures} failed</div>
              ) : null}
            </article>
          );
        })}
      </div>

      <p style={{ fontSize: 13, color: "var(--vn-ink-muted)", lineHeight: 1.5 }}>
        The shortest post gap is 20 minutes. If a post is still being made, the next one waits until it finishes.
        The other jobs keep their own gaps. Nothing is published until you say so.
      </p>
    </section>
  );
}
