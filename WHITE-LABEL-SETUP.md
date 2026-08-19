# White-label setup — running this pipeline for another company

How to take this system, which is currently wired end to end for **Vanna**, and
stand it up for a different company.

Audited against the code on **2026-08-10**. Every file path and line number
below was verified. Companion documents: [ARCHITECTURE.md](ARCHITECTURE.md) for
how the machinery works, [JOURNEY.md](JOURNEY.md) for why it is shaped this way.

---

## Read this first: the system is not multi-tenant

There is no tenant id anywhere in this codebase. One installation serves one
company. The spend ledger, the content history, the review chat, the Nostr
channel and the draft directories are all singular and unnamespaced.

So "setting it up for another company" means **forking the tree per company**,
not adding a config flag. Two installations, two directories, two spend ledgers,
two Telegram bots.

```
D:\clients\
  acme\          <- full copy of this tree, re-branded
  globex\        <- full copy of this tree, re-branded
```

Making it genuinely multi-tenant from one checkout is a real project, not a
configuration exercise — see §8 for exactly what blocks it.

**Where the work actually is.** The code changes are a couple of hours of
mechanical edits. The knowledge base, the personas and the safety rules are
where the real effort sits, and they cannot be skipped without the pipeline
producing confident, false claims about a company it does not understand. Budget
accordingly: this is a content-strategy job with a small engineering task
attached, not the reverse.

---

## 1. The coupling surface

Everything company-specific in the tree, in ascending order of effort.

| Tier | What | Where | Effort |
|---|---|---|---|
| 1 | Runtime config | `pipeline/config/marketing_config.json` | Minutes |
| 2 | Environment variables | env / `.env` | Minutes |
| 3 | Hardcoded constants | 6 code locations, below | ~1 hour |
| 4 | Brand assets | `render_visual.py`, `state/logo.png` | ~1 hour |
| 5 | Knowledge base + personas | `files/`, `pipeline/buzz-pack/` | **Days** |
| 6 | Safety rules | `claim_safety_gate.py` — 32 rules | **Days, and highest risk** |

Tiers 1–4 make it *run* for another company. Tiers 5–6 make it *safe* for
another company. Shipping after tier 4 means shipping a system that will write
Vanna's arguments with a new logo on them.

---

## 2. Tier 1 — `marketing_config.json`

`pipeline/config/marketing_config.json` is already fully externalised and is the
one file designed to be swapped. Five keys:

| Key | Contains today | Replace with |
|---|---|---|
| `competitors` | 5 objects: `name`, `x_handle`, `specialty` | The new company's real competitors |
| `subreddits` | `defi`, `Stellar`, `ethereum`, `cryptocurrency` | Where the new audience actually is |
| `search_keywords` | 6 phrases, e.g. `agent credit`, `liquidation survival` | The new company's problem language |
| `taxonomy` | 5 objects: `topic`, `angle`, `description` | The new company's content pillars |
| `settings` | scrape limits and depth | Usually unchanged |

**`taxonomy` is load-bearing.** Its `topic` values are the vocabulary the whole
pipeline speaks. The scout is required to return one of them, the conductor
picks from them, `content_history.json` records them, and the anti-repetition
logic rotates through them. Change the topic strings and you must change the
scout's allowed-values list too — see tier 3.

The current five are `capital-efficiency`, `risk-relief`, `agentic-credit`,
`developer-experience`, `ecosystem-news`. Three of those double as the debate
arcs (§5).

---

## 3. Tier 2 — environment variables

| Variable | Default | Set per company |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | none | **Yes** — a separate bot per company |
| `VERTEX_PROJECT` | `sales-agent-504607` | Yes, if billing is separated |
| `VERTEX_CAP_USD` | `10.00` | Yes — per-company budget |
| `VERTEX_PROXY_URL` | `http://127.0.0.1:8900` | **Yes if running two installs at once** — one port each |
| `PYTHONIOENCODING` | none | Always `utf-8` |

**Two installations cannot share a spend proxy port.** Give each company its own
(`8900`, `8901`, …) and set `VERTEX_PROXY_URL` accordingly, or the second one
meters into the first one's ledger.

---

## 4. Tier 3 — hardcoded constants

Six places where company identity is compiled in rather than configured. All
verified present.

| # | File:line | Current value | Notes |
|---|---|---|---|
| 1 | `pipeline/scripts/telegram_review.py:36` | `REVIEWER_CHAT_ID = "5501720892"` | The reviewer's chat. Must change or drafts go to the wrong person |
| 2 | `pipeline/scripts/trendjack_news_orchestrator.py:57` | Vertex URL with `sales-agent-504607` inline | **See the trap below** |
| 3 | `pipeline/scripts/autonomous_orchestrator.py:55` | same URL, same project inline | same trap |
| 4 | `pipeline/scripts/trendjack_news_orchestrator.py:124` | `https://decrypt.co/feed` | Crypto news source. A non-crypto company needs a different feed |
| 5 | `pipeline/scripts/watch_channel.py:25` | `CHANNEL = "31098616-…"` | Buzz channel uuid (Path B only) |
| 6 | `mission-control/app/api/messages/route.ts:48` | same uuid as a fallback | Dashboard |

**The trap at #2 and #3.** `VERTEX_PROJECT` exists as an environment variable and
is read by `run_agents.py:50` and `vertex_spend_proxy.py:44` — but both
orchestrators build the Vertex URL with the project id **written into the
string**. Setting `VERTEX_PROJECT` alone does nothing for the path that actually
runs. Edit the URLs, or thread the variable through them.

**Also change if you altered `taxonomy` topic strings:** the scout prompt in
`trendjack_news_orchestrator.py` (~line 241) lists the five permitted topic
values inline. A mismatch there silently produces runs with an unrecognised
topic.

**And the fourteen route files.** Every route in both dashboards resolves
absolute paths beginning `D:/new orchestration` (see
[ARCHITECTURE.md §8](ARCHITECTURE.md#8-frontend)). Each company copy needs those
paths pointed at its own tree. This is the single largest mechanical cost of a
fork, and fixing it properly — one `PIPELINE_ROOT` env var read in one module —
is worth doing once instead of fourteen times per company.

---

## 5. Tier 4 — brand assets

**Palette.** `pipeline/scripts/render_visual.py:48–57`:

```
violet #703AE6   violet_light #9F7BEE   rose #FF007A   rose_light #FF54A6
red    #FC5457   blue         #32EEE2   gray #A9A9A9   gray_dim     #949494
```

Plus the card background at `:155` (`#0D0616`) and the `ACCENT` subset at `:57`
used for emphasis. Replace all of them together — the accents are chosen against
that dark background and will not survive a light one unaltered.

**Logo.** `render_visual.py:145` base64-inlines `pipeline/state/logo.png` at 44px
height. Drop in the new company's PNG at the same path. If it is missing the
render still succeeds with an empty brand block, so **check the card, do not
trust the exit code**.

**Card geometry** is fixed at 1080×1080 (`:155`, `:234`). Changing it means
changing both the CSS and the Chrome `--window-size`.

**Theme reference.** `design references/theme.md` documents the *light* app
system; the dark social variant exists only in `render_visual.py`. There is no
second spec to update — the renderer is the spec.

---

## 6. Tier 5 — the knowledge base and personas

This is the bulk of the work and it cannot be automated away.

### `files/` — twelve documents

| File | Role | Reusable? |
|---|---|---|
| `00-INDEX.md` | Map | Structure yes, content no |
| `01` identity and positioning | Who the company is | Rewrite |
| `02` product and technical architecture | What it does | Rewrite |
| `03` agentic layer and AI thesis | Domain-specific | Rewrite or delete |
| `04` brand voice and message library | **Defines the narrative arcs** | Rewrite |
| `05` audiences, personas, objections | Who is being spoken to | Rewrite |
| `06` market context and competitive frame | Rewrite |
| `07` knowledge graph | Rewrite |
| `08` **facts ledger and claim safety** | **The tier system is the reusable asset** | See below |
| `09` GTM toolkit and agent operating guide | Structure reusable |
| `10` competitor battlecards | Rewrite |
| `11` competitive strategy and repositioning | Rewrite |

**Keep the shape of `files/08`, replace its contents.** The tier system — Tier A
quotable verbatim, Tier B state carefully, Tier C future tense only — is the
genuinely portable idea in this whole project. Every company has claims it can
make, claims it must qualify, and claims that are roadmap. Sorting them before
any agent writes a word is the mechanism that keeps this pipeline honest.

**The equivalent of "Vanna is on testnet".** Vanna's overriding constraint is
that it has no mainnet, no token, no audit and no TVL, and every safety rule
descends from that. Find the new company's equivalent — pre-revenue, in beta, in
a regulated category, results not yet published, whatever it is — and write it
down before anything else. If a company has no such constraint, say so
explicitly rather than leaving it undefined; the gate needs to know.

### `pipeline/buzz-pack/` — seven personas

Each `agents/*.persona.md` describes a role and a position. The roles are
portable; the positions are not.

- **`conductor`, `trend-scout`, `editorial-judge`, `visual-creator`** — role
  descriptions are broadly company-neutral. Edit references to the company and
  its domain, keep the behaviour. Keep the judge's default posture of rejection;
  that is what stops the pipeline shipping mediocre content.
- **The three strategists carry a named narrative arc each** and are the point of
  the whole design:

  | Persona file | Current arc |
  |---|---|
  | `strategist-capital-efficiency.persona.md` | "Your collateral is doing one job. It should be doing six." |
  | `strategist-risk-relief.persona.md` | "Leverage is easy. Not getting liquidated is hard." |
  | `strategist-agentic-credit.persona.md` | "Agents can pay. Agents can't borrow." |

  Replace with three arcs for the new company that are **genuinely in tension**.
  This is the part most likely to be done badly. Three arcs that all say "we are
  better" produce three versions of the same post and the debate collapses back
  into the monologue problem the architecture was built to solve
  ([JOURNEY.md](JOURNEY.md#three-monologues-not-a-debate)). Good arcs disagree
  about *which problem matters most*, not about who is best.

- **`instructions.md`** is the shared contract every agent gets appended to its
  persona. Update the company name, the claim rules, and the one-arc-per-asset
  requirement.

### `marketing/`

Eleven directories of Vanna research — `seo` (19 files), `strategy` (16),
`reports` (15), `cro` (11), `competitive` (10), `social` (9), `content` (7),
`ads` (5), `analytics`/`brand`/`email` (2 each). None of it transfers. Either
rebuild it for the new company or delete it; leaving it in place means an agent
may cite another company's research as if it were the client's.

---

## 7. Tier 6 — the safety gate

`pipeline/scripts/claim_safety_gate.py` holds **32 rules** across four sets:

| Set | Rules | Portability |
|---|---|---|
| `HARD_PROHIBITIONS` (`:54`) | 13 | Patterns portable, content Vanna-specific (mainnet, token, audit, TVL) |
| `TIER_F` (`:172`) | 8 | Mechanism portable, facts specific |
| `RETIRED` (`:204`) | 6 | **Entirely Vanna-specific** — names Morpho, MCP, agent credit scoring |
| `VOICE` (`:248`) | 5 | Mostly portable — generic hype and hedging patterns |

**The rules are hardcoded Python, not read from `files/08` at runtime.** The
docstring at `:5` says they derive from the facts ledger; that describes their
origin, not a live coupling. Rewriting `files/08` for a new company changes
nothing about what the gate blocks. **You must edit the Python.**

This is the most dangerous step to skip, and skipping it fails in the worst
possible direction: an un-rewritten gate happily passes every false claim about
the new company while blocking innocent mentions of Vanna's old competitors. It
looks like it is working. It is inert.

**A worked warning from this installation.** `R-mcp-differentiator` blocks
superlative framings ("the only protocol with MCP") but passes the bare phrase
"MCP-native" — which is exactly what sits in `files/05` lines 14 and 47, a file
the strategists read as a source. Tested 2026-08-10; see
[ARCHITECTURE.md §4a](ARCHITECTURE.md#4a-the-claim-safety-gate). The lesson for a
new tenant: **write the rule, then write a draft that should trip it and confirm
it does.** A rule that has never blocked anything has never been tested.

```bash
python pipeline/scripts/claim_safety_gate.py --text "a claim that must be blocked" --platform x
```

Exit code 1 and a non-empty `violations` array is a pass for that test. Build a
small suite of these per company — a handful of strings that must block and a
handful that must pass — and run it after every rule edit.

---

## 8. What must never be copied between companies

When forking the tree, delete these from the copy before the first run.

| Path | Why |
|---|---|
| `pipeline/state/content_history.json` | Drives anti-repetition. Carrying it over blacklists hooks the new company never used, and pollutes topic rotation |
| `pipeline/state/drafts/`, `approved/`, `rejected/` | Another company's content |
| `pipeline/state/spend-ledger.json` | Carries spend forward; the new install starts pre-charged |
| `pipeline/keys/agent-keys.json`, `operator-key.json` | **Private keys.** Regenerate with `gen_agent_keys.py` |
| `pipeline/logs/` | Another company's transcripts and call records |
| `pipeline/state/*.png` | Rendered cards |
| `mission-control/lib/fixture.json`, `hermes-mission/lib/mission-data.ts` | Captured demo data containing Vanna copy — 23 and 18 Vanna references respectively |

Reset `content_history.json` to `[]`, not to a deleted file — the orchestrator
refuses to start if it is missing (`trendjack_news_orchestrator.py:191`).

---

## 9. Setup checklist

Work top to bottom. Nothing below the line marked **STOP** should run until
everything above it is done.

**Fork and clean**

- [ ] Copy the tree to a per-company directory
- [ ] Delete everything in §8; reset `content_history.json` to `[]`
- [ ] `python pipeline/scripts/gen_agent_keys.py` for fresh identities

**Config and constants**

- [ ] Rewrite `pipeline/config/marketing_config.json` — all five keys
- [ ] `telegram_review.py:36` → new reviewer chat id
- [ ] New Telegram bot; set `TELEGRAM_BOT_TOKEN`
- [ ] Vertex project id in `trendjack_news_orchestrator.py:57` **and**
      `autonomous_orchestrator.py:55` (env var alone is not enough)
- [ ] `trendjack_news_orchestrator.py:124` → the new company's news feed
- [ ] Scout prompt's permitted topic list (~`:241`) → match the new taxonomy
- [ ] `VERTEX_CAP_USD`, and a distinct `VERTEX_PROXY_URL` port if running
      alongside another install
- [ ] Dashboard route paths → the new tree (14 files, or refactor to one env var)

**Brand**

- [ ] Palette at `render_visual.py:48–57` and background at `:155`
- [ ] `pipeline/state/logo.png`
- [ ] Render one card and **look at it**

**Voice and knowledge**

- [ ] Rewrite `files/01`–`files/07`, `files/09`–`files/11`
- [ ] Rebuild `files/08` with the tier structure and the new company's facts
- [ ] Write down the company's overriding constraint (the "testnet rule")
- [ ] Rewrite the four role personas
- [ ] Write three genuinely opposed narrative arcs; rewrite the three strategists
- [ ] Update `pipeline/buzz-pack/instructions.md`
- [ ] Empty or rebuild `marketing/`

**STOP — do not run a live pipeline until the gate is rewritten.**

**Safety**

- [ ] Rewrite `RETIRED` entirely; rewrite `HARD_PROHIBITIONS` and `TIER_F` around
      the new company's facts; review `VOICE`
- [ ] Write must-block and must-pass test strings and run them
- [ ] Confirm at least one rule actually blocks something

**Verify**

- [ ] Spend proxy answers on its port with a zeroed ledger
- [ ] One full run to Telegram with review, **not** `--auto-approve`
- [ ] Read the draft as an outsider: does any sentence make a claim the company
      cannot support?
- [ ] Confirm the publishing account is the company's, not a personal one —
      `opencli twitter whoami`
- [ ] Only then publish

---

## 10. What blocks real multi-tenancy

If the goal is one installation serving many companies rather than a fork per
company, these are the specific obstacles, roughly in order of cost:

1. **No tenant id in any data structure.** Drafts, history, ledger and logs are
   flat directories with no namespace.
2. **The spend proxy is a single global ledger on a single port**, with the cap
   as a module-level constant.
3. **`REVIEWER_CHAT_ID` is a module constant**, so one bot serves one reviewer.
4. **The gate's rules are code, not data.** Per-tenant rules mean loading rule
   sets from files — which is also the fix for the `files/08` decoupling problem
   described in §7, so it pays for itself twice.
5. **Fourteen dashboard routes hardcode an absolute path**, and the dashboards
   have no concept of selecting a tenant.
6. **One Buzz channel uuid** is hardcoded in `watch_channel.py` and the dashboard
   route (Path B only).

The cheapest meaningful step toward this — and worth doing even if you stay with
forks — is **externalising the gate's rule sets into per-company data files**.
It removes the highest-risk manual step from every new setup and fixes the
gate/ledger decoupling at the same time.

---

## 11. Known-good order of operations

The failure mode to avoid is a technically working pipeline pointed at a company
whose story has not been written. It will produce fluent, on-brand, confidently
wrong content, and the gate will not stop it because the gate still describes
Vanna.

Do the company work first: constraint, facts ledger, three opposed arcs, safety
rules. Then wire the machinery. The machinery is the easy half.
