"""Terminal rendering (rich) and rendered artifacts (HTML/markdown) for the audience."""
import json, time, html
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
console = Console(highlight=False)

def banner(title: str, sub: str = ""):
    t = Text(title, style="bold white")
    if sub: t.append(f"  {sub}", style="dim")
    console.print(Panel(t, box=box.DOUBLE, style="cyan", padding=(0, 2)))

def step(name: str):
    console.print(f"\n[bold cyan]▶ {name}[/]")

def line(msg: str, style: str = ""):
    console.print(f"  {msg}", style=style)

def done(msg: str):
    console.print(f"  [green]✓[/] {msg}")

def spinner(label: str, seconds: float):
    with console.status(f"[dim]{label}[/]", spinner="dots"):
        time.sleep(seconds)

def cluster_table(themes: list[dict]):
    t = Table(title="Themes, ranked by count × severity", box=box.ROUNDED, title_style="bold")
    for col, j in (("#", "right"), ("Theme", "left"), ("Count", "right"), ("Severity", "center"), ("Score", "right")):
        t.add_column(col, justify=j)
    for th in themes:
        sev = {"HIGH": "[bold red]HIGH[/]", "MED": "[yellow]MED[/]", "LOW": "[dim]LOW[/]"}[th["severity"]]
        t.add_row(str(th["rank"]), th["name"], str(th["count"]), sev, str(th["count"] * th["weight"]))
    console.print(t)

def brief_text(brief: dict) -> str:
    cites = {c["id"]: c for c in brief["claims"]}
    lines = [f"# {brief['title']}", "", f"**Recommendation:** {brief['recommendation']}", "", "## Problem", brief["problem"], "", "## Evidence"]
    for c in brief["claims"]:
        lines.append(f"- {c['text']}  [{_cite_label(c)}]")
    lines += ["", "## Options"]
    for o in brief["options"]:
        lines.append(f"- **{o['name']}.** {o['note']}")
    lines += ["", "## Ask", brief["ask"]]
    return "\n".join(lines)

def _cite_label(c: dict) -> str:
    if c["kind"] == "internal": return "internal data, 90 days"
    from .tools import fetch_source
    s = fetch_source(c["source"]) or {}
    return f"{s.get('publisher','?')}, 2025"

def print_brief(brief: dict):
    console.rule("[bold]FreshCart · Smart Substitutions · Product Brief")
    console.print(f"[bold]Recommendation:[/] {brief['recommendation']}\n")
    console.print("[bold]Evidence[/]")
    for c in brief["claims"]:
        console.print(f"  · {c['text']}  [dim]\\[{_cite_label(c)}][/]")
    console.rule()

CSS = """
body{font-family:Georgia,'Iowan Old Style',serif;max-width:720px;margin:48px auto;padding:0 24px;color:#1a1a1a;line-height:1.55;background:#fff}
h1{font-size:30px;margin:0 0 8px;letter-spacing:-.01em}h2{font-size:15px;margin:28px 0 8px;color:#444;font-weight:600}
.rec{font-size:19px;padding:16px 20px;border-left:4px solid #1a1a1a;background:#f6f6f4;margin:16px 0 24px}
li{margin:6px 0}.cite{color:#666;font-size:.9em}.meta{color:#666;font-size:13px;margin-bottom:24px}
.pass{color:#0a7a3b}.fail{color:#b3261e;font-weight:600}
table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:8px;border-bottom:1px solid #e5e5e5;vertical-align:top}th{font-weight:600;font-size:13px;color:#444}
"""

def write_brief_html(brief: dict, usage: dict, path: Path = OUT / "brief.html", flagged: set[str] | None = None):
    OUT.mkdir(exist_ok=True)
    ev = []
    for c in brief["claims"]:
        cls = ' class="fail"' if flagged and c["id"] in flagged else ""
        ev.append(f"<li{cls}>{html.escape(c['text'])} <span class='cite'>[{html.escape(_cite_label(c))}]</span></li>")
    opts = "".join(f"<li><strong>{html.escape(o['name'])}.</strong> {html.escape(o['note'])}</li>" for o in brief["options"])
    doc = f"""<!doctype html><meta charset="utf-8"><title>{html.escape(brief['title'])}</title><style>{CSS}</style>
<h1>{html.escape(brief['title'])}</h1>
<div class="meta">Product brief · generated in {usage['elapsed_s']:.0f}s · est. cost ${usage['est_cost_usd']:.2f}</div>
<div class="rec"><strong>Recommendation.</strong> {html.escape(brief['recommendation'])}</div>
<h2>Problem</h2><p>{html.escape(brief['problem'])}</p>
<h2>Evidence</h2><ul>{''.join(ev)}</ul>
<h2>Options</h2><ul>{opts}</ul>
<h2>Ask</h2><p>{html.escape(brief['ask'])}</p>"""
    path.write_text(doc)
    (OUT / "brief.md").write_text(brief_text(brief))
    return path

def print_gate(results, verdict_only=False):
    for r in results:
        if r.passed:
            console.print(f"  [green]✓ PASS[/]  {r.text}")
            if not verdict_only: console.print(f"          [dim]{r.note}[/]")
        else:
            console.print(f"  [bold red]✗ FAIL[/]  {r.text}")
            console.print(f"          [dim]cited: {r.source}[/]")
            for reason in r.reasons: console.print(f"          [red]→ {reason}[/]")
            if r.note: console.print(f"          [yellow]{r.note}[/]")
        console.print()

def verdict(results):
    n = len(results); p = sum(r.passed for r in results)
    if p == n:
        console.print(Panel(Text.assemble(("✓  GATE PASSED", "bold white"), (f"  ·  {p} of {n} claims supported\n", "white"),
                            ("evidence_pack.md written · brief cleared to ship", "white")), style="bold green", box=box.DOUBLE, padding=(0, 2)))
    else:
        console.print(Panel(Text.assemble(("✗  GATE FAILED", "bold white"), (f"  ·  {n-p} of {n} claims unsupported\n", "white"),
                            ("brief blocked. not ready to ship.", "white")), style="bold red", box=box.DOUBLE, padding=(0, 2)))

def metrics_panel(m: dict):
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="bold"); t.add_column()
    t.add_row("Groundedness", m["groundedness"]); t.add_row("Completion", m["completion"])
    t.add_row("Cost per run", m["cost_per_run"]); t.add_row("Latency", m["latency"])
    console.print(Panel(t, title="[bold]Operator metrics[/]", box=box.ROUNDED, style="blue"))

def write_evidence_pack(results, brief: dict, usage: dict, m: dict):
    OUT.mkdir(exist_ok=True)
    rows = []
    for r in results:
        rows.append({"claim_id": r.claim_id, "claim": r.text, "source": r.source, "passed": r.passed, "reasons": r.reasons, "note": r.note})
    (OUT / "evidence_pack.json").write_text(json.dumps({"brief": brief["title"], "usage": usage, "metrics": m, "claims": rows}, indent=2))
    md = ["# Evidence pack", f"Brief: {brief['title']}", "", "| Claim | Source | Result | Note |", "|---|---|---|---|"]
    for r in rows:
        res = "PASS" if r["passed"] else "FAIL: " + "; ".join(r["reasons"])
        md.append(f"| {r['claim']} | {r['source']} | {res} | {r['note']} |")
    md += ["", "## Operator metrics"] + [f"- {k}: {v}" for k, v in m.items()]
    (OUT / "evidence_pack.md").write_text("\n".join(md))
    trs = "".join(f"<tr><td>{html.escape(r['claim'])}</td><td>{html.escape(r['source'])}</td><td class='{'pass' if r['passed'] else 'fail'}'>{'PASS' if r['passed'] else 'FAIL'}</td><td>{html.escape('; '.join(r['reasons']) or r['note'])}</td></tr>" for r in rows)
    mets = "".join(f"<li><strong>{k.replace('_',' ').title()}</strong>: {v}</li>" for k, v in m.items())
    (OUT / "evidence_pack.html").write_text(f"<!doctype html><meta charset='utf-8'><title>Evidence pack</title><style>{CSS}</style><h1>Evidence pack</h1><div class='meta'>{html.escape(brief['title'])}</div><table><tr><th>Claim</th><th>Source</th><th>Result</th><th>Note</th></tr>{trs}</table><h2>Operator metrics</h2><ul>{mets}</ul>")
