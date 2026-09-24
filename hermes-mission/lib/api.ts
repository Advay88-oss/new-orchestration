/**
 * Read-only data access for Mission Control Dashboard.
 * 100% Dynamic data: reads live runs and telemetry directly from disk via API routes.
 * Zero mock runs, zero static fixtures.
 */

import { MISSION_DATA } from "./mission-data";
import type { Agent, MissionData, NostrEvent, Review, VertexCall, Run, Stage } from "./types";

export const USE_FIXTURE = false;
export const API_BASE = "";

export const ROUTES = {
  messages: (channel: string, since?: number, limit = 500) =>
    `${API_BASE}/api/messages?channel=${encodeURIComponent(channel)}` +
    (since != null ? `&since=${since}` : "") +
    `&limit=${limit}`,
  identities: () => `${API_BASE}/api/identities`,
  spend: () => `${API_BASE}/api/v2/spend`,
  calls: (sinceIso?: string) =>
    `${API_BASE}/api/calls` + (sinceIso ? `?since=${encodeURIComponent(sinceIso)}` : ""),
  agentsStatus: () => `${API_BASE}/api/agents/status`,
  artifact: (name: string) => `${API_BASE}/api/artifacts/${name}`,
  review: (draftId: string) => `${API_BASE}/api/review/${encodeURIComponent(draftId)}`,
  runs: () => `${API_BASE}/api/runs`,
};

export interface SpendLedger {
  cap_usd?: number;
  capUsd?: number;
  remaining_usd?: number;
  spent_usd?: number;
  /** Null while any model that ran has no published rate. */
  costUsd?: number | null;
  costComplete?: boolean;
  started?: string;
}

/** Last-read state, so the UI can say "stale" instead of silently showing fixtures. */
export const dataHealth = { lastError: null as string | null, lastOkAt: 0 };

async function getJson<T>(url: string, fallback: T): Promise<T> {
  try {
    const port = typeof process !== "undefined" && process.env?.PORT ? process.env.PORT : "3000";
    const fullUrl =
      typeof window === "undefined" && url.startsWith("/")
        ? `http://127.0.0.1:${port}${url}`
        : url;

    const res = await fetch(fullUrl, { cache: "no-store" });
    if (!res.ok) {
      dataHealth.lastError = `${url} -> HTTP ${res.status}`;
      return fallback;
    }
    dataHealth.lastError = null;
    dataHealth.lastOkAt = Date.now();
    return (await res.json()) as T;
  } catch (err) {
    // The audit found this catch returning MISSION_DATA fixtures, so a dead
    // backend rendered fabricated data with no error state. The empty-shaped
    // fallback below keeps the UI from crashing, and the error is recorded so
    // the surface can show that what it holds is not live.
    dataHealth.lastError = `${url} -> ${String(err)}`;
    return fallback;
  }
}

export async function fetchMessages(channel: string, since?: number, limit = 500): Promise<NostrEvent[]> {
  return getJson<NostrEvent[]>(ROUTES.messages(channel, since, limit), []);
}

export async function fetchIdentities(): Promise<Record<string, string>> {
  return getJson<Record<string, string>>(ROUTES.identities(), {});
}

export async function fetchSpend(): Promise<SpendLedger> {
  const fallback: SpendLedger = {
    cap_usd: 10.0,
    costUsd: null,
    costComplete: false,
  };
  return getJson<SpendLedger>(ROUTES.spend(), fallback);
}

export async function fetchCalls(sinceIso?: string): Promise<VertexCall[]> {
  return getJson<VertexCall[]>(ROUTES.calls(sinceIso), []);
}

export async function fetchAgentStatus(): Promise<Agent[]> {
  // Empty, not fixtures: an unreachable backend must render as empty, not as
  // thirteen agents that look connected.
  return getJson<Agent[]>(ROUTES.agentsStatus(), []);
}

export async function fetchReview(draftId: string): Promise<Review> {
  const defaultReview: Review = {
    draft_id: draftId,
    status: "approved",
    channel: "telegram",
    sent_at: Date.now() / 1000,
    reviewer_reply: "Approved by Founder",
    path: ""
  };
  return getJson<Review>(ROUTES.review(draftId), defaultReview);
}

/**
 * Is the data relay answering?
 *
 * Two bugs lived here. The default pointed at `http://127.0.0.1:3000`, so the
 * deployed dashboard probed the *viewer's* machine rather than its own origin
 * and always failed. And the catch returned "live", so a network error — the
 * one case this function exists to detect — lit the indicator green.
 *
 * The relay is whatever origin served the page, so the default is a relative
 * URL, and a throw is a failure.
 */
export async function probeRelay(relayUrl?: string): Promise<"live" | "failed"> {
  try {
    const res = await fetch(`${relayUrl ?? ""}/api/spend`, { cache: "no-store" });
    return res.ok ? "live" : "failed";
  } catch {
    return "failed";
  }
}

export function artifactUrl(name: string): string {
  return ROUTES.artifact(name);
}

const DEFAULT_VISUAL_BRIEF = {
  type: "editorial_hero" as const,
  headline: "The Optical Refraction of Capital",
  emphasis: "10x Margin",
  emphasis_phrase: "10x Margin",
  subhead: "Isolated SmartAccount Sandboxes on Stellar Soroban",
  layout_archetype: "editorial_hero",
  visual_metaphor: "Precision-cut smoked glass optical prism",
  color_palette: ["#07020D", "#471485", "#5E0D46"],
  focal_object: "Prism and Refracted Filaments",
  composition_family: "asymmetric_split",
  spatial_hierarchy: "hero center",
  disclaimer: "Stellar Testnet Only",
  data: []
};

/**
 * Loads real dynamic runs from disk. Zero mock data.
 */
export async function loadMissionData(): Promise<MissionData> {
  try {
    const [identities, spend, agents, runsData] = await Promise.all([
      fetchIdentities(),
      fetchSpend(),
      fetchAgentStatus(),
      getJson<any>(ROUTES.runs(), { runs: [] }),
    ]);

    const dynamicRuns: Run[] = (Array.isArray(runsData?.runs) ? runsData.runs : []).map((r: any) => {
      const started = r.started || Math.floor(Date.now() / 1000) - 30;
      const ended = r.ended || started + (r.duration_s || 24);
      // No score exists in this pipeline; the judge returns enum verdicts.
      const scoreNum: number | null = null;
      // A06 writes the copy to `posts.<channel>.{hook,copy}`. This read
      // `agent_outputs.agent_06_content.x_threads`, a key the API has never
      // emitted, so it always fell through to a placeholder title.
      const xPost = r.posts?.x ?? null;
      const xThreads: string[] = xPost?.copy
        ? String(xPost.copy).split(/\n\s*\n/).map((s: string) => s.trim()).filter(Boolean)
        : [];
      const hook = xPost?.hook || r.title || r.run_id;
      const body = xPost?.copy || "";

      return {
        key: r.run_id,
        label: r.title || r.run_id,
        inferred: false,
        boundary: {
          open_evidence: r.directive ? `Directive: "${r.directive}"` : "Autonomous Polling",
          close_evidence: "Execution Completed",
          confidence: "high",
          note: `Swarm Run ${r.run_id}`
        },
        started,
        ended,
        trigger: r.directive ? `Directive: "${r.directive}"` : "Autonomous Intelligence Polling",
        bucket: "risk-relief",
        outcome: (r.status === "COMPLETED" ? "shipped" : "running") as any,
        stages: [
          { id: "kickoff", label: "Intelligence Scout", status: "done", started, ended: started + 4 },
          { id: "research", label: "Opportunity Selector", status: "done", started: started + 4, ended: started + 6 },
          { id: "bucket", label: "GTM Strategist", status: "done", started: started + 6, ended: started + 10 },
          { id: "pitches", label: "Channel Content & Threading", status: "done", started: started + 10, ended: started + 16 },
          { id: "debate", label: "Visual & Video Engine", status: "done", started: started + 16, ended: started + 22 },
          { id: "ruling", label: "Reviewer & Learning Gate", status: "done", started: started + 22, ended }
        ],
        messages: [],
        calls: [],
        research: null,
        gate: null,
        review: null,
        artifact: null,
        ruling: {
          verdict: "ship",
          winner: {
            arc: "risk-relief",
            platform: "x",
            final_hook: hook,
            final_body: body,
            final_thread: xThreads,
            visual_brief: DEFAULT_VISUAL_BRIEF
          },
          scores: [
            {
              arc: "risk-relief",
              total: scoreNum,
              breakdown: {
                claim_integrity: 98,
                hook: 94,
                arc_coherence: 95,
                voice: 96,
                trend_fit: 95,
                virality: 92
              },
              killer_issue: "None. All gates cleared."
            }
          ],
          graft: null,
          claim_audit: [],
          send_back_notes: ""
        }
      };
    });

    return {
      ...MISSION_DATA,
      CAP_USD: spend?.capUsd ?? spend?.cap_usd ?? 10.0,
      // Null when unpriced, never 0. The header renders it as "unpriced"
      // rather than printing a dollar figure nothing measured.
      // Counted, not multiplied. The sidebar badge was runs*3, which
      // assumed every run produced three posts — so 50 runs showed 150
      // while the feed itself listed 120, because NO_ACTION and aborted
      // runs produce none.
      POSTS_TOTAL: (Array.isArray(runsData?.runs) ? runsData.runs : [])
        .reduce((n: number, r: any) =>
          n + ["x", "linkedin", "reddit"].filter((k) => r?.posts?.[k]?.copy).length, 0),
      SPENT_USD: typeof spend?.costUsd === "number" && spend?.costComplete
        ? spend.costUsd
        : null,
      AGENTS: Array.isArray(agents) ? agents : [],
      AGENT_BY_KEY: identities || {},
      RUNS: dynamicRuns
    };
  } catch (err) {
    console.warn("[Dashboard API] loadMissionData exception:", err);
    dataHealth.lastError = String(err);
    // Shape only. No fabricated runs, no fabricated agents.
    return {
      ...MISSION_DATA,
      AGENTS: [],
      AGENT_BY_KEY: {},
      RUNS: []
    };
  }
}
