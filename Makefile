.PHONY: check lint format typecheck test test-min-deps

check: lint format typecheck test

lint:
	ruff check src/

format:
	ruff format --check src/

typecheck:
	mypy src/

test:
	pytest

test-min-deps:
	uv run --with "aiohttp==3.9.0" pytest
