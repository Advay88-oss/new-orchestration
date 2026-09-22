"use client";

/**
 * Direct translation of the original component's state + `renderVals()`.
 *
 * The original recomputed every value on each render and ticked a 1s timer that
 * either advanced the poll or forced a repaint so elapsed times stayed live.
 * That is reproduced exactly: `frame` is the forceUpdate, `lastPoll` the poll clock.
 */
import { useCallback, useEffect, useState } from "react";
import { probeRelay } from "./api";
import {
  ACCENT,
  ACCENT_DEEP,
  ACCENT_SOFT,
  BAD,
  BAD_SOFT,
  GRADIENT,
  INK,
  INK2,
  INK3,
  MONO,
  MUTED,
  NEUTRAL,
  OK,
  OK_SOFT,
  WARN,
  WARN_SOFT,
} from "./colors";
import {
  ARC_OF,
  ARC_ORDER,
  STRATS,
  chipStyle,
  classify,
  crossReplies,
  dur,
  int,
  local,
  localDate,
  parentOf,
  pill,
  rulingOf,
  runCost,
  steppsList,
  tierStyle,
  tint,
  usd,
  utc,
} from "./derive";
import type {
  ArcScore,
  Classified,
  MissionControlProps,
  MissionData,
  NostrEvent,
  Run,
  Stage,
} from "./types";

type RelayState = "unknown" | "trying" | "live" | "failed";

export type ExpandedMap = Record<string, boolean>;

export function useMissionControl(props: MissionControlProps) {
  const [data, setData] = useState<MissionData | null>(null);
  const [view, setView] = useState<string>("runs");
  const [runKey, setRunKey] = useState<string>("");
  const [expanded, setExpanded] = useState<ExpandedMap>({});
  const [paused, setPaused] = useState(false);
  const [tick, setTick] = useState(0);
  const [interval_, setInterval_] = useState(15);
  // Starts at 0 so the server render and the first client render agree; the mount
  // effect sets the real clock.
  const [lastPoll, setLastPoll] = useState(0);
  const [relay, setRelay] = useState<RelayState>("unknown");
  const [liveKey, setLiveKey] = useState<string | null>(null);
  const [postFilter, setPostFilter] = useState("All");
  const [, setFrame] = useState(0);

  /* ---------------------------------------------------------- componentDidMount & Polling */
  useEffect(() => {
    let alive = true;
    import("./api").then(({ loadMissionData, probeRelay }) =>
      loadMissionData().then((d) => {
        if (!alive) return;
        setData(d);
        // Step 2 Fix: Safely load RUNS[0] (active run) since hardcoded runs are removed
        if (d.RUNS && d.RUNS.length > 0) {
          setRunKey(prev => prev || d.RUNS[0].key);
        }
        // Auto-probe the relay on every tick
        probeRelay(d.RELAY ?? "http://127.0.0.1:3000").then(setRelay);
      }),
    );
    return () => {
      alive = false;
    };
  }, [tick]);

  useEffect(() => {
    setLastPoll(Date.now());
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (paused) return;
      const elapsed = (Date.now() - lastPoll) / 1000;
      if (elapsed >= interval_) {
        setLastPoll(Date.now());
        setTick((t) => t + 1);
      } else {
        setFrame((f) => f + 1);
      }
    }, 1000);
    return () => window.clearInterval(timer);
  }, [paused, lastPoll, interval_]);

  /* ------------------------------------------------------------------- helpers */
  const hues = useCallback((): Record<string, string> => {
    const d = ["#703AE6", "#24A0A9", "#FF007A"];
    const v = Array.isArray(props.arcPalette) ? props.arcPalette : d;
    return {
      "capital-efficiency": v[0] || d[0],
      "risk-relief": v[1] || d[1],
      "agentic-credit": v[2] || d[2],
    };
  }, [props.arcPalette]);

  const arcHue = useCallback((arc: string): string => hues()[arc] || INK2, [hues]);
  const agentHue = useCallback(
    (id: string): string => (ARC_OF[id] ? arcHue(ARC_OF[id]) : INK),
    [arcHue],
  );
  const cap = props.capUsd ?? (data ? data.CAP_USD : 10);

  const agentOf = useCallback(
    (msg: NostrEvent): string => (data ? data.AGENT_BY_KEY[msg.pubkey] || "unknown" : "unknown"),
    [data],
  );

  const runs = useCallback((): Run[] => (data ? data.RUNS : []), [data]);

  const totalSpent = data ? (data.SPENT_USD ?? data.RUNS.reduce((a, r) => a + runCost(r), 0)) : 0;

  const outcomeMeta = useCallback((run?: Run | null) => {
    if (!run) return { label: "Standby", color: NEUTRAL, soft: "#F4F4F4", note: "No active run" };
    if (run.outcome === "shipped")
      return { label: "Shipped", color: OK, soft: OK_SOFT, note: "sent for human review" };
    if (run.outcome === "killed")
      return { label: "Killed", color: BAD, soft: BAD_SOFT, note: "judge rejected all three" };
    if (run.outcome === "died")
      return {
        label: "Died mid-run",
        color: NEUTRAL,
        soft: "#F4F4F4",
        note: "stopped at " + (run.died ? run.died.stage : ""),
      };
    return { label: "Running", color: ACCENT, soft: ACCENT_SOFT, note: "no close message yet" };
  }, []);

  const headlineOf = useCallback((run?: Run | null): string => {
    if (!run) return "System 2 Standby";
    const rl = rulingOf(run);
    if (rl && rl.winner) return rl.winner.final_hook + " …";
    if (run.outcome === "killed") return "reject_all — nothing cleared 70";
    if (run.outcome === "died") return run.died ? run.died.error : "";
    const last = run.messages && run.messages.length > 0 ? run.messages[run.messages.length - 1] : null;
    if (!last) return "Standby";
    return classify(last).type === "broken"
      ? "awaiting third pitch — one arrived truncated"
      : "in flight";
  }, []);

  /* -------------------------------------------------------------------- actions */
  const toggleExpanded = useCallback((key: string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const tryRelay = useCallback(() => {
    setRelay("trying");
    probeRelay(data ? data.RELAY : "http://127.0.0.1:3000").then(setRelay);
  }, [data]);

  /* ================================================================ renderVals */
  // Computed on every render, exactly as the original class did — the 1s timer's
  // forceUpdate is what keeps elapsed times live.
  const vals = (() => {
    const d = data;

    const nav = [
      { id: "live", label: "Agent Decisions" },
      { id: "scheduler", label: "⏰ 24/7 Scheduler" },
      { id: "ideas", label: "💡 Ideas Panel" },
      { id: "memes", label: "🎭 Crypto Memes" },
      { id: "runs", label: "Runs Observatory" },
      { id: "run", label: "Run Detail" },
      { id: "agents", label: "13 GTM Agents" },
      { id: "research", label: "Scraped Intelligence" },
      { id: "pipeline", label: "13-Stage Matrix" },
      { id: "posts", label: "Multi-Channel Feed" },
      { id: "cost", label: "Cost & Cap" },
      { id: "notes", label: "Backend Topology" },
    ].map((n) => {
      const on = view === n.id;
      return {
        id: n.id,
        label: n.label,
        count:
          n.id === "runs"
            ? String(runs().length)
            : n.id === "agents"
              ? "13"
              : n.id === "posts"
                ? String(runs().length > 0 ? runs().length * 3 : 0)
                : n.id === "live"
                  ? runs().some((r) => r.outcome === "running")
                    ? "●"
                    : ""
                  : "",
        go: () => setView(n.id),
        dot: {
          width: "6px",
          height: "6px",
          borderRadius: "999px",
          flex: "0 0 6px",
          background: on ? ACCENT : "#2C2C2C",
        } as const,
        style: {
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "8px",
          width: "100%",
          textAlign: "left",
          padding: "11px 14px",
          borderRadius: "12px",
          cursor: "pointer",
          border: "none",
          background: on ? "#1E1E1E" : "transparent",
          color: on ? "#FFFFFF" : "#A9A9A9",
          fontWeight: 600,
          fontSize: "14px",
          lineHeight: "21px",
        } as React.CSSProperties,
      };
    });

    const spent = totalSpent,
      pct = Math.min(1, spent / cap);
    const capColor = pct > 0.85 ? BAD : pct > 0.6 ? ACCENT : INK;
    const capBar = pct > 0.85 ? "linear-gradient(90deg, #FC5457, #E54C4F)" : GRADIENT;
    const secsLeft = Math.max(0, Math.ceil(interval_ - (Date.now() - lastPoll) / 1000));
    const intervals = [10, 15, 60].map((v) => {
      const on = interval_ === v;
      return {
        label: v + "s",
        set: () => {
          setInterval_(v);
          setLastPoll(Date.now());
        },
        style: {
          border: "1px solid " + (on ? ACCENT : "#2C2C2C"),
          background: on ? "rgba(112,58,230,0.18)" : "transparent",
          color: on ? "#FFFFFF" : "#777777",
          borderRadius: "8px",
          padding: "7px 10px",
          fontSize: "11px",
          fontWeight: 600,
          cursor: "pointer",
          fontFamily: MONO,
        } as React.CSSProperties,
      };
    });

    const base = {
      nav,
      intervals,
      isRuns: view === "runs",
      isRun: view === "run",
      isAgents: view === "agents",
      isResearch: view === "research",
      isScheduler: view === "scheduler",
      isIdeas: view === "ideas",
      isMemes: view === "memes",
      isCost: view === "cost",
      isNotes: view === "notes",
      isLive: view === "live",
      isPipeline: view === "pipeline",
      isPosts: view === "posts",
      goRuns: () => setView("runs"),
      goLive: () => setView("live"),
      goResearch: () => setView("research"),
      goScheduler: () => setView("scheduler"),
      goIdeas: () => setView("ideas"),
      goMemes: () => setView("memes"),
      runKey,
      openRun: (key?: string) => {
        if (key) setRunKey(key);
        setView("run");
      },
      goNotes: (e?: { preventDefault?: () => void }) => {
        if (e && e.preventDefault) e.preventDefault();
        setView("notes");
      },
      spentText: usd(spent, 4),
      capText: usd(cap, 2),
      capPct: (pct * 100).toFixed(1) + "%",
      capColor,
      capBar,
      capNote: pct > 0.85 ? "approaching cap" : Math.round(pct * 100) + "% of cap used",
      relayDotColor: relay === "live" ? OK : "#595959",
      relayLabel: d ? "127.0.0.1:3000" : "loading…",
      relayNote:
        relay === "live"
          ? "live relay"
          : relay === "failed"
            ? "unreachable — showing captured fixture"
            : "not connected — showing captured fixture",
      tryRelay,
      togglePause: () => {
        setPaused((p) => !p);
        setLastPoll(Date.now());
      },
      pollButton: paused ? "Resume" : "Pause",
      pollStatus: paused ? "paused" : "next in " + secsLeft + "s",
      showMatrix: (props.debateEdges ?? "both") !== "rail",
      showRail: (props.debateEdges ?? "both") !== "matrix",
    };

    if (!d) {
      return {
        ...base,
        pageTitle: "Runs",
        pageSub: "Loading captured channel…",
        runRows: [],
        d: null,
        agentRows: [],
        agentScopeLabel: "",
        live: null,
        postRows: [],
        postFilters: [],
        postStats: [],
        stageMeta: [],
        lifecycles: [],
        postCount: "",
        runsFootnote: "",
        costByRun: [],
        costByAgent: [],
        costByStage: [],
        costCapLine: "",
        remainingText: "",
        ledgerStarted: "",
        cachedPct: "",
        cachedTokens: "",
        freshTokens: "",
        outputTokens: "",
        cachedCost: "",
        freshCost: "",
        outputCost: "",
        cachedOverstate: "",
        totalCalls: "",
        meanCall: "",
        rewrites: "",
        rewriteNote: "",
        endpoints: [],
        gaps: [],
      };
    }

    const titles: Record<string, [string, string]> = {
      live: [
        "Live debate",
        "The channel as it happens: who is speaking, who is answering whom, and whether the three arcs are actually arguing.",
      ],
      pipeline: [
        "Lifecycles",
        "Every run's progress through the nine stages, side by side — where each one is now and where it stopped.",
      ],
      posts: [
        "Posts",
        "Every piece of copy the pipeline produced, across all runs, with what happened to it.",
      ],
      runs: [
        "Runs",
        "Every lifecycle observed on channel " +
          d.CHANNEL.slice(0, 8) +
          "…, newest first. Boundaries are inferred, not recorded.",
      ],
      run: [
        "Run detail",
        "One inferred lifecycle: stages, the debate, research, drafts, the ruling, and what shipped.",
      ],
      agents: [
        "Agents",
        // There is no relay and there are no process logs. This header claimed
        // both for agents whose status now comes from the run journal.
        "The 13 GTM agents. Status, model and token counts are read from the "
        + "last cycle's run journal; an agent that did not run says so.",
      ],
      cost: [
        "Cost",
        "Spend against the " +
          usd(cap, 0) +
          " cap, by run, agent and stage. Cached input is priced separately.",
      ],
      notes: [
        "Backend note",
        "The endpoints this needs, what the sources cannot answer, and the run-id decision.",
      ],
      research: [
        "Scraped Intelligence",
        "Deep web research, discovered ecosystem players, and canonical claims extracted via OpenCLI Browser Bridge.",
      ],
      scheduler: [
        "24/7 Autonomous Scheduler",
        "Configurable interval jobs, failure backoff, and non-overlapping execution locks that survive restarts.",
      ],
      ideas: [
        "Strategic Ideas Panel",
        "8-12 claim-gated ideas synthesized from scraped competitor patterns, Curve/Stellar news, and on-chain intelligence.",
      ],
      memes: [
        "Crypto & DeFi Memes Panel",
        "Culturally grounded humor addressing liquidation anxiety, gas price shock, and pooled contagion without named competitor attacks.",
      ],
    };
    const [pageTitle, pageSub] = titles[view] || ["Mission Control", "System 2: 13-Agent Autonomous GTM OS"];

    const runRows = runs().map((r) => {
      const om = outcomeMeta(r),
        cr = crossReplies(r, agentOf);
      const debateStage = r.stages?.find((s) => s.id === "debate");
      let debateLabel: string, debateColor: string;
      if (!debateStage || debateStage.status === "not_reached") {
        debateLabel = "not reached";
        debateColor = MUTED;
      } else if (cr.n === 0) {
        debateLabel = "3 monologues — 0 cross-replies";
        debateColor = WARN;
      } else {
        debateLabel = cr.n + " cross-replies · " + cr.pairs + " of 3 pairs";
        debateColor = INK2;
      }
      const weak = r.boundary.confidence !== "high";
      return {
        key: r.key,
        label: r.label,
        startedLocal: localDate(r.started),
        startedUtc: utc(r.started),
        headline: headlineOf(r),
        trigger: r.trigger,
        bucket: r.bucket,
        bucketColor: hues()[r.bucket] || INK2,
        outcomeLabel: om.label,
        outcomeColor: om.color,
        outcomeNote: om.note,
        debateLabel,
        debateColor,
        boundaryLabel:
          r.boundary.confidence === "high"
            ? "inferred"
            : r.boundary.confidence === "open"
              ? "open"
              : "inferred · weak",
        boundaryStyle: pill(weak ? "#8C0043" : INK3, weak ? WARN_SOFT : "#F4F4F4", {
          size: "10px",
          pad: "3px 9px",
        }),
        duration: r.ended ? dur(r.ended - r.started) : dur(Date.now() / 1000 - r.started) + " …",
        cost: usd(runCost(r), 4),
        stageDots: r.stages.map((s) => ({
          id: s.id,
          title: s.label + " — " + s.status.replace("_", " "),
          style: {
            width: "14px",
            height: "5px",
            borderRadius: "999px",
            boxSizing: "border-box",
            background:
              s.status === "done"
                ? "#1F1F1F"
                : s.status === "active"
                  ? ACCENT
                  : s.status === "failed"
                    ? BAD
                    : s.status === "skipped"
                      ? "#DFDFDF"
                      : "#FFFFFF",
            border: s.status === "not_reached" ? "1px solid #DFDFDF" : "none",
          } as React.CSSProperties,
        })),
        open: () => {
          setView("run");
          setRunKey(r.key);
        },
      };
    });

    const dummyRun: Run = {
      key: "idle",
      label: "System 2 Standby",
      inferred: false,
      boundary: { open_evidence: "", close_evidence: "", confidence: "low", note: "" },
      started: 0,
      ended: 0,
      trigger: "none",
      bucket: "capital-efficiency",
      outcome: "shipped",
      stages: [
        { id: "kickoff", label: "Intelligence Scout", status: "not_reached", started: 0, ended: 0 },
        { id: "research", label: "Opportunity Selector", status: "not_reached", started: 0, ended: 0 },
        { id: "bucket", label: "GTM Strategist", status: "not_reached", started: 0, ended: 0 },
        { id: "pitches", label: "Channel Content", status: "not_reached", started: 0, ended: 0 },
        { id: "debate", label: "Tri-Arc Debate", status: "not_reached", started: 0, ended: 0 },
        { id: "ruling", label: "Reviewer Firewall", status: "not_reached", started: 0, ended: 0 }
      ],
      messages: [],
      calls: [],
      research: null,
      gate: null,
      review: null,
      artifact: null,
      ruling: null
    };

    const run = runs().find((r) => r.key === runKey) || runs()[0] || dummyRun;
    const om = outcomeMeta(run),
      cr = crossReplies(run, agentOf);
    const nowSec = Date.now() / 1000;

    const stages = run.stages.map((s: Stage) => {
      const cfg = {
        done: {
          dot: "#1F1F1F",
          label: INK,
          meta: INK3,
          weight: 500,
          bg: "#F7F7F7",
          border: "1px solid #F7F7F7",
        },
        active: {
          dot: ACCENT,
          label: ACCENT_DEEP,
          meta: ACCENT,
          weight: 600,
          bg: ACCENT_SOFT,
          border: "1px solid " + ACCENT,
        },
        failed: {
          dot: BAD,
          label: "#8B2E30",
          meta: BAD,
          weight: 600,
          bg: BAD_SOFT,
          border: "1px solid " + BAD_SOFT,
        },
        skipped: {
          dot: "transparent",
          label: INK3,
          meta: MUTED,
          weight: 500,
          bg: "#F7F7F7",
          border: "1px solid #F7F7F7",
        },
        not_reached: {
          dot: "transparent",
          label: "#BFBFBF",
          meta: "#BFBFBF",
          weight: 500,
          bg: "#FFFFFF",
          border: "1px dashed #DFDFDF",
        },
      }[s.status];
      let meta: string;
      if (s.status === "done") meta = dur((s.ended ?? 0) - (s.started ?? 0));
      else if (s.status === "active") meta = dur(nowSec - (s.started ?? 0)) + " ↻";
      else if (s.status === "failed") meta = "failed " + dur((s.ended ?? 0) - (s.started ?? 0));
      else if (s.status === "skipped") meta = "no messages";
      else meta = "not reached";
      return {
        id: s.id,
        label: s.label,
        labelColor: cfg.label,
        metaColor: cfg.meta,
        weight: cfg.weight,
        meta,
        cardStyle: {
          background: cfg.bg,
          border: cfg.border,
          borderRadius: "12px",
          padding: "14px 14px 16px",
        } as React.CSSProperties,
        dotStyle: {
          width: "10px",
          height: "10px",
          borderRadius: "999px",
          flex: "0 0 10px",
          boxSizing: "border-box",
          background: cfg.dot,
          border:
            s.status === "not_reached"
              ? "1.5px solid #DFDFDF"
              : s.status === "skipped"
                ? "1.5px dashed #A9A9A9"
                : "none",
        } as React.CSSProperties,
      };
    });

    const short: Record<string, string> = {
      "capital-efficiency": "CE",
      "risk-relief": "RR",
      "agentic-credit": "AC",
    };
    const matrixCols = ARC_ORDER.map((a) => ({
      short: short[a],
      full: a,
      hue: arcHue(a),
    }));
    const matrixRows = ARC_ORDER.map((a) => {
      const from = STRATS[ARC_ORDER.indexOf(a)];
      return {
        short: short[a],
        full: a,
        hue: arcHue(a),
        cells: ARC_ORDER.map((b) => {
          const to = STRATS[ARC_ORDER.indexOf(b)];
          const n = cr.matrix[from][to],
            self = a === b;
          return {
            key: b,
            text: n === 0 ? "·" : String(n),
            title:
              n === 0
                ? "no replies from " + a + " to " + b
                : n + " reply/replies from " + a + " to " + b,
            style: {
              width: "38px",
              height: "34px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: MONO,
              fontSize: "14px",
              fontWeight: 600,
              borderRadius: "10px",
              background:
                n === 0 ? "#F7F7F7" : self ? "#F4F4F4" : tint(arcHue(a), "24"),
              color: n === 0 ? "#BFBFBF" : self ? INK3 : arcHue(a),
            } as React.CSSProperties,
          };
        }),
      };
    });

    const debateStage = run.stages?.find((s) => s.id === "debate");
    let engagedVerdict: string, engagedDetail: string, engagedColor: string;
    if (!debateStage || debateStage.status === "not_reached") {
      engagedVerdict = "Debate not reached";
      engagedDetail =
        "This run has not got past the pitch stage. No strategist has replied to another yet — which is an absence of data, not an absence of argument.";
      engagedColor = INK3;
    } else if (cr.n === 0) {
      engagedVerdict = "Three monologues";
      engagedDetail =
        "Every strategist replied to the conductor's bucket call and to nobody else. No claim was cross-examined, and the judge cited exactly that when rejecting all three.";
      engagedColor = WARN;
    } else {
      engagedVerdict = "They argued";
      engagedDetail =
        "The strategists replied to each other " +
        cr.n +
        " times across " +
        cr.pairs +
        " of the 3 possible pairs. Every reply below shows the message it answers, so a monologue cannot hide inside a busy thread.";
      engagedColor = INK;
    }

    const buildMessages = (srcRun: Run) => {
      const bid: Record<string, NostrEvent> = {};
      srcRun.messages.forEach((x) => (bid[x.id] = x));
      return srcRun.messages.map((m) => {
        const agent = agentOf(m),
          cls: Classified = classify(m);
        const pid = parentOf(m),
          parent = pid ? bid[pid] : null;
        const parentAgent = parent ? agentOf(parent) : null;
        const pc = parent ? classify(parent) : null;
        let parentSnippet = "";
        if (parent && pc) {
          if (pc.type === "prose" || pc.type === "error")
            parentSnippet =
              parent.content.slice(0, 90) + (parent.content.length > 90 ? "…" : "");
          else if (pc.type === "draft")
            parentSnippet = "“" + pc.value.posts[0].hook + "…”";
          else if (pc.type === "research")
            parentSnippet =
              pc.value.trends.length + " trends, " + pc.value.keywords.length + " keywords";
          else if (pc.type === "ruling") parentSnippet = "verdict: " + pc.value.verdict;
          else parentSnippet = "payload";
        }
        const isStrat =
          STRATS.includes(agent as (typeof STRATS)[number]) &&
          !!parentAgent &&
          STRATS.includes(parentAgent as (typeof STRATS)[number]) &&
          parentAgent !== agent;
        const open = !!expanded[m.id];
        const full = cls.type === "prose" || cls.type === "error" ? m.content : "";
        const long = full.length > 620;
        const chip = (text: string, color?: string, bg?: string) => ({
          text,
          style: chipStyle(bg, color),
        });
        let summary = "";
        let chips: { text: string; style: React.CSSProperties }[] = [];
        if (cls.type === "research") {
          const v = cls.value;
          summary =
            "Research payload — " +
            v.trends.length +
            " trends, " +
            v.keywords.length +
            " keywords. " +
            (v.notes || "").slice(0, 150) +
            ((v.notes || "").length > 150 ? "…" : "");
          const trends = Array.isArray(v?.trends) ? v.trends : [];
          const nulls = trends.reduce(
            (a, t) => a + (Array.isArray(t?.sources) ? t.sources.filter((s) => !s?.engagement).length : 0),
            0,
          );
          chips = [
            chip(trends.map((t) => t?.momentum || "").filter(Boolean).join(" · ") || "trends"),
            chip(
              nulls ? nulls + " sources: no engagement data" : "engagement retrieved",
              nulls ? WARN : OK,
              nulls ? WARN_SOFT : OK_SOFT,
            ),
          ];
        } else if (cls.type === "draft") {
          const v = cls.value,
            p = v?.posts?.[0];
          const claims = Array.isArray(p?.claims) ? p.claims : [];
          summary =
            "Pitch — “" + (p?.hook || "") + "…” on " + (p?.platform || "") + ", template " + (p?.template || "") + ".";
          chips = [
            chip(v?.arc || "", arcHue(v?.arc || ""), tint(arcHue(v?.arc || ""), "18")),
            chip(claims.length + " claims"),
            chip("tiers " + claims.map((c: any) => c?.tier || "").join("")),
          ];
        } else if (cls.type === "ruling") {
          const v = cls.value;
          const scoresList = Array.isArray(v?.scores) ? v.scores : [];
          const winScore = v?.winner ? scoresList.find((s) => s.arc === v.winner?.arc) : null;
          summary =
            v.verdict === "reject_all"
              ? "Ruling — reject_all. Nothing cleared the threshold of 70."
              : "Ruling — ship. Winner: " +
                (v.winner ? v.winner.arc : "") +
                (winScore ? " at " + winScore.total + "/100." : ".");
          chips = scoresList.map((s) =>
            chip(
              s.arc + " " + s.total,
              s.total >= 70 ? OK : BAD,
              s.total >= 70 ? OK_SOFT : BAD_SOFT,
            ),
          );
        } else if (cls.type === "gate") {
          const checks = Array.isArray(cls.value?.checks) ? cls.value.checks : [];
          const violations = Array.isArray(cls.value?.violations) ? cls.value.violations : [];
          summary =
            "Compliance gate — " +
            (cls.value?.gate || "") +
            ", " +
            violations.length +
            " violations across " +
            checks.length +
            " checks.";
          chips = checks.map((c: any) => chip(c));
        } else if (cls.type === "json") summary = "Payload";

        return {
          id: m.id,
          agentLabel: agent,
          hue: agentHue(agent),
          local: local(m.created_at),
          utc: utc(m.created_at),
          kindLabel: {
            prose: "message",
            error: "error",
            research: "research",
            draft: "pitch",
            ruling: "ruling",
            gate: "gate",
            broken: "malformed",
            json: "payload",
          }[cls.type],
          hasParent: !!parent,
          parentAgent,
          parentHue: parentAgent ? agentHue(parentAgent) : MUTED,
          parentSnippet,
          railColor: isStrat && base.showRail ? agentHue(agent) : "#F4F4F4",
          railWidth: isStrat && base.showRail ? "3px" : "2px",
          isProse: cls.type === "prose" || cls.type === "error",
          isPayload: ["research", "draft", "ruling", "gate", "json"].includes(cls.type),
          parseFailed: cls.type === "broken",
          parseError: cls.type === "broken" ? cls.error : "",
          raw: m.content,
          body: long && !open ? full.slice(0, 560).trimEnd() + "…" : full,
          summary,
          chips,
          canExpand: long,
          toggle: () => toggleExpanded(m.id),
          toggleLabel: open ? "Collapse" : "Expand · " + int(full.length) + " chars",
        };
      });
    };
    const messages = buildMessages(run);

    /* ------------------------------------------------------------------- live */
    const liveRun =
      runs().find((r) => r.key === liveKey) ||
      runs().find((r) => r.outcome === "running") ||
      runs()[0] ||
      dummyRun;
    const liveCr = crossReplies(liveRun, agentOf);
    const liveOm = outcomeMeta(liveRun);
    const liveStage = (liveRun.stages || [])
      .filter((s) => s.status === "active" || s.status === "done")
      .slice(-1)[0];
    const liveLast = liveRun.messages && liveRun.messages.length > 0 ? liveRun.messages[liveRun.messages.length - 1] : null;
    const live = {
      label: liveRun.label,
      outcomeLabel: liveOm.label,
      outcomePill: pill(liveOm.color, liveOm.soft, { size: "13px", pad: "5px 14px" }),
      isRunning: liveRun.outcome === "running",
      stageLabel: liveStage ? liveStage.label : "—",
      stageNote:
        liveRun.outcome === "running"
          ? "Stage has been open " +
            dur(nowSec - (liveStage ? (liveStage.started ?? 0) : 0)) +
            (liveLast?.created_at ? ". Last message " + dur(nowSec - liveLast.created_at) + " ago." : ".")
          : "This lifecycle is closed — you are reading the recorded thread, not a live one.",
      quietNote:
        liveRun.outcome === "running" && liveLast?.created_at && nowSec - liveLast.created_at > 240
          ? "Quiet for " +
            dur(nowSec - liveLast.created_at) +
            ". No error has been logged, so this reads as waiting, not stalled."
          : "",
      hasQuiet: Boolean(liveRun.outcome === "running" && liveLast?.created_at && nowSec - liveLast.created_at > 240),
      verdict: liveCr.n === 0 ? "No cross-examination yet" : "They argued",
      verdictColor: liveCr.n === 0 ? WARN : INK,
      crossReplies: String(liveCr.n),
      pairs: liveCr.pairs + " / 3",
      msgCount: String(liveRun.messages.length),
      messages: buildMessages(liveRun),
      picker: runs().map((r) => ({
        key: r.key,
        label: r.label,
        on: r.key === liveRun.key,
        pick: () => setLiveKey(r.key),
        style: {
          border: "1px solid " + (r.key === liveRun.key ? ACCENT : "#E5E7EB"),
          background: r.key === liveRun.key ? ACCENT_SOFT : "#FFFFFF",
          color: r.key === liveRun.key ? ACCENT_DEEP : INK2,
          borderRadius: "999px",
          padding: "7px 16px",
          fontFamily: MONO,
          fontSize: "12px",
          fontWeight: 600,
          cursor: "pointer",
          whiteSpace: "nowrap",
        } as React.CSSProperties,
      })),
      participants: STRATS.map((id) => {
        const a = d.AGENTS.find((x) => x.id === id);
        const turns = liveRun.messages.filter((m) => agentOf(m) === id).length;
        const replies = liveRun.messages.filter((m) => {
          if (agentOf(m) !== id) return false;
          const pid = parentOf(m);
          if (!pid) return false;
          const p = liveRun.messages.find((x) => x.id === pid);
          return !!p && STRATS.includes(agentOf(p) as (typeof STRATS)[number]) && agentOf(p) !== id;
        }).length;
        const arc = a?.arc || ARC_OF[id] || "risk-relief";
        const arcline = a?.arcline || id;
        return {
          id,
          hue: arcHue(arc),
          arcline,
          turns: String(turns),
          replies: String(replies),
          barStyle: {
            height: "4px",
            borderRadius: "999px",
            background: arcHue(arc),
            width: Math.min(1, turns / 4) * 100 + "%",
          } as React.CSSProperties,
          state: replies > 0 ? "engaged" : turns > 0 ? "posted only" : "silent",
          stateStyle: pill(
            replies > 0 ? OK : turns > 0 ? WARN : INK3,
            replies > 0 ? OK_SOFT : turns > 0 ? WARN_SOFT : "#F4F4F4",
            { size: "11px", pad: "3px 10px" },
          ),
        };
      }),
    };

    /* -------------------------------------------------------------- run detail */
    const researchVM = (() => {
      const r = run.research;
      if (!r)
        return {
          hasResearch: false,
          trends: [],
          keywords: [],
          competitors: [],
          hasCompetitors: false,
          researchNotes: "",
          researchNoteLabel: "",
          researchNoteColor: "",
          researchNoteBg: "",
          researchNoteChip: {} as React.CSSProperties,
        };
      const srcs = r.trends.reduce(
        (a, t) => a.concat(t.sources),
        [] as (typeof r.trends)[number]["sources"],
      );
      const nulls = srcs.filter((s) => !s.engagement).length;
      const blind = nulls === srcs.length;
      const tone = blind
        ? { c: BAD, bg: BAD_SOFT, text: "#8B2E30", l: "Research was blind" }
        : nulls
          ? {
              c: WARN,
              bg: WARN_SOFT,
              text: "#8C0043",
              l: nulls + " of " + srcs.length + " sources: no data",
            }
          : { c: OK, bg: OK_SOFT, text: "#155F64", l: "Engagement retrieved" };
      return {
        hasResearch: true,
        researchNotes: r.notes,
        researchNoteLabel: tone.l,
        researchNoteColor: tone.text,
        researchNoteBg: tone.bg,
        researchNoteChip: pill("#FFFFFF", tone.c, { size: "10px" }),
        keywords: r.keywords,
        hasCompetitors: r.competitor_content.length > 0,
        competitors: r.competitor_content,
        trends: r.trends.map((t) => {
          const mc =
            ({ rising: OK, peaked: WARN, dead: BAD, evergreen: INK2 } as Record<string, string>)[
              t.momentum
            ] || INK2;
          const mbg =
            (
              {
                rising: OK_SOFT,
                peaked: WARN_SOFT,
                dead: BAD_SOFT,
                evergreen: "#F4F4F4",
              } as Record<string, string>
            )[t.momentum] || "#F4F4F4";
          const unknown = /unknown|unavailable/.test(t.why_it_works.engagement_shape);
          return {
            id: t.id,
            headline: t.headline,
            type: t.type,
            momentum: t.momentum,
            momentumStyle: pill(mc, mbg, { size: "11px", pad: "4px 12px" }),
            window: t.window_hours + "h window",
            hookText: t.why_it_works.hook_text,
            hookCategory: t.why_it_works.hook_category,
            pattern: t.why_it_works.virality_pattern,
            format: t.why_it_works.format,
            engagementShape: t.why_it_works.engagement_shape,
            shapeColor: unknown ? WARN : INK2,
            evidence: t.evidence,
            hooks: t.vanna_hooks.length ? t.vanna_hooks : ["none proposed"],
            stepps: steppsList(t.why_it_works.stepps, 10),
            sources: t.sources.map((s) => ({
              platform: s.platform,
              url: s.url,
              engagementText: s.engagement
                ? int(s.engagement.likes) + " likes · " + int(s.engagement.replies) + " replies"
                : "no data — engagement not retrieved",
              style: s.engagement
                ? ({ color: INK2 } as React.CSSProperties)
                : pill(WARN, WARN_SOFT, { size: "11px", pad: "3px 10px" }),
            })),
          };
        }),
      };
    })();

    const draftsVM = (() => {
      const ruling = rulingOf(run);
      const scores: Record<string, ArcScore> = {};
      if (ruling && Array.isArray(ruling.scores)) ruling.scores.forEach((s) => (scores[s.arc] = s));
      const drafts: {
        arc: string;
        hue: string;
        hook: string;
        meta: string;
        body: string;
        canExpand: boolean;
        toggleLabel: string;
        toggle: () => void;
        claims: { text: string; tier: string; tierStyle: React.CSSProperties; source: string }[];
        stepps: { label: string; v: string; pct: string }[];
        scoreText: string;
        scoreStyle: React.CSSProperties;
        hasKiller: boolean;
        killer: string;
      }[] = [];
      let broken = 0;
      run.messages.forEach((m) => {
        const c = classify(m);
        if (c.type === "broken" && STRATS.includes(agentOf(m) as (typeof STRATS)[number]))
          broken += 1;
        if (c.type !== "draft") return;
        const v = c.value,
          p = v.posts[0];
        const key = "draft:" + v.arc,
          open = !!expanded[key],
          long = p.body.length > 300;
        const sc = scores[v.arc];
        drafts.push({
          arc: v.arc,
          hue: arcHue(v.arc),
          hook: p.hook,
          meta: p.platform + " · " + p.template + " · " + p.persona,
          body: long && !open ? p.body.slice(0, 260).trimEnd() + "…" : p.body,
          canExpand: long,
          toggleLabel: open ? "Collapse" : "Expand full copy",
          toggle: () => toggleExpanded(key),
          claims: p.claims.map((cl) => ({
            text: cl.text,
            tier: cl.tier,
            tierStyle: tierStyle(cl.tier),
            source: cl.source,
          })),
          stepps: steppsList(p.stepps_self_score, 10),
          scoreText: sc ? String(sc.total) : "—",
          scoreStyle: {
            fontFamily: MONO,
            fontSize: "22px",
            lineHeight: "24px",
            fontWeight: 600,
            flex: "0 0 auto",
            fontVariantNumeric: "tabular-nums",
            color: sc ? (sc.total >= 70 ? OK : BAD) : "#BFBFBF",
          } as React.CSSProperties,
          hasKiller: !!sc,
          killer: sc ? sc.killer_issue : "",
        });
      });
      drafts.sort(
        (a, b) =>
          ARC_ORDER.indexOf(a.arc as (typeof ARC_ORDER)[number]) -
          ARC_ORDER.indexOf(b.arc as (typeof ARC_ORDER)[number]),
      );
      let note = ruling
        ? "Scores are the judge's, overlaid after the fact. Ship threshold is 70."
        : "No scores yet — the judge has not ruled.";
      if (broken)
        note =
          broken +
          " pitch could not be parsed and is excluded here; it is shown raw in the debate above. " +
          note;
      return { drafts, draftsNote: note };
    })();

    const rulingVM = (() => {
      const v = rulingOf(run);
      if (!v)
        return {
          hasRuling: false,
          noRuling: true,
          scoreCards: [],
          audit: [],
          noRulingText:
            run.stages.find((s) => s.id === "ruling")?.status === "not_reached"
              ? "The ruling stage has not been reached. Pitches are still arriving; nothing has been scored."
              : "No ruling was posted.",
          verdictLabel: "",
          verdictPill: {} as React.CSSProperties,
          verdictNote: "",
          hasGraft: false,
          graftTook: "",
          graftFrom: "",
          graftWhy: "",
          graftHue: INK2,
          inflationNote: "",
          inflationColor: OK,
          sendBack: "",
        };
      const MAX: Record<string, number> = {
        claim_integrity: 30,
        hook: 15,
        arc_coherence: 20,
        voice: 15,
        trend_fit: 10,
        virality: 10,
      };
      const LAB: Record<string, string> = {
        claim_integrity: "Claim integrity",
        hook: "Hook",
        arc_coherence: "Arc coherence",
        voice: "Voice",
        trend_fit: "Trend fit",
        virality: "Virality",
      };
      const rank: Record<string, number> = { A: 0, B: 1, C: 2 };
      const audit = (Array.isArray(v.claim_audit) ? v.claim_audit : []).map((a, i) => {
        const inflated = rank[a.you_found] > rank[a.strategist_said];
        return {
          key: i,
          claim: a.claim,
          said: a.strategist_said,
          found: a.you_found,
          verified: a.verified_against,
          saidStyle: tierStyle(a.strategist_said),
          foundStyle: tierStyle(a.you_found),
          flag: inflated ? "tier inflation" : "",
          flagColor: BAD,
          rowBg: inflated ? BAD_SOFT : "#FFFFFF",
        };
      });
      const inflations = audit.filter((a) => a.flag).length;
      return {
        hasRuling: true,
        noRuling: false,
        noRulingText: "",
        verdictLabel:
          v.verdict === "ship" ? "Ship" : v.verdict === "reject_all" ? "Reject all" : "Revise",
        verdictPill: pill(
          v.verdict === "ship" ? "#FFFFFF" : "#FFFFFF",
          v.verdict === "ship" ? OK : BAD,
          { size: "16px", pad: "8px 20px" },
        ),
        verdictNote:
          v.verdict === "ship" && v.winner
            ? "Winner: " +
              v.winner.arc +
              " on " +
              v.winner.platform +
              ", " +
              ((Array.isArray(v.scores) && v.scores.find((s) => s.arc === v.winner?.arc)?.total) ?? "") +
              "/100 against a threshold of 70."
            : "Nothing cleared 70. Highest was " +
              (Array.isArray(v.scores) && v.scores.length > 0
                ? Math.max(...v.scores.map((s) => s.total))
                : 0) +
              ".",
        scoreCards: (Array.isArray(v.scores) ? v.scores : [])
          .slice()
          .sort((a, b) => b.total - a.total)
          .map((s) => ({
            arc: s.arc,
            hue: arcHue(s.arc),
            total: String(s.total),
            totalColor: s.total >= 70 ? OK : BAD,
            killer: s.killer_issue,
            bars: Object.keys(MAX).map((k) => ({
              label: LAB[k],
              pct:
                ((s.breakdown as unknown as Record<string, number>)[k] / MAX[k]) * 100 + "%",
              text: (s.breakdown as unknown as Record<string, number>)[k] + "/" + MAX[k],
            })),
          })),
        hasGraft: !!v.graft,
        graftTook: v.graft ? v.graft.took : "",
        graftFrom: v.graft ? v.graft.from : "",
        graftWhy: v.graft ? v.graft.why : "",
        graftHue: v.graft ? arcHue(v.graft.from) : INK2,
        audit,
        inflationNote: inflations
          ? inflations +
            " claim filed at a higher tier than the judge could verify — the pipeline's most dangerous failure mode."
          : "No tier inflation: every claim verified at the tier the strategist filed it under.",
        inflationColor: inflations ? BAD : OK,
        sendBack: v.send_back_notes,
      };
    })();

    const artifactVM = (() => {
      const a = run.artifact;
      if (!a)
        return {
          hasArtifact: false,
          noArtifact: true,
          noArtifactText:
            run.outcome === "died"
              ? "No artifact. The renderer exited before writing a file — pipeline/state/ has nothing for this run."
              : run.outcome === "killed"
                ? "No artifact. The visual stage was never reached, because nothing was approved to render."
                : "No artifact yet. The visual stage has not been reached.",
          artFile: "",
          artSize: "",
          artType: "",
          artRendered: "",
          artHeadline: "",
          artEmphasis: "",
          artSubhead: "",
          artDisclaimer: "",
          artHue: INK2,
        };
      return {
        hasArtifact: true,
        noArtifact: false,
        noArtifactText: "",
        artFile: a.file,
        artSize: a.size,
        artType: a.type,
        artRendered: a.rendered_at,
        artHeadline: a.headline,
        artEmphasis: a.emphasis,
        artSubhead: a.subhead,
        artDisclaimer: a.disclaimer,
        // Ported as-is. The original reads `run.ruling.winner.arc` whenever a
        // ruling exists, which throws for a reject_all ruling (winner: null).
        // Unreachable in this data — a rejected run never has an artifact — so
        // the behaviour is preserved rather than fixed. See the port notes.
        artHue: arcHue(run.ruling?.winner?.arc || run.bucket),
      };
    })();

    const gateVM = (() => {
      const g = run.gate,
        rv = run.review;
      const map: Record<string, { l: string; c: string; s: string }> = {
        awaiting_review: { l: "Awaiting review", c: WARN, s: WARN_SOFT },
        changes_requested: { l: "Changes requested", c: WARN, s: WARN_SOFT },
        approved: { l: "Approved", c: OK, s: OK_SOFT },
        rejected: { l: "Rejected", c: BAD, s: BAD_SOFT },
      };
      const st = rv ? map[rv.status] : null;
      return {
        gateLabel: g ? (g.gate === "pass" ? "Passed" : "Failed") : "Not reached",
        gatePill: g
          ? pill("#FFFFFF", g.gate === "pass" ? OK : BAD, { size: "14px", pad: "6px 16px" })
          : pill(INK3, "#F4F4F4", { size: "14px", pad: "6px 16px" }),
        gateSub: g
          ? g.violations.length + " violations · " + g.checks.length + " checks"
          : "the gate was never called",
        gateChecks: g ? g.checks : [],
        gateNote: g
          ? g.note || "No notes."
          : "Not reached is not the same as passed. Nothing was checked.",
        reviewLabel: st ? st.l : "Not sent",
        reviewPill: st
          ? pill(st.c, st.s, { size: "14px", pad: "6px 16px" })
          : pill(INK3, "#F4F4F4", { size: "14px", pad: "6px 16px" }),
        reviewMeta: rv ? rv.draft_id + " · " + rv.channel : "nothing reached a human",
        reviewReply: rv
          ? rv.reviewer_reply || "No reply yet. Sent " + dur(Date.now() / 1000 - rv.sent_at) + " ago."
          : "—",
        reviewPath: rv ? rv.path : "",
      };
    })();

    const detail = {
      label: run.label,
      headline: headlineOf(run),
      outcomeLabel: om.label,
      outcomePill: pill(om.color, om.soft, { size: "14px", pad: "6px 16px" }),
      outcomeDetail:
        run.outcome === "died"
          ? "The " +
            (run.died ? run.died.stage : "") +
            " stage failed — " +
            (run.died ? run.died.error : "") +
            ". Stages after it were never reached. Everything before it succeeded and is intact below."
          : run.outcome === "killed"
            ? "The judge rejected all three drafts. No visual was rendered and the compliance gate was never called — those stages were not reached, not failed."
            : run.outcome === "running"
              ? "Still running. Last message " +
                dur(nowSec - (run.quiet_since ?? 0)) +
                " ago — quiet, not stalled: no error has been logged and no close message has arrived."
              : "Cleared the compliance gate and was sent to human review. Review state is below.",
      duration: run.ended ? dur(run.ended - run.started) : dur(nowSec - run.started) + " …",
      cost: usd(runCost(run), 4),
      msgCount: String(run.messages.length),
      boundaryNote: run.boundary.note,
      boundaryOpen: run.boundary.open_evidence,
      boundaryClose: run.boundary.close_evidence || "no close message observed",
      stages,
      stageNote:
        "Elapsed per stage is measured between the first and last message attributed to it. " +
        (run.stages.some((s) => s.status === "not_reached")
          ? "Dashed cards were never reached; they did not fail."
          : "All nine stages ran."),
      engagedVerdict,
      engagedDetail,
      engagedColor,
      crossReplies: String(cr.n),
      pairsEngaged: cr.pairs + " / 3",
      graftCount: rulingOf(run)?.graft ? "1" : "0",
      matrixCols,
      matrixRows,
      messages,
      ...researchVM,
      ...draftsVM,
      ...rulingVM,
      ...artifactVM,
      ...gateVM,
    };

    /* ------------------------------------------------------------------ agents */
    const agentRows = d.AGENTS.map((a) => {
      const calls = run.calls.filter((c) => c.agent === a.id);
      const turns = run.messages.filter((m) => agentOf(m) === a.id).length;
      const inTok = calls.reduce((x, c) => x + c.usage.promptTokenCount, 0);
      const cached = calls.reduce((x, c) => x + c.usage.cachedContentTokenCount, 0);
      const out = calls.reduce((x, c) => x + c.usage.candidatesTokenCount, 0);
      const cfg = ({
        connected: { c: OK, s: OK_SOFT },
        thinking: { c: ACCENT, s: ACCENT_SOFT },
        idle: { c: INK3, s: "#F4F4F4" },
        errored: { c: BAD, s: BAD_SOFT },
      } as Record<string, { c: string; s: string }>)[a.status] || { c: OK, s: OK_SOFT };
      return {
        id: a.id,
        role: a.role,
        distinct: a.distinct,
        log: a.log,
        hue: agentHue(a.id),
        hasArc: !!a.arcline,
        arcline: a.arcline || "",
        arcColor: a.arcline ? arcHue(a.arc || "") : INK3,
        statusLabel: a.status,
        statusColor: cfg.c,
        statusPill: pill(cfg.c, cfg.s, { size: "13px", pad: "5px 14px" }),
        working: a.working_on,
        turns: String(turns),
        calls: String(calls.length),
        tokens: int(inTok + out),
        cachedPct: inTok ? Math.round((cached / inTok) * 100) + "%" : "—",
        cost: usd(
          calls.reduce((x, c) => x + c.cost_usd, 0),
          4,
        ),
      };
    });

    /* -------------------------------------------------------------------- cost */
    const allCalls = runs().reduce(
      (a, r) => a.concat(r.calls.map((c) => ({ ...c, run: r.key }))),
      [] as (Run["calls"][number] & { run: string })[],
    );
    const bar = (rows: { label: string; value: number; color?: string }[]) => {
      const max = Math.max.apply(
        null,
        rows.map((r) => r.value).concat([0.000001]),
      );
      return rows.map((r) => ({
        label: r.label,
        cost: usd(r.value, 4),
        pct: (r.value / max) * 100 + "%",
        color: r.color || "#A9A9A9",
      }));
    };
    const costByRun = bar(
      runs().map((r) => ({ label: r.label, value: runCost(r), color: outcomeMeta(r).color })),
    );
    const costByAgent = bar(
      d.AGENTS.map((a) => ({
        label: a.id.replace("strategist-", "s-"),
        color: ARC_OF[a.id] ? arcHue(ARC_OF[a.id]) : "#A9A9A9",
        value: allCalls.filter((c) => c.agent === a.id).reduce((x, c) => x + c.cost_usd, 0),
      })).sort((a, b) => b.value - a.value),
    );
    const costByStage = bar(
      d.STAGE_ORDER.filter((s) => allCalls.some((c) => c.stage === s)).map((s) => ({
        label: s,
        value: allCalls.filter((c) => c.stage === s).reduce((x, c) => x + c.cost_usd, 0),
        color: "#2C2C2C",
      })),
    );

    const cachedTok = allCalls.reduce((a, c) => a + c.usage.cachedContentTokenCount, 0);
    const inTok = allCalls.reduce((a, c) => a + c.usage.promptTokenCount, 0);
    const outTok = allCalls.reduce((a, c) => a + c.usage.candidatesTokenCount, 0);
    const PR: Record<string, { in: number; cached: number; out: number }> = {
      "gemini-2.5-flash": { in: 0.3e-6, cached: 0.075e-6, out: 2.5e-6 },
      "gemini-2.5-pro": { in: 1.25e-6, cached: 0.3125e-6, out: 10e-6 },
    };
    const cachedCost = allCalls.reduce(
      (a, c) => a + c.usage.cachedContentTokenCount * PR[c.model].cached,
      0,
    );
    const freshCost = allCalls.reduce(
      (a, c) =>
        a + (c.usage.promptTokenCount - c.usage.cachedContentTokenCount) * PR[c.model].in,
      0,
    );
    const outCost = allCalls.reduce(
      (a, c) => a + c.usage.candidatesTokenCount * PR[c.model].out,
      0,
    );
    const naive = allCalls.reduce((a, c) => a + c.usage.promptTokenCount * PR[c.model].in, 0);
    const rewrites = allCalls.filter((c) => c.rewritten_from).length;

    /* ------------------------------------------------------------------- posts */
    const allPosts: {
      key: string;
      runKey: string;
      runLabel: string;
      when: string;
      whenUtc: string;
      arc: string;
      hue: string;
      platform: string;
      template: string;
      persona: string;
      hook: string;
      body: string;
      canExpand: boolean;
      expandLabel: string;
      toggle: () => void;
      thread: string[];
      hasThread: boolean;
      threadCount: string;
      isFinal: boolean;
      finalNote: string;
      status: string;
      statusPill: React.CSSProperties;
      note: string;
      score: string;
      scoreColor: string;
      claims: { tier: string; tierStyle: React.CSSProperties; text: string }[];
      visual: string;
      disclaimer: string;
      openRun: () => void;
      _shipped: boolean;
      _killed: boolean;
      _pending: boolean;
      _notSel: boolean;
    }[] = [];
    runs().forEach((r) => {
      const rl = rulingOf(r);
      r.messages.forEach((m) => {
        const c = classify(m);
        if (c.type !== "draft") return;
        const v = c.value,
          p = v.posts[0];
        const sc = (rl && Array.isArray(rl.scores)) ? rl.scores.find((s) => s.arc === v.arc) : null;
        const won = !!(rl && rl.winner && rl.winner.arc === v.arc);
        let status: string, sColor: string, sSoft: string, note: string;
        if (won && r.outcome === "shipped") {
          const rv = r.review;
          status = rv && rv.status === "changes_requested" ? "Changes requested" : "Awaiting review";
          sColor = WARN;
          sSoft = WARN_SOFT;
          note =
            rv && rv.reviewer_reply
              ? rv.reviewer_reply
              : "Sent to the reviewer on telegram. No reply yet.";
        } else if (won && r.outcome === "died") {
          status = "Won, never rendered";
          sColor = NEUTRAL;
          sSoft = "#F4F4F4";
          note = "Cleared the judge, then the visual stage failed. Nothing was sent to a human.";
        } else if (rl && rl.verdict === "reject_all") {
          status = "Killed";
          sColor = BAD;
          sSoft = BAD_SOFT;
          note = sc ? sc.killer_issue : "";
        } else if (rl) {
          status = "Not selected";
          sColor = INK3;
          sSoft = "#F4F4F4";
          note = sc ? sc.killer_issue : "";
        } else {
          status = "Awaiting ruling";
          sColor = ACCENT;
          sSoft = ACCENT_SOFT;
          note = "The judge has not scored this run yet.";
        }
        const key = "post:" + r.key + ":" + v.arc;
        const openBody = !!expanded[key];
        const bodyFull = (won && rl?.winner?.final_body) ? rl.winner.final_body : p.body;
        const thread = (won && rl?.winner?.final_thread) ? rl.winner.final_thread : p.thread;
        allPosts.push({
          key,
          runKey: r.key,
          runLabel: r.label,
          when: localDate(m.created_at),
          whenUtc: utc(m.created_at),
          arc: v.arc,
          hue: arcHue(v.arc),
          platform: p.platform,
          template: p.template,
          persona: p.persona,
          hook: p.hook,
          body: openBody
            ? bodyFull
            : bodyFull.length > 340
              ? bodyFull.slice(0, 300).trimEnd() + "…"
              : bodyFull,
          canExpand: bodyFull.length > 340,
          expandLabel: openBody ? "Collapse" : "Read full post",
          toggle: () => toggleExpanded(key),
          thread,
          hasThread: thread.length > 0,
          threadCount: String(thread.length),
          isFinal: won,
          finalNote: won ? "Judge's final copy, after the graft and send-back edits." : "As pitched.",
          status,
          statusPill: pill(sColor, sSoft, { size: "12px", pad: "5px 14px" }),
          note,
          score: sc ? String(sc.total) : "—",
          scoreColor: sc ? (sc.total >= 70 ? OK : BAD) : "#BFBFBF",
          claims: p.claims.map((cl) => ({
            tier: cl.tier,
            tierStyle: tierStyle(cl.tier),
            text: cl.text,
          })),
          visual: p.visual_brief.type,
          disclaimer: p.visual_brief.disclaimer,
          openRun: () => {
            setView("run");
            setRunKey(r.key);
          },
          _shipped: won && r.outcome === "shipped",
          _killed: !!(rl && rl.verdict === "reject_all"),
          _pending: !rl,
          _notSel: !!(rl && rl.winner && rl.winner.arc !== v.arc),
        });
      });
    });
    allPosts.reverse();
    const pf = postFilter;
    const postFilters = ["All", "Selected", "Not selected", "Killed", "Awaiting ruling"].map(
      (f) => ({
        label: f,
        set: () => setPostFilter(f),
        style: {
          border: "1px solid " + (pf === f ? ACCENT : "#E5E7EB"),
          background: pf === f ? ACCENT_SOFT : "#FFFFFF",
          color: pf === f ? ACCENT_DEEP : INK2,
          borderRadius: "999px",
          padding: "8px 18px",
          fontSize: "13px",
          fontWeight: 600,
          cursor: "pointer",
          whiteSpace: "nowrap",
        } as React.CSSProperties,
      }),
    );
    const postRows = allPosts.filter((p) =>
      pf === "All"
        ? true
        : pf === "Selected"
          ? p._shipped || p.status === "Won, never rendered"
          : pf === "Not selected"
            ? p._notSel
            : pf === "Killed"
              ? p._killed
              : p._pending,
    );
    const postStats = [
      { label: "Posts written", value: String(allPosts.length), color: INK },
      {
        label: "Selected by the judge",
        value: String(
          allPosts.filter((p) => p._shipped || p.status === "Won, never rendered").length,
        ),
        color: OK,
      },
      { label: "With a human now", value: String(allPosts.filter((p) => p._shipped).length), color: WARN },
      { label: "Killed outright", value: String(allPosts.filter((p) => p._killed).length), color: BAD },
      { label: "Published", value: "0", color: INK3 },
    ];

    const STAGE_LABELS: Record<string, string> = {
      kickoff: "Intelligence Scout",
      research: "Opportunity Selector",
      bucket: "GTM Strategist",
      pitches: "Channel Content & Blueprint",
      debate: "Visual & Video Engine",
      ruling: "Reviewer & Learning Gate",
      visual: "Visual Synthesis",
      gate: "Compliance Gate",
      review: "Human Review",
    };

    /* -------------------------------------------------------------- lifecycles */
    const stageMeta = d.STAGE_ORDER.map((id) => {
      const match = runs()[0]?.stages?.find((s) => s.id === id);
      const label = match?.label || STAGE_LABELS[id] || id;
      const here = runs().filter((r) => {
        const reached = (Array.isArray(r.stages) ? r.stages : []).filter(
          (x) => x.status === "active" || x.status === "failed" || x.status === "done",
        );
        const resting = reached[reached.length - 1];
        return resting && resting.id === id;
      });
      return {
        id,
        label,
        chips: here.map((r) => ({
          key: r.key,
          label: r.label,
          style: pill(outcomeMeta(r).color, outcomeMeta(r).soft, { size: "12px", pad: "5px 12px" }),
          open: () => {
            setView("run");
            setRunKey(r.key);
          },
        })),
        empty: here.length === 0,
      };
    });
    const lifecycles = runs().map((r) => {
      const total = (r.ended || nowSec) - r.started;
      return {
        key: r.key,
        label: r.label,
        outcomeLabel: outcomeMeta(r).label,
        outcomeColor: outcomeMeta(r).color,
        outcomePill: pill(outcomeMeta(r).color, outcomeMeta(r).soft, {
          size: "12px",
          pad: "4px 12px",
        }),
        when: localDate(r.started),
        duration: r.ended ? dur(r.ended - r.started) : dur(nowSec - r.started) + " …",
        cost: usd(runCost(r), 4),
        open: () => {
          setView("run");
          setRunKey(r.key);
        },
        watch: () => {
          setView("live");
          setLiveKey(r.key);
        },
        reached:
          r.stages.filter(
            (s) => s.status === "done" || s.status === "active" || s.status === "failed",
          ).length + " / 9 stages",
        segments: r.stages.map((s) => {
          const span =
            s.started && s.ended
              ? s.ended - s.started
              : s.started
                ? Math.max(20, nowSec - s.started)
                : 0;
          const bg =
            s.status === "done"
              ? "#2C2C2C"
              : s.status === "active"
                ? ACCENT
                : s.status === "failed"
                  ? BAD
                  : s.status === "skipped"
                    ? "#DFDFDF"
                    : "transparent";
          return {
            id: s.id,
            title:
              s.label +
              " — " +
              s.status.replace("_", " ") +
              (span ? " · " + dur(span) : ""),
            style: {
              flex: span ? span / total + " 1 0" : "0.6 1 0",
              height: "14px",
              borderRadius: "4px",
              background: bg,
              border: s.status === "not_reached" ? "1px dashed #DFDFDF" : "none",
              boxSizing: "border-box",
              minWidth: "10px",
            } as React.CSSProperties,
          };
        }),
      };
    });

    return {
      ...base,
      pageTitle,
      pageSub,
      runRows,
      d: detail,
      agentRows,
      agentScopeLabel: run.label,
      live,
      postRows,
      postFilters,
      postStats,
      stageMeta,
      lifecycles,
      postCount: String(allPosts.length),
      runsFootnote:
        runs().length +
        " runs derived from " +
        runs().reduce((a, r) => a + r.messages.length, 0) +
        " messages on one channel. No run_id exists in the source data.",
      costByRun,
      costByAgent,
      costByStage,
      costCapLine: "across " + runs().length + " runs and " + allCalls.length + " model calls",
      remainingText: usd(cap - spent, 4),
      ledgerStarted: d.LEDGER_STARTED,
      cachedPct: Math.round((cachedTok / inTok) * 100) + "%",
      cachedTokens: int(cachedTok),
      freshTokens: int(inTok - cachedTok),
      outputTokens: int(outTok),
      cachedCost: usd(cachedCost, 4),
      freshCost: usd(freshCost, 4),
      outputCost: usd(outCost, 4),
      cachedOverstate: usd(naive - (cachedCost + freshCost), 2),
      totalCalls: String(allCalls.length),
      meanCall: usd(spent / allCalls.length, 4),
      rewrites: String(rewrites),
      rewriteNote: rewrites
        ? rewrites +
          " calls carry a rewritten_from field: the requested model (gemini-3.5-flash) does not exist and was silently rewritten to gemini-2.5-flash. Cost is billed at the served model's rate, which is what is shown here."
        : "No model rewrites in this window.",
      endpoints: [
        {
          route: "GET /api/messages?channel=<uuid>&since=<unix>&limit=500",
          why: "Proxies the relay. Returns raw Nostr events unchanged so the client can parse defensively. `since` makes polling cheap.",
        },
        {
          route: "GET /api/identities",
          why: "pubkey → agent name map. Sent once so the client never has to render hex, and never has to guess who spoke.",
        },
        {
          route: "GET /api/spend",
          why: "pipeline/state/spend-ledger.json verbatim, including cap_usd and remaining_usd.",
        },
        {
          route: "GET /api/calls?since=<iso>",
          why: "pipeline/logs/vertex-calls.jsonl parsed to an array. Must keep cachedContentTokenCount and rewritten_from — both change what the numbers mean.",
        },
        {
          route: "GET /api/agents/status",
          why: "Tail of each pipeline/logs/agents/<agent>.log with the last `subscribed`, `agent_returned`, and error line parsed out. Without it, live status is a guess from silence.",
        },
        {
          route: "GET /api/artifacts/<name>.png",
          why: "Serves pipeline/state/*.png. Until it exists the artifact panel can only compose the visual_brief, not show the render.",
        },
        {
          route: "GET /api/review/<draft_id>",
          why: "The drafts|approved|rejected JSON for one draft, with status and the reviewer's reply.",
        },
      ],
      gaps: [
        {
          title: "No run identity",
          body: "The single blocking gap. Runs are inferred from conductor prose. A `run` tag on every event removes the inference entirely.",
        },
        {
          title: "No stage attribution on model calls",
          body: "vertex-calls.jsonl has a timestamp but no stage or agent field. Per-stage and per-agent cost here is joined by timestamp against message order, which breaks whenever two agents call concurrently. Add `agent` and `stage` to each line.",
        },
        {
          title: "No token attribution per message",
          body: "A call cannot be tied to the message it produced. Cost per draft, or the price of one debate reply, is not answerable from the current sources.",
        },
        {
          title: "Engagement is frequently absent",
          body: "The scout records null when a tool is unavailable. That is correct behaviour, and it means trend ranking in those runs rests on post volume alone. Shown as “no data” everywhere, never as zero.",
        },
        {
          title: "No queue or dispatch state",
          body: "There is no way to distinguish an agent that is thinking from one that has not been dispatched. Status comes from log lines, so an idle agent and a hung agent look identical until an error is logged.",
        },
        {
          title: "Reply threading is partial",
          body: "Only some messages carry an `e` tag. A strategist who addresses another by name in prose without a reply tag will not appear as a cross-reply — the debate matrix undercounts rather than guesses.",
        },
      ],
    };
  })();

  return vals;
}

export type MissionVM = ReturnType<typeof useMissionControl>;
