"use client";

import React, { useCallback, useEffect, useState } from "react";
import { MONO } from "@/lib/colors";
import { ErrorState, ViewSkeleton } from "@/components/States";
import { COMPANY_EVENT, readCompany, writeCompany } from "@/lib/company";
import type { MissionVM } from "@/lib/viewmodel";

const cardStyle: React.CSSProperties = {
  background: "var(--vn-surface)",
  border: "1px solid var(--vn-line)",
  borderRadius: 14,
  padding: 24,
  marginBottom: 24,
  boxShadow: "0 4px 16px rgba(0, 0, 0, 0.2)",
};

const subcardStyle: React.CSSProperties = {
  background: "var(--vn-sunken)",
  border: "1px solid var(--vn-line)",
  borderRadius: 10,
  padding: 16,
};

const labelStyle: React.CSSProperties = {
  fontFamily: MONO,
  fontSize: 10.5,
  letterSpacing: 0.8,
  textTransform: "uppercase",
  color: "var(--vn-ink-muted)",
  marginBottom: 6,
};

const fmt = (n: number | null | undefined) => (n == null ? "—" : n.toLocaleString("en-US"));
const day = (s: string | undefined) => (s ? String(s).slice(0, 10) : "");

const CHANNEL: Record<string, string> = {
  x: "X", linkedin: "LinkedIn", reddit: "Reddit", reference: "Docs",
};

const FIELDS: { key: string; label: string }[] = [
  { key: "this_post", label: "What this post is doing" },
  { key: "vanna_can", label: "What Vanna can do" },
  { key: "how", label: "How" },
];

function Line({ k, v }: { k: string; v?: string }) {
  if (!v || !String(v).trim()) return null;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(148px, 190px) 1fr", gap: "8px 16px", padding: "11px 0", borderTop: "1px solid var(--vn-line)" }}>
      <div style={{ fontFamily: MONO, fontSize: 11, letterSpacing: 0.4, textTransform: "uppercase", color: "var(--vn-ink-muted)" }}>{k}</div>
      <div style={{ fontSize: 15, color: "var(--vn-ink)", lineHeight: 1.55, whiteSpace: "pre-wrap" }}>{v}</div>
    </div>
  );
}

function Strategy({ m }: { m: any }) {
  const value = (key: string) => {
    if (key === "this_post") return m.this_post || m.did;
    if (key === "vanna_can") return m.vanna_can || m.adapt || m.vanna_move;
    if (key === "how") return m.how || m.why || m.what_worked;
    return m[key];
  };
  return (
    <article style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: "16px 18px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "baseline", flexWrap: "wrap", marginBottom: 8 }}>
        <div style={labelStyle}>From their {CHANNEL[m.channel] || "post"}</div>
        <a href={m.url} target="_blank" rel="noreferrer" style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-accent-light)", textDecoration: "none" }}>
          {CHANNEL[m.channel] || "Source"} · {day(m.at) || "source"} ↗
        </a>
      </div>
      {FIELDS.map((f) => (
        <Line key={f.key} k={f.label} v={value(f.key) || "—"} />
      ))}
      {(m.post_line || m.visual || m.video) && (
        <div style={{ marginTop: 8 }}>
          <div style={{ ...labelStyle, marginTop: 8 }}>What they would make from this</div>
          <Line k="Post" v={m.post_line} />
          <Line k="Visual" v={m.visual} />
          <Line k="Video" v={m.video} />
          <div style={{ fontSize: 12, color: "var(--vn-ink-faint)", marginTop: 6 }}>A plan. The poster and the video are not rendered on this shelf.</div>
        </div>
      )}
      {m.format ? (
        <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-accent-light)", marginTop: 8 }}>{m.format}</div>
      ) : null}
      {m.source_text ? (
        <div style={{ marginTop: 12, padding: "10px 12px", background: "var(--vn-sunken)", borderRadius: 8, fontSize: 13.5, color: "var(--vn-ink-muted)", lineHeight: 1.5 }}>
          Their post: &ldquo;{m.source_text}&rdquo;
        </div>
      ) : null}
    </article>
  );
}

export function WhatVannaCanDo({ vm: _vm, tenant }: { vm?: MissionVM; tenant?: string }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState<string>("ALL");
  const [msg, setMsg] = useState<string | null>(null);
  const [company, setCompany] = useState(tenant || "");

  useEffect(() => {
    // This page opens on Vanna, where the collected posts live. A company
    // button, or a switch made while the page is open, moves it.
    const on = () => setCompany(readCompany());
    window.addEventListener(COMPANY_EVENT, on);
    return () => window.removeEventListener(COMPANY_EVENT, on);
  }, []);

  const load = useCallback(() => {
    const q = company ? "?tenant=" + encodeURIComponent(company) : "";
    fetch("/api/gtm/brain/inspiration" + q, { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        if (d.ok) setData(d);
        else setMsg(d.error || "Could not load this company's posts");
      })
      .catch((e) => setMsg(String(e)))
      .finally(() => setLoading(false));
  }, [company]);

  useEffect(() => { load(); }, [load]);

  const brands: any[] = data?.brands || data?.inspiration || [];
  const running = brands.some((b) => b.job?.state === "running");

  useEffect(() => {
    if (!running) return;
    const t = setInterval(load, 6000);
    return () => clearInterval(t);
  }, [running, load]);

  if (loading) return <ViewSkeleton cards={3} label="Loading What Vanna Can Do" />;
  if (!data) return <ErrorState title="What Vanna can do is unavailable" detail={msg || "Could not reach this company's posts."} />;

  const visible = brands.filter((b) => active === "ALL" || b.id === active);

  return (
    <div className="vanna-section">
      <div style={cardStyle}>
        {(data.tenants || []).length > 1 && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", marginBottom: 14 }}>
            <span style={{ fontSize: 12, color: "var(--vn-ink-muted)" }}>Company</span>
            {(data.tenants as string[]).map((t) => (
              <button key={t} onClick={() => { writeCompany(t); setCompany(t); setLoading(true); setActive("ALL"); }}
                      style={{ fontFamily: MONO, fontSize: 12, padding: "6px 12px", borderRadius: 6, cursor: "pointer",
                               border: "1px solid " + (t === (data.tenant || company) ? "var(--vn-accent)" : "var(--vn-line)"),
                               background: t === (data.tenant || company) ? "var(--vn-accent-soft)" : "transparent", color: "var(--vn-ink)" }}>
                {t}
              </button>
            ))}
          </div>
        )}
        <div style={labelStyle}>FOR {(data.company || "VANNA").toString().toUpperCase()}</div>
        <h2 style={{ fontSize: 24, fontWeight: 800, color: "var(--vn-ink)", margin: "4px 0" }}>
          What {data.company || "Vanna"} can do, taking inspiration from each brand
        </h2>
        <p style={{ fontSize: 13.5, color: "var(--vn-ink-muted)", maxWidth: 820, lineHeight: 1.5, margin: "4px 0 0" }}>
          Tell the Assistant the company, or set a scrape. The agents file each competitor here, read its posts,
          and write what a post from it could be. Nothing on this page is typed in by hand.
        </p>
        {msg && <div style={{ fontSize: 12.5, color: "var(--vn-bad)", marginTop: 10 }}>{msg}</div>}
      </div>

      {brands.length === 0 ? (
        <div style={{ ...cardStyle, fontSize: 13, color: "var(--vn-ink-muted)" }}>
          Nothing here yet. Tell the Assistant a company, or let a scrape run. The cards appear on their own.
          {data.tenant && data.tenant !== "vanna" && (
            <div style={{ marginTop: 8 }}>Posts already collected sit on Vanna. Choose vanna in the company row to see them.</div>
          )}
        </div>
      ) : (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", borderBottom: "1px solid var(--vn-line)", paddingBottom: 14, marginBottom: 20 }}>
          {[{ id: "ALL", name: "All brands" }, ...brands].map((tab: any) => (
            <button key={tab.id} onClick={() => setActive(tab.id)}
                    style={{
                      background: active === tab.id ? "var(--vn-accent-soft)" : "var(--vn-hover)",
                      border: `1px solid ${active === tab.id ? "var(--vn-accent)" : "var(--vn-line-strong)"}`,
                      color: active === tab.id ? "var(--vn-ink)" : "var(--vn-ink-muted)",
                      padding: "6px 14px", borderRadius: 8, cursor: "pointer", fontFamily: MONO, fontSize: 11.5, fontWeight: 700,
                    }}>
              {tab.name}
            </button>
          ))}
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
        {visible.map((b: any) => {
          const fetching = b.job?.state === "running";
          return (
            <div key={b.id} style={cardStyle}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12, borderBottom: "1px solid var(--vn-line)", paddingBottom: 16, marginBottom: 20 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                  <h3 style={{ fontSize: 20, fontWeight: 800, color: "var(--vn-ink)", margin: 0 }}>{b.name}</h3>
                  {b.handle && (
                    <a href={"https://x.com/" + b.handle.replace("@", "")} target="_blank" rel="noreferrer"
                       style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-accent-light)", background: "var(--vn-hover)", padding: "2px 8px", borderRadius: 6, textDecoration: "none" }}>
                      {b.handle}
                    </a>
                  )}
                  <span style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-muted)" }}>
                    {fetching ? "fetching…" : b.fetched_at ? "fetched " + day(b.fetched_at) : "not fetched yet"}
                  </span>
                </div>
              </div>

              {Object.keys(b.errors || {}).length > 0 && (
                <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-warn)", marginBottom: 12 }}>
                  {Object.entries(b.errors).map(([k, v]) => k + ": " + String(v)).join(" · ")}
                </div>
              )}

              <div style={labelStyle}>WHERE {b.name.toUpperCase()} POSTS, AND WHERE THE RESPONSE IS · LAST {b.window_days} DAYS</div>
              {b.hype_origin && (
                <div style={{ fontSize: 13.5, color: "var(--vn-ink-body)", lineHeight: 1.5, marginBottom: 12 }}>{b.hype_origin}</div>
              )}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 10, marginBottom: 18 }}>
                {Object.entries(b.channels || {}).map(([id, ch]: [string, any]) => (
                  <div key={id} style={subcardStyle}>
                    <div style={{ fontFamily: MONO, fontSize: 10, color: "var(--vn-ink-muted)" }}>{ch.label}</div>
                    <div style={{ fontSize: 20, fontWeight: 800, color: "var(--vn-ink)", marginTop: 4 }}>
                      {ch.posts}<span style={{ fontSize: 12, fontWeight: 600, color: "var(--vn-ink-muted)" }}>{id === "reddit" ? " threads naming it" : " posts"}</span>
                    </div>
                    <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-body)", marginTop: 6, lineHeight: 1.5 }}>
                      {ch.counted
                        ? <>{fmt(ch.likes)} likes · {fmt(ch.comments)} replies<br />{fmt(ch.reposts)} reposts · {fmt(ch.views)} views</>
                        : <>Counts appear when the source reports them</>}
                    </div>
                  </div>
                ))}
              </div>

              {(b.agents || []).length > 0 && (
                <div style={{ marginBottom: 18 }}>
                  <div style={labelStyle}>WHO DID THIS</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {b.agents.map((a: any) => (
                      <div key={a.id} style={{ display: "flex", gap: 10, alignItems: "baseline", flexWrap: "wrap" }}>
                        <span style={{ fontFamily: MONO, fontSize: 11, color: a.status === "ok" ? "var(--vn-ok)" : "var(--vn-warn)", minWidth: 168 }}>
                          {a.name}
                        </span>
                        <span style={{ fontSize: 13, color: "var(--vn-ink-body)", lineHeight: 1.45 }}>{a.detail}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div style={labelStyle}>WHAT { (data.company || "VANNA").toString().toUpperCase() } CAN DO FROM {b.name.toUpperCase()}</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 18 }}>
                {(b.vanna_moves || []).length === 0 ? (
                  <div style={{ ...subcardStyle, fontSize: 12.5, color: "var(--vn-ink-muted)" }}>
                    {fetching ? "Being written from the posts that got the response…" : "No strategy yet. Refresh to write one from each post that got a response."}
                  </div>
                ) : b.vanna_moves.map((m: any, i: number) => (
                  <Strategy key={i} m={m} />
                ))}
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div style={labelStyle}>THE POSTS THIS COMES FROM</div>
                <span style={{ fontFamily: MONO, fontSize: 10.5, color: "var(--vn-ink-muted)" }}>top {(b.top_posts || []).length} by response</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 12 }}>
                {(b.top_posts || []).length === 0 ? (
                  <div style={{ ...subcardStyle, fontSize: 12.5, color: "var(--vn-ink-muted)" }}>
                    {fetching ? "Fetching…" : "No posts in the last " + b.window_days + " days."}
                  </div>
                ) : b.top_posts.map((p: any, i: number) => {
                  const x = p.channel === "x";
                  const tone = p.channel === "linkedin" ? "#0A66C2" : p.channel === "reddit" ? "#FF4500" : p.channel === "reference" ? "var(--vn-accent-ink)" : "#1D9BF0";
                  const chip = p.channel === "x" ? "X" : p.channel === "linkedin" ? "LinkedIn" : p.channel === "reference" ? "Docs" : (p.by || "Reddit");
                  return (
                    <div key={(p.url || "post") + ":" + i} style={subcardStyle}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6, gap: 6 }}>
                        <span style={{
                          fontFamily: MONO, fontSize: 10, fontWeight: 700, padding: "2px 6px", borderRadius: 4,
                          background: "var(--vn-hover)",
                          color: tone,
                          border: "1px solid var(--vn-line)",
                        }}>
                          {chip}
                        </span>
                        <span style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-muted)" }}>{day(p.at)}</span>
                      </div>
                      <div style={{ fontSize: 13, color: "var(--vn-ink)", lineHeight: 1.45, margin: "8px 0" }}>
                        &ldquo;{String(p.text || "").slice(0, 320)}&rdquo;
                      </div>
                      <a href={p.url} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: "var(--vn-accent-light)", textDecoration: "none" }}>
                        View original post ↗
                      </a>
                      <div style={{ fontFamily: MONO, fontSize: 10.5, color: "var(--vn-ink-body)", marginTop: 10, paddingTop: 8, borderTop: "1px solid var(--vn-line)" }}>
                        {x
                          ? <>{fmt(p.likes)} likes · {fmt(p.reposts)} reposts · {fmt(p.replies)} replies · {fmt(p.views)} views</>
                          : <>Counts appear when the source reports them</>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
