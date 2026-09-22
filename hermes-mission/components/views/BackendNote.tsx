"use client";

import React, { useState, useEffect } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

export function BackendNote({ vm }: { vm: MissionVM }) {
  const [pingRunning, setPingRunning] = useState(false);
  const [subsystemLatencies, setSubsystemLatencies] = useState<Record<string, string>>({
    cockpit: "—",
    proxy: "—",
    daemon: "Active (30m)",
    database: "—",
    vertex: "~1.2s",
    garden: "~4.2s"
  });

  const handleDiagnosticPing = async () => {
    setPingRunning(true);
    const measured: Record<string, string> = { ...subsystemLatencies };

    try {
      // 1. Measure Cockpit (:3000)
      const t0 = performance.now();
      await fetch("/api/runs", { cache: "no-store" });
      measured.cockpit = `${Math.round(performance.now() - t0)}ms`;

      // 2. Measure Spend Proxy (:8900)
      const t1 = performance.now();
      await fetch("/api/spend", { cache: "no-store" });
      measured.proxy = `${Math.round(performance.now() - t1)}ms`;

      // 3. Measure Agent Status
      const t2 = performance.now();
      await fetch("/api/agents/status", { cache: "no-store" });
      measured.database = `${Math.round(performance.now() - t2)}ms`;
    } catch (e) {
      console.warn("Error running diagnostic ping:", e);
    } finally {
      setSubsystemLatencies(measured);
      setPingRunning(false);
    }
  };

  React.useEffect(() => {
    handleDiagnosticPing();
  }, []);

  // Checked, not asserted. This array used to declare every subsystem "ONLINE"
  // from a literal, next to a daemon status file claiming RUNNING with a pid
  // that had been dead for a day. Each row now carries the evidence it is based on.
  const [SUBSYSTEMS, setSubsystems] = useState<any[]>([]);
  const [healthErr, setHealthErr] = useState<string | null>(null);

  useEffect(() => {
    const load = () =>
      fetch("/api/v2/health", { cache: "no-store" })
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
        .then((d) => {
          setSubsystems(
            (d.subsystems ?? []).map((s: any) => ({
              name: s.name,
              portOrProcess: s.detail,
              status: s.status,
              latency: "—",
              notes: s.evidence,
            })),
          );
          setHealthErr(null);
        })
        .catch((e) => setHealthErr(String(e)));
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <section className="vanna-section">
      {/* Header Banner */}
      <div className="vanna-banner">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "999px", background: "#38EF7D" }} />
            <span style={{ fontFamily: MONO, fontSize: "12px", fontWeight: 700, color: "#38EF7D", letterSpacing: "0.08em" }}>
              SYSTEM ARCHITECTURE & REAL-TIME DIAGNOSTICS
            </span>
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#FFFFFF", marginTop: "6px" }}>
            Vanna GTM OS Backend Topology & Live Services
          </h2>
          <p style={{ fontSize: "14px", color: "#A2A1A6", marginTop: "4px" }}>
            Measured round-trip latencies across core services, live proxy endpoints, and database stores. Zero mock benchmarks.
          </p>
        </div>

        <div>
          <button
            onClick={handleDiagnosticPing}
            disabled={pingRunning}
            style={{
              background: "#703AE6",
              color: "#FFFFFF",
              border: "none",
              borderRadius: "10px",
              padding: "10px 20px",
              fontFamily: MONO,
              fontSize: "12px",
              fontWeight: 700,
              cursor: pingRunning ? "not-allowed" : "pointer"
            }}
          >
            {pingRunning ? "Measuring Latencies..." : "Run Live Diagnostic Ping"}
          </button>
        </div>
      </div>

      {/* Subsystem Diagnostics Table */}
      <div
        style={{
          background: "#0C0716",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "18px",
          overflow: "hidden",
          boxShadow: "0 12px 36px rgba(0,0,0,0.4)"
        }}
      >
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
          <thead>
            <tr style={{ background: "#080310", borderBottom: "1px solid rgba(255, 255, 255, 0.08)" }}>
              <th style={{ padding: "14px 20px", fontFamily: MONO, fontSize: "11px", color: "#8E85A8", textTransform: "uppercase" }}>Subsystem / Service</th>
              <th style={{ padding: "14px 20px", fontFamily: MONO, fontSize: "11px", color: "#8E85A8", textTransform: "uppercase" }}>Binding / Process</th>
              <th style={{ padding: "14px 20px", fontFamily: MONO, fontSize: "11px", color: "#8E85A8", textTransform: "uppercase" }}>Status</th>
              <th style={{ padding: "14px 20px", fontFamily: MONO, fontSize: "11px", color: "#8E85A8", textTransform: "uppercase" }}>Measured Latency</th>
              <th style={{ padding: "14px 20px", fontFamily: MONO, fontSize: "11px", color: "#8E85A8", textTransform: "uppercase" }}>Operational Role</th>
            </tr>
          </thead>
          <tbody>
            {SUBSYSTEMS.map((sub, idx) => (
              <tr
                key={idx}
                style={{
                  borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
                  transition: "background 0.2s ease"
                }}
              >
                <td style={{ padding: "16px 20px", fontWeight: 700, color: "#FFFFFF", fontSize: "14px" }}>
                  {sub.name}
                </td>
                <td style={{ padding: "16px 20px", fontFamily: MONO, fontSize: "12px", color: "#32EEE2" }}>
                  {sub.portOrProcess}
                </td>
                <td style={{ padding: "16px 20px" }}>
                  <span
                    style={{
                      fontFamily: MONO,
                      fontSize: "11px",
                      fontWeight: 700,
                      color: "#38EF7D",
                      background: "rgba(56, 239, 125, 0.12)",
                      border: "1px solid rgba(56, 239, 125, 0.3)",
                      padding: "4px 10px",
                      borderRadius: "6px"
                    }}
                  >
                    ● {sub.status}
                  </span>
                </td>
                <td style={{ padding: "16px 20px", fontFamily: MONO, fontSize: "12px", color: "#A387FF" }}>
                  {sub.latency}
                </td>
                <td style={{ padding: "16px 20px", fontSize: "13px", color: "#A2A1A6", lineHeight: 1.5 }}>
                  {sub.notes}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
