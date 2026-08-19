# Prompt — "How it works" documentation

Paste everything below the line into a fresh Hermes session opened at
`D:\new orchestration`.

---

Write **`ARCHITECTURE.md`** at the root of `D:\new orchestration`: a complete
technical description of what this project is and how every piece of it works.

The reader is a competent engineer who has never seen this folder. They should
finish able to run the system, change it, and explain it to someone else. They
should not have to open a single source file to understand the shape of it.

## Ground rules — these outrank the section list

1. **Read before you write. Every claim traces to a file you opened.** This
   folder contains prose written at different times, some of it now stale. Where
   a document and the code disagree, the code wins and you say so explicitly in
   the doc.
2. **Never invent a number, a port, a filename, a model id, or a command.** If
   you cannot verify something, write what you checked and mark it
   `UNVERIFIED —` with the reason. A short honest doc beats a padded one.
3. **Vanna is on testnet.** No mainnet, no token, no audit, no TVL. If you
   describe what the pipeline publishes, do not restate product claims as fact —
   describe the *claim-safety machinery* instead, and point at
   `files/08-facts-ledger-and-claim-safety.md` and
   `files/11-competitive-strategy-and-repositioning.md` as the authorities.
4. **Distinguish "built" from "wired" from "proven".** Several parts of this
   system exist, run, and have never completed a full cycle. Do not let a
   working script imply a working pipeline. Use those three words consistently.
5. **Do not redesign anything.** This is documentation, not a review. Where you
   spot a bug, note it in a single "Known defects" section with a file:line and
   move on. No refactor proposals.

## What to read, in this order

Start with the prose, then verify all of it against the code.

**Orientation**
- `HANDOFF.md` — the existing cold-read handoff. Treat it as a *claim set to
  verify*, not as source of truth. Its "Open items" section is important.
- `DASHBOARD-PROMPT.md` — the spec the dashboard was generated from. Tells you
  what the UI was *asked* to be.
- `MAC_MINI_SETUP.md` — the migration guide. Contains the clearest statement of
  the intended production topology, including the **Hermes Multi-Platform
  Gateway** (Telegram + Slack) which does not exist on the Windows box.

**The pipeline (the backend)**
- `pipeline/scripts/` — every `.py` and `.js`. These are the actual machinery.
  There is more than one orchestrator and they are **not** interchangeable:
  `autonomous_orchestrator.py`, `trendjack_news_orchestrator.py`,
  `run_twitter_lifecycle.py`, `run_campaign_lifecycle.py`,
  `run_two_consecutive_runs.py`. Work out what distinguishes each, which is
  current, and which are superseded. Say so plainly.
- `pipeline/buzz-pack/agents/*.persona.md` and `pipeline/buzz-pack/instructions.md`
  — the seven agent identities and the shared contract between them.
- `pipeline/config/marketing_config.json` — competitors and topic taxonomy.
- `pipeline/state/` — drafts, approved, rejected, prompts, trends,
  `content_history.json`, `spend-ledger.json`. Explain what each directory means
  in the run loop and who writes it.
- `pipeline/logs/` — `vertex-calls.jsonl`, `agents/*.log`, gate fixtures.
- `.claude/settings.local.json` — the permission allowlist that bounds what the
  agents may execute. This is a real security boundary; describe it as one.

**The dashboards (the frontend) — there are two, and this trips people up**
- `mission-control/` — Next.js 15, App Router. `lib/data.ts` exports
  `source = 'fixture'` and reads `lib/fixture.json`. Three components. This is
  the earlier, fixture-only build.
- `hermes-mission/` — Next.js 14.2.15, React 18. `lib/api.ts` sets
  `USE_FIXTURE = false` and defines seven read-only routes; eight views under
  `components/views/`. This is the fuller port.
- `hermes-mission/PORT-NOTES.md` — read this in full. Section (c) is an exact
  backend endpoint contract table; reproduce that contract faithfully.
- Both ship `app/api/**/route.ts`. **Diff the two route sets.** Establish which
  app is canonical, which port each runs on, and whether the API routes are
  duplicated or divergent. If you cannot establish which is canonical from the
  code, say that — it is a genuine finding, not a gap in your work.

**Knowledge base and assets** — describe their role, do not summarise their content
- `files/00-INDEX.md` through `files/11-*.md` — brand, product, personas, facts
  ledger, battlecards, positioning. Note that `00-INDEX.md` is the map.
- `marketing/` — eleven subdirectories of research. Give counts and purpose, not
  a chapter each.
- `design references/theme.md` plus the `cl-*.png` cards — the visual source of
  truth. Note which system `theme.md` actually documents.
- `Agent-Reach/` and the OpenCLI toolchain — the research and publishing layer.

## Sections the document must contain

Order them as you see fit, but all of these must be present and answerable.

1. **What this is** — one paragraph, no marketing tone. Then a diagram of the
   run loop from trigger to published post, in a fenced code block.
2. **The seven agents** — table: name, persona file, what it decides, what it
   may never do. Include *why* the three strategists are locked to fixed
   narrative arcs rather than choosing their own.
3. **Runtime and dependency inventory** — every language, framework, service and
   external tool actually used, with the version you observed and where you
   observed it. Cover at minimum: Python and its venv, Node/Next/React,
   Docker Compose services, Postgres, Redis, the Buzz relay, Vertex AI and the
   model id in use, Playwright/headless Chrome, OpenCLI, the Telegram Bot API,
   and `@agentclientprotocol/claude-agent-acp`. Mark anything you could not
   version-check.
4. **Backend, in execution order** — for each stage: which script, what it
   reads, what it writes, what makes it fail, and whether failure is fatal.
   Give the claim-safety gate its own subsection: it is a *blocking* gate and
   the reason the whole design exists.
5. **The spend cap** — `vertex_spend_proxy.py`. Explain why a GCP budget was not
   sufficient, how metering works, where the ledger lives, and what a corrupt
   ledger does. This is load-bearing; do not compress it.
6. **The human review gate** — `telegram_review.py`. Document the send/poll/status
   commands, the reply protocol, where draft state is persisted, and where the
   token is read from. **Never print or reproduce a token.**
7. **Publishing** — the Twitter path via OpenCLI, including which account it is
   authenticated as and what its failure modes look like.
8. **Frontend** — both apps. Data seam, route contracts, view inventory,
   theming, and the run-boundary inference problem (runs are not delimited in
   the data; boundaries are inferred and the UI flags them as such). Explain the
   three display invariants the UI defends: `null` is not `0`, cached input
   tokens are counted separately, and five stage states rather than two.
9. **How to run it, cold** — exact commands in `bash` fenced blocks, one command
   per block, in dependency order, with the check that proves each step worked.
   Include the correct interpreter path and `PYTHONIOENCODING=utf-8`.
10. **Configuration and secrets** — every env var and `.env` location, what reads
    it, and what breaks without it. Values redacted.
11. **Known defects** — file:line, symptom, impact. Include the ones already
    recorded in `HANDOFF.md` "Open items" and `PORT-NOTES.md` section (b), and
    verify each still exists before listing it.
12. **What is not built** — publishing beyond Twitter, the Hermes gateway on
    Windows, live polling, anything else you find stubbed.

## Format

Markdown. Tables where the content is tabular. Fenced `bash` blocks for
commands, one command per block. File references as clickable relative paths
with line numbers where useful (`pipeline/scripts/telegram_review.py:177`).
No emoji. No "Conclusion" section. Aim for completeness over brevity, but every
paragraph must carry information — cut anything that only restates a heading.

When you are done, list separately: every claim in `HANDOFF.md` that you found
to be **stale or wrong**, and every question you could not resolve from the
repository alone.
