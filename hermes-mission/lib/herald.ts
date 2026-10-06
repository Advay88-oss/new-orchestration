/**
 * Helpers for the Herald app (/app): how a run reads to the owner — its
 * status, headline, the twelve agent steps, and short dates.
 *
 * The design reference (App-html.zip, Main.dc.html) names six post states:
 * Writing, Ready for review, Blocked, Approved, Revision requested, Killed.
 * Runs that ended without a post are listed separately with a reason.
 */

export type Run = Record<string, any>;

export type PostState = "running" | "review" | "blocked" | "approved" | "revised" | "killed" | "nopost";

export const STATE_LABEL: Record<PostState, [string, string]> = {
  running: ["Writing", "s-running"],
  review: ["Ready for review", "s-review"],
  blocked: ["Blocked", "s-blocked"],
  approved: ["Approved", "s-approved"],
  revised: ["Revision requested", "s-review"],
  killed: ["Killed", "s-failed"],
  nopost: ["No post", ""],
};

/** A run marked running that has not moved for this long died mid-run. */
const STALE_S = 90 * 60;

export function isWriting(r: Run): boolean {
  if (r.status !== "running") return false;
  const started = Number(r.started || 0);
  return started > 0 && Date.now() / 1000 - started < STALE_S;
}

export function hasPost(r: Run): boolean {
  const posts = r.posts || {};
  return Boolean(r.visual) || ["x", "linkedin", "reddit"].some((k) => posts[k]?.copy || posts[k]?.hook);
}

export function stateOf(r: Run): PostState {
  if (isWriting(r)) return "running";
  const v = String(r.decision?.verdict || "");
  if (v === "approve" || v === "edit") return "approved";
  if (v === "revise") return "revised";
  if (v === "kill") return "killed";
  if (!hasPost(r)) return "nopost";
  if (r.blocked_reason || r.status === "review_blocked") return "blocked";
  return "review";
}

export function headlineOf(r: Run): string {
  const brief = String(r.poster_brief || "");
  const m = brief.match(/Headline:\s*([^\n]+)/);
  if (m) return m[1].replace(/\s*\(gradient word:.*\)\s*$/, "").trim();
  const hook = r.posts?.x?.hook || r.reasoning?.hook;
  if (hook) return String(hook);
  if (r.title && r.title !== r.run_id) return String(r.title);
  return "Untitled post";
}

/** Why a run ended without a post, in a sentence. */
export function noPostReason(r: Run): [string, string] {
  if (r.status === "NO_ACTION" || r.status === "KILL") {
    const t = r.title && r.title !== r.run_id ? String(r.title) : "";
    return ["Declined", t ? "Declined — “" + t.slice(0, 90) + "” had nothing for the product to say." : "Declined — nothing worth a post."];
  }
  if (r.status === "running") return ["Stopped", "Stopped before it finished."];
  if (r.status === "aborted") return ["Nothing to read", "Stopped before writing started."];
  if (r.status === "failed") return ["Failed", "A step failed before the post was written."];
  return ["No post", "Ended without a post."];
}

/** Who stopped a blocked post, and why, from the reviewer's notes. */
export function blockOf(r: Run): { by: string; reason: string } | null {
  if (stateOf(r) !== "blocked") return null;
  const n = r.review_notes || {};
  const facts: string[] = Array.isArray(n.facts) ? n.facts : [];
  const bad = facts.find((f) => /contradicted|unsupported|not supported/i.test(f));
  if (bad) return { by: "Fact check", reason: bad.replace(/^\w+:\s*/, "").split(" — ")[0] + " — " + (bad.split(" — ")[1] || "not in your sources") };
  if (Array.isArray(n.blocked_claims) && n.blocked_claims.length) return { by: "Fact check", reason: "Unsourced claim: " + String(n.blocked_claims[0]).slice(0, 160) };
  if (n.creative === "REJECT") {
    const a = (r.creative_review?.assets || [])[0] || {};
    const why = Array.isArray(a.prohibited_elements) && a.prohibited_elements.length
      ? "The poster shows " + a.prohibited_elements.slice(0, 2).join(", ") + "."
      : a.on_brand === false ? "The poster is off brand." : "The poster did not pass.";
    return { by: "Creative check", reason: why };
  }
  const issues = Object.entries(n.channel_issues || {}).find(([, v]) => Array.isArray(v) && v.length) as [string, string[]] | undefined;
  if (issues) return { by: "Review", reason: issues[1][0] };
  return { by: "Review", reason: "The reviewer held it before it reached you." };
}

export const AGENT_STEPS: [string, string][] = [
  ["A01_intelligence_scout", "Scout"],
  ["A02_market_analyst", "Analyst"],
  ["A02_opportunity_selector", "Topic picker"],
  ["A03_gtm_strategist", "Strategist"],
  ["A06_channel_adapter", "Copywriter"],
  ["A07_creative_director", "Creative director"],
  ["A08_visual_synthesis", "Poster designer"],
  ["A09_video_production", "Video producer"],
  ["A15_creative_judge", "Creative check"],
  ["A10_reviewer_firewall", "Fact check"],
  ["A11_delivery", "Review packet"],
  ["A13_learning_engine", "Learning"],
];

export type Step = { name: string; s: "done" | "running" | "pending" | "blocked" | "declined" | "skipped"; label: string };

export function stepsOf(r: Run): Step[] {
  const agents: any[] = Array.isArray(r.agents) ? r.agents : [];
  const writing = isWriting(r);
  const block = blockOf(r);
  let sawRunning = false;
  return AGENT_STEPS.map(([id, name]) => {
    const a = agents.find((x) => x.id === id);
    let s: Step["s"] = "skipped";
    if (a?.status === "ok" || a?.status === "degraded") s = "done";
    else if (a?.status === "failed") s = "blocked";
    else if (a?.status === "running") { s = "running"; sawRunning = true; }
    else if (writing) { s = sawRunning ? "pending" : "running"; sawRunning = true; }
    if (block && block.by === name) s = "blocked";
    if ((r.status === "NO_ACTION" || r.status === "KILL") && (name === "Topic picker" || name === "Strategist") && s === "done") s = "declined";
    const label = { done: "Done", running: "Working…", pending: "Waiting", blocked: "Blocked", declined: "Declined", skipped: "Not needed" }[s];
    return { name, s, label: a?.detail ? label + " · " + String(a.detail).slice(0, 120) : label };
  });
}

/** "Today, 09:12", "Yesterday, 16:30", "3 Oct, 11:02". */
export function whenOf(unixOrIso: number | string | null | undefined): string {
  if (unixOrIso == null || unixOrIso === "") return "";
  const d = typeof unixOrIso === "number" ? new Date(unixOrIso * 1000) : new Date(unixOrIso);
  if (Number.isNaN(d.getTime())) return "";
  const now = new Date();
  const time = d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false });
  if (d.toDateString() === now.toDateString()) return "Today, " + time;
  const y = new Date(now); y.setDate(now.getDate() - 1);
  if (d.toDateString() === y.toDateString()) return "Yesterday, " + time;
  return d.toLocaleDateString(undefined, { day: "numeric", month: "short" }) + ", " + time;
}

/** "4m", "2h", "3d". */
export function agoOf(iso: string | number | null | undefined): string {
  if (iso == null || iso === "") return "";
  const t = typeof iso === "number" ? iso * 1000 : Date.parse(String(iso));
  if (Number.isNaN(t)) return "";
  const s = Math.max(0, (Date.now() - t) / 1000);
  if (s < 3600) return Math.max(1, Math.round(s / 60)) + "m";
  if (s < 86400) return Math.round(s / 3600) + "h";
  return Math.round(s / 86400) + "d";
}

/** Day heading for a feed: Today, Yesterday, or a date. */
export function dayOf(iso: string | number | null | undefined): string {
  if (iso == null || iso === "") return "Earlier";
  const d = typeof iso === "number" ? new Date(iso * 1000) : new Date(iso);
  if (Number.isNaN(d.getTime())) return "Earlier";
  const now = new Date();
  if (d.toDateString() === now.toDateString()) return "Today";
  const y = new Date(now); y.setDate(now.getDate() - 1);
  if (d.toDateString() === y.toDateString()) return "Yesterday";
  return d.toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "short" });
}

/** A short channel mark for a source: X, R, TG, N, Docs. */
export function glyphOf(kind: string | null | undefined, name?: string | null): string {
  const k = String(kind || "").toLowerCase() + " " + String(name || "").toLowerCase();
  if (/twitter|\bx\b|x\.com/.test(k)) return "X";
  if (/reddit/.test(k)) return "R";
  if (/telegram|t\.me/.test(k)) return "TG";
  if (/linkedin/.test(k)) return "in";
  if (/defillama|llama/.test(k)) return "DL";
  if (/github/.test(k)) return "GH";
  if (/docs|blog/.test(k)) return "Docs";
  if (/gdelt|news|coindesk|block|decrypt|defiant|cointelegraph/.test(k)) return "N";
  if (/galxe/.test(k)) return "G";
  if (/zealy/.test(k)) return "Z";
  return (String(name || kind || "?").trim().charAt(0) || "?").toUpperCase();
}

/** The poster style for a run without an image, picked from its id. */
export function posterClass(id: string): string {
  const cls = ["p-ink", "p-sage", "p-paper", "p-indigo"];
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return cls[h % cls.length];
}
