"use client";

/**
 * Research pages: Signals (what Herald is reading), References (its notes on
 * each source and the post it could become), Inspiration (brands worth
 * learning from) and Campaigns (live programs, busiest first).
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { agoOf, dayOf, glyphOf, whenOf } from "@/lib/herald";
import { Empty, IChevR, IOut, IPlus, IRefresh, ISearch, Loading, Seg } from "./ui";

function useJson<T = any>(url: string | null, every = 0): { data: T | null; error: string | null; reload: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => {
    if (!url) return;
    fetch(url, { cache: "no-store" })
      .then(async (r) => { const j = await r.json().catch(() => null); if (!r.ok) throw new Error((j && (j.error || j.message)) || "HTTP " + r.status); return j; })
      .then((j) => { setData(j); setError(null); })
      .catch((e) => setError(String(e?.message || e)));
  }, [url]);
  useEffect(() => {
    setData(null);
    load();
    if (!every) return;
    const t = setInterval(load, every);
    return () => clearInterval(t);
  }, [load, every]);
  return { data, error, reload: load };
}

const GRADE: Record<string, [string, string]> = {
  DIRECT: ["Relevant", "g-direct"], ADJACENT: ["Related", "g-adjacent"], NONE: ["Skip", ""], UNREAD: ["Unread", "g-unread"],
};
const gradeOf = (r: any): string => (r?.relevance ? String(r.relevance).toUpperCase() : "UNREAD");

/* ------------------------------------------------------------------ Signals */

export function SignalsView({ scrapeGap, onOpenRef, onAutopilot }: { scrapeGap: string; onOpenRef: (id: string) => void; onAutopilot: () => void }) {
  const [tab, setTab] = useState<"latest" | "used">("latest");
  const harvest = useJson<any>("/api/gtm/harvest", 15000);
  useEffect(() => {
    const on = () => harvest.reload();
    window.addEventListener("herald-signals", on);
    return () => window.removeEventListener("herald-signals", on);
  }, [harvest.reload]);
  const refs = useJson<any>("/api/gtm/references");
  const refIds = useMemo(() => new Set(((refs.data?.items || []) as any[]).map((i) => i.id)), [refs.data]);

  const latest = useMemo(() => {
    const h = harvest.data;
    if (!h) return [];
    const fresh = ((h.collected?.items || []) as any[]).map((i, n) => ({
      key: "c" + n, glyph: glyphOf(i.source_type, i.source), headline: String(i.headline || "").replace(/^\[[^\]]+\]\s*/, ""),
      source: String(i.source || i.source_type || "").replace(/^https?:\/\//, "").split("/")[0],
      style: String(i.kind || i.source_type || "").replace(/_/g, " ").replace(/^\w/, (c: string) => c.toUpperCase()),
      at: i.at || h.collected?.collected_at, id: null as string | null, url: /^https?:/.test(String(i.source)) ? String(i.source) : null,
    }));
    const sigs = ((h.signals || []) as any[]).map((s) => ({
      key: s.signal_id, glyph: glyphOf(s.source_type, s.source_root || s.source), headline: String(s.headline || "").replace(/^\[[^\]]+\]\s*/, ""),
      source: String(s.source_root || s.source_type || "").replace(/_/g, " "), style: String(s.market_category || s.source_type || "").replace(/_/g, " "),
      at: s.observed_at || s.scraped_at, id: s.signal_id as string, url: /^https?:/.test(String(s.source)) ? String(s.source) : null,
    }));
    const seen = new Set<string>();
    return [...fresh, ...sigs].filter((i) => {
      const k = i.headline.toLowerCase().slice(0, 120);
      if (!i.headline || seen.has(k)) return false;
      seen.add(k);
      return true;
    }).sort((a, b) => String(b.at || "").localeCompare(String(a.at || "")));
  }, [harvest.data]);

  const groups = useMemo(() => {
    const out: { day: string; items: typeof latest }[] = [];
    for (const it of latest.slice(0, 80)) {
      const d = dayOf(it.at);
      if (!out.length || out[out.length - 1].day !== d) out.push({ day: d, items: [] });
      out[out.length - 1].items.push(it);
    }
    return out;
  }, [latest]);

  const used = ((refs.data?.items || []) as any[]).filter((r) => gradeOf(r) === "DIRECT" || gradeOf(r) === "ADJACENT").slice().sort((a, b) => {
    const o: Record<string, number> = { DIRECT: 0, ADJACENT: 1, UNREAD: 2, NONE: 3 };
    return (o[gradeOf(a)] ?? 9) - (o[gradeOf(b)] ?? 9);
  });
  const updated = harvest.data?.collected?.collected_at || harvest.data?.scrapedAt;

  return (
    <div className="page view">
      <div className="head">
        <div><h1 className="title">Signals</h1><p className="sub">What Herald is reading about your market. New items arrive between posts.</p></div>
        {updated && <div className="meta"><span className={"live" + (scrapeGap ? "" : " off")} /><span>Updated {agoOf(updated)} ago</span></div>}
      </div>
      <div className="toolbar">
        <Seg label="View" value={tab} onChange={setTab} options={[{ key: "latest", label: "Latest", count: latest.length || undefined }, { key: "used", label: "Used in last post", count: used.length || undefined }]} />
        <button className="btn btn-quiet btn-sm" onClick={onAutopilot}>{scrapeGap ? "Checking every " + scrapeGap : "Research is paused"}</button>
      </div>
      {harvest.error && <Empty title="Signals are unavailable" text={harvest.error} />}
      {tab === "latest" && !harvest.data && !harvest.error && <Loading rows={6} />}
      {tab === "latest" && harvest.data && !latest.length && (
        <Empty title="Nothing read yet" text="Tell the Assistant how often to look for news." action={<button className="btn btn-sm" style={{ marginTop: 6 }} onClick={onAutopilot}>Set it up</button>} />
      )}
      {tab === "latest" && latest.length > 0 && (
        <div className="card feed">
          {groups.map((g) => (
            <React.Fragment key={g.day}>
              <div className="feed-group">{g.day}</div>
              {g.items.map((r) => {
                const toRef = r.id && refIds.has(r.id);
                const go = () => { if (toRef) onOpenRef(r.id!); else if (r.url) window.open(r.url, "_blank", "noopener"); };
                return (
                  <button key={r.key} className={"item" + (!toRef && !r.url ? " missing" : "")} onClick={go}>
                    <span className="ch">{r.glyph}</span>
                    <span className="item-main"><span className="item-t">{r.headline}</span><span className="item-s"><span>{r.source}</span></span></span>
                    <span className="item-r">{r.style && <span className="tag">{r.style}</span>}<span className="when">{agoOf(r.at)}</span><IChevR className="go" /></span>
                  </button>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      )}
      {tab === "used" && !refs.data && !refs.error && <Loading rows={5} />}
      {tab === "used" && refs.data && (
        <div className="card feed">
          <div className="feed-group">Read for the latest post · {refs.data.runId}</div>
          {used.map((r) => {
            const [label, cls] = GRADE[gradeOf(r)] || GRADE.DIRECT;
            return (
              <button key={r.id} className="item" onClick={() => onOpenRef(r.id)}>
                <span className="ch">{glyphOf(r.kind, r.channel)}</span>
                <span className="item-main"><span className="item-t">{r.headline}</span><span className="item-s">{r.publisher || r.channel}</span></span>
                <span className="item-r"><span className={"tag " + cls}>{label}</span><IChevR className="go" /></span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* --------------------------------------------------------------- References */

type RF = "all" | "DIRECT" | "ADJACENT";

export function ReferencesView({ focusId, owner, onDraft }: { focusId: string; owner: boolean; onDraft: (text: string) => void }) {
  const [runId, setRunId] = useState("");
  const { data, error } = useJson<any>("/api/gtm/references" + (runId ? "?runId=" + encodeURIComponent(runId) : ""));
  const [f, setF] = useState<RF>("all");
  const [sel, setSel] = useState<string>("");
  useEffect(() => { if (focusId) { setSel(focusId); setF("all"); } }, [focusId]);
  const items = ((data?.items || []) as any[]).filter((r) => gradeOf(r) === "DIRECT" || gradeOf(r) === "ADJACENT");
  const shown = items.filter((r) => f === "all" || gradeOf(r) === f);
  const cur = shown.find((r) => r.id === sel) || shown[0];
  const counts: Record<string, number> = {};
  for (const r of items) counts[gradeOf(r)] = (counts[gradeOf(r)] || 0) + 1;

  useEffect(() => {
    if (!focusId || !data) return;
    const el = document.getElementById("ref-" + focusId);
    el?.scrollIntoView({ block: "center" });
  }, [focusId, data]);

  return (
    <div className="page view">
      <div className="head">
        <div><h1 className="title">References</h1><p className="sub">Sources that matter to Vanna, and the post each one could become.</p></div>
        {Array.isArray(data?.recent) && data.recent.length > 1 && (
          <select className="select" aria-label="Read for which post" value={runId || data.runId || ""} onChange={(e) => { setRunId(e.target.value); setSel(""); }}>
            {data.recent.map((r: any) => <option key={r.runId} value={r.runId}>{r.runId.replace(/^GTM-(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2}).*/, "$3/$2 $4:$5")}{r.hasAnalysis ? "" : " · not graded"}</option>)}
          </select>
        )}
      </div>
      <div className="toolbar">
        <Seg label="Filter by relevance" value={f} onChange={(k) => { setF(k); setSel(""); }} options={[
          { key: "all", label: "All", count: items.length || undefined }, { key: "DIRECT", label: "Relevant", count: counts.DIRECT },
          { key: "ADJACENT", label: "Related", count: counts.ADJACENT },
        ]} />
      </div>
      {error && <Empty title="References are unavailable" text={error} />}
      {!data && !error && <Loading rows={5} />}
      {data && !shown.length && <Empty title="Nothing here" text="No sources with this label yet." />}
      {data && shown.length > 0 && (
        <div className="md">
          <div className="card ref-list stagger">
            {shown.map((r) => {
              const [label, cls] = GRADE[gradeOf(r)] || GRADE.UNREAD;
              return (
                <button key={r.id} id={"ref-" + r.id} className={"ref-item" + (cur?.id === r.id ? " sel" : "")} onClick={() => setSel(r.id)}>
                  <span style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}><span className={"tag " + cls}>{label}</span><span className="meta" style={{ fontSize: 12 }}>{agoOf(r.observedAt)}</span></span>
                  <b>{r.headline}</b>
                  <span className="meta">{r.publisher || r.channel}</span>
                </button>
              );
            })}
          </div>
          {cur && (
            <div key={cur.id} className="card ref-detail">
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}><span className={"tag " + (GRADE[gradeOf(cur)] || GRADE.UNREAD)[1]}>{(GRADE[gradeOf(cur)] || GRADE.UNREAD)[0]}</span><span className="meta">{cur.publisher || cur.channel} · {whenOf(cur.observedAt)}</span></div>
                <h2 style={{ margin: 0, fontSize: 22, fontWeight: 600, letterSpacing: "-.025em", lineHeight: 1.25 }}>{cur.headline}</h2>
              </div>
              {cur.whatItIs && <div><div className="label">What it is</div><p style={{ margin: 0, color: "var(--muted)" }}>{cur.whatItIs}</p></div>}
              <div><div className="label">Post idea</div><div className="idea">{cur.postIdea || (gradeOf(cur) === "UNREAD" ? "Not read yet." : "No post here.")}</div></div>
              {(cur.vannaMove || cur.why) && <div><div className="label">Angle</div><p style={{ margin: 0, color: "var(--muted)" }}>{cur.vannaMove || cur.why}</p></div>}
              {cur.why && cur.vannaMove && <div><div className="label">Why</div><p style={{ margin: 0, color: "var(--muted)" }}>{cur.why}</p></div>}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", borderTop: "1px solid var(--line)", paddingTop: 18 }}>
                {owner && cur.postIdea && (gradeOf(cur) === "DIRECT" || gradeOf(cur) === "ADJACENT") && <button className="btn btn-primary" onClick={() => onDraft(cur.postIdea)}>Make this post</button>}
                {cur.url && <a className="btn" href={cur.url} target="_blank" rel="noreferrer">Open source</a>}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* -------------------------------------------------------------- Inspiration */

export function InspirationView({ tenant, brand, owner, onAsk, onMake }: { tenant: string; brand: string; owner: boolean; onAsk: (text: string) => void; onMake: (text: string) => void }) {
  const { data, error } = useJson<any>(tenant ? "/api/gtm/brain/inspiration?tenant=" + encodeURIComponent(tenant) : null);
  const brands = ((data?.brands || []) as any[]);
  return (
    <div className="page view">
      <div className="head">
        <div><h1 className="title">Inspiration</h1><p className="sub">Brands {brand} can learn from: how they post, and an idea worth borrowing.</p></div>
        {owner && <button className="btn btn-sm" onClick={() => onAsk("Study ")}><IPlus />Add a brand</button>}
      </div>
      {error && <Empty title="Inspiration is unavailable" text={error} />}
      {!data && !error && <Loading rows={3} />}
      {data && !brands.length && <Empty title="No brands yet" text="Tell the Assistant a name — and an X handle if you have one." />}
      <div className="insp stagger">
        {brands.map((b) => {
          const move = (b.vanna_moves || [])[0] || {};
          const state = b.job?.state === "running" ? "Reading…" : b.errors && Object.keys(b.errors).length ? "Partly read" : "Watching";
          const x = b.channels?.twitter;
          return (
            <article key={b.id || b.name} className="card insp-card">
              <div className="insp-top">
                <span className="logo">{String(b.name || "?").charAt(0).toUpperCase()}</span>
                <div style={{ flex: 1, minWidth: 0 }}><div style={{ fontWeight: 600, fontSize: 15, letterSpacing: "-.01em" }}>{b.name}</div><div className="meta">{b.handle}{x?.posts ? " · " + x.posts + " posts read" : ""}</div></div>
                <span className="tag">{state}</span>
              </div>
              <div className="insp-sec"><div className="label">How they post</div><p>{move.did ? move.did + (move.format ? " (" + String(move.format).toLowerCase() + ")" : "") : move.what_worked || b.hype_origin || "Reading their recent posts — this fills in after the next pass."}</p></div>
              <div className="insp-sec"><div className="label" style={{ color: "var(--accent)" }}>Idea for {brand}</div><p>{move.vanna_move || move.adapt || move.vanna_can || "An idea appears here once Herald has read enough."}</p></div>
              <div className="insp-foot">
                <span className="meta">Updated {b.fetched_at ? agoOf(b.fetched_at) + " ago" : "—"}</span>
                {owner && <button className="btn btn-quiet btn-sm" onClick={() => onMake("A post inspired by how " + b.name + " posts: " + (move.vanna_move || move.adapt || move.vanna_can || ""))}>Make a post from this<IChevR size={13} /></button>}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- Campaigns */

function Fact({ k, v }: { k: string; v: React.ReactNode }) {
  return <div style={{ minWidth: 0 }}><div className="stat-l">{k}</div><div style={{ fontSize: 13.5, fontWeight: 500, marginTop: 2 }}>{v}</div></div>;
}

const WORTH_CLS: Record<string, string> = { "Worth studying": "s-approved", "Only as an idea": "s-review", Skip: "s-failed" };

export function CampaignsView({ owner, brand, onAsk, onMake, flash }: {
  owner: boolean; brand: string; onAsk: (text: string) => void; onMake: (text: string) => void; flash: (t: string) => void;
}) {
  const { data, error, reload } = useJson<any>("/api/gtm/campaigns");
  const [limits, setLimits] = useState<Record<string, number>>({});
  const running = data?.job?.state === "running";
  useEffect(() => {
    if (!running) return;
    const t = setInterval(reload, 4000);
    return () => clearInterval(t);
  }, [running, reload]);
  const shelves: any[] = data?.shelves?.length ? data.shelves : (data?.campaigns ? [data] : []);

  const again = async (sh: any) => {
    const r = await fetch("/api/gtm/campaigns", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: sh.query, source: sh.source_input || sh.source }) });
    const j = await r.json().catch(() => ({}));
    flash(j.ok ? "Searching again…" : (j.error || "That did not start"));
    setTimeout(reload, 1500);
  };

  return (
    <div className="page view">
      <div className="head">
        <div><h1 className="title">Campaigns</h1><p className="sub">Live campaigns from the source you name, ranked by how many people joined, with what {brand} could take from the busiest ones.</p></div>
        {owner && <button className="btn btn-sm" onClick={() => onAsk("Find campaigns on Galxe about ")}><ISearch size={14} />Find campaigns</button>}
      </div>
      {running && <div className="banner b-neutral"><span className="status s-running">Searching</span><div>Reading the live listing, then Herald studies the busiest ones for {brand}. About a minute.</div></div>}
      {error && <Empty title="Campaigns are unavailable" text={error} />}
      {!data && !error && <Loading rows={3} />}
      {data && !shelves.length && <Empty title="No campaigns saved" text="Ask the Assistant to find some — say what kind and where, for example Galxe quests about lending." />}
      <div className="stagger" style={{ display: "flex", flexDirection: "column", gap: 40 }}>
        {shelves.map((sh) => {
          const key = (sh.source_input || sh.source || "") + sh.scraped_at;
          const list = ((sh.campaigns || []) as any[]).slice().sort((a, b) => (a.rank || 999) - (b.rank || 999));
          const picked = list.filter((c) => c.selected);
          const rest = list.filter((c) => !c.selected);
          const lim = limits[key] || 12;
          const src = String(sh.source_input || sh.source || "the source");
          const studied = Math.min(18, list.length);
          return (
            <section key={key} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div className="card" style={{ padding: 18, display: "flex", flexDirection: "column", gap: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
                  <div>
                    <div className="label">How this list is made</div>
                    <div style={{ fontWeight: 600, fontSize: 16, letterSpacing: "-.01em" }}>“{sh.query}” on <span style={{ textTransform: "capitalize" }}>{src}</span></div>
                  </div>
                  {owner && <button className="btn btn-sm" disabled={running} onClick={() => again(sh)}><IRefresh />Search again</button>}
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 14 }}>
                  <Fact k="Source" v={<span style={{ textTransform: "capitalize" }}>{src} · live listing</span>} />
                  <Fact k="Searched" v={sh.scraped_at ? whenOf(sh.scraped_at) : "—"} />
                  <Fact k="Ranked by" v="People who joined, most first" />
                  <Fact k="Kept" v={list.length + " campaigns (0–1 joined are dropped)"} />
                  <Fact k={"Studied for " + brand} v={"Top " + studied + " · " + picked.length + " picked"} />
                </div>
                <div className="meta" style={{ fontSize: 12.5 }}>
                  A campaign with no public count is placed after the counted ones. Herald reads the {studied} busiest and picks up to 8 that teach {brand} something — close to credit, lending, margin or collateral first. Its notes use only the listing and {brand}’s own facts; numbers are the source’s.
                  {sh.judge_error ? " The study step failed this time: " + String(sh.judge_error).slice(0, 120) : ""}
                </div>
              </div>

              {picked.length > 0 && (
                <>
                  <div className="sec-h"><h2>Picked for {brand}</h2><span className="meta">{picked.length} of the busiest, with what {brand} can do</span></div>
                  <div className="insp">
                    {picked.map((c) => (
                      <article key={c.id} className="card insp-card">
                        <div className="insp-top" style={{ alignItems: "flex-start" }}>
                          <span className="logo" style={{ fontSize: 13 }}>#{c.rank}</span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontWeight: 600, fontSize: 15, letterSpacing: "-.01em", lineHeight: 1.35 }}>{c.name}</div>
                            <div className="meta">{c.space}{c.verified ? " ✓" : ""} · {c.participants != null ? Number(c.participants).toLocaleString() + " joined" : "count not public"} · {c.related === "close" ? "Close to " + brand : "An idea to borrow"}</div>
                          </div>
                          {c.worth && <span className={"pill " + (WORTH_CLS[c.worth] || "")}>{c.worth}</span>}
                        </div>
                        <div className="insp-sec" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                          <Fact k="Reward" v={c.reward || "Not stated"} />
                          <Fact k="Type" v={[c.type, c.chain].filter(Boolean).join(" · ") || "—"} />
                        </div>
                        {c.why_selected && <div className="insp-sec"><div className="label">Why it was picked</div><p>{c.why_selected}</p></div>}
                        {c.vanna_can && <div className="insp-sec"><div className="label" style={{ color: "var(--accent)" }}>What {brand} can do</div><p>{c.vanna_can}</p></div>}
                        {c.why_it_works && <div className="insp-sec"><div className="label">Why it would work</div><p>{c.why_it_works}</p></div>}
                        {c.what_else && <div className="insp-sec"><div className="label">Another way to use it</div><p>{c.what_else}</p></div>}
                        {c.worth_why && <div className="insp-sec"><div className="label">Worth it?</div><p>{c.worth_why}</p></div>}
                        <div className="insp-foot">
                          {c.url ? <a className="btn btn-quiet btn-sm" style={{ marginLeft: -8 }} href={c.url} target="_blank" rel="noreferrer">Open on <span style={{ textTransform: "capitalize" }}>{src}</span><IOut /></a> : <span />}
                          {owner && c.vanna_can && <button className="btn btn-sm" onClick={() => onMake("A post on how " + brand + " could run this: " + c.vanna_can)}>Make a post from this</button>}
                        </div>
                      </article>
                    ))}
                  </div>
                </>
              )}

              <div className="sec-h" style={{ marginTop: picked.length ? 12 : 0 }}><h2>All campaigns, busiest first</h2><span className="meta">{rest.length} more · not studied for {brand}</span></div>
              <div className="camp-grid">
                {rest.slice(0, lim).map((c) => (
                  <div key={c.id} className="card camp">
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}>
                      <span className="meta" style={{ color: "var(--muted)" }}><span className="ch" style={{ width: 24, height: 24, borderRadius: 7, fontSize: 10.5 }}>{glyphOf(src, c.space)}</span>{c.space || src}{c.verified ? " ✓" : ""}</span>
                      <span className={"pill " + (c.status === "Active" ? "s-approved" : "")}>{c.participants != null ? Number(c.participants).toLocaleString() + " joined" : c.status || "Live"}</span>
                    </div>
                    <div className="camp-t">#{c.rank} · {c.name}</div>
                    <div style={{ color: "var(--muted)", fontSize: 13.5, flex: 1 }}>{String(c.description || "No description on the listing.").replace(/\*\*/g, "").slice(0, 150)}{String(c.description || "").length > 150 ? "…" : ""}</div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 10, borderTop: "1px solid var(--line)", gap: 8 }}>
                      <span style={{ display: "flex", gap: 6, minWidth: 0 }}><span className="tag">{c.type || "Campaign"}</span>{c.reward && c.reward !== c.type && <span className="tag" title={c.reward} style={{ maxWidth: 110, overflow: "hidden", textOverflow: "ellipsis" }}>{c.reward}</span>}</span>
                      <span style={{ display: "flex", gap: 2 }}>
                        {owner && <button className="btn btn-quiet btn-sm" title={"Ask what " + brand + " could take from it"} onClick={() => onAsk("What could " + brand + " learn from the " + src + " campaign #" + c.rank + " “" + c.name + "” (" + (c.participants ?? "?") + " joined, reward: " + (c.reward || "not stated") + ")" + (c.url ? " " + c.url : "") + "? Say what they did, why it drew people, and what " + brand + " could do.")}>Ask Herald</button>}
                        {c.url && <a className="btn btn-quiet btn-sm" href={c.url} target="_blank" rel="noreferrer">View<IOut /></a>}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              {rest.length > lim && <div className="more"><button className="btn btn-sm" onClick={() => setLimits((l) => ({ ...l, [key]: lim + 24 }))}>Show more ({rest.length - lim})</button></div>}
            </section>
          );
        })}
      </div>
    </div>
  );
}
