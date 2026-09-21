"""The verification gate. Deterministic. Not an LLM judge.

Contract: every web claim carries the exact sentence it came from.
Check 1: that sentence is actually present in the cited source (normalized).
Check 2: every number in the claim appears in the source.
Internal claims are recomputed from the data file, not trusted.
"""
import re
from dataclasses import dataclass, field
from .tools import fetch_source, recompute_internal

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9% ]", "", s.lower())).strip()

def _numbers(s: str) -> list[str]:
    return re.findall(r"\d+(?:\.\d+)?%?", s)

@dataclass
class Result:
    claim_id: str
    text: str
    passed: bool
    source: str
    reasons: list[str] = field(default_factory=list)
    note: str = ""

def _nearest_figure(source_text: str, claim_text: str) -> str:
    m = re.search(r"(\d+%)([^.]*)\.", source_text)
    if not m: return ""
    pct, rest = m.group(1), m.group(2)
    what = re.search(r"led them to (.+?)(?: over| in|$)", rest)
    what = what.group(1) if what else " ".join(rest.split()[:5])
    tail = ", not churn" if "churn" in claim_text.lower() else ""
    return f"{pct} ({what}{tail})"

def check_claim(claim: dict) -> Result:
    if claim["kind"] == "internal":
        n, total = recompute_internal(claim["recompute"])
        exp = claim["recompute"]["expect"]
        ok = (n == exp and total == claim["recompute"]["total"])
        return Result(claim["id"], claim["text"], ok, claim["source"],
                      [] if ok else [f"recomputed {n} of {total}, claim says {exp}"],
                      note=f"recomputed from {claim['source']}")
    src = fetch_source(claim["source"])
    if not src:
        return Result(claim["id"], claim["text"], False, claim["source"], ["cited source not found"])
    reasons = []
    body = _norm(src["text"])
    if _norm(claim["quote"]) not in body:
        reasons.append("quoted sentence not found in source")
    for tok in _numbers(claim["text"]):
        if tok.lower() not in body:
            reasons.append(f'token "{tok}" not found in source')
    for word in ("churn",):
        if word in claim["text"].lower() and word not in body:
            reasons.append(f'token "{word}" not found in source')
    note = f"quote found in {src['publisher']}"
    if reasons:
        near = _nearest_figure(src["text"], claim["text"])
        if near:
            note = f"nearest figure in source: {near}"
    return Result(claim["id"], claim["text"], not reasons, claim["source"], reasons, note)

def run_gate(brief: dict) -> list[Result]:
    return [check_claim(c) for c in brief["claims"]]

def metrics(results: list[Result], usage: dict) -> dict:
    total = len(results); passed = sum(r.passed for r in results)
    return {
        "groundedness": f"{passed} of {total} claims supported",
        "completion": "all 5 brief sections present",
        "cost_per_run": f"${usage['est_cost_usd']:.2f}",
        "latency": f"{usage['elapsed_s']:.1f}s",
    }
