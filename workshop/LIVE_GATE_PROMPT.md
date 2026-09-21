# The prompt you paste into Claude Code on stage

Say the rule out loud first. Then paste this. It is specific enough that Claude Code produces a working gate reliably in one pass.

```
Implement check_claim() in freshcart_agent/gate.py. Keep everything else in the file as is.

The rule: every fact has to carry the exact sentence it came from, and something has to go back and check that the sentence is really there.

For a claim with kind == "web":
  - fetch the cited source with fetch_source(claim["source"])
  - normalize both the source text and claim["quote"] (lowercase, strip punctuation, collapse whitespace)
  - FAIL with reason "quoted sentence not found in source" if the normalized quote is not a substring of the normalized source text
  - for every number token in claim["text"] (like 41% or 182), FAIL with reason 'token "<tok>" not found in source' if it is not in the source
  - if the claim mentions "churn" and the source does not, add reason 'token "churn" not found in source'
  - on FAIL, set note to the nearest percentage figure that IS in the source, so the reader sees the real number
  - on PASS, set note to "quote found in <publisher>"

For a claim with kind == "internal":
  - recompute it from the data with recompute_internal(claim["recompute"]) and compare to claim["recompute"]["expect"]
  - never trust the stated count

Return a Result. Ordinary code only. Do not call any model. Do not change the Result dataclass or run_gate/metrics.
```

If Claude Code stalls past 90 seconds, or its version breaks:
```
cp ../freshcart_agent/gate.py freshcart_agent/gate.py
```
and say: "Let me grab the version I wrote earlier." Nobody minds. It is a cooking show.
