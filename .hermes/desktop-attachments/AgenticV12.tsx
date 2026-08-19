"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import "./agentic-v12.css";

/* =====================================================================
   AGENTIC — round-6 revision of the spotlight.
   - Section headline restored from V5: "Managing a leveraged book is a
     full-time job." ("Agentic by design" dropped).
   - The reference HTML was a DESIGN reference, not a font reference:
     every caption/label/number now uses the site's Plus Jakarta Sans.
     Mono survives ONLY inside real code (editor, JSON, hashes, endpoint).
   - Index numerals restyled (solid gradient, site weight — no outline).
   - Card 01 merges V5's copilot content (1,000 USDC delta-neutral carry,
     1.40 floor) into the phrase→parameter design. Asset: ETH.
   - Card 02 keeps the deck but shows each playbook's V5 steps inside the
     card; the wandering chart dot is gone. XLM appears exactly once
     site-wide (the Blend rate-carry playbook).
   - Card 03 restores V5's who-it's-for framing per rail + the custody/
     session-key line.
   - Card 04 rebuilt closer to V5's layout (identity + dial | behavior
     bars + credit line + x402) on the light reference surface. EVM id.
   - Card 05 asset → SOL; labels de-monoed.
   ===================================================================== */

const prefersReduced = () =>
  typeof window !== "undefined" &&
  typeof window.matchMedia === "function" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const SP_PERIOD = 8200;

const SPOTS: { sub: string; title: string; acc: string }[] = [
  { sub: "Copilot · intent", title: "Intent becomes positions", acc: "#8D61EB" },
  { sub: "Strategy templates", title: "Proven playbooks, ready to run", acc: "#D68A1E" },
  { sub: "MCP · CLI · SDK", title: "Same rails, any interface", acc: "#F0484B" },
  { sub: "Agent Score", title: "We underwrite behavior", acc: "#2B8FE6" },
  { sub: "Risk Guardian", title: "Never get liquidated in your sleep", acc: "#0FB5A6" },
];

/* ============================================================
   01 · INTENT — V5 content in the phrase→parameter design
   ============================================================ */

function IntentCard({ active }: { active: boolean }) {
  const [step, setStep] = useState(0);
  useEffect(() => {
    if (prefersReduced()) { setStep(5); return; }
    if (!active) return;
    setStep(0);
    let s = 0;
    let t: number;
    const adv = () => {
      s += 1;
      if (s > 5) {
        t = window.setTimeout(() => { s = 0; setStep(0); t = window.setTimeout(adv, 800); }, 2600);
        return;
      }
      setStep(s);
      t = window.setTimeout(adv, 1150);
    };
    t = window.setTimeout(adv, 700);
    return () => window.clearTimeout(t);
  }, [active]);

  const on = (n: number) => (step >= n ? " on" : "");
  const settled = step >= 5;

  return (
    <div className="v12sp-cardbody v12in">
      <div className="v12in-head">
        <div>
          <h4 className="v12sp-ch2">Every word becomes <span className="v12sp-chgrad">a parameter.</span></h4>
          <p className="v12sp-clede">Say what you want in plain language — the copilot compiles it into a guarded position and hands it back for approval. Nothing signs without you.</p>
        </div>
        <span className={"v12sp-runchip" + (settled ? " done" : "")}>{settled ? "compiled ✓" : "compiling…"}</span>
      </div>
      <div className="v12in-prog"><span style={{ width: Math.min(100, (step / 5) * 100) + "%" }} /></div>

      <div className="v12in-grid">
        <div className="v12in-left">
          <div className="v12in-sentence">
            Deposit <span className={"v12in-hl v12in-hl-col" + on(1)}>1,000 USDC</span>, run a{" "}
            <span className={"v12in-hl v12in-hl-pos" + on(2)}>delta-neutral ETH carry</span>, keep{" "}
            <span className={"v12in-hl v12in-hl-guard" + on(3)}>health above 1.40</span>.
          </div>

          <div className="v12in-caplabel">Plain language → on-chain intent</div>

          <div className={"v12in-row" + on(1)}>
            <span className="v12in-phrase" style={{ color: "#B97A10" }}>&ldquo;1,000 USDC&rdquo;</span>
            <span className="v12in-arrow">→</span>
            <span><b>Collateral</b> <span className="v12in-det">posted once · backs the whole strategy</span></span>
          </div>
          <div className={"v12in-row" + on(2)}>
            <span className="v12in-phrase" style={{ color: "#703AE6" }}>&ldquo;Δ-neutral ETH carry&rdquo;</span>
            <span className="v12in-arrow">→</span>
            <span><b>Position</b> <span className="v12in-det">borrow $2,000 of ETH · deploy to lending · Δ ≈ 0</span></span>
          </div>
          <div className={"v12in-row v12in-row-last" + on(3)}>
            <span className="v12in-phrase" style={{ color: "#159C93" }}>&ldquo;health above 1.40&rdquo;</span>
            <span className="v12in-arrow">→</span>
            <span><b>Guardrail</b> <span className="v12in-det">floor 1.40 · guardian armed · auto-deleverage</span></span>
          </div>
        </div>

        <div className="v12in-right">
          <div className="v12sp-panelcap">
            <span>Compiled on-chain</span>
            <span className="v12sp-livechip"><i />live</span>
          </div>
          <div className={"v12in-lrow" + on(1)}><span>Collateral</span><b style={{ color: "#B97A10" }}>1,000 USDC</b></div>
          <div className={"v12in-lrow" + on(2)}><span>Borrowed</span><b style={{ color: "#703AE6" }}>$2,000 of ETH</b></div>
          <div className={"v12in-lrow" + on(2)}><span>Position</span><b>Δ-neutral carry</b></div>
          <div className={"v12in-hfrow" + on(4)}>
            <svg viewBox="0 0 120 66" width="82" style={{ overflow: "visible", flex: "none" }} aria-hidden>
              <path d="M12 58 A46 46 0 0 1 108 58" fill="none" stroke="#EAE8E2" strokeWidth="9" strokeLinecap="round" pathLength={100} />
              <path d="M12 58 A46 46 0 0 1 108 58" fill="none" stroke="#22CED9" strokeWidth="9" strokeLinecap="round" pathLength={100}
                strokeDasharray={step >= 4 ? "66 100" : "0 100"} style={{ transition: "stroke-dasharray 1.1s cubic-bezier(.3,0,.2,1)" }} />
            </svg>
            <div>
              <div className="v12in-hfnum">1.43</div>
              <div className="v12in-hfcap">health factor · above your 1.40 floor</div>
            </div>
          </div>
          <div className={"v12in-txrow" + on(4)}>
            <span className="v12in-txdot" style={{ background: settled ? "#159C93" : "#F2B24A" }} />
            <span className="v12in-txhash">tx {settled ? "0x9f4c…a3e2" : "0x……"}</span>
            <span className={"v12in-txstatus" + (settled ? " ok" : "")}>{settled ? "confirmed" : "pending…"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   02 · PLAYBOOK DECK — V5 strategies, steps shown on the card
   ============================================================ */

type Play = {
  key: string; name: string; badge: string; c: string;
  mlabel: string; metric: string; hf: string;
  steps: string[]; series: number[];
};
/* Five desk-grade playbooks — each one a real, coherent multi-leg trade,
   spanning perps, options, tokenized stocks, AI compute, and LP + lending. */
const PLAYS: Play[] = [
  { key: "funding", name: "Funding-Rate Harvest", badge: "Δ-NEUTRAL · PERPS", c: "#32EEE2", mlabel: "Funding capture", metric: "≈ 12%", hf: "2.4",
    steps: ["Buy BTC spot with the credit line", "Short the same size in BTC perps", "Collect funding · rebalance the drift"],
    series: [.3, .33, .36, .39, .42, .46, .5, .55, .6, .65, .7, .76] },
  { key: "volcarry", name: "Delta-Hedged Vol Carry", badge: "OPTIONS", c: "#8D61EB", mlabel: "Premium capture", metric: "θ carry", hf: "2.1",
    steps: ["Sell a 30-day ETH strangle", "Hedge the delta with perps", "Roll or close at 21 days out"],
    series: [.34, .36, .35, .4, .42, .41, .47, .5, .53, .57, .62, .68] },
  { key: "compute", name: "Compute Yield, Hedged", badge: "AI COMPUTE", c: "#F2B24A", mlabel: "GPU-hour income", metric: "real yield", hf: "2.3",
    steps: ["Buy tokenized GPU-hours earning rent", "Short the token leg — stay neutral", "Keep the compute yield, not the beta"],
    series: [.3, .33, .35, .38, .4, .43, .46, .5, .53, .57, .61, .66] },
  { key: "stocks", name: "Tokenized-Stock Basis", badge: "T-STOCKS", c: "#4B8DF8", mlabel: "Basis capture", metric: "≈ 9%", hf: "2.2",
    steps: ["Buy tokenized NVDA spot", "Short the NVDA perp against it", "Capture the basis, immune to direction"],
    series: [.32, .34, .37, .39, .43, .45, .49, .52, .56, .6, .64, .69] },
  { key: "lp", name: "LP + Lending Spread", badge: "LP · LENDING", c: "#FC5457", mlabel: "Net spread", metric: "≈ 11%", hf: "2.5",
    steps: ["Borrow stables at the pool rate", "LP a correlated pair · lend the rest", "Earn fees + supply over the borrow"],
    series: [.3, .32, .35, .37, .41, .44, .48, .51, .55, .59, .64, .7] },
];

function PlayChart({ f }: { f: Play }) {
  const W = 396, H = 108, PT = 14, PB = 12, n = f.series.length;
  const X = (i: number) => (i / (n - 1)) * W;
  const Y = (v: number) => H - PB - v * (H - PT - PB);
  let d = "";
  f.series.forEach((v, i) => { d += (i ? "L" : "M") + X(i).toFixed(1) + "," + Y(v).toFixed(1) + " "; });
  const area = d + "L" + W + "," + (H - PB) + " L0," + (H - PB) + " Z";
  const gid = "v12pg_" + f.key;
  return (
    <svg key={f.key} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ width: "100%", height: H, display: "block" }} aria-hidden>
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={f.c} stopOpacity={0.28} />
          <stop offset="100%" stopColor={f.c} stopOpacity={0} />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gid})`} />
      <path d={d} fill="none" stroke={f.c} strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round"
        pathLength={100} strokeDasharray={100} className="v12dk-draw" />
    </svg>
  );
}

function DeckCard({ active }: { active: boolean }) {
  const [feat, setFeat] = useState(0);
  useEffect(() => {
    if (prefersReduced() || !active) return;
    const id = window.setInterval(() => setFeat((f) => (f + 1) % PLAYS.length), 3800);
    return () => window.clearInterval(id);
  }, [active]);
  const n = PLAYS.length;
  const f = PLAYS[feat];
  const pv = PLAYS[(feat - 1 + n) % n];
  const nx = PLAYS[(feat + 1) % n];

  return (
    <div className="v12sp-cardbody v12dk">
      <div className="v12dk-left">
        <h4 className="v12sp-ch2">Flip through proven playbooks. <span className="v12sp-chgrad">Or write your own.</span></h4>
        <p className="v12sp-clede">Every card is a ready strategy from one unified margin account. The agent runs whichever you pick; the risk engine keeps it alive.</p>
        <div className="v12dk-own">
          <span className="v12dk-ownic" aria-hidden>
            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" /></svg>
          </span>
          <span>
            <span className="v12dk-ownt">Write your own instruction</span>
            <span className="v12dk-owns">Plain words in — a defended position out</span>
          </span>
        </div>
        <div className="v12dk-nav">
          <button type="button" aria-label="Previous playbook" onClick={() => setFeat((feat - 1 + n) % n)}>←</button>
          <div className="v12dk-dots">
            {PLAYS.map((pp, i) => (
              <span key={pp.key} className={i === feat ? "on" : ""} style={i === feat ? { background: pp.c } : undefined} />
            ))}
          </div>
          <button type="button" aria-label="Next playbook" onClick={() => setFeat((feat + 1) % n)}>→</button>
        </div>
      </div>

      <div className="v12dk-stage">
        <button type="button" className="v12dk-side v12dk-side-l" style={{ background: `linear-gradient(180deg, ${pv.c}, #703AE6)` }}
          onClick={() => setFeat((feat - 1 + n) % n)} aria-label={"Show " + pv.name}>
          <span>{pv.name}</span>
        </button>
        <button type="button" className="v12dk-side v12dk-side-r" style={{ background: `linear-gradient(180deg, ${nx.c}, #703AE6)` }}
          onClick={() => setFeat((feat + 1) % n)} aria-label={"Show " + nx.name}>
          <span>{nx.name}</span>
        </button>

        <div className="v12dk-feat">
          <div className="v12dk-feathead" style={{ background: `linear-gradient(135deg, ${f.c} 6%, #703AE6 86%)` }}>
            <span className="v12dk-shine" aria-hidden />
            <div className="v12dk-featmeta">
              <span className="v12dk-kicker">Playbook</span>
              <span className="v12dk-badge">{f.badge}</span>
            </div>
            <div className="v12dk-featrow">
              <div className="v12dk-featname">{f.name}</div>
              <div className="v12dk-featmetric">
                <div>{f.metric}</div>
                <span>{f.mlabel}</span>
              </div>
            </div>
          </div>
          <div className="v12dk-chart"><PlayChart f={f} /></div>
          <ol className="v12dk-steps">
            {f.steps.map((st, si) => (
              <li key={si}><span style={{ background: f.c }}>{si + 1}</span>{st}</li>
            ))}
          </ol>
          <div className="v12dk-featfoot">
            <span className="v12dk-agent">AGENT</span>
            <span className="v12dk-step">runs it end-to-end under your policy</span>
            <span className="v12dk-hf">HF {f.hf}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   03 · RAILS — V5's who-it's-for framing + custody line
   ============================================================ */

const RAIL_TABS = ["MCP", "CLI", "SDK"] as const;
const RAIL_FILES = ["agent.mcp.json", "run.sh", "strategy.ts"];
const RAIL_COLORS = ["#703AE6", "#FC5457", "#1AA39A"];
const RAIL_WHO = [
  "For agents — Vanna becomes typed, policy-bounded tools they can call.",
  "For developers & power users — script it, cron it, automate it.",
  "For businesses & institutions — embed credit inside your own product.",
];

function RailsCard({ active }: { active: boolean }) {
  const [ri, setRi] = useState(0);
  useEffect(() => {
    if (prefersReduced() || !active) return;
    const id = window.setInterval(() => setRi((r) => (r + 1) % 3), 2800);
    return () => window.clearInterval(id);
  }, [active]);

  return (
    <div className="v12sp-cardbody v12rl">
      <div className="v12rl-head">
        <h4 className="v12sp-ch2">However it&rsquo;s written, <span className="v12sp-chgrad">it hits the same rails.</span></h4>
        <p className="v12sp-clede">One <b>open_position</b> call, three front doors — one unified account and risk engine behind all of them.</p>
      </div>

      <div className="v12rl-tabrow">
        <div className="v12rl-tabs" aria-label="Interface">
          {RAIL_TABS.map((t, k) => (
            <button key={t} type="button" aria-pressed={ri === k}
              className={"v12rl-tab" + (ri === k ? " on" : "")}
              style={ri === k ? { background: RAIL_COLORS[k], borderColor: RAIL_COLORS[k] } : undefined}
              onClick={() => setRi(k)}>
              {t}
            </button>
          ))}
        </div>
        <span className="v12rl-who" style={{ color: RAIL_COLORS[ri] }}>{RAIL_WHO[ri]}</span>
      </div>

      <div className="v12rl-grid">
        <div className="v12rl-code">
          <div className="v12rl-codebar">
            <span className="d r" /><span className="d y" /><span className="d g" />
            <span className="v12rl-file">{RAIL_FILES[ri]}</span>
          </div>
          <div className="v12rl-codestack">
            <pre className={"v12rl-pre" + (ri === 0 ? " on" : "")}>
              <span className="c">{"// register the server once"}</span>{"\n"}
              <span className="k">&quot;vanna&quot;</span>: {"{ "}<span className="k">&quot;url&quot;</span>: <span className="s">&quot;mcp.vanna.finance&quot;</span>{" }"}{"\n\n"}
              <span className="c">{"// the agent calls a typed tool"}</span>{"\n"}
              <span className="v">vanna</span>.<span className="f">open_position</span>({"{"}{"\n"}
              {"  "}<span className="k">strategy</span>: <span className="s">&quot;dn-carry&quot;</span>, <span className="k">floor</span>: <span className="n">1.40</span>{"\n"}
              {"}"})
            </pre>
            <pre className={"v12rl-pre" + (ri === 1 ? " on" : "")}>
              <span className="c"># one command, policy-bound</span>{"\n"}
              <span className="s">$</span> vanna open-position \{"\n"}
              {"    "}<span className="v">--strategy</span> dn-carry \{"\n"}
              {"    "}<span className="v">--collateral</span> <span className="n">1000usdc</span> \{"\n"}
              {"    "}<span className="v">--floor</span> <span className="n">1.40</span>{"\n\n"}
              <span className="c">→ tx 4f2a…c91 · settled ✓ · fee $0.004</span>
            </pre>
            <pre className={"v12rl-pre" + (ri === 2 ? " on" : "")}>
              <span className="c">{"// TypeScript SDK"}</span>{"\n"}
              <span className="f">import</span> {"{ Vanna }"} <span className="f">from</span> <span className="s">&quot;@vanna/sdk&quot;</span>;{"\n\n"}
              <span className="f">const</span> <span className="v">v</span> = <span className="f">new</span> <span className="f">Vanna</span>({"{ session }"});{"\n"}
              <span className="f">await</span> <span className="v">v</span>.<span className="f">openPosition</span>({"{"}{"\n"}
              {"  "}<span className="k">strategy</span>: <span className="s">&quot;dn-carry&quot;</span>, <span className="k">floor</span>: <span className="n">1.40</span>{"\n"}
              {"}"});
            </pre>
          </div>
        </div>

        <div className="v12rl-resp">
          <div className="v12sp-panelcap">
            <span>Response</span>
            <span className="v12sp-livechip"><i />same account</span>
          </div>
          <pre className="v12rl-json">{"{"}{"\n"}  <span className="k">status</span>: <span className="g">&quot;open&quot;</span>,{"\n"}  <span className="k">health_factor</span>: <span className="a">1.43</span>,{"\n"}  <span className="k">collateral</span>: <span className="g">&quot;1,000 USDC&quot;</span>,{"\n"}  <span className="k">borrowed</span>:   <span className="g">&quot;$2,000 of ETH&quot;</span>,{"\n"}  <span className="k">tx</span>: <span className="g">&quot;0x9f4c…a3e2&quot;</span>{"\n"}{"}"}</pre>
          <div className="v12rl-respfoot">Same account, risk engine &amp; guardrails — <b>whichever way you call it.</b></div>
        </div>
      </div>

      {/* the V5 tool registry — what the same rail exposes */}
      <div className="v12rl-reg">
        <div className="v12rl-regcol">
          <span className="v12rl-reghead teal">READ</span>
          <span>get_account_state · estimate_capacity · simulate_position</span>
        </div>
        <div className="v12rl-regcol">
          <span className="v12rl-reghead violet">WRITE</span>
          <span>open_position · repay_debt · rebalance</span>
        </div>
        <div className="v12rl-regcol">
          <span className="v12rl-reghead rose">RISK</span>
          <span>protect_position · get_risk_alerts</span>
        </div>
      </div>
      <p className="v12rl-custody">Scoped session keys · Vanna never holds custody · the guardian runs beneath all three.</p>
    </div>
  );
}

/* ============================================================
   04 · AGENT SCORE — V5 layout on the light surface
   ============================================================ */

const SIGNALS: { name: string; val: string; strong?: boolean; pct: number }[] = [
  { name: "Repayment record", val: "100% on time", strong: true, pct: 100 },
  { name: "Liquidations avoided", val: "47 saves", strong: true, pct: 94 },
  { name: "Health-factor discipline", val: "1.8 avg · never < 1.4", pct: 82 },
  { name: "Account age · volume", val: "214d · $1.2M", pct: 66 },
];

function ScoreCard({ active }: { active: boolean }) {
  const [filled, setFilled] = useState(false);
  const [score, setScore] = useState(0);
  const [mult, setMult] = useState(1.0);
  const timers = useRef<number[]>([]);

  useEffect(() => {
    if (prefersReduced()) { setFilled(true); setScore(742); setMult(7.0); return; }
    if (!active) return;
    let iv = 0;
    const cycle = () => {
      timers.current.length = 0;
      setFilled(false); setScore(0); setMult(1.0);
      timers.current.push(window.setTimeout(() => {
        setFilled(true);
        const t0 = performance.now();
        iv = window.setInterval(() => {
          const p = Math.min(1, (performance.now() - t0) / 1500);
          const e = 1 - Math.pow(1 - p, 3);
          setScore(Math.round(742 * e));
          setMult(Math.round((1 + 6 * e) * 10) / 10);
          if (p >= 1) { window.clearInterval(iv); timers.current.push(window.setTimeout(cycle, 3400)); }
        }, 40);
      }, 480));
    };
    cycle();
    const saved = timers.current;
    return () => { saved.forEach(window.clearTimeout); window.clearInterval(iv); };
  }, [active]);

  const CIRC = 100;
  const ring = filled ? Math.round((742 / 850) * 100) : 0;

  return (
    <div className="v12sp-cardbody v12sc">
      <div className="v12sc-head">
        <h4 className="v12sp-ch2">We underwrite <span className="v12sp-chgrad">behavior, not promises.</span></h4>
        <p className="v12sp-clede">Every guarded action leaves an on-chain trail. Vanna reads it, scores it, and turns it into an undercollateralized credit line.</p>
      </div>

      <div className="v12sc-grid">
        {/* identity + dial */}
        <div className="v12sc-id">
          <div className="v12sc-idrow">
            <span className="v12sc-avatar">◎</span>
            <span>
              <span className="v12sc-addr">0x7a2f…c4e9</span>
              <span className="v12sc-sub">autonomous · treasury agent</span>
            </span>
          </div>
          <div className="v12sc-ring">
            <svg viewBox="0 0 150 150" width="150" height="150" style={{ transform: "rotate(-90deg)" }} aria-label={"Agent score " + score + " of 850"}>
              <circle cx="75" cy="75" r="64" fill="none" stroke="#ECE7F7" strokeWidth="11" />
              <circle cx="75" cy="75" r="64" fill="none" stroke="url(#v12sc-g)" strokeWidth="11" strokeLinecap="round"
                pathLength={CIRC} strokeDasharray={`${ring} ${CIRC}`} style={{ transition: "stroke-dasharray 1.3s cubic-bezier(.3,0,.2,1)" }} />
              <defs>
                <linearGradient id="v12sc-g" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stopColor="#FC5457" /><stop offset="1" stopColor="#703AE6" />
                </linearGradient>
              </defs>
            </svg>
            <div className="v12sc-ringtxt">
              <b>{score}</b>
              <span>/ 850 · score</span>
            </div>
          </div>
          <div className={"v12sc-tier" + (filled ? " on" : "")}>Tier 4 · Established</div>
        </div>

        {/* behavior + credit line */}
        <div className="v12sc-right">
          <div className="v12sc-cap">How it has behaved · on-chain</div>
          {SIGNALS.map((sg, k) => (
            <div className="v12sc-sig" key={sg.name}>
              <div className="v12sc-sigrow">
                <span>{sg.name}</span>
                <span className={"v12sc-sigval" + (sg.strong ? " strong" : "")}>{sg.val}</span>
              </div>
              <div className="v12sc-bar">
                <span style={{ width: (filled ? sg.pct : 0) + "%", transitionDelay: k * 0.08 + "s" }} />
              </div>
            </div>
          ))}

          <div className="v12sc-line">
            <span className="v12sc-line-note">The steadier the record, the deeper the line — climbing toward <b>10×</b>.</span>
            <span className="v12sc-mult">{mult.toFixed(1)}×</span>
          </div>
          <div className="v12sc-x402">
            Any business can pull the score over <b>x402</b> before it extends trust —{" "}
            <span className="v12sc-endpoint">GET /agent-score/0x7a2f…c4e9</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   05 · RISK GUARDIAN — SOL overnight story
   ============================================================ */

const G_LINE = "M8,60 L120,70 L200,102 L252,142 L296,118 L356,100 L430,92 L512,90";

function GuardianCard({ active }: { active: boolean }) {
  const [gs, setGs] = useState(0);
  useEffect(() => {
    if (prefersReduced()) { setGs(3); return; }
    if (!active) return;
    setGs(0);
    let s = 0;
    let t: number;
    const adv = () => {
      s += 1;
      if (s > 3) {
        t = window.setTimeout(() => { s = 0; setGs(0); t = window.setTimeout(adv, 1100); }, 3000);
        return;
      }
      setGs(s);
      t = window.setTimeout(adv, 1250);
    };
    t = window.setTimeout(adv, 700);
    return () => window.clearTimeout(t);
  }, [active]);

  const on = (n: number) => (gs >= n ? " on" : "");
  const drawOff = Math.round(((3 - gs) / 3) * 100);

  return (
    <div className="v12sp-cardbody v12gd">
      <div className="v12gd-head">
        <h4 className="v12sp-ch2">Never get liquidated <span className="v12sp-chgrad">in your sleep.</span></h4>
        <p className="v12sp-clede">One night SOL dropped 12% at 03:14. The guardian&rsquo;s log on the left, your health factor on the right — it never touched the red.</p>
      </div>

      <div className="v12gd-grid">
        <div className="v12gd-log">
          <div className="v12sp-panelcap"><span>While you were asleep</span><span className="v12sp-livechip"><i />watching 24/7</span></div>
          <div className={"v12gd-ev" + on(1)}>
            <span className="v12gd-time">03:14</span>
            <span className="v12gd-dot warn" />
            <span className="v12gd-evtxt"><b>SOL dropped 12%.</b> <span className="v12gd-red">Health 2.4 → 1.3</span></span>
          </div>
          <div className={"v12gd-ev" + on(2)}>
            <span className="v12gd-time">03:14</span>
            <span className="v12gd-dot act" />
            <span className="v12gd-evtxt"><b>Guardian stepped in.</b> Trimmed leverage, topped up collateral.</span>
          </div>
          <div className={"v12gd-ev last" + on(3)}>
            <span className="v12gd-time">03:15</span>
            <span className="v12gd-dot ok" />
            <span className="v12gd-evtxt"><b>Position secured.</b> <span className="v12gd-green">Back to 2.1 — you stayed in.</span></span>
          </div>
          <div className="v12gd-stats">
            <div><span className="v12gd-statk">Lowest HF</span><b style={{ color: "#B97A10" }}>1.3</b></div>
            <div><span className="v12gd-statk">Liquidation at</span><b style={{ color: "#E0484B" }}>1.10</b></div>
            <div><span className="v12gd-statk">Recovered to</span><b style={{ color: "#159C93" }}>2.1</b></div>
          </div>
        </div>

        <div className="v12gd-chart">
          <div className="v12gd-charttitle">It caught the dip you slept through.</div>
          <div className="v12gd-chartmeta">
            <span>Health factor · overnight</span>
            <span>00:00 – 06:00</span>
          </div>
          <div className="v12gd-plot">
            <svg viewBox="0 0 520 200" preserveAspectRatio="none" style={{ width: "100%", height: "100%", display: "block" }} aria-hidden>
              <defs>
                <linearGradient id="v12gd-fill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22CED9" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#22CED9" stopOpacity={0} />
                </linearGradient>
              </defs>
              <line x1="8" y1="164" x2="512" y2="164" stroke="#F2B9BA" strokeWidth="2" strokeDasharray="5 5" />
              <path d={G_LINE + " L512,190 L8,190 Z"} fill="url(#v12gd-fill)" style={{ transition: "opacity .8s .3s", opacity: gs >= 3 ? 1 : 0 }} />
              <path d={G_LINE} fill="none" stroke="#22CED9" strokeWidth="2.6" strokeLinejoin="round" strokeLinecap="round"
                pathLength={100} strokeDasharray={100} strokeDashoffset={drawOff} style={{ transition: "stroke-dashoffset 1.7s ease-out" }} />
            </svg>
            <div className="v12gd-liqlab">liquidation · 1.10</div>
            <div className={"v12gd-mark" + on(2)}><span /></div>
            <div className={"v12gd-marklab" + on(2)}>guardian acted · 03:14</div>
          </div>
          <div className="v12gd-axis">
            <span>00:00</span><span>02:00</span><span>03:14</span><span>04:00</span><span>06:00</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   MAIN — spotlight shell
   ============================================================ */

const CARD_W = [1040, 1040, 1040, 1040, 1040];

export default function AgenticV12() {
  const [active, setActive] = useState(0);
  const [cycle, setCycle] = useState(0);
  const [scales, setScales] = useState<number[]>([0.9, 0.9, 0.9, 0.9, 0.9]);
  const stageRef = useRef<HTMLDivElement>(null);
  const autoRef = useRef<number>(0);
  const reduced = useRef(false);

  const go = useCallback((i: number) => {
    setActive(((i % SPOTS.length) + SPOTS.length) % SPOTS.length);
    setCycle((c) => c + 1);
    if (!reduced.current) {
      window.clearInterval(autoRef.current);
      autoRef.current = window.setInterval(() => {
        setActive((a) => (a + 1) % SPOTS.length);
        setCycle((c) => c + 1);
      }, SP_PERIOD);
    }
  }, []);

  useEffect(() => {
    reduced.current = prefersReduced();
    if (!reduced.current) {
      autoRef.current = window.setInterval(() => {
        setActive((a) => (a + 1) % SPOTS.length);
        setCycle((c) => c + 1);
      }, SP_PERIOD);
    }
    return () => window.clearInterval(autoRef.current);
  }, []);

  useEffect(() => {
    const measure = () => {
      const stage = stageRef.current;
      if (!stage) return;
      const sw = stage.clientWidth, sh = stage.clientHeight;
      const cards = Array.from(stage.querySelectorAll<HTMLElement>(".v12sp-card"));
      setScales(cards.map((c) => {
        const w = c.offsetWidth || 1040, h = c.offsetHeight || 480;
        return Math.min((sw - 8) / w, (sh - 8) / h, 1.08);
      }));
    };
    const t = window.setTimeout(measure, 350);
    window.addEventListener("resize", measure);
    if (typeof document !== "undefined" && document.fonts?.ready) {
      document.fonts.ready.then(() => measure()).catch(() => {});
    }
    return () => { window.clearTimeout(t); window.removeEventListener("resize", measure); };
  }, []);

  const acc = SPOTS[active].acc;

  return (
    <section id="agents" className="v12-sec v12-glow-dual v12sp-sec">
      <div className="v12-wrap">
        <div className="v12-head v12sp-sechead" data-v12r>
          <h2 className="v12-h2">
            Managing a leveraged book is a full-time job.{" "}
            <span className="v12-gradtext">Vanna&rsquo;s agents make it run itself.</span>
          </h2>
        </div>

        <div className="v12sp" data-v12r>
          <div className="v12sp-top">
            <div className="v12sp-topl">
              <div className="v12sp-num" aria-hidden>{"0" + (active + 1)}</div>
              <div className="v12sp-toplbl">
                <div className="v12sp-sub" style={{ color: acc }}>{SPOTS[active].sub}</div>
                <h3 className="v12sp-title">{SPOTS[active].title}</h3>
              </div>
            </div>
            <span className="v12sp-counter">{"0" + (active + 1)} / 05</span>
          </div>

          <div className="v12sp-stage" ref={stageRef}>
            {[IntentCard, DeckCard, RailsCard, ScoreCard, GuardianCard].map((Comp, i) => (
              <div
                key={i}
                className={"v12sp-layer" + (i === active ? " on" : "")}
                aria-hidden={i !== active}
                /* inert removes hidden layers' buttons from tab order —
                   aria-hidden alone leaves focusable children (a11y violation) */
                ref={(el) => {
                  if (el) {
                    if (i === active) el.removeAttribute("inert");
                    else el.setAttribute("inert", "");
                  }
                }}
              >
                <div className="v12sp-fit" style={{ transform: `translate(-50%,-50%) scale(${scales[i] ?? 0.9})` }}>
                  <div className="v12sp-card" style={{ width: CARD_W[i] }}>
                    <Comp active={i === active} />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="v12sp-nav">
            <button type="button" className="v12sp-arrow" aria-label="Previous capability" onClick={() => go(active - 1)}>
              <svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 6l-6 6 6 6" /></svg>
            </button>
            <div className="v12sp-segs">
              {SPOTS.map((sp, i) => (
                <button
                  key={sp.sub} type="button" className="v12sp-seg"
                  aria-label={"Show " + sp.title}
                  aria-current={i === active}
                  style={{ background: i < active ? sp.acc + "59" : "rgba(255,255,255,.16)" }}
                  onClick={() => go(i)}
                >
                  {i === active && (
                    <span
                      key={cycle}
                      className="v12sp-segfill"
                      style={{ background: sp.acc, animationDuration: SP_PERIOD + "ms" }}
                    />
                  )}
                </button>
              ))}
            </div>
            <button type="button" className="v12sp-arrow" aria-label="Next capability" onClick={() => go(active + 1)}>
              <svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 6l6 6-6 6" /></svg>
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
