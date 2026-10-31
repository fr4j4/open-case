# Open Case · shortcuts to export cases to PDF.
#   make install                      set up the environment (once)
#   make export                       export the sample case in ink-saver mode
#   make export CASE=cases/my-case    export another case
#   make export ARGS="--lang en"      pass any option of export.py (see python3 export.py --help)
#   make color                        same, but in full colour
#   make check                        check the case files without making PDFs
#   make signatures                   draw the pen strokes of the signers that have none (cases/<case>/signatures.yaml)
#   make images                       PDFs + one image per evidence sheet to send through a chat
#   make export ARGS="--teams 2"      material for the first 2 teams only (the print plan counts 2 copies)
#   make export ARGS="--chat"         the Evidence file goes through the chat: 0 copies in the plan, images made
#   make print-check                  every PDF has the pages of the print plan and every sheet has room (as the CI)
#   make site                         build the website in _site/ (PDFs, zips, cases.json and the page)
#   make test                         run the tests (HTML photos, strings, validation)
#   make test-update                  rewrite the HTML photos in tests/snapshots/ after an intended change
#   make lint                         run the skill's case_lint.py on every case
#   make snapshot REF=development     text, pages and HTML of every document at a git ref (default: working tree)
#   make compare BASE=development     what changes in the PDFs from BASE to HEAD (default: working tree)
#   make clean                        delete the output/ folder and the snapshots

CASE ?= cases/chupacabras-labranza
ARGS ?=
REF ?=
BASE ?= development
HEAD ?=
VENV ?= .venv
PY := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3)

.PHONY: install export color check signatures images site test test-update lint print-check snapshot compare clean

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

signatures:
	$(PY) tools/signatures.py $(CASE) $(ARGS)

images:
	$(PY) export.py $(CASE) $(ARGS) --images

site:
	$(PY) -m opencase.site $(ARGS)

test:
	$(PY) -m pytest

test-update:
	$(PY) -m pytest tests/test_html_snapshots.py --update-snapshots

lint:
	@for case in cases/*/; do echo "== $$case"; $(PY) skills/open-case-author/scripts/case_lint.py $$case || exit 1; done

print-check:
	$(PY) tools/check_print.py $(ARGS)

snapshot:
	$(PY) tools/snapshot.py take $(REF)

compare:
	$(PY) tools/snapshot.py compare $(BASE) $(HEAD) $(ARGS)

clean:
	rm -rf output _site _preview .site-work .snapshots

# Web (phase F0): serve the site over an HTTPS tunnel (cloudflared) to try it on phones.
#   make web-preview                  build the light site, serve it and open the tunnel; prints the URLs
#   make web-preview ARGS="--no-tunnel --port 9000"
.PHONY: web-preview
web-preview:
	$(PY) tools/web_preview.py $(ARGS)
