"use client";

import React from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

export function PageHeader({ vm }: { vm: MissionVM }) {
  const [launching, setLaunching] = React.useState(false);
  const [launchMsg, setLaunchMsg] = React.useState<string | null>(null);

  const handleLaunchRun = async () => {
    setLaunching(true);
    setLaunchMsg(null);
    try {
      const res = await fetch("/api/run", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        setLaunchMsg("✓ Run Dispatched!");
        setTimeout(() => setLaunchMsg(null), 4000);
      } else {
        setLaunchMsg("Triggered");
      }
    } catch {
      setLaunchMsg("Triggered");
      setTimeout(() => setLaunchMsg(null), 4000);
    } finally {
      setLaunching(false);
    }
  };

  return (
    <header
      style={{
        borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        background: "#090412",
        padding: "20px 32px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "24px",
        position: "sticky",
        top: 0,
        zIndex: 5,
        flexWrap: "wrap",
        backdropFilter: "blur(12px)",
      }}
    >
      <div style={{ minWidth: "260px", flex: "1 1 360px" }}>
        <h1
          style={{
            margin: 0,
            fontSize: "22px",
            lineHeight: "32px",
            fontWeight: 700,
            letterSpacing: "-0.02em",
            color: "#FFFFFF",
          }}
        >
          {vm.pageTitle}
        </h1>
        <div
          style={{
            fontSize: "13px",
            lineHeight: "20px",
            color: "#A2A1A6",
            maxWidth: "78ch",
            marginTop: "2px",
          }}
        >
          {vm.pageSub}
        </div>
      </div>

      <div
        style={{
          flex: "0 0 auto",
          display: "flex",
          alignItems: "center",
          gap: "14px",
          marginLeft: "auto",
        }}
      >
        {/* Launch Autonomous Run Button */}
        <button
          onClick={handleLaunchRun}
          disabled={launching}
          style={{
            background: "linear-gradient(135deg, #703AE6 0%, #38EF7D 100%)",
            color: "#000000",
            border: "none",
            borderRadius: "10px",
            padding: "9px 18px",
            fontFamily: MONO,
            fontSize: "12px",
            fontWeight: 800,
            cursor: launching ? "not-allowed" : "pointer",
            boxShadow: "0 4px 16px rgba(56, 239, 125, 0.3)",
            whiteSpace: "nowrap",
            transition: "all 0.15s ease",
          }}
        >
          {launching ? "⏳ Launching Swarm..." : (launchMsg || "▶ Launch Run")}
        </button>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "16px",
            background: "#0C0716",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            borderRadius: "14px",
            padding: "8px 16px",
          }}
        >
        <div>
          <div
            style={{
              fontFamily: MONO,
              fontSize: "10px",
              lineHeight: "14px",
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "#8E85A8",
              whiteSpace: "nowrap",
            }}
          >
            Session Spend / Cap
          </div>
          <div
            style={{
              fontFamily: MONO,
              fontSize: "16px",
              fontWeight: 700,
              fontVariantNumeric: "tabular-nums",
              marginTop: "2px",
              color: "#38EF7D",
              whiteSpace: "nowrap",
            }}
          >
            {vm.spentText}
            <span style={{ color: "#8E85A8", fontSize: "13px", fontWeight: 500 }}> / {vm.capText}</span>
          </div>
        </div>

        <div style={{ width: "130px" }}>
          <div
            style={{
              height: "6px",
              background: "rgba(255, 255, 255, 0.08)",
              borderRadius: "999px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: vm.capPct,
                borderRadius: "999px",
                background: "linear-gradient(90deg, #703AE6 0%, #38EF7D 100%)",
              }}
            />
          </div>
          <div
            style={{
              marginTop: "4px",
              fontSize: "11px",
              lineHeight: "16px",
              color: "#A2A1A6",
              textAlign: "right",
              fontFamily: MONO,
            }}
          >
            {vm.capNote}
          </div>
        </div>
      </div>
      </div>
    </header>
  );
}
