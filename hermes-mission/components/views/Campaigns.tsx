"use client";

import React, { useCallback, useEffect, useState } from "react";
import { MONO } from "@/lib/colors";
import { ErrorState, ViewSkeleton } from "@/components/States";

const card: React.CSSProperties = {
  background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 14, padding: 22,
};
const label: React.CSSProperties = {
  fontFamily: MONO, fontSize: 10.5, letterSpacing: 0.8, textTransform: "uppercase",
  color: "var(--vn-ink-muted)", marginBottom: 6,
};
const fmt = (n: number | null | undefined) => (n == null ? "—" : n.toLocaleString("en-US"));

function when(v: string | undefined) {
  if (!v) return "";
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? v.slice(0, 16) : d.toLocaleString();
}

export function Campaigns() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    fetch("/api/gtm/campaigns", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => { if (d.ok) { setData(d); setErr(null); } else setErr(d.error || "Could not read campaigns"); })
      .catch((e) => setErr(String(e)));
  }, []);

  useEffect(() => { load(); }, [load]);

  const running = busy || data?.job?.state === "running";
  useEffect(() => {
    if (!running) return;
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [running, load]);

  useEffect(() => {
    if (busy && data?.job?.state === "done") setBusy(false);
    if (busy && data?.job?.state === "failed") {
      setBusy(false);
      setMsg(data?.job?.error || "The scrape failed");
    }
  }, [busy, data]);

  const go = async (q?: string, src?: string) => {
    const asked = (q || "").trim();
    const from = (src || "").trim() || "galxe";
    if (!asked) return;
    setMsg(null);
    setBusy(true);
    const res = await fetch("/api/gtm/campaigns", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: asked, source: from }),
    });
    const j = await res.json().catch(() => ({}));
    if (!j.ok) {
      setBusy(false);
      setMsg(j.error || "That did not start");
      return;
    }
    setTimeout(load, 1500);
  };

  if (!data && !err) return <ViewSkeleton cards={3} label="Loading campaigns" />;
  if (err && !data) return <ErrorState title="Campaigns are unavailable" detail={err} />;

  const shelves: any[] = data?.shelves?.length
    ? data.shelves
    : (data?.campaigns ? [data] : []);

  return (
    <div className="vanna-section">
      <div style={card}>
        <div style={label}>For the GTM engineer</div>
        <h2 style={{ fontSize: 24, fontWeight: 800, color: "var(--vn-ink)", margin: "4px 0 8px" }}>Campaigns</h2>
        <p style={{ fontSize: 13.5, color: "var(--vn-ink-muted)", maxWidth: 760, lineHeight: 1.5, margin: 0 }}>
          Tell the Assistant the campaign and the source. Each source keeps its own list here.
          The table is numbered by people who joined, most first. Campaigns that 0 or 1 people joined are left out.
        </p>
        {running && <div style={{ fontFamily: MONO, fontSize: 12, color: "var(--vn-ink-muted)", marginTop: 10 }}>Reading the live listing, then writing the GTM notes. About a minute.</div>}
        {msg && <div style={{ fontSize: 12.5, color: "var(--vn-bad)", marginTop: 10 }}>{msg}</div>}
      </div>

      {shelves.map((shelf: any) => {
        const rows: any[] = shelf.campaigns || [];
        const picked = rows.filter((c) => c.selected).slice().sort((a, b) => (a.rank || 0) - (b.rank || 0));
        const title = shelf.source_input || shelf.source || "Source";
        return (
          <section key={title + (shelf.scraped_at || "")} style={{ marginTop: 18 }}>
            <div style={{ ...card, display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              <div>
                <div style={label}>{title}</div>
                <div style={{ fontSize: 14, color: "var(--vn-ink)", marginTop: 4 }}>{shelf.query}</div>
                <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-muted)", marginTop: 6, lineHeight: 1.5 }}>
                  {shelf.count} campaigns · {when(shelf.scraped_at)}
                  {shelf.order ? <div>{shelf.order}</div> : null}
                </div>
              </div>
              <button onClick={() => go(shelf.query, shelf.source_input || shelf.source)}
                      disabled={running}
                      style={{ background: "transparent", color: "var(--vn-ink)", border: "1px solid var(--vn-line-strong)",
                               borderRadius: 8, padding: "8px 14px", fontWeight: 600, cursor: "pointer" }}>
                Search again
              </button>
            </div>
            {rows.length > 0 && (
              <div style={{ ...card, marginTop: 10, overflowX: "auto" }}>
                <div style={label}>Number 1 joined the most</div>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                  <thead>
                    <tr style={{ color: "var(--vn-ink-muted)", textAlign: "left" }}>
                      {["#", "Campaign", "Participants", "Reward", "Space", "Chain"].map((h) => (
                        <th key={h} style={{ padding: "6px 8px", fontWeight: 500 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((c) => (
                      <tr key={c.id} style={{ borderTop: "1px solid var(--vn-line)", background: c.selected ? "var(--vn-accent-soft)" : "transparent" }}>
                        <td style={{ padding: "8px", fontFamily: MONO, color: "var(--vn-ink-muted)" }}>{c.rank}</td>
                        <td style={{ padding: "8px" }}>
                          <a href={c.url} target="_blank" rel="noreferrer" style={{ color: "var(--vn-ink)", textDecoration: "none" }}>{c.name}</a>
                          <div style={{ fontFamily: MONO, fontSize: 10.5, color: "var(--vn-ink-muted)", marginTop: 2 }}>{c.status} · {c.type}</div>
                        </td>
                        <td style={{ padding: "8px", fontFamily: MONO }}>{fmt(c.participants)}</td>
                        <td style={{ padding: "8px" }}>{c.reward}</td>
                        <td style={{ padding: "8px" }}>{c.space}{c.verified ? " · verified" : ""}</td>
                        <td style={{ padding: "8px", fontFamily: MONO, fontSize: 11 }}>{c.chain}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div style={{ display: "flex", flexDirection: "column", gap: 14, marginTop: 10 }}>
              {picked.map((c) => (
                <article key={c.id} style={card}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "baseline" }}>
                    <div>
                      <div style={label}>{c.rank}. {c.related === "close" ? "Close to Vanna" : "A usable idea"}</div>
                      <h3 style={{ margin: "4px 0 0", fontSize: 18, color: "var(--vn-ink)", lineHeight: 1.35 }}>{c.name}</h3>
                    </div>
                    <a href={c.url} target="_blank" rel="noreferrer" style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-accent-light)", textDecoration: "none" }}>
                      {String(c.url || "").includes("galxe.com") ? "Open on Galxe" : "Open source"} ↗
                    </a>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 10, marginTop: 14 }}>
                    <Fact k="Joined" v={c.participants == null ? "Not stated" : fmt(c.participants)} />
                    <Fact k="Reward" v={c.reward} />
                    <Fact k="Who runs it" v={(c.space || "—") + (c.verified ? " · verified" : "")} />
                    <Fact k="Where" v={[c.status, c.type, c.chain].filter(Boolean).join(" · ") || "—"} />
                  </div>
                  <Field k="The listing says" v={c.description} />
                  <Field k="Why this one" v={c.why_selected} />
                  <Field k="Worth it?" v={worthLine(c)} />
                  <Field k="What Vanna can do" v={c.vanna_can} />
                  <Field k="Why this would work" v={c.why_it_works} />
                  <Field k="What else we can do" v={c.what_else} />
                </article>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function worthLine(c: { worth?: string; worth_why?: string }) {
  const why = (c.worth_why || "").trim();
  const tag = (c.worth || "").trim();
  if (!tag) return why;
  if (why.toLowerCase().startsWith(tag.toLowerCase())) return why;
  return tag + (why ? ". " + why : "");
}

function Fact({ k, v }: { k: string; v?: string }) {
  return (
    <div style={{ background: "var(--vn-sunken)", borderRadius: 8, padding: "8px 10px" }}>
      <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: 0.6, textTransform: "uppercase", color: "var(--vn-ink-muted)" }}>{k}</div>
      <div style={{ fontSize: 13, color: "var(--vn-ink)", marginTop: 3, lineHeight: 1.4 }}>{v || "—"}</div>
    </div>
  );
}

function Field({ k, v }: { k: string; v?: string }) {
  if (!v || !String(v).trim()) return null;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(140px, 180px) 1fr", gap: "8px 16px", padding: "12px 0", borderTop: "1px solid var(--vn-line)", marginTop: 12 }}>
      <div style={{ fontFamily: MONO, fontSize: 11, letterSpacing: 0.4, textTransform: "uppercase", color: "var(--vn-ink-muted)" }}>{k}</div>
      <div style={{ fontSize: 15, color: "var(--vn-ink)", lineHeight: 1.55 }}>{v}</div>
    </div>
  );
}
