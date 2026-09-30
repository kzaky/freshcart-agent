# FreshCart Analyst

A demo agent that turns 90 days of raw customer feedback into a one-page product brief, then runs a verification gate that catches the one claim the agent made up.

Built for the BrainStation session **Build an AI Analyst You Can Trust with Claude Code** (Toronto, Oct 5 and Nov 2, 2026).

## Run the whole show

```bash
pip install -r requirements.txt
make preflight     # verifies the offline golden path
make stage         # same, plus refuses unless the fixture provenance is honest ('engineered' or 'live'). Run THIS before you walk on.
make demo          # the agent runs: read, cluster, ground, draft. Brief lands with the lie inside it.
make gate          # FAILS on the 62% claim. Red panel.
make fix           # removes the unsupported claim
make gate          # PASSES. Evidence pack written. Operator metrics shown.
make deck          # approved brief → 5-slide deck
```

Rendered artifacts land in `out/`: `brief.html`, `evidence_pack.html`, `deck.html`. Open them in a browser for the audience. The terminal shows the process, and the browser shows what a human would actually read.

## Why it is deterministic

`DEMO_MODE=1` (default) replays one captured agent run from `fixtures/captured_run.json`, byte for byte, with no network. The gate then runs for real against it.

Provenance matters here. This build ships an **engineered** fixture: I deliberately authored the failing 62% churn claim as a realistic citation drift to demonstrate the gate, so it didn't come from a live model run. `provenance.kind = "engineered"`, and the honest stage line is *"I engineered a realistic failure."* `make stage` accepts `engineered` or `live`, and still refuses a raw unreviewed `authored` placeholder. The gate always runs for real against the replayed brief.

Why engineered instead of live: as shipped, `make capture` can't produce a genuine live drift. `web_search` in `tools.py` always reads the fixed offline cache keyed by exact-string query match, so a live model's own queries miss it and it can cite no web claims (the drift lives in a web claim). Separately, `system.md` tells the model to put a `quote` on every claim and never mentions `recompute`, while `gate.py` requires `recompute` on internal claims, so a live brief crashes the gate. Making capture genuinely live means fixing both (fuzzy-match the search cache; reconcile the prompt/gate schema).

`DEMO_MODE=0` runs a live tool-use loop. It auto-selects the provider: **Amazon Bedrock** (`us.anthropic.claude-sonnet-4-6`, via ambient AWS creds) when `ANTHROPIC_API_KEY` is unset, or the direct Anthropic API when it's set. Same tools, same contract.

`FAST=1` collapses the stage pacing for preflight and recording.

## Why the trap fires

`fixtures/search_cache.json` contains one authoritative-looking report (Provision Retail Analytics 2025) whose only substitution figure is a 41% reduced-order-frequency stat. It contains no churn figure, no "62", and never names FreshCart. The grounding prompt asks for a churn number. With only an adjacent figure available, the model synthesized "62% of FreshCart users churn" and cited the report with an invented supporting sentence. Three real errors at once: number inflation, concept drift, false specificity.

## Why the gate catches it honestly

The system prompt requires every web claim to carry the exact sentence it came from. `gate.py` re-fetches the cited source from the same cache and checks that sentence is present, plus every number in the claim. Real claims pass because their sentence is there. The 62% claim fails because its sentence isn't, and "62%" and "churn" appear nowhere in the source. The gate is ordinary Python with no model in the loop.

## This gate is one eval, not the whole story

`gate.py` is the smallest honest version of the idea: one deterministic check, run once, against one brief. A real system keeps the habit and grows it. You'd want a set of test cases and a suite of checks (completeness, retrieval quality, scope, a regression set), run offline in CI and online in production. A model-as-judge belongs only where plain code can't reach, and even then I'd use it carefully.

The ceiling matters too. A groundedness gate catches a fabricated citation, but it won't catch a real source bent to the wrong conclusion. That's why it stays a suite and a human still signs off.

I've written up the full map at [khaledzaky.com/trust/evals](https://khaledzaky.com/trust/evals): the kinds of evals, when to trust a model to judge, the LLM gotchas I've run into, and the evals you'd run on this exact analyst.

## Layout

```
freshcart_agent/   agent.py (loop)  tools.py (2 tools)  gate.py (the check)  render.py  deck.py
prompts/           system contract + 4 step prompts
data/              freshcart_feedback.csv, 182 synthetic rows
fixtures/          search_cache.json (offline corpus, trap host)  captured_run.json (the replayed run)
workshop/          same repo with gate.py stubbed to a TODO. For rebuilding at home.
out/               rendered artifacts
```
