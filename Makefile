.PHONY: check check-live

check:
	uv run black --check .
	uv run ruff check .
	uv run python tools/validate.py
	uv run pytest

check-live:
	uv run pytest tests/test_api_drift.py -v

