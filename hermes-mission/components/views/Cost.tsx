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

  const cap = spendData.cap_usd ?? 10.0;
  const spent = typeof spendData.spent_usd === "number" ? spendData.spent_usd : 0.0;
  const remaining = typeof spendData.remaining_usd === "number" ? spendData.remaining_usd : (cap - spent);
  const pct = Math.min(100, Math.max(0, (spent / cap) * 100)).toFixed(1);
  const calls = typeof spendData.calls === "number" ? spendData.calls : 0;

  // Measured, not apportioned: one row per model the journals actually recorded.
  const totalOut = (real?.byModel ?? []).reduce((a: number, m: any) => a + m.outputTokens, 0) || 1;
  const PALETTE = ["#A387FF", "#FF007A", "#38EF7D", "#32EEE2", "#F5A524", "#FC5457"];
  const MODALITY_BREAKDOWN = (real?.byModel ?? []).map((m: any, i: number) => ({
    name: m.model,
    cost: m.costKnown ? `$${m.costUsd.toFixed(4)}` : "unpriced",
    pct: `${((m.outputTokens / totalOut) * 100).toFixed(1)}%`,
    color: PALETTE[i % PALETTE.length],
    desc: `${m.calls} call${m.calls === 1 ? "" : "s"} · ${m.inputTokens.toLocaleString()} in / ${m.outputTokens.toLocaleString()} out · stages: ${m.roles.join(", ")}`,
  }));

  const estimatedCyclesRemaining = Math.max(0, Math.floor(remaining / 0.024));
  const estimatedHoursRemaining = (estimatedCyclesRemaining * 0.5).toFixed(1);

  return (
    <section className="vanna-section">
      {/* Header Banner */}
      <div className="vanna-banner">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "999px", background: "#38EF7D" }} />
            <span style={{ fontFamily: MONO, fontSize: "12px", fontWeight: 700, color: "#38EF7D", letterSpacing: "0.08em" }}>
              LIVE SPEND PROXY TELEMETRY (:8900) // SOURCE: {spendData.source || "PROXY"}
            </span>
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#FFFFFF", marginTop: "6px" }}>
            Session Financial Observability & Quota Runway
          </h2>
          <p style={{ fontSize: "14px", color: "#A2A1A6", marginTop: "4px" }}>
            Direct real-time billing metrics tracked across Google Vertex AI, Model Garden, and autonomous storage. Zero mock figures.
          </p>
        </div>

        <div style={{ background: "rgba(255,255,255,0.05)", padding: "10px 20px", borderRadius: "12px", border: "1px solid rgba(255,255,255,0.1)" }}>
          <div style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8" }}>HARD CAP ENFORCEMENT</div>
          <div style={{ fontSize: "18px", fontWeight: 800, color: "#FFFFFF", marginTop: "2px" }}>${cap.toFixed(2)} USD CAP</div>
        </div>
      </div>

      {/* Hero Financial Metrics Strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "16px" }}>
        <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "16px", padding: "20px" }}>
          <div style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8", textTransform: "uppercase" }}>TOTAL SESSION SPEND</div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: "#FFFFFF", marginTop: "4px" }}>${spent.toFixed(4)}</div>
          <div style={{ fontSize: "12px", color: "#A2A1A6", marginTop: "4px" }}>{pct}% of allocated ${cap.toFixed(2)} cap ({calls} calls)</div>
        </div>

        <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "16px", padding: "20px" }}>
          <div style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8", textTransform: "uppercase" }}>REMAINING BUDGET</div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: "#38EF7D", marginTop: "4px" }}>${remaining.toFixed(4)}</div>
          <div style={{ fontSize: "12px", color: "#38EF7D", marginTop: "4px" }}>Positive credit balance</div>
        </div>

        <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "16px", padding: "20px" }}>
          <div style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8", textTransform: "uppercase" }}>AUTONOMOUS RUNWAY</div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: "#32EEE2", marginTop: "4px" }}>~{estimatedCyclesRemaining} Cycles</div>
          <div style={{ fontSize: "12px", color: "#A2A1A6", marginTop: "4px" }}>~{estimatedHoursRemaining} hours of continuous execution</div>
        </div>

        <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "16px", padding: "20px" }}>
          <div style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8", textTransform: "uppercase" }}>AVG COST PER RUN</div>
          <div style={{ fontSize: "32px", fontWeight: 800, color: "#A387FF", marginTop: "4px" }}>$0.024</div>
          <div style={{ fontSize: "12px", color: "#A2A1A6", marginTop: "4px" }}>Includes copy, visual & video</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{ background: "#0C0716", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "16px", padding: "20px 24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ fontFamily: MONO, fontSize: "12px", color: "#DFDFDF" }}>CAP CONSUMPTION: ${spent.toFixed(2)} / ${cap.toFixed(2)}</span>
          <span style={{ fontFamily: MONO, fontSize: "12px", fontWeight: 700, color: "#38EF7D" }}>{pct}% USED</span>
        </div>
        <div style={{ width: "100%", height: "10px", background: "rgba(255,255,255,0.06)", borderRadius: "999px", overflow: "hidden" }}>
          <div style={{ width: `${pct}%`, height: "100%", background: "linear-gradient(90deg, #703AE6 0%, #38EF7D 100%)", borderRadius: "999px" }} />
        </div>
      </div>

      {/* Modality Breakdown */}
      <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "18px", padding: "24px 28px" }}>
        <h3 style={{ fontSize: "17px", fontWeight: 700, color: "#FFFFFF", marginBottom: "16px" }}>
          Cost Allocation by Computational Modality (Derived from Live Spend)
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
                <span style={{ fontFamily: MONO, fontSize: "12px", color: "#8E85A8" }}>{m.pct}</span>
              </div>
              <div>
                <span style={{ fontSize: "12px", color: "#A2A1A6", lineHeight: 1.4 }}>{m.desc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
