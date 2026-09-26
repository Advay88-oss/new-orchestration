"use client";

/**
 * Brand Brain — the one place a company's knowledge lives, as the agents see it.
 *
 * Every agent reads the brand through the brain (profile, knowledge search,
 * visual memory, What's new, competitor patterns), so this view shows exactly
 * that: what is in it, how fresh it is, what still needs the founder's review,
 * and how well each scrape source is feeding it. Read-only — approving a
 * profile version stays a deliberate founder action.
 *
 * Colours come from the theme tokens so the view follows the dashboard theme.
 */

import React, { useCallback, useEffect, useState } from "react";
import { MONO } from "@/lib/colors";

type Hit = {
  id: string; text: string; section: string; title: string; source: string;
  authority: number; url: string | null; content_type: string; score: number;
};

const AUTH: Record<number, string> = { 1: "founder-confirmed", 2: "live docs", 3: "knowledge pack", 4: "archive" };
const card: React.CSSProperties = {
  background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: 18,
};
const label: React.CSSProperties = {
  fontFamily: MONO, fontSize: 10.5, letterSpacing: 0.8, textTransform: "uppercase",
  color: "var(--vn-ink-muted)", marginBottom: 10,
};

function Stat({ v, l }: { v: React.ReactNode; l: string }) {
  return (
    <div style={{ minWidth: 92 }}>
      <div style={{ fontFamily: MONO, fontSize: 20, color: "var(--vn-ink)", lineHeight: 1.1 }}>{v}</div>
      <div style={{ fontSize: 11, color: "var(--vn-ink-muted)", marginTop: 3 }}>{l}</div>
    </div>
  );
}

function ago(iso?: string | null): string {
  if (!iso) return "—";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (!isFinite(s)) return "—";
  if (s < 3600) return Math.max(1, Math.round(s / 60)) + " min ago";
  if (s < 86400) return Math.round(s / 3600) + " h ago";
  return Math.round(s / 86400) + " d ago";
}

/** Approve the newest version, or edit it and save a new draft. */
function ProfileActions({ tenant, version, status, onChanged }: { tenant: string; version: number; status: string; onChanged: () => void }) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const post = async (body: any) => {
    setBusy(true);
    setMsg(null);
    try {
      const d = await (await fetch("/api/gtm/brain/profile", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...body, tenant }),
      })).json();
      if (!d.ok) setMsg(d.error || "failed");
      else { setEditing(false); onChanged(); }
    } catch (e) {
      setMsg(String(e));
    } finally {
      setBusy(false);
    }
  };

  const openEditor = async () => {
    const d = await (await fetch("/api/gtm/brain/profile?version=" + version + "&tenant=" + tenant, { cache: "no-store" })).json();
    if (d.ok) { setText(JSON.stringify(d.profile, null, 2)); setEditing(true); } else setMsg(d.error);
  };

  const save = () => {
    let prof: any;
    try { prof = JSON.parse(text); } catch (e) { setMsg("Not valid JSON: " + String(e)); return; }
    post({ action: "save", profile: prof, note });
  };

  const btn: React.CSSProperties = { border: "1px solid var(--vn-line-strong)", background: "transparent",
    color: "var(--vn-ink)", borderRadius: 8, padding: "7px 14px", fontSize: 13, cursor: "pointer" };
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {status !== "approved" && (
          <button disabled={busy} onClick={() => post({ action: "approve", version })}
                  style={{ ...btn, background: "var(--vn-accent)", borderColor: "var(--vn-accent)", color: "#fff", fontWeight: 600 }}>
            Approve v{version}
          </button>
        )}
        <button disabled={busy} onClick={editing ? () => setEditing(false) : openEditor} style={btn}>
          {editing ? "Close editor" : "Edit profile"}
        </button>
      </div>
      {editing && (
        <div style={{ marginTop: 10 }}>
          <textarea value={text} onChange={(e) => setText(e.target.value)} spellCheck={false}
                    style={{ width: "100%", minHeight: 360, fontFamily: MONO, fontSize: 12, lineHeight: 1.5,
                             background: "var(--vn-sunken)", color: "var(--vn-ink)", border: "1px solid var(--vn-line)",
                             borderRadius: 8, padding: 12 }} />
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="What changed (optional)"
                   style={{ flex: 1, background: "var(--vn-sunken)", border: "1px solid var(--vn-line)", borderRadius: 8,
                            padding: "7px 10px", color: "var(--vn-ink)", fontSize: 13 }} />
            <button disabled={busy} onClick={save} style={btn}>Save as new draft</button>
          </div>
          <div style={{ fontSize: 11.5, color: "var(--vn-ink-muted)", marginTop: 6 }}>
            Saving creates a new draft version; the agents use it once it is the newest, and approval is a separate step.
          </div>
        </div>
      )}
      {msg && <div style={{ color: "var(--vn-bad)", fontSize: 12.5, marginTop: 8 }}>{msg}</div>}
    </div>
  );
}

/** Onboard a company from its website: the analyzer drafts its profile. */
function Onboard({ onDone }: { onDone: (tenant: string) => void }) {
  const [url, setUrl] = useState("");
  const [tenant, setTenant] = useState("");
  const [job, setJob] = useState<any | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!job || job.state !== "running") return;
    const t = setInterval(async () => {
      const d = await (await fetch("/api/gtm/brain/analyze?tenant=" + job.tenant, { cache: "no-store" })).json();
      if (d.state && d.state !== "running") {
        setJob(d);
        if (d.state === "done") onDone(job.tenant);
      }
    }, 5000);
    return () => clearInterval(t);
  }, [job, onDone]);

  const start = async () => {
    setErr(null);
    const d = await (await fetch("/api/gtm/brain/analyze", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, tenant: tenant.toLowerCase() }),
    })).json();
    if (d.ok) setJob(d); else setErr(d.error || "could not start");
  };

  const input: React.CSSProperties = { background: "var(--vn-sunken)", border: "1px solid var(--vn-line)",
    borderRadius: 8, padding: "9px 12px", color: "var(--vn-ink)", fontSize: 13 };
  return (
    <div style={card}>
      <div style={label}>Onboard a company from its website</div>
      <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", marginBottom: 10, lineHeight: 1.5 }}>
        The analyzer crawls the site (sitemap, docs / blog / app subdomains), measures colours and fonts from the
        rendered pages, reads the voice, suggests competitors, and saves a DRAFT profile for your review. A company
        that already has a profile gets a report instead; nothing it has is replaced.
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="company.com" style={{ ...input, flex: 2, minWidth: 200 }} />
        <input value={tenant} onChange={(e) => setTenant(e.target.value)} placeholder="tenant id, e.g. acme" style={{ ...input, flex: 1, minWidth: 140 }} />
        <button onClick={start} disabled={!url || !tenant || job?.state === "running"}
                style={{ background: "var(--vn-accent)", color: "#fff", border: "none", borderRadius: 8, padding: "0 16px", fontWeight: 600, cursor: "pointer" }}>
          {job?.state === "running" ? "Analysing…" : "Analyse"}
        </button>
      </div>
      {job && (
        <div style={{ fontFamily: MONO, fontSize: 12, marginTop: 10,
                      color: job.state === "failed" ? "var(--vn-bad)" : job.state === "done" ? "var(--vn-ok)" : "var(--vn-ink-muted)" }}>
          {job.state === "running" && "Crawling and analysing " + job.url + " — this takes one to three minutes."}
          {job.state === "done" && (job.result?.saved
            ? "Done: " + (job.name || job.tenant) + " — draft profile v" + job.result.version + ", " + job.result.pages + " pages, " + job.result.knowledge_chunks + " knowledge chunks."
            : "Done: report written for " + job.tenant + " (it already has a profile, so nothing was replaced).")}
          {job.state === "failed" && "Failed: " + (job.error || job.result?.error || "unknown error")}
        </div>
      )}
      {err && <div style={{ color: "var(--vn-bad)", fontSize: 12.5, marginTop: 8 }}>{err}</div>}
    </div>
  );
}

export function BrandBrain() {
  const [data, setData] = useState<any | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const [tenant, setTenant] = useState<string>("");
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<Hit[] | null>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    fetch("/api/gtm/brain" + (tenant ? "?tenant=" + tenant : ""), { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => (d.ok ? setData(d) : setErr(d.error || "brain unavailable")))
      .catch((e) => setErr(String(e)));
  }, [tick, tenant]);

  const search = useCallback(async () => {
    if (!q.trim()) return;
    setSearching(true);
    try {
      const d = await (await fetch("/api/gtm/brain?q=" + encodeURIComponent(q.trim()) + (data?.tenant ? "&tenant=" + data.tenant : ""), { cache: "no-store" })).json();
      setHits(d.ok ? d.hits : []);
    } finally {
      setSearching(false);
    }
  }, [q, data]);

  if (err) {
    return (
      <div className="vanna-section" style={{ color: "var(--vn-ink-body)" }}>
        <div style={{ ...card, borderColor: "var(--vn-bad)" }}>Brand brain unavailable: {err}</div>
      </div>
    );
  }
  if (!data) return <div className="vanna-section" style={{ color: "var(--vn-ink-muted)", fontFamily: MONO }}>Loading the brand brain…</div>;

  const p = data.profile;
  const st = data.stats;
  const last = data.sources?.last_scrape || {};
  const rec = data.sources?.record || {};
  const acc = data.analyst_accuracy || {};
  const kinds: Record<string, any[]> = {};
  for (const im of data.images) (kinds[im.kind] ||= []).push(im);

  return (
    <div className="vanna-section" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {(data.tenants || []).length > 1 && (
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontSize: 12, color: "var(--vn-ink-muted)" }}>Tenant</span>
          {(data.tenants as string[]).map((t) => (
            <button key={t} onClick={() => { setHits(null); setTenant(t); }}
                    style={{ fontFamily: MONO, fontSize: 12, padding: "5px 12px", borderRadius: 6, cursor: "pointer",
                             border: "1px solid " + (t === data.tenant ? "var(--vn-accent)" : "var(--vn-line)"),
                             background: t === data.tenant ? "var(--vn-accent-soft)" : "transparent", color: "var(--vn-ink)" }}>
              {t}
            </button>
          ))}
        </div>
      )}
      {/* Identity and freshness */}
      <div style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "baseline" }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 600, color: "var(--vn-ink)" }}>{p.company?.name ?? data.tenant}</div>
            <div style={{ fontSize: 13, color: "var(--vn-ink-body)", marginTop: 4, maxWidth: 760, lineHeight: 1.5 }}>
              {p.company?.what_it_is}
            </div>
            <div style={{ fontSize: 12, color: "var(--vn-ink-muted)", marginTop: 6 }}>{p.company?.deployment}</div>
          </div>
          <span style={{
            fontFamily: MONO, fontSize: 11, padding: "4px 10px", borderRadius: 6,
            color: p.status === "approved" ? "var(--vn-ok)" : "var(--vn-warn)",
            border: "1px solid " + (p.status === "approved" ? "var(--vn-ok)" : "var(--vn-warn)"),
          }}>
            profile v{p.version} · {p.status}
          </span>
        </div>
        <div style={{ display: "flex", gap: 28, marginTop: 18, flexWrap: "wrap" }}>
          <Stat v={st.chunks} l="knowledge chunks" />
          <Stat v={st.images} l="images" />
          <Stat v={st.competitor_patterns} l="competitor patterns" />
          <Stat v={st.events} l="what's new" />
          <Stat v={st.outcomes} l="post outcomes" />
          <Stat v={ago(st.last_ingest)} l="last ingest" />
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 14, flexWrap: "wrap" }}>
          {Object.entries(st.chunks_by_source || {}).map(([k, v]) => (
            <span key={k} style={{ fontFamily: MONO, fontSize: 10.5, color: "var(--vn-ink-muted)",
                                   border: "1px solid var(--vn-line)", borderRadius: 5, padding: "2px 8px" }}>
              {k} {String(v)}
            </span>
          ))}
        </div>
      </div>

      {/* Needs the founder */}
      {(p.status !== "approved" || (p.open_questions || []).length > 0) && (
        <div style={{ ...card, borderColor: "var(--vn-warn)" }}>
          <div style={label}>Needs your review</div>
          {p.status !== "approved" && (
            <div style={{ fontSize: 13, color: "var(--vn-ink-body)", marginBottom: 10 }}>
              The profile is a draft. The agents use it, but it has not been approved.
            </div>
          )}
          {(p.open_questions || []).map((qq: string) => (
            <div key={qq} style={{ fontSize: 13, color: "var(--vn-ink)", padding: "6px 0", borderTop: "1px solid var(--vn-line)" }}>{qq}</div>
          ))}
          {(p.palette_candidates || []).length > 0 && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 10, marginTop: 12 }}>
              {[{ name: "In use (profile)", colors: p.palette }, ...p.palette_candidates].map((c: any) => (
                <div key={c.name} style={{ border: "1px solid var(--vn-line)", borderRadius: 8, padding: 10 }}>
                  <div style={{ fontSize: 12, color: "var(--vn-ink-body)", marginBottom: 8 }}>{c.name}</div>
                  <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                    {Object.entries(c.colors || {}).filter(([, v]) => typeof v === "string" && String(v).startsWith("#")).map(([k, v]) => (
                      <span key={k} title={k + " " + v} style={{ width: 22, height: 22, borderRadius: 4, background: String(v),
                                                               border: "1px solid var(--vn-line-strong)" }} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
          <ProfileActions tenant={data.tenant} version={p.version} status={p.status} onChanged={() => setTick((x) => x + 1)} />
        </div>
      )}

      {/* Knowledge search */}
      <div style={card}>
        <div style={label}>Search the knowledge base (what the agents retrieve)</div>
        <div style={{ display: "flex", gap: 8 }}>
          <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && search()}
                 placeholder="e.g. health factor liquidation floor"
                 style={{ flex: 1, background: "var(--vn-sunken)", border: "1px solid var(--vn-line)", borderRadius: 8,
                          padding: "9px 12px", color: "var(--vn-ink)", fontSize: 13 }} />
          <button onClick={search} disabled={searching}
                  style={{ background: "var(--vn-accent)", color: "#fff", border: "none", borderRadius: 8,
                           padding: "0 16px", fontWeight: 600, cursor: "pointer" }}>
            {searching ? "…" : "Search"}
          </button>
        </div>
        {hits && (
          <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
            {hits.length === 0 && <div style={{ color: "var(--vn-ink-muted)", fontSize: 13 }}>Nothing in the brain matches.</div>}
            {hits.map((h) => (
              <div key={h.id} style={{ borderTop: "1px solid var(--vn-line)", paddingTop: 8 }}>
                <div style={{ fontFamily: MONO, fontSize: 10.5, color: "var(--vn-ink-muted)" }}>
                  {h.source} · {AUTH[h.authority] ?? h.authority} · {h.section}
                  {h.url && <> · <a href={h.url} target="_blank" rel="noreferrer" style={{ color: "var(--vn-accent-light)" }}>source</a></>}
                </div>
                <div style={{ fontSize: 13, color: "var(--vn-ink-body)", marginTop: 4, lineHeight: 1.5 }}>{h.text.slice(0, 420)}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Sources feeding the brain and the scout */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
        <div style={card}>
          <div style={label}>Scrape sources — last run {last.run_id ? "(" + ago(last.scraped_at) + ")" : ""}</div>
          <table style={{ width: "100%", fontSize: 12.5, borderCollapse: "collapse" }}>
            <tbody>
              {Object.entries(last.sources || {}).map(([k, v]: [string, any]) => {
                const r = rec[k];
                return (
                  <tr key={k} style={{ borderTop: "1px solid var(--vn-line)" }}>
                    <td style={{ padding: "6px 0", color: "var(--vn-ink)" }}>{k}</td>
                    <td style={{ fontFamily: MONO, color: v.ok && v.signals ? "var(--vn-ok)" : "var(--vn-warn)" }}>
                      {v.ok ? v.signals + " signals" : "failed"}
                    </td>
                    <td style={{ fontFamily: MONO, color: "var(--vn-ink-muted)", textAlign: "right" }}>
                      {r ? Math.round(r.mean * 100) + "% useful" : "no record"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div style={{ fontSize: 11, color: "var(--vn-ink-faint)", marginTop: 8 }}>
            "Useful" is the scout's learned record: the market analyst's grades and the founder's decisions.
          </div>
        </div>
        <div style={card}>
          <div style={label}>Market analyst accuracy</div>
          <div style={{ display: "flex", gap: 28 }}>
            <Stat v={acc.scored ? acc.right + "/" + acc.scored : "—"} l="calls right" />
            <Stat v={acc.pending ?? 0} l="pending" />
          </div>
          <div style={{ fontSize: 12, color: "var(--vn-ink-muted)", marginTop: 10, lineHeight: 1.5 }}>
            Each theme's rising / steady / fading call is scored against the scrapes that follow it — never against approval.
          </div>
        </div>
      </div>

      {/* Visual memory */}
      <div style={card}>
        <div style={label}>Visual memory — what the poster designer is shown</div>
        {Object.entries(kinds).map(([k, ims]) => (
          <div key={k} style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 12, color: "var(--vn-ink-body)", marginBottom: 8 }}>{k.replace("_", " ")} · {ims.length}</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 10 }}>
              {ims.map((im: any) => (
                <figure key={im.id} style={{ margin: 0 }} title={im.caption || ""}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={"/api/gtm/brain/image?path=" + encodeURIComponent(im.path)} alt={im.caption || k}
                       loading="lazy" style={{ width: "100%", aspectRatio: "1", objectFit: "cover", borderRadius: 8,
                                                border: "1px solid var(--vn-line)" }} />
                  {im.score != null && (
                    <figcaption style={{ fontFamily: MONO, fontSize: 10, color: "var(--vn-ink-muted)", marginTop: 4 }}>
                      founder score {im.score}
                    </figcaption>
                  )}
                </figure>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
        <div style={card}>
          <div style={label}>Competitor patterns (summaries, never their text)</div>
          {(data.competitor_patterns || []).map((c: any, i: number) => (
            <div key={i} style={{ borderTop: "1px solid var(--vn-line)", padding: "7px 0" }}>
              <div style={{ fontSize: 12, color: "var(--vn-ink)" }}>{c.competitor} · <span style={{ color: "var(--vn-ink-muted)" }}>{c.topic}</span></div>
              <div style={{ fontSize: 12.5, color: "var(--vn-ink-body)", marginTop: 2, lineHeight: 1.45 }}>{c.pattern}</div>
            </div>
          ))}
        </div>
        <div style={card}>
          <div style={label}>What's new</div>
          <div style={{ fontFamily: MONO, fontSize: 11, color: data.notion?.configured ? "var(--vn-ok)" : "var(--vn-warn)", marginBottom: 8 }}>
            Notion: {data.notion?.configured
              ? "connected · " + (data.notion.pages || 0) + " pages · last sync " + ago(data.notion.last_sync)
                + (data.notion.pending_webhook ? " · change pending" : "")
              : "not connected (set NOTION_TOKEN and share pages with the integration)"}
          </div>
          {(data.whats_new || []).length === 0 ? (
            <div style={{ fontSize: 13, color: "var(--vn-ink-muted)", lineHeight: 1.5 }}>
              No dated events yet. The Notion sync classifies every change (feature launch, factual update or
              noise) and dates the first two here.
            </div>
          ) : (data.whats_new || []).map((e: any) => (
            <div key={e.id} style={{ borderTop: "1px solid var(--vn-line)", padding: "7px 0", fontSize: 12.5 }}>
              <span style={{ fontFamily: MONO, color: "var(--vn-ink-muted)" }}>{String(e.at).slice(0, 10)}</span>{" "}
              <span style={{ color: "var(--vn-ink)" }}>{e.title}</span>
            </div>
          ))}
        </div>
      </div>

      <Onboard onDone={(t) => { setTenant(t); setTick((x) => x + 1); }} />
    </div>
  );
}
