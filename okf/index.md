---
okf_version: "0.2"
---

# Vanna knowledge bundle

The company-specific knowledge this content pipeline runs on, packaged as an
[Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)
v0.2 bundle so the same pipeline can be pointed at a different company by
swapping this directory.

Everything here was company-specific and previously hardcoded across
`files/`, `pipeline/buzz-pack/`, `pipeline/config/marketing_config.json` and
`pipeline/scripts/claim_safety_gate.py`. See [/log.md](/log.md) for history and
`OKF-PACKS.md` at the repository root for how to author a bundle for another
company.

## Company

* [Identity](/company/identity.md) - who this company is and what it sells.
* [Overriding constraint](/company/constraint.md) - the single rule that outranks every other instruction. Read this first.

## Positioning

Standing strategic directives that sit over every arc and every launch plan.

* [Infrastructure-led, dual B2B + B2C](/positioning/infrastructure-thesis.md) - lead with the infrastructure; one system serving businesses and consumers.

## Narrative arcs

The three competing positions the strategists argue. One per strategist, assigned rather than chosen.

* [Capital efficiency](/arcs/capital-efficiency.md) - collateral doing one job when it could do six.
* [Risk relief](/arcs/risk-relief.md) - surviving leverage, not acquiring it.
* [Agentic credit](/arcs/agentic-credit.md) - agents can pay but cannot borrow.

## Facts

Claims sorted by how they may be stated. Nothing outside these files may be asserted about the company.

* [Tier A - quotable](/facts/tier-a-quotable.md) - may be stated plainly.
* [Tier B - qualified](/facts/tier-b-qualified.md) - true but must be stated carefully.
* [Tier C - future](/facts/tier-c-future.md) - future tense only, never present.
* [Retired](/facts/retired.md) - claims that were once safe and are now deprecated.

## Safety rules

Machine-enforced. These are loaded by the claim-safety gate; editing them changes what the gate blocks.

* [Hard prohibitions](/rules/hard-prohibitions.md) - claims that are false at this company's stage.
* [Retired claims](/rules/retired-claims.md) - positioning retired by competitive reality.
* [Voice](/rules/voice.md) - brand-voice prohibitions.
* [Platform limits](/rules/platform-limits.md) - per-channel length and format constraints.

## Content

* [Taxonomy](/taxonomy/index.md) - the content pillars the pipeline rotates through.
* [Competitors](/competitors/index.md) - who is referenced and how.
* [Channels](/channels/index.md) - where content goes and who approves it.

## Brand

* [Palette and assets](/brand/palette.md) - colours, logo and card geometry used by the renderer.

## Agents

* [Agent roster](/agents/index.md) - the seven personas and what each may never do.
