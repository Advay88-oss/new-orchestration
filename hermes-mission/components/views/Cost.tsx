"use client";

import React, { useState, useEffect } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

export function Cost({ vm }: { vm: MissionVM }) {
  const [spendData, setSpendData] = useState<any>({
    spent_usd: 0.0,
    cap_usd: 10.0,
    remaining_usd: 10.0,
    calls: 0,
    source: "LIVE_PROXY_8900"
  });

  // Real per-model spend, summed from the run journals. The breakdown below
  // used to multiply the real total by hardcoded shares (0.37/0.30/0.28/0.05);
  // those numbers were typed, not measured.
  const [real, setReal] = useState<any>(null);
  const [spendErr, setSpendErr] = useState<string | null>(null);

  useEffect(() => {
    const load = () => {
      fetch("/api/spend", { cache: "no-store" })
        .then((r) => r.json())
        .then((d) => { if (typeof d.spent_usd === "number") setSpendData(d); })
        .catch((e) => setSpendErr(String(e)));
      fetch("/api/v2/spend", { cache: "no-store" })
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
        .then((d) => { setReal(d); setSpendErr(null); })
        .catch((e) => setSpendErr(String(e)));
    };
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  // The journal is the source of truth, not the :8900 proxy. The proxy is
  // usually not running, so its ledger reported "$0.0000 ... (0 calls)" next
  // to a table showing 63 real calls — a zero that reads as "this cost
  // nothing" rather than "nothing measured this".
  const cap = real?.capUsd ?? spendData.cap_usd ?? 10.0;
  const calls = real?.calls ?? 0;
  const runs = real?.runs ?? 0;
  const inTok = real?.inputTokens ?? 0;
  const outTok = real?.outputTokens ?? 0;

  // Known only when every model that ran has a published rate. Partial
  // pricing is reported as partial, never rounded up into a total.
  const costKnown = typeof real?.costUsd === "number";
  const spent = costKnown ? (real.costUsd as number) : null;
  const complete = Boolean(real?.costComplete);
  const unpriced: string[] = real?.unpricedModels ?? [];
  const remaining = spent !== null && complete ? Math.max(0, cap - spent) : null;
  const pct = spent !== null && complete ? Math.min(100, Math.max(0, (spent / cap) * 100)) : null;
  const perRun = spent !== null && complete && runs > 0 ? spent / runs : null;
  const cycles = perRun && perRun > 0 && remaining !== null ? Math.floor(remaining / perRun) : null;

  const DASH = "—";
  const money = (v: number | null) => (v === null ? DASH : `$${v.toFixed(4)}`);

  // Measured, not apportioned: one row per model the journals actually recorded.
  const totalOut = (real?.byModel ?? []).reduce((a: number, m: any) => a + m.outputTokens, 0) || 1;
  const PALETTE = ["#A98CFF", "#FF007A", "#4ADE9B", "#A98CFF", "#F5A524", "#F0666B"];
  const MODALITY_BREAKDOWN = (real?.byModel ?? []).map((m: any, i: number) => ({
    name: m.model,
    cost: m.costKnown ? `$${m.costUsd.toFixed(4)}` : "unpriced",
    pct: `${((m.outputTokens / totalOut) * 100).toFixed(1)}%`,
    color: PALETTE[i % PALETTE.length],
    desc: `${m.calls} call${m.calls === 1 ? "" : "s"} · ${m.inputTokens.toLocaleString()} in / ${m.outputTokens.toLocaleString()} out · stages: ${m.roles.join(", ")}`,
  }));

  return (
    <section className="vanna-section">
      {/* Header Banner */}
      <div className="vanna-banner">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "999px", background: "#4ADE9B" }} />
            <span style={{ fontFamily: MONO, fontSize: "12px", fontWeight: 700, color: complete ? "#4ADE9B" : "#F5A524", letterSpacing: "0.08em" }}>
              SOURCE: RUN JOURNAL ({runs} RUN{runs === 1 ? "" : "S"})
              {complete ? " · PRICED" : ""}
            </span>
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#FFFFFF", marginTop: "6px" }}>
            Usage &amp; Cap
          </h2>
          <p style={{ fontSize: "14px", color: "#7B7590", marginTop: "4px" }}>
            What the 13 agents spent, counted from every cycle they ran.
          </p>
        </div>

        <div style={{ background: "rgba(255,255,255,0.05)", padding: "10px 20px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.1)" }}>
          <div style={{ fontFamily: MONO, fontSize: "11px", color: "#7B7590" }}>HARD CAP ENFORCEMENT</div>
          <div style={{ fontSize: "18px", fontWeight: 800, color: "#FFFFFF", marginTop: "2px" }}>${cap.toFixed(2)} USD CAP</div>
        </div>
      </div>

      {/* Hero Financial Metrics Strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "16px" }}>
        <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "16px", padding: "20px" }}>
          <div style={{ fontFamily: MONO, fontSize: "11px", color: "#7B7590", textTransform: "uppercase" }}>MODEL CALLS</div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: "#FFFFFF", marginTop: "4px" }}>{calls.toLocaleString()}</div>
          <div style={{ fontSize: "12px", color: "#7B7590", marginTop: "4px" }}>across {runs} run{runs === 1 ? "" : "s"}</div>
        </div>

        <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "16px", padding: "20px" }}>
          <div style={{ fontFamily: MONO, fontSize: "11px", color: "#7B7590", textTransform: "uppercase" }}>TOKENS</div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: "#A98CFF", marginTop: "4px" }}>{((inTok + outTok) / 1000).toFixed(1)}k</div>
          <div style={{ fontSize: "12px", color: "#7B7590", marginTop: "4px" }}>{inTok.toLocaleString()} in / {outTok.toLocaleString()} out</div>
        </div>

        <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "16px", padding: "20px" }}>
          <div style={{ fontFamily: MONO, fontSize: "11px", color: "#7B7590", textTransform: "uppercase" }}>MEASURED COST</div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: complete ? "#4ADE9B" : "#F5A524", marginTop: "4px" }}>
            {complete ? money(spent) : "unpriced"}
          </div>
          <div style={{ fontSize: "12px", color: "#7B7590", marginTop: "4px" }}>
            {complete
              ? `${pct!.toFixed(1)}% of the $${cap.toFixed(2)} cap`
              : unpriced.length
                ? `${unpriced.length} model${unpriced.length === 1 ? "" : "s"} without a rate`
                : "no calls yet"}
          </div>
        </div>

        <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "16px", padding: "20px" }}>
          <div style={{ fontFamily: MONO, fontSize: "11px", color: "#7B7590", textTransform: "uppercase" }}>COST PER RUN</div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: "#A98CFF", marginTop: "4px" }}>
            {perRun === null ? DASH : money(perRun)}
          </div>
          <div style={{ fontSize: "12px", color: "#7B7590", marginTop: "4px" }}>
            {cycles === null ? `over ${runs} run${runs === 1 ? "" : "s"}` : `~${cycles} cycles left under the cap`}
          </div>
        </div>
      </div>

      {/* The cap-consumption bar lived here. With no rate table it could only
          draw an empty track labelled NOT MEASURABLE above a paragraph
          explaining why — a large block of UI whose whole content was an
          apology. The cap itself is stated in the banner; when rates exist
          the MEASURED COST card carries the percentage. */}
      {spendErr && (
        <div style={{ background: "#0C0716", border: "1px solid rgba(252,84,87,0.3)", borderRadius: "16px", padding: "14px 20px", fontSize: "12px", color: "#F0666B", fontFamily: MONO }}>
          journal unreachable: {spendErr}
        </div>
      )}

      {/* Modality Breakdown */}
      <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "18px", padding: "24px 28px" }}>
        <h3 style={{ fontSize: "17px", fontWeight: 700, color: "#FFFFFF", marginBottom: "16px" }}>
          Per model
        </h3>
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {MODALITY_BREAKDOWN.map((m: any, idx: number) => (
            <div
              key={idx}
              style={{
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.05)",
                borderRadius: "12px",
                padding: "16px 20px",
                display: "grid",
                gridTemplateColumns: "minmax(240px, 1.5fr) 100px 100px minmax(280px, 2fr)",
                alignItems: "center",
                gap: "16px"
              }}
            >
              <div>
                <span style={{ fontSize: "14px", fontWeight: 700, color: "#FFFFFF" }}>{m.name}</span>
              </div>
              <div>
                <span style={{ fontFamily: MONO, fontSize: "14px", fontWeight: 700, color: m.color }}>{m.cost}</span>
              </div>
              <div>
                <span style={{ fontFamily: MONO, fontSize: "12px", color: "#7B7590" }}>{m.pct}</span>
              </div>
              <div>
                <span style={{ fontSize: "12px", color: "#7B7590", lineHeight: 1.4 }}>{m.desc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
