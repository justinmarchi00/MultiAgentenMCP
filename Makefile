.PHONY: setup setup-metagpt setup-all run cli mcp-inspector mcp-http test lint check clean

PYTHON ?= python3.11

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"

setup-metagpt:
	$(PYTHON) scripts/setup_metagpt.py

setup-all: setup setup-metagpt

run:
	.venv/bin/streamlit run streamlit_app.py

cli:
	.venv/bin/orderflow-demo --scenario normal

mcp-inspector:
	.venv/bin/mcp dev src/orderflow/mcp_server.py

mcp-http:
	.venv/bin/mcp run src/orderflow/mcp_server.py --transport streamable-http

test:
	.venv/bin/pytest --cov=orderflow --cov-report=term-missing

lint:
	.venv/bin/ruff check .

check: lint test

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +

