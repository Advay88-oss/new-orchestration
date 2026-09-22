# Vanna GTM — Production Architecture v2

Supersedes `ARCHITECTURE.md` (which describes a design that was never connected; see `AUDIT-2026-09-21.md`).

---

## The one principle

The audit's root finding was not "agents are fake". It was:

> **Every quality gate returns a constant, and every failure falls back to something that looks like success.**

While that holds, no other fix is verifiable. So v2 is built on one inviolable rule:

> **A stage may fail. A stage may degrade. A stage may never lie.**

Concretely, enforced in code:

1. Every stage returns a `StageResult` with `status ∈ {ok, degraded, failed}`. A fallback sets `degraded` and records `degraded_reason`. There is no path that returns `ok` without doing the work.
2. A run's status is the **worst** stage status. A run containing a degraded stage cannot be reported as a clean success.
3. **No unconditional constants in any score.** A score not derived from its input is a bug, not a default.
4. Every artifact carries `provenance`. Text with an unverified factual claim cannot reach a human labelled as verified.

---

## What is an agent, honestly

Ten of thirteen "agents" were rule tables. v2 stops calling them agents. Naming is a correctness property: it determines what reviewers expect to be true.

| Kind | Definition | v2 members |
|---|---|---|
| **Agent** | Makes a model call whose *reasoning* materially determines the output; can fail in interesting ways | Strategist · Copywriter · Concept Director · Visual Critic · Claim Verifier |
| **Stage** | Deterministic function. Fast, testable, no model | Ingest · Select · Classify · Render · Compose · Gate · Journal |
| **Tool** | External effect behind an interface | Scraper · ImageModel · Browser · Telegram · Store |

Five agents, not thirteen. Each one earns its model call, and each has a defined failure mode.

---

## Runtime topology

```
                    ┌──────────────────────┐
   dashboard ──────►│  JobQueue (durable)  │◄────── scheduler (supervised)
   POST /api/run    │  jobs/*.json         │
                    └──────────┬───────────┘
                               │ claim (atomic, idempotent)
                               ▼
                        ┌─────────────┐
                        │   Worker    │   long-lived process
                        └──────┬──────┘
                               │
                    ┌──────────▼───────────┐
                    │      Pipeline        │  journals EVERY stage
                    │  (resumable)         │  before and after
                    └──────────┬───────────┘
                               │
   Ingest → Select → Strategy* → Copy* → Verify* → Concept* → Spec
        → Render(HTML+tokens→Playwright) → Critic* → [revise ≤2] → Gate → Stage → Human
                                                                              (* = agent)
                               │
                    ┌──────────▼───────────┐
                    │ RunLog (append-only) │  one JSONL per run, immutable
                    └──────────────────────┘
```

**The dashboard never spawns a subprocess.** It enqueues and reads the journal. A run survives the HTTP request, a deploy, and the process dying.

---

## Module map

```
core/
  contracts.py   typed I/O for every stage; strict — unknown/missing fields raise
  runlog.py      append-only journal, per-stage spans, resume support
  llm.py         ONE model client: real ids, retry+jitter, timeout, token/cost, prompt version, RAISES
  evidence.py    evidence store with provenance (url, observed_at, snippet)
  verify.py      claim extraction + entailment verification
  design.py      design tokens — single source of truth
  render.py      VisualSpec → HTML → Playwright → PNG (deterministic)
  critic.py      multimodal critic → structured defects
  stages/        the real implementations
  pipeline.py    orchestration + journaling
  queue.py       durable job queue (atomic claim)
  worker.py      queue consumer
```

---

## Key contracts

**StageResult** — the load-bearing type.

```python
class StageResult(BaseModel, Generic[T]):
    stage: str
    status: Literal["ok", "degraded", "failed"]
    value: T | None
    degraded_reason: str | None = None   # REQUIRED when status == degraded
    error: str | None = None             # REQUIRED when status == failed
    started_at: float
    ended_at: float
    model: str | None = None             # real model id, never an alias
    prompt_version: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    input_hash: str
    output_hash: str | None = None
```

Validators enforce that `degraded` carries a reason and `failed` carries an error. You cannot construct a lie.

**Claim** — grounding is a type, not a convention.

```python
class Claim(BaseModel):
    text: str
    kind: Literal["vanna_fact", "competitor_fact", "comparative", "inference", "creative"]
    status: Literal["verified", "unverified", "refuted", "unsupported"]
    source_id: str | None      # REQUIRED when status == verified
    source_url: str | None
    observed_at: str | None
    method: str | None         # how it was verified
```

Copy is assembled from claims. Any claim that is not `verified` or explicitly `creative` blocks the run at the gate.

**VisualSpec** — the LLM specs; it does not draw.

```python
class VisualSpec(BaseModel):
    layout: Literal["hero_stat", "comparison", "sequence", "quote", "diagram"]
    headline: str
    subhead: str | None
    blocks: list[Block]        # typed content blocks, each with role + text
    focal: Focal               # what the eye lands on first
    palette: PaletteSlice      # chosen FROM tokens, not invented
    background: Literal["flat", "gradient", "texture"]
    disclaimer: str | None
```

A schema-validated spec is executed by a deterministic renderer. The image model, if used at all, paints only the `texture` background layer — never text, never logo.

---

## Grounding

```
scraped/researched source ──► EvidenceStore (url, observed_at, snippet, hash)
                                     │
copy draft ──► claim extraction ──► verification ──► Claim[status, source_id]
                                     │
                              gate: any unverified factual claim ⇒ BLOCK
```

Verification is entailment against a retrieved snippet, not substring matching. A number that appears in no source is `unsupported` — which is the case the old blacklist could never detect.

The prompt never supplies facts. Facts arrive as retrieved evidence, and the model is instructed to use only what it is given and to mark anything it cannot support.

**Untrusted content is delimited.** Scraped text enters prompts inside an explicit boundary with an instruction that content within is data, never instructions. Source text is never concatenated raw.

---

## Visual pipeline

The audit's root cause was that structured creative decisions were computed and then dropped, because both deterministic renderers failed at import. v2 makes the spec the only path to pixels.

```
Concept Director (agent)   3 real competing concepts, scored on inputs
        │
   novelty gate            BLOCKS a clone — does not "select the least bad"
        │
Spec Author (agent)        VisualSpec, schema-validated
        │
   design tokens           typography scale, grid, spacing, palette
        │
   HTML/CSS template       everything readable, pixel-exact
        │
   [optional] image model  background texture layer ONLY
        │
   Playwright @2×          deterministic PNG
        │
Visual Critic (agent)      structured defects, not a score
        │
   revise ≤ 2 rounds       stop on convergence or no high-severity defects
        │
   human review
```

**Critic output is a defect list**, which is what makes revision possible:

```json
{ "severity": "high", "issue": "headline overlaps focal object",
  "location": "top-right", "reason": "...", "fix": "...", "confidence": 0.94 }
```

This is **evaluator-guided iterative generation**, not reinforcement learning. No reward model is trained; no policy is updated.

---

## Observability

Every stage emits an OpenTelemetry-GenAI-shaped span: operation name, agent name, provider, **real** model id, input/output tokens, finish reason, latency, cost, prompt version, and the tool calls it made. Run records are append-only and immutable; the approve action writes a **new** record rather than overwriting.

The dashboard renders the journal. It never synthesizes status, and when the backend is unavailable it shows an error state — never fixtures.

Per-stage lifecycle is explicit: `QUEUED · RUNNING · SUCCEEDED · DEGRADED · FAILED · RETRYING · SKIPPED · BLOCKED · STALE`.

---

## Reliability

Timeouts on every remote call. Capped exponential backoff **with jitter**, retried at one level only. Idempotency keys on anything with an effect. A circuit breaker on the model provider. Jobs that exceed max attempts move to a dead-letter directory with their journal intact.

The scheduler is supervised by the OS (Task Scheduler / systemd / cloud scheduler) — not a bare `while True`. Missed runs are detected and caught up; overlap is forbidden by policy.

---

## Security

Untrusted scraped content is delimited and never interpolated raw. No `shell=True`. Tools are least-privilege. The dashboard requires auth.

**Rule of Two is preserved deliberately**: this pipeline processes untrusted input and changes state, so it must not also communicate externally without a human. Publication stays behind human approval. This was the one industry check the old system passed; v2 keeps it.

---

## Migration

v2 lands beside the old code as `core/`. Nothing is deleted until its replacement passes tests. The old 14 orchestrators are quarantined, not rewritten. `run_autonomous_gtm_master.py` remains until the worker path is proven, then becomes a thin shim.

**Definition of done for each phase: a test that fails against the old behaviour and passes against the new one.**
