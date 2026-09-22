"""Turn an approved brief into a deck. One decision per slide. Recommendation first.

Self-contained, full-screen, keyboard-navigable HTML deck (dark, presenter-grade).
Composition and fit are tuned per a design review: centered layout (never left-heavy),
JS scale-to-fit so arbitrary content always fills exactly one screen (never scrolls),
vh-led type, projector-safe contrast, editorial lists, staggered entrance.
Speaker notes are NEVER on the shared slide — they open in a separate window (press S).
The SAME renderer makes the teaching slides and the FreshCart deck (keeps the reveal true).
"""
import html, json, re
from pathlib import Path
from .render import OUT

DECK_CSS = """
:root{
  --font:ui-sans-serif,system-ui,-apple-system,"SF Pro Display","Segoe UI Variable Display","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --bg:#080b12; --ink:#f4f7fb; --body:#dfe6f1; --dim:#9aa6bb;
  --accent:#38bdf8; --accent-2:#7dd3fc; --num:#8fe0ff; --line:rgba(255,255,255,.10);
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  font-family:var(--font);background:var(--bg);color:var(--ink);overflow:hidden;
  -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
  text-rendering:optimizeLegibility;font-optical-sizing:auto;
}
.slide{
  position:absolute;inset:0;display:none;place-content:center;justify-items:center;
  padding:8vh 8vw;overflow:hidden;
  background:
    radial-gradient(90% 70% at 82% 6%, rgba(56,189,248,.14), rgba(56,189,248,0) 55%),
    radial-gradient(80% 70% at 8% 96%, rgba(14,165,233,.12), rgba(14,165,233,0) 55%),
    radial-gradient(130% 120% at 50% 50%, transparent 58%, rgba(0,0,0,.5)),
    linear-gradient(180deg,#0b111c,#080b12);
}
.slide.active{display:grid}
.ghost{
  position:absolute;right:5.5%;top:2%;z-index:0;font-size:46vh;font-weight:850;line-height:1;
  color:#fff;opacity:.035;letter-spacing:-.04em;font-variant-numeric:tabular-nums;
  pointer-events:none;user-select:none;
}
.inner{
  position:relative;z-index:1;width:min(100%,1000px);
  display:flex;flex-direction:column;align-items:center;text-align:center;
  gap:clamp(.9rem,2.4vh,1.7rem);transform-origin:center center;will-change:transform;
}
.eyebrow{
  font-weight:600;font-size:clamp(.8rem,calc(1.5vh + .2vw),1.05rem);letter-spacing:.18em;
  text-transform:uppercase;color:var(--accent-2);position:relative;padding-bottom:.75em;
}
.eyebrow::after{content:"";position:absolute;left:50%;bottom:0;transform:translateX(-50%);
  width:2.4rem;height:2px;border-radius:2px;background:linear-gradient(90deg,transparent,var(--accent),transparent)}
h1.title{
  font-weight:720;font-size:clamp(2rem,calc(3.8vh + 1vw),4.6rem);line-height:1.03;
  letter-spacing:-.025em;max-width:16ch;color:var(--ink);text-wrap:balance;
}
.body{max-width:36ch;text-align:left;display:flex;flex-direction:column;gap:1rem}
.body p{font-size:clamp(1.15rem,calc(1.9vh + .4vw),1.95rem);line-height:1.5;font-weight:450;color:var(--body);text-wrap:pretty}
.body p:first-child{color:var(--ink);font-weight:500}
.body ul{list-style:none;display:flex;flex-direction:column;gap:clamp(.7rem,1.7vh,1.3rem);counter-reset:b;max-width:42ch}
.body li{
  position:relative;padding:0 0 clamp(.7rem,1.6vh,1.2rem) 2.6em;border-bottom:1px solid var(--line);
  font-size:clamp(1.05rem,calc(1.7vh + .35vw),1.7rem);line-height:1.34;font-weight:500;color:#e8edf6;
}
.body li:last-child{border-bottom:0;padding-bottom:0}
.body li::before{counter-increment:b;content:counter(b,decimal-leading-zero);position:absolute;left:0;top:.02em;
  font-weight:800;font-size:.8em;color:var(--accent);font-variant-numeric:tabular-nums}
.body strong{color:var(--ink);font-weight:750}
.num{color:var(--num);font-weight:800;font-variant-numeric:tabular-nums;text-shadow:0 0 22px rgba(56,189,248,.35)}

.slide.active .eyebrow{animation:rise .5s .04s cubic-bezier(.2,.7,.2,1) both}
.slide.active .title{animation:rise .5s .11s cubic-bezier(.2,.7,.2,1) both}
.slide.active .body{animation:rise .5s .19s cubic-bezier(.2,.7,.2,1) both}
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@media(prefers-reduced-motion:reduce){.slide.active *{animation:none!important}}

.progress{position:fixed;left:5vw;right:5vw;bottom:4.4vh;height:3px;border-radius:2px;background:rgba(255,255,255,.1);z-index:5}
.progress>span{display:block;height:100%;border-radius:2px;background:linear-gradient(90deg,var(--accent),#0ea5e9);box-shadow:0 0 16px rgba(56,189,248,.5);transition:width .5s ease}
.count{position:fixed;right:5vw;bottom:5.6vh;font-size:14px;font-weight:600;color:var(--dim);letter-spacing:.05em;font-variant-numeric:tabular-nums;z-index:5}
.brandmark{position:fixed;left:5vw;bottom:5.6vh;font-size:12.5px;font-weight:700;color:#6b7688;letter-spacing:.04em;z-index:5}
.hint{position:fixed;left:50%;transform:translateX(-50%);bottom:5.6vh;font-size:12px;color:#5b6678;font-weight:500;z-index:5;transition:opacity .5s}
.hint.hide{opacity:0;pointer-events:none}
::-webkit-scrollbar{width:0;height:0}
"""

DECK_JS = """
(function(){
  var slides=[].slice.call(document.querySelectorAll('.slide'));
  var barin=document.getElementById('barin'), cnt=document.getElementById('cnt'), hint=document.getElementById('hint');
  var i=0, notes=window.__NOTES__||[], titles=window.__TITLES__||[], pop=null;
  function fit(s){
    if(!s) return;
    var inner=s.querySelector('.inner'); if(!inner) return;
    inner.style.transform='scale(1)';
    var cs=getComputedStyle(s);
    var aw=s.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    var ah=s.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
    var r=inner.getBoundingClientRect();
    var k=Math.min(1, aw/r.width, ah/r.height);
    inner.style.transform = k<1 ? 'scale('+k+')' : 'scale(1)';
  }
  function show(n){
    i=Math.max(0,Math.min(slides.length-1,n));
    for(var k=0;k<slides.length;k++){ slides[k].classList.toggle('active',k===i); }
    barin.style.width=((i+1)/slides.length*100)+'%';
    cnt.textContent=(i+1)+' / '+slides.length;
    requestAnimationFrame(function(){ fit(slides[i]); });
    if(pop&&!pop.closed) drawNotes();
    if(i>0&&hint) hint.classList.add('hide');
  }
  function next(){show(i+1)} function prev(){show(i-1)}
  document.addEventListener('keydown',function(e){
    if(['ArrowRight','ArrowDown',' ','PageDown'].indexOf(e.key)>=0){next();e.preventDefault();}
    else if(['ArrowLeft','ArrowUp','PageUp'].indexOf(e.key)>=0){prev();e.preventDefault();}
    else if(e.key==='Home'){show(0);} else if(e.key==='End'){show(slides.length-1);}
    else if(e.key==='f'||e.key==='F'){ if(!document.fullscreenElement){ (document.documentElement.requestFullscreen||function(){})(); } else { (document.exitFullscreen||function(){})(); } }
    else if(e.key==='s'||e.key==='S'){ openNotes(); }
  });
  document.addEventListener('click',function(e){ if(e.clientX < window.innerWidth*0.28){prev();} else {next();} });
  window.addEventListener('resize',function(){ fit(slides[i]); });
  if(document.fonts&&document.fonts.ready){ document.fonts.ready.then(function(){ fit(slides[i]); }); }
  function openNotes(){ pop=window.open('','spk','width=560,height=680'); if(pop){ drawNotes(); } }
  function drawNotes(){
    if(!pop||pop.closed) return;
    var b=pop.document;
    b.title='Speaker notes';
    var nx = notes[i+1] ? ('<div class=nx>NEXT &middot; '+esc(titles[i+1]||'')+'</div><div class=nb>'+esc(notes[i+1])+'</div>') : '';
    b.body.innerHTML=
      '<style>body{font:16px/1.55 system-ui,sans-serif;color:#0b1220;background:#fff;margin:0}'+
      '.wrap{padding:24px}.tag{color:#0284c7;font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase}'+
      '.tt{font-size:20px;font-weight:700;margin:8px 0 14px}.cur{color:#1f2937;font-size:18px;line-height:1.6}'+
      '.nx{margin-top:22px;color:#94a3b8;font-size:12px;font-weight:700;letter-spacing:.08em}.nb{color:#64748b;font-size:15px;margin-top:6px}</style>'+
      '<div class=wrap><div class=tag>Slide '+(i+1)+' / '+slides.length+'</div>'+
      '<div class=tt>'+esc(titles[i]||'')+'</div><div class=cur>'+esc(notes[i]||'')+'</div>'+nx+'</div>';
  }
  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  show(0);
  if(hint){ setTimeout(function(){hint.classList.add('hide');},4500); }
})();
"""

_NUM = re.compile(r"(\$?\d[\d.,]*%?)")


def _inline(s: str) -> str:
    s = html.escape(s)
    if ":" in s and len(s.split(":", 1)[0]) < 24 and not s.startswith("http"):
        head, tail = s.split(":", 1)
        s = f"<strong>{head}:</strong>{tail}"
    return _NUM.sub(r"<span class='num'>\1</span>", s)


def _render_body(body: str) -> str:
    lines = [l for l in body.split("\n") if l.strip()]
    bullets = [l for l in lines if l.lstrip().startswith(("•", "-"))]
    if bullets and len(bullets) == len(lines):
        items = "".join(f"<li>{_inline(l.lstrip('•- ').strip())}</li>" for l in lines)
        return f"<ul>{items}</ul>"
    return "".join(f"<p>{_inline(l.strip())}</p>" for l in lines)


def _write(title: str, slides: list[tuple], out_name: str) -> Path:
    OUT.mkdir(exist_ok=True)
    n = len(slides)
    md = [f"# {title}", ""]
    for i, (t, body, notes) in enumerate(slides, 1):
        md += [f"## Slide {i}: {t}", "", body, "", f"> Speaker notes: {notes}", ""]
    (OUT / f"{out_name}.md").write_text("\n".join(md))

    sections, notes_js, titles_js = [], [], []
    for i, (t, body, notes) in enumerate(slides, 1):
        sections.append(
            f'<section class="slide">'
            f'<div class="ghost" aria-hidden="true">{i:02d}</div>'
            f'<div class="inner">'
            f'<div class="eyebrow">{html.escape(title)} &nbsp;·&nbsp; {i:02d} / {n:02d}</div>'
            f'<h1 class="title">{html.escape(t)}</h1>'
            f'<div class="body">{_render_body(body)}</div>'
            f'</div></section>'
        )
        notes_js.append(json.dumps(notes))
        titles_js.append(json.dumps(t))

    doc = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)}</title><meta name='robots' content='noindex'>"
        f"<style>{DECK_CSS}</style></head><body>"
        f"{''.join(sections)}"
        "<div class='progress'><span id='barin'></span></div>"
        "<div class='brandmark'>Build an AI Analyst You Can Trust</div>"
        "<div class='count' id='cnt'></div>"
        "<div class='hint' id='hint'>&rarr; / space &nbsp;·&nbsp; F fullscreen &nbsp;·&nbsp; S speaker notes</div>"
        f"<script>window.__NOTES__=[{','.join(notes_js)}];window.__TITLES__=[{','.join(titles_js)}];</script>"
        f"<script>{DECK_JS}</script></body></html>"
    )
    (OUT / f"{out_name}.html").write_text(doc)
    return OUT / f"{out_name}.html"


def build_teaching(path: Path) -> Path:
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
