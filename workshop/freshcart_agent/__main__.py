"""CLI.  python -m freshcart_agent [demo|gate|fix|deck|preflight]"""
import json, sys, os
from pathlib import Path
from . import render as R
from .agent import run, ROOT
from .gate import run_gate, metrics
from .deck import build as build_deck, build_teaching

OUT = ROOT / "out"

def _load_brief():
    p = OUT / "brief.json"
    if not p.exists():
        R.line("no brief yet. run: make demo", "red"); sys.exit(1)
    d = json.load(open(p)); return d["brief"], d["usage"]

def cmd_demo():
    run()

def cmd_gate():
    brief, usage = _load_brief()
    R.banner("VERIFICATION GATE", f"checking {len(brief['claims'])} cited claims")
    R.console.print()
    results = run_gate(brief)
    R.print_gate(results)
    R.verdict(results)
    m = metrics(results, usage)
    first = OUT / "gate_first_run.json"
    if all(r.passed for r in results):
        if first.exists():
            f = json.load(open(first))
            m["groundedness"] = f"{f['passed']} of {f['total']} on first run · 1 caught and removed · {len(results)} of {len(results)} now"
        R.write_evidence_pack(results, brief, usage, m)
        R.metrics_panel(m)
        R.line("rendered → out/evidence_pack.html", "dim")
    else:
        flagged = {r.claim_id for r in results if not r.passed}
        first.write_text(json.dumps({"passed": len(results)-len(flagged), "total": len(results)}))
        R.write_brief_html(brief, usage, flagged=flagged)
        R.line("rendered → out/brief.html (failed claims highlighted)", "dim")
        sys.exit(2)

def cmd_fix():
    """Remove the claims the gate failed. This is the 'fix the brief' beat."""
    brief, usage = _load_brief()
    results = run_gate(brief)
    failed = {r.claim_id for r in results if not r.passed}
    if not failed:
        R.done("nothing to fix"); return
    kept = [c for c in brief["claims"] if c["id"] not in failed]
    dropped = [c["text"] for c in brief["claims"] if c["id"] in failed]
    brief["claims"] = kept
    (OUT / "brief.json").write_text(json.dumps({"brief": brief, "usage": usage}, indent=2))
    R.banner("FIX", f"removed {len(dropped)} unsupported claim(s)")
    for d in dropped: R.line(f"[red]−[/] {d}")
    R.write_brief_html(brief, usage)
    R.done("brief updated. re-run: make gate")

def cmd_deck():
    brief, _ = _load_brief()
    R.banner("DECK", "approved brief → 5 slides")
    R.spinner("laying out slides...", 1.4)
    p = build_deck(brief)
    for i, t in enumerate(("The recommendation", "The problem", "The evidence", "The options", "The ask"), 1):
        R.done(f"slide {i}  {t}")
    R.line(f"rendered → {p.relative_to(ROOT)}", "dim")

def cmd_teach():
    R.banner("TEACHING SLIDES", "same generator as the FreshCart deck")
    p = build_teaching(ROOT / "fixtures" / "teaching_slides.json")
    R.done(f"teaching slides → {p.relative_to(ROOT)}")

def cmd_capture():
    from .capture import capture
    sys.exit(capture(int(os.environ.get("ATTEMPTS", "5"))))

def cmd_preflight():
    os.environ["FAST"] = "1"
    checks = []
    def ok(name, cond): checks.append((name, bool(cond))); (R.done if cond else lambda m: R.line(f"[red]✗[/] {m}"))(name)
    R.banner("PREFLIGHT", "verifying the offline golden path")
    ok("fixtures present", (ROOT/"fixtures"/"captured_run.json").exists() and (ROOT/"fixtures"/"search_cache.json").exists())
    ok("data present", (ROOT/"data"/"freshcart_feedback.csv").exists())
    ok("DEMO_MODE offline", os.environ.get("DEMO_MODE","1") != "0")
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        R.console.quiet = True
        brief, usage = run()
        results = run_gate(brief)
        R.console.quiet = False
    failed = [r for r in results if not r.passed]
    ok("brief has 4 claims", len(brief["claims"]) == 4)
    ok("gate fails exactly 1 claim", len(failed) == 1)
    ok("failed claim is the 62% churn claim", failed and "62%" in failed[0].text)
    ok("fail reasons include 'quoted sentence not found'", failed and any("quoted sentence" in x for x in failed[0].reasons))
    ok("nearest-figure hint present (41%)", failed and "41%" in failed[0].note)
    ok("rendered brief written", (OUT/"brief.html").exists())
    prov = json.load(open(ROOT/"fixtures"/"captured_run.json")).get("provenance", {}).get("kind")
    if os.environ.get("STAGE") == "1":
        ok("fixture provenance is honest — 'live' or 'engineered' (STAGE=1 requires it)", prov in ("live", "engineered"))
    else:
        R.line(f"[yellow]note[/] fixture provenance = {prov}. Stage narrative must match: 'live' → 'the model did this on its own'; 'engineered' → 'I engineered a realistic failure'. `STAGE=1 make preflight` enforces one of the two.")
    allok = all(c for _, c in checks)
    R.console.print()
    R.console.print(f"[bold {'green' if allok else 'red'}]{'PREFLIGHT PASSED. Go.' if allok else 'PREFLIGHT FAILED. Do not walk on.'}[/]")
    sys.exit(0 if allok else 1)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "demo"
    {"demo": cmd_demo, "gate": cmd_gate, "fix": cmd_fix, "deck": cmd_deck, "teach": cmd_teach, "capture": cmd_capture, "preflight": cmd_preflight}[cmd]()
