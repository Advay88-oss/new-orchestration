# Vanna Content Pipeline

Autonomous social content pipeline: trend research → competing strategist drafts →
editorial judgement → on-brand visual → deterministic compliance gate → human review.

Built 2026-08-07.

## Run it

```
/vanna-content-pipeline
```

The orchestrator skill lives at `.claude/skills/vanna-content-pipeline/SKILL.md`.
It dispatches the agents; it never writes copy itself.

## Agents (`.claude/agents/`)

| Agent | Stage | Job |
|---|---|---|
| `trend-scout` | 1 | Scans X, Reddit, HN, ProductHunt, DefiLlama, Exa in parallel. Scores with STEPPS and the 5 virality patterns. Returns evidence, never copy. |
| `content-strategist` | 3 | Invoked **three times in parallel**, one per narrative arc. They compete rather than converge. |
| `editorial-judge` | 4 | Scores all three out of 100, re-verifies every claim against file 08, ships at ≥70. Default posture is rejection. |
| `visual-creator` | 5 | Renders the winner's visual brief to a 1080×1080 PNG. |

The three arcs come from `files/04-brand-voice-and-message-library.md`, which
requires one arc per asset and forbids mixing:

- **capital-efficiency** — "Your collateral is doing one job. It should be doing six."
- **risk-relief** — "Leverage is easy. Not getting liquidated is the hard part."
- **agentic-credit** — "Agents can pay. Agents can't borrow."

## Scripts

```bash
PY="/c/Users/Advay Anand/.agent-reach-venv/Scripts/python.exe"
export PYTHONIOENCODING=utf-8
```

**`claim_safety_gate.py`** — deterministic compliance gate. Encodes the 14 hard
prohibitions, the Tier F poison list and the voice prohibitions. Exit 0 = pass,
1 = blocked. A blocked draft goes back to the strategist and never reaches a human.

```bash
"$PY" scripts/claim_safety_gate.py --text "post copy"
"$PY" scripts/claim_safety_gate.py --file draft.json
```

**`render_visual.py`** — JSON brief → 1080×1080 PNG via headless Chrome. Three
types: `infographic`, `stat-card`, `quote-card`. Optional AI background texture.

```bash
"$PY" scripts/render_visual.py brief.json -o card.png
```

**`telegram_review.py`** — sends the draft to Advay (chat `5501720892`) via
@vanna0bot and waits for a reply. `ok` approves, `no` rejects, anything else is
revision notes.

```bash
"$PY" scripts/telegram_review.py send --draft draft.json --image card.png
"$PY" scripts/telegram_review.py poll --draft-id <id> --timeout 3600
```

## Visual approach — and why

AI image generation never touches anything that must be read. This was tested,
not assumed: asked for a Vanna card with a specific headline and hex value, FLUX
returned a photorealistic portrait with illegible pseudo-glyph text. Asked for
pure abstract texture, it returned something usable.

So: **AI makes the wallpaper, CSS makes the poster.** Text, brand colours, layout
and the disclaimer are rendered deterministically from HTML. AI is allowed one
job — an abstract background with no text, objects or people.

The dark social theme was derived from `design references/cl-11` and `cl-16`, which
are HTML renders, not AI output. `design references/theme.md` documents the *light*
app design system; the social variant is dark and had no written spec before this.

## The compliance gate is the load-bearing part

Vanna is pre-mainnet with no published audits. `files/08-facts-ledger-and-claim-safety.md`
opens by warning that the marketing site is a *vision* site and "an agent that treats
depiction as fact will produce false marketing."

Auto-generated content is exactly that risk, at volume. The gate blocks: mainnet-live
implications, TVL, audits, token/airdrop/points (including jokes), demo figures
presented as results, return promises, financial advice, competitor superiority
claims, Tier E internal material, legacy vocabulary, overstated agent autonomy,
regulatory claims, and fabricated customers.

Meme-jacking is where this breaks most easily — trend-riding copy drifts toward hype
register, emoji and exclamation marks, all of which are banned brand-wide.

## State

```
state/trends/    scout output per run
state/drafts/    sent for review, awaiting reply
state/approved/  cleared by Advay — waiting for the dashboard
state/rejected/  killed at review
logs/            per-run stage-by-stage trace
```

## Not wired, deliberately

**Publishing.** The pipeline ends at `state/approved/`. Postiz was researched
(working REST API, `Authorization: <key>`, `POST /upload` then `POST /posts`,
90-100 req/hr) but Advay is building his own dashboard, so scheduling is left out.

## Known constraints

- `agent-reach doctor` gives false negatives and false positives. Trust the actual
  `opencli` command.
- `files/11-competitive-strategy-and-repositioning.md` is referenced by file 10 but
  **does not exist**. Two differentiation claims were retired by events (Morpho
  shipped MCP+CLI so "MCP-native" is table stakes; the Agent Score moat is contested
  by Kojiru, ERC-8004 and Visa TAP) and the strategic response is missing.
- LinkedIn `people-search` / `salesnav-search` burn a monthly Commercial Use Limit.
  `connect`, `safe-send`, `salesnav-message` are writes needing explicit permission.
- Bilibili blocked by risk control. `gh` CLI not authenticated.
