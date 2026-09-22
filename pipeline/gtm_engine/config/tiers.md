# GTM Engine - Operational Tier Definitions & Context Isolation

```
TIER 0   Deterministic Python        Math · promotion count · numbering regex ·
         NEVER FAILS                 claim gate · rendering · enum mapping
         CAN READ: registry, golden set, regression tests

TIER 0b  Python + HTTP               DefiLlama · blog/forum scrape ·
         FALLIBLE, degrades          X (capped 20) · HEAD probes
         CAN READ: external sources only

TIER 1   gemini-3.8-flash            Classification · structured tagging ·
         PINNED                      template descriptions
         CAN READ: classification_view ONLY
         FORBIDDEN: knowledge/internal, golden set, Vanna docs

TIER 2   gemini-3.1-pro-preview      Pair comparison · objection derivation ·
         PINNED, single vendor       Vanna verdicts
         CAN READ: registry + patterns + knowledge/internal
         FORBIDDEN: golden set, regression tests
```

## Derivation Labeling Policy
- `derived_by: "regex_rules"` -> content_category, subcategory, hook_type
- `derived_by: "arithmetic"`  -> pattern_type, instance_count, cadence
- `derived_by: "template"`    -> pattern_template description, Vanna verdicts
- `derived_by: "model"`       -> only where an LLM actually ran (recorded with `model_id`)
