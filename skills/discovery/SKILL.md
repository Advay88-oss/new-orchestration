---
name: discovery
description: Autonomous Discovery Mode — rules, axes, evidence schema, and link verification for surfacing novel market players.
version: 1.0.0
metadata:
  hermes:
    tags: [discovery, market-intelligence, competitor-research, gtm, evidence-verification]
---

# DISCOVERY MODE — Permanent Rule

Every research run must surface players it has never surfaced before, and every statement about them must carry a link that resolves.

This rule applies to every competitor research, growth analysis, or pattern extraction task from now on.

---

## A1 · Exclude What is Already Covered

```python
seen = {p["player_id"] for p in load_all_registry_players()}
candidates = [c for c in candidates if resolve_player_id(c) not in seen]
```

If a run returns only names already documented, it failed. Say so plainly rather than re-reporting them.

---

## A2 · Rotate the Discovery Axis

Never screen the same way twice in a row. Track the last axis used and pick a different one from the canonical registry.

Canonical Axes:
1. `mechanism`: description markers: `leverage`, `credit line`, `looping`, `prime broker`, `cross-margin`, `credit account`
2. `chain`: rotate: `Stellar`, `Solana`, `Base`, `Sui`, `TON`, `Aptos`, `Cosmos`
3. `category_adjacent`: `Collateral Markets`, `Secondary Debt Markets`, `Basis Trading`, `RWA Lending`, `Synthetics`, `Interest Rate Derivatives`
4. `size_band`: rotate: `<$5M`, `$5–50M`, `$50–200M`, `$200M–1B`
5. `recency`: listedAt within last `6` / `12` / `24` months
6. `publishing`: high `gtm_per_tvl`, any category

Log `discovery_axis` on every run. Repeating an axis before the others have been used is a bug.

Screen beyond DeFi-native as well: non-EVM ecosystems, regional protocols with local user bases, TradFi-adjacent credit products, consumer fintech running credit mechanics. Some of the most transferable GTM comes from outside crypto entirely.

---

## A3 · Every Record Carries Its Evidence

Output Schema:
```json
{
  "player_id": "...",
  "discovery_axis": "chain:sui",
  "run_date": "2026-09-14",

  "tvl_usd": 4820000,
  "tvl_source": "@url:`https://api.llama.fi/protocols`",
  "snapshot_date": "2026-09-14",
  "category_raw": "Lending",

  "twitter": "@handle",
  "twitter_source": "@url:`https://api.llama.fi/protocols`",
  "website": "https://...",
  "website_probe_status": "CONFIRMED_200 | DEAD | NO_URL",

  "confirmed_blog_urls": ["https://..."],
  "confirmed_forum_urls": ["https://..."],
  "probe_status": "PROBED",

  "relevance": "MECHANISM | AUDIENCE | GTM_PATTERN | RISK_MODEL | ADJACENT | NOT_RELEVANT",
  "why": "Runs isolated margin accounts on a non-EVM chain — closest structural parallel to Soroban SmartAccounts found so far",
  "why_evidence": ["@url:`https://docs.example.com/architecture`"],

  "evidence_tier": "OBSERVED | INFERRED | UNKNOWN",
  "derived_by": "code | model"
}
```

### Evidence Rules:
- `OBSERVED` requires a `source_url` returning `< 400`. Verify with HTTP HEAD before writing the record, not after.
- `INFERRED` requires `inference_basis` naming the observed facts it was reasoned from.
- `UNKNOWN` is a valid answer. Never estimate a figure, never guess a handle, never construct a URL you have not opened.
- `why` must cite something. "Looks interesting" is not relevance — point at a docs page, a blog post, or the specific DeFiLlama field.
- DeFiLlama numbers are `derived_by: "code"` and cannot be fabricated. Anything a model wrote is `derived_by: "model"` and needs closer review.
- `NOT_RELEVANT` is a useful output. Three genuinely instructive players plus seven honest `NOT_RELEVANT` entries beats ten forced ones.

---

## A4 · Verify Links Before Reporting

```python
for url in record_urls:
    if http_head(url).status >= 400:
        record["evidence_tier"] = "UNKNOWN"
        record["quarantine_reason"] = f"unresolvable: {url}"
        quarantine.append(record)
```

Per-record quarantine — one dead link must not discard a good batch. But if run-level resolution drops below **80%**, halt and alert. That pattern means sources are being invented.

---

## A5 · Discovery Ledger

Every discovery cycle must append to `registry/discovery_log.jsonl`:

```json
{
  "run_date": "2026-09-20T12:00:00Z",
  "discovery_axis": "chain:stellar",
  "candidates_screened": 44,
  "already_seen_excluded": 3,
  "new_players_found": 41,
  "relevant": 12,
  "urls_checked": 38,
  "urls_resolved": 38,
  "unknown_fields": 7
}
```

If `new_players_found` trends toward zero on an axis, that axis is exhausted — retire it and rotate to a new one.
