VENV := venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip

.PHONY: help install run clean

help:
	@echo "=========================================="
	@echo " Discord Server Manager "
	@echo "=========================================="
	@echo "  make install  - Create venv & install dependencies"
	@echo "  make run      - Run the Discord bot"
	@echo "  make clean    - Remove venv and Python cache"
	@echo "=========================================="

install:
	python3 -m venv $(VENV)
	. $(VENV)/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "Installation finished! Remember to setup your .env file."

run:
	. $(VENV)/bin/activate && PYTHONPATH=src python src/main.py

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
