"""The agent loop.

DEMO_MODE (default): replay one genuine captured run, byte for byte, with realistic pacing.
LIVE mode: a real Anthropic tool-use loop. Same tools, same contract. Needs ANTHROPIC_API_KEY.
"""
import json, os, time
from pathlib import Path
from . import render as R
from .tools import read_feedback, web_search

ROOT = Path(__file__).resolve().parent.parent
CAPTURED = ROOT / "fixtures" / "captured_run.json"
PROMPTS = ROOT / "prompts"

def demo_mode() -> bool:
    return os.environ.get("DEMO_MODE", "1") != "0"

def _pace(seconds: float):
    """Stage pacing. FAST=1 collapses waits for preflight/recording checks."""
    if os.environ.get("FAST") == "1": return
    time.sleep(min(seconds, 2.5))

def run_demo() -> tuple[dict, dict]:
    cap = json.load(open(CAPTURED))
    ph, usage = cap["phases"], cap["usage"]
    R.banner("FRESHCART ANALYST", "agent run  ·  DEMO MODE (offline)")

    R.step("READING FEEDBACK")
    fb = read_feedback("data/freshcart_feedback.csv")
    R.line(f"data/freshcart_feedback.csv  ·  {fb['rows']} rows  ·  {ph['read']['days']} days")
    bc = fb["by_channel"]
    R.line(f"app reviews {bc.get('app_review',0)} · support tickets {bc.get('support_ticket',0)} · NPS {bc.get('nps_verbatim',0)}")
    _pace(0.4); R.done(f"loaded in {ph['read']['elapsed_s']}s")

    R.step("CLUSTERING")
    R.spinner("thinking...", 2.0)
    R.cluster_table(ph["cluster"]["themes"])
    R.done(f"{len(ph['cluster']['themes'])} themes in {ph['cluster']['elapsed_s']}s")

    top = ph["cluster"]["themes"][0]["name"]
    R.step(f"GROUNDING  (top theme: {top})")
    for s in ph["ground"]["searches"]:
        R.line(f'→ web_search("{s["query"]}")', "dim"); _pace(0.9)
        hits = web_search(s["query"], offline=True)
        R.done(f"{len(hits)} sources")
    R.done(f"grounded in {ph['ground']['elapsed_s']}s")

    R.step("DRAFTING BRIEF")
    R.spinner("writing...", 1.6)
    R.done(f"brief drafted in {ph['draft']['elapsed_s']}s")
    R.line(f"tokens {usage['input_tokens']:,} in · {usage['output_tokens']:,} out   est. cost ${usage['est_cost_usd']:.2f}   elapsed {usage['elapsed_s']}s", "dim")
    R.console.print()
    R.print_brief(cap["brief"])
    path = R.write_brief_html(cap["brief"], usage)
    R.line(f"rendered → {path.relative_to(ROOT)}", "dim")
    (ROOT / "out" / "brief.json").write_text(json.dumps({"brief": cap["brief"], "usage": usage}, indent=2))
    return cap["brief"], usage

def run_live() -> tuple[dict, dict]:
    """Real loop. Kept honest and small: the model decides which tools to call and when it is done."""
    import anthropic
    # Prefer a direct Anthropic API key if present; otherwise talk to Claude via
    # Amazon Bedrock using the ambient AWS credentials (default profile / env).
    if os.environ.get("ANTHROPIC_API_KEY"):
        client = anthropic.Anthropic()
        model = "claude-sonnet-4-6"
    else:
        client = anthropic.AnthropicBedrock(aws_region=os.environ.get("AWS_REGION", "us-east-1"))
        model = os.environ.get("BEDROCK_MODEL", "us.anthropic.claude-sonnet-4-6")
    system = (PROMPTS / "system.md").read_text()
    tools = [
        {"name": "read_feedback", "description": "Read the customer feedback CSV.", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
        {"name": "web_search", "description": "Search for external evidence. Returns sources with full text.", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    ]
    goal = "\n\n".join((PROMPTS / f).read_text() for f in ("01_cluster.md", "02_ground.md", "03_synthesize.md"))
    msgs = [{"role": "user", "content": goal}]
    R.banner("FRESHCART ANALYST", "agent run  ·  LIVE")
    t0 = time.time(); usage = {"input_tokens": 0, "output_tokens": 0}
    while True:
        resp = client.messages.create(model=model, max_tokens=4000, system=system, tools=tools, messages=msgs)
        usage["input_tokens"] += resp.usage.input_tokens; usage["output_tokens"] += resp.usage.output_tokens
        msgs.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            break
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                R.step(block.name.upper().replace("_", " "))
                if block.name == "read_feedback":
                    fb = read_feedback(block.input["path"]); out = json.dumps({"rows": fb["rows"], "by_channel": fb["by_channel"], "items": fb["items"][:200]})
                else:
                    out = json.dumps(web_search(block.input["query"]))
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": out})
        msgs.append({"role": "user", "content": results})
    text = "".join(b.text for b in resp.content if b.type == "text")
    usage["elapsed_s"] = round(time.time() - t0, 1)
    usage["est_cost_usd"] = round(usage["input_tokens"] * 3e-6 + usage["output_tokens"] * 15e-6, 2)
    brief = json.loads(text[text.find("{"): text.rfind("}") + 1])
    (ROOT / "out" / "brief.json").write_text(json.dumps({"brief": brief, "usage": usage}, indent=2))
    R.print_brief(brief); R.write_brief_html(brief, usage)
    return brief, usage

def run() -> tuple[dict, dict]:
    return run_demo() if demo_mode() else run_live()
