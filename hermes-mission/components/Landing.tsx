"use client";

/**
 * herald — the public front page. The app lives at /app.
 */
import React, { useEffect, useState } from "react";
import { useTheme } from "@/lib/theme";
import { HeraldMark, IconArrowRight, IconCheck, IconClose, IconMoon, IconSun } from "./icons";

const STAGES: { title: string; items: string[] }[] = [
  { title: "Research", items: ["Scout", "Analyst", "Topic picker"] },
  { title: "Strategy", items: ["Strategist", "Creative director"] },
  { title: "Create", items: ["Copywriter", "Poster designer", "Video producer"] },
  { title: "Review", items: ["Creative check", "Fact check", "Review packet"] },
];
const SOURCES: [string, string][] = [["N", "Industry news"], ["X", "Competitors"], ["R", "Communities"], ["D", "Your docs"]];

const AGENTS: { title: string; n: string; line: string; rows: [string, string][] }[] = [
  { title: "Research", n: "01", line: "Finds what’s worth talking about.", rows: [["Scout", "Reads sources"], ["Analyst", "Grades relevance"], ["Topic picker", "Chooses one"]] },
  { title: "Strategy", n: "02", line: "Decides if it’s worth a post at all.", rows: [["Strategist", "Accepts or declines"], ["Creative director", "Sets the look"]] },
  { title: "Create", n: "03", line: "Makes the post and its visuals.", rows: [["Copywriter", "Three channels"], ["Poster designer", "Square image"], ["Video producer", "When asked"]] },
  { title: "Review", n: "04", line: "Checks the work, then hands it to you.", rows: [["Creative check", "Can reject"], ["Fact check", "Can block"], ["Review packet", "To Telegram"], ["Learning", "Gets smarter"]] },
];

const PRINCIPLES: [string, string][] = [
  ["Never posts for you", "There’s no publish button. Nothing goes live unless you post it yourself."],
  ["Never invents numbers", "A figure appears only if one of your sources states it."],
  ["Never swaps your topic", "Ask for a topic and you get that topic — or a clear no."],
  ["Never mixes brands", "Every brand’s knowledge stays its own."],
];

const card: React.CSSProperties = {
  background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 16,
  boxShadow: "0 1px 2px rgba(28,27,25,0.03)",
};
const muted: React.CSSProperties = { color: "var(--vn-ink-muted)" };

function Eyebrow({ children }: { children: React.ReactNode }) {
  return <div style={{ fontSize: 13, fontWeight: 500, color: "var(--vn-accent-ink)", marginBottom: 12 }}>{children}</div>;
}

function Title({ a, b }: { a: string; b: string }) {
  return (
    <h2 className="lp-h2">
      {a} <span style={{ color: "var(--vn-ink-faint)" }}>{b}</span>
    </h2>
  );
}

function Verdicts({ small }: { small?: boolean }) {
  const pad = small ? "4px 10px" : "6px 14px";
  return (
    <div style={{ display: "flex", gap: 6 }}>
      <span className="hd-btn" style={{ padding: pad, fontSize: 12.5, color: "var(--vn-bad)" }}>Kill</span>
      <span className="hd-btn" style={{ padding: pad, fontSize: 12.5 }}>Revise</span>
      <span className="hd-btn hd-btn-dark" style={{ padding: pad, fontSize: 12.5 }}>Approve</span>
    </div>
  );
}

function Pipeline() {
  // The step lights move through the twelve agents, as one run would.
  const flat = STAGES.flatMap((s) => s.items);
  const [step, setStep] = useState(8);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t = setInterval(() => setStep((s) => (s + 1) % (flat.length + 2)), 1400);
    return () => clearInterval(t);
  }, [flat.length]);
  const done = step >= flat.length;
  return (
    <div className="lp-pipe" style={{ ...card, borderRadius: 20, boxShadow: "var(--vn-shadow-lg)", overflow: "hidden" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 20px", borderBottom: "1px solid var(--vn-line)", fontSize: 13 }}>
        <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="hd-dot" style={{ background: "var(--vn-ok)", boxShadow: "0 0 0 3px var(--vn-ok-soft)" }} />
          <span style={muted}>Writing a post for</span> <b style={{ fontWeight: 600 }}>Northwind</b>
        </span>
        <span style={{ ...muted, fontVariantNumeric: "tabular-nums" }}>step {Math.min(step + 1, 12)} of 12</span>
      </div>
      <div className="lp-pipe-grid">
        <div>
          <div className="lp-col-title">Sources</div>
          {SOURCES.map(([k, l]) => (
            <div key={l} className="lp-node" style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 18, height: 18, borderRadius: 5, background: "var(--vn-raised)", fontSize: 10, fontWeight: 600, display: "inline-flex", alignItems: "center", justifyContent: "center" }}>{k}</span>{l}
            </div>
          ))}
        </div>
        {STAGES.map((s) => (
          <div key={s.title}>
            <div className="lp-col-title">{s.title}</div>
            {s.items.map((it) => {
              const i = flat.indexOf(it);
              const state = i < step ? "done" : i === step ? "live" : "todo";
              return (
                <div key={it} className="lp-node" data-state={state}>
                  {state === "done" && <IconCheck size={13} style={{ color: "var(--vn-ok)" }} />}
                  {state === "live" && <span className="hd-dot lp-pulse" style={{ background: "var(--vn-accent)" }} />}
                  {it}
                </div>
              );
            })}
          </div>
        ))}
        <div>
          <div className="lp-col-title">You</div>
          <div style={{ ...card, padding: 12, borderRadius: 12, opacity: done ? 1 : 0.55, transition: "opacity 0.4s ease" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 6 }}>
              <span style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12.5, fontWeight: 600 }}>
                <span style={{ width: 20, height: 20, borderRadius: 999, background: "#2E5E8C", color: "#fff", fontSize: 10, display: "inline-flex", alignItems: "center", justifyContent: "center" }}>N</span>Northwind
              </span>
              <span className="hd-pill" style={{ background: "var(--vn-warn-soft)", color: "var(--vn-warn)", fontSize: 11, padding: "1px 7px" }}>● Ready</span>
            </div>
            <div style={{ fontSize: 12, lineHeight: 1.45, color: "var(--vn-ink-body)", margin: "8px 0" }}>We shipped three things this week. Here’s the one our customers asked for most…</div>
            <div style={{ background: "#16161A", borderRadius: 8, aspectRatio: "1.6", padding: 10, display: "flex", flexDirection: "column", justifyContent: "flex-end", position: "relative" }}>
              <span style={{ position: "absolute", top: 8, right: 8, width: 14, height: 14, borderRadius: 999, background: "#E5D3B3" }} />
              <span style={{ color: "#fff", fontSize: 12.5, fontWeight: 600, lineHeight: 1.2 }}>Launch week, in one post.</span>
            </div>
            <div style={{ marginTop: 10 }}><Verdicts small /></div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function Landing() {
  const [theme, setTheme] = useTheme();
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const read = () => setDark(theme === "dark" || (theme === "system" && mq.matches));
    read();
    mq.addEventListener("change", read);
    return () => mq.removeEventListener("change", read);
  }, [theme]);

  return (
    <div className="lp" style={{ background: "var(--vn-bg)", color: "var(--vn-ink)", minHeight: "100vh" }}>
      <header className="lp-nav">
        <div className="lp-wrap" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: 60 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 36 }}>
            <a href="/" style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--vn-ink)", fontWeight: 600, fontSize: 16 }}>
              <HeraldMark size={22} />Herald
            </a>
            <nav className="lp-links" style={{ display: "flex", gap: 24, fontSize: 13.5 }}>
              {[["Product", "#product"], ["Agents", "#agents"], ["Brands", "#brands"], ["Principles", "#principles"]].map(([l, h]) => (
                <a key={l} href={h} style={{ color: "var(--vn-ink-muted)", fontWeight: 450 }}>{l}</a>
              ))}
            </nav>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <button className="hd-icon-btn" aria-label={dark ? "Light theme" : "Dark theme"} onClick={() => setTheme(dark ? "light" : "dark")}>
              {dark ? <IconSun size={16} /> : <IconMoon size={16} />}
            </button>
            <a className="hd-btn lp-hide-sm" href="/brief" style={{ padding: "6px 12px", fontSize: 13 }}>See a post</a>
            <a className="hd-btn hd-btn-dark" href="/app" style={{ padding: "6px 12px", fontSize: 13 }}>Open app</a>
          </div>
        </div>
      </header>

      <section className="lp-wrap" style={{ textAlign: "center", paddingTop: 72 }}>
        <span className="hd-pill" style={{ border: "1px solid var(--vn-line)", background: "var(--vn-surface)", color: "var(--vn-ink-body)", padding: "4px 12px 4px 4px", fontSize: 12.5 }}>
          <span style={{ background: "var(--vn-accent-soft)", color: "var(--vn-accent-ink)", borderRadius: 999, padding: "1px 8px", fontWeight: 600, fontSize: 11.5 }}>New</span>
          Twelve AI agents, working as one marketing team
        </span>
        <h1 className="lp-h1">Your social team, on autopilot. <span style={{ color: "var(--vn-ink-faint)" }}>Until it matters.</span></h1>
        <p style={{ maxWidth: 560, margin: "0 auto", fontSize: 17, lineHeight: 1.6, ...muted }}>
          Herald researches your market, writes posts for X, LinkedIn and Reddit, designs the visuals and checks every claim — then hands you a finished post to approve.
        </p>
        <div style={{ display: "flex", gap: 10, justifyContent: "center", marginTop: 28, flexWrap: "wrap" }}>
          <a className="hd-btn hd-btn-dark" href="/app" style={{ padding: "10px 18px", fontSize: 14 }}>Start with Herald <IconArrowRight size={15} /></a>
          <a className="hd-btn" href="/brief" style={{ padding: "10px 18px", fontSize: 14 }}>See a finished post</a>
        </div>
      </section>

      <section className="lp-wrap" style={{ paddingTop: 56 }}>
        <Pipeline />
      </section>

      <div className="lp-strip">
        {["X", "LinkedIn", "Reddit", "Telegram", "Notion", "GitHub", "Industry news", "Company blogs"].map((s) => <span key={s}>{s}</span>)}
      </div>

      <section id="product" className="lp-wrap lp-section">
        <Eyebrow>Product</Eyebrow>
        <Title a="Everything a content team does." b="In one quiet loop." />
        <p className="lp-lead">From the first headline to a post ready for your approval, Herald handles the work in between.</p>
        <div className="lp-bento">
          <div className="lp-card" style={{ gridColumn: "span 3" }}>
            <h3>Reads your market</h3>
            <p>News, competitors, communities, your own docs and Notion — gathered into one feed and remembered for your brand.</p>
            <div className="lp-well">
              {[["N", "Industry: demand keeps growing", "4m"], ["X", "Competitor posted a how-it-works thread", "18m"], ["R", "Customers asking the same question", "32m"]].map(([k, l, t]) => (
                <div key={l} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 10px", background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 8, fontSize: 12.5 }}>
                  <span style={{ width: 18, height: 18, borderRadius: 5, background: "var(--vn-raised)", fontSize: 10, fontWeight: 600, display: "inline-flex", alignItems: "center", justifyContent: "center" }}>{k}</span>
                  <span style={{ flex: 1 }}>{l}</span><span style={muted}>{t}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="lp-card" style={{ gridColumn: "span 3" }}>
            <h3>Writes for every channel</h3>
            <p>One idea, written three ways — short for X, considered for LinkedIn, honest for Reddit.</p>
            <div className="lp-well">
              <div style={{ display: "flex", gap: 4, background: "var(--vn-raised)", borderRadius: 8, padding: 3, width: "fit-content" }}>
                {["X", "LinkedIn", "Reddit"].map((c, i) => (
                  <span key={c} style={{ fontSize: 11.5, padding: "3px 10px", borderRadius: 6, background: i === 0 ? "var(--vn-surface)" : "transparent", boxShadow: i === 0 ? "var(--vn-shadow)" : "none" }}>{c}</span>
                ))}
              </div>
              <div style={{ fontSize: 12.5, lineHeight: 1.5, color: "var(--vn-ink-body)", marginTop: 4 }}>We shipped three things this week. Here’s the one our customers asked for most — and why it took us a year to get right. ↓</div>
            </div>
          </div>
          <div className="lp-card" style={{ gridColumn: "span 2" }}>
            <h3>Designs the visuals</h3>
            <p>A clean, on-brand poster for every post. A short video when you ask for one.</p>
            <div style={{ marginTop: "auto", background: "#16161A", borderRadius: 10, aspectRatio: "1.35", padding: 14, display: "flex", alignItems: "flex-end", position: "relative" }}>
              <span style={{ position: "absolute", top: 12, right: 12, width: 18, height: 18, borderRadius: 999, background: "#E5D3B3" }} />
              <span style={{ color: "#fff", fontSize: 14, fontWeight: 600 }}>Launch week, in one post.</span>
            </div>
          </div>
          <div className="lp-card" style={{ gridColumn: "span 2" }}>
            <h3>Checks every claim</h3>
            <p>A separate reviewer matches each claim to your sources. Unsourced numbers never make it through.</p>
            <div className="lp-well" style={{ marginTop: "auto" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5 }}>
                <IconCheck size={14} style={{ color: "var(--vn-ok)" }} /><span style={{ flex: 1 }}>Shipped three features</span><span style={muted}>Changelog</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5 }}>
                <IconClose size={14} style={{ color: "var(--vn-bad)" }} /><span style={{ flex: 1, textDecoration: "line-through", ...muted }}>“2× faster”</span><span style={{ color: "var(--vn-bad)" }}>No source</span>
              </div>
            </div>
          </div>
          <div className="lp-card" style={{ gridColumn: "span 2" }}>
            <h3>Learns what works</h3>
            <p>Your decisions teach it. Once a post is live, it reads the results about 48 hours later.</p>
            <div style={{ marginTop: "auto", display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              {[["1.0", "Approve"], ["0.3", "Revise"], ["0", "Kill"]].map(([v, l]) => (
                <div key={l} style={{ border: "1px solid var(--vn-line)", borderRadius: 10, padding: "10px 12px" }}>
                  <div style={{ fontSize: 18, fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>{v}</div>
                  <div style={{ fontSize: 11.5, ...muted }}>{l}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="lp-card" style={{ gridColumn: "span 4" }}>
            <h3>Runs from one sentence</h3>
            <p>No forms or settings pages. Tell the Assistant how often to research and post, which brand to study, or which campaigns to find.</p>
            <div className="lp-well" style={{ marginTop: "auto" }}>
              <div style={{ alignSelf: "flex-end", background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: "7px 12px", fontSize: 12.5 }}>Research every 5 minutes and post every 20.</div>
              <div style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 12.5 }}>
                <HeraldMark size={18} tone="accent" />Done. I’ll research every 5 minutes and write a new post every 20.
              </div>
            </div>
          </div>
          <div className="lp-card" style={{ gridColumn: "span 2" }}>
            <h3>Approve from anywhere</h3>
            <p>Every finished post also lands in Telegram. Approve, revise or kill from your phone.</p>
            <div className="lp-well" style={{ marginTop: "auto", alignItems: "center" }}><Verdicts /></div>
          </div>
        </div>
      </section>

      <section id="agents" className="lp-band">
        <div className="lp-wrap lp-section">
          <Eyebrow>Agents</Eyebrow>
          <Title a="Twelve specialists." b="None of them grades its own work." />
          <p className="lp-lead">Each agent does one job well. The ones that review are always separate from the ones that create.</p>
          <div className="lp-agents">
            {AGENTS.map((g) => (
              <div key={g.title}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", borderTop: "2px solid var(--vn-ink)", paddingTop: 12 }}>
                  <span style={{ fontWeight: 600, fontSize: 15 }}>{g.title}</span>
                  <span style={{ fontSize: 12, ...muted }}>{g.n}</span>
                </div>
                <div style={{ fontSize: 13, ...muted, margin: "6px 0 14px" }}>{g.line}</div>
                {g.rows.map(([a, b]) => (
                  <div key={a} style={{ display: "flex", justifyContent: "space-between", padding: "9px 12px", marginBottom: 6, background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 9, fontSize: 13 }}>
                    <span style={{ fontWeight: 500 }}>{a}</span><span style={muted}>{b}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="brands" className="lp-wrap lp-section lp-split">
        <div>
          <Eyebrow>Brands</Eyebrow>
          <Title a="One engine." b="Every brand keeps its own memory." />
          <p className="lp-lead">Run several brands from one place. Each has its own sources, profile and voice — and none can read another’s.</p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {[["N", "Northwind", "B2B software · 3 channels", "Autopilot", "#2E5E8C", "ok"], ["A", "Atlas Coffee", "Consumer brand · X and Reddit", "2 to review", "#8A5A2B", "warn"], ["L", "Lumen Health", "Healthcare · LinkedIn only", "Paused", "#2F6B57", "muted"]].map(([k, n, d, s, c, tone]) => (
            <div key={n} style={{ ...card, display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", borderRadius: 12 }}>
              <span style={{ width: 34, height: 34, borderRadius: 9, background: c, color: "#fff", display: "inline-flex", alignItems: "center", justifyContent: "center", fontWeight: 600 }}>{k}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{n}</div>
                <div style={{ fontSize: 12.5, ...muted }}>{d}</div>
              </div>
              <span className="hd-pill" style={{ background: tone === "ok" ? "var(--vn-ok-soft)" : tone === "warn" ? "var(--vn-warn-soft)" : "var(--vn-raised)", color: tone === "ok" ? "var(--vn-ok)" : tone === "warn" ? "var(--vn-warn)" : "var(--vn-ink-muted)" }}>● {s}</span>
            </div>
          ))}
          <a href="/app" style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", borderRadius: 12, border: "1px dashed var(--vn-line-strong)", color: "var(--vn-ink-muted)", fontSize: 14, fontWeight: 450 }}>
            <span style={{ width: 34, height: 34, borderRadius: 9, background: "var(--vn-raised)", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>+</span>Add your brand
          </a>
        </div>
      </section>

      <section id="principles" className="lp-band">
        <div className="lp-wrap lp-section">
          <Eyebrow>Principles</Eyebrow>
          <h2 className="lp-h2">Built so you can trust<br />it with your name.</h2>
          <div className="lp-principles">
            {PRINCIPLES.map(([t, d]) => (
              <div key={t} style={{ padding: "22px 22px 26px" }}>
                <span style={{ width: 26, height: 26, borderRadius: 999, background: "var(--vn-bad-soft)", color: "var(--vn-bad)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}><IconClose size={13} /></span>
                <div style={{ fontWeight: 600, fontSize: 15, margin: "18px 0 6px" }}>{t}</div>
                <div style={{ fontSize: 13.5, lineHeight: 1.55, ...muted }}>{d}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="lp-wrap" style={{ textAlign: "center", padding: "110px 0 120px" }}>
        <h2 className="lp-h2" style={{ fontSize: "clamp(30px, 3vw + 12px, 44px)" }}>Let Herald do the busywork.<br /><span style={{ color: "var(--vn-ink-faint)" }}>Keep the final say.</span></h2>
        <div style={{ display: "flex", gap: 10, justifyContent: "center", marginTop: 28, flexWrap: "wrap" }}>
          <a className="hd-btn hd-btn-dark" href="/app" style={{ padding: "10px 18px", fontSize: 14 }}>Start with Herald <IconArrowRight size={15} /></a>
          <a className="hd-btn" href="/brief" style={{ padding: "10px 18px", fontSize: 14 }}>See a finished post</a>
        </div>
      </section>

      <footer style={{ borderTop: "1px solid var(--vn-line)" }}>
        <div className="lp-wrap" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, padding: "22px 0", flexWrap: "wrap", fontSize: 13 }}>
          <span style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 600 }}><HeraldMark size={18} />Herald</span>
          <span style={muted}>Researches, writes, checks — and waits for you.</span>
        </div>
      </footer>
    </div>
  );
}
