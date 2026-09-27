"use client";

/**
 * Today's spend against the caps, and what the watch has raised
 * (pipeline/ops). Paid calls stop at a cap until 00:00 UTC; alerts go to the
 * owner's Telegram once per window.
 */
import React, { useCallback, useEffect, useState } from "react";
import { MONO } from "@/lib/colors";

export function OpsCard() {
  const [d, setD] = useState<any>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const load = useCallback(async () => {
    try { setD(await (await fetch("/api/ops", { cache: "no-store" })).json()); } catch { /* shown as empty */ }
  }, []);
  useEffect(() => { load(); const t = setInterval(load, 30_000); return () => clearInterval(t); }, [load]);
  const test = async () => {
    setMsg("sending…");
    const r = await (await fetch("/api/ops", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ test: true }) })).json();
    setMsg(r.sent ? "Test alert sent to Telegram." : "Not sent (Telegram not configured, or one was sent in the last hours).");
    load();
  };
  if (!d?.ok) return null;
  const b = d.budget;
  const pct = b.daily_usd ? Math.min(100, (b.spent_usd / b.daily_usd) * 100) : 0;
  const tone = pct >= 100 ? "var(--vn-bad)" : pct >= 80 ? "var(--vn-warn)" : "var(--vn-ok)";
  return (
    <div className="vanna-card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
        <div>
          <h3 style={{ margin: 0 }}>Budget &amp; alerts</h3>
          <div style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", marginTop: 2 }}>
            Paid calls stop at a cap until 00:00 UTC. Alerts reach your Telegram once per hour at most, per problem.
          </div>
        </div>
        <button onClick={test} style={{ border: "1px solid var(--vn-line-strong)", background: "transparent", color: "var(--vn-ink)", borderRadius: 6, padding: "6px 12px", fontSize: 12.5, cursor: "pointer" }}>
          Send test alert
        </button>
      </div>
      {msg && <div style={{ fontSize: 12, color: "var(--vn-ink-muted)", marginTop: 6 }}>{msg}</div>}

      <div style={{ marginTop: 14 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
          <span>Today ({b.day})</span>
          <span style={{ fontFamily: MONO }}>${b.spent_usd.toFixed(2)} / ${Number(b.daily_usd).toFixed(2)}</span>
        </div>
        <div style={{ height: 6, background: "var(--vn-raised)", borderRadius: 3, marginTop: 6, overflow: "hidden" }}>
          <div style={{ width: pct + "%", height: "100%", background: tone, transition: "width .3s" }} />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 10, marginTop: 12 }}>
          {Object.entries(b.services || {}).map(([k, v]: [string, any]) => (
            <div key={k} style={{ border: "1px solid var(--vn-line)", borderRadius: 8, padding: "8px 10px" }}>
              <div style={{ fontSize: 12, color: "var(--vn-ink-muted)" }}>{k}</div>
              <div style={{ fontFamily: MONO, fontSize: 13 }}>${Number(v.usd || 0).toFixed(3)}{v.cap != null ? " / $" + v.cap : ""}</div>
              <div style={{ fontSize: 11, color: "var(--vn-ink-faint)" }}>{v.calls || 0} calls</div>
            </div>
          ))}
        </div>
        {b.limits && (
          <div style={{ fontSize: 11.5, color: "var(--vn-ink-faint)", marginTop: 8 }}>
            Limits: assistant {b.limits.assistant_per_minute}/min and {b.limits.assistant_per_day}/day · cycles {b.limits.cycles_per_day}/day · launches 6/hour
          </div>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16, marginTop: 16 }}>
        <div>
          <div style={{ fontSize: 12.5, fontWeight: 600, marginBottom: 6 }}>Recent alerts</div>
          {(d.alerts || []).length === 0 && <div style={{ fontSize: 12.5, color: "var(--vn-ink-faint)" }}>None.</div>}
          {(d.alerts || []).slice(0, 6).map((a: any) => (
            <div key={a.key} style={{ fontSize: 12.5, padding: "5px 0", borderTop: "1px solid var(--vn-line)" }}>
              <span style={{ fontFamily: MONO, fontSize: 10.5, color: a.severity === "critical" ? "var(--vn-bad)" : a.severity === "warn" ? "var(--vn-warn)" : "var(--vn-ink-muted)" }}>
                {String(a.severity).toUpperCase()}
              </span>{" "}
              {String(a.text).slice(0, 160)}
              <span style={{ color: "var(--vn-ink-faint)" }}> · ×{a.count} · {new Date(a.last_at).toLocaleString()}</span>
            </div>
          ))}
        </div>
        <div>
          <div style={{ fontSize: 12.5, fontWeight: 600, marginBottom: 6 }}>Recent errors</div>
          {(d.errors || []).length === 0 && <div style={{ fontSize: 12.5, color: "var(--vn-ink-faint)" }}>None.</div>}
          {(d.errors || []).slice(0, 6).map((e: any) => (
            <div key={e.fingerprint} style={{ fontSize: 12.5, padding: "5px 0", borderTop: "1px solid var(--vn-line)" }}>
              <b>{e.where_}</b> ×{e.count}: <span style={{ color: "var(--vn-ink-muted)" }}>{String(e.message).slice(0, 140)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
