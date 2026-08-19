---
name: okf-pack
description: Create, validate, or migrate an Open Knowledge Format (OKF v0.2) bundle so the content pipeline can run for a different company. Use when asked to onboard a new company, set up the pipeline for another client, scaffold or check a knowledge pack, or when someone edits the safety rules and needs the gate and bundle kept in sync.
---

# OKF knowledge packs

Everything company-specific in this pipeline lives in one OKF v0.2 bundle.
Swapping that directory points the whole system at a different company. This
skill scaffolds a new bundle, validates one, and keeps the safety gate and the
bundle from drifting apart.

Spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf
Reference bundle: `okf/` (Vanna). Authoring guide: `OKF-PACKS.md`.

## The rule that governs this whole skill

**A safety control must never fail open.** The gate falls back to its built-in
rules when a bundle is missing, unreadable or carries no rules — which means an
un-rewritten pack does not disable the gate, it silently applies **the previous
company's rules**. That looks like a working gate and is not one.

So: never report a new company's pack as ready until `okf_validate.py --strict`
passes *and* a must-block test written for that company actually blocks.

## Commands

Always run with the pipeline interpreter and UTF-8:

```bash
export PYTHONIOENCODING=utf-8
```

Inspect a bundle:

```bash
python pipeline/scripts/okf_loader.py
```

Validate — conformance errors and pipeline-readiness warnings, separately:

```bash
python pipeline/scripts/okf_validate.py --bundle okf --strict
```

Prove bundle rules still match the gate's built-ins:

```bash
python pipeline/scripts/okf_parity_test.py
```

Re-export after any gate edit, or check in CI that nobody forgot:

```bash
python pipeline/scripts/okf_export_rules.py --check
```

Regenerate `marketing_config.json` after editing taxonomy, competitors or
research config in the bundle:

```bash
python pipeline/scripts/okf_sync_config.py
```

```bash
python pipeline/scripts/okf_sync_config.py --check
```

Point the pipeline at a different bundle:

```bash
export OKF_BUNDLE="D:/clients/acme/okf"
```

## Scaffolding a new company

Copy the structure, not the content. Work in this order — the later steps are
worthless if the earlier ones are wrong.

1. **`company/constraint.md` first.** The single fact about the company's stage
   that makes otherwise-normal marketing claims false: pre-revenue, in beta,
   regulated, results unpublished, licence pending. Every safety rule descends
   from it. If the company genuinely has no such constraint, write that
   explicitly rather than deleting the file — absent and undefined are
   different, and only one is safe.
2. **`facts/`** — Tier A quotable, Tier B needs its qualifier, Tier C future
   tense only. The tier *test* questions in the reference bundle are portable;
   the facts are not.
3. **`arcs/`** — exactly three, and they must genuinely disagree about *which
   problem matters most*. Three arcs that all say "we are better" collapse the
   debate back into three versions of one post, which is the failure the
   architecture exists to prevent. Each arc names what it may not claim and how
   it argues against the other two.
4. **`rules/`** — rewrite `retired-claims` entirely (it is almost always empty
   for a new company; that is correct), rewrite `hard-prohibitions` and
   `tier-f-unsupported` around the new facts, review `voice` — it is mostly
   portable.
5. **`taxonomy/`** — the `topic` values are the vocabulary the whole pipeline
   speaks. Renaming one is a breaking change: the permitted-value list is also
   written into the scout prompt in the orchestrator.
6. **`competitors/`, `channels/`, `brand/`, `agents/`** — mechanical.
7. **`index.md` per directory, `log.md` at the root**, and `okf_version: "0.2"`
   in the root index only.

## Writing a concept

Only `type` is required (OKF §11). Recommended: `title`, `description`,
`resource`, `tags`. Useful families this pipeline reads:

- `status: draft | stable | deprecated` — absent means stable. Retired claims
  should be `deprecated`, not deleted; deleting loses the reason.
- `verified: [{by, at}]` — `human:<id>` yields the **human-reviewed** trust
  tier, which is what a Telegram approval represents. No `verified` key means
  **unverified**.
- `stale_after: YYYY-MM-DD` — for claims that expire.
- `sources: [{id, resource, title}]` — provenance. `resource` is required
  within each entry.

Cross-link with bundle-absolute markdown links (`[text](/facts/retired.md)`) —
they survive files moving. Links out of the bundle to repository paths
(`/pipeline/...`, `/files/...`) are fine and the validator ignores them.

## Adding or changing a safety rule

Rules live in the `rules` list of a `Claim Rule Set` concept: `id`, `severity`,
`pattern`, `why`, `fix`, `flags`.

`why` is shown to the agent that wrote the draft and `fix` tells it what to
write instead. **A rule with no usable `fix` produces a strategist that retries
the same mistake** — the validator warns on this.

Then prove it. A rule that has never blocked anything has never been tested:

```bash
python pipeline/scripts/claim_safety_gate.py --text "a claim that must be blocked"
```

Exit 1 with a non-empty `violations` array is the pass condition. Add the case
to `CORPUS` in `okf_parity_test.py` so it stays proven.

**The reference bundle contains a worked example of getting this wrong:**
`R-mcp-differentiator` matches "the only protocol with MCP" but passes a bare
"MCP-native" feature bullet — the exact phrasing sitting in the company's own
source file. The rule looked correct and had never been tested against the
string it was written for. Assume yours has the same flaw until a test says
otherwise.

## Reporting

When you finish, state plainly: which concepts you wrote, what
`okf_validate.py --strict` returned, and which must-block cases you proved. If
a rule set was left as the reference company's, say so — that is the single most
dangerous thing to leave unmentioned.
