"use client";

/**
 * Vanna References — what was scraped, where it came from, and what it is for.
 *
 * Scraped Intelligence lists A01's harvest with its receipts, and stops there:
 * a reader saw forty links and nothing about which mattered or what Vanna
 * could do with them. A02 has been reading every harvest since 2026-09-24 —
 * a grade per item, one move per relevant item, and strategies that cite the
 * items they rest on — and none of that was on any page.
 *
 * Every strategy links back to its sources, and every source links out to
 * the original post, doc or article. Nothing here is written by the view:
 * an item A02 did not read shows as unread, not as irrelevant.
 */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { MONO } from "@/lib/colors";

const DIM = "#7B7590";
const CARD = { background: "#0C0716", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 16 } as const;

type Kind = "post" | "docs" | "news" | "data";
const KINDS: { id: "all" | Kind; label: string }[] = [
  { id: "all", label: "All" },
  { id: "post", label: "Posts" },
  { id: "docs", label: "Docs" },
  { id: "news", label: "News" },
  { id: "data", label: "Market data" },
];

const GRADE: Record<string, { tone: string; label: string }> = {
  DIRECT: { tone: "#4ADE9B", label: "DIRECT" },
  ADJACENT: { tone: "#A98CFF", label: "ADJACENT" },
  NONE: { tone: DIM, label: "NOT RELEVANT" },
};
const ORDER: Record<string, number> = { DIRECT: 0, ADJACENT: 1, NONE: 2 };

function when(v: string | null | undefined): string {
  if (!v) return "—";
  const d = new Date(String(v));
  return isNaN(d.getTime()) ? String(v).slice(0, 19) : d.toLocaleString();
}

function Cite({ c }: { c: { id: string; headline: string; url: string | null; channel: string } }) {
  const text = `${c.channel} · ${c.headline.replace(/\s+/g, " ").slice(0, 70)}${c.headline.length > 70 ? "…" : ""}`;
  const style: React.CSSProperties = {
    display: "inline-block", maxWidth: "100%", overflow: "hidden", textOverflow: "ellipsis",
    whiteSpace: "nowrap", verticalAlign: "top",
    background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: 7, padding: "4px 9px", fontSize: 12, color: "#CFC8E0", textDecoration: "none",
  };
  return c.url
    ? <a href={c.url} target="_blank" rel="noopener noreferrer" style={style}>{text} ↗</a>
    : <span style={style}>{text}</span>;
}

export function VannaReferences() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [runId, setRunId] = useState<string>("");
  const [kind, setKind] = useState<"all" | Kind>("all");
  const [relevantOnly, setRelevantOnly] = useState(true);

  const load = useCallback(() => {
    const q = runId ? `?runId=${encodeURIComponent(runId)}` : "";
    fetch(`/api/gtm/references${q}`, { cache: "no-store" })
      .then((r) => r.json().then((j) => (r.ok && j.success ? j : Promise.reject(new Error(j.error || `HTTP ${r.status}`)))))
      .then((d) => { setData(d); setErr(null); })
      .catch((e) => setErr(String(e.message || e)));
  }, [runId]);

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [load]);

  const items: any[] = data?.items ?? [];
  const read = items.some((i) => i.relevance);

  const shown = useMemo(() => {
    return items
      .filter((i) => kind === "all" || i.kind === kind)
      // "Relevant only" means relevant by A02's reading. On an unread run
      // there is no reading to filter by, so everything is shown.
      .filter((i) => !relevantOnly || !read || i.relevance === "DIRECT" || i.relevance === "ADJACENT")
      .sort((a, b) => (ORDER[a.relevance] ?? 3) - (ORDER[b.relevance] ?? 3));
  }, [items, kind, relevantOnly, read]);

  if (err) {
    return (
      <div style={{ ...CARD, padding: "20px 24px", fontFamily: MONO, fontSize: 13, color: DIM }}>
        No references yet — run a cycle and A01 will scrape some. ({err})
      </div>
    );
  }
  if (!data) return null;

  const land = data.landscape;
  const strategies: any[] = land?.strategies ?? [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, minWidth: 0 }}>
      {/* Header: which run, when, and a selector for the recent ones. */}
      <div style={{ ...CARD, borderRadius: 18, padding: "22px 26px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
          <div style={{ minWidth: 0 }}>
            <span style={{ fontFamily: MONO, fontSize: 11, color: "#A98CFF", fontWeight: 700 }}>
              VANNA REFERENCES · A01 HARVEST × A02 READING
            </span>
            <h3 style={{ fontSize: 19, fontWeight: 700, color: "#FFFFFF", margin: "4px 0 0" }}>
              {items.length} live references
              {read && <> · {items.filter((i) => i.relevance === "DIRECT").length} direct, {items.filter((i) => i.relevance === "ADJACENT").length} adjacent</>}
            </h3>
            <div style={{ fontFamily: MONO, fontSize: 12, color: DIM, marginTop: 4 }}>
              scraped {when(data.scrapedAt)}
            </div>
          </div>
          <label style={{ fontFamily: MONO, fontSize: 11, color: DIM, display: "flex", flexDirection: "column", gap: 4 }}>
            RUN
            <select
              value={runId || data.runId}
              onChange={(e) => setRunId(e.target.value)}
              style={{ background: "#080310", color: "#FFFFFF", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, padding: "6px 8px", fontFamily: MONO, fontSize: 12, maxWidth: "100%" }}
            >
              {(data.recent ?? []).map((r: any) => (
                <option key={r.runId} value={r.runId}>
                  {r.runId}{r.hasAnalysis ? "" : " (unread)"}
                </option>
              ))}
            </select>
          </label>
        </div>

        {data.analysisNote && (
          <div style={{ marginTop: 14, background: "rgba(245,165,36,0.08)", border: "1px solid rgba(245,165,36,0.3)", borderRadius: 10, padding: "10px 14px", fontSize: 13, color: "#F5C26B" }}>
            This run's references were not read, so there are no strategies for it. {data.analysisNote}
            {(data.recent ?? []).some((r: any) => r.hasAnalysis) && " Pick a run without \"(unread)\" above."}
          </div>
        )}
      </div>

      {/* What Vanna can do — the strategies, each with its evidence. */}
      {land && (
        <div style={{ ...CARD, padding: "20px 24px" }}>
          <div style={{ fontFamily: MONO, fontSize: 11, color: "#A98CFF", fontWeight: 700 }}>
            WHAT VANNA CAN DO
          </div>
          {land.forVanna && (
            <p style={{ fontSize: 15, color: "#FFFFFF", lineHeight: 1.6, margin: "8px 0 0" }}>{land.forVanna}</p>
          )}

          {strategies.length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))", gap: 12, marginTop: 16 }}>
              {strategies.map((st, i) => (
                <div key={i} style={{ background: "#080310", border: "1px solid rgba(112,58,230,0.35)", borderRadius: 12, padding: "16px 18px", minWidth: 0 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "baseline" }}>
                    <div style={{ fontSize: 15, fontWeight: 700, color: "#FFFFFF" }}>{st.title}</div>
                    {st.horizon && (
                      <span style={{ fontFamily: MONO, fontSize: 10, color: "#A98CFF", whiteSpace: "nowrap" }}>
                        {String(st.horizon).toUpperCase()}
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: 13, color: "#E6E1F0", lineHeight: 1.55, margin: "8px 0 0" }}>{st.move}</p>
                  {st.rationale && (
                    <p style={{ fontSize: 12, color: DIM, lineHeight: 1.5, margin: "6px 0 0" }}>Why now: {st.rationale}</p>
                  )}
                  <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 12 }}>
                    <span style={{ fontFamily: MONO, fontSize: 10, color: DIM }}>BASED ON</span>
                    {(st.cites ?? []).map((c: any) => <Cite key={c.id} c={c} />)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: 13, color: DIM, margin: "12px 0 0" }}>
              No strategies recorded for this run. Runs read before strategies were added carry the landscape only.
            </p>
          )}

          {/* The picture behind the strategies. */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 280px), 1fr))", gap: 16, marginTop: 18 }}>
            {land.summary && (
              <div style={{ minWidth: 0 }}>
                <div style={{ fontFamily: MONO, fontSize: 10, color: DIM }}>THE MARKET RIGHT NOW</div>
                <p style={{ fontSize: 13, color: "#CFC8E0", lineHeight: 1.55, margin: "6px 0 0" }}>{land.summary}</p>
              </div>
            )}
            {(land.quietOn ?? []).length > 0 && (
              <div style={{ minWidth: 0 }}>
                <div style={{ fontFamily: MONO, fontSize: 10, color: DIM }}>WHAT NOBODY IS TALKING ABOUT</div>
                <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 13, color: "#CFC8E0", lineHeight: 1.55 }}>
                  {land.quietOn.map((q: string, i: number) => <li key={i}>{q}</li>)}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Filters. */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
        {KINDS.map((k) => {
          const on = kind === k.id;
          const n = k.id === "all" ? items.length : data.counts?.[k.id] ?? 0;
          return (
            <button
              key={k.id}
              onClick={() => setKind(k.id)}
              style={{
                background: on ? "rgba(112,58,230,0.3)" : "rgba(255,255,255,0.04)",
                border: `1px solid ${on ? "#703AE6" : "rgba(255,255,255,0.1)"}`,
                color: on ? "#FFFFFF" : DIM,
                padding: "6px 12px", borderRadius: 8, cursor: "pointer",
                fontFamily: MONO, fontSize: 12, fontWeight: 600,
              }}
            >
              {k.label} <span style={{ color: DIM }}>{n}</span>
            </button>
          );
        })}
        {read && (
          <label style={{ display: "flex", alignItems: "center", gap: 6, marginLeft: "auto", fontFamily: MONO, fontSize: 12, color: DIM, cursor: "pointer" }}>
            <input type="checkbox" checked={relevantOnly} onChange={(e) => setRelevantOnly(e.target.checked)} />
            relevant to Vanna only
          </label>
        )}
      </div>

      {/* The references. */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {shown.length === 0 && (
          <div style={{ ...CARD, padding: "18px 22px", fontSize: 13, color: DIM }}>
            Nothing in this filter. {relevantOnly && read && "Untick \"relevant to Vanna only\" to see every item."}
          </div>
        )}
        {shown.map((i) => {
          const g = i.relevance ? GRADE[i.relevance] : null;
          return (
            <div key={i.id} style={{ ...CARD, borderRadius: 14, padding: "16px 20px", minWidth: 0 }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center", fontFamily: MONO, fontSize: 11 }}>
                <span style={{ color: "#A98CFF", fontWeight: 700 }}>{i.channel.toUpperCase()}</span>
                {i.publisher && <span style={{ color: DIM }}>· {i.publisher}</span>}
                <span style={{ color: DIM }}>· {when(i.observedAt)}</span>
                <span style={{ marginLeft: "auto", color: g ? g.tone : DIM, border: `1px solid ${g ? g.tone + "55" : "rgba(255,255,255,0.1)"}`, borderRadius: 6, padding: "2px 8px", fontWeight: 700 }}>
                  {g ? g.label : "UNREAD"}
                </span>
              </div>

              <div style={{ marginTop: 8, fontSize: 15, fontWeight: 600, lineHeight: 1.45, wordBreak: "break-word" }}>
                {i.url
                  ? <a href={i.url} target="_blank" rel="noopener noreferrer" style={{ color: "#FFFFFF", textDecoration: "none" }}>{i.headline} <span style={{ color: DIM }}>↗</span></a>
                  : <span style={{ color: "#FFFFFF" }}>{i.headline}</span>}
              </div>

              {i.whatItIs && (
                <p style={{ fontSize: 13, color: "#CFC8E0", lineHeight: 1.5, margin: "6px 0 0" }}>{i.whatItIs}</p>
              )}
              {i.vannaMove && (
                <div style={{ marginTop: 10, background: "rgba(112,58,230,0.1)", borderLeft: "3px solid #703AE6", borderRadius: 6, padding: "8px 12px", fontSize: 13, color: "#FFFFFF", lineHeight: 1.5 }}>
                  <span style={{ fontFamily: MONO, fontSize: 10, color: "#A98CFF", fontWeight: 700, marginRight: 8 }}>VANNA CAN</span>
                  {i.vannaMove}
                </div>
              )}
              {i.why && (
                <p style={{ fontSize: 12, color: DIM, lineHeight: 1.5, margin: "8px 0 0" }}>{i.why}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
