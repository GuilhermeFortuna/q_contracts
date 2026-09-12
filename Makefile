.PHONY: check

check:
	uv run black --check .
	uv run ruff check .
	uv run python tools/validate.py
	uv run pytest
