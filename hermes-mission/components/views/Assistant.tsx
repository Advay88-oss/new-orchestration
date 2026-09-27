"use client";

/**
 * The home screen: a chat about one company at a time.
 *
 * Pick a company, ask anything (answers come from its brand brain, with
 * sources), add a new company from its website, connect its Notion. The
 * assistant (pipeline/assistant) shows what it is doing — each tool it calls
 * — and returns cards: an analysis running, a Notion button, an action for
 * the owner to confirm, a run to open. It never launches, approves or
 * publishes anything itself.
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

type Card = { type: string; [k: string]: any };
type Tool = { name: string; summary: string };
type Msg = { role: "user" | "assistant"; text: string; tools?: Tool[]; cards?: Card[]; error?: string; pending?: boolean };

const STORE = (t: string) => "vn_assistant_" + t;

function load(t: string): Msg[] {
  try { return JSON.parse(localStorage.getItem(STORE(t)) || "[]"); } catch { return []; }
}
function save(t: string, m: Msg[]) {
  try { localStorage.setItem(STORE(t), JSON.stringify(m.filter((x) => !x.pending).slice(-60))); } catch { /* private mode */ }
}

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

function ActionCard({ c, vm }: { c: Card; vm: MissionVM }) {
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
      setState(j.success || j.ok ? "done" : "failed: " + (j.error || r.status));
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

function CardView({ c, vm, onPick }: { c: Card; vm: MissionVM; onPick: (t: string) => void }) {
  if (c.type === "analysis") return <AnalysisCard c={c} vm={vm} onPick={onPick} />;
  if (c.type === "competitors") return <CompetitorsCard c={c} />;
  if (c.type === "notion") return <NotionCard c={c} />;
  if (c.type === "action") return <ActionCard c={c} vm={vm} />;
  if (c.type === "run") return <RunCard c={c} vm={vm} />;
  return null;
}

// --------------------------------------------------------------------- view

const TOOL_LABEL: Record<string, string> = {
  search_knowledge: "Searched the brain", brand_profile: "Read the brand profile", whats_new: "Checked what's new",
  competitor_patterns: "Read competitor patterns", list_runs: "Listed runs", get_run: "Opened a run",
  learning_overview: "Read the learning loop", add_company: "Started the website analyzer",
  analysis_status: "Checked the analysis", analyse_competitors: "Started the competitor analysis",
  notion_connect: "Made a Notion link", propose_action: "Prepared an action", list_companies: "Listed companies",
};

export function Assistant({ vm }: { vm: MissionVM }) {
  const [tenants, setTenants] = useState<string[]>([]);
  const [names, setNames] = useState<Record<string, string>>({});
  const [tenant, setTenant] = useState<string>("");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const scroller = useRef<HTMLDivElement>(null);
  const box = useRef<HTMLTextAreaElement>(null);

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

  useEffect(() => {
    if (!tenant) return;
    setMsgs(load(tenant));
    try { localStorage.setItem("vn_assistant_tenant", tenant); } catch { /* */ }
    fetch("/api/gtm/brain?tenant=" + tenant, { cache: "no-store" }).then((r) => r.json())
      .then((d) => d.profile?.company?.name && setNames((n) => ({ ...n, [tenant]: d.profile.company.name }))).catch(() => {});
  }, [tenant]);

  useEffect(() => { scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" }); }, [msgs]);

  const pick = useCallback((t: string) => {
    setTenants((ts) => (ts.includes(t) ? ts : [...ts, t]));
    setTenant(t);
  }, []);

  const send = async (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || busy || !tenant) return;
    setInput("");
    setErr(null);
    const history = [...msgs, { role: "user" as const, text: q }];
    const reply: Msg = { role: "assistant", text: "", tools: [], cards: [], pending: true };
    setMsgs([...history, reply]);
    setBusy(true);
    const update = (f: (m: Msg) => Msg) => setMsgs((all) => { const c = [...all]; c[c.length - 1] = f({ ...c[c.length - 1] }); return c; });
    try {
      const r = await fetch("/api/assistant", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant, messages: history.map((m) => ({ role: m.role, text: m.text })) }),
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
          if (ev.type === "tool") update((m) => ({ ...m, tools: [...(m.tools || []), { name: ev.name, summary: ev.summary }] }));
          else if (ev.type === "card") update((m) => ({ ...m, cards: [...(m.cards || []), ev.card] }));
          else if (ev.type === "text") update((m) => ({ ...m, text: ev.text }));
          else if (ev.type === "error") update((m) => ({ ...m, error: ev.error }));
        }
      }
    } catch (e: any) {
      update((m) => ({ ...m, error: String(e?.message || e) }));
    } finally {
      update((m) => ({ ...m, pending: false }));
      setBusy(false);
      setMsgs((all) => { save(tenant, all); return all; });
      box.current?.focus();
    }
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
      <div className="vanna-card" style={{ display: "flex", flexDirection: "column", padding: 0, height: "calc(100dvh - 170px)", minHeight: 480 }}>
        {/* header: company + add */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "14px 18px", borderBottom: "1px solid var(--vn-line)", flexWrap: "wrap" }}>
          <span style={{ fontSize: 12.5, color: "var(--vn-ink-muted)" }}>Company</span>
          <select value={tenant} onChange={(e) => setTenant(e.target.value)}
                  style={{ background: "var(--vn-sunken)", border: "1px solid var(--vn-line-strong)", borderRadius: 6, padding: "6px 10px", fontSize: 13.5, color: "var(--vn-ink)" }}>
            {tenants.length === 0 && <option value="">no companies yet</option>}
            {tenants.map((t) => <option key={t} value={t}>{names[t] || t}</option>)}
          </select>
          <button style={btn} onClick={addCompany}>+ Add company</button>
          <span style={{ flex: 1 }} />
          {msgs.length > 0 && (
            <button style={{ ...btn, border: "none", color: "var(--vn-ink-muted)" }} disabled={busy}
                    onClick={() => { setMsgs([]); save(tenant, []); }}>New chat</button>
          )}
        </div>

        {/* messages */}
        <div ref={scroller} style={{ flex: 1, overflowY: "auto", padding: "20px 18px" }}>
          <div style={{ maxWidth: 780, margin: "0 auto" }}>
            {msgs.length === 0 && (
              <div style={{ padding: "32px 0" }}>
                <h2 style={{ marginBottom: 8 }}>Ask about {name || "a company"}</h2>
                <p style={{ maxWidth: "60ch" }}>
                  Answers come from {name || "the company"}&rsquo;s brand brain, with their sources: docs, Notion, the knowledge pack,
                  runs and what the agents learned. You can also add a company or connect its Notion from here.
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
                  <div key={j} style={{ fontFamily: MONO, fontSize: 11.5, color: "var(--vn-ink-muted)", margin: "2px 0" }}>
                    {TOOL_LABEL[t.name] || t.name} · {t.summary}
                  </div>
                ))}
                {m.text && <div style={{ marginTop: (m.tools || []).length ? 8 : 0 }}><Markdown text={m.text} /></div>}
                {(m.cards || []).filter((c) => c.type !== "run").map((c, j) => <CardView key={j} c={c} vm={vm} onPick={pick} />)}
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
                {m.error && <div style={{ fontSize: 13, color: "var(--vn-bad)", marginTop: 6 }}>{m.error}</div>}
              </div>
            ))}
          </div>
        </div>

        {/* composer */}
        <div style={{ borderTop: "1px solid var(--vn-line)", padding: "12px 18px" }}>
          <div style={{ maxWidth: 780, margin: "0 auto", display: "flex", gap: 8, alignItems: "flex-end" }}>
            <textarea ref={box} value={input} rows={1} disabled={!tenant}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                      placeholder={tenant ? "Ask about " + name + ", or say “add acme.com”…" : "Add a company to begin"}
                      style={{ flex: 1, resize: "none", minHeight: 44, maxHeight: 180, background: "var(--vn-sunken)", border: "1px solid var(--vn-line-strong)",
                               borderRadius: 10, padding: "11px 12px", fontSize: 14.5, lineHeight: 1.45, fontFamily: "inherit", color: "var(--vn-ink)" }} />
            <button style={{ ...cta, padding: "11px 16px" }} disabled={busy || !input.trim() || !tenant} onClick={() => send()}>
              {busy ? "…" : "Send"}
            </button>
          </div>
          {err && <div style={{ maxWidth: 780, margin: "6px auto 0", fontSize: 12.5, color: "var(--vn-bad)" }}>{err}</div>}
        </div>
      </div>
    </section>
  );
}
