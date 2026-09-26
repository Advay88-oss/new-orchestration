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

const card: React.CSSProperties = {
  background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: 18,
};
const label: React.CSSProperties = {
  fontFamily: MONO, fontSize: 10.5, letterSpacing: 0.8, textTransform: "uppercase",
  color: "var(--vn-ink-muted)", marginBottom: 10,
};
const DIM_LABEL: Record<string, string> = { pillar: "Narrative pillar", hook_type: "Hook type", length: "Post length" };

function Bar({ v }: { v: number }) {
  return (
    <div style={{ width: 120, height: 6, borderRadius: 3, background: "var(--vn-sunken)", overflow: "hidden" }}>
      <div style={{ width: Math.round(v * 100) + "%", height: "100%", background: "var(--vn-accent-light)" }} />
    </div>
  );
}

export function Learning() {
  const [d, setD] = useState<any | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [metrics, setMetrics] = useState<Record<string, string>>({});
  const [runId, setRunId] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    fetch("/api/gtm/learning", { cache: "no-store" })
      .then((r) => r.json())
      .then((j) => (j.ok ? setD(j) : setErr(j.error || "unavailable")))
      .catch((e) => setErr(String(e)));
  }, []);
  useEffect(() => { load(); }, [load]);

  const post = async (body: any) => {
    setBusy(true);
    setMsg(null);
    try {
      const j = await (await fetch("/api/gtm/learning", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      })).json();
      if (!j.ok) setMsg(j.error || "failed");
      else {
        if (body.action === "outcome") setMsg(j.event ? "Recorded. Reward now " + j.event.total : "Recorded (no reward yet: needs a baseline of 3 posts).");
        load();
      }
    } finally {
      setBusy(false);
    }
  };

  if (err) return <div className="vanna-section"><div style={{ ...card, borderColor: "var(--vn-bad)" }}>Learning unavailable: {err}</div></div>;
  if (!d) return <div className="vanna-section" style={{ fontFamily: MONO, color: "var(--vn-ink-muted)" }}>Loading the learning loop…</div>;

  const input: React.CSSProperties = { background: "var(--vn-sunken)", border: "1px solid var(--vn-line)",
    borderRadius: 8, padding: "7px 10px", color: "var(--vn-ink)", fontSize: 13, width: 110 };

  return (
    <div className="vanna-section" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={card}>
        <div style={{ fontSize: 13, color: "var(--vn-ink-body)", lineHeight: 1.6 }}>
          Every run earns one reward: <b>0 if the reviewer blocked it</b> (the hard gate), otherwise the founder's
          decision (approve 1, edit 0.8, revise 0.3, kill 0) weighted 0.6 and engagement against the brand's own
          baseline weighted 0.4. The strategist's bandit reads these records by context and explores{" "}
          {Math.round((d.explore || 0) * 100)}% of the time. {d.n_events} reward events so far.
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: 16 }}>
        {Object.entries(d.arms as Record<string, any[]>).map(([dim, rows]) => (
          <div key={dim} style={card}>
            <div style={label}>{DIM_LABEL[dim] ?? dim}</div>
            {rows.map((r) => {
              const locked = d.locks?.[dim] === r.option;
              return (
                <div key={r.option} style={{ display: "flex", alignItems: "center", gap: 10, padding: "7px 0",
                                             borderTop: "1px solid var(--vn-line)" }}>
                  <div style={{ flex: 1, fontSize: 12.5, color: "var(--vn-ink)" }}>{r.option}</div>
                  <Bar v={r.mean} />
                  <div style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-ink-muted)", width: 78, textAlign: "right" }}>
                    {r.mean.toFixed(2)} · {r.n}
                  </div>
                  <button disabled={busy}
                          onClick={() => post(locked ? { action: "unlock", dim } : { action: "lock", dim, option: r.option })}
                          style={{ fontFamily: MONO, fontSize: 10.5, padding: "3px 8px", borderRadius: 5, cursor: "pointer",
                                   border: "1px solid " + (locked ? "var(--vn-warn)" : "var(--vn-line)"),
                                   color: locked ? "var(--vn-warn)" : "var(--vn-ink-muted)", background: "transparent" }}>
                    {locked ? "locked" : "lock"}
                  </button>
                </div>
              );
            })}
            <div style={{ fontSize: 11, color: "var(--vn-ink-faint)", marginTop: 8 }}>mean reward · runs. A lock makes the bandit use that option every run.</div>
          </div>
        ))}
      </div>

      <div style={card}>
        <div style={label}>Log a published post's engagement</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <input value={runId} onChange={(e) => setRunId(e.target.value)} placeholder="GTM-20260925-154856"
                 style={{ ...input, width: 200, fontFamily: MONO }} />
          {["impressions", "likes", "reposts", "replies", "clicks"].map((k) => (
            <input key={k} value={metrics[k] ?? ""} onChange={(e) => setMetrics({ ...metrics, [k]: e.target.value })}
                   placeholder={k} inputMode="numeric" style={input} />
          ))}
          <button disabled={busy || !/^GTM-\d{8}-\d{6}$/.test(runId)}
                  onClick={() => post({ action: "outcome", runId, metrics })}
                  style={{ background: "var(--vn-accent)", color: "#fff", border: "none", borderRadius: 8, padding: "8px 14px", fontWeight: 600, cursor: "pointer" }}>
            Record
          </button>
        </div>
        {msg && <div style={{ fontSize: 12.5, color: "var(--vn-ink-body)", marginTop: 8 }}>{msg}</div>}
      </div>

      <div style={card}>
        <div style={label}>Reward trend — latest runs</div>
        <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ color: "var(--vn-ink-muted)", textAlign: "left" }}>
              <th style={{ padding: "4px 0", fontWeight: 500 }}>run</th><th>reward</th><th>reviewer</th>
              <th>founder</th><th>engagement</th><th>arms</th>
            </tr>
          </thead>
          <tbody>
            {(d.events as any[]).map((e) => (
              <tr key={e.run_id} style={{ borderTop: "1px solid var(--vn-line)" }}>
                <td style={{ fontFamily: MONO, padding: "6px 0", color: "var(--vn-ink-body)" }}>{e.run_id}</td>
                <td style={{ fontFamily: MONO, color: e.total >= 0.6 ? "var(--vn-ok)" : e.total > 0 ? "var(--vn-warn)" : "var(--vn-bad)" }}>{Number(e.total).toFixed(2)}</td>
                <td style={{ color: e.reviewer_ok === 0 ? "var(--vn-bad)" : "var(--vn-ink-muted)" }}>{e.reviewer_ok === 0 ? "blocked" : e.reviewer_ok === 1 ? "passed" : "—"}</td>
                <td style={{ fontFamily: MONO, color: "var(--vn-ink-muted)" }}>{e.human ?? "—"}</td>
                <td style={{ fontFamily: MONO, color: "var(--vn-ink-muted)" }}>{e.engagement ?? "—"}</td>
                <td style={{ color: "var(--vn-ink-muted)" }}>{[e.arms.hook_type, e.arms.length].filter(Boolean).join(" · ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={card}>
        <div style={label}>Preference pairs (draft vs your edit) · {d.n_pairs}</div>
        {d.n_pairs === 0 ? (
          <div style={{ fontSize: 13, color: "var(--vn-ink-muted)" }}>
            None yet. Use "Edit & approve" on a run: your version is recorded as the approved one and the pair is kept
            as a training example for a later tuning step.
          </div>
        ) : (d.pairs as any[]).map((p) => (
          <div key={p.id} style={{ borderTop: "1px solid var(--vn-line)", padding: "8px 0", fontSize: 12.5 }}>
            <div style={{ fontFamily: MONO, color: "var(--vn-ink-muted)" }}>{p.run_id} · {String(p.at).slice(0, 10)}</div>
            <div style={{ color: "var(--vn-ink-faint)", textDecoration: "line-through", marginTop: 4 }}>{String(p.rejected).slice(0, 220)}</div>
            <div style={{ color: "var(--vn-ink-body)", marginTop: 4 }}>{String(p.chosen).slice(0, 220)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
