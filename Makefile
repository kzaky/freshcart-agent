.PHONY: demo gate fix deck teach preflight capture stage clean all site-slides reset
export DEMO_MODE ?= 1
# Use the project venv when present so `make` works without activating it first.
PY ?= $(if $(VIRTUAL_ENV),python3,$(if $(wildcard .venv/bin/python),.venv/bin/python,python3))
demo:      ; $(PY) -m freshcart_agent demo
gate:      ; $(PY) -m freshcart_agent gate
fix:       ; $(PY) -m freshcart_agent fix
deck:      ; $(PY) -m freshcart_agent deck
teach:     ; $(PY) -m freshcart_agent teach
capture:   ; DEMO_MODE=0 $(PY) -m freshcart_agent capture
stage:     ; STAGE=1 $(PY) -m freshcart_agent preflight
preflight: ; $(PY) -m freshcart_agent preflight
clean:     ; rm -rf out/*
# The show runs from workshop/; this resets that copy from here too (discards edits to workshop/freshcart_agent/gate.py).
reset:     ; $(MAKE) -C workshop reset
all: clean demo ; -$(MAKE) gate ; $(MAKE) fix ; $(MAKE) gate ; $(MAKE) deck

# Publish the teaching slides to the website (same renderer; live slides and fallbacks left out).
# Presenter-only: needs a local checkout of the site. Override with SITE=/path/to/site.
SITE ?= $(HOME)/Documents/khaledzaky.com
site-slides: ; @test -d "$(SITE)/public" || { echo "site-slides: $(SITE)/public not found. Set SITE=/path/to/your/site."; exit 1; }
	WEB_OUT="$(SITE)/public/trust/teaching-slides/index.html" $(PY) -m freshcart_agent teach
