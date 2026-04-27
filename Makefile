.PHONY: check lint format typecheck test test-min-deps integration

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

# Runs integration tests against a real device. Requires OUMAN_URL,
# OUMAN_USERNAME, OUMAN_PASSWORD env vars. Tests are skipped otherwise.
# -s disables output capture so endpoint dumps stream live for debugging.
integration:
	pytest --override-ini="addopts=" -s -v tests/integration/
