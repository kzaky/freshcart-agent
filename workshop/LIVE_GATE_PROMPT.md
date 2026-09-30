# The prompt you paste into Claude Code on stage

Say the rule out loud first. Then paste this. It's specific enough that Claude Code produces a working gate reliably in one pass. To put just the prompt on the clipboard before the show, from `workshop/`: `awk '/^```/{n++;next} n==1' LIVE_GATE_PROMPT.md | pbcopy`. If Claude Code offers to run the gate itself, say no: the first run belongs in front of the room.

```
Implement check_claim() in freshcart_agent/gate.py. Keep everything else in the file as is.

The rule: every fact has to carry the exact sentence it came from, and something has to go back and check that the sentence is really there.

For a claim with kind == "web":
  - fetch the cited source with fetch_source(claim["source"])
  - normalize both the source text and claim["quote"] (lowercase, strip punctuation, collapse whitespace)
  - FAIL with reason "quoted sentence not found in source" if the normalized quote is not a substring of the normalized source text
  - for every number token in claim["text"] (like 41% or 182), FAIL with reason 'token "<tok>" not found in source' if it is not in the source
  - on FAIL, set note to the nearest percentage figure that IS in the source, so the reader sees the real number
  - on PASS, set note to "quote found in <publisher>"

For a claim with kind == "internal":
  - recompute it from the data with recompute_internal(claim["recompute"]) and compare to claim["recompute"]["expect"]
  - never trust the stated count

Return a Result. Ordinary code only. Do not call any model. Do not change the Result dataclass or run_gate/metrics.
Don't run the gate, make, or any tests. I'll run it myself.
```

If Claude Code stalls past 90 seconds, or its version breaks, run this in terminal tab 1 (the backslash skips the `cp -i` alias, which would ask "overwrite?" and default to no):
```
\cp ../freshcart_agent/gate.py freshcart_agent/gate.py
```
and say: "Let me grab the version I wrote earlier." Nobody minds. It's a cooking show.
