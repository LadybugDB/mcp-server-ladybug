.PHONY: install dev lint test clean

install:
	uv pip install -e .

dev:
	python -m mcp_server_ladybug --db-path :memory:

lint:
	ruff check src/

test:
	pytest tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf .venv/
