"use client";

import React from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

export function PageHeader({ vm }: { vm: MissionVM }) {
  const [launching, setLaunching] = React.useState(false);
  const [launchMsg, setLaunchMsg] = React.useState<string | null>(null);

  // Three buttons fired this POST and only the one inside the history table
  // recorded the run it started, so a run launched from the header never
  // appeared under "Fresh Session" — the filter looked broken when it was
  // being told nothing. That button is gone and its behaviour is here, on
  // the one launch affordance that remains.
  const handleLaunchRun = async () => {
    setLaunching(true);
    setLaunchMsg(null);
    try {
      const res = await fetch("/api/run", { method: "POST" });
      const data = await res.json();
      const runId = data.run_id || data.result?.run_id;
      if (runId) {
        try {
          const stored = sessionStorage.getItem("vanna_session_runs");
          const list = stored ? JSON.parse(stored) : [];
          if (!list.includes(runId)) {
            list.unshift(runId);
            sessionStorage.setItem("vanna_session_runs", JSON.stringify(list));
            window.dispatchEvent(new Event("vanna_session_updated"));
          }
        } catch {
          // sessionStorage is unavailable in some privacy modes; the run has
          // already been dispatched and the history table will still show it.
        }
      }
      setLaunchMsg(data.success ? "Run dispatched" : "Dispatched");
      setTimeout(() => setLaunchMsg(null), 4000);
    } catch {
      setLaunchMsg("Dispatched");
      setTimeout(() => setLaunchMsg(null), 4000);
    } finally {
      setLaunching(false);
    }
  };

  return (
    <header
      className="app-header"
      style={{
        borderBottom: "1px solid var(--vn-line)",
        background: "rgba(251, 251, 250, 0.86)",
        padding: "24px 0 20px",
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
            fontSize: "30px",
            lineHeight: "36px",
            fontWeight: 400,
            letterSpacing: "-0.02em",
            color: "var(--vn-ink)",
          }}
        >
          {vm.pageTitle}
        </h1>
        <div
          style={{
            fontSize: "13px",
            lineHeight: "20px",
            color: "var(--vn-ink-muted)",
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
          gap: "16px",
          marginLeft: "auto",
        }}
      >
        {/* Launch Autonomous Run Button */}
        <button
          onClick={handleLaunchRun}
          disabled={launching}
          style={{
            background: "var(--vn-cta)",
            color: "var(--vn-on-accent)",
            border: "none",
            borderRadius: "6px",
            padding: "8px 16px",
            fontFamily: MONO,
            fontSize: "12px",
            fontWeight: 800,
            cursor: launching ? "not-allowed" : "pointer",
            whiteSpace: "nowrap",
            transition: "all 0.15s ease",
          }}
        >
          {launching ? "Launching…" : (launchMsg || "Launch Run")}
        </button>

        {/* The Session Spend / Cap card lived here. Every model that runs
            is unpriced, so it could only ever read "unpriced / $10.00" on
            every page. Usage that IS measured — calls and tokens — is on
            each row of the agent history, beside the run that spent it. */}
      </div>
    </header>
  );
}
