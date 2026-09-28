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
import { useViewer } from "@/lib/useViewer";

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

function AnalysisCard({ c, onPick, vm }: { c: Card; onPick: (t: string) => void; vm: MissionVM }) {
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
            <button style={btn} onClick={() => vm.nav.find((n) => n.id === "brain")?.go()}>Review in Brand Brain</button>
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

function ActionCard({ c, vm, tenant, threadId }: { c: Card; vm: MissionVM; tenant: string; threadId: string | null }) {
  const [state, setState] = useState<string | null>(null);
  const label: Record<string, string> = { launch_run: "Launch run", approve: "Approve", revise: "Send back for revision", kill: "Kill", approve_profile: "Open Brand Brain to approve" };
  const go = async () => {
    setState("working");
    try {
      if (c.action === "approve_profile") { vm.nav.find((n) => n.id === "brain")?.go(); return; }
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
        {state === "done" && c.action === "launch_run" && <span style={{ fontSize: 12.5, color: "var(--vn-ink-muted)" }}>Started. Follow it in Live Trace.</span>}
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
  if (c.type === "analysis") return <AnalysisCard c={c} vm={vm} onPick={onPick} />;
  if (c.type === "competitors") return <CompetitorsCard c={c} />;
  if (c.type === "notion") return <NotionCard c={c} />;
  if (c.type === "action") return <ActionCard c={c} vm={vm} tenant={tenant} threadId={threadId} />;
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
};

export function Assistant({ vm }: { vm: MissionVM }) {
  // A client link talks about its own company only: no other companies, no
  // onboarding, no model checks (those are the owner's).
  const isClient = Boolean(useViewer()?.client);
  const [tenants, setTenants] = useState<string[]>([]);
  const [names, setNames] = useState<Record<string, string>>({});
  const [tenant, setTenant] = useState<string>("");
  const [threads, setThreads] = useState<Thread[]>([]);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingThread, setLoadingThread] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const scroller = useRef<HTMLDivElement>(null);
  const box = useRef<HTMLTextAreaElement>(null);
  const abort = useRef<AbortController | null>(null);
  const [checks, setChecks] = useState(false);

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

  const remove = async (id: string) => {
    await fetch("/api/assistant/threads?tenant=" + tenant + "&id=" + id, { method: "DELETE" }).catch(() => {});
    if (id === threadId) openThread(tenant, null);
    loadThreads(tenant);
  };

  const addCompany = () => {
    setMsgs((m) => [...m, { role: "assistant", text: "Which company? Paste its website (for example `acme.com`), and optionally a short id. I'll crawl it, measure its colours and fonts, read its voice, find its competitors and draft a profile for you to approve." }]);
    setInput("Add this company: ");
    setTimeout(() => box.current?.focus(), 50);
  };

  const name = names[tenant] || tenant;
  const suggestions = [
    "What's new at " + name + " lately?",
    "Why were the last runs blocked?",
    "How do competitors post about leverage?",
    "Connect " + name + "'s Notion",
  ];

  return (
    <section className="vanna-section" style={{ paddingBottom: 24 }}>
      <div className="vanna-card" style={{ display: "flex", padding: 0, height: "calc(100dvh - 170px)", minHeight: 480, overflow: "hidden" }}>
        {/* conversations of this company */}
        <aside className="assistant-threads" style={{ width: 230, flex: "0 0 230px", borderRight: "1px solid var(--vn-line)", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: 12 }}>
            <button style={{ ...btn, width: "100%" }} disabled={busy} onClick={() => openThread(tenant, null)}>+ New chat</button>
          </div>
          <div style={{ flex: 1, overflowY: "auto", padding: "0 6px 12px" }}>
            {threads.length === 0 && <div style={{ fontSize: 12, color: "var(--vn-ink-faint)", padding: "4px 8px" }}>No conversations yet.</div>}
            {threads.map((t) => (
              <div key={t.id} className="assistant-thread" style={{ display: "flex", alignItems: "center", borderRadius: 6,
                   background: t.id === threadId ? "var(--vn-raised)" : "transparent" }}>
                <button onClick={() => !busy && openThread(tenant, t.id)} title={t.title}
                        style={{ flex: 1, minWidth: 0, textAlign: "left", border: "none", background: "transparent", padding: "7px 8px",
                                 fontSize: 12.5, color: t.id === threadId ? "var(--vn-ink)" : "var(--vn-ink-body)", cursor: "pointer",
                                 whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {t.title || "New chat"}
                </button>
                <button aria-label="Delete conversation" onClick={() => remove(t.id)}
                        style={{ border: "none", background: "transparent", color: "var(--vn-ink-faint)", cursor: "pointer", padding: "4px 8px", fontSize: 12 }}>✕</button>
              </div>
            ))}
          </div>
        </aside>

        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
          {/* header: company + add */}
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "14px 18px", borderBottom: "1px solid var(--vn-line)", flexWrap: "wrap" }}>
            <span style={{ fontSize: 12.5, color: "var(--vn-ink-muted)" }}>Company</span>
            <select value={tenant} onChange={(e) => setTenant(e.target.value)} disabled={busy}
                    style={{ background: "var(--vn-sunken)", border: "1px solid var(--vn-line-strong)", borderRadius: 6, padding: "6px 10px", fontSize: 13.5, color: "var(--vn-ink)" }}>
              {tenants.length === 0 && <option value="">no companies yet</option>}
              {tenants.map((t) => <option key={t} value={t}>{names[t] || t}</option>)}
            </select>
            {!isClient && <button style={btn} onClick={addCompany}>+ Add company</button>}
            <span style={{ flex: 1 }} />
            {!isClient && (
              <button style={{ ...btn, background: checks ? "var(--vn-raised)" : "transparent" }} onClick={() => setChecks((c) => !c)}>
                {checks ? "Back to chat" : "Checks"}
              </button>
            )}
          </div>

          {/* messages */}
          {checks && <div style={{ flex: 1, overflowY: "auto", padding: "20px 18px" }}><ChecksPanel /></div>}
          <div ref={scroller} style={{ flex: 1, overflowY: "auto", padding: "20px 18px", display: checks ? "none" : "block" }}>
            <div style={{ maxWidth: 780, margin: "0 auto" }}>
              {loadingThread && <div style={{ padding: "24px 0" }}><span className="vn-skel" style={{ width: 260, height: 12 }} /></div>}
              {!loadingThread && msgs.length === 0 && (
                <div style={{ padding: "32px 0" }}>
                  <h2 style={{ marginBottom: 8 }}>Ask about {name || "a company"}</h2>
                  <p style={{ maxWidth: "60ch" }}>
                    Answers come from {name || "the company"}&rsquo;s brand brain, with their sources, and are checked against them.
                    You can also add a company or connect its Notion from here. Conversations are kept, on every device.
                  </p>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 14 }}>
                    {suggestions.map((s) => <button key={s} style={btn} onClick={() => send(s)} disabled={!tenant || busy}>{s}</button>)}
                    <button style={btn} onClick={addCompany}>Add a new company</button>
                  </div>
                </div>
              )}
              {msgs.map((m, i) => m.role === "user" ? (
                <div key={i} style={{ display: "flex", justifyContent: "flex-end", margin: "14px 0" }}>
                  <div style={{ background: "var(--vn-raised)", borderRadius: 12, padding: "10px 14px", maxWidth: "80%", fontSize: 14.5, lineHeight: 1.55, whiteSpace: "pre-wrap" }}>{m.text}</div>
                </div>
              ) : (
                <div key={i} style={{ margin: "14px 0" }}>
                  {(m.tools || []).map((t, j) => (
                    <div key={j} style={{ fontFamily: MONO, fontSize: 11.5, color: t.summary.startsWith("failed: refused") ? "var(--vn-warn)" : "var(--vn-ink-muted)", margin: "2px 0" }}>
                      {TOOL_LABEL[t.name] || t.name} · {t.summary}
                    </div>
                  ))}
                  {m.text && <div style={{ marginTop: (m.tools || []).length ? 8 : 0 }}><Markdown text={m.text} /></div>}
                  {m.grounding && <Grounding g={m.grounding} />}
                  {(m.cards || []).filter((c) => c.type !== "run").map((c, j) => <CardView key={j} c={c} vm={vm} onPick={pick} tenant={tenant} threadId={threadId} />)}
                  {(m.cards || []).some((c) => c.type === "run") && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
                      {Array.from(new Set((m.cards || []).filter((c) => c.type === "run").map((c) => c.run_id as string))).map((rid) => (
                        <button key={rid} style={{ ...btn, fontFamily: MONO, fontSize: 11.5, padding: "4px 8px" }}
                                onClick={() => (vm as any).openRun(rid)}>{rid}</button>
                      ))}
                    </div>
                  )}
                  {m.pending && !m.text && (
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

          {/* composer */}
          <div style={{ borderTop: "1px solid var(--vn-line)", padding: "12px 18px", display: checks ? "none" : "block" }}>
            <div style={{ maxWidth: 780, margin: "0 auto", display: "flex", gap: 8, alignItems: "flex-end" }}>
              <textarea ref={box} value={input} rows={1} disabled={!tenant}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                        placeholder={tenant ? "Ask about " + name + ", or say “add acme.com”…" : "Add a company to begin"}
                        style={{ flex: 1, resize: "none", minHeight: 44, maxHeight: 180, background: "var(--vn-sunken)", border: "1px solid var(--vn-line-strong)",
                                 borderRadius: 10, padding: "11px 12px", fontSize: 14.5, lineHeight: 1.45, fontFamily: "inherit", color: "var(--vn-ink)" }} />
              {busy ? (
                <button style={{ ...btn, padding: "11px 16px" }} onClick={stop}>Stop</button>
              ) : (
                <button style={{ ...cta, padding: "11px 16px" }} disabled={!input.trim() || !tenant} onClick={() => send()}>Send</button>
              )}
            </div>
            {err && <div style={{ maxWidth: 780, margin: "6px auto 0", fontSize: 12.5, color: "var(--vn-bad)" }}>{err}</div>}
          </div>
        </div>
      </div>
    </section>
  );
}
