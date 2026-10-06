"use client";

/**
 * Learning — the fast loop, visible and steerable (the architecture's
 * "learning dashboard: which arms are winning, reward trend; the enterprise
 * can lock an arm or pillar").
 *
 *  - Arms: each strategy choice's record (posterior mean, runs), with a lock
 *    the founder can set; a locked option is used every run.
 *  - Reward trend: every run's reward event and where it came from — the
 *    reviewer's hard gate, the founder's decision, engagement.
 *  - Engagement: nothing publishes on its own, so a post's metrics are
 *    entered here after it goes out; they are normalised against the brand's
 *    own baseline.
 *  - Preference pairs: drafts the founder edited before approving.
 */

import React, { useCallback, useEffect, useState } from "react";
import { MONO } from "@/lib/colors";
import { ErrorState, ViewSkeleton } from "@/components/States";
import { CompanyChip } from "@/components/CompanyChip";
import { COMPANY_EVENT, readCompany, writeCompany } from "@/lib/company";

const card: React.CSSProperties = {
  background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: 18,
};
const label: React.CSSProperties = {
  fontFamily: MONO, fontSize: 10.5, letterSpacing: 0.8, textTransform: "uppercase",
  color: "var(--vn-ink-muted)", marginBottom: 10,
};
const DIM_LABEL: Record<string, string> = {
  pillar: "Narrative pillar",
  technical_depth: "Technical Grounding Level (Code vs Docs)",
  format: "Format (as published)",
  hook_type: "Hook type",
  length: "Post length",
  slot: "Posting slot (as published)"
};

function said(e: any) {
  if (e.reviewer_ok === 0) return "The reviewer blocked it.";
  const h = Number(e.human);
  if (h === 1) return "You approved it.";
  if (h === 0.8) return "You edited it, then approved.";
  if (h === 0.3) return "You sent it back.";
  if (h === 0) return "You stopped it.";
  return "Recorded. Waiting on your decision.";
}

export function Learning() {
  const [d, setD] = useState<any | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tenant, setTenant] = useState("");
  const [companies, setCompanies] = useState<string[]>([]);

  useEffect(() => {
    const apply = () => setTenant(readCompany());
    apply();
    window.addEventListener(COMPANY_EVENT, apply);
    return () => window.removeEventListener(COMPANY_EVENT, apply);
  }, []);

  const load = useCallback(() => {
    const q = tenant ? "?tenant=" + encodeURIComponent(tenant) : "";
    fetch("/api/gtm/learning" + q, { cache: "no-store" })
      .then((r) => r.json())
      .then((j) => (j.ok ? setD(j) : setErr(j.error || "unavailable")))
      .catch((e) => setErr(String(e)));
    fetch("/api/gtm/brain/inspiration" + q, { cache: "no-store" })
      .then((r) => r.json())
      .then((j) => { if (Array.isArray(j.tenants)) setCompanies(j.tenants); })
      .catch(() => {});
  }, [tenant]);
  useEffect(() => { load(); }, [load]);

  if (err) return <section className="vanna-section"><ErrorState title="The learning loop is unavailable" detail={err} /></section>;
  if (!d) return <ViewSkeleton cards={3} label="Loading the learning loop" />;

  const leans: string[] = [];
  for (const [dim, rows] of Object.entries((d.arms || {}) as Record<string, any[]>)) {
    const tried = (rows || []).filter((r) => r.n);
    if (!tried.length) continue;
    const top = tried.slice().sort((a, b) => b.mean - a.mean)[0];
    leans.push((DIM_LABEL[dim] || dim) + ": " + top.option + ", from " + top.n + (top.n === 1 ? " run" : " runs"));
  }

  return (
    <div className="vanna-section">
      <div style={card}>
        <div style={{ marginBottom: 10, display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", fontSize: 12.5, color: "var(--vn-ink-muted)" }}>
          <CompanyChip company={d.company || tenant || "vanna"} size="md" /> this company's learning record
          {companies.length > 1 && companies.map((t) => (
            <button key={t} onClick={() => { writeCompany(t); setTenant(t); }}
                    style={{ fontFamily: MONO, fontSize: 11, padding: "4px 10px", borderRadius: 6, cursor: "pointer",
                             border: "1px solid " + ((d.company || tenant) === t ? "var(--vn-accent)" : "var(--vn-line)"),
                             background: (d.company || tenant) === t ? "var(--vn-accent-soft)" : "transparent", color: "var(--vn-ink)" }}>
              {t}
            </button>
          ))}
        </div>
        <h2 style={{ fontSize: 22, fontWeight: 800, color: "var(--vn-ink)", margin: "8px 0" }}>What the agents remember</h2>
        <div style={{ fontSize: 14.5, color: "var(--vn-ink-body)", lineHeight: 1.6, maxWidth: 720 }}>
          This runs on its own. When you approve a post, send it back, or stop it, that decision is stored.
          The next post uses it. You do not set a gap or a score on this page.
          {d.n_events ? " They have " + d.n_events + " decisions so far." : " Nothing is stored yet."}
        </div>
      </div>

      <div style={card}>
        <div style={label}>What they lean toward</div>
        {leans.length === 0 && (
          <div style={{ fontSize: 14, color: "var(--vn-ink-muted)" }}>No pattern yet. It appears after a few decisions.</div>
        )}
        {leans.map((line) => (
          <div key={line} style={{ fontSize: 14.5, color: "var(--vn-ink)", padding: "8px 0", borderTop: "1px solid var(--vn-line)", lineHeight: 1.45 }}>{line}</div>
        ))}
      </div>

      <div style={card}>
        <div style={label}>Recent decisions</div>
        {(d.events as any[]).length === 0 && (
          <div style={{ fontSize: 14, color: "var(--vn-ink-muted)" }}>None yet. Approve, revise, or stop a post and it shows up here.</div>
        )}
        {(d.events as any[]).map((e) => (
          <div key={e.run_id} style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", padding: "10px 0", borderTop: "1px solid var(--vn-line)" }}>
            <div style={{ fontSize: 14.5, color: "var(--vn-ink)" }}>{said(e)}</div>
            <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-muted)" }}>{e.run_id}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
