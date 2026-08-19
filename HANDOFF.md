# Handoff — Vanna autonomous content pipeline

Paste this whole file as your first message in a fresh agent session opened at
`D:\new orchestration`. It is written to be read cold.

---

## What this project is

An autonomous social-content pipeline for **Vanna**, a composable-credit DeFi
protocol on Stellar Soroban **testnet**. Seven agents research live trends,
debate three competing narrative arcs in the open, judge the drafts
adversarially, render a visual, pass a deterministic compliance gate, and send
the winner to Telegram for human review.

The defining design decision: **the agents talk to each other in a shared
channel.** An earlier version had a coordinator relaying between subagents,
which produced three parallel monologues rather than an argument. They now run
as separate processes with their own identities on a Buzz relay, so a strategist
can read a rival's pitch and answer it by name.

## The one rule that outranks everything

**Vanna is on testnet. There is no mainnet, no token, no audit, no TVL.**

Every product claim must trace to `files/08-facts-ledger-and-claim-safety.md`,
which sorts facts into Tier A (quotable), Tier B (state carefully), Tier C
(future tense only). `files/11-competitive-strategy-and-repositioning.md`
retires claims that used to be safe — read it before writing anything
competitive. Two that catch people out:

- Never lead with "MCP-native". Morpho Agents shipped MCP + CLI on mainnet in
  April 2026.
- Never claim Vanna owns agent credit scoring. Kojiru, ERC-8004, Visa TAP, WEF
  KYA and Agentics Credit are all in that space. The Agent Score stays future
  tense until sybil resistance is designed.

A **known live defect**: `files/05` line 14 still lists "MCP-native" in the
Agents row, contradicting file 11 §10.1. File 11 wins. This was found by the
editorial-judge agent unprompted and verified by hand. It has not been fixed.

## Layout

| Path | What |
|---|---|
| `files/04,05,08,10,11` | brand voice + arcs, personas, facts ledger, battlecards, current positioning |
| `marketing/` | STEPPS/contagious, x-twitter-growth, viral patterns, copywriting |
| `pipeline/buzz-pack/` | the 7 agent personas + shared `instructions.md` |
| `pipeline/scripts/` | the machinery, below |
| `pipeline/keys/` | Nostr keys, gitignored — never print these |
| `pipeline/logs/agents/` | one log per agent |
| `.claude/settings.local.json` | what the agents are permitted to run |
| `D:\buzz` | the Buzz relay checkout (separate repo, block/buzz) |

Scripts:

- `run_agents.py` — starts one `buzz-acp` harness per agent
- `vertex_spend_proxy.py` — the hard dollar cap (see below)
- `claim_safety_gate.py` — blocking compliance gate; exit 1 = draft never reaches a human
- `render_visual.py` — JSON brief → 1080×1080 PNG via headless Chrome
- `telegram_review.py` — sends to chat 5501720892, polls for ok/no/notes
- `watch_channel.py` — read the run transcript with agent names instead of pubkeys
- `gemini_acp_shim.js` — ACP auth shim (see below)
- `gen_agent_keys.py` — one-time key generation

## Bringing it up

```bash
# 1. Docker Desktop must be running first, then:
cd /d/buzz && docker compose up -d

# 2. Relay — note 127.0.0.1, never localhost (see gotchas)
DATABASE_URL="postgres://buzz:buzz_dev@127.0.0.1:5432/buzz?sslmode=disable" \
REDIS_URL="redis://127.0.0.1:6379" BUZZ_BIND_ADDR="0.0.0.0:3000" \
  D:/buzz/target/debug/buzz-relay.exe

# 3. Wait for the WebSocket, not just /health — they come up separately
curl http://127.0.0.1:3000/health

# 4. Spend cap (required for the gemini runtime)
python pipeline/scripts/vertex_spend_proxy.py --port 8900

# 5. Agents
python pipeline/scripts/run_agents.py --runtime claude   # proven path
python pipeline/scripts/run_agents.py --runtime gemini   # see blocker

# 6. Kick off a run by posting to the channel as the operator identity
#    (agents ignore their own messages, so the conductor cannot self-start)
```

Channel: `content-pipeline` = `31098616-3d0b-4202-86b4-96bfd36680cd`

Read a run: `python pipeline/scripts/watch_channel.py --limit 30`

## Spend control — read this before touching Vertex

**GCP budgets are alerts, not caps.** A $10 budget does not stop spend at $10;
it emails you while the meter runs. This is the most likely explanation for an
unexplained $109 GCP bill a few days before 8 Aug 2026. The only native hard
stop is a Cloud Function that detaches the billing account, which on project
`sales-agent-504607` would also kill the sales-agent workload — so that is off
the table.

The cap therefore lives in `vertex_spend_proxy.py`, which sits between the
agents and Vertex:

- meters every call from `usageMetadata` (handles streaming and SSE, not just
  single-object responses — missing this charges a flat pessimistic rate and
  burns the budget ~10× too fast)
- persists to `pipeline/state/spend-ledger.json`, so restarting does not reset
  the budget; a corrupt ledger reads as **exhausted**, never as fresh
- returns HTTP 402 once $10 is reached
- rewrites model ids and strips unsupported fields (below)
- `run_agents.py` refuses to start the gemini runtime if the proxy is down

Check spend: `curl http://127.0.0.1:8900/_spend`
Reset for a new period: `python pipeline/scripts/vertex_spend_proxy.py --reset`

**Verify the prices in `PRICES` against current Vertex rates.** They are set
deliberately high so the cap trips early; a wrong-but-low rate is how surprise
bills happen.

## Runtimes

**Claude (`--runtime claude`) — works, proven end to end.** Uses
`@agentclientprotocol/claude-agent-acp`, authenticated by the Claude Code
subscription, no API key. Verified: an agent woke on an @mention, reasoned from
its persona, and posted its own reply. Limitation: 7 parallel Opus agents
exhausted a subscription session limit in ~28 minutes.

**Gemini (`--runtime gemini`) — auth solved, turn completion unverified.**
Vertex via ADC (already working — `gcloud.cmd` mints tokens fine even though
Git Bash's `gcloud` shim reports a reauth error). Model is `gemini-2.5-flash`:
**`gemini-3.5-flash` does not exist on this project**, nor do 3-flash, 3-pro or
flash-latest — only the 2.5 family answers, probed 8 Aug 2026.

Gemini CLI's `--acp` mode advertises `authMethods` and expects the client to
call `authenticate`; `buzz-acp` has no auth flag and never does, so every turn
died with "Gemini API key is missing or not configured". `gemini_acp_shim.js`
sits between them and performs that handshake, handing buzz-acp an
already-authenticated agent. **Verified working** — buzz-acp now sees
`authMethods: []`.

**Where it stands, unresolved:** with the shim in place the scout connects,
subscribes, and consumes real tokens (3 calls, ~63k input tokens, $0.034
metered, no errors) — but no turn completion was ever logged and it did not
post. Whether the turn is merely slow, or completing without posting, was not
determined. `steering_supported=false` for gemini-cli where Claude reports
true; that difference is unexplored and may matter.

**Next step:** run one Gemini agent, tail its log and
`pipeline/logs/vertex-calls.jsonl` together, and find out whether the turn ends.
If it hangs, compare against a Claude agent doing the same prompt.

## Windows gotchas, all paid for in real time

- **`localhost` resolves to IPv6 `::1`, where `wslrelay.exe` listens — not
  Docker's proxy.** Postgres connections fail with `unexpected response from
  SSLRequest: 0x00`. Use `127.0.0.1` for every service URL.
- **The relay's WebSocket comes up after `/health` does.** Agents started
  immediately get `404 Not Found` on connect. `run_agents.py` staggers starts by
  6s; even so, one or two sometimes need an individual restart.
- **`buzz-acp --agent-args` must use the equals form** (`--agent-args=--acp`).
  A value starting with `--` is otherwise parsed as a buzz-acp flag.
- **`buzz-acp` defaults to `--respond-to owner-only`**, which silently drops
  every event when no owner is set. The agent connects, goes online, and ignores
  everyone. Always pass `--respond-to anyone`.
- **Permission mode `dont-ask` blocks posting** until the tool is allowed in
  `.claude/settings.local.json` and `buzz` is on PATH.
- **Compound commands defeat permission patterns.** The scout wrote
  `export PATH=... && opencli ...`; that does not match `Bash(opencli:*)`, so
  every research call was denied and it fell back to plain web search with no
  engagement data. Tools are now put on PATH by the launcher instead.
- **Spawning `.cmd` shims needs `shell:true`, which mangles the space in
  "Advay Anand".** Spawn `node.exe` on the package's entry `.js` instead.
- **`.env` values containing spaces must be quoted** — several bash scripts
  `source .env` and an unquoted Windows path executes as a command.
- **`scripts/seed-local-community.sh` needs `python3`**, which does not exist
  here. Seed via `docker exec buzz-postgres psql` instead.
- **The full Buzz workspace does not build on Windows** — `sherpa-onnx` fails,
  the `windows` crate crashes rustc with `STATUS_STACK_BUFFER_OVERRUN`, and
  `buzz-test-client` panics the compiler. Build only `buzz-relay`, `buzz-cli`,
  `buzz-agent`, `buzz-dev-mcp`, `buzz-acp`. `CARGO_HOME=D:\cargo-home` and it
  must be a **Windows** path — a Git Bash path like `/d/cargo-home` stalls cargo
  silently with zero output.
- **Never pass `--installation-dir` to the Docker Desktop installer.** It
  extracts files but skips registration, and Docker then dies on launch with
  "cannot find registry key". Docker Desktop 4.85 installs per-user to
  `%LOCALAPPDATA%\Programs\DockerDesktop` with its uninstall entry under HKCU.
- **nvm4w 1.2.2 is broken here** — `nvm use` fails on the space in the profile
  path, and `C:\nvm4w\nodejs` did not exist at all, so PATH silently fell
  through to a stray Node install. Fixed with a junction (`mklink /J`), which
  needs no admin.
- **C: runs chronically full.** ~8 GB is reclaimable via
  `npm cache clean --force`, `yarn cache clean`, `pip cache purge`.

## Open items

1. **Gemini turn completion** — see above. The blocker to a full Gemini cycle.
2. **`files/05` line 14** still carries the retired "MCP-native" claim.
3. **Telegram draft `a4cb2c02`** is `changes_requested`; the reviewer replied
   "send notes", which was never resolved.
4. **Agentics Credit** (Base, 90-day track-record agent credit scoring) trips
   the file 11 §9 watch trigger. The agentic-credit strategist correctly refused
   to adjust positioning on its own authority and escalated. Still open.
5. **A full cycle has never completed.** The Claude run died on a session limit
   after the scout and conductor; the Gemini run has not produced a post. What
   *has* been proven is that agents wake, reason from their personas, research,
   correct each other, and post autonomously.

## How to behave

- **Never invent a number, a source, an engagement count, or a quote.** If a
  tool fails, say it failed. A short honest result beats a padded one.
- **Verify before asserting.** Several confident conclusions in this project
  turned out wrong on inspection — an "expired" ADC that worked fine, a gate
  defect that did not exist. Check, then claim.
- **Report blockers plainly**, including the ones you caused.
