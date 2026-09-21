"""Turn an approved brief into a 5-slide deck. One decision per slide. Recommendation first."""
import html, json
from pathlib import Path
from .render import CSS, OUT

def _write(title: str, slides: list[tuple], out_name: str) -> Path:
    n = len(slides)
    md = [f"# {title}", ""]; sec = []
    for i, (t, body, notes) in enumerate(slides, 1):
        md += [f"## Slide {i}: {t}", "", body, "", f"> Speaker notes: {notes}", ""]
        sec.append(f"<section><div class='n'>Slide {i} of {n}</div><h1>{html.escape(t)}</h1><p>{html.escape(body).replace(chr(10),'<br>')}</p><div class='notes'>Speaker notes: {html.escape(notes)}</div></section>")
    (OUT / f"{out_name}.md").write_text("\n".join(md))
    (OUT / f"{out_name}.html").write_text(f"""<!doctype html><meta charset='utf-8'><title>{html.escape(title)}</title><style>{CSS}
body{{max-width:none;margin:0;padding:0;background:#e9e9e6}}section{{background:#fff;min-height:70vh;margin:24px auto;max-width:900px;padding:56px 64px;box-shadow:0 2px 12px rgba(0,0,0,.08);position:relative}}
section h1{{font-size:40px;margin:8px 0 24px}}section p{{font-size:22px;line-height:1.5}}.n{{color:#888;font-size:13px}}.notes{{position:absolute;bottom:20px;left:64px;right:64px;color:#777;font-size:14px;border-top:1px solid #eee;padding-top:10px}}
@media print{{section{{page-break-after:always;box-shadow:none;margin:0;min-height:0}}}}</style>{''.join(sec)}""")
    return OUT / f"{out_name}.html"

def build_teaching(path: Path) -> Path:
    """The three teaching slides, through the same generator as the FreshCart deck. That is what makes the reveal true."""
    d = json.load(open(path))
    return _write(d["title"], [(s["title"], s["body"], s["notes"]) for s in d["slides"]], "teaching_slides")

def build(brief: dict) -> Path:
    OUT.mkdir(exist_ok=True)
    claims = [c for c in brief["claims"] if not c.get("_flagged")]
    slides = [
        ("The recommendation", brief["recommendation"], "Lead with the decision. Everything after this slide is support."),
        ("The problem", brief["problem"], "Say it in the customer's words. One sentence of consequence."),
        ("The evidence", "\n".join(f"• {c['text']}" for c in claims), "Every line here passed the verification gate. Say that out loud."),
        ("The options", "\n".join(f"• {o['name']}: {o['note']}" for o in brief["options"]), "Show you considered do-nothing. It is the credibility slide."),
        ("The ask", brief["ask"], "Specific people, specific quarter, specific outcome. Then stop talking."),
    ]
    return _write(f"{brief['title']}: leadership deck", slides, "deck")
