"""Typed contracts for every pipeline stage.

The audit found that every quality gate returned a constant and every failure
fell back to something that looked like success. These types exist to make that
impossible to express: a StageResult cannot be `ok` without a value, cannot be
`degraded` without a reason, and cannot be `failed` without an error.

Strict by construction — unknown fields raise rather than being silently dropped,
because a silently dropped field is how Agent 03 stopped reaching Agent 08.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T")

Status = Literal["ok", "degraded", "failed"]

StageState = Literal[
    "queued", "running", "succeeded", "degraded",
    "failed", "retrying", "skipped", "blocked", "stale",
]


class Strict(BaseModel):
    """Base for every contract. Extra fields are an error, not a shrug."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def digest(obj: Any) -> str:
    """Stable content hash, used to prove two runs saw the same input."""
    try:
        blob = json.dumps(obj, sort_keys=True, default=str, ensure_ascii=False)
    except Exception:
        blob = repr(obj)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------
# Evidence and claims — grounding is a type, not a convention
# --------------------------------------------------------------------------

class Evidence(Strict):
    """One retrieved fact with enough provenance to re-check it later."""
    id: str
    snippet: str
    source_url: str | None = None
    source_name: str
    observed_at: str
    kind: Literal["scraped", "onchain", "docs", "research", "manual"]

    @model_validator(mode="after")
    def _require_locator(self) -> "Evidence":
        # Anything fetched from the web must carry the URL it came from, so the
        # claim it supports can be re-checked. Onchain readings and manual
        # entries are located by source_name + observed_at instead.
        if self.kind in ("scraped", "docs", "research") and not self.source_url:
            raise ValueError(f"evidence {self.id}: {self.kind} evidence requires source_url")
        return self


ClaimKind = Literal["vanna_fact", "competitor_fact", "comparative", "inference", "creative"]
ClaimStatus = Literal["verified", "unverified", "refuted", "unsupported"]


class Claim(Strict):
    """A single assertion extracted from generated copy.

    `verified` demands a source. `unsupported` is the verdict the old blacklist
    could never reach: the statement is coherent but appears in no evidence.
    """
    text: str
    kind: ClaimKind
    status: ClaimStatus = "unverified"
    source_id: str | None = None
    source_url: str | None = None
    observed_at: str | None = None
    method: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _verified_needs_source(self) -> "Claim":
        if self.status == "verified":
            if not self.source_id:
                raise ValueError(f"claim {self.text[:40]!r}: verified requires source_id")
            if not self.method:
                raise ValueError(f"claim {self.text[:40]!r}: verified requires method")
        return self

    @property
    def blocks_publication(self) -> bool:
        """Creative framing may ship unverified. Factual assertions may not."""
        if self.kind == "creative":
            return False
        return self.status != "verified"


# --------------------------------------------------------------------------
# StageResult — the load-bearing type
# --------------------------------------------------------------------------

class StageResult(Strict, Generic[T]):
    stage: str
    status: Status
    value: T | None = None
    degraded_reason: str | None = None
    error: str | None = None

    started_at: float
    ended_at: float

    # Observability. `model` is the REAL id returned by the provider, never an
    # alias — the audit found `gemini-3.8-flash` was a label on gemini-2.5-flash.
    model: str | None = None
    prompt_version: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    # False when the provider has no published rate we hold for this model.
    # Reporting $0.00 for an unpriced model is the same class of error as the
    # wall-clock token estimates this replaces, so it is flagged instead.
    cost_known: bool = True
    attempts: int = 1
    tool_calls: list[str] = Field(default_factory=list)

    input_hash: str
    output_hash: str | None = None

    @model_validator(mode="after")
    def _no_lying(self) -> "StageResult":
        if self.status == "degraded" and not self.degraded_reason:
            raise ValueError(f"{self.stage}: degraded requires degraded_reason")
        if self.status == "failed" and not self.error:
            raise ValueError(f"{self.stage}: failed requires error")
        if self.status == "ok":
            if self.value is None:
                raise ValueError(f"{self.stage}: ok requires a value")
            if self.degraded_reason or self.error:
                raise ValueError(f"{self.stage}: ok cannot carry a reason or error")
        if self.ended_at < self.started_at:
            raise ValueError(f"{self.stage}: ended before it started")
        return self

    @property
    def duration_s(self) -> float:
        return round(self.ended_at - self.started_at, 3)

    @property
    def state(self) -> StageState:
        return {"ok": "succeeded", "degraded": "degraded", "failed": "failed"}[self.status]


def ok(stage: str, value: T, started: float, *, input_hash: str, **meta: Any) -> StageResult[T]:
    return StageResult[T](
        stage=stage, status="ok", value=value,
        started_at=started, ended_at=time.time(),
        input_hash=input_hash, output_hash=digest(value), **meta,
    )


def degraded(stage: str, value: T | None, started: float, reason: str, *,
             input_hash: str, **meta: Any) -> StageResult[T]:
    """A fallback fired. The output may still be usable — but it is NOT a success."""
    return StageResult[T](
        stage=stage, status="degraded", value=value, degraded_reason=reason,
        started_at=started, ended_at=time.time(),
        input_hash=input_hash, output_hash=digest(value) if value is not None else None, **meta,
    )


def failed(stage: str, started: float, error: str, *, input_hash: str, **meta: Any) -> StageResult[Any]:
    return StageResult[Any](
        stage=stage, status="failed", error=error,
        started_at=started, ended_at=time.time(), input_hash=input_hash, **meta,
    )


# --------------------------------------------------------------------------
# Pipeline payloads
# --------------------------------------------------------------------------

class Signal(Strict):
    """One ingested intelligence signal. Engagement is optional and, when
    present, must be real — the old scout filled it with random.randint()."""
    id: str
    title: str
    summary: str = ""
    source_name: str
    source_url: str | None = None
    observed_at: str
    engagement: dict[str, int] | None = None


class Opportunity(Strict):
    id: str
    title: str
    rationale: str
    audience: str
    score: float = Field(ge=0.0, le=1.0)
    signal_ids: list[str] = Field(default_factory=list)


class Strategy(Strict):
    id: str
    opportunity_id: str
    audience: str
    narrative_arc: Literal["capital_efficiency", "risk_relief", "agentic_credit"]
    problem_statement: str
    angle: str
    evidence_ids: list[str] = Field(default_factory=list)


class CopyDraft(Strict):
    id: str
    strategy_id: str
    channel: Literal["x", "linkedin", "reddit"]
    hook: str
    body: str
    thread: list[str] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)

    @property
    def blocking_claims(self) -> list[Claim]:
        return [c for c in self.claims if c.blocks_publication]


# --------------------------------------------------------------------------
# Visual contracts — the LLM specifies, the renderer draws
# --------------------------------------------------------------------------

class Block(Strict):
    role: Literal["stat", "label", "caption", "step", "compare_left", "compare_right"]
    text: str
    emphasis: Literal["primary", "secondary", "muted"] = "secondary"


class Focal(Strict):
    """What the eye lands on first. A composition without one is why the old
    output read as 'dead centre object on a gradient'."""
    block_index: int = Field(ge=0)
    reason: str


class PaletteSlice(Strict):
    """Chosen FROM design tokens. Free-form colours are rejected by render."""
    ink: str
    ground: str
    accent: str


class VisualSpec(Strict):
    layout: Literal["hero_stat", "comparison", "sequence", "quote", "diagram"]
    headline: str
    subhead: str | None = None
    blocks: list[Block] = Field(min_length=1, max_length=6)
    focal: Focal
    palette: PaletteSlice
    background: Literal["flat", "gradient", "texture"] = "flat"
    disclaimer: str | None = None

    @model_validator(mode="after")
    def _focal_in_range(self) -> "VisualSpec":
        if self.focal.block_index >= len(self.blocks):
            raise ValueError("focal.block_index points past the end of blocks")
        return self


DefectSeverity = Literal["low", "medium", "high"]


class Defect(Strict):
    """Critic output. A defect list is actionable; a score is not."""
    severity: DefectSeverity
    issue: str
    location: str
    reason: str
    fix: str
    confidence: float = Field(ge=0.0, le=1.0)


class Critique(Strict):
    defects: list[Defect] = Field(default_factory=list)
    verdict: Literal["accept", "revise", "reject"]

    @property
    def high_severity(self) -> list[Defect]:
        return [d for d in self.defects if d.severity == "high"]

    @model_validator(mode="after")
    def _verdict_matches_defects(self) -> "Critique":
        # A critic that says "accept" while listing high-severity defects is the
        # 100/100-with-empty-audit pattern. Forbid it.
        if self.verdict == "accept" and any(d.severity == "high" for d in self.defects):
            raise ValueError("cannot accept with high-severity defects outstanding")
        return self


class GateDecision(Strict):
    passed: bool
    blocking_claims: list[Claim] = Field(default_factory=list)
    rule_violations: list[str] = Field(default_factory=list)
    rules_source: str

    @model_validator(mode="after")
    def _pass_means_clean(self) -> "GateDecision":
        if self.passed and (self.blocking_claims or self.rule_violations):
            raise ValueError("gate cannot pass with outstanding claims or violations")
        return self
