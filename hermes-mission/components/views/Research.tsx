"use client";

/**
 * Scraped Intelligence — A01's harvest, and nothing else.
 *
 * This view used to be 989 lines reporting a different subsystem: the
 * `research_runs` / `discovered_players` / `evidence.jsonl` registry, shown as
 * six tabs (Actionable Post Ideas, Discovered Ecosystem Players, Deep Scraped
 * Profiles, Canonical Claims Ledger, Discovery Axis Logs, Scraped Social
 * Posts). That registry is not what the 13 agents run — A01 scrapes live every
 * cycle and its harvest had no surface at all, while a section named "Scraped
 * Intelligence" showed a static snapshot from a system nothing schedules.
 *
 * The tabs are gone. What remains is what the scout actually pulled: every
 * signal with its publisher, the companies named in it, and both timestamps.
 */

import React from "react";
import type { MissionVM } from "@/lib/viewmodel";
import { LiveHarvest } from "./LiveHarvest";

export function Research({ vm }: { vm: MissionVM }) {
  return (
    <section className="vanna-section">
      <LiveHarvest />
    </section>
  );
}
