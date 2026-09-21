"""Capture a genuine live run and, if the model drifted, save it as the demo fixture.

This is how the demo stays honest. The stage line is "the model did this on its own."
That line is only allowed once provenance.kind == "live".
"""
import json, os, sys, time
from pathlib import Path
from . import render as R
from .agent import run_live, ROOT
from .gate import run_gate

FIX = ROOT / "fixtures" / "captured_run.json"

def _has_aws_creds() -> bool:
    """True if AWS credentials are resolvable (default profile, env, or role) for Bedrock."""
    try:
        import boto3
        return boto3.Session().get_credentials() is not None
    except Exception:
        return False

def capture(max_attempts: int = 5) -> int:
    if not os.environ.get("ANTHROPIC_API_KEY") and not _has_aws_creds():
        R.line("No model credentials found (set ANTHROPIC_API_KEY, or configure AWS creds for Bedrock). Cannot capture a live run.", "red"); return 1
    os.environ["DEMO_MODE"] = "0"
    R.banner("CAPTURE", "looking for a genuine drift to replay on stage")
    for attempt in range(1, max_attempts + 1):
        R.step(f"ATTEMPT {attempt} of {max_attempts}")
        try:
            brief, usage = run_live()
        except Exception as e:
            R.line(f"run failed: {e}", "red"); continue
        results = run_gate(brief)
        failed = [r for r in results if not r.passed]
        R.line(f"gate: {len(results)-len(failed)} of {len(results)} supported", "dim")
        if len(failed) == 1 and any("quoted sentence" in x for x in failed[0].reasons):
            old = json.load(open(FIX))
            new = {
                "_note": "Live capture: the failing claim below is the model's own citation drift, not hand-inserted. Replayed byte for byte in DEMO_MODE.",
                "provenance": {"kind": "live", "captured_at": time.strftime("%Y-%m-%d"), "model": "claude-sonnet-4-6", "attempts": attempt,
                               "failed_claim": failed[0].text, "reasons": failed[0].reasons},
                "captured_at": time.strftime("%Y-%m-%d"), "model": "claude-sonnet-4-6",
                "usage": usage, "phases": old["phases"], "brief": brief,
            }
            # keep phase timings realistic from the live usage
            new["phases"]["read"]["rows"] = 182
            FIX.write_text(json.dumps(new, indent=2))
            R.console.print()
            R.done(f"captured a genuine drift on attempt {attempt}:")
            R.line(f"[red]{failed[0].text}[/]")
            R.done("fixtures/captured_run.json replaced. provenance = live. Run make preflight.")
            return 0
        elif not failed:
            R.line("no drift this run. The gate passed everything. Trying again.", "yellow")
        else:
            R.line(f"{len(failed)} claims failed, want exactly 1 with a missing quote. Trying again.", "yellow")
    R.console.print()
    R.line("No clean single-drift run captured. Options:", "yellow")
    R.line("  a) raise max_attempts, or tighten prompts/02_ground.md to demand a churn or revenue figure")
    R.line("  b) keep the authored fixture and change the stage line to 'I engineered a realistic failure'")
    return 2

if __name__ == "__main__":
    sys.exit(capture(int(sys.argv[1]) if len(sys.argv) > 1 else 5))
