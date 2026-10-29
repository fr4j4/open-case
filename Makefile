# Open Case · atajos para exportar casos a PDF.
#   make instalar                     prepara el entorno (una sola vez)
#   make exportar                     exporta el caso de ejemplo en modo ahorro de tinta
#   make exportar CASO=casos/mi-caso  exporta otro caso
#   make color                        lo mismo, pero a todo color
#   make revisar                      revisa los archivos del caso sin generar PDF
#   make imagenes                     PDF + una imagen por prueba para mandar por chat
#   make limpiar                      borra la carpeta salida/

CASO ?= casos/chupacabras-labranza
VENV ?= .venv
PY := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3)

.PHONY: instalar exportar color revisar imagenes limpiar

instalar:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/python -m playwright install chromium

exportar:
	$(PY) exportar.py $(CASO)

color:
	$(PY) exportar.py $(CASO) --color

revisar:
	$(PY) exportar.py $(CASO) --revisar

imagenes:
	$(PY) exportar.py $(CASO) --imagenes

limpiar:
	rm -rf salida
