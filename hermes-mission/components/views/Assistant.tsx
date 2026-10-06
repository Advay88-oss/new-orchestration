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
import { useTenant } from "@/lib/tenant";
import { Badge } from "../Sidebar";
import { HeraldMark, IconArrowUp, IconStop } from "../icons";

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
        {state === "done" && c.action === "launch_run" && <span style={{ fontSize: 12.5, color: "var(--vn-ink-muted)" }}>Started. It shows up in Posts.</span>}
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


const SUGGEST: { label: string; fill?: string; send?: string; autopilot?: boolean }[] = [
  { label: "Draft a post", fill: "Draft a post about " },
  { label: "What’s new this week", send: "What's new this week?" },
  { label: "Change the schedule", autopilot: true },
  { label: "Study a brand", fill: "Study the brand " },
  { label: "Find campaigns", fill: "Find campaigns on Galxe about " },
];

function greeting(): string {
  const h = new Date().getHours();
  return h < 5 ? "Good evening" : h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
}

function useOwnerName(): string {
  const [name, setName] = useState("");
  useEffect(() => {
    try { setName(localStorage.getItem("vn_owner_name") || ""); } catch { /* */ }
    const on = (e: Event) => setName(String((e as CustomEvent).detail || ""));
    window.addEventListener("vn:owner-name", on);
    return () => window.removeEventListener("vn:owner-name", on);
  }, []);
  return name;
}

function Composer({ value, onChange, onSend, onStop, busy, disabled, company, placeholder, boxRef, big }: {
  value: string; onChange: (v: string) => void; onSend: () => void; onStop: () => void; busy: boolean; disabled: boolean;
  company: { id: string; name: string } | null; placeholder: string; boxRef: React.RefObject<HTMLTextAreaElement>; big?: boolean;
}) {
  const ready = Boolean(value.trim()) && !disabled;
  return (
    <div className="hd-composer" style={{ padding: big ? "8px 10px 10px" : "6px 8px 8px" }}>
      <textarea ref={boxRef} value={value} rows={big ? 2 : 1} disabled={disabled}
                onChange={(e) => onChange(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSend(); } }}
                placeholder={placeholder}
                style={{ width: "100%", resize: "none", minHeight: big ? 64 : 40, maxHeight: 200, background: "transparent", border: "none",
                         padding: big ? "12px 12px 6px" : "10px 10px 4px", fontSize: big ? 16.5 : 15, lineHeight: 1.5, fontFamily: "inherit", color: "var(--vn-ink)" }} />
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, padding: "0 2px 0 6px" }}>
        {company ? (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 7, border: "1px solid var(--vn-line)", borderRadius: 8, padding: "4px 10px 4px 5px", fontSize: 13.5, color: "var(--vn-ink-body)", background: "var(--vn-surface)" }}>
            <Badge id={company.id} name={company.name} size={18} />{company.name}
          </span>
        ) : <span />}
        {busy ? (
          <button onClick={onStop} aria-label="Stop" className="hd-icon-btn" style={{ width: 38, height: 38, borderRadius: 11, background: "var(--vn-raised)", color: "var(--vn-ink)" }}><IconStop /></button>
        ) : (
          <button onClick={onSend} disabled={!ready} aria-label="Send"
                  style={{ width: 38, height: 38, borderRadius: 11, border: "none", display: "inline-flex", alignItems: "center", justifyContent: "center",
                           background: ready ? "var(--vn-cta)" : "var(--vn-raised)", color: ready ? "var(--vn-on-accent)" : "var(--vn-ink-muted)", cursor: ready ? "pointer" : "default" }}>
            <IconArrowUp />
          </button>
        )}
      </div>
    </div>
  );
}

export function Assistant({ vm, newChat = 0, onAutopilot }: { vm: MissionVM; newChat?: number; onAutopilot?: () => void }) {
  const [company, , pickCompany] = useTenant();
  const tenant = company?.id || "";
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
  const owner = useOwnerName();

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
    } catch (e) { setErr(String(e)); } finally { setLoadingThread(false); }
  }, []);

  useEffect(() => {
    if (!tenant) return;
    loadThreads(tenant);
    let last: string | null = null;
    try { last = localStorage.getItem("vn_assistant_thread_" + tenant); } catch { /* */ }
    openThread(tenant, last);
  }, [tenant, loadThreads, openThread]);

  // "New chat" from the sidebar or the palette.
  useEffect(() => {
    if (!newChat || !tenant) return;
    abort.current?.abort();
    openThread(tenant, null);
    setInput("");
    setTimeout(() => box.current?.focus(), 0);
  }, [newChat]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { scroller.current?.scrollTo({ top: scroller.current.scrollHeight }); }, [msgs]);

  const pick = useCallback((t: string) => pickCompany(t), [pickCompany]);

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
          } else if (ev.type === "tool") {
            update((m) => ({ ...m, tools: [...(m.tools || []), { name: ev.name, summary: ev.summary }] }));
            if (ev.name === "set_post_cadence") window.dispatchEvent(new Event("vn:autopilot"));
          }
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
  const name = company?.name || tenant;
  const planned = (m: Msg) => (m.tools || []).some((t) => (t.name === "set_post_cadence" || t.name === "find_campaigns") && !t.summary.startsWith("failed"));
  const empty = !loadingThread && msgs.length === 0;

  const suggest = (s: typeof SUGGEST[number]) => {
    if (s.autopilot) { onAutopilot?.(); return; }
    if (s.send) { send(s.send); return; }
    setInput(s.fill || "");
    setTimeout(() => { const b = box.current; if (b) { b.focus(); b.setSelectionRange(b.value.length, b.value.length); } }, 0);
  };

  if (empty) {
    return (
      <section style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "24px 20px 12vh", minHeight: "calc(100dvh - 60px)" }}>
        <div className="hd-pop" style={{ width: "min(760px, 100%)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 14, marginBottom: 28 }}>
            <HeraldMark size={36} tone="accent" />
            <div className="hd-greeting" role="heading" aria-level={1}>{greeting()}{owner ? ", " + owner : ""}</div>
          </div>
          <Composer big value={input} onChange={setInput} onSend={() => send()} onStop={stop} busy={busy} disabled={!tenant}
                    company={company} boxRef={box} placeholder={"Ask anything about " + (name || "your company") + ", or tell me what to make…"} />
          <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 10, marginTop: 22 }}>
            {SUGGEST.map((s) => (
              <button key={s.label} className="hd-chip" onClick={() => suggest(s)} disabled={!tenant}>{s.label}</button>
            ))}
          </div>
          {err && <div style={{ marginTop: 12, fontSize: 13, color: "var(--vn-bad)", textAlign: "center" }}>{err}</div>}
        </div>
      </section>
    );
  }

  return (
    <section style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0, height: "calc(100dvh - 60px)" }}>
      <div ref={scroller} style={{ flex: 1, overflowY: "auto", padding: "16px 20px 8px" }}>
        <div style={{ maxWidth: 760, margin: "0 auto" }}>
          {loadingThread && <div style={{ padding: "24px 0" }}><span className="vn-skel" style={{ width: 260, height: 12, borderRadius: 6 }} /></div>}
          {msgs.map((m, i) => m.role === "user" ? (
            <div key={i} style={{ display: "flex", justifyContent: "flex-end", margin: "18px 0" }}>
              <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 16, padding: "10px 15px", maxWidth: "80%", fontSize: 15, lineHeight: 1.55, whiteSpace: "pre-wrap", color: "var(--vn-ink)" }}>{m.text}</div>
            </div>
          ) : (
            <div key={i} style={{ margin: "18px 0", color: "var(--vn-ink)", display: "flex", gap: 12 }}>
              <div style={{ paddingTop: 2 }}><HeraldMark size={22} tone="accent" /></div>
              <div style={{ flex: 1, minWidth: 0 }}>
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
                {planned(m) && onAutopilot && (
                  <button className="hd-btn" style={{ marginTop: 10 }} onClick={onAutopilot}>Open Autopilot</button>
                )}
                {m.pending && !m.text && !(m.tools || []).length && (
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 4 }} aria-label="thinking">
                    <span className="vn-skel" style={{ width: 140, height: 10, borderRadius: 5 }} />
                    <span style={{ fontSize: 12.5, color: "var(--vn-ink-faint)" }}>Thinking…</span>
                  </div>
                )}
                {m.stopped && <div style={{ fontSize: 12.5, color: "var(--vn-ink-faint)", marginTop: 4 }}>Stopped.</div>}
                {m.error && <div style={{ fontSize: 13, color: "var(--vn-bad)", marginTop: 6 }}>{m.error}</div>}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div style={{ padding: "8px 20px 18px" }}>
        <div style={{ maxWidth: 760, margin: "0 auto" }}>
          <Composer value={input} onChange={setInput} onSend={() => send()} onStop={stop} busy={busy} disabled={!tenant}
                    company={company} boxRef={box} placeholder={"Reply about " + (name || "your company") + "…"} />
          {err && <div style={{ marginTop: 6, fontSize: 12.5, color: "var(--vn-bad)" }}>{err}</div>}
          <div style={{ fontSize: 11.5, color: "var(--vn-ink-faint)", textAlign: "center", marginTop: 8 }}>
            Answers come from {name || "the company"}’s sources. Nothing is published from here.
          </div>
        </div>
      </div>
    </section>
  );
}
