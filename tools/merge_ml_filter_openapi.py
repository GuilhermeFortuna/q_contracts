"""One-shot merge helper for Q-085 ML filter OpenAPI components and paths."""

from __future__ import annotations

from pathlib import Path

import yaml


def merge(openapi_path: Path, fragment_path: Path) -> None:
    fragment = yaml.safe_load(fragment_path.read_text(encoding="utf-8"))
    doc = yaml.safe_load(openapi_path.read_text(encoding="utf-8"))

    schemas = doc.setdefault("components", {}).setdefault("schemas", {})
    for name, schema in sorted(fragment["schemas"].items()):
        schemas[name] = schema

    # BacktestRequest / BacktestResponse / StrategyInfo patches
    backtest_request = schemas["BacktestRequest"]
    props = backtest_request.setdefault("properties", {})
    props["ml_filter"] = {
        "anyOf": [
            {"$ref": "#/components/schemas/MlFilterConfig"},
            {"type": "null"},
        ],
        "title": "Ml Filter",
    }

    backtest_response = schemas["BacktestResponse"]
    backtest_response.setdefault("properties", {})["ml_filter_summary"] = {
        "anyOf": [
            {"$ref": "#/components/schemas/MlFilterBacktestSummary"},
            {"type": "null"},
        ],
        "title": "Ml Filter Summary",
    }

    strategy_info = schemas["StrategyInfo"]
    for field in (
        "research_only",
        "supports_discovery",
        "supports_optimization",
        "supports_walkforward",
    ):
        strategy_info.setdefault("properties", {})[field] = {
            "anyOf": [{"type": "boolean"}, {"type": "null"}],
            "title": field.replace("_", " ").title().replace(" ", " "),
        }

    paths = doc.setdefault("paths", {})
    for path, item in sorted(fragment["paths"].items()):
        paths[path] = item

    openapi_path.write_text(
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    merge(
        root / "schema" / "api" / "openapi.yaml",
        root / "tools" / "ml_filter_openapi_fragment.yaml",
    )
