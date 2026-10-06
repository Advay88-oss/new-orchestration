"use client";

/**
 * Autopilot: what runs on its own, and the one line that changes it.
 *
 * The owner says the plan in a sentence ("research every 2 minutes", "make 10
 * posts") and the scheduler follows it: every named job keeps its own gap,
 * and posts asked for by count run one after another until the count is done.
 * Every post still stops at review. Nothing here publishes.
 */
import React, { useCallback, useEffect, useState } from "react";
import { MONO } from "@/lib/colors";
import { IconClose } from "./icons";

export const WORK_LABEL: Record<string, string> = {
  gtm_cycle: "Posts",
  research_collect: "Research",
  campaigns_refresh: "Campaigns",
  trend_scan: "Trends",
  ideas_panel: "Ideas",
  memes_panel: "Memes",
  github_commits: "GitHub",
  notion_sync: "Notion",
  brain_watch: "Public listening",
  metrics_collect: "Post results",
  ops_watch: "Health check",
};

const WORK_LANDS: Record<string, string> = {
  gtm_cycle: "Posts",
  research_collect: "Signals",
  campaigns_refresh: "Campaigns",
  trend_scan: "Signals",
  ideas_panel: "Posts",
  memes_panel: "Telegram",
  github_commits: "the brand brain",
  notion_sync: "the brand brain",
  brain_watch: "the brand brain",
  metrics_collect: "Learning",
  ops_watch: "Telegram, when something breaks",
};

const TELL: Record<string, { stop: string; start: string }> = {
  gtm_cycle: { stop: "stop posts", start: "start posts" },
  research_collect: { stop: "stop headlines", start: "start headlines" },
  campaigns_refresh: { stop: "stop campaigns", start: "start campaigns" },
  trend_scan: { stop: "stop trends", start: "start trends" },
  ideas_panel: { stop: "stop ideas", start: "start ideas" },
  memes_panel: { stop: "stop memes", start: "start memes" },
  github_commits: { stop: "stop github", start: "start github" },
  notion_sync: { stop: "stop notion", start: "start notion" },
  brain_watch: { stop: "stop brand watch", start: "start brand watch" },
  metrics_collect: { stop: "stop metrics", start: "start metrics" },
  ops_watch: { stop: "stop health", start: "start health" },
};

/** "20m" -> "20 min", "2h" -> "2 hours". */
export function gapLabel(g: string | undefined): string {
  const m = String(g || "").match(/^(\d+)\s*([mhd])$/);
  if (!m) return String(g || "");
  const n = Number(m[1]);
  if (m[2] === "m") return n + " min";
  if (m[2] === "h") return n === 1 ? "hour" : n + " hours";
  return n === 1 ? "day" : n + " days";
}

function istWhen(iso: string): string {
  const d = new Date(iso);
  if (!iso || Number.isNaN(d.getTime())) return "";
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata", month: "short", day: "numeric", hour: "numeric", minute: "2-digit", hour12: true,
  }).format(d) + " IST";
}

export type Clock = {
  jobs?: any[];
  posts?: string;
  posts_left?: number | null;
  chain?: { where?: string } | null;
  until?: string;
};

export type Daemon = { running?: boolean; cloud?: boolean; label?: string; wanted?: boolean } | null;

/** The scheduler and the process behind it, polled. */
export function useAutopilot(every = 15000, enabled = true) {
  const [clock, setClock] = useState<Clock | null>(null);
  const [daemon, setDaemon] = useState<Daemon>(null);
  const load = useCallback(async () => {
    const [s, d] = await Promise.all([
      fetch("/api/scheduler", { cache: "no-store" }).then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch("/api/daemon", { cache: "no-store" }).then((r) => (r.ok ? r.json() : null)).catch(() => null),
    ]);
    setClock(s);
    setDaemon(d);
  }, []);
  useEffect(() => {
    if (!enabled) return;
    load();
    const t = setInterval(load, every);
    const on = () => load();
    window.addEventListener("vn:autopilot", on);
    return () => { clearInterval(t); window.removeEventListener("vn:autopilot", on); };
  }, [load, every, enabled]);
  return { clock, daemon, reload: load };
}

/** One line for the sidebar card: what posts and research are doing. */
export function autopilotSummary(clock: Clock | null, daemon: Daemon): { on: boolean; title: string; sub: string } {
  const jobs = (clock?.jobs || []) as any[];
  const job = (name: string) => jobs.find((j) => j.job === name);
  const post = job("gtm_cycle");
  const research = job("research_collect");
  const alive = Boolean(daemon?.running || daemon?.cloud);
  const postsOn = Boolean(post && post.enabled !== false && !post.paused);
  const left = typeof clock?.posts_left === "number" ? clock.posts_left : null;
  let title = "Autopilot off";
  if (postsOn && clock?.chain && left) title = "Autopilot · " + left + (left === 1 ? " post left" : " posts left");
  else if (postsOn) title = "Autopilot · every " + gapLabel(post.interval);
  else if (alive) title = "Autopilot · posts paused";
  const researchOn = Boolean(research && research.enabled !== false && !research.paused);
  const sub = !alive ? "Scheduler is not running"
    : researchOn ? "Research every " + gapLabel(research.interval)
    : "Research paused";
  const anyOn = jobs.some((j) => WORK_LABEL[j.job] && j.enabled !== false && !j.paused);
  return { on: alive && anyOn, title, sub };
}

export function AutopilotPanel({ onClose, goCampaigns }: { onClose: () => void; goCampaigns?: () => void }) {
  const { clock, daemon, reload } = useAutopilot(8000);
  const [line, setLine] = useState("");
  const [busy, setBusy] = useState("");
  const [note, setNote] = useState<string[]>([]);
  const [shelves, setShelves] = useState<any[]>([]);

  useEffect(() => {
    fetch("/api/gtm/campaigns", { cache: "no-store" }).then((r) => r.json())
      .then((c) => setShelves(Array.isArray(c?.shelves) ? c.shelves : [])).catch(() => {});
  }, []);

  useEffect(() => {
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);

  const tell = async (text: string, key = "line") => {
    if (!text.trim()) return;
    setBusy(key);
    setNote([]);
    try {
      const r = await fetch("/api/scheduler", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "tell", text }),
      });
      const d = await r.json();
      const lines = String(d.message || d.error || "").split("\n").filter(Boolean);
      setNote(d.success ? lines : [lines[0] || "That did not stick."]);
      if (d.success && key === "line") setLine("");
    } catch {
      setNote(["That did not reach the scheduler."]);
    }
    setBusy("");
    await reload();
    window.dispatchEvent(new Event("vn:autopilot"));
  };

  const power = async (action: "start" | "stop") => {
    setBusy("daemon");
    try {
      await fetch("/api/daemon", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action }) });
    } catch { /* the status below says what happened */ }
    setBusy("");
    await reload();
    window.dispatchEvent(new Event("vn:autopilot"));
  };

  const jobs = ((clock?.jobs || []) as any[]).filter((j) => WORK_LABEL[j.job]);
  const isOn = (j: any) => j.enabled !== false && !j.paused;
  const running = jobs.filter(isOn);
  const stopped = jobs.filter((j) => !isOn(j) && (j.cron_id || j.paused));
  const left = typeof clock?.posts_left === "number" ? clock.posts_left : null;
  const alive = Boolean(daemon?.running || daemon?.cloud);

  const Row = ({ j }: { j: any }) => {
    const on = isOn(j);
    const phrase = TELL[j.job];
    const chain = j.job === "gtm_cycle" && clock?.chain && left;
    return (
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12, padding: "12px 14px", borderTop: "1px solid var(--vn-line)" }}>
        <span className="hd-dot" style={{ marginTop: 7, background: on ? (j.status === "RUNNING" ? "var(--vn-warn)" : "var(--vn-ok)") : "var(--vn-line-strong)" }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 550, color: on ? "var(--vn-ink)" : "var(--vn-ink-muted)" }}>
            {WORK_LABEL[j.job]}
            <span style={{ fontWeight: 400, color: "var(--vn-ink-muted)" }}>
              {chain ? " · " + left + " left, one after another" : " · every " + gapLabel(j.interval)}
            </span>
          </div>
          <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", marginTop: 2, lineHeight: 1.45 }}>
            {j.status === "RUNNING" ? "Running now. " : ""}Shows in {WORK_LANDS[j.job] || j.lands}.
            {j.last_run && j.last_run !== "Never" ? " Last ran " + istWhen(j.last_run) + "." : ""}
          </div>
          {j.cron_id && j.cron_state === "live" && (
            <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-faint)", marginTop: 3 }}>GCP cron · {j.cron}</div>
          )}
          {j.status === "DISABLED_AUTO_BACKOFF" && (
            <div style={{ fontSize: 12, color: "var(--vn-bad)", marginTop: 3 }}>Paused after 3 failures in a row.</div>
          )}
        </div>
        {phrase && (
          <button className="hd-btn" disabled={busy === j.job} onClick={() => tell(on ? phrase.stop : phrase.start, j.job)}
                  style={{ padding: "5px 10px", fontSize: 12.5, fontWeight: 500 }}>
            {busy === j.job ? "…" : on ? "Pause" : "Resume"}
          </button>
        )}
      </div>
    );
  };

  return (
    <>
      <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 80, background: "var(--vn-overlay)" }} />
      <aside className="hd-drawer" role="dialog" aria-label="Autopilot">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 16px 8px 20px" }}>
          <div style={{ fontSize: 16, fontWeight: 600, color: "var(--vn-ink)" }}>Autopilot</div>
          <button className="hd-icon-btn" onClick={onClose} aria-label="Close"><IconClose /></button>
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: "0 16px 24px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, padding: "10px 4px 14px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "var(--vn-ink-body)" }}>
              <span className="hd-dot" style={{ background: alive ? "var(--vn-ok)" : "var(--vn-ink-faint)" }} />
              {daemon === null ? "Checking the scheduler…"
                : daemon.cloud ? "Runs on GCP (Cloud Scheduler)"
                : daemon.running ? "Runs on this machine, restarted if it stops"
                : daemon.wanted === false ? "Scheduler stopped by you" : "Scheduler is not running"}
            </div>
            {daemon && !daemon.cloud && (
              <button className="hd-btn" disabled={busy === "daemon"} onClick={() => power(daemon.running ? "stop" : "start")}
                      style={{ padding: "5px 10px", fontSize: 12.5, fontWeight: 500 }}>
                {busy === "daemon" ? "…" : daemon.running ? "Stop all" : "Start"}
              </button>
            )}
          </div>

          <form onSubmit={(e) => { e.preventDefault(); tell(line); }} className="hd-composer" style={{ padding: 6 }}>
            <textarea value={line} onChange={(e) => setLine(e.target.value)} rows={2}
                      onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); tell(line); } }}
                      placeholder="Research every 2 minutes and make 10 posts"
                      style={{ width: "100%", resize: "none", border: "none", background: "transparent", padding: "10px 10px 4px",
                               fontSize: 14, lineHeight: 1.5, fontFamily: "inherit", color: "var(--vn-ink)" }} />
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 4px 4px 10px" }}>
              <span style={{ fontSize: 12, color: "var(--vn-ink-faint)" }}>One line sets every gap</span>
              <button type="submit" className="hd-btn hd-btn-dark" disabled={!line.trim() || busy === "line"} style={{ padding: "6px 12px" }}>
                {busy === "line" ? "Setting…" : "Set"}
              </button>
            </div>
          </form>
          {note.length > 0 && (
            <div className="hd-pop" style={{ marginTop: 10, padding: "10px 12px", borderRadius: 10, background: "var(--vn-surface)", border: "1px solid var(--vn-line)", fontSize: 13, lineHeight: 1.55, color: "var(--vn-ink-body)" }}>
              {note.map((l, i) => <div key={i}>{l}</div>)}
            </div>
          )}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
            {["Research every 2 minutes", "Make 10 posts", "Memes every 30 minutes", "Stop posts"].map((s) => (
              <button key={s} className="hd-chip" style={{ fontSize: 12.5, padding: "5px 11px" }} onClick={() => tell(s, "line")}>{s}</button>
            ))}
          </div>

          <div style={{ fontSize: 12, color: "var(--vn-ink-faint)", margin: "22px 4px 6px" }}>Running{clock ? " (" + running.length + ")" : ""}</div>
          <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, overflow: "hidden" }}>
            {!clock && <div style={{ padding: "14px" }}><span className="vn-skel" style={{ width: "70%", height: 10, borderRadius: 5 }} /></div>}
            {clock && running.length === 0 && <div style={{ padding: "12px 14px", fontSize: 13, color: "var(--vn-ink-muted)" }}>Nothing runs on its own yet.</div>}
            {running.map((j, i) => <div key={j.job} style={i === 0 ? { marginTop: -1 } : undefined}><Row j={j} /></div>)}
          </div>

          {stopped.length > 0 && (
            <>
              <div style={{ fontSize: 12, color: "var(--vn-ink-faint)", margin: "18px 4px 6px" }}>Paused ({stopped.length})</div>
              <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, overflow: "hidden" }}>
                {stopped.map((j, i) => <div key={j.job} style={i === 0 ? { marginTop: -1 } : undefined}><Row j={j} /></div>)}
              </div>
            </>
          )}

          {shelves.length > 0 && (
            <>
              <div style={{ fontSize: 12, color: "var(--vn-ink-faint)", margin: "18px 4px 6px" }}>Campaign searches</div>
              {shelves.map((s: any) => (
                <button key={(s.source_input || s.source) + (s.scraped_at || "")} onClick={() => { goCampaigns?.(); onClose(); }}
                        style={{ width: "100%", textAlign: "left", background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12,
                                 padding: "12px 14px", cursor: "pointer", color: "inherit", marginBottom: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, fontWeight: 550, color: "var(--vn-ink)" }}>
                    <span style={{ textTransform: "capitalize" }}>{s.source_input || s.source || "Campaigns"}</span>
                    <span style={{ fontFamily: MONO, fontSize: 12, color: "var(--vn-ink-muted)" }}>{s.count || (s.campaigns || []).length}</span>
                  </div>
                  <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", marginTop: 3 }}>{s.query}</div>
                </button>
              ))}
            </>
          )}
          <div style={{ fontSize: 12, color: "var(--vn-ink-faint)", lineHeight: 1.5, margin: "18px 4px 0" }}>
            Every post stops at review, here and on Telegram. Nothing is published on its own.
          </div>
        </div>
      </aside>
    </>
  );
}
