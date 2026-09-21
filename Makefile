.PHONY: demo gate fix deck teach preflight capture stage clean all
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
