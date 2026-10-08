"use client";

/**
 * Herald (/app): the shell from the design reference — sidebar, top bar,
 * search palette, toast — around seven pages, all on live data.
 *
 * The page is in the address bar (?view=, ?run=, ?ref=) so a link, a reload
 * or the Notion callback opens the same place.
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useViewer } from "@/lib/useViewer";
import { useTheme } from "@/lib/theme";
import { brainOf, companyHue, useTenant } from "@/lib/tenant";
import { Run, STATE_LABEL, headlineOf, stateOf } from "@/lib/herald";
import { WORK_LABEL, autopilotSummary, gapLabel, useAutopilot } from "../AutopilotPanel";
import { AssistantView } from "./AssistantView";
import { PostDetail, PostsView } from "./PostsView";
import { CampaignsView, InspirationView, ReferencesView, SignalsView } from "./ResearchViews";
import {
  IBookmark, IChat, ICheck, IChevR, IChevUD, IClose, ICompass, IEdit, IImage, IMegaphone, IMenu, IMoon, IPulse,
  ISearch, IShare, ISun, Mark,
} from "./ui";

type View = "assistant" | "history" | "run" | "scraped" | "references" | "inspiration" | "campaigns";
const PAGES: { key: Exclude<View, "run">; label: string; hint: string }[] = [
  { key: "assistant", label: "Assistant", hint: "Chat" }, { key: "history", label: "Posts", hint: "Review" },
  { key: "scraped", label: "Signals", hint: "Research" }, { key: "references", label: "References", hint: "Notes" },
  { key: "inspiration", label: "Inspiration", hint: "Brands" }, { key: "campaigns", label: "Campaigns", hint: "Programs" },
];
const CRUMB: Record<View, string> = { assistant: "Assistant", history: "Posts", run: "Post", scraped: "Signals", references: "References", inspiration: "Inspiration", campaigns: "Campaigns" };
// Older links (?view=runs, research, vanna_plays, brain…) still land somewhere sensible.
const OLD: Record<string, View> = { runs: "history", posts: "history", research: "scraped", signals: "scraped", vanna_plays: "inspiration", brain: "assistant", scheduler: "assistant", live: "assistant", trace: "history", ideas: "history", memes: "assistant", learning: "assistant", agents: "assistant" };

function readUrl(): { view: View; run: string; ref: string } {
  try {
    const q = new URLSearchParams(window.location.search);
    const raw = q.get("view") || "";
    const view = (PAGES.some((p) => p.key === raw) || raw === "run" ? raw : OLD[raw]) as View | undefined;
    return { view: view || (q.get("run") ? "run" : "assistant"), run: q.get("run") || "", ref: q.get("ref") || "" };
  } catch { return { view: "assistant", run: "", ref: "" }; }
}

function writeUrl(view: View, run: string, ref: string) {
  try {
    const q = new URLSearchParams(window.location.search);
    q.set("view", view);
    if (run && view === "run") q.set("run", run); else q.delete("run");
    if (ref && view === "references") q.set("ref", ref); else q.delete("ref");
    window.history.replaceState(null, "", window.location.pathname + "?" + q.toString());
  } catch { /* */ }
}

/** How long one run of a job usually takes, where the job's own history is not enough. */
const RUN_TIME: Record<string, string> = { gtm_cycle: "~20 min", research_collect: "~1–4 min", campaigns_refresh: "~1 min" };

function fmtDur(s: number): string {
  if (!s || s < 1) return "<1 s";
  if (s < 90) return Math.round(s) + " s";
  if (s < 5400) return "~" + Math.round(s / 60) + " min";
  return "~" + (s / 3600).toFixed(1) + " h";
}

function Autopilot({ onClose }: { onClose: () => void }) {
  const { clock, daemon, reload } = useAutopilot(8000);
  const [busy, setBusy] = useState("");
  const [note, setNote] = useState<string[]>([]);
  useEffect(() => {
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);
  const tell = async (text: string, key = "line") => {
    if (!text.trim()) return;
    setBusy(key); setNote([]);
    try {
      const r = await fetch("/api/scheduler", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "tell", text }) });
      const d = await r.json();
      const lines = String(d.message || d.error || "").split("\n").filter(Boolean);
      setNote(d.success ? lines : [lines[0] || "That did not stick."]);
    } catch { setNote(["That did not reach the scheduler."]); }
    setBusy("");
    await reload();
    window.dispatchEvent(new Event("vn:autopilot"));
  };
  const TELL: Record<string, [string, string]> = {
    gtm_cycle: ["stop posts", "start posts"], research_collect: ["stop headlines", "start headlines"], campaigns_refresh: ["stop campaigns", "start campaigns"],
    trend_scan: ["stop trends", "start trends"], ideas_panel: ["stop ideas", "start ideas"], memes_panel: ["stop memes", "start memes"],
    github_commits: ["stop github", "start github"], notion_sync: ["stop notion", "start notion"], brain_watch: ["stop brand watch", "start brand watch"],
    metrics_collect: ["stop metrics", "start metrics"], ops_watch: ["stop health", "start health"],
  };
  const jobs = ((clock?.jobs || []) as any[]).filter((j) => WORK_LABEL[j.job]);
  const isOn = (j: any) => j.enabled !== false && !j.paused;
  const left = typeof clock?.posts_left === "number" ? clock.posts_left : null;
  const alive = Boolean(daemon?.running || daemon?.cloud);
  const Row = ({ j }: { j: any }) => {
    const on = isOn(j);
    const chain = j.job === "gtm_cycle" && clock?.chain && left;
    return (
      <div className="ap-row">
        <span className={"live" + (on ? "" : " off")} style={{ marginTop: 6 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 500, color: on ? "var(--text)" : "var(--muted)" }}>{WORK_LABEL[j.job]} <span style={{ color: "var(--faint)", fontWeight: 400 }}>· {chain ? left + " left, one after another" : "every " + gapLabel(j.interval)}</span></div>
          <div className="meta" style={{ fontSize: 12.5 }}>
            {j.on_since ? "On for " + fmtDur((Date.now() - new Date(j.on_since).getTime()) / 1000) + " · " : ""}
            {j.status === "RUNNING" && j.current_run_start ? "This run " + fmtDur((Date.now() - new Date(j.current_run_start).getTime()) / 1000) + " · " : ""}
            {j.last_duration_s ? "Last run " + fmtDur(j.last_duration_s) + " · " : ""}
            {"Shows in " + (j.lands || (j.job === "research_collect" ? "Signals" : j.job === "gtm_cycle" ? "Posts" : "the dashboard"))}
          </div>
          {j.status === "DISABLED_AUTO_BACKOFF" && <div className="meta bad-c">Paused after 3 failures in a row.</div>}
        </div>
        {on && TELL[j.job] && <button className="btn btn-sm" disabled={busy === j.job} onClick={() => tell(TELL[j.job][0], j.job)}>{busy === j.job ? "…" : "Pause"}</button>}
      </div>
    );
  };
  return (
    <div className="ap-wrap">
      <button className="palette-bg" aria-label="Close" onClick={onClose} />
      <aside className="ap" role="dialog" aria-label="Autopilot">
        <div className="box-h" style={{ border: 0, padding: "16px 16px 6px 20px", fontSize: 16 }}>Autopilot<button className="btn btn-quiet btn-sm icon-btn" onClick={onClose} aria-label="Close"><IClose /></button></div>
        <div className="ap-body">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
            <span className="meta" style={{ color: "var(--muted)" }}><span className={"live" + (alive ? "" : " off")} />
              {daemon === null ? "Checking the scheduler…" : daemon.cloud ? "Runs on GCP" : daemon.running ? "Running on this machine" : daemon.wanted === false ? "Stopped" : "Scheduler is not running"}</span>
          </div>
          <div className="side-label" style={{ padding: "6px 2px 0" }}>Running{clock ? " (" + jobs.filter(isOn).length + ")" : ""}</div>
          <div className="card">{!clock ? <div className="ap-row"><span className="skel" style={{ width: "60%", height: 12 }} /></div> : jobs.filter(isOn).length ? jobs.filter(isOn).map((j) => <Row key={j.job} j={j} />) : <div className="ap-row meta">Nothing is running.</div>}</div>
          {clock && jobs.some((j) => !isOn(j) && (j.paused || j.cron_id)) && (
            <>
              <div className="side-label" style={{ padding: "6px 2px 0" }}>Paused</div>
              <div className="card">{jobs.filter((j) => !isOn(j) && (j.paused || j.cron_id)).map((j) => <Row key={j.job} j={j} />)}</div>
            </>
          )}
          {note.length > 0 && <div className="note" style={{ flexDirection: "column", alignItems: "flex-start", gap: 2 }}>{note.map((l, i) => <span key={i}>{l}</span>)}</div>}
          <div className="hint" style={{ textAlign: "left" }}>The scheduler keeps each job on its own gap. This list shows what is running, and for how long. Nothing is published.</div>
        </div>
      </aside>
    </div>
  );
}


/** Start a post from a topic: the agents write it, with its poster, fact check and review. */
function MakePost({ initial, tenant, onClose, onStarted }: { initial: string; tenant: string; onClose: () => void; onStarted: (note: string) => void }) {
  const [text, setText] = useState(initial);
  const [video, setVideo] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  useEffect(() => {
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);
  const start = async () => {
    const d = text.trim();
    if (!d) return;
    setBusy(true); setErr("");
    try {
      const r = await fetch("/api/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ directive: d, tenant, video }) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok || !j.success) throw new Error(j.error || "HTTP " + r.status);
      onStarted(video ? "Writing started — with a video, about 30 minutes" : "Writing started — about 20 minutes");
    } catch (e: any) { setErr(String(e?.message || e)); setBusy(false); }
  };
  return (
    <div className="palette-wrap">
      <button className="palette-bg" aria-label="Close" onClick={onClose} />
      <div className="palette" role="dialog" aria-label="Make a post" style={{ maxWidth: 560 }}>
        <div className="box-h" style={{ fontSize: 15 }}>Make a post<button className="btn btn-quiet btn-sm icon-btn" onClick={onClose} aria-label="Close"><IClose /></button></div>
        <div className="box-b" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="field">
            <label htmlFor="mk">What should the post be about? It is kept as written — it may be declined, never swapped.</label>
            <textarea id="mk" className="ta" autoFocus value={text} onChange={(e) => setText(e.target.value)} placeholder="One credit line that works across apps" style={{ minHeight: 96 }} />
          </div>
          <label className="meta" style={{ gap: 8, cursor: "pointer", color: "var(--muted)" }}>
            <input type="checkbox" checked={video} onChange={(e) => setVideo(e.target.checked)} /> Also make a short video (takes longer)
          </label>
          <div className="note">Twelve agents research, write for X, LinkedIn and Reddit, design the poster and check every claim. It lands in Posts for your review. Nothing is published.</div>
          {err && <div className="note bad-c">{err}</div>}
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button className="btn btn-quiet" onClick={onClose}>Cancel</button>
            <button className="btn btn-primary" disabled={!text.trim() || busy} onClick={start}>{busy ? "Starting…" : "Start writing"}</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function HeraldApp() {
  const viewer = useViewer();
  const owner = Boolean(viewer?.owner);
  // The public link is the demo. A visitor can chat and ask about the brand
  // and its posts; starting runs, the schedule and onboarding stay with the
  // owner (the assistant only offers a visitor its read-only tools).
  const canChat = true;
  const [theme, setTheme] = useTheme();
  const [dark, setDark] = useState(false);
  const [company, companies, pickCompany] = useTenant();
  const [view, setView] = useState<View>("assistant");
  const [runId, setRunId] = useState("");
  const [refFocus, setRefFocus] = useState("");
  const [menu, setMenu] = useState(false);
  const [wsOpen, setWsOpen] = useState(false);
  const [palette, setPalette] = useState(false);
  const [pq, setPq] = useState("");
  const [toast, setToast] = useState("");
  const [unread, setUnread] = useState<{ scraped?: boolean; history?: boolean }>({});
  const [autopilot, setAutopilot] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [threads, setThreads] = useState<{ id: string; title: string; updated_at: string; preview?: string }[]>([]);
  const [prefill, setPrefill] = useState({ text: "", n: 0 });
  const [make, setMake] = useState<string | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [runsLoading, setRunsLoading] = useState(true);
  const [ownerName, setOwnerName] = useState("");
  const [editName, setEditName] = useState(false);
  const [lastIngest, setLastIngest] = useState<string | null>(null);
  const toastT = useRef<ReturnType<typeof setTimeout>>();
  const viewRef = useRef(view);
  viewRef.current = view;
  const seenNotes = useRef<Set<string> | null>(null);
  const seenRuns = useRef<Set<string> | null>(null);
  const wsRef = useRef<HTMLDivElement>(null);
  const { clock, daemon } = useAutopilot(15000);
  const auto = autopilotSummary(clock, daemon);
  const scrapeJob = ((clock?.jobs || []) as any[]).find((j) => j.job === "research_collect");
  const scrapeGap = scrapeJob && scrapeJob.enabled !== false && !scrapeJob.paused ? gapLabel(scrapeJob.interval) : "";

  // The page from the address bar, once; the address bar follows the page
  // only after that, or the first write would replace the link being opened.
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const u = readUrl();
    setView(u.view); setRunId(u.run); setRefFocus(u.ref);
    try { setOwnerName(localStorage.getItem("vn_owner_name") || ""); } catch { /* */ }
    setReady(true);
  }, []);
  useEffect(() => { if (ready) writeUrl(view, runId, refFocus); }, [ready, view, runId, refFocus]);
  // a visitor has no Assistant (its routes answer 403)

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const read = () => setDark(theme === "dark" || (theme === "system" && mq.matches));
    read();
    mq.addEventListener("change", read);
    return () => mq.removeEventListener("change", read);
  }, [theme]);

  const [threadsLoaded, setThreadsLoaded] = useState(false);
  const [threadsErr, setThreadsErr] = useState("");
  const [studies, setStudies] = useState<{ id: string; name: string; line: string }[]>([]);
  const threadReq = useRef(0);
  // Show the last list at once. A slow or failed refresh must not blank Recents,
  // and New chat must not drop the chats already had.
  useEffect(() => {
    if (!company?.id) return;
    try {
      const raw = localStorage.getItem("herald-threads:" + company.id);
      const saved = raw ? JSON.parse(raw) : [];
      if (Array.isArray(saved) && saved.length) {
        setThreads(saved);
        setThreadsLoaded(true);
      }
    } catch { /* a bad copy is ignored; the server list replaces it */ }
  }, [company?.id]);
  // `fresh` waits for the saved list; otherwise the server answers from its
  // last copy at once. Chats started here stay listed until the server has them.
  // A slower reply must not replace a newer one — that was wiping Recents.
  const loadThreads = useCallback((fresh = false) => {
    if (!company?.id) return;
    const n = ++threadReq.current;
    fetch("/api/assistant/threads?tenant=" + encodeURIComponent(company.id) + (fresh ? "&fresh=1" : ""), { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        if (n !== threadReq.current) return;
        if (!d.ok || !Array.isArray(d.threads)) {
          setThreadsErr(d.error || "Chats could not be loaded");
          return;
        }
        setThreadsErr("");
        setThreads((cur) => {
          const saved = d.threads as { id: string; title: string; updated_at: string; preview?: string }[];
          const pending = cur.filter((t) => t.updated_at === "pending" && !saved.some((x) => x.id === t.id));
          const next = [...pending, ...saved];
          try { localStorage.setItem("herald-threads:" + company.id, JSON.stringify(next.slice(0, 40))); } catch { /* private mode */ }
          return next;
        });
      })
      .catch(() => { if (n === threadReq.current) setThreadsErr("Chats could not be loaded"); })
      .finally(() => { if (n === threadReq.current) setThreadsLoaded(true); });
  }, [company?.id]);
  const addThread = useCallback((id: string, title: string) => {
    setThreads((cur) => (cur.some((t) => t.id === id) ? cur : [{ id, title: title || "New chat", updated_at: "pending", preview: "" }, ...cur]));
  }, []);
  useEffect(() => { setThreadId(null); loadThreads(); }, [loadThreads]);
  useEffect(() => {
    if (!company?.id) return;
    const t = setInterval(() => loadThreads(), 20000);
    return () => clearInterval(t);
  }, [company?.id, loadThreads]);
  useEffect(() => {
    if (!company?.id) return;
    let stop = false;
    fetch("/api/gtm/brain/inspiration?tenant=" + encodeURIComponent(company.id), { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        if (stop || !Array.isArray(d?.brands)) return;
        setStudies(d.brands.slice(0, 6).map((b: any) => {
          const move = (b.vanna_moves || [])[0] || {};
          const line = String(move.vanna_move || move.adapt || move.vanna_can || "What Vanna can do");
          return { id: String(b.id || b.name), name: String(b.name || "Brand"), line };
        }));
      })
      .catch(() => {});
    return () => { stop = true; };
  }, [company?.id]);

  const loadRuns = useCallback(() => {
    fetch("/api/runs", { cache: "no-store" }).then((r) => r.json())
      .then((d) => { if (Array.isArray(d.runs)) setRuns(d.runs); })
      .catch(() => {}).finally(() => setRunsLoading(false));
  }, []);
  useEffect(() => { loadRuns(); const t = setInterval(loadRuns, 20000); return () => clearInterval(t); }, [loadRuns]);

  useEffect(() => {
    if (!company?.id) return;
    let alive = true;
    brainOf(company.id).then((d) => { if (alive) setLastIngest(d?.stats?.last_ingest || null); });
    return () => { alive = false; };
  }, [company?.id]);

  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setPq(""); setPalette((p) => !p); }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, []);

  useEffect(() => {
    if (!wsOpen) return;
    const off = (e: MouseEvent) => { if (!wsRef.current?.contains(e.target as Node)) setWsOpen(false); };
    window.addEventListener("mousedown", off);
    return () => window.removeEventListener("mousedown", off);
  }, [wsOpen]);

  const flash = useCallback((t: string) => {
    setToast(t);
    clearTimeout(toastT.current);
    toastT.current = setTimeout(() => setToast(""), 4200);
  }, []);

  useEffect(() => {
    let stop = false;
    const pull = async () => {
      try {
        const r = await fetch("/api/notices", { cache: "no-store" });
        const d = await r.json();
        const list = Array.isArray(d.notices) ? d.notices : [];
        if (seenNotes.current === null) {
          seenNotes.current = new Set(list.map((n: { id?: string }) => String(n.id || "")));
          return;
        }
        const fresh = list.filter((n: { id?: string }) => n?.id && !seenNotes.current!.has(String(n.id)));
        if (!fresh.length || stop) return;
        for (const n of fresh) seenNotes.current.add(String(n.id));
        const top = fresh[0] as { title?: string; body?: string };
        flash([top.title, top.body].filter(Boolean).join(" — "));
        if (viewRef.current !== "scraped") setUnread((u) => ({ ...u, scraped: true }));
        window.dispatchEvent(new Event("herald-signals"));
      } catch { /* the next poll tries again */ }
    };
    pull();
    const t = setInterval(pull, 8000);
    return () => { stop = true; clearInterval(t); };
  }, [flash]);

  useEffect(() => {
    const ids = runs.map((r) => r.run_id).filter(Boolean);
    if (seenRuns.current === null) {
      if (!runsLoading) seenRuns.current = new Set(ids);
      return;
    }
    const fresh = ids.filter((id) => !seenRuns.current!.has(id));
    if (!fresh.length) return;
    for (const id of fresh) seenRuns.current!.add(id);
    flash(fresh.length === 1 ? "A new post is in Posts" : fresh.length + " new posts are in Posts");
    if (viewRef.current !== "history" && viewRef.current !== "run") setUnread((u) => ({ ...u, history: true }));
  }, [runs, runsLoading, flash]);

  const go = useCallback((v: View) => {
    setView(v); setMenu(false); setPalette(false);
    if (v !== "run") setRunId("");
    if (v !== "references") setRefFocus("");
    if (v === "scraped" || v === "history") setUnread((u) => ({ ...u, [v]: false }));
  }, []);
  const openRun = useCallback((id: string) => { setRunId(id); setView("run"); setPalette(false); setMenu(false); }, []);
  const ask = useCallback((text: string) => { setThreadId(null); setPrefill((p) => ({ text, n: p.n + 1 })); go("assistant"); }, [go]);
  const openRef = useCallback((id: string) => { setRefFocus(id); setView("references"); }, []);

  const mine = useMemo(() => runs.filter((r) => !company?.id || String(r.company || "vanna").toLowerCase() === company.id), [runs, company?.id]);
  const postCount = mine.filter((r) => { const s = stateOf(r); return s !== "nopost" && s !== "running"; }).length;
  const run = mine.find((r) => r.run_id === runId) || runs.find((r) => r.run_id === runId) || null;
  const ws = company ? { id: company.id, name: company.name, color: companyHue(company.id) } : null;
  const brand = company?.name || "your company";
  const navKey = view === "run" ? "history" : view;
  const knowFresh = lastIngest ? (Date.now() - Date.parse(lastIngest)) / 3_600_000 < 24 : false;

  // palette
  const q = pq.trim().toLowerCase();
  const pages = PAGES.filter((p) => !q || p.label.toLowerCase().includes(q));
  const pPosts = mine.filter((r) => { const s = stateOf(r); return s !== "nopost"; })
    .filter((r) => !q || headlineOf(r).toLowerCase().includes(q)).slice(0, q ? 20 : 6);

  const saveName = (v: string) => {
    const clean = v.trim().slice(0, 40);
    setOwnerName(clean); setEditName(false);
    try { if (clean) localStorage.setItem("vn_owner_name", clean); else localStorage.removeItem("vn_owner_name"); } catch { /* */ }
  };

  const NavBtn = ({ k, icon, children, count, ping }: { k: View; icon: React.ReactNode; children: React.ReactNode; count?: number; ping?: boolean }) => (
    <button className={"side-btn" + (navKey === k ? " active" : "")} aria-current={navKey === k ? "page" : undefined} onClick={() => go(k)}>
      {icon}{children}{(count != null || ping) && <span className="nav-end">{count != null && <span className="count">{count}</span>}{ping && <span className="ping" aria-label="New" />}</span>}
    </button>
  );

  return (
    <div className={"root" + (dark ? " dark" : "")}>
      <div className={"shell" + (menu ? " menu-open" : "")}>
        <button className="scrim" aria-label="Close menu" onClick={() => setMenu(false)} />

        <aside className="side" aria-label="Main navigation">
          <a className="brand" href="/"><Mark /><span className="brand-name">Herald</span></a>

          <div className="ws" ref={wsRef}>
            <button className="ws-btn" onClick={() => setWsOpen((o) => !o)} aria-label="Switch brand" aria-expanded={wsOpen}>
              <span className="ws-av" style={{ background: ws?.color || "var(--line-2)" }}>{ws?.name.charAt(0) || ""}</span>
              <span style={{ display: "flex", flexDirection: "column", lineHeight: 1.25, minWidth: 0, flex: 1 }}>
                <span style={{ fontWeight: 500, fontSize: 13.5 }}>{ws?.name || "…"}</span>
                <span style={{ fontSize: 12, color: "var(--faint)" }}>{viewer?.client ? "Client" : owner ? "Owner" : viewer ? "Viewer" : ""}</span>
              </span>
              <IChevUD />
            </button>
            {wsOpen && (
              <div className="ws-menu">
                {companies.map((c) => (
                  <button key={c.id} className="ws-opt" onClick={() => { pickCompany(c.id); setWsOpen(false); if (view === "run") go("history"); }}>
                    <span className="ws-av" style={{ background: companyHue(c.id) }}>{c.name.charAt(0)}</span>
                    <span style={{ flex: 1, display: "flex", flexDirection: "column", lineHeight: 1.25 }}><span style={{ fontWeight: 500 }}>{c.name}</span><span style={{ fontSize: 12, color: "var(--faint)" }}>{viewer?.client ? "Client" : owner ? "Owner" : "Viewer"}</span></span>
                    {c.id === company?.id && <ICheck />}
                  </button>
                ))}
                {owner && (
                  <button className="ws-opt ws-add" onClick={() => { setWsOpen(false); ask("Add the company at "); }}>
                    <span className="ws-av" style={{ background: "var(--surface-2)", color: "var(--muted)", boxShadow: "inset 0 0 0 1px var(--line-2)" }}>+</span><span>Add a brand</span>
                  </button>
                )}
                <div className="ws-note">Each brand keeps its own knowledge and voice.</div>
              </div>
            )}
          </div>

          <button className="side-btn" style={{ color: "var(--text)" }} onClick={() => { setThreadId(null); go("assistant"); loadThreads(true); }}><IEdit />New chat</button>
          <button className="side-btn" onClick={() => { setPq(""); setPalette(true); setMenu(false); }}><ISearch />Search <span className="kbd">⌘K</span></button>

          <div className="side-label">Create</div>
          <NavBtn k="assistant" icon={<IChat />}>Assistant</NavBtn>
          <NavBtn k="history" icon={<IImage />} count={runsLoading ? undefined : postCount} ping={Boolean(unread.history)}>Posts</NavBtn>
          {(
            <>
              <div className="side-label">Recents</div>
              <div className="recents">
                <button className="side-btn" onClick={() => { setThreadId(null); go("assistant"); loadThreads(true); }}><IEdit />New chat</button>
                {studies.length > 0 && <div className="side-label" style={{ paddingLeft: 12 }}>What Vanna can do</div>}
                {studies.map((s) => (
                  <button key={s.id} className="side-btn recent"
                          title={s.name + "\n" + s.line} onClick={() => go("inspiration")}>
                    <span className="recent-t">{s.name}</span>
                    <span className="recent-p">{s.line}</span>
                  </button>
                ))}
                {!threadsLoaded && !threads.length && [0, 1, 2].map((i) => <span key={i} className="skel" style={{ width: "80%", height: 12, margin: "10px 12px", borderRadius: 5 }} />)}
                {threadsLoaded && !threads.length && !studies.length && <span className="meta" style={{ padding: "6px 12px", fontSize: 12.5 }}>{threadsErr || "Your chats show here."}</span>}
                {threads.slice(0, 30).map((t) => {
                  const asked = (t.title || "Untitled chat").replace(/\s+/g, " ").trim();
                  const said = (t.preview || "").replace(/\s+/g, " ").trim();
                  const showSaid = said && said.toLowerCase() !== asked.toLowerCase();
                  const when = t.updated_at && t.updated_at !== "pending" ? new Date(t.updated_at) : null;
                  const stamp = when && !Number.isNaN(when.getTime())
                    ? (when.toDateString() === new Date().toDateString()
                      ? when.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
                      : when.toLocaleDateString([], { month: "short", day: "numeric" }))
                    : "";
                  return (
                    <button key={t.id} className={"side-btn recent" + (view === "assistant" && threadId === t.id ? " active" : "")}
                            title={asked + (showSaid ? "\n" + said : "")} onClick={() => { setThreadId(t.id); go("assistant"); }}>
                      <span className="recent-t">{asked}</span>
                      {(showSaid || stamp) && <span className="recent-p">{showSaid ? said : stamp}</span>}
                    </button>
                  );
                })}
              </div>
            </>
          )}
          <div className="side-label">Research</div>
          <NavBtn k="scraped" icon={<IPulse />} ping={Boolean(unread.scraped)}>Signals</NavBtn>
          <NavBtn k="references" icon={<IBookmark />}>References</NavBtn>
          <NavBtn k="inspiration" icon={<ICompass />}>Inspiration</NavBtn>
          <NavBtn k="campaigns" icon={<IMegaphone />}>Campaigns</NavBtn>

          <div className="side-foot">
            <button className="sched" onClick={() => { setAutopilot(true); setMenu(false); }}>
              <span className={"live" + (auto.on ? "" : " off")} />
              <span style={{ display: "flex", flexDirection: "column", lineHeight: 1.3, flex: 1, minWidth: 0 }}>
                <span style={{ fontSize: 13.5, fontWeight: 500 }}>{clock || daemon ? auto.title : "Autopilot"}</span>
                <span style={{ fontSize: 12, color: "var(--faint)" }}>{clock || daemon ? auto.sub : "Checking…"}</span>
              </span>
              <IChevR style={{ color: "var(--faint)" }} />
            </button>
            <a className="side-btn" href="/brief" target="_blank" rel="noreferrer"><IShare />Share page</a>
            <div className="user">
              <span className="user-av">{(ownerName || (owner ? "O" : "V")).charAt(0).toUpperCase()}</span>
              <span style={{ display: "flex", flexDirection: "column", lineHeight: 1.25, minWidth: 0 }}>
                {editName ? (
                  <input className="input" autoFocus defaultValue={ownerName} placeholder="Your name" style={{ height: 26, width: 110, fontSize: 13 }}
                         onBlur={(e) => saveName(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") saveName((e.target as HTMLInputElement).value); if (e.key === "Escape") setEditName(false); }} />
                ) : (
                  <button onClick={() => setEditName(true)} title="Set your name" style={{ border: 0, background: "transparent", padding: 0, fontSize: 13.5, fontWeight: 500, textAlign: "left", cursor: "pointer" }}>{ownerName || "Add your name"}</button>
                )}
                <span style={{ fontSize: 12, color: "var(--faint)" }}>{viewer?.client ? "Client" : owner ? "Owner" : "Viewer"}</span>
              </span>
              <div className="theme-sw" role="group" aria-label="Theme">
                <span className="theme-thumb" style={{ transform: `translateX(${dark ? "100%" : "0%"})` }} />
                <button className={dark ? "" : "on"} onClick={() => setTheme("light")} aria-label="Light theme"><ISun /></button>
                <button className={dark ? "on" : ""} onClick={() => setTheme("dark")} aria-label="Dark theme"><IMoon /></button>
              </div>
            </div>
            {viewer && !viewer.client && !(viewer as any).all && <a href="?all" className="meta" style={{ fontSize: 12, padding: "2px 6px", color: "var(--faint)" }}>Show all history</a>}
            {viewer && (viewer as any).all && viewer.since === null && <a href="?fresh" className="meta" style={{ fontSize: 12, padding: "2px 6px", color: "var(--faint)" }}>Start fresh</a>}
          </div>
        </aside>

        <main className="main">
          <header className={"top" + (view === "assistant" ? "" : " lined")}>
            <button className="btn btn-quiet icon-btn menu-btn" onClick={() => setMenu(true)} aria-label="Open menu"><IMenu /></button>
            <div className="crumb">
              <span className="hide-sm">{ws?.name || ""}</span>
              <IChevR size={14} className="hide-sm" style={{ color: "var(--line-2)" }} />
              {view === "run" && <><button className="crumb-btn" onClick={() => go("history")}>Posts</button><IChevR size={14} style={{ color: "var(--line-2)" }} /></>}
              <b>{view === "run" && run ? headlineOf(run) : CRUMB[view]}</b>
            </div>
            <div className="top-right">
              {lastIngest && (
                <span className="chip-status hide-sm" title={"Last read " + new Date(lastIngest).toLocaleString()}>
                  <span className={"live" + (knowFresh ? "" : " off")} />
                  {knowFresh ? "Knowledge up to date" : "Knowledge from " + new Date(lastIngest).toLocaleDateString(undefined, { day: "numeric", month: "short" })}
                </span>
              )}
              <button className="btn btn-quiet btn-sm icon-btn" onClick={() => { setPq(""); setPalette(true); }} aria-label="Search"><ISearch size={17} /></button>
            </div>
          </header>

          {view === "assistant" && (
            <AssistantView company={ws} owner={canChat} ownerName={ownerName} prefill={prefill} threadId={threadId}
                           onThreadChange={setThreadId} onSaved={() => loadThreads(true)} onNewThread={addThread}
                           onOpenRun={openRun} onAutopilot={() => setAutopilot(true)} flash={(t) => { flash(t); loadRuns(); }} />
          )}
          {view === "history" && <PostsView runs={mine} loading={runsLoading} brand={brand} owner={owner} onOpen={openRun} onAsk={() => setMake("")} />}
          {view === "run" && (
            <PostDetail run={run} brand={brand} brandColor={ws?.color || "#2F6B5E"} owner={owner}
                        onBack={() => go("history")} onReferences={() => go("references")} onChanged={loadRuns} flash={flash} />
          )}
          {view === "scraped" && <SignalsView scrapeGap={scrapeGap} onOpenRef={openRef} onAutopilot={() => setAutopilot(true)} />}
          {view === "references" && <ReferencesView focusId={refFocus} owner={owner} onDraft={(t) => setMake(t)} />}
          {view === "inspiration" && <InspirationView tenant={company?.id || ""} brand={brand} owner={owner} onAsk={ask} onMake={(t) => setMake(t)} />}
          {view === "campaigns" && <CampaignsView owner={owner} brand={brand} onAsk={ask} onMake={(t) => setMake(t)} flash={flash} />}

          {toast && <div className="toast" role="status"><ICheck size={15} className="check-draw" />{toast}</div>}
        </main>

        {palette && (
          <div className="palette-wrap">
            <button className="palette-bg" aria-label="Close search" onClick={() => setPalette(false)} />
            <div className="palette" role="dialog" aria-label="Search">
              <div className="palette-in">
                <ISearch style={{ color: "var(--faint)" }} />
                <label htmlFor="pq" style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0 0 0 0)" }}>Search</label>
                <input id="pq" autoFocus placeholder="Jump to a page or a post…" value={pq} onChange={(e) => setPq(e.target.value)}
                       onKeyDown={(e) => {
                         if (e.key === "Escape") setPalette(false);
                         if (e.key === "Enter") { if (pages[0]) go(pages[0].key); else if (pPosts[0]) openRun(pPosts[0].run_id); }
                       }} />
                <span className="kbd">esc</span>
              </div>
              <div className="palette-list">
                {pages.length > 0 && <div className="p-group">Pages</div>}
                {pages.map((p) => <button key={p.key} className="p-item" onClick={() => go(p.key)}>{p.label}<span className="hint-r">{p.hint}</span></button>)}
                {pPosts.length > 0 && <div className="p-group">Posts</div>}
                {pPosts.map((r) => {
                  const [l, c] = STATE_LABEL[stateOf(r)];
                  return (
                    <button key={r.run_id} className="p-item" onClick={() => openRun(r.run_id)}>
                      <span style={{ flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{headlineOf(r)}</span>
                      <span className={"status " + c} style={{ fontSize: 12 }}>{l}</span>
                    </button>
                  );
                })}
                {!pages.length && !pPosts.length && <div style={{ padding: 24, textAlign: "center", color: "var(--faint)" }}>No matches. Try asking the Assistant.</div>}
              </div>
            </div>
          </div>
        )}

        {autopilot && <Autopilot onClose={() => setAutopilot(false)} />}
        {make !== null && owner && (
          <MakePost initial={make} tenant={company?.id || "vanna"} onClose={() => setMake(null)}
                    onStarted={(note) => { setMake(null); flash(note); go("history"); setTimeout(loadRuns, 4000); setTimeout(loadRuns, 15000); }} />
        )}
      </div>
    </div>
  );
}
