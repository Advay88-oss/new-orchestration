"use client";

import { PageHeader } from "./PageHeader";
import { Sidebar } from "./Sidebar";
import { Agents } from "./views/Agents";
import { BackendNote } from "./views/BackendNote";
import { Cost } from "./views/Cost";
import { Lifecycles } from "./views/Lifecycles";
import { LiveDebate } from "./views/LiveDebate";
import { Posts } from "./views/Posts";
import { RunDetail } from "./views/RunDetail";
import { Runs } from "./views/Runs";
import { useMissionControl } from "@/lib/viewmodel";
import type { MissionControlProps } from "@/lib/types";

/**
 * The three tweakable props keep the original's names and defaults:
 *   debateEdges  "rail" | "matrix" | "both"   default "both"
 *   capUsd       number                        default 10
 *   arcPalette   [hex, hex, hex]               default ["#703AE6","#24A0A9","#FF007A"]
 */
export function MissionControl({
  debateEdges = "both",
  capUsd = 10,
  arcPalette = ["#703AE6", "#24A0A9", "#FF007A"],
}: MissionControlProps) {
  const vm = useMissionControl({ debateEdges, capUsd, arcPalette });

  return (
    <div
      style={{
        display: "flex",
        alignItems: "stretch",
        minHeight: "100vh",
        background: "#F7F7F7",
        fontSize: "14px",
        lineHeight: "21px",
      }}
    >
      <Sidebar vm={vm} />

      <main
        style={{
          flex: "1 1 auto",
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <PageHeader vm={vm} />

        {vm.isLive && <LiveDebate vm={vm} />}
        {vm.isPipeline && <Lifecycles vm={vm} />}
        {vm.isPosts && <Posts vm={vm} />}
        {vm.isRuns && <Runs vm={vm} />}
        {vm.isRun && <RunDetail vm={vm} />}
        {vm.isAgents && <Agents vm={vm} />}
        {vm.isCost && <Cost vm={vm} />}
        {vm.isNotes && <BackendNote vm={vm} />}
      </main>
    </div>
  );
}
