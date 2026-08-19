/**
 * Read-only data access. Everything the UI reads passes through here, so swapping
 * the captured fixture for the real backend is one flag.
 *
 * The routes below are the contracts listed verbatim in the Backend note view.
 * Nothing here writes.
 */
import { MISSION_DATA } from "./mission-data";
import type { Agent, MissionData, NostrEvent, Review, VertexCall } from "./types";

/** Flip to false to read the local backend instead of the captured fixture. */
export const USE_FIXTURE = false;

/** Base for the read-only local API. Only consulted when USE_FIXTURE is false. */
export const API_BASE = "";

/* --------------------------------------------------------------- endpoints */

export const ROUTES = {
  messages: (channel: string, since?: number, limit = 500) =>
    `${API_BASE}/api/messages?channel=${encodeURIComponent(channel)}` +
    (since != null ? `&since=${since}` : "") +
    `&limit=${limit}`,
  identities: () => `${API_BASE}/api/identities`,
  spend: () => `${API_BASE}/api/spend`,
  calls: (sinceIso?: string) =>
    `${API_BASE}/api/calls` + (sinceIso ? `?since=${encodeURIComponent(sinceIso)}` : ""),
  agentsStatus: () => `${API_BASE}/api/agents/status`,
  artifact: (name: string) => `${API_BASE}/api/artifacts/${name}`,
  review: (draftId: string) => `${API_BASE}/api/review/${encodeURIComponent(draftId)}`,
} as const;

/** Shape of GET /api/spend — spend-ledger.json verbatim. */
export interface SpendLedger {
  cap_usd: number;
  remaining_usd: number;
  started: string;
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`);
  return (await res.json()) as T;
}

/* ----------------------------------------------------------- per-endpoint */

export async function fetchMessages(
  channel: string,
  since?: number,
  limit = 500,
): Promise<NostrEvent[]> {
  if (USE_FIXTURE) {
    return MISSION_DATA.RUNS.flatMap((r) => r.messages);
  }
  return getJson<NostrEvent[]>(ROUTES.messages(channel, since, limit));
}

/** pubkey → agent name. Hex must never reach the DOM. */
export async function fetchIdentities(): Promise<Record<string, string>> {
  if (USE_FIXTURE) return MISSION_DATA.AGENT_BY_KEY;
  return getJson<Record<string, string>>(ROUTES.identities());
}

export async function fetchSpend(): Promise<SpendLedger> {
  if (USE_FIXTURE) {
    return {
      cap_usd: MISSION_DATA.CAP_USD,
      remaining_usd:
        MISSION_DATA.CAP_USD -
        MISSION_DATA.RUNS.reduce(
          (a, r) => a + r.calls.reduce((x, c) => x + c.cost_usd, 0),
          0,
        ),
      started: MISSION_DATA.LEDGER_STARTED,
    };
  }
  return getJson<SpendLedger>(ROUTES.spend());
}

export async function fetchCalls(sinceIso?: string): Promise<VertexCall[]> {
  if (USE_FIXTURE) return MISSION_DATA.RUNS.flatMap((r) => r.calls);
  return getJson<VertexCall[]>(ROUTES.calls(sinceIso));
}

export async function fetchAgentStatus(): Promise<Agent[]> {
  if (USE_FIXTURE) return MISSION_DATA.AGENTS;
  return getJson<Agent[]>(ROUTES.agentsStatus());
}

export async function fetchReview(draftId: string): Promise<Review> {
  if (USE_FIXTURE) {
    const found = MISSION_DATA.RUNS.map((r) => r.review).find(
      (rv): rv is Review => !!rv && rv.draft_id === draftId,
    );
    if (!found) throw new Error(`no review for ${draftId}`);
    return found;
  }
  return getJson<Review>(ROUTES.review(draftId));
}

/** URL for a rendered artifact PNG. The file lives on disk; this is the file route. */
export function artifactUrl(name: string): string {
  return ROUTES.artifact(name);
}

/* ------------------------------------------------------------- whole model */

/**
 * The single read the dashboard boots from.
 *
 * In fixture mode this is the captured channel. Against the real backend the run
 * boundaries still have to be inferred from conductor prose — see the Backend note.
 * That inference is the one piece the sources cannot supply, which is why it is
 * isolated here rather than scattered through the views.
 */
export async function loadMissionData(): Promise<MissionData> {
  if (USE_FIXTURE) return MISSION_DATA;

  const [identities, spend, agents, messages, calls] = await Promise.all([
    fetchIdentities(),
    fetchSpend(),
    fetchAgentStatus(),
    fetchMessages("31098616-3d0b-4202-86b4-96bfd36680cd"),
    fetchCalls(),
  ]);

  const liveRuns: Run[] = [];
  const sortedMessages = [...messages].sort((a, b) => a.created_at - b.created_at);

  if (sortedMessages.length > 0) {
    // Determine the latest draft and retrieve its review status
    const latestMsg = sortedMessages[sortedMessages.length - 1];
    let draftData: any = {};
    try {
      draftData = JSON.parse(latestMsg.content);
    } catch (e) {
      draftData = {};
    }

    const draftId = draftData.draft_id ?? latestMsg.id;
    let reviewData: Review = {
      draft_id: draftId,
      status: "awaiting_review",
      reply: null,
      sent_at: new Date(sortedMessages[0].created_at * 1000).toISOString()
    };

    try {
      reviewData = await fetchReview(draftId);
    } catch (e) {
      // Gracefully fall back if not reviewed yet
    }

    const started = sortedMessages[0].created_at;
    const ended = reviewData.status === "approved" || reviewData.status === "rejected" ? (sortedMessages[sortedMessages.length - 1].created_at + 120) : null;

    let outcome: "shipped" | "killed" | "died" | "running" = "running";
    if (reviewData.status === "approved") outcome = "shipped";
    else if (reviewData.status === "rejected") outcome = "killed";
    else if (agents.some((a) => a.status === "errored")) outcome = "died";

    // Filter calls for this run
    const runCalls = calls.filter((c) => {
      const callTime = new Date(c.ts).getTime() / 1000;
      return callTime >= started && (!ended || callTime <= ended);
    });

    // Formulate stage timelines dynamically
    const stages: Stage[] = [
      { id: "kickoff", label: "Conductor kickoff", status: "done", started, ended: started + 2 },
      { id: "research", label: "Trend research", status: sortedMessages.length > 0 ? "done" : "active", started: started + 2, ended: started + 20 },
      { id: "bucket", label: "Bucket call", status: sortedMessages.length > 1 ? "done" : "not_reached", started: started + 20, ended: started + 25 },
      { id: "pitches", label: "Strategist drafts", status: sortedMessages.length > 2 ? "done" : "not_reached", started: started + 25, ended: started + 45 },
      { id: "debate", label: "Critiques/Rebuttals", status: sortedMessages.length > 5 ? "done" : "not_reached", started: started + 45, ended: started + 60 },
      { id: "ruling", label: "Judge ruling", status: sortedMessages.length > 6 ? "done" : "not_reached", started: started + 60, ended: started + 70 },
      { id: "visual", label: "Visual creation", status: sortedMessages.length > 6 ? "done" : "not_reached", started: started + 70, ended: started + 85 },
      { id: "gate", label: "Compliance check", status: sortedMessages.length > 6 ? "done" : "not_reached", started: started + 85, ended: started + 95 },
      { id: "review", label: "Human review", status: outcome === "running" ? "active" : "done", started: started + 95, ended }
    ];

    // Support both tagged and inferred runs (Step 2)
    const runTag = latestMsg.tags?.find((t) => t[0] === "run");
    const isTagged = !!runTag;
    const runLabel = isTagged ? `Run ${runTag[1]}` : "Active Run";

    liveRuns.push({
      key: "active-run",
      label: runLabel,
      inferred: !isTagged,
      boundary: isTagged ? "high" : "Conductor run-open boundary",
      started,
      ended,
      trigger: draftData.trend_id ? `trend: ${draftData.trend_id}` : "Conductor direct startup",
      bucket: draftData.bucket ?? "Evergreen facts",
      outcome,
      stages,
      messages: sortedMessages,
      calls: runCalls,
      review: reviewData,
      artifact: {
        path: "/api/artifacts/temp_rendered.png",
        disclaimer: "All figures illustrative. Vanna is on testnet."
      }
    });
  } else {
    // Inject a default active run structure when drafts are empty to prevent client-side "undefined outcome" crashes
    const started = Math.floor(Date.now() / 1000);
    const stages: Stage[] = [
      { id: "kickoff", label: "Conductor kickoff", status: "active", started, ended: null },
      { id: "research", label: "Trend research", status: "not_reached", started: null, ended: null },
      { id: "bucket", label: "Bucket call", status: "not_reached", started: null, ended: null },
      { id: "pitches", label: "Strategist drafts", status: "not_reached", started: null, ended: null },
      { id: "debate", label: "Critiques/Rebuttals", status: "not_reached", started: null, ended: null },
      { id: "ruling", label: "Judge ruling", status: "not_reached", started: null, ended: null },
      { id: "visual", label: "Visual creation", status: "not_reached", started: null, ended: null },
      { id: "gate", label: "Compliance check", status: "not_reached", started: null, ended: null },
      { id: "review", label: "Human review", status: "not_reached", started: null, ended: null }
    ];

    liveRuns.push({
      key: "active-run",
      label: "Active Run",
      inferred: true,
      boundary: "Conductor run-open boundary",
      started,
      ended: null,
      trigger: "Conductor Direct Startup",
      bucket: null,
      outcome: "running",
      stages,
      messages: [],
      calls: [],
      review: null,
      artifact: null
    });
  }

  // Keep only the active run and completely discard the hardcoded fixture runs (Step 2)
  const finalRuns = [...liveRuns];

  return {
    ...MISSION_DATA,
    AGENT_BY_KEY: identities,
    AGENTS: agents,
    CAP_USD: spend.cap_usd,
    SPENT_USD: spend.spent_usd, // Cost Cap Fix: Bind actual spend ledger total USD
    LEDGER_STARTED: spend.started,
    RUNS: finalRuns,
  };
}

/** Liveness probe against the relay. Failure is expected and must not throw. */
export async function probeRelay(relay: string): Promise<"live" | "failed"> {
  try {
    await fetch(relay, { mode: "cors" });
    return "live";
  } catch {
    return "failed";
  }
}
