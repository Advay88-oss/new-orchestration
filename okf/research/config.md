---
type: Research Config
title: Research configuration
description: Where the scout looks and how deep it goes, per company.
tags: [research, config]
status: stable
subreddits: [defi, Stellar, ethereum, cryptocurrency]
search_keywords:
  - agent credit
  - onchain agent
  - liquidation survival
  - composable liquidity
  - unified margin
  - oracle latency
settings:
  deprioritize_depth_limit: 3
  max_twitter_scrapes: 4
  max_reddit_scrapes: 4
sources:
  - id: marketing-config
    resource: /pipeline/config/marketing_config.json
    title: marketing_config non-content keys
---

# Research configuration

The non-content operational settings the scout uses: which subreddits to sweep,
which keywords to search, and how many scrapes to run before giving up.

These are company-specific — a different company lives in different subreddits
and speaks a different problem language — so they belong in the bundle rather
than in code. `marketing_config.json` is generated from this concept plus the
[taxonomy](/taxonomy/index.md) and [competitors](/competitors/index.md), by
`pipeline/scripts/okf_sync_config.py`.

## Fields

- `subreddits` — communities the scout reads for organic signal.
- `search_keywords` — the phrases the audience actually uses; not the company's
  own vocabulary.
- `settings.max_twitter_scrapes` / `max_reddit_scrapes` — hard caps on how much
  the scout pulls per source, so a run cannot balloon.
- `settings.deprioritize_depth_limit` — how far back the anti-repetition logic
  looks before a topic is allowed again.
