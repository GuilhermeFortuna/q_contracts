.PHONY: check check-live generate-check hooks

check: generate-check
	uv run black --check .
	uv run ruff check .
	uv run python tools/validate.py
	uv run pytest

generate-check:
	generated_tmp="$$(mktemp -d)"; \
	trap 'rm -rf "$$generated_tmp"' EXIT; \
	uv run python tools/generate.py --out "$$generated_tmp"; \
	diff -ru generated "$$generated_tmp"

check-live:
	uv run pytest tests/test_api_drift.py -v

hooks:
	git config core.hooksPath .githooks
	@echo "Git hooks enabled from .githooks"
