"""The verification gate. YOUR job to build this. It is the only piece of the system that matters.

The rule, in English:
  Every fact has to carry the exact sentence it came from.
  Something has to go back and check that the sentence is really there.

Implement check_claim(claim) -> Result so that:
  - web claims PASS only if claim["quote"] appears in the cited source text (normalize whitespace/case),
    and every number in claim["text"] appears in the source
  - internal claims are recomputed from the CSV, never trusted
  - a FAIL returns human-readable reasons

Do not use an LLM to judge. Ordinary code only. The moment one AI grades another, they can be wrong together.

Hint: fetch_source(source_id) and recompute_internal(spec) in tools.py do the fetching for you.
Reference implementation: ../../freshcart_agent/gate.py  (look only after you have tried)
On stage: paste LIVE_GATE_PROMPT.md into Claude Code and let it fill this in.
"""
import re
from dataclasses import dataclass, field
from .tools import fetch_source, recompute_internal

@dataclass
class Result:
    claim_id: str
    text: str
    passed: bool
    source: str
    reasons: list[str] = field(default_factory=list)
    note: str = ""

def check_claim(claim: dict) -> Result:
    # TODO: build the gate.
    raise NotImplementedError("Build the gate. See the docstring at the top of this file.")

def run_gate(brief: dict) -> list[Result]:
    return [check_claim(c) for c in brief["claims"]]

def metrics(results: list[Result], usage: dict) -> dict:
    total = len(results); passed = sum(r.passed for r in results)
    return {"groundedness": f"{passed} of {total} claims supported", "completion": "all 5 brief sections present",
            "cost_per_run": f"${usage['est_cost_usd']:.2f}", "latency": f"{usage['elapsed_s']:.1f}s"}
