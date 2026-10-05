# Workshop copy

Same agent, same data, same fixtures. One difference: `freshcart_agent/gate.py` is a TODO.

```bash
pip install -r requirements.txt
make demo    # watch the agent produce the brief, lie included
make gate    # fails with NotImplementedError until you build it
```

Build the gate. The rule is at the top of `gate.py`. To build it the way I do on stage, open Claude Code in this folder and paste the prompt in [`LIVE_GATE_PROMPT.md`](LIVE_GATE_PROMPT.md). When yours catches the 62% claim and passes the other three, you've built the part of this system that matters most.
