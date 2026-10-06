"use client";

import React, { useCallback, useEffect, useState } from "react";
import { PageHeader } from "./PageHeader";
import { Sidebar } from "./Sidebar";
import { AutopilotPanel } from "./AutopilotPanel";
import { CommandPalette } from "./CommandPalette";
import { RunDetail } from "./views/RunDetail";
import { Runs } from "./views/Runs";
import { Research } from "./views/Research";
import { VannaReferences } from "./views/VannaReferences";
import { SchedulerView } from "./views/SchedulerView";
import { WhatVannaCanDo } from "./views/WhatVannaCanDo";
import { Campaigns } from "./views/Campaigns";
import { useMissionControl } from "@/lib/viewmodel";
import type { MissionControlProps } from "@/lib/types";
import { Assistant } from "./views/Assistant";

export function MissionControl({
  debateEdges = "both",
  capUsd = 10,
  arcPalette = ["var(--vn-accent)", "#2E6E8C", "var(--vn-rose)"],
}: MissionControlProps) {
  const vm = useMissionControl({ debateEdges, capUsd, arcPalette });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [autopilot, setAutopilot] = useState(false);
  const [palette, setPalette] = useState(false);
  const [newChat, setNewChat] = useState(0);
  const v = vm as any;

  const startChat = useCallback(() => {
    v.nav.find((n: any) => n.id === "assistant")?.go();
    setNewChat((n) => n + 1);
  }, [v]);
  const openAutopilot = useCallback(() => setAutopilot(true), []);

  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPalette((p) => !p);
      }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, []);

  return (
    <div style={{ display: "flex", alignItems: "stretch", minHeight: "100vh", background: "var(--vn-bg)", color: "var(--vn-ink)", fontSize: 14, lineHeight: "21px" }}>
      <Sidebar vm={vm} mobileOpen={mobileMenuOpen} onCloseMobile={() => setMobileMenuOpen(false)}
               onAutopilot={openAutopilot} onSearch={() => setPalette(true)} onNewChat={startChat} />

      {/* `app-shell-main` reserves the gutter the fixed sidebar occupies. */}
      <main className="app-shell-main" style={{ flex: "1 1 auto", minWidth: 0, display: "flex", flexDirection: "column" }}>
        <PageHeader vm={vm} onSearch={() => setPalette(true)} onMenu={() => setMobileMenuOpen(true)} />
        {!v.isAssistant && (
          <div className="hd-page-head">
            <h1>{vm.pageTitle}</h1>
            {vm.pageSub && vm.pageSub !== "Loading…" && <p>{vm.pageSub}</p>}
          </div>
        )}
        {v.isScheduler && <SchedulerView vm={vm} />}
        {vm.isRuns && <Runs vm={vm} />}
        {vm.isRun && <RunDetail vm={vm} />}
        {v.isResearch && <Research vm={vm} />}
        {v.isVannaPlays && <WhatVannaCanDo vm={vm} />}
        {v.isCampaigns && <Campaigns />}
        {v.isReferences && <VannaReferences focusId={v.referenceFocus || ""} />}
        {v.isAssistant && <Assistant vm={vm} newChat={newChat} onAutopilot={openAutopilot} />}
      </main>

      {autopilot && <AutopilotPanel onClose={() => setAutopilot(false)} goCampaigns={v.goCampaigns} />}
      {palette && <CommandPalette vm={vm} onClose={() => setPalette(false)} onAutopilot={openAutopilot} onNewChat={startChat} />}
    </div>
  );
}
