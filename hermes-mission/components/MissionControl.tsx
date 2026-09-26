"use client";

import React, { useState } from "react";
import { PageHeader } from "./PageHeader";
import { Sidebar } from "./Sidebar";
import { CommandConsole } from "./CommandConsole";
import { GtmAgents } from "./views/GtmAgents";
import { AgentReasoning } from "./views/AgentReasoning";
import { LiveTrace } from "./views/LiveTrace";
import { RunDetail } from "./views/RunDetail";
import { Runs } from "./views/Runs";
import { Research } from "./views/Research";
import { VannaReferences } from "./views/VannaReferences";
import { BrandBrain } from "./views/BrandBrain";
import { Learning } from "./views/Learning";
import { SchedulerView } from "./views/SchedulerView";
import { IdeasView } from "./views/IdeasView";
import { MemesView } from "./views/MemesView";
import { useMissionControl } from "@/lib/viewmodel";
import type { MissionControlProps } from "@/lib/types";

export function MissionControl({
  debateEdges = "both",
  capUsd = 10,
  arcPalette = ["var(--vn-accent)", "#24A0A9", "var(--vn-rose)"],
}: MissionControlProps) {
  const vm = useMissionControl({ debateEdges, capUsd, arcPalette });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "stretch",
        minHeight: "100vh",
        background: "var(--vn-sunken)",
        color: "var(--vn-ink)",
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
            background: "var(--vn-surface)",
            borderBottom: "1px solid var(--vn-line)",
            position: "sticky",
            top: 0,
            zIndex: 40,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "26px",
                height: "26px",
                borderRadius: "6px",
                background: "var(--vn-ink)",
                color: "var(--vn-on-accent)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: "var(--font-display)",
                fontSize: "17px",
                lineHeight: 1,
              }}
            >
              V
            </div>
            <span style={{ fontSize: "15px", fontWeight: 600, color: "var(--vn-ink)" }}>
              Vanna Mission Control
            </span>
          </div>

          <button
            onClick={() => setMobileMenuOpen(true)}
            style={{
              background: "var(--vn-raised)",
              border: "1px solid var(--vn-line-strong)",
              color: "var(--vn-ink)",
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "13px",
              fontWeight: 500,
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
        {vm.isRuns && <Runs vm={vm} />}
        {vm.isRun && <RunDetail vm={vm} />}
        {vm.isAgents && <GtmAgents />}
        {(vm as any).isResearch && <Research vm={vm} />}
        {(vm as any).isReferences && <VannaReferences />}
        {(vm as any).isBrain && <BrandBrain />}
        {(vm as any).isLearning && <Learning />}
      </main>
    </div>
  );
}
