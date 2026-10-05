.PHONY: demo gate fix deck teach preflight capture stage clean all reset
export DEMO_MODE ?= 1
# Use the project venv (../.venv) when present so `make` works without activating it first.
PY ?= $(if $(VIRTUAL_ENV),python3,$(firstword $(wildcard ../.venv/bin/python .venv/bin/python) python3))
demo:      ; $(PY) -m freshcart_agent demo
gate:      ; $(PY) -m freshcart_agent gate
fix:       ; $(PY) -m freshcart_agent fix
deck:      ; $(PY) -m freshcart_agent deck
teach:     ; $(PY) -m freshcart_agent teach
capture:   ; DEMO_MODE=0 $(PY) -m freshcart_agent capture
stage:     ; STAGE=1 $(PY) -m freshcart_agent preflight
preflight: ; $(PY) -m freshcart_agent preflight
clean:     ; rm -rf out/*
all: clean demo ; -$(MAKE) gate ; $(MAKE) fix ; $(MAKE) gate ; $(MAKE) deck

# Presenter reset after a rehearsal. DISCARDS your edits to gate.py (back to the stub),
# then rebuilds the pre-show outputs: the clean brief and the slides.
reset:     ; git checkout -- freshcart_agent/gate.py ; $(MAKE) clean demo teach
