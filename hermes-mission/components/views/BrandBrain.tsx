"use client";

/**
 * Brand Brain — the one place a company's knowledge lives, as the agents see it.
 *
 * Every agent reads the brand through the brain (profile, knowledge search,
 * visual memory, What's new), so this view shows exactly
 * that: what is in it, how fresh it is, what still needs the founder's review,
 * and how well each scrape source is feeding it. Read-only — approving a
 * profile version stays a deliberate founder action.
 *
 * Colours come from the theme tokens so the view follows the dashboard theme.
 */

import React, { useCallback, useEffect, useState } from "react";
import { MONO } from "@/lib/colors";
import { ErrorState, ViewSkeleton } from "@/components/States";
import { useViewer } from "@/lib/useViewer";
import { COMPANY_EVENT, readCompany, writeCompany } from "@/lib/company";
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
    color: "var(--vn-ink)", borderRadius: 8, padding: "8px 14px", fontSize: 13, cursor: "pointer" };
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
                            padding: "8px 10px", color: "var(--vn-ink)", fontSize: 13 }} />
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

/** Connect or disconnect the tenant's Notion (OAuth; the token is stored
 *  encrypted). Connecting always goes through a signed invite: open it
 *  yourself, or send it to the client so they pick their own pages. */
/** The owner's client link for this company: that browser becomes the
 *  company's client (its own runs, Assistant, brain, Notion, launches). */
function ClientLink({ tenant }: { tenant: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const make = async () => {
    setBusy(true); setMsg(null);
    try {
      const j = await (await fetch("/api/client-link", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ tenant, days: 30 }),
      })).json();
      if (j.ok) setUrl(j.url); else setMsg(j.error || "could not make the link");
    } finally { setBusy(false); }
  };
  const copy = async () => {
    if (!url) return;
    try { await navigator.clipboard.writeText(url); setMsg("Copied."); } catch { setMsg("Select the link and copy it."); }
  };
  return (
    <div style={card}>
      <div style={label}>Client link · {tenant}</div>
      <div style={{ fontSize: 13, color: "var(--vn-ink-body)", lineHeight: 1.55, marginBottom: 10 }}>
        Send this to {tenant}&apos;s team. Whoever opens it gets {tenant}&apos;s own dashboard: its runs, the
        Assistant, this Brand Brain, Notion, launching runs (up to 10 a day) and approving them. Nothing of any
        other company. It works for 30 days.
      </div>
      {!url ? (
        <button onClick={make} disabled={busy}
                style={{ background: "var(--vn-accent)", color: "#fff", border: "none", borderRadius: 8, padding: "8px 14px", fontWeight: 600, cursor: "pointer" }}>
          {busy ? "Making…" : "Make a client link"}
        </button>
      ) : (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <input readOnly value={url} onFocus={(e) => e.currentTarget.select()}
                 style={{ flex: 1, minWidth: 240, background: "var(--vn-sunken)", border: "1px solid var(--vn-line)", borderRadius: 8,
                          padding: "8px 10px", color: "var(--vn-ink)", fontFamily: MONO, fontSize: 11.5 }} />
          <button onClick={copy} style={{ background: "var(--vn-hover)", border: "1px solid var(--vn-line-strong)", borderRadius: 8,
                                         padding: "8px 12px", color: "var(--vn-ink)", cursor: "pointer" }}>Copy</button>
        </div>
      )}
      {msg && <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", marginTop: 8 }}>{msg}</div>}
    </div>
  );
}

function NotionConnect({ tenant, notion, onChange }: { tenant: string; notion: any; onChange: () => void }) {
  const [busy, setBusy] = useState(false);
  const [link, setLink] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const invite = async (): Promise<string | null> => {
    setErr(null);
    setBusy(true);
    try {
      const d = await (await fetch("/api/gtm/brain/notion/invite", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ tenant }),
      })).json();
      if (!d.ok || !d.url) { setErr(d.error || "could not make an invite"); return null; }
      return d.url as string;
    } finally {
      setBusy(false);
    }
  };
  const disconnect = async () => {
    setBusy(true);
    try {
      await fetch("/api/gtm/brain/notion/disconnect", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ tenant }),
      });
      onChange();
    } finally {
      setBusy(false);
    }
  };
  const copy = async () => {
    if (!link) return;
    try { await navigator.clipboard.writeText(link); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { /* shown anyway */ }
  };

  const b: React.CSSProperties = { border: "1px solid var(--vn-line-strong)", background: "transparent",
    color: "var(--vn-ink)", borderRadius: 6, padding: "6px 12px", fontSize: 12.5, cursor: "pointer" };
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        {notion?.oauth_connected ? (
          <button disabled={busy} onClick={disconnect} style={b}>Disconnect Notion</button>
        ) : (
          <button disabled={busy} onClick={async () => { const u = await invite(); if (u) window.location.href = u; }}
                  style={{ ...b, background: "var(--vn-cta)", color: "var(--vn-on-accent)", border: "none" }}>
            Connect my Notion
          </button>
        )}
        <button disabled={busy} onClick={async () => { const u = await invite(); if (u) setLink(u); }} style={b}>
          Create client invite link
        </button>
        {!notion?.oauth_configured && (
          <span style={{ fontSize: 11.5, color: "var(--vn-ink-muted)" }}>
            Needs the Notion OAuth connection: NOTION_OAUTH_CLIENT_ID / _SECRET.
          </span>
        )}
      </div>
      {link && (
        <div style={{ marginTop: 8, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <code style={{ flex: "1 1 320px", minWidth: 0, fontSize: 11.5, background: "var(--vn-sunken)", border: "1px solid var(--vn-line)",
                         borderRadius: 6, padding: "6px 8px", overflowX: "auto", whiteSpace: "nowrap" }}>{link}</code>
          <button onClick={copy} style={b}>{copied ? "Copied" : "Copy"}</button>
          <span style={{ fontSize: 11.5, color: "var(--vn-ink-muted)", flexBasis: "100%" }}>
            Send this to the client. It connects their Notion to {tenant} only, works once, and expires in 7 days.
          </span>
        </div>
      )}
      {err && <div style={{ fontSize: 12, color: "var(--vn-bad)", marginTop: 6 }}>{err}</div>}
    </div>
  );
}

/** The code the brain knows (GitHub chunks, authority 2) and the reviewer's
 *  record on the runs that followed. Counted from the brain and the reward
 *  events; a repo that was never synced is simply absent. */
function CodeToMarket({ repos, commits }: { repos: any[]; commits?: any }) {
  const log: any[] = commits?.commits || [];
  const [events, setEvents] = useState<any[] | null>(null);
  useEffect(() => {
    fetch("/api/gtm/learning", { cache: "no-store" })
      .then((r) => r.json())
      .then((j) => setEvents(j.ok ? j.events || [] : []))
      .catch(() => setEvents([]));
  }, []);
  const reviewed = (events || []).filter((e) => e.reviewer_ok === 0 || e.reviewer_ok === 1);
  const passed = reviewed.filter((e) => e.reviewer_ok === 1).length;
  const decided = (events || []).filter((e) => e.human != null);
  const approved = decided.filter((e) => Number(e.human) >= 0.8).length;
  const th: React.CSSProperties = { padding: "8px 12px", fontWeight: 600 };
  const td: React.CSSProperties = { padding: "10px 12px", fontFamily: MONO, color: "var(--vn-ink)" };
  return (
    <>
      <div style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <div style={label}>Codebase to market — the code the brain knows</div>
          <span style={{ fontFamily: MONO, fontSize: 11, padding: "3px 8px", borderRadius: 6,
                         color: repos.length ? "var(--vn-ok)" : "var(--vn-warn)",
                         background: repos.length ? "var(--vn-ok-soft)" : "transparent",
                         border: repos.length ? "none" : "1px solid var(--vn-warn)" }}>
            {repos.length ? "● GITHUB SYNCED" : "GITHUB NOT SYNCED"}
          </span>
        </div>
        <div style={{ fontSize: 12.5, color: "var(--vn-ink-body)", margin: "4px 0 14px", lineHeight: 1.5 }}>
          Repositories indexed into the brain as authority-2 knowledge, so posts about a shipped feature can be checked
          against the code.
        </div>
        {repos.length === 0 ? (
          <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", lineHeight: 1.6 }}>
            No repository has been synced yet, so the brain holds no code. Run{" "}
            <code style={{ fontFamily: MONO, fontSize: 11.5 }}>python -m pipeline.brand_brain.github_sync sync --tenant vanna</code>{" "}
            (a <code style={{ fontFamily: MONO, fontSize: 11.5 }}>GITHUB_TOKEN</code> in pipeline/.env reads private repos).
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ color: "var(--vn-ink-muted)", textAlign: "left", borderBottom: "1px solid var(--vn-line)" }}>
                  <th style={{ ...th, paddingLeft: 0 }}>Repository</th><th style={th}>Files</th>
                  <th style={th}>Chunks</th><th style={th}>Last synced</th>
                </tr>
              </thead>
              <tbody>
                {repos.map((r) => (
                  <tr key={r.repo} style={{ borderBottom: "1px solid var(--vn-line)" }}>
                    <td style={{ ...td, paddingLeft: 0, fontWeight: 700 }}>
                      {r.url ? <a href={r.url} target="_blank" rel="noreferrer" style={{ color: "inherit" }}>{r.repo}</a> : r.repo}
                    </td>
                    <td style={td}>{r.files}</td>
                    <td style={td}>{r.chunks}</td>
                    <td style={{ ...td, color: "var(--vn-ink-muted)" }}>{r.last_synced ? ago(r.last_synced) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <div style={label}>Latest commits — every branch, last 30 days</div>
          {commits?.synced_at && (
            <span style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-muted)" }}>synced {ago(commits.synced_at)}</span>
          )}
        </div>
        {log.length === 0 ? (
          <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", lineHeight: 1.6 }}>
            No commits synced yet. Run{" "}
            <code style={{ fontFamily: MONO, fontSize: 11.5 }}>python -m pipeline.brand_brain.github_sync commits --tenant vanna</code>{" "}
            (the scheduler&apos;s hourly github_commits job does this).
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ color: "var(--vn-ink-muted)", textAlign: "left", borderBottom: "1px solid var(--vn-line)" }}>
                  <th style={{ ...th, paddingLeft: 0 }}>When</th><th style={th}>Repository</th>
                  <th style={th}>Commit</th><th style={th}>Author</th><th style={th}>Message</th>
                </tr>
              </thead>
              <tbody>
                {log.map((c) => (
                  <tr key={c.sha} style={{ borderBottom: "1px solid var(--vn-line)" }}>
                    <td style={{ ...td, paddingLeft: 0, color: "var(--vn-ink-muted)", whiteSpace: "nowrap" }}
                        title={new Date(c.date).toLocaleString()}>{ago(c.date)}</td>
                    <td style={{ ...td, whiteSpace: "nowrap" }}>{c.repo}</td>
                    <td style={td}>
                      <a href={c.url} target="_blank" rel="noreferrer" style={{ color: "inherit" }}>{c.short}</a>
                    </td>
                    <td style={{ ...td, whiteSpace: "nowrap" }}>{c.author}</td>
                    <td style={{ ...td, fontFamily: "inherit" }}>
                      {c.message}
                      <span style={{ color: "var(--vn-ink-muted)", fontFamily: MONO, fontSize: 10.5 }}>
                        {"  "}{(c.branches || []).slice(0, 2).join(", ")}{(c.branches || []).length > 2 ? " +" + (c.branches.length - 2) : ""}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {(commits?.errors || []).map((e: string) => (
          <div key={e} style={{ fontSize: 11.5, color: "var(--vn-warn)", marginTop: 6 }}>{e}</div>
        ))}
      </div>

      <div style={card}>
        <div style={label}>Reviewer firewall — claim safety on real runs</div>
        {events === null ? (
          <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)" }}>Loading…</div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginTop: 4 }}>
            {[
              { k: "Passed the reviewer", v: reviewed.length ? passed + " / " + reviewed.length : "—",
                d: "runs whose claims passed the hard gate" },
              { k: "Blocked", v: reviewed.length ? String(reviewed.length - passed) : "—",
                d: "runs stopped for an unsupported or unsafe claim" },
              { k: "Founder approved", v: decided.length ? approved + " / " + decided.length : "—",
                d: "approved or edited, of the runs you decided" },
            ].map((s) => (
              <div key={s.k} style={{ background: "var(--vn-sunken)", padding: 14, borderRadius: 8, border: "1px solid var(--vn-line)" }}>
                <div style={{ fontFamily: MONO, fontSize: 10, color: "var(--vn-ink-muted)", textTransform: "uppercase" }}>{s.k}</div>
                <div style={{ fontFamily: MONO, fontSize: 20, fontWeight: 700, color: "var(--vn-ink)", marginTop: 4 }}>{s.v}</div>
                <div style={{ fontSize: 11, color: "var(--vn-ink-muted)", marginTop: 4 }}>{s.d}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
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
  const viewer = useViewer();
  const isClient = Boolean(viewer?.client);
  const [data, setData] = useState<any | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const [tenant, setTenant] = useState<string>("");
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<Hit[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [ledger, setLedger] = useState(false);

  useEffect(() => {
    const apply = () => {
      const saved = readCompany();
      if (saved) setTenant(saved);
    };
    apply();
    window.addEventListener(COMPANY_EVENT, apply);
    return () => window.removeEventListener(COMPANY_EVENT, apply);
  }, []);

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
      <section className="vanna-section">
        <ErrorState title="The brand brain is unavailable" detail={err} />
      </section>
    );
  }
  if (!data) return <ViewSkeleton cards={3} media label="Loading the brand brain" />;

  const p = data.profile;
  const st = data.stats;
  const last = data.sources?.last_scrape || {};
  const rec = data.sources?.record || {};
  const acc = data.analyst_accuracy || {};
  const kinds: Record<string, any[]> = {};
  for (const im of data.images) (kinds[im.kind] ||= []).push(im);

  return (
    <div className="vanna-section">
      {(data.tenants || []).length > 1 && (
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontSize: 12, color: "var(--vn-ink-muted)" }}>Company</span>
          {(data.tenants as string[]).map((t) => (
            <button key={t} onClick={() => { setHits(null); setLedger(false); writeCompany(t); setTenant(t); }}
                    style={{ fontFamily: MONO, fontSize: 12, padding: "6px 12px", borderRadius: 6, cursor: "pointer",
                             border: "1px solid " + (t === data.tenant ? "var(--vn-accent)" : "var(--vn-line)"),
                             background: t === data.tenant ? "var(--vn-accent-soft)" : "transparent", color: "var(--vn-ink)" }}>
              {t}
            </button>
          ))}
        </div>
      )}
      {/* Identity and freshness */}
      <div style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "flex-start" }}>
          <div style={{ flex: "1 1 280px", minWidth: 0 }}>
            <div style={{ fontSize: 18, fontWeight: 600, color: "var(--vn-ink)" }}>{p.company?.name ?? data.tenant}</div>
            <div style={{ fontSize: 13, color: "var(--vn-ink-body)", marginTop: 4, maxWidth: 760, lineHeight: 1.5 }}>
              {p.company?.what_it_is}
            </div>
            <div style={{ fontSize: 12, color: "var(--vn-ink-muted)", marginTop: 6 }}>{p.company?.deployment}</div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8, flex: "0 0 auto" }}>
            <span style={{
              fontFamily: MONO, fontSize: 11, padding: "4px 10px", borderRadius: 6,
              color: p.status === "approved" ? "var(--vn-ok)" : "var(--vn-warn)",
              border: "1px solid " + (p.status === "approved" ? "var(--vn-ok)" : "var(--vn-warn)"),
            }}>
              profile v{p.version} · {p.status}
            </span>
            <button type="button" onClick={() => setLedger((v) => !v)} aria-expanded={ledger}
                    style={{
                      border: "1px solid " + (ledger ? "var(--vn-accent)" : "var(--vn-line-strong)"),
                      background: ledger ? "var(--vn-accent)" : "transparent",
                      color: ledger ? "#fff" : "var(--vn-ink)",
                      borderRadius: 8, padding: "8px 14px", fontSize: 13, fontWeight: 600, cursor: "pointer",
                    }}>
              {ledger ? "Hide post outcomes" : "Post outcomes · " + (st.outcomes ?? 0)}
            </button>
          </div>
        </div>
        <div style={{ display: "flex", gap: 24, marginTop: 18, flexWrap: "wrap" }}>
          <Stat v={st.chunks} l="knowledge chunks" />
          <Stat v={st.images} l="images" />
          <Stat v={(data.inspiration || []).length} l="brands Vanna learns from" />
          <Stat v={st.events} l="what's new" />
          <Stat v={ago(st.last_ingest)} l="last ingest" />
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 14, flexWrap: "wrap" }}>
          {Object.entries(st.chunks_by_source || {}).map(([k, v]) => (
            <span key={k} style={{ fontFamily: MONO, fontSize: 10.5, color: "var(--vn-ink-muted)",
                                   border: "1px solid var(--vn-line)", borderRadius: 6, padding: "2px 8px" }}>
              {k} {String(v)}
            </span>
          ))}
        </div>
      </div>

      {ledger && (
        <div style={card}>
          <div style={label}>Post outcomes ledger</div>
          {(data.outcomes || []).length === 0 ? (
            <div style={{ fontSize: 13, color: "var(--vn-ink-muted)" }}>No published-post metrics recorded yet.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {(data.outcomes as any[]).map((o: any, i: number) => (
                <div key={o.id ?? i} style={{ borderTop: "1px solid var(--vn-line)", paddingTop: 8 }}>
                  <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink)" }}>
                    {o.post_id || o.run_id || "post"}
                    <span style={{ color: "var(--vn-ink-muted)" }}> · {String(o.at || "").slice(0, 16).replace("T", " ")} · {o.source || "recorded"}</span>
                  </div>
                  <div style={{ fontSize: 12.5, color: "var(--vn-ink-body)", marginTop: 4 }}>
                    {o.metrics && typeof o.metrics === "object"
                      ? Object.entries(o.metrics).map(([k, v]) => k + " " + String(v)).join(" · ")
                      : "no metrics"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <CodeToMarket repos={data.github || []} commits={data.commits} />

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
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12, marginTop: 12 }}>
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
          <div style={{ display: "flex", gap: 24 }}>
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
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 12 }}>
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

      {data.tenant === "vanna" && <div style={card}>
        <div style={label}>Rejected — the agent was told not to make these</div>
        <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", marginBottom: 12, lineHeight: 1.5 }}>
          Kept in their own list. They stay out of the approved visual memory the designer is shown.
        </div>
        {(data.rejected || []).length === 0 ? (
          <div style={{ fontSize: 13, color: "var(--vn-ink-muted)" }}>No rejected posters on file.</div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12 }}>
            {(data.rejected as any[]).map((im: any) => (
              <figure key={im.path} style={{ margin: 0 }} title={im.brief || ""}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={"/api/gtm/brain/image?path=" + encodeURIComponent(im.path)} alt={im.note || "rejected poster"}
                     loading="lazy" style={{ width: "100%", aspectRatio: "1", objectFit: "cover", borderRadius: 8,
                                              border: "1px solid var(--vn-bad)" }} />
                <figcaption style={{ fontSize: 11, color: "var(--vn-ink-body)", marginTop: 6, lineHeight: 1.4 }}>
                  <span style={{ fontFamily: MONO, fontSize: 10, letterSpacing: 0.4, textTransform: "uppercase",
                                 color: "var(--vn-bad)" }}>
                    rejected{im.verdict && im.verdict !== "kill" ? " · " + im.verdict : ""}
                  </span>
                  {im.note ? <div style={{ marginTop: 3 }}>{im.note}</div> : null}
                </figcaption>
              </figure>
            ))}
          </div>
        )}
      </div>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
        <div style={{ ...card, gridColumn: "1 / -1" }}>
          <div style={label}>What's new</div>
          <NotionConnect tenant={data.tenant} notion={data.notion} onChange={() => setTick((x) => x + 1)} />
          <div style={{ fontFamily: MONO, fontSize: 11, color: data.notion?.configured ? "var(--vn-ok)" : "var(--vn-warn)", marginBottom: 8 }}>
            Notion: {data.notion?.configured
              ? "connected" + (data.notion.workspace ? " to " + data.notion.workspace : "")
                + (data.notion.via === "token" ? " (internal token)" : "")
                + " · " + (data.notion.pages || 0) + " pages · last sync " + ago(data.notion.last_sync)
                + (data.notion.pending_webhook ? " · change pending" : "")
              : "not connected"}
          </div>
          {/* The public watch (brain_watch job): X, Reddit, news, the blog, a web summary. */}
          <div style={{ fontFamily: MONO, fontSize: 11, color: data.watch?.at ? "var(--vn-ink-muted)" : "var(--vn-warn)", marginBottom: 8, lineHeight: 1.6 }}>
            Public watch: {data.watch?.at
              ? "last run " + ago(data.watch.at) + " · "
                + Object.entries(data.watch.collected || {}).map(([k, v]) => k.replace("_", " ") + " " + v).join(", ")
                + " · " + (data.watch.stored ?? 0) + " kept"
                + (data.watch.x_handle ? " · X @" + data.watch.x_handle + (data.watch.x_confirmed ? "" : " (found by search: set company.x_handle to confirm)") : "")
                + (Object.keys(data.watch.errors || {}).length ? " · failed: " + Object.keys(data.watch.errors).join(", ") : "")
              : "not run yet (every 6 hours on the scheduler)"}
          </div>
          {(data.whats_new || []).length === 0 ? (
            <div style={{ fontSize: 13, color: "var(--vn-ink-muted)", lineHeight: 1.5 }}>
              No dated events yet. The Notion sync classifies every change (feature launch, factual update or
              noise) and dates the first two here.
            </div>
          ) : (data.whats_new || []).map((e: any) => (
            <div key={e.id} style={{ borderTop: "1px solid var(--vn-line)", padding: "7px 0", fontSize: 12.5 }}>
              <span style={{ fontFamily: MONO, color: "var(--vn-ink-muted)" }}>{String(e.at).slice(0, 10)}</span>{" "}
              <span style={{ color: "var(--vn-ink)" }}>{e.url ? <a href={e.url} target="_blank" rel="noreferrer" style={{ color: "inherit" }}>{e.title}</a> : e.title}</span>
              {(e.kind || e.source) && (
                <span style={{ fontFamily: MONO, fontSize: 10.5, marginLeft: 6,
                               color: e.kind === "incident" || e.kind === "controversy" ? "var(--vn-bad)" : "var(--vn-ink-faint)" }}>
                  {String(e.kind || "").replace("_", " ")}{String(e.source || "").startsWith("public:") ? " · reported by others" : ""}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {data?.tenant && viewer?.owner && <ClientLink tenant={data.tenant} />}
      {/* A new company is the owner's decision; a client works on their own. */}
      {!isClient && <Onboard onDone={(t) => { writeCompany(t); setTenant(t); setTick((x) => x + 1); }} />}
    </div>
  );
}
