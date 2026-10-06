"use client";

/**
 * The Assistant: one chat per company, answered from its brand brain with
 * sources. It shows each tool it calls, streams the answer, and returns
 * cards (an action to confirm, a run to open). It never launches, approves
 * or publishes anything itself; the owner confirms every action.
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { ICheck, ILock, ISend, ISpin, IStop, Mark } from "./ui";

type Card = { type: string; [k: string]: any };
type Tool = { name: string; summary: string };
type Grounding = { checked: number; supported?: number; flagged?: { text: string; verdict: string }[]; note?: string };
type Msg = { role: "user" | "assistant"; text: string; tools?: Tool[]; cards?: Card[]; grounding?: Grounding;
             error?: string; pending?: boolean; stopped?: boolean };

const TOOL_LABEL: Record<string, string> = {
  search_knowledge: "Searched your sources", web_search: "Searched the web", brand_profile: "Read the company profile",
  whats_new: "Checked what’s new", competitor_patterns: "Read how others post", list_runs: "Listed posts", get_run: "Opened a post",
  learning_overview: "Read what’s working", add_company: "Started studying a website", analysis_status: "Checked the study",
  analyse_competitors: "Started reading competitors", notion_connect: "Made a Notion link", propose_action: "Prepared an action",
  list_companies: "Listed brands", set_post_cadence: "Updated the schedule", find_campaigns: "Searched campaigns",
  study_brand: "Added to Inspiration",
};

function inline(s: string, key: string): React.ReactNode[] {
  const out: React.ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\((https?:\/\/[^)\s]+)\))/g;
  let last = 0, m: RegExpExecArray | null, i = 0;
  while ((m = re.exec(s))) {
    if (m.index > last) out.push(s.slice(last, m.index));
    const t = m[0];
    if (t.startsWith("**")) out.push(<strong key={key + i++}>{t.slice(2, -2)}</strong>);
    else if (t.startsWith("`")) out.push(<code key={key + i++}>{t.slice(1, -1)}</code>);
    else out.push(<a key={key + i++} href={m[2]} target="_blank" rel="noopener noreferrer">{t.slice(1, t.indexOf("]"))}</a>);
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
    blocks.push(<L key={"l" + blocks.length}>{list.items.map((it, j) => <li key={j}>{inline(it, "li" + j)}</li>)}</L>);
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
    if (h) blocks.push(<h4 key={n}>{inline(h[1], "h" + n)}</h4>);
    else if (line.trim() && !/^---+$/.test(line)) blocks.push(<p key={n}>{inline(line, "p" + n)}</p>);
  });
  flush();
  return <>{blocks}</>;
}

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

function ActionCard({ c, tenant, threadId, owner, onDone }: { c: Card; tenant: string; threadId: string | null; owner: boolean; onDone: (t: string) => void }) {
  const [state, setState] = useState<"" | "working" | string>("");
  const titles: Record<string, string> = { launch_run: "Write a new post", approve: "Approve this post", revise: "Send it back for revision", kill: "Kill this post", approve_profile: "Keep this company profile" };
  const go = async () => {
    setState("working");
    try {
      if (c.action === "approve_profile") { setState("It stays in the brand brain."); return; }
      const r = c.action === "launch_run"
        ? await fetch("/api/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ directive: c.directive || "" }) })
        : await fetch("/api/gtm/feedback", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ runId: c.run_id, verdict: c.action, note: c.note || "" }) });
      const j = await r.json();
      const ok = Boolean(j.success || j.ok);
      const line = ok ? (c.action === "launch_run" ? "Writing started. It’ll be in Posts in about 15–20 minutes." : "Recorded.") : "That did not go through: " + (j.error || r.status);
      setState(line);
      if (ok) onDone(c.action === "launch_run" ? "Writing started" : "Recorded");
      fetch("/api/assistant/audit", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant, action: c.action, run_id: c.run_id, directive: c.directive, result: ok ? "ok" : String(j.error || r.status), thread_id: threadId, asked: c.asked }) }).catch(() => {});
    } catch (e: any) { setState("That did not go through: " + String(e?.message || e)); }
  };
  const resolved = state && state !== "working" ? state : "";
  return (
    <div className="action">
      <div className="action-top"><ILock />Needs your go-ahead</div>
      <div className="action-body">
        <div className="action-title">{titles[c.action] || c.action}</div>
        <div className="kvs">
          {c.directive && <><span>Topic</span><span>{c.directive}</span></>}
          {c.run_id && <><span>Post</span><span className="mono" style={{ fontSize: 12.5 }}>{c.run_id}</span></>}
          {c.action === "launch_run" && <><span>Format</span><span>Still image</span><span>Channels</span><span>X, LinkedIn, Reddit</span></>}
          {c.note && <><span>Note</span><span>{c.note}</span></>}
        </div>
        {!resolved && owner && (
          <div style={{ display: "flex", gap: 8 }}>
            <button className={"btn btn-sm " + (c.action === "kill" ? "btn-danger" : "btn-primary")} disabled={state === "working"} onClick={go}>
              {state === "working" ? "Starting…" : c.action === "launch_run" ? "Start writing" : titles[c.action]?.split(" ")[0] || "Confirm"}
            </button>
            <button className="btn btn-quiet btn-sm" onClick={() => setState("Okay — nothing was started.")}>Not now</button>
          </div>
        )}
        {!resolved && !owner && <div className="note">Only the owner can start this.</div>}
        {resolved && <div className="done-line"><ICheck className="check-draw ok-c" />{resolved}</div>}
      </div>
    </div>
  );
}

function StatusCard({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="action">
      <div className="action-top">{label}</div>
      <div className="action-body" style={{ fontSize: 14 }}>{children}</div>
    </div>
  );
}

function AnalysisCard({ c }: { c: Card }) {
  const d = usePoll("/api/gtm/brain/analyze?tenant=" + c.tenant, (j) => j.state && j.state !== "running");
  const state = d?.state || "running";
  return (
    <StatusCard label={"Studying " + (c.url || c.tenant)}>
      {state === "running" && <span className="thinking">Reading the site: pages, colours, fonts, voice. One to three minutes.</span>}
      {state === "done" && <span>{d.result?.saved ? <>A draft profile for <b>{d.name || c.tenant}</b> is ready: {d.result.pages} pages read. It waits for your approval.</> : <>Report written for <b>{d.name || c.tenant}</b>.</>}</span>}
      {state === "failed" && <span className="bad-c">Failed: {d.error || d.result?.error}</span>}
    </StatusCard>
  );
}

function CompetitorsCard({ c }: { c: Card }) {
  const d = usePoll("/api/gtm/brain/competitors?tenant=" + c.tenant, (j) => j.state && j.state !== "running");
  const rep = d?.report;
  return (
    <StatusCard label="Reading competitors">
      {(!d || d.state === "running") && <span className="thinking">Reading their websites and recent posts. A few minutes.</span>}
      {d?.state === "done" && rep && <span>{(rep.analysed || []).map((a: any) => a.competitor + (a.ok ? " (" + a.patterns + " patterns)" : "")).join(", ") || "Done."}</span>}
      {d?.state === "failed" && <span className="bad-c">Failed: {d.job?.error}</span>}
    </StatusCard>
  );
}

function NotionCard({ c }: { c: Card }) {
  const [copied, setCopied] = useState(false);
  const full = c.url?.startsWith("http") ? c.url : (typeof window !== "undefined" ? window.location.origin : "") + c.url;
  return (
    <StatusCard label={"Notion · " + c.tenant + (c.connected ? " · connected" : "")}>
      {!c.configured && <span className="note">The Notion connection is not set up yet, so the link will say so.</span>}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {!c.for_client && <a className="btn btn-primary btn-sm" href={full}>Connect Notion</a>}
        <button className="btn btn-sm" onClick={async () => { try { await navigator.clipboard.writeText(full); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { /* */ } }}>
          {copied ? "Copied" : "Copy invite link"}
        </button>
      </div>
      <span className="meta">Works once, for {c.tenant} only, and expires in 7 days.</span>
    </StatusCard>
  );
}

function greeting(): string {
  const h = new Date().getHours();
  return h < 5 ? "Good evening" : h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
}

function Composer({ id, rows, value, onChange, onSend, onStop, busy, disabled, company, placeholder, boxRef }: {
  id: string; rows: number; value: string; onChange: (v: string) => void; onSend: () => void; onStop: () => void; busy: boolean;
  disabled: boolean; company: { id: string; name: string; color: string } | null; placeholder: string; boxRef: React.RefObject<HTMLTextAreaElement>;
}) {
  return (
    <div className="composer">
      <label htmlFor={id} style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0 0 0 0)" }}>Message the Assistant</label>
      <textarea id={id} ref={boxRef} rows={rows} placeholder={placeholder} value={value} disabled={disabled}
                onChange={(e) => onChange(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSend(); } }} />
      <div className="comp-row">
        {company && (
          <span className="comp-ws">
            <span className="ws-av" style={{ width: 16, height: 16, borderRadius: 4, fontSize: 9, background: company.color }}>{company.name.charAt(0)}</span>
            {company.name}
          </span>
        )}
        {busy
          ? <button className="send idle" onClick={onStop} aria-label="Stop"><IStop /></button>
          : <button className={"send " + (value.trim() ? "" : "idle")} onClick={onSend} aria-label="Send"><ISend /></button>}
      </div>
    </div>
  );
}

export function AssistantView({ company, owner, ownerName, prefill, threadId, onThreadChange, onSaved, onOpenRun, onAutopilot, flash }: {
  company: { id: string; name: string; color: string } | null;
  owner: boolean;
  ownerName: string;
  prefill: { text: string; n: number };
  /** The open conversation; null is a new chat. The sidebar's Recents choose it. */
  threadId: string | null;
  onThreadChange: (id: string | null) => void;
  /** A message was saved: the Recents list should refresh. */
  onSaved: () => void;
  onOpenRun: (id: string) => void;
  onAutopilot: () => void;
  flash: (t: string) => void;
}) {
  const tenant = company?.id || "";
  // The conversation these messages belong to. A switch to another one
  // replaces them; a reply still streaming into the old one is dropped.
  const current = useRef<string | null | undefined>(undefined);
  const cache = useRef(new Map<string, Msg[]>());
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingThread, setLoadingThread] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const box = useRef<HTMLTextAreaElement>(null);
  const abort = useRef<AbortController | null>(null);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!tenant) return;
    if (current.current === threadId) return;      // the stream already named this one
    current.current = threadId;
    abort.current?.abort();
    setErr(null);
    if (!threadId) {
      setMsgs([]);
      setInput("");
      setTimeout(() => box.current?.focus(), 0);
      return;
    }
    const id = threadId;
    // A chat opened before shows at once; the saved copy replaces it when it arrives.
    const seen = cache.current.get(id);
    setMsgs(seen || []);
    setLoadingThread(!seen);
    fetch("/api/assistant/threads?tenant=" + tenant + "&id=" + id, { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        if (d.ok && d.thread) cache.current.set(id, d.thread.messages);
        if (current.current !== id) return;
        if (d.ok && d.thread) setMsgs(d.thread.messages);
        else { setErr("That conversation could not be opened."); onThreadChange(null); }
      })
      .catch((e) => { if (current.current === id) setErr(String(e)); })
      .finally(() => { if (current.current === id) setLoadingThread(false); });
  }, [tenant, threadId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!prefill.n) return;
    setInput(prefill.text);
    setTimeout(() => { const b = box.current; if (b) { b.focus(); b.setSelectionRange(b.value.length, b.value.length); } }, 0);
  }, [prefill.n]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [msgs]);

  const send = async (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || busy || !tenant) return;
    setInput("");
    setErr(null);
    setMsgs((m) => [...m, { role: "user", text: q }, { role: "assistant", text: "", tools: [], cards: [], pending: true }]);
    setBusy(true);
    const ctl = new AbortController();
    abort.current = ctl;
    const startedIn = current.current;
    let mine = startedIn;
    // Updates land only while this conversation is still the open one.
    const update = (f: (m: Msg) => Msg) => {
      if (current.current !== mine) return;
      setMsgs((all) => { const c = [...all]; c[c.length - 1] = f({ ...c[c.length - 1] }); return c; });
    };
    try {
      const r = await fetch("/api/assistant", {
        method: "POST", headers: { "Content-Type": "application/json" }, signal: ctl.signal,
        body: JSON.stringify({ tenant, text: q, thread_id: startedIn || null }),
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
            if (ev.thread_id !== mine && current.current === mine) {
              mine = ev.thread_id;
              current.current = ev.thread_id;
              onThreadChange(ev.thread_id);
              onSaved();
            }
          } else if (ev.type === "tool") {
            update((m) => ({ ...m, tools: [...(m.tools || []), { name: ev.name, summary: ev.summary }] }));
            if (ev.name === "set_post_cadence") window.dispatchEvent(new Event("vn:autopilot"));
          } else if (ev.type === "card") update((m) => ({ ...m, cards: [...(m.cards || []), ev.card] }));
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
      if (mine && current.current === mine) setMsgs((all) => { cache.current.set(mine as string, all); return all; });
      setBusy(false);
      abort.current = null;
      onSaved();
      box.current?.focus();
    }
  };
  const stop = () => abort.current?.abort();

  const SUGG: [string, string | null][] = [
    ["Draft a post", "Draft a post about "],
    ["What’s new this week", null],
    ["Change the schedule", "@autopilot"],
    ["Study a brand", "Study "],
    ["Find campaigns", "Find campaigns on Galxe about "],
  ];
  const useSugg = (label: string, fill: string | null) => {
    if (fill === "@autopilot") { onAutopilot(); return; }
    if (fill === null) { send("What's new this week?"); return; }
    setInput(fill);
    setTimeout(() => { const b = box.current; if (b) { b.focus(); b.setSelectionRange(b.value.length, b.value.length); } }, 0);
  };

  const name = company?.name || "your company";
  const empty = !loadingThread && msgs.length === 0;

  if (empty) {
    return (
      <div className="chat-shell">
        <div className="greet">
          <h1 className="greet-h"><span className="greet-mark"><Mark size={34} stroke="var(--bg)" /></span>{greeting()}{ownerName ? ", " + ownerName : ""}</h1>
          <Composer id="ask1" rows={2} value={input} onChange={setInput} onSend={() => send()} onStop={stop} busy={busy} disabled={!tenant}
                    company={company} boxRef={box} placeholder={"Ask anything about " + name + ", or tell me what to make…"} />
          <div className="pills">
            {SUGG.map(([l, f]) => <button key={l} className="pill-s" onClick={() => useSugg(l, f)} disabled={!tenant}>{l}</button>)}
          </div>
          {err && <div className="note bad-c">{err}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className="chat-shell">
      <div className="thread" aria-live="polite">
        {loadingThread && <span className="thinking">Opening the conversation…</span>}
        {msgs.map((m, i) => {
          if (m.role === "user") return <div key={i} className="m-user">{m.text}</div>;
          const tools = m.tools || [];
          const planned = tools.some((t) => (t.name === "set_post_cadence" || t.name === "find_campaigns") && !t.summary.startsWith("failed"));
          const runs = Array.from(new Set((m.cards || []).filter((c) => c.type === "run").map((c) => String(c.run_id))));
          if (m.pending && !m.text && !tools.length) {
            return <div key={i} className="m-bot"><span className="bot-mark"><ISpin /></span><span className="thinking">Reading your sources…</span></div>;
          }
          return (
            <React.Fragment key={i}>
              <div className="m-bot">
                <span className="bot-mark"><Mark size={22} stroke="var(--bg)" /></span>
                <div className="bot-body">
                  {tools.map((t, j) => (
                    <span key={j} className="tool-line" style={t.summary.startsWith("failed") ? { color: "var(--bad)" } : undefined}>
                      <ICheck size={14} />{TOOL_LABEL[t.name] || t.name}{t.summary && !planned ? <span style={{ color: "var(--faint)", opacity: 0.8 }}>· {t.summary.slice(0, 110)}</span> : null}
                    </span>
                  ))}
                  {planned && tools.filter((t) => t.name === "set_post_cadence" || t.name === "find_campaigns").map((t, j) => (
                    <div key={"p" + j} className="bot-text">{t.summary}</div>
                  ))}
                  {m.text && !planned && <div className="bot-text"><Markdown text={m.text} />{m.pending && <span className="caret" />}</div>}
                  {m.grounding && !planned && m.grounding.checked > 0 && (
                    <div className="grounding">
                      <span>{(m.grounding.flagged || []).length ? m.grounding.supported + " of " + m.grounding.checked + " claims found in your sources" : "All " + m.grounding.checked + " claims found in your sources"}</span>
                      {(m.grounding.flagged || []).map((f, k) => <span key={k} className="flag">{f.verdict === "CONTRADICTED" ? "Contradicted" : "Not in your sources"}: “{f.text}”</span>)}
                    </div>
                  )}
                  {runs.length > 0 && (
                    <div className="cites">{runs.map((rid, k) => <button key={rid} className="cite" onClick={() => onOpenRun(rid)} style={{ cursor: "pointer" }}><i>{k + 1}</i>{rid}</button>)}</div>
                  )}
                  {!m.pending && !tools.length && m.text && <span className="nobrain">Answered without searching your sources</span>}
                  {planned && <button className="btn btn-sm" style={{ alignSelf: "flex-start" }} onClick={onAutopilot}>Open Autopilot</button>}
                  {m.stopped && <span className="nobrain">Stopped.</span>}
                  {m.error && <span className="nobrain" style={{ color: "var(--bad)" }}>{m.error}</span>}
                </div>
              </div>
              {(m.cards || []).map((c, j) => {
                if (c.type === "action") return <ActionCard key={j} c={c} tenant={tenant} threadId={current.current || null} owner={owner} onDone={flash} />;
                if (c.type === "analysis") return <AnalysisCard key={j} c={c} />;
                if (c.type === "competitors") return <CompetitorsCard key={j} c={c} />;
                if (c.type === "notion") return <NotionCard key={j} c={c} />;
                return null;
              })}
            </React.Fragment>
          );
        })}
        <div ref={end} />
      </div>
      <div className="dock">
        <Composer id="ask2" rows={1} value={input} onChange={setInput} onSend={() => send()} onStop={stop} busy={busy} disabled={!tenant}
                  company={company} boxRef={box} placeholder="Reply…" />
        <div className="hint">Herald suggests. You decide. Nothing is ever published for you.</div>
      </div>
    </div>
  );
}
