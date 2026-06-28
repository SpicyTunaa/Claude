.PHONY: install dev test lint fmt run resume example clean docker-build docker-up

VENV ?= .venv
PY := $(VENV)/bin/python

install:
	python3 -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

dev: install

test:
	$(PY) -m pytest

lint:
	$(VENV)/bin/ruff check src tests

fmt:
	$(VENV)/bin/ruff check --fix src tests

# Full pass over all enabled sources.
run:
	$(VENV)/bin/leadengine run --once

resume:
	$(VENV)/bin/leadengine resume

# Offline demo: deterministic example source only.
example:
	LEADENGINE_FROZEN_NOW=2026-06-28T12:00:00 $(VENV)/bin/leadengine run --source example

clean:
	rm -rf data output .pytest_cache .ruff_cache

docker-build:
	docker build -t leadengine:latest .

docker-up:
	docker compose up --build
