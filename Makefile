.PHONY: demo gate fix deck teach preflight capture stage clean all site-slides
export DEMO_MODE ?= 1
demo:      ; python3 -m freshcart_agent demo
gate:      ; python3 -m freshcart_agent gate
fix:       ; python3 -m freshcart_agent fix
deck:      ; python3 -m freshcart_agent deck
teach:     ; python3 -m freshcart_agent teach
capture:   ; DEMO_MODE=0 python3 -m freshcart_agent capture
stage:     ; STAGE=1 python3 -m freshcart_agent preflight
preflight: ; python3 -m freshcart_agent preflight
clean:     ; rm -rf out/*
all: clean demo ; -$(MAKE) gate ; $(MAKE) fix ; $(MAKE) gate ; $(MAKE) deck

# Publish the teaching slides to the website (same renderer; live slides and fallbacks left out).
# Presenter-only: needs a local checkout of the site. Override with SITE=/path/to/site.
SITE ?= $(HOME)/Documents/khaledzaky.com
site-slides: ; @test -d "$(SITE)/public" || { echo "site-slides: $(SITE)/public not found. Set SITE=/path/to/your/site."; exit 1; }
	WEB_OUT="$(SITE)/public/trust/teaching-slides/index.html" python3 -m freshcart_agent teach
