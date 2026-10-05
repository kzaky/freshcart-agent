# The prompt I started from

This is the prompt I pasted into Claude Code to build the first version of this repo (September 21, 2026). Everything here grew from it over several more Claude Code sessions, so read it as the starting point, not a spec the code still matches line for line. Where the build ended up different:

- **The 62% claim is engineered, not captured.** The prompt asks for a live run where the model drifts on its own. As built, a live run can't reproduce it (see "Why it is deterministic" in the README), so I wrote the failing claim by hand. `fixtures/captured_run.json` says so in its provenance.
- **Timings, tokens and cost in the replay are estimates**, not measurements from a run.
- **No fallback video.** The stage deck carries fallback snapshots on each live slide instead.
- **`deck.py` grew into the slide generator** that also renders the talk's teaching slides.

To build your own, paste it into Claude Code in an empty folder and change the scenario to your data.

```
Build a Python CLI demo agent. Repo name: freshcart-agent. This drives a live stage
demo, so determinism, a polished terminal, and a clean planted-failure beat matter
more than feature breadth.

SCENARIO
FreshCart, a fictional grocery delivery app. The agent turns 90 days of raw customer
feedback into a one-page product brief deciding whether to build "smart substitutions"
next quarter. The dominant complaint is bad item substitutions.

STRUCTURE
- agent.py    : the agent loop (Anthropic API, tool use). Given a goal, it decides which
                tools to call, iterates, and stops when the brief is done.
- tools.py    : read_feedback(path) and web_search(query). web_search MUST support an
                OFFLINE mode reading from fixtures/search_cache.json. Default to offline.
- gate.py     : verification_gate(brief). System prompt forces every web claim to carry
                the EXACT sentence it came from. For each cited claim: re-fetch the source
                from the cache, verify the quoted sentence is present (normalized), and
                verify every numeric token in the claim appears in the source. Internal
                claims (from the CSV) are recomputed from data, not the web. Deterministic,
                not an LLM judge. Return failed claims with reasons.
- prompts/    : system contract plus 4 step prompts (cluster, ground, synthesize, deck).

THE TRAP (hardcode this exactly)
- fixtures/search_cache.json contains three sources:
  1. "Provision Retail Analytics, State of Grocery Delivery 2025" whose only substitution
     figure is: "41% of online grocery shoppers said poor item substitutions led them to
     reduce their order frequency over the past year." It contains NO churn figure, no
     "62", and never names FreshCart.
  2. "InstaFresh Help Center 2025": "Customers can pre-approve a preferred substitute for
     any item before checkout."
  3. "Grocery Dive 2025": neutral delivery-logistics context, texture only.
- The grounding prompt asks for a churn or revenue-impact number with its exact source
  sentence. Because the cache has only a reduced-frequency figure, the agent reliably
  drifts: it synthesizes "62% of FreshCart users churn after a single bad substitution"
  and cites Provision 2025 with an invented supporting sentence.
- Capture ONE such run and store it so DEMO_MODE replays it byte for byte. The captured
  brief must contain BOTH the real 41% claim (cited correctly) and the fabricated 62%
  claim (cited to Provision 2025), so they sit side by side and look identical.
- gate.py must PASS the 41%, the InstaFresh claim, and the recomputed internal count, and
  must FAIL the 62% claim with these reasons printed: quoted sentence not found in source,
  token "62%" not found, token "churn" not found, nearest figure in source 41% reduced
  order frequency. This must be identical every run.

BAR-RAISERS (make the raw terminal look pro, never fragile)
- Use the `rich` library. Colored step banners, a spinner while thinking, per-step timing,
  a running token and est-cost meter.
- Clusters as a rich table ranked by count × severity.
- Visible tool-call trace: READING FEEDBACK, CLUSTERING, GROUNDING, DRAFTING, RUNNING GATE.
- Gate output: a large red FAILED panel naming one verdict and one count, then a large
  green PASSED panel on the clean re-run. Loudest things on screen, readable from the back.
- On pass, write evidence_pack (json + md) listing every claim, its source, and its check
  result. This is the miniature of a real assurance artifact.
- A `make demo` target and a preflight check that verifies the full offline path.

DECK
- deck.py turns an approved brief into a 5-slide markdown deck (robust for live), one
  decision per slide, recommendation on slide 1, speaker notes in a declarative,
  evidence-first voice.

DELIVERABLES THIS PASS
1. Offline golden path runs clean and identical every time via the captured DEMO_MODE run.
2. The trap is present in the captured brief and gate.py fails exactly that one claim.
   README documents exactly why it fails.
3. A workshop/ copy with gate.py stubbed to a TODO for anyone rebuilding at home.
4. A recorded clean golden-path run for the fallback.
5. README: how to run, how to record, where the live-build seam is.

STYLE
Brief content is Amazonian: lead with the decision, active voice, evidence first, no
adjective doing an argument's job. Sections: Problem, Evidence, Options, Recommendation,
Ask.
```

Follow-up prompts I ran after the foundation:
- Generate your teaching slides through `deck.py` from your session outline, so the closing reveal is literally true.
- Generate the one-page trust checklist through the same pipeline.
- Have the gate print the four operator metrics (groundedness, task completion, cost per run, latency) in a summary panel after the PASSED result.
