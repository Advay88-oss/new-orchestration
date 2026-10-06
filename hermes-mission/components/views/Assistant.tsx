"use client";

/**
 * The home screen: a chat about one company at a time.
 *
 * Pick a company, ask anything (answers come from its brand brain, with
 * sources), add a new company from its website, connect its Notion. The
 * assistant (pipeline/assistant) shows what it is doing — each tool it calls
 * — and returns cards: an analysis running, a Notion button, an action for
 * the owner to confirm, a run to open. It never launches, approves or
 * publishes anything itself. Conversations are stored per company on the
 * server; answers stream in and are checked against their sources.
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

type Card = { type: string; [k: string]: any };
type Tool = { name: string; summary: string };
type Grounding = { checked: number; supported?: number; flagged?: { text: string; verdict: string }[]; note?: string };
type Msg = { role: "user" | "assistant"; text: string; tools?: Tool[]; cards?: Card[]; grounding?: Grounding;
             error?: string; pending?: boolean; stopped?: boolean };
type Thread = { id: string; title: string; updated_at: string };


// ---------------------------------------------------------------- markdown

function inline(s: string, key: string): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\((https?:\/\/[^)\s]+)\))/g;
  let last = 0, m: RegExpExecArray | null, i = 0;
  while ((m = re.exec(s))) {
    if (m.index > last) out.push(s.slice(last, m.index));
    const t = m[0];
    if (t.startsWith("**")) out.push(<strong key={key + i++}>{t.slice(2, -2)}</strong>);
    else if (t.startsWith("`")) out.push(<code key={key + i++} style={{ fontFamily: MONO, fontSize: "0.9em", background: "var(--vn-sunken)", border: "1px solid var(--vn-line)", borderRadius: 4, padding: "0 4px" }}>{t.slice(1, -1)}</code>);
    else {
      const label = t.slice(1, t.indexOf("]"));
      out.push(<a key={key + i++} href={m[2]} target="_blank" rel="noopener noreferrer">{label}</a>);
    }
    last = m.index + t.length;
  }
  if (last < s.length) out.push(s.slice(last));
  return out;
}

function Markdown({ text }: { text: string }) {
  const blocks: React.ReactNode[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;
  const flush = () => {
    if (!list) return;
    const L = list.ordered ? "ol" : "ul";
    blocks.push(<L key={"l" + blocks.length} style={{ margin: "4px 0 10px", paddingLeft: 20, lineHeight: 1.6 }}>
      {list.items.map((it, j) => <li key={j}>{inline(it, "li" + j)}</li>)}</L>);
    list = null;
  };
  text.split("\n").forEach((raw, n) => {
    const line = raw.trimEnd();
    const b = line.match(/^\s*[-*•]\s+(.*)/), o = line.match(/^\s*\d+[.)]\s+(.*)/), h = line.match(/^#{1,4}\s+(.*)/);
    if (b || o) {
      const ordered = Boolean(o);
      if (!list || list.ordered !== ordered) { flush(); list = { ordered, items: [] }; }
      list.items.push((b || o)![1]);
      return;
    }
    flush();
    if (h) blocks.push(<div key={n} style={{ fontWeight: 600, fontSize: 14.5, margin: "10px 0 4px", color: "var(--vn-ink)" }}>{inline(h[1], "h" + n)}</div>);
    else if (/^---+$/.test(line)) blocks.push(<hr key={n} style={{ border: 0, borderTop: "1px solid var(--vn-line)", margin: "10px 0" }} />);
    else if (line.trim()) blocks.push(<p key={n} style={{ margin: "0 0 8px", color: "var(--vn-ink-body)", fontSize: 14.5, lineHeight: 1.65 }}>{inline(line, "p" + n)}</p>);
  });
  flush();
  return <>{blocks}</>;
}

// ---------------------------------------------------------------- grounding

function Grounding({ g }: { g: Grounding }) {
  if (!g.checked) {
    return g.note ? <div style={{ fontSize: 11.5, color: "var(--vn-ink-faint)", marginTop: 4 }}>{g.note}</div> : null;
  }
  const flagged = g.flagged || [];
  return (
    <div style={{ marginTop: 6 }}>
      <div style={{ fontFamily: MONO, fontSize: 11, color: flagged.length ? "var(--vn-warn)" : "var(--vn-ok)" }}>
        {flagged.length ? g.supported + " of " + g.checked + " claims found in the sources"
                        : "all " + g.checked + " claims found in the sources"}
      </div>
      {flagged.map((f, i) => (
        <div key={i} style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", margin: "3px 0 0", paddingLeft: 10,
                              borderLeft: "2px solid " + (f.verdict === "CONTRADICTED" ? "var(--vn-bad)" : "var(--vn-warn)") }}>
          {f.verdict === "CONTRADICTED" ? "Contradicted by the sources" : "Not in the sources"}: &ldquo;{f.text}&rdquo;
        </div>
      ))}
    </div>
  );
}

function Asked({ c }: { c: Card }) {
  return c.asked ? <div style={{ fontSize: 11, color: "var(--vn-ink-faint)", marginTop: 6 }}>Because you asked: &ldquo;{String(c.asked).slice(0, 120)}&rdquo;</div> : null;
}

// -------------------------------------------------------------------- cards

const btn: React.CSSProperties = { border: "1px solid var(--vn-line-strong)", background: "transparent", color: "var(--vn-ink)",
  borderRadius: 6, padding: "7px 12px", fontSize: 13, cursor: "pointer", textDecoration: "none", display: "inline-block" };
const cta: React.CSSProperties = { ...btn, background: "var(--vn-cta)", color: "var(--vn-on-accent)", border: "none" };
const cardBox: React.CSSProperties = { border: "1px solid var(--vn-line)", borderRadius: 10, padding: "12px 14px", background: "var(--vn-surface)", marginTop: 8 };

function usePoll(url: string | null, done: (d: any) => boolean) {
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    if (!url) return;
    let stop = false;
    const tick = async () => {
      try {
        const j = await (await fetch(url, { cache: "no-store" })).json();
        if (!stop) setD(j);
        if (!stop && !done(j)) setTimeout(tick, 4000);
      } catch { if (!stop) setTimeout(tick, 6000); }
    };
    tick();
    return () => { stop = true; };
  }, [url]); // eslint-disable-line react-hooks/exhaustive-deps
  return d;
}

function AnalysisCard({ c, onPick }: { c: Card; onPick: (t: string) => void }) {
  const d = usePoll("/api/gtm/brain/analyze?tenant=" + c.tenant, (j) => j.state && j.state !== "running");
  const state = d?.state || "running";
  return (
    <div style={cardBox}>
      <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-muted)" }}>WEBSITE ANALYZER · {c.tenant}</div>
      {state === "running" && <div style={{ fontSize: 13.5, marginTop: 6 }}>Crawling {c.url || "the site"}: pages, colours, fonts, voice, competitors. One to three minutes.</div>}
      {state === "done" && (
        <>
          <div style={{ fontSize: 13.5, marginTop: 6 }}>
            {d.result?.saved
              ? <>Draft profile v{d.result.version} for <b>{d.name || c.tenant}</b>: {d.result.pages} pages, {d.result.knowledge_chunks} knowledge chunks. It waits for your approval.</>
              : <>Report written for <b>{d.name || c.tenant}</b> (it already had a profile, so nothing was replaced).</>}
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
            <button style={cta} onClick={() => onPick(c.tenant)}>Chat about {d.name || c.tenant}</button>
            <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", marginTop: 8 }}>
              The draft is stored in the brand brain. Read it with <code>python -m pipeline.brand_brain profile {c.tenant}</code>.
            </div>
          </div>
        </>
      )}
      {state === "failed" && <div style={{ fontSize: 13.5, marginTop: 6, color: "var(--vn-bad)" }}>Failed: {d.error || d.result?.error}</div>}
    </div>
  );
}

function CompetitorsCard({ c }: { c: Card }) {
  const d = usePoll("/api/gtm/brain/competitors?tenant=" + c.tenant, (j) => j.state && j.state !== "running");
  const rep = d?.report;
  return (
    <div style={cardBox}>
      <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-muted)" }}>COMPETITOR ANALYSIS · {c.tenant}</div>
      {(!d || d.state === "running") && <div style={{ fontSize: 13.5, marginTop: 6 }}>Reading competitors' websites and recent X posts. A few minutes.</div>}
      {d?.state === "done" && rep && (
        <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 13.5, lineHeight: 1.6 }}>
          {(rep.analysed || []).map((a: any) => <li key={a.competitor}>{a.competitor}: {a.ok ? a.patterns + " patterns, " + a.x_posts_read + " posts" : "not analysed"}</li>)}
          {(rep.suggested || []).length > 0 && <li>Suggested (confirm in the profile): {rep.suggested.map((s: any) => s.name).join(", ")}</li>}
        </ul>
      )}
      {d?.state === "failed" && <div style={{ fontSize: 13.5, color: "var(--vn-bad)" }}>Failed: {d.job?.error}</div>}
    </div>
  );
}

function NotionCard({ c }: { c: Card }) {
  const [copied, setCopied] = useState(false);
  const full = c.url?.startsWith("http") ? c.url : (typeof window !== "undefined" ? window.location.origin : "") + c.url;
  return (
    <div style={cardBox}>
      <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-muted)" }}>NOTION · {c.tenant}{c.connected ? " · connected" : ""}</div>
      {!c.configured && <div style={{ fontSize: 13, color: "var(--vn-warn)", marginTop: 6 }}>The Notion OAuth connection is not set up yet (NOTION_OAUTH_CLIENT_ID / _SECRET), so the link will say so.</div>}
      <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap", alignItems: "center" }}>
        {!c.for_client && <a href={full} style={cta}>Connect Notion</a>}
        <button style={btn} onClick={async () => { try { await navigator.clipboard.writeText(full); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { /* */ } }}>
          {copied ? "Copied" : c.for_client ? "Copy client invite link" : "Copy invite link"}
        </button>
      </div>
      <div style={{ fontSize: 11.5, color: "var(--vn-ink-muted)", marginTop: 6 }}>Works once, for {c.tenant} only, and expires in 7 days.</div>
    </div>
  );
}

function ActionCard({ c, tenant, threadId }: { c: Card; tenant: string; threadId: string | null }) {
  const [state, setState] = useState<string | null>(null);
  const label: Record<string, string> = { launch_run: "Launch run", approve: "Approve", revise: "Send back for revision", kill: "Kill", approve_profile: "Profile stays in the brain" };
  const go = async () => {
    setState("working");
    try {
      if (c.action === "approve_profile") {
        setState("Stored in the brand brain. Read it with: python -m pipeline.brand_brain profile " + (tenant || "vanna"));
        return;
      }
      const r = c.action === "launch_run"
        ? await fetch("/api/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ directive: c.directive || "" }) })
        : await fetch("/api/gtm/feedback", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ runId: c.run_id, verdict: c.action, note: c.note || "" }) });
      const j = await r.json();
      const ok = Boolean(j.success || j.ok);
      setState(ok ? "done" : "failed: " + (j.error || r.status));
      // The audit log records what the owner confirmed from the chat.
      fetch("/api/assistant/audit", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant, action: c.action, run_id: c.run_id, directive: c.directive,
                               result: ok ? "ok" : String(j.error || r.status), thread_id: threadId, asked: c.asked }) }).catch(() => {});
    } catch (e: any) { setState("failed: " + String(e?.message || e)); }
  };
  return (
    <div style={cardBox}>
      <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-muted)" }}>NEEDS YOUR CONFIRMATION</div>
      <div style={{ fontSize: 13.5, marginTop: 6 }}>
        {label[c.action] || c.action}{c.run_id ? " · " + c.run_id : ""}{c.directive ? " · “" + c.directive + "”" : ""}
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 10, alignItems: "center" }}>
        <button style={c.action === "kill" ? { ...btn, color: "var(--vn-bad)", borderColor: "var(--vn-bad-line)" } : cta}
                disabled={state === "working" || state === "done"} onClick={go}>
          {state === "done" ? "Done" : label[c.action] || "Confirm"}
        </button>
        {state && state.startsWith("failed") && <span style={{ fontSize: 12.5, color: "var(--vn-bad)" }}>{state}</span>}
        {state === "done" && c.action === "launch_run" && <span style={{ fontSize: 12.5, color: "var(--vn-ink-muted)" }}>Started. It shows up in Post History.</span>}
      </div>
      <Asked c={c} />
    </div>
  );
}

function RunCard({ c, vm }: { c: Card; vm: MissionVM }) {
  return (
    <div style={{ ...cardBox, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
      <span style={{ fontFamily: MONO, fontSize: 12 }}>{c.run_id}</span>
      <button style={btn} onClick={() => (vm as any).openRun(c.run_id)}>Open run</button>
    </div>
  );
}

function CardView({ c, vm, onPick, tenant, threadId }: { c: Card; vm: MissionVM; onPick: (t: string) => void;
                                                       tenant: string; threadId: string | null }) {
  if (c.type === "analysis") return <AnalysisCard c={c} onPick={onPick} />;
  if (c.type === "competitors") return <CompetitorsCard c={c} />;
  if (c.type === "notion") return <NotionCard c={c} />;
  if (c.type === "action") return <ActionCard c={c} tenant={tenant} threadId={threadId} />;
  if (c.type === "run") return <RunCard c={c} vm={vm} />;
  return null;
}

// ------------------------------------------------------------------ checks

/** The assistant's checks: real questions, judged (pipeline/assistant/evals.py). */
function ChecksPanel() {
  const [d, setD] = useState<any>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const load = useCallback(async () => {
    try { setD(await (await fetch("/api/assistant/evals", { cache: "no-store" })).json()); } catch (e) { setErr(String(e)); }
  }, []);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (d?.status?.state !== "running") return;
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [d?.status?.state, load]);
  const start = async () => {
    setErr(null);
    const r = await (await fetch("/api/assistant/evals", { method: "POST" })).json();
    if (!r.ok) setErr(r.error || "could not start"); else load();
  };
  const rep = d?.report;
  const running = d?.status?.state === "running";
  return (
    <div style={{ maxWidth: 820, margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
          <h2 style={{ marginBottom: 4 }}>Assistant checks</h2>
          <p style={{ margin: 0, maxWidth: "62ch" }}>
            Real questions through the real model and brain: facts from the sources, no invented numbers, a document
            that tries to give orders, actions only as buttons, Notion links, your language, memory, Stop, and speed.
          </p>
        </div>
        <button style={cta} disabled={running} onClick={start}>{running ? "Running… (3-5 min)" : "Run checks"}</button>
      </div>
      {err && <div style={{ color: "var(--vn-bad)", fontSize: 13, marginTop: 8 }}>{err}</div>}
      {!rep && !running && <p style={{ marginTop: 16 }}>No checks have run yet.</p>}
      {rep && (
        <>
          <div style={{ display: "flex", gap: 28, margin: "18px 0 12px", flexWrap: "wrap" }}>
            {[["passed", rep.passed + " / " + rep.total, rep.passed === rep.total ? "var(--vn-ok)" : "var(--vn-bad)"],
              ["first words", (rep.first_token_s_median ?? "–") + " s", "var(--vn-ink)"],
              ["full answer", (rep.answer_s_median ?? "–") + " s", "var(--vn-ink)"],
              ["checked", new Date(rep.finished_at || rep.at).toLocaleString(), "var(--vn-ink-muted)"]].map(([k, v, c]) => (
              <div key={k as string}>
                <div style={{ fontFamily: MONO, fontSize: 20, color: c as string }}>{v}</div>
                <div style={{ fontSize: 11.5, color: "var(--vn-ink-muted)" }}>{k}</div>
              </div>
            ))}
          </div>
          <div style={{ border: "1px solid var(--vn-line)", borderRadius: 10, overflow: "hidden" }}>
            {rep.results.map((x: any, i: number) => (
              <div key={x.case} style={{ borderTop: i ? "1px solid var(--vn-line)" : "none" }}>
                <button onClick={() => setOpen(open === x.case ? null : x.case)}
                        style={{ width: "100%", display: "flex", alignItems: "center", gap: 12, padding: "11px 14px", border: "none",
                                 background: open === x.case ? "var(--vn-raised)" : "transparent", cursor: "pointer", textAlign: "left" }}>
                  <span style={{ fontFamily: MONO, fontSize: 11, padding: "2px 7px", borderRadius: 4,
                                 background: x.passed ? "var(--vn-ok-soft)" : "var(--vn-bad-soft)",
                                 color: x.passed ? "var(--vn-ok)" : "var(--vn-bad)" }}>{x.passed ? "PASS" : "FAIL"}</span>
                  <span style={{ flex: 1, fontSize: 13.5, color: "var(--vn-ink)" }}>{x.title}</span>
                  <span style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-faint)" }}>{x.total_s != null ? x.total_s + " s" : ""}</span>
                </button>
                {open === x.case && (
                  <div style={{ padding: "4px 14px 14px", fontSize: 13 }}>
                    {x.question && <div style={{ color: "var(--vn-ink-muted)", margin: "4px 0 8px" }}>Asked: &ldquo;{x.question}&rdquo;</div>}
                    <ul style={{ margin: "0 0 8px", paddingLeft: 18, lineHeight: 1.6 }}>
                      {(x.checks || []).map((c: any, j: number) => (
                        <li key={j} style={{ color: c.ok ? "var(--vn-ink-body)" : "var(--vn-bad)" }}>{c.ok ? "✓ " : "✗ "}{c.check}</li>
                      ))}
                    </ul>
                    {x.tools?.length > 0 && <div style={{ fontFamily: MONO, fontSize: 11.5, color: "var(--vn-ink-muted)" }}>tools: {x.tools.join(", ")}</div>}
                    {x.grounding?.checked > 0 && <div style={{ fontFamily: MONO, fontSize: 11.5, color: "var(--vn-ink-muted)" }}>
                      grounding: {x.grounding.supported}/{x.grounding.checked} claims in the sources</div>}
                    {x.answer && <div style={{ marginTop: 8, padding: "10px 12px", background: "var(--vn-sunken)", borderRadius: 8 }}><Markdown text={x.answer} /></div>}
                    {x.error && <div style={{ color: "var(--vn-bad)", marginTop: 6 }}>{x.error}</div>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// --------------------------------------------------------------------- view

const TOOL_LABEL: Record<string, string> = {
  search_knowledge: "Searched the brain", web_search: "Searched the web", brand_profile: "Read the brand profile", whats_new: "Checked what's new",
  competitor_patterns: "Read competitor patterns", list_runs: "Listed runs", get_run: "Opened a run",
  learning_overview: "Read the learning loop", add_company: "Started the website analyzer",
  analysis_status: "Checked the analysis", analyse_competitors: "Started the competitor analysis",
  notion_connect: "Made a Notion link", propose_action: "Prepared an action", list_companies: "Listed companies",
  set_post_cadence: "Set a cron", find_campaigns: "Started a campaign search",
  study_brand: "Studying a company",
};

function istWhen(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata", month: "long", day: "numeric", year: "numeric",
    hour: "numeric", minute: "2-digit", hour12: true,
  }).format(d) + " IST";
}

const WORK_LABEL: Record<string, string> = {
  gtm_cycle: "Posts",
  research_collect: "Headlines and competitor posts",
  campaigns_refresh: "Campaigns",
  trend_scan: "Trends",
  ideas_panel: "Ideas",
  memes_panel: "Memes",
  github_commits: "GitHub",
  notion_sync: "Notion",
  brain_watch: "Public listening",
  metrics_collect: "Published-post results",
  ops_watch: "Health check",
};

const WORK_LANDS: Record<string, string> = {
  gtm_cycle: "Post History",
  research_collect: "Scraped Intelligence",
  campaigns_refresh: "Campaigns",
  trend_scan: "Scraped Intelligence",
  ideas_panel: "Post History",
  memes_panel: "Telegram",
  github_commits: "the brand brain",
  notion_sync: "the brand brain",
  brain_watch: "the brand brain",
  metrics_collect: "Learning",
  ops_watch: "Telegram when something breaks",
};

const CRON_BADGE: Record<string, string> = {
  live: "Cron set",
  auth: "Saved · sign-in needed",
  clock: "On the 2-minute clock",
  local: "Saved on this machine",
  failed: "Saved · cron failed",
  stopped: "Stopped",
};

const CRON_TELL: Record<string, { stop: string; start: string }> = {
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

function WorkRail({ vm }: { vm: MissionVM }) {
  const [clock, setClock] = useState<any>(null);
  const [shelves, setShelves] = useState<any[]>([]);
  const [job, setJob] = useState<any>(null);
  const [busy, setBusy] = useState("");
  const [note, setNote] = useState("");
  const load = useCallback(async () => {
    try {
      const [s, c] = await Promise.all([
        fetch("/api/scheduler", { cache: "no-store" }).then((r) => r.json()).catch(() => null),
        fetch("/api/gtm/campaigns", { cache: "no-store" }).then((r) => r.json()).catch(() => null),
      ]);
      setClock(s);
      setShelves(Array.isArray(c?.shelves) ? c.shelves : []);
      setJob(c?.job || null);
    } catch { /* the chat still works */ }
  }, []);
  useEffect(() => {
    let stop = false;
    const tick = async () => {
      if (!stop) await load();
      if (!stop) setTimeout(tick, 8000);
    };
    tick();
    return () => { stop = true; };
  }, [load]);
  const searching = job?.state === "running";
  const cards = ((clock?.jobs || []) as any[]).filter((j) => {
    if (!WORK_LABEL[j.job]) return false;
    if (j.paused) return j.cron_state === "stopped" || Boolean(j.cron_id);
    return j.enabled !== false;
  });
  const count = cards.length + shelves.length + (searching ? 1 : 0);
  const flip = async (name: string, phrase: string) => {
    setBusy(name);
    setNote("");
    try {
      const res = await fetch("/api/scheduler", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "tell", text: phrase }),
      });
      const data = await res.json();
      const line = String(data.message || data.error || "").split("\n").find(Boolean) || "";
      setNote(data.success ? line : (line || "Could not change that cron"));
    } catch {
      setNote("Could not change that cron");
    }
    setBusy("");
    await load();
  };
  const until = typeof clock?.until === "string" ? clock.until : "";
  const left = typeof clock?.posts_left === "number" ? clock.posts_left : null;
  return (
    <aside className="assistant-work" style={{ width: 340, flex: "0 0 340px", borderLeft: "1px solid var(--vn-line)", display: "flex", flexDirection: "column", background: "var(--vn-sunken)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "16px 16px 12px" }}>
        <div style={{ fontWeight: 700, fontSize: 16, color: "var(--vn-ink)" }}>Automations <span style={{ color: "var(--vn-ink-muted)", fontWeight: 500 }}>({count})</span></div>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "0 12px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
        {cards.map((item) => {
          const stopped = Boolean(item.paused) || item.cron_state === "stopped";
          const phrase = CRON_TELL[item.job];
          return (
          <div key={item.job} style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 14, padding: "14px 14px 12px", opacity: stopped ? 0.72 : 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
              <div style={{ fontWeight: 700, fontSize: 14.5, color: "var(--vn-ink)" }}>{WORK_LABEL[item.job]} every {item.interval}</div>
              <span style={{ fontSize: 11, fontWeight: 700, padding: "3px 8px", borderRadius: 99, background: stopped ? "var(--vn-sunken)" : "var(--vn-ok-soft)", color: stopped ? "var(--vn-ink-muted)" : "var(--vn-ok)" }}>{stopped ? "Stopped" : (CRON_BADGE[item.cron_state] || "Active")}</span>
            </div>
            {item.cron_id && (
              <div style={{ fontFamily: MONO, fontSize: 11.5, color: "var(--vn-ink-muted)", marginTop: 8 }}>
                {item.cron_id}{item.cron ? " · " + item.cron : ""}
              </div>
            )}
            {item.job === "gtm_cycle" && !stopped && (
              <div style={{ fontSize: 13, color: "var(--vn-ink-body)", marginTop: 10, lineHeight: 1.45 }}>
                {left ? left + " posts left. Each one reads the newest scrape." : "When: " + (until ? istWhen(until) : "until you say stop")}
              </div>
            )}
            <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", marginTop: 6, lineHeight: 1.45 }}>
              Shows in {item.lands || WORK_LANDS[item.job] || "the dashboard"}.
            </div>
            {item.last_run && item.last_run !== "Never" && (
              <div style={{ fontSize: 12, color: "var(--vn-ink-faint)", marginTop: 8 }}>Last activity: {istWhen(item.last_run)}</div>
            )}
            {phrase && (
              <button type="button" disabled={busy === item.job}
                onClick={() => flip(item.job, stopped ? phrase.start : phrase.stop)}
                style={{ marginTop: 12, width: "100%", borderRadius: 10, padding: "8px 10px", cursor: busy === item.job ? "wait" : "pointer", fontWeight: 700, fontSize: 13, border: "1px solid " + (stopped ? "var(--vn-line)" : "var(--vn-bad)"), background: stopped ? "var(--vn-surface)" : "transparent", color: stopped ? "var(--vn-ink)" : "var(--vn-bad)" }}>
                {busy === item.job ? (stopped ? "Starting…" : "Stopping…") : (stopped ? "Start again" : "Stop cron")}
              </button>
            )}
          </div>
          );
        })}
        {note && <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", lineHeight: 1.45, padding: "0 4px" }}>{note}</div>}
        {searching && (
          <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 14, padding: "14px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
              <div style={{ fontWeight: 700, fontSize: 14.5, color: "var(--vn-ink)" }}>Searching {job.source || "campaigns"}</div>
              <span style={{ fontSize: 11, fontWeight: 700, padding: "3px 8px", borderRadius: 99, background: "var(--vn-ok-soft)", color: "var(--vn-ok)" }}>Active</span>
            </div>
            <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", marginTop: 8 }}>{job.query || "Reading the live listing."}</div>
          </div>
        )}
        {shelves.map((s: any) => (
          <button key={(s.source_input || s.source) + (s.scraped_at || "")} onClick={() => (vm as any).goCampaigns?.()}
                  style={{ textAlign: "left", background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 14, padding: "14px", cursor: "pointer", color: "inherit" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
              <div style={{ fontWeight: 700, fontSize: 14.5, color: "var(--vn-ink)" }}>{s.source_input || s.source || "Campaigns"}</div>
              <span style={{ fontSize: 11, fontWeight: 700, color: "var(--vn-ok)" }}>{s.count || (s.campaigns || []).length}</span>
            </div>
            <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", marginTop: 8, lineHeight: 1.45 }}>{s.query}</div>
          </button>
        ))}
        {count === 0 && <div style={{ fontSize: 13, color: "var(--vn-ink-muted)", lineHeight: 1.5, padding: "4px 4px" }}>Nothing on a cron. Say the job and the gap: competitor Twitter every 5 minutes, or campaigns every 5 minutes. A post still needs 20 minutes.</div>}
      </div>
    </aside>
  );
}

function CheckLine({ q, k, v, bad }: { q: string; k: string; v: string; bad?: boolean }) {
  return (
    <div style={{ display: "flex", gap: 10, alignItems: "baseline", padding: "4px 0", fontSize: 15, lineHeight: 1.45 }}>
      <span style={{ color: bad ? "var(--vn-bad)" : "var(--vn-ok)", fontWeight: 700, width: 16 }}>{bad ? "×" : "✓"}</span>
      <span style={{ fontFamily: MONO, fontSize: 12, color: "var(--vn-ink-muted)", width: 26 }}>{q}</span>
      <span style={{ color: "var(--vn-ink-muted)" }}>{k}</span>
      <span style={{ color: "var(--vn-ink-faint)" }}>→</span>
      <span style={{ color: "var(--vn-ink)", fontWeight: 600 }}>{v}</span>
    </div>
  );
}

function ToolSteps({ tools }: { tools: Tool[] }) {
  const cadence = tools.find((t) => t.name === "set_post_cadence");
  const camps = tools.find((t) => t.name === "find_campaigns");
  const rest = tools.filter((t) => t !== cadence && t !== camps);
  return (
    <div style={{ marginBottom: 8 }}>
      {cadence && (
        <>
          {cadence.summary.split("\n").filter(Boolean).map((line, i) => (
            <CheckLine key={i} q={"Q" + (i + 1)} k="Set" v={line.replace(/\.$/, "")} bad={cadence.summary.startsWith("failed")} />
          ))}
          {!cadence.summary.startsWith("failed") && (
            <div style={{ display: "flex", gap: 8, alignItems: "center", margin: "8px 0 10px", fontSize: 14.5 }}>
              <span style={{ color: "var(--vn-ok)", fontWeight: 700 }}>✓</span>
              <span>Thanks. I have what I need to continue.</span>
            </div>
          )}
          {!cadence.summary.startsWith("failed") && (
            <div style={{ border: "1px solid var(--vn-line)", borderRadius: 12, padding: "12px 14px", background: "var(--vn-sunken)", fontSize: 14, lineHeight: 1.55 }}>
              {cadence.summary.split("\n").filter(Boolean).map((line, i) => <div key={i}>{line}</div>)}
            </div>
          )}
        </>
      )}
      {camps && (
        <>
          <CheckLine q="Q1" k="What" v="Campaigns" bad={camps.summary.startsWith("failed")} />
          <CheckLine q="Q2" k="Where" v={camps.summary.replace(/^searching\s+/i, "")} bad={camps.summary.startsWith("failed")} />
          {!camps.summary.startsWith("failed") && (
            <div style={{ display: "flex", gap: 8, alignItems: "center", margin: "8px 0 4px", fontSize: 14.5 }}>
              <span style={{ color: "var(--vn-ok)", fontWeight: 700 }}>✓</span>
              <span>Thanks. I have what I need to continue.</span>
            </div>
          )}
        </>
      )}
      {rest.map((t, j) => (
        <div key={j} style={{ display: "flex", gap: 8, alignItems: "baseline", padding: "3px 0", fontSize: 14.5, lineHeight: 1.45 }}>
          <span style={{ color: t.summary.startsWith("failed") ? "var(--vn-bad)" : "var(--vn-ok)", fontWeight: 700 }}>{t.summary.startsWith("failed") ? "×" : "✓"}</span>
          <span style={{ color: "var(--vn-ink)" }}>{TOOL_LABEL[t.name] || t.name}</span>
          <span style={{ color: "var(--vn-ink-muted)" }}>→ {t.summary}</span>
        </div>
      ))}
    </div>
  );
}

export function Assistant({ vm }: { vm: MissionVM }) {
  // A client link talks about its own company only: no other companies, no
  // onboarding, no model checks (those are the owner's).
  const [tenants, setTenants] = useState<string[]>([]);
  const [names, setNames] = useState<Record<string, string>>({});
  const [tenant, setTenant] = useState<string>("");
  const [, setThreads] = useState<Thread[]>([]);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingThread, setLoadingThread] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const scroller = useRef<HTMLDivElement>(null);
  const box = useRef<HTMLTextAreaElement>(null);
  const abort = useRef<AbortController | null>(null);

  useEffect(() => {
    fetch("/api/gtm/brain", { cache: "no-store" }).then((r) => r.json()).then((d) => {
      const ts: string[] = d.tenants || [];
      setTenants(ts);
      let pick = ts[0] || "";
      try { pick = localStorage.getItem("vn_assistant_tenant") || pick; } catch { /* */ }
      if (!ts.includes(pick)) pick = ts[0] || "";
      setTenant(pick);
      if (d.tenant && d.profile?.company?.name) setNames((n) => ({ ...n, [d.tenant]: d.profile.company.name }));
    }).catch((e) => setErr(String(e)));
  }, []);

  const loadThreads = useCallback(async (t: string) => {
    try {
      const d = await (await fetch("/api/assistant/threads?tenant=" + t, { cache: "no-store" })).json();
      setThreads(d.ok ? d.threads : []);
    } catch { setThreads([]); }
  }, []);

  const openThread = useCallback(async (t: string, id: string | null) => {
    setThreadId(id);
    try { if (id) localStorage.setItem("vn_assistant_thread_" + t, id); else localStorage.removeItem("vn_assistant_thread_" + t); } catch { /* */ }
    if (!id) { setMsgs([]); return; }
    setLoadingThread(true);
    try {
      const d = await (await fetch("/api/assistant/threads?tenant=" + t + "&id=" + id, { cache: "no-store" })).json();
      setMsgs(d.ok && d.thread ? d.thread.messages : []);
      if (!d.ok) setThreadId(null);
    } finally { setLoadingThread(false); }
  }, []);

  useEffect(() => {
    if (!tenant) return;
    try { localStorage.setItem("vn_assistant_tenant", tenant); } catch { /* */ }
    fetch("/api/gtm/brain?tenant=" + tenant, { cache: "no-store" }).then((r) => r.json())
      .then((d) => d.profile?.company?.name && setNames((n) => ({ ...n, [tenant]: d.profile.company.name }))).catch(() => {});
    loadThreads(tenant);
    let last: string | null = null;
    try { last = localStorage.getItem("vn_assistant_thread_" + tenant); } catch { /* */ }
    openThread(tenant, last);
  }, [tenant, loadThreads, openThread]);

  useEffect(() => { scroller.current?.scrollTo({ top: scroller.current.scrollHeight }); }, [msgs]);

  const pick = useCallback((t: string) => {
    setTenants((ts) => (ts.includes(t) ? ts : [...ts, t]));
    setTenant(t);
  }, []);

  const send = async (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || busy || !tenant) return;
    setInput("");
    setErr(null);
    setMsgs((m) => [...m, { role: "user", text: q }, { role: "assistant", text: "", tools: [], cards: [], pending: true }]);
    setBusy(true);
    const ctl = new AbortController();
    abort.current = ctl;
    const update = (f: (m: Msg) => Msg) => setMsgs((all) => { const c = [...all]; c[c.length - 1] = f({ ...c[c.length - 1] }); return c; });
    try {
      const r = await fetch("/api/assistant", {
        method: "POST", headers: { "Content-Type": "application/json" }, signal: ctl.signal,
        body: JSON.stringify({ tenant, text: q, thread_id: threadId }),
      });
      if (!r.ok || !r.body) {
        const j = await r.json().catch(() => ({}));
        throw new Error(j.error || "HTTP " + r.status);
      }
      const reader = r.body.getReader();
      const dec = new TextDecoder();
      let buf = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        let i;
        while ((i = buf.indexOf("\n\n")) >= 0) {
          const chunk = buf.slice(0, i); buf = buf.slice(i + 2);
          if (!chunk.startsWith("data: ")) continue;
          const ev = JSON.parse(chunk.slice(6));
          if (ev.type === "thread") {
            if (ev.thread_id !== threadId) {
              setThreadId(ev.thread_id);
              try { localStorage.setItem("vn_assistant_thread_" + tenant, ev.thread_id); } catch { /* */ }
            }
          } else if (ev.type === "tool") update((m) => ({ ...m, tools: [...(m.tools || []), { name: ev.name, summary: ev.summary }] }));
          else if (ev.type === "card") update((m) => ({ ...m, cards: [...(m.cards || []), ev.card] }));
          else if (ev.type === "delta") update((m) => ({ ...m, text: (m.text || "") + ev.text }));
          else if (ev.type === "grounding") update((m) => ({ ...m, grounding: { checked: ev.checked, supported: ev.supported, flagged: ev.flagged, note: ev.note } }));
          else if (ev.type === "error") update((m) => ({ ...m, error: ev.error }));
        }
      }
    } catch (e: any) {
      if (e?.name === "AbortError") update((m) => ({ ...m, stopped: true }));
      else update((m) => ({ ...m, error: String(e?.message || e) }));
    } finally {
      update((m) => ({ ...m, pending: false }));
      setBusy(false);
      abort.current = null;
      loadThreads(tenant);
      box.current?.focus();
    }
  };

  const stop = () => abort.current?.abort();

  const name = names[tenant] || tenant;
  const planned = (m: Msg) => (m.tools || []).some((t) => (t.name === "set_post_cadence" || t.name === "find_campaigns") && !t.summary.startsWith("failed"));

  return (
    <section className="vanna-section" style={{ paddingBottom: 12 }}>
      <div className="vanna-card assistant-shell" style={{ display: "flex", padding: 0, height: "calc(100dvh - 150px)", minHeight: 520, overflow: "hidden", background: "var(--vn-surface)", color: "var(--vn-ink)" }}>
        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", background: "var(--vn-surface)" }}>
          <div ref={scroller} style={{ flex: 1, overflowY: "auto", padding: "28px 22px 12px" }}>
            <div style={{ maxWidth: 720, margin: "0 auto" }}>
              {loadingThread && <div style={{ padding: "24px 0" }}><span className="vn-skel" style={{ width: 260, height: 12 }} /></div>}
              {!loadingThread && msgs.length === 0 && (
                <div style={{ padding: "48px 0 12px", color: "var(--vn-ink-muted)", fontSize: 15, lineHeight: 1.5 }}>
                  One line does it. Scrape every 5 minutes and make 10 posts. Add memes, ideas, GitHub, or Notion in the same line.
                </div>
              )}
              {msgs.map((m, i) => m.role === "user" ? (
                <div key={i} style={{ display: "flex", justifyContent: "flex-end", margin: "16px 0" }}>
                  <div style={{ background: "var(--vn-raised)", borderRadius: 14, padding: "10px 14px", maxWidth: "80%", fontSize: 15, lineHeight: 1.55, whiteSpace: "pre-wrap", color: "var(--vn-ink)" }}>{m.text}</div>
                </div>
              ) : (
                <div key={i} style={{ margin: "16px 0", color: "var(--vn-ink)" }}>
                  {(m.tools || []).length > 0 && <ToolSteps tools={m.tools || []} />}
                  {m.text && !planned(m) && <div style={{ marginTop: (m.tools || []).length ? 8 : 0 }}><Markdown text={m.text} /></div>}
                  {m.grounding && !planned(m) && <Grounding g={m.grounding} />}
                  {(m.cards || []).filter((c) => c.type !== "run").map((c, j) => <CardView key={j} c={c} vm={vm} onPick={pick} tenant={tenant} threadId={threadId} />)}
                  {(m.cards || []).some((c) => c.type === "run") && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
                      {Array.from(new Set((m.cards || []).filter((c) => c.type === "run").map((c) => c.run_id as string))).map((rid) => (
                        <button key={rid} style={{ ...btn, fontFamily: MONO, fontSize: 11.5, padding: "4px 8px" }}
                                onClick={() => (vm as any).openRun(rid)}>{rid}</button>
                      ))}
                    </div>
                  )}
                  {m.pending && !m.text && !(m.tools || []).length && (
                    <div style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 6 }} aria-label="thinking">
                      <span className="vn-skel" style={{ width: 120, height: 10, borderRadius: 5 }} />
                      <span style={{ fontSize: 12, color: "var(--vn-ink-faint)" }}>thinking…</span>
                    </div>
                  )}
                  {m.stopped && <div style={{ fontSize: 12, color: "var(--vn-ink-faint)", marginTop: 4 }}>Stopped.</div>}
                  {m.error && <div style={{ fontSize: 13, color: "var(--vn-bad)", marginTop: 6 }}>{m.error}</div>}
                </div>
              ))}
            </div>
          </div>

          <div style={{ padding: "8px 16px 16px" }}>
            <div style={{ maxWidth: 760, margin: "0 auto" }}>
              <div style={{ display: "flex", gap: 8, alignItems: "flex-end", background: "var(--vn-sunken)", border: "1px solid var(--vn-line)", borderRadius: 16, padding: 6 }}>
                <textarea ref={box} value={input} rows={1} disabled={!tenant}
                          onChange={(e) => setInput(e.target.value)}
                          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                          placeholder="Ask anything"
                          style={{ flex: 1, resize: "none", minHeight: 46, maxHeight: 160, background: "transparent", border: "none",
                                   padding: "12px 12px", fontSize: 15, lineHeight: 1.45, fontFamily: "inherit", color: "var(--vn-ink)", outline: "none" }} />
                {busy ? (
                  <button style={{ background: "transparent", color: "var(--vn-ink)", border: "1px solid var(--vn-line-strong)", borderRadius: 12, padding: "12px 16px", fontWeight: 700, cursor: "pointer" }} onClick={stop}>Stop</button>
                ) : (
                  <button style={{ background: "var(--vn-cta)", color: "var(--vn-on-accent)", border: "none", borderRadius: 12, padding: "12px 20px", fontWeight: 700, fontSize: 15, cursor: input.trim() && tenant ? "pointer" : "default", opacity: input.trim() && tenant ? 1 : 0.45 }}
                          disabled={!input.trim() || !tenant} onClick={() => send()}>Ask</button>
                )}
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 10, alignItems: "center" }}>
                {tenants.length > 1 ? (
                  <select value={tenant} onChange={(e) => setTenant(e.target.value)} disabled={busy} aria-label="Company"
                          style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-body)", background: "var(--vn-raised)", border: "1px solid var(--vn-line)", borderRadius: 99, padding: "4px 10px" }}>
                    {tenants.map((t) => <option key={t} value={t}>{names[t] || t}</option>)}
                  </select>
                ) : (
                  <span style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-body)", border: "1px solid var(--vn-line)", borderRadius: 99, padding: "4px 10px", background: "var(--vn-raised)" }}>{name || "Company"}</span>
                )}
              </div>
              {err && <div style={{ marginTop: 6, fontSize: 12.5, color: "var(--vn-bad)" }}>{err}</div>}
            </div>
          </div>
        </div>
        <WorkRail vm={vm} />
      </div>
    </section>
  );
}
