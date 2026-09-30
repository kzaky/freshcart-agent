"""Turn an approved brief into a deck. One decision per slide. Recommendation first.

Self-contained, full-screen, keyboard-navigable HTML deck (dark, presenter-grade).
Composition and fit are tuned per a design review: centered layout (never left-heavy),
JS scale-to-fit so arbitrary content always fills exactly one screen (never scrolls),
vh-led type, projector-safe contrast, editorial lists, staggered entrance.
Speaker notes are NEVER on the shared slide — they open in a separate window (press S).
The SAME renderer makes the teaching slides and the FreshCart deck (keeps the reveal true).
"""
from __future__ import annotations

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
.body{max-width:40ch;text-align:left;display:flex;flex-direction:column;gap:1rem}
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

.inner.wide{width:min(100%,1320px)}
.inner.wide .body{max-width:none;width:100%;text-align:center}
.qr{display:flex;align-items:center;gap:clamp(1rem,2.6vw,2.2rem);margin-top:.4rem}
.qr .code{background:#fff;border-radius:14px;padding:10px;width:clamp(120px,21vh,230px);aspect-ratio:1;box-shadow:0 0 40px rgba(56,189,248,.18)}
.qr .code svg{display:block;width:100%;height:100%}
.qr .code path{fill:#000}
.qr .url{font-size:clamp(1.1rem,calc(2.2vh + .4vw),2.2rem);font-weight:750;color:var(--ink);letter-spacing:-.01em;text-align:left}
.qr .url small{display:block;font-size:.5em;font-weight:500;color:var(--dim);letter-spacing:.02em;margin-top:.35em}
.cue{margin-top:.6rem;display:inline-flex;align-items:center;gap:.6em;border:1px solid rgba(56,189,248,.45);border-radius:999px;
  padding:.45em 1.1em;font-size:clamp(.85rem,calc(1.4vh + .2vw),1.15rem);font-weight:650;color:var(--accent-2);letter-spacing:.04em}
.cue::before{content:"";width:.55em;height:.55em;border-radius:50%;background:#f43f5e;box-shadow:0 0 12px #f43f5e}
.cols{display:grid;grid-template-columns:repeat(var(--n,2),minmax(0,1fr));gap:clamp(1rem,2.4vw,2rem);width:100%;text-align:left}
.col{border:1px solid var(--line);border-radius:16px;padding:clamp(1rem,2.6vh,1.8rem) clamp(1rem,1.8vw,1.6rem);background:rgba(255,255,255,.03)}
.col .lab{font-size:clamp(.75rem,calc(1.2vh + .2vw),1rem);font-weight:700;letter-spacing:.14em;text-transform:uppercase;margin-bottom:.8em}
.col .txt{font-size:clamp(1.1rem,calc(2vh + .45vw),2rem);line-height:1.35;font-weight:550;color:var(--ink)}
.col.bad{border-color:rgba(244,63,94,.5);background:rgba(244,63,94,.07)} .col.bad .lab{color:#fb7185}
.col.good{border-color:rgba(52,211,153,.45);background:rgba(52,211,153,.06)} .col.good .lab{color:#6ee7b7}
.col.plain .lab{color:var(--accent-2)}
.term{font:500 clamp(.7rem,calc(1.3vh + .25vw),1.08rem)/1.45 ui-monospace,"SF Mono",Menlo,Consolas,monospace;color:#cbd5e1;
  background:#05070c;border:1px solid var(--line);border-radius:14px;padding:1.2em 1.4em;text-align:left;white-space:pre;overflow:hidden;max-width:100%}
.term .ok{color:#6ee7b7} .term .bad{color:#fb7185} .term .hi{color:var(--ink);font-weight:700}
.frame{width:1200px;height:720px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff}
.frame iframe{width:100%;height:100%;border:0;pointer-events:none}
.map{list-style:none;display:flex;flex-direction:column;gap:clamp(.5rem,1.4vh,1rem);width:min(100%,900px);text-align:left;margin-top:.4rem}
.map li{display:grid;grid-template-columns:4.2em 1fr auto;align-items:center;gap:1em;padding:clamp(.7rem,1.8vh,1.2rem) 1.2em;border-radius:14px;border:1px solid transparent;opacity:.42}
.map .n{white-space:nowrap;font-weight:800;font-size:clamp(1.2rem,calc(2.2vh + .4vw),2.2rem);color:var(--accent);font-variant-numeric:tabular-nums}
.map .l{font-weight:720;font-size:clamp(1.2rem,calc(2.3vh + .5vw),2.3rem);color:var(--ink);line-height:1.15}
.map .d{display:block;font-weight:450;font-size:.55em;color:var(--dim);margin-top:.3em}
.map .t{font-size:clamp(.7rem,calc(1.1vh + .2vw),.95rem);font-weight:750;letter-spacing:.14em;text-transform:uppercase;border-radius:999px;padding:.35em .9em;border:1px solid var(--line);color:var(--dim)}
.map .t.live{color:#fda4af;border-color:rgba(244,63,94,.5)}
.map li.done{opacity:.35} .map li.done .n::after{content:" ✓";color:#6ee7b7}
.map li.now{opacity:1;border-color:rgba(56,189,248,.45);background:rgba(56,189,248,.08);box-shadow:0 0 40px rgba(56,189,248,.12)}
.map.all li{opacity:1}
.slide.live > .inner .title{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-weight:700;letter-spacing:-.01em;max-width:none}
.livetag{display:inline-flex;align-items:center;gap:.55em;font-weight:800;letter-spacing:.22em;font-size:clamp(.9rem,calc(1.6vh + .3vw),1.4rem);color:#fda4af}
.livetag::before{content:"";width:.75em;height:.75em;border-radius:50%;background:#f43f5e;box-shadow:0 0 18px #f43f5e;animation:pulse 1.6s ease-in-out infinite}
@keyframes pulse{50%{opacity:.35}}
.fb{position:absolute;inset:0;display:none;place-content:center;justify-items:center;padding:6vh 6vw 11vh;z-index:3;
  background:radial-gradient(90% 70% at 82% 6%,rgba(245,158,11,.10),rgba(245,158,11,0) 55%),linear-gradient(180deg,#0b111c,#080b12)}
.fb.on{display:grid}
.fbin{display:flex;flex-direction:column;align-items:center;text-align:center;gap:clamp(.7rem,2vh,1.4rem);transform-origin:center center}
.fbin .title{max-width:30ch}
.fb .eyebrow{color:#fbbf24} .fb .eyebrow::after{background:linear-gradient(90deg,transparent,#f59e0b,transparent)}
.slide.backup .eyebrow{color:#fbbf24}
.slide.backup .eyebrow::after{background:linear-gradient(90deg,transparent,#f59e0b,transparent)}
"""

DECK_JS = """
(function(){
  var slides=[].slice.call(document.querySelectorAll('.slide'));
  var barin=document.getElementById('barin'), cnt=document.getElementById('cnt'), hint=document.getElementById('hint');
  var i=0, notes=window.__NOTES__||[], titles=window.__TITLES__||[], pop=null, typed='';
  var nums=window.__NUMS__||slides.map(function(_,k){return k+1}), main=Math.max.apply(null,nums.concat([1])), fbi=-1;
  function fbs(){ return slides[i].querySelectorAll('.fb'); }
  function tag(){ return (nums[i] ? String(nums[i]) : 'i'+(i+1)) + (fbi>=0 ? '.'+(fbi+1) : ''); }
  function sync(){ try{ history.replaceState(null,'','#'+tag()); }catch(_){} }
  function fitIn(inner,box){
    inner.style.transform='scale(1)';
    var cs=getComputedStyle(box);
    var aw=box.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight);
    var ah=box.clientHeight-parseFloat(cs.paddingTop)-parseFloat(cs.paddingBottom);
    var r=inner.getBoundingClientRect(), k=Math.min(1,aw/r.width,ah/r.height);
    inner.style.transform=k<1?'scale('+k+')':'scale(1)';
  }
  function showFb(k){
    var f=fbs(); if(!f.length) return false;
    fbi=Math.max(-1,Math.min(f.length-1,k));
    for(var j=0;j<f.length;j++) f[j].classList.toggle('on',j===fbi);
    if(fbi>=0) requestAnimationFrame(function(){ fitIn(f[fbi].querySelector('.fbin'),f[fbi]); });
    label(); sync(); if(pop&&!pop.closed) drawNotes(); return true;
  }
  function label(){
    var f=fbs();
    cnt.textContent = nums[i] ? nums[i]+' / '+main : (fbi>=0 ? 'Fallback '+(fbi+1)+' / '+f.length : 'Live' + (f.length ? '  ·  ↓ fallback' : ''));
  }
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
    [].forEach.call(document.querySelectorAll('.fb.on'),function(e){e.classList.remove('on')}); fbi=-1;
    barin.style.width=((i+1)/slides.length*100)+'%';
    label(); sync();
    requestAnimationFrame(function(){ fit(slides[i]); });
    if(pop&&!pop.closed) drawNotes();
    if(i>0&&hint) hint.classList.add('hide');
  }
  function next(){show(i+1)} function prev(){show(i-1)}
  function refit(){ fit(slides[i]); var f=fbs(); if(fbi>=0&&f[fbi]) fitIn(f[fbi].querySelector('.fbin'),f[fbi]); }
  function fullscreen(){
    var d=document, el=d.documentElement, p;
    try{
      if(!(d.fullscreenElement||d.webkitFullscreenElement)) p=el.requestFullscreen ? el.requestFullscreen() : (el.webkitRequestFullscreen&&el.webkitRequestFullscreen());
      else p=d.exitFullscreen ? d.exitFullscreen() : (d.webkitExitFullscreen&&d.webkitExitFullscreen());
      if(p&&p.catch) p.catch(function(){});
    }catch(_){}
  }
  function onKey(e){
    if(e.metaKey||e.ctrlKey||e.altKey) return;
    if(/^[0-9]$/.test(e.key)){ typed+=e.key; return; }
    if(e.key==='Enter'&&typed){ var t=nums.indexOf(parseInt(typed,10)); if(t>=0) show(t); typed=''; e.preventDefault(); return; }
    typed='';
    if(e.key==='ArrowDown'&&fbs().length){ showFb(fbi+1); e.preventDefault(); }
    else if(e.key==='ArrowUp'&&fbi>=0){ showFb(fbi-1); e.preventDefault(); }
    else if(['ArrowRight','ArrowDown',' ','PageDown'].indexOf(e.key)>=0){next();e.preventDefault();}
    else if(['ArrowLeft','ArrowUp','PageUp'].indexOf(e.key)>=0){prev();e.preventDefault();}
    else if(e.key==='Home'){show(0);} else if(e.key==='End'){show(slides.length-1);}
    else if(e.key==='f'||e.key==='F'){ fullscreen(); }
    else if((e.key==='s'||e.key==='S')&&!window.__NONOTES__){ openNotes(); }
  }
  document.addEventListener('keydown',onKey);
  if(!window.__NOCLICK__) document.addEventListener('click',function(e){ if(e.clientX < window.innerWidth*0.28){prev();} else {next();} });
  window.addEventListener('resize',refit);
  if(document.fonts&&document.fonts.ready){ document.fonts.ready.then(refit); }
  function openNotes(){
    pop=window.open('','spk','width=560,height=680'); if(!pop) return;
    try{ /* keys pressed in the notes window drive the deck too */
      if(pop.__fcKey) pop.document.removeEventListener('keydown',pop.__fcKey);
      pop.__fcKey=onKey; pop.document.addEventListener('keydown',onKey);
    }catch(_){}
    drawNotes();
  }
  function slideLabel(k){ return nums[k] ? 'Slide '+nums[k]+' / '+main : 'Live'; }
  function drawNotes(){
    if(!pop||pop.closed) return;
    var b=pop.document;
    b.title='Speaker notes';
    var nx = i+1<slides.length ? ('<div class=nx>NEXT &middot; '+esc(slideLabel(i+1))+' &middot; '+esc(titles[i+1]||'')+'</div><div class=nb>'+esc(notes[i+1]||'')+'</div>') : '';
    b.body.innerHTML=
      '<style>body{font:16px/1.55 system-ui,sans-serif;color:#0b1220;background:#fff;margin:0}'+
      '.wrap{padding:24px}.tag{color:#0284c7;font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase}'+
      '.tt{font-size:20px;font-weight:700;margin:8px 0 14px}.cur{color:#1f2937;font-size:18px;line-height:1.6}'+
      '.nx{margin-top:22px;color:#94a3b8;font-size:12px;font-weight:700;letter-spacing:.08em}.nb{color:#64748b;font-size:15px;margin-top:6px}</style>'+
      '<div class=wrap><div class=tag>'+esc(slideLabel(i))+(fbi>=0?' &middot; fallback '+(fbi+1):'')+'</div>'+
      '<div class=tt>'+esc(titles[i]||'')+'</div><div class=cur>'+esc(notes[i]||'')+'</div>'+nx+'</div>';
  }
  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function fromHash(){
    var h=(location.hash||'').slice(1), hl=h.charAt(0)==='i'; var hn=parseInt(hl?h.slice(1):h,10)||1;
    show(hl ? hn-1 : Math.max(0,nums.indexOf(hn)));
    var hf=parseInt((h.split('.')[1]||''),10); if(hf) showFb(hf-1);
  }
  fromHash();
  window.addEventListener('hashchange',fromHash);
  if(hint){ setTimeout(function(){hint.classList.add('hide');},4500); }
})();
"""

_NUM = re.compile(r"(\$?\d[\d.,]*%?)")


def _inline(s: str, head_max: int = 24) -> str:
    s = html.escape(s, quote=False)
    if ":" in s and len(s.split(":", 1)[0]) < head_max and not s.startswith("http"):
        head, tail = s.split(":", 1)
        s = f"<strong>{head}:</strong>{tail}"
    return _NUM.sub(r"<span class='num'>\1</span>", s)


def _render_body(body: str) -> str:
    lines = [l for l in body.split("\n") if l.strip()]
    bullets = [l for l in lines if l.lstrip().startswith(("•", "-"))]
    if bullets and len(bullets) == len(lines):
        texts = [l.lstrip("•- ").strip() for l in lines]
        # A list where every item is "Label: text" bolds every label, however long (e.g. the options slide).
        head_max = 48 if all(":" in t and len(t.split(":", 1)[0]) < 48 for t in texts) else 24
        items = "".join(f"<li>{_inline(t, head_max)}</li>" for t in texts)
        return f"<ul>{items}</ul>"
    return "".join(f"<p>{_inline(l.strip())}</p>" for l in lines)


def _term(text: str) -> str:
    out = []
    for line in html.escape(text.rstrip("\n")).split("\n"):
        if "PASS" in line or "✓" in line:
            line = f"<span class='ok'>{line}</span>"
        elif "FAIL" in line or "✗" in line or "not found" in line:
            line = f"<span class='bad'>{line}</span>"
        out.append(line)
    return f"<pre class='term'>{chr(10).join(out)}</pre>"


def _snapshot(f: dict, assets: Path) -> str:
    if f.get("term"):
        return _term((assets / f["term"]).read_text(encoding="utf-8"))
    doc = html.escape((assets / f["frame"]).read_text(encoding="utf-8"), quote=True)
    return f'<div class="frame"><iframe srcdoc="{doc}" tabindex="-1" loading="lazy"></iframe></div>'


def _slide_html(s: dict, num: int | None, n: int, deck_title: str, assets: Path | None,
                parts_map: list | None = None, web: bool = False) -> str:
    """One slide. Optional blocks, in order: body, map, cols, term, frame, qr, cue.

    A "live" slide marks a switch to the terminal. It isn't numbered, and its
    "fallback" snapshots stay hidden until the presenter presses the down arrow.
    """
    backup = s.get("backup", False)
    live = s.get("live", False)
    label = s.get("section") or deck_title
    count = "live" if live else f"{num:02d} / {n:02d}"
    parts = []
    if s.get("body"):
        parts.append(f'<div class="body">{_render_body(s["body"])}</div>')
    if s.get("map") is not None and parts_map:
        cur = s["map"]
        rows = []
        for k, m in enumerate(parts_map, 1):
            state = "now" if k == cur else ("done" if k < cur else "")
            tag = f'<span class="t{" live" if m.get("tag") == "live" else ""}">{html.escape(m["tag"])}</span>' if m.get("tag") else "<span></span>"
            rows.append(f'<li class="{state}"><span class="n">{k:02d}</span>'
                        f'<span class="l">{html.escape(m["label"])}<span class="d">{html.escape(m.get("desc", ""))}</span></span>{tag}</li>')
        parts.append(f'<ol class="map{" all" if cur == 0 else ""}">{"".join(rows)}</ol>')
    if s.get("cols"):
        cards = "".join(
            f'<div class="col {c.get("tone", "plain")}"><div class="lab">{html.escape(c["label"])}</div>'
            f'<div class="txt">{_inline(c["text"])}</div></div>' for c in s["cols"])
        parts.append(f'<div class="cols" style="--n:{3 if len(s["cols"]) == 3 else 2}">{cards}</div>')
    if s.get("term") and assets:
        parts.append(_term((assets / s["term"]).read_text(encoding="utf-8")))
    if s.get("frame") and assets:
        doc = html.escape((assets / s["frame"]).read_text(encoding="utf-8"), quote=True)
        parts.append(f'<div class="frame"><iframe srcdoc="{doc}" tabindex="-1" loading="lazy"></iframe></div>')
    if s.get("qr") and assets and (assets / "qr-trust.svg").exists():
        svg = (assets / "qr-trust.svg").read_text(encoding="utf-8")
        parts.append(f'<div class="qr"><div class="code">{svg}</div>'
                     f'<div class="url">khaledzaky.com/trust<small>{html.escape(s["qr"] if isinstance(s["qr"], str) else "scan to follow along")}</small></div></div>')
    if s.get("cue"):
        parts.append(f'<div class="cue">{html.escape(s["cue"])}</div>')
    wide = " wide" if (s.get("cols") or s.get("term") or s.get("frame") or s.get("map") is not None) else ""
    fbs = ""
    if s.get("fallback") and assets and not web:
        m = len(s["fallback"])
        fbs = "".join(
            f'<div class="fb"><div class="fbin"><div class="eyebrow">Fallback &nbsp;·&nbsp; {k} / {m}</div>'
            f'<h1 class="title">{html.escape(f["title"])}</h1>{_snapshot(f, assets)}</div></div>'
            for k, f in enumerate(s["fallback"], 1))
    head = '<div class="livetag">LIVE</div>' if live else f'<div class="eyebrow">{html.escape(label)} &nbsp;·&nbsp; {count}</div>'
    return (
        f'<section class="slide{" backup" if backup else ""}{" live" if live else ""}">'
        f'<div class="ghost" aria-hidden="true">{"●" if live else f"{num:02d}"}</div>'
        f'<div class="inner{wide}">'
        f'{head}'
        f'<h1 class="title">{html.escape(s["title"])}</h1>'
        f'{"".join(parts)}'
        f'</div>{fbs}</section>'
    )


def _write(title: str, slides: list[dict], out: Path, assets: Path | None = None, web: bool = False,
           parts_map: list | None = None, brand: str | None = None, stage: bool = False) -> Path:
    """Render slides to <out>.html (and <out>.md unless web). Live slides (and their fallbacks) never reach the web copy."""
    if web:
        slides = [s for s in slides if not s.get("live")]
    nums, k = [], 0
    for s in slides:
        k += 0 if s.get("live") else 1
        nums.append(None if s.get("live") else k)
    n = k
    out.parent.mkdir(parents=True, exist_ok=True)

    if not web:
        md = [f"# {title}", ""]
        for s, num in zip(slides, nums):
            md += [f"## {'Live' if num is None else f'Slide {num}'}: {s['title']}", ""]
            if s.get("body"):
                md += [s["body"], ""]
            if s.get("cols"):
                md += [f"- **{c['label']}**: {c['text']}" for c in s["cols"]] + [""]
            md += [f"> Speaker notes: {s.get('notes', '')}", ""]
        out.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")

    sections = [_slide_html(s, num, n, title, assets, parts_map, web) for s, num in zip(slides, nums)]
    labels_js = json.dumps([num or 0 for num in nums])
    # The web copy is public, so it carries no speaker notes. The stage copy ignores
    # clicks: a click to refocus the browser after the terminal shouldn't move the deck.
    notes_js = [json.dumps("" if web else s.get("notes", "")) for s in slides]
    flags = ("window.__NONOTES__=true;" if web else "") + ("window.__NOCLICK__=true;" if stage else "")
    hint = ("&rarr; / space &nbsp;·&nbsp; F fullscreen" if web else
            "&rarr; / space" if stage else "&rarr; / space &nbsp;·&nbsp; F fullscreen &nbsp;·&nbsp; S speaker notes")
    titles_js = [json.dumps(s["title"]) for s in slides]
    icon = "<link rel='icon' type='image/png' href='/favicon.png'>" if web else ""
    doc = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)}</title><meta name='robots' content='noindex'>{icon}"
        f"<style>{DECK_CSS}</style></head><body>"
        f"{''.join(sections)}"
        "<div class='progress'><span id='barin'></span></div>"
        f"<div class='brandmark'>{html.escape(brand or title)}</div>"
        "<div class='count' id='cnt'></div>"
        f"<div class='hint' id='hint'>{hint}</div>"
        f"<script>{flags}window.__NOTES__=[{','.join(notes_js)}];window.__TITLES__=[{','.join(titles_js)}];window.__NUMS__={labels_js};</script>"
        f"<script>{DECK_JS}</script></body></html>"
    )
    out.with_suffix(".html").write_text(doc, encoding="utf-8")
    return out.with_suffix(".html")


def build_teaching(path: Path, web_out: Path | None = None) -> Path:
    """The teaching slides. With web_out, also write the public copy there (HTML only; no live slides, fallbacks or md)."""
    d = json.loads(path.read_text(encoding="utf-8"))
    p = _write(d["title"], d["slides"], OUT / "teaching_slides", assets=path.parent, parts_map=d.get("map"), stage=True)
    if web_out:
        _write(d["title"], d["slides"], web_out.with_suffix(""), assets=path.parent, web=True, parts_map=d.get("map"))
    return p


def build(brief: dict) -> Path:
    OUT.mkdir(exist_ok=True)
    claims = [c for c in brief["claims"] if not c.get("_flagged")]
    slides = [
        ("The recommendation", brief["recommendation"], "Lead with the decision. Everything after this slide is support."),
        ("The problem", brief["problem"], "Say it in the customer's words. One sentence of consequence."),
        ("The evidence", "\n".join(f"• {c['text']}" for c in claims), "Every line here passed the verification gate. Say that out loud."),
        ("The options", "\n".join(f"• {o['name']}: {o['note']}" for o in brief["options"]), "Show you considered do-nothing. It's the credibility slide."),
        ("The ask", brief["ask"], "Specific people, specific quarter, specific outcome. Then stop talking."),
    ]
    return _write(f"{brief['title']} · leadership deck",
                  [{"title": t, "body": b, "notes": nt} for t, b, nt in slides], OUT / "deck", brand=brief["title"])
