"""A real agent runtime — goal, tools, and a bounded loop.

Everything called an "agent" so far in this codebase has been a single-shot
model call with a structured response: input in, JSON out. That is a function
with a model inside it, and it shows in the output. The copywriter states a
fact slightly wider than the evidence supports, the verifier rejects it two
stages later, and nobody finds out until the gate blocks the run — because the
writer had no way to check its own work before submitting.

An agent here means three things a function does not have:

  **A goal, not a prompt.** It is told what "done" looks like and judged
  against that, rather than asked to produce one output.

  **Tools.** It can go and get what it needs — search the evidence store,
  check whether a claim would verify, read the voice guidance — instead of
  being handed a fixed context block and hoping it contains the right facts.

  **A loop.** It decides what to do next: search, draft, check, search again,
  revise, submit. The loop is bounded and every step is journaled, so the
  autonomy is inspectable rather than a black box.

Bounds are not optional. An unbounded tool loop with a model that disagrees
with its own checker will spend the budget and produce nothing, so there is a
hard step cap, a wall-clock deadline, and a rule that a repeated identical tool
call counts as a step without being executed twice.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .contracts import StageResult, degraded, digest, ok
from .llm import LLMClient, LLMError

MAX_STEPS = 8
DEADLINE_S = 180.0


@dataclass(frozen=True)
class Tool:
    """One capability an agent may call."""
    name: str
    description: str
    parameters: dict[str, Any]
    fn: Callable[..., Any]

    def declaration(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description,
                "parameters": self.parameters}

    def call(self, args: dict[str, Any]) -> Any:
        return self.fn(**args)


@dataclass
class Step:
    n: int
    kind: str                     # "tool" | "final" | "error"
    tool: str | None = None
    args: dict[str, Any] | None = None
    result_summary: str = ""
    cached: bool = False


@dataclass
class AgentRun:
    """What the agent did, not just what it returned."""
    answer: Any | None
    steps: list[Step] = field(default_factory=list)
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    cost_known: bool = True
    stopped_because: str = ""
    elapsed_s: float = 0.0

    @property
    def tool_calls(self) -> list[str]:
        return [f"{s.tool}{'(cached)' if s.cached else ''}"
                for s in self.steps if s.kind == "tool" and s.tool]

    @property
    def completed(self) -> bool:
        return self.answer is not None


class Agent:
    """A goal, a toolbox, and a bounded loop."""

    def __init__(
        self,
        name: str,
        goal: str,
        tools: list[Tool],
        answer_schema: dict[str, Any],
        *,
        client: LLMClient | None = None,
        prompt_version: str = "agent/v1",
        max_steps: int = MAX_STEPS,
        deadline_s: float = DEADLINE_S,
        temperature: float = 0.4,
    ) -> None:
        self.name = name
        self.goal = goal
        self.tools = {t.name: t for t in tools}
        self.answer_schema = answer_schema
        self.prompt_version = prompt_version
        self.max_steps = max_steps
        self.deadline_s = deadline_s
        self.temperature = temperature
        self._client = client

    # -- the loop --------------------------------------------------------

    def run(self, task: str) -> AgentRun:
        from .models import client_for

        client = self._client
        if client is None:
            client, _ = client_for("reasoning")

        started = time.time()
        run = AgentRun(answer=None)
        seen_calls: dict[str, Any] = {}

        contents: list[dict[str, Any]] = [
            {"role": "user", "parts": [{"text": task}]}
        ]
        declarations = [t.declaration() for t in self.tools.values()]
        # The submit tool is how the agent says it is done. Modelling the
        # finish as a tool rather than "any text reply" means the answer is
        # always schema-checked, and a rambling reply cannot be mistaken for one.
        declarations.append({
            "name": "submit",
            "description": "Submit the final answer. Call this only when the goal is met.",
            "parameters": self.answer_schema,
        })

        for step_n in range(1, self.max_steps + 1):
            if time.time() - started > self.deadline_s:
                run.stopped_because = f"deadline {self.deadline_s}s exceeded"
                break

            try:
                reply = client.call_with_tools(
                    contents=contents,
                    tools=declarations,
                    system=self.goal,
                    prompt_version=self.prompt_version,
                    temperature=self.temperature,
                )
            except LLMError as exc:
                run.steps.append(Step(step_n, "error", result_summary=str(exc)[:200]))
                run.stopped_because = f"model error: {exc}"[:200]
                break

            run.model = reply.model
            run.input_tokens += reply.input_tokens
            run.output_tokens += reply.output_tokens
            run.cost_usd += reply.cost_usd or 0.0
            run.cost_known = run.cost_known and reply.pricing_known

            if not reply.function_calls:
                # No tool, no submit: nudge once, then stop. A model that will
                # not use its tools is not going to start on the fifth ask.
                run.steps.append(Step(step_n, "error",
                                      result_summary="no tool call returned"))
                run.stopped_because = "agent replied without calling a tool"
                break

            contents.append({"role": "model", "parts": reply.raw_parts})

            responses: list[dict[str, Any]] = []
            finished = False

            for fc in reply.function_calls:
                name = fc.get("name", "")
                args = fc.get("args") or {}

                if name == "submit":
                    run.answer = args
                    run.steps.append(Step(step_n, "final",
                                          result_summary="submitted"))
                    run.stopped_because = "submitted"
                    finished = True
                    break

                tool = self.tools.get(name)
                if tool is None:
                    payload: Any = {"error": f"unknown tool {name!r}"}
                    run.steps.append(Step(step_n, "error", tool=name, args=args,
                                          result_summary=payload["error"]))
                else:
                    key = digest([name, args])
                    if key in seen_calls:
                        payload = seen_calls[key]
                        run.steps.append(Step(step_n, "tool", name, args,
                                              "repeat call, cached", cached=True))
                    else:
                        try:
                            payload = tool.call(args)
                        except Exception as exc:          # noqa: BLE001 — boundary
                            # Tool failures go back to the agent. It may be able
                            # to recover with different arguments; raising here
                            # would end a run that could still succeed.
                            payload = {"error": f"{type(exc).__name__}: {exc}"[:300]}
                        seen_calls[key] = payload
                        run.steps.append(Step(step_n, "tool", name, args,
                                              _summarise(payload)))

                responses.append({
                    "functionResponse": {
                        "name": name,
                        "response": {"result": payload},
                    }
                })

            if finished:
                break

            # Tell the agent what it has left. Without this an agent explores
            # until the cap and submits nothing — it has no way to know a budget
            # exists, so it behaves as though it is unlimited. The last two
            # steps become an explicit instruction to converge.
            remaining = self.max_steps - step_n
            if remaining <= 0:
                run.stopped_because = f"step cap {self.max_steps} reached"
                break

            # Function responses must be their own turn — the API rejects a
            # request whose final turn mixes tool results with free text.
            contents.append({"role": "user", "parts": responses})

            if remaining <= 2:
                note = (f"BUDGET: {remaining} step(s) left. Stop gathering. Draft "
                        f"with what you have, check only the claims you intend to "
                        f"keep, then call submit. Submitting something honest and "
                        f"narrow beats submitting nothing.")
            else:
                note = f"BUDGET: {remaining} step(s) left."
            contents.append({"role": "user", "parts": [{"text": note}]})
        else:
            run.stopped_because = f"step cap {self.max_steps} reached"

        run.elapsed_s = round(time.time() - started, 2)
        if run.answer is None and not run.stopped_because:
            run.stopped_because = "loop ended without an answer"
        return run

    # -- stage adapter ---------------------------------------------------

    def as_stage(self, stage: str, task: str, *, input_hash: str,
                 build: Callable[[dict], Any] | None = None) -> StageResult[Any]:
        """Run the agent and return a StageResult with its trace attached."""
        started = time.time()
        run = self.run(task)

        meta = dict(model=run.model, prompt_version=self.prompt_version,
                    input_tokens=run.input_tokens, output_tokens=run.output_tokens,
                    cost_usd=run.cost_usd, cost_known=run.cost_known,
                    attempts=len(run.steps), tool_calls=run.tool_calls)

        if not run.completed:
            return degraded(stage, None, started,
                            f"{self.name} did not submit an answer: {run.stopped_because}",
                            input_hash=input_hash, **meta)

        try:
            value = build(run.answer) if build else run.answer
        except Exception as exc:                          # noqa: BLE001 — boundary
            return degraded(stage, None, started,
                            f"{self.name} submitted an answer that failed validation: {exc}"[:300],
                            input_hash=input_hash, **meta)

        return ok(stage, value, started, input_hash=input_hash, **meta)


def _summarise(payload: Any, limit: int = 200) -> str:
    try:
        s = json.dumps(payload, default=str)
    except Exception:
        s = str(payload)
    return s[:limit]
