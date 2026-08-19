# OKF knowledge packs

How this pipeline is pointed at a different company by swapping one directory.

Everything company-specific now lives in an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)
v0.2 bundle. OKF is Google Cloud's vendor-neutral spec, published June 2026:
knowledge as a directory of markdown files with YAML frontmatter, one required
field (`type`), no SDK and no runtime.

Companion documents: [WHITE-LABEL-SETUP.md](WHITE-LABEL-SETUP.md) for the full
per-company setup surface, [ARCHITECTURE.md](ARCHITECTURE.md) for how the
pipeline works.

---

## What changed

Before, a new company meant editing Python — 32 safety rules were literals
inside `claim_safety_gate.py`, and the facts ledger it was derived from was not
read at runtime at all. Editing the ledger changed nothing.

Now those rules are data in the bundle. The gate loads them, and falls back to
its built-ins if the bundle is missing.

| | Before | Now |
|---|---|---|
| Safety rules | Python literals | `okf/rules/*.md` |
| Facts ledger coupling | none — docstring only | loaded from the bundle |
| Narrative arcs | prose inside personas | `okf/arcs/*.md`, with `opposes` links |
| Taxonomy, competitors | `marketing_config.json` | `okf/taxonomy/`, `okf/competitors/` |
| Overriding constraint | implicit, repeated in many files | one concept, `okf/company/constraint.md` |
| New company | edit code | edit markdown |

---

## The bundle

```
okf/
  index.md              okf_version: "0.2"
  log.md                change history (§9)
  company/              identity, and the overriding constraint
  arcs/                 the three competing positions
  facts/                tier A / B / C, and retired
  rules/                the safety rules, as data
  taxonomy/             content pillars
  competitors/          who is watched and referenced
  channels/             where content goes, who approves
  brand/                palette, logo, card geometry
  agents/               the seven personas
```

Current state: **34 concepts, 32 rules**, conforming to v0.2.

```bash
python pipeline/scripts/okf_validate.py --strict
```

---

## Tooling

| Script | Does |
|---|---|
| `okf_loader.py` | Reads a bundle. `Bundle.load(path)`, then `.rules()`, `.arcs()`, `.taxonomy()`, `.constraint()` |
| `okf_validate.py` | Conformance (§11) as errors, pipeline readiness as warnings. `--strict` fails on warnings |
| `okf_export_rules.py` | Dumps the gate's built-ins to the bundle. `--check` fails if they have drifted |
| `okf_parity_test.py` | Proves bundle rules and built-ins give identical verdicts |

Point at another bundle with `OKF_BUNDLE`:

```bash
export OKF_BUNDLE="D:/clients/acme/okf"
```

The `okf-pack` skill wraps all of this — ask for a new company pack and it
follows the order below.

---

## How the gate uses it

`claim_safety_gate.active_rules()` prefers the bundle and falls back to the
built-in literals when a bundle is absent, unreadable, or carries no rules. Every
verdict now reports which was used:

```json
{ "pass": false, "rules_source": "okf:D:\\new orchestration\\okf", "rule_count": 32 }
```

**Why fallback rather than failing hard.** A safety control must not fail open.
But note what the fallback actually means for a *new* company: an un-rewritten
pack does not disable the gate — it silently applies **the previous company's
rules**. That looks like a working gate and is not one. `rules_source` in the
verdict is how you catch it, so log it.

### Parity is asserted, not assumed

Moving a safety control's rules out of code is only safe if behaviour is
unchanged, so that is tested rather than hoped for:

```bash
python pipeline/scripts/okf_parity_test.py
```

```
built-in rules : 32
OKF rules      : 32
OK    rule ids identical (32)
OK    every pattern and flag matches verbatim
OK    identical verdicts on all 10 corpus inputs
```

The same run doubles as a must-block / must-pass suite. Extend `CORPUS` per
company.

---

## Onboarding a new company

Order matters — later steps are worthless if earlier ones are wrong.

1. **`company/constraint.md`** — the one fact about the company's stage that
   makes normal marketing claims false. Everything else descends from it. If
   there genuinely is none, write that explicitly rather than deleting the file.
2. **`facts/`** — sort every claim into quotable / needs-a-qualifier /
   future-tense-only. The tier *tests* in the reference bundle are portable; the
   facts are not.
3. **`arcs/`** — exactly three, genuinely opposed. They must disagree about
   *which problem matters most*, not about who is best. Three arcs that all say
   "we are better" collapse the debate into three versions of one post, which is
   the exact failure this architecture was built to fix.
4. **`rules/`** — `retired-claims` is usually empty for a new company and that
   is correct; it fills as the market moves. Rewrite the prohibitions around the
   new facts. `voice` is mostly portable — review, don't rewrite.
5. **`taxonomy/`** — `topic` values are the pipeline's vocabulary. Renaming one
   is a breaking change: the permitted-value list is *also* inline in the scout
   prompt in the orchestrator.
6. **`competitors/`, `channels/`, `brand/`, `agents/`** — mechanical.
7. `okf_validate.py --strict`, then prove one rule blocks something.

---

## What OKF gave us for free

Three of the spec's optional families turned out to model things this pipeline
already did informally:

- **`status: deprecated`** is exactly right for retired claims. They should not
  be deleted — deleting loses *why* a claim was retired and when, which is the
  part that stops someone reinstating it six months later.
- **`verified: [{by: human:<id>}]`** and OKF's derived trust tiers —
  unverified / machine-confirmed / human-reviewed — describe this pipeline's
  human review gate precisely. A Telegram approval *is* a human verification
  event.
- **`sources: [{id, resource}]`** gives per-claim attribution, which is what the
  facts ledger needed and never had in a machine-readable form.

---

## What the bundle now drives

Wired and verified, each with a fail-safe fallback to the previous hardcoded
values so a missing or broken bundle never takes the pipeline down:

| Consumer | Reads from bundle | Fallback |
|---|---|---|
| `claim_safety_gate.py` | all 32 rules, live | built-in literals |
| `render_visual.py` | palette, accents, background | built-in Vanna palette |
| `marketing_config.json` | taxonomy, competitors, research config | — (generated file) |

The orchestrators still read `marketing_config.json` rather than the bundle
directly — but that file is now **generated from the bundle** by
`okf_sync_config.py`, so the bundle is its source of truth. Edit the bundle, run
sync, the orchestrators see it:

```bash
python pipeline/scripts/okf_sync_config.py          # regenerate
python pipeline/scripts/okf_sync_config.py --check   # CI: fail if stale
```

The generated config is byte-for-value identical to the hand-written one that
preceded it — verified — so nothing about the running pipeline changed; only its
source moved.

## Known limits

- **One concept per rule *set*, not per rule.** OKF's model is one concept per
  file, so 32 rules would strictly be 32 files. They are grouped into five sets
  with the rules as a frontmatter list instead. Conformant — `type` is present
  and extra keys are allowed — but a deliberate departure, chosen because
  per-company editing is far easier with grouped sets. The same applies to the
  Research Config concept, which holds subreddits, keywords and settings as
  frontmatter lists rather than one concept each.
- **The bundle mirrors `files/`; it does not replace it.** The twelve documents
  under `files/` are still the long-form source. Concepts reference them via
  `sources` rather than duplicating them, so the two can still drift.
- **`marketing_config.json` is a generated artifact now, but still committed.**
  Editing it by hand will be overwritten on the next sync, and `--check` will
  flag it as stale in the meantime. Edit the bundle, not the config.
- **The narrative arcs live in two places.** The bundle's `arcs/` concepts and
  the strategist personas in `pipeline/buzz-pack/` both carry the arc positions.
  The bundle is the documented source; the personas are what the reasoning step
  actually loads. Keep them in step by hand until the personas are generated
  from the bundle.
- **`agents/` points at the persona files rather than containing them.** Persona
  text stays in `pipeline/buzz-pack/` where both execution paths load it.
