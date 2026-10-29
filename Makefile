# Open Case · shortcuts to export cases to PDF.
#   make install                      set up the environment (once)
#   make export                       export the sample case in ink-saver mode
#   make export CASE=cases/my-case    export another case
#   make export ARGS="--lang en"      pass any option of export.py (see python3 export.py --help)
#   make color                        same, but in full colour
#   make check                        check the case files without making PDFs
#   make images                       PDFs + one image per evidence sheet to send through a chat
#   make clean                        delete the output/ folder

CASE ?= cases/chupacabras-labranza
ARGS ?=
VENV ?= .venv
PY := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3)

.PHONY: install export color check images clean

install:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/python -m playwright install chromium

export:
	$(PY) export.py $(CASE) $(ARGS)

color:
	$(PY) export.py $(CASE) $(ARGS) --color

check:
	$(PY) export.py $(CASE) $(ARGS) --check

images:
	$(PY) export.py $(CASE) $(ARGS) --images

clean:
	rm -rf output
