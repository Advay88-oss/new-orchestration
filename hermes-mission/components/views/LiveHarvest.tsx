"use client";

/**
 * What the scout brought back, with its receipts.
 *
 * The Scraped Intelligence view reported a different subsystem entirely (the
 * research_runs / discovered_players registry), so A01's own harvest — the
 * thing that actually runs every cycle — had no surface at all. Worse, the run
 * summary kept only a headline, a type and a date per candidate, so "which
 * source, whose news, pulled when" was thrown away the moment A02 chose a
 * winner.
 *
 * Every column here is read from `harvest.json`. Nothing is inferred: a signal
 * with no identifiable company shows "(unattributed)" rather than being
 * assigned one.
 */

import React, { useCallback, useEffect, useState } from "react";
import { MONO } from "@/lib/colors";
import { EmptyState, SkeletonCard } from "@/components/States";
import { CompanyChip } from "@/components/CompanyChip";

const DIM = "var(--vn-ink-muted)";

function when(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(String(iso));
  return isNaN(d.getTime()) ? String(iso).slice(0, 19).replace("T", " ") : d.toLocaleString();
}

function kindOf(s: { signal_id?: string; source_type?: string; source?: string; source_root?: string }): string {
  const blob = [s.signal_id, s.source_type, s.source, s.source_root].join(" ").toLowerCase();
  if (/twitter|reddit|telegram|\bt\.me\b|x\.com/.test(blob)) return "Post";
  if (/docs|github|blog/.test(blob)) return "Docs";
  if (/llama|defillama/.test(blob)) return "Market data";
  return "News";
}

const SOURCE_BTN: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 6,
  width: "fit-content",
  maxWidth: "100%",
  background: "var(--vn-hover)",
  border: "1px solid var(--vn-line-strong)",
  color: "var(--vn-ink)",
  borderRadius: 8,
  padding: "7px 10px",
  fontFamily: MONO,
  fontSize: 11,
  fontWeight: 650,
  lineHeight: 1.2,
  cursor: "pointer",
  textDecoration: "none",
};

export function LiveHarvest({ onOpenReference }: { onOpenReference?: (id: string) => void }) {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [company, setCompany] = useState<string>("ALL");

  const load = useCallback(() => {
    fetch("/api/gtm/harvest", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => { setData(d); setErr(null); })
      .catch((e) => setErr(String(e.message || e)));
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 20000);
    return () => clearInterval(t);
  }, [load]);

  if (err) {
    return (
      <EmptyState icon="signal" title="No scrape recorded yet"
        body="Each run starts with the Intelligence Scout reading news, Reddit, X, Telegram and DefiLlama. Its signals appear here when the next run starts." />
    );
  }
  if (!data) return <SkeletonCard lines={5} />;

  const signals: any[] = data.signals ?? [];
  const collected = data.collected as { collected_at?: string; used_by?: string; items?: { headline: string; source?: string; kind?: string; style?: string }[] } | null;
  const shown = company === "ALL"
    ? signals
    : signals.filter((s) => (s.entities ?? []).includes(company));

  const sourceRows = Object.entries(data.sources ?? {}) as [string, any][];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {collected?.items?.length ? (
        <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: "16px 18px" }}>
          <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-accent-ink)", fontWeight: 700 }}>COLLECTED RESEARCH</div>
          <p style={{ margin: "6px 0 10px", fontSize: 13.5, color: "var(--vn-ink-body)", lineHeight: 1.45 }}>
            {collected.used_by || "The next post reads this list."} Collected {when(collected.collected_at)}.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {collected.items.filter((item, i, all) => all.findIndex((o) => o.headline === item.headline) === i).slice(0, 12).map((item, i) => (
              <div key={i} style={{ padding: "10px 12px", border: "1px solid var(--vn-line)", borderRadius: 10, background: "var(--vn-sunken)" }}>
                <div style={{ display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
                  <span style={{ fontFamily: MONO, fontSize: 10, letterSpacing: 0.6, textTransform: "uppercase", color: "var(--vn-ink-muted)" }}>{item.kind || "Source"}</span>
                  {item.source ? <span style={{ fontSize: 12, color: "var(--vn-ink-muted)" }}>{item.source}</span> : null}
                </div>
                <div style={{ fontSize: 14.5, color: "var(--vn-ink)", lineHeight: 1.45, marginTop: 4 }}>{item.headline}</div>
                {item.style ? <div style={{ fontSize: 12.5, color: "var(--vn-ink-body)", marginTop: 4, lineHeight: 1.45 }}>{item.style}</div> : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
      <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: "var(--vn-card-pad)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: 12 }}>
          <div>
            <span style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-accent-ink)", fontWeight: 700 }}>
              A01 INTELLIGENCE SCOUT · LIVE HARVEST
            </span>
            <h3 style={{ fontSize: 19, fontWeight: 700, color: "var(--vn-ink)", margin: "4px 0 0" }}>
              {data.totalSignals} signals from {sourceRows.filter(([, v]) => v?.signals).length} sources
            </h3>
            <p style={{ margin: "8px 0 0", fontSize: 13.5, color: "var(--vn-ink-body)", lineHeight: 1.45, maxWidth: 640 }}>
              These are the docs, posts, news pages and market pages the scout took. Open one in References to see the post idea the other agents write from that same source.
            </p>
          </div>
          <div style={{ textAlign: "right", fontFamily: MONO, fontSize: 12, color: DIM }}>
            <div>SCRAPED AT</div>
            <div style={{ color: "var(--vn-ink)", fontWeight: 700 }}>{when(data.scrapedAt)}</div>
            <div style={{ marginTop: 2, display: "flex", gap: 8, justifyContent: "flex-end", alignItems: "center" }}>
              <CompanyChip company={data.company || "vanna"} /> run {data.runId}
            </div>
          </div>
        </div>

        {/* Per source: what answered, what was quiet, and what errored. */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: 12, marginTop: 18 }}>
          {sourceRows.map(([name, v]) => {
            const ok = v?.ok && v?.signals > 0;
            const tone = ok ? "var(--vn-ok)" : v?.ok ? "var(--vn-warn)" : "var(--vn-bad)";
            return (
              <div key={name} style={{ background: "var(--vn-sunken)", border: `1px solid color-mix(in srgb, ${tone} 20%, transparent)`, borderRadius: 8, padding: "12px 14px" }}>
                <div style={{ fontFamily: MONO, fontSize: 10, color: DIM, textTransform: "uppercase" }}>{name}</div>
                <div style={{ fontSize: 17, fontWeight: 700, color: tone, marginTop: 2 }}>
                  {v?.signals ?? 0} signals
                </div>
                {!v?.ok && v?.error && (
                  <div style={{ fontSize: 11, color: "var(--vn-bad)", marginTop: 4 }}>{String(v.error).slice(0, 70)}</div>
                )}
                {v?.ok && !v?.signals && (
                  <div style={{ fontSize: 11, color: "var(--vn-warn)", marginTop: 4 }}>quiet this cycle</div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Companies, as a filter rather than a decoration. */}
      {data.byCompany?.length > 0 && (
        <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: "16px 20px" }}>
          <div style={{ fontFamily: MONO, fontSize: 11, color: DIM, marginBottom: 10 }}>
            COMPANIES &amp; PROTOCOLS SCRAPED — click to filter
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {["ALL", ...data.byCompany.map((c: any) => c.name)].map((name: string) => {
              const on = company === name;
              const count = name === "ALL"
                ? signals.length
                : data.byCompany.find((c: any) => c.name === name)?.count ?? 0;
              return (
                <button
                  key={name}
                  onClick={() => setCompany(name)}
                  style={{
                    background: on ? "var(--vn-accent-soft)" : "var(--vn-hover)",
                    border: `1px solid ${on ? "var(--vn-accent)" : "var(--vn-line-strong)"}`,
                    color: on ? "var(--vn-ink)" : "var(--vn-ink-muted)",
                    padding: "5px 11px", borderRadius: 6, cursor: "pointer",
                    fontFamily: MONO, fontSize: 11, fontWeight: 600,
                  }}
                >
                  {name} <span style={{ color: DIM }}>{count}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* The signals themselves, with full provenance. */}
      <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, overflow: "hidden" }}>
        <div className="responsive-table-container">
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--vn-line)" }}>
                {["Signal", "Companies", "Source", "Observed", "Scraped"].map((h) => (
                  <th key={h} style={{ padding: "12px 16px", fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-muted)", textTransform: "uppercase", whiteSpace: "nowrap" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {shown.map((s: any, i: number) => (
                <tr key={s.signal_id ?? i} style={{ borderBottom: "1px solid var(--vn-line)" }}>
                  <td style={{ padding: "12px 16px", maxWidth: 420 }}>
                    <div style={{ color: "var(--vn-ink)", fontSize: 13, lineHeight: 1.5 }}>{s.headline}</div>
                    {s.metric_change && s.metric_change !== "LIVE_SIGNAL" && (
                      <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ok)", marginTop: 3 }}>{s.metric_change}</div>
                    )}
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                      {(s.entities ?? []).map((e: string) => (
                        <span key={e} style={{ fontFamily: MONO, fontSize: 10, background: "var(--vn-accent-soft)", color: e === "(unattributed)" ? DIM : "var(--vn-accent-ink)", padding: "2px 7px", borderRadius: 6 }}>
                          {e}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 6 }}>
                      <span style={{ fontFamily: MONO, fontSize: 10, color: "var(--vn-accent-ink)", fontWeight: 700 }}>{kindOf(s)}</span>
                      {s.source?.startsWith("http") ? (
                        <a href={s.source} target="_blank" rel="noreferrer" style={SOURCE_BTN}>
                          {s.source_root || "Open source"} ↗
                        </a>
                      ) : (
                        <span style={{ ...SOURCE_BTN, cursor: "default", color: DIM }}>{s.source_root || s.source || "No link"}</span>
                      )}
                      {onOpenReference && s.signal_id && (
                        <button type="button" onClick={() => onOpenReference(String(s.signal_id))} style={SOURCE_BTN}>
                          Open in References
                        </button>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: "12px 16px", fontFamily: MONO, fontSize: 11, color: DIM, whiteSpace: "nowrap" }}>
                    {when(s.observed_at)}
                  </td>
                  <td style={{ padding: "12px 16px", fontFamily: MONO, fontSize: 11, color: DIM, whiteSpace: "nowrap" }}>
                    {when(s.scraped_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
