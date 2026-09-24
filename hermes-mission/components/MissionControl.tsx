"use client";

import React, { useState } from "react";
import { PageHeader } from "./PageHeader";
import { Sidebar } from "./Sidebar";
import { CommandConsole } from "./CommandConsole";
import { GtmAgents } from "./views/GtmAgents";
import { AgentReasoning } from "./views/AgentReasoning";
import { LiveTrace } from "./views/LiveTrace";
import { Posts } from "./views/Posts";
import { Problems } from "./views/Problems";
import { RunDetail } from "./views/RunDetail";
import { Runs } from "./views/Runs";
import { Research } from "./views/Research";
import { VannaReferences } from "./views/VannaReferences";
import { SchedulerView } from "./views/SchedulerView";
import { IdeasView } from "./views/IdeasView";
import { MemesView } from "./views/MemesView";
import { useMissionControl } from "@/lib/viewmodel";
import type { MissionControlProps } from "@/lib/types";

export function MissionControl({
  debateEdges = "both",
  capUsd = 10,
  arcPalette = ["#703AE6", "#24A0A9", "#FF007A"],
}: MissionControlProps) {
  const vm = useMissionControl({ debateEdges, capUsd, arcPalette });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "stretch",
        minHeight: "100vh",
        background: "#07020D",
        color: "#F3F1F8",
        fontSize: "14px",
        lineHeight: "21px",
      }}
    >
      {/* Sidebar with responsive mobile drawer support */}
      <Sidebar
        vm={vm}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* `app-shell-main` reserves the gutter the fixed sidebar occupies. */}
      <main
        className="app-shell-main"
        style={{
          flex: "1 1 auto",
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Mobile Top Navigation Bar (<= 768px only) */}
        <div
          className="mobile-only"
          style={{
            display: "none",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "12px 16px",
            background: "#0C0716",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            position: "sticky",
            top: 0,
            zIndex: 40,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "24px",
                height: "24px",
                borderRadius: "8px",
                background: "#703AE6",
              }}
            />
            <span style={{ fontSize: "15px", fontWeight: 700, color: "#FFFFFF" }}>
              Vanna Mission Control
            </span>
          </div>

          <button
            onClick={() => setMobileMenuOpen(true)}
            style={{
              background: "#130B22",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              color: "#A98CFF",
              padding: "6px 14px",
              borderRadius: "8px",
              fontSize: "13px",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            ☰ Menu
          </button>
        </div>

        <PageHeader vm={vm} />
        <CommandConsole vm={vm} />

        {(vm as any).isTrace && <LiveTrace />}
        {vm.isLive && <AgentReasoning />}
        {(vm as any).isScheduler && <SchedulerView vm={vm} />}
        {(vm as any).isIdeas && <IdeasView vm={vm} />}
        {(vm as any).isMemes && <MemesView vm={vm} />}
        {vm.isPosts && <Posts vm={vm} />}
        {vm.isRuns && <Runs vm={vm} />}
        {vm.isProblems && <Problems vm={vm} />}
        {vm.isRun && <RunDetail vm={vm} />}
        {vm.isAgents && <GtmAgents />}
        {(vm as any).isResearch && <Research vm={vm} />}
        {(vm as any).isReferences && <VannaReferences />}
      </main>
    </div>
  );
}
