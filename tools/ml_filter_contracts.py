"""ML entry filter contract helpers and service-boundary validation (Q-085).

JSON Schema and OpenAPI express shape and many field constraints. Rules that
depend on strategy identity, chronological ordering, or duplicate-free ordered
lists are enforced by q_backend and mirrored here for contract tests.
"""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any

FEATURE_ALLOWLIST: tuple[str, ...] = (
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "real_volume",
    "ma_short",
    "ma_long",
    "delta",
    "prev_delta",
    "side",
)

ML_FILTER_ALGORITHMS: frozenset[str] = frozenset(
    {"lightgbm", "random_forest", "logistic_regression"}
)

ML_FILTER_ERROR_CODES: frozenset[str] = frozenset(
    {
        "missing_source",
        "incompatible_source",
        "invalid_split",
        "insufficient_training_samples",
        "missing_features",
        "incompatible_model",
        "artifact_unavailable",
        "lockbox_consumed",
        "training_failed",
    }
)

MACROSSOVER_ML_FILTER_STRATEGY = "MACrossoverMLFilter"

# RFC 3339 with explicit offset or Z (timezone-aware UTC on the wire).
_UTC_DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}" r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)

SERVICE_VALIDATIONS: tuple[str, ...] = (
    (
        "BacktestRequest.ml_filter is required when strategy is MACrossoverMLFilter "
        "and must be absent for all other strategies."
    ),
    (
        "MlFilterTrainingRequest.train_end must be strictly before validation_end "
        "(chronological UTC instants)."
    ),
    (
        "MlFilterTrainingRequest.selected_features must be duplicate-free; order is "
        "significant and must include side plus at least one other feature."
    ),
    "MlFilterTrainingRequest.algorithms must be duplicate-free and non-empty.",
    (
        "Per-algorithm hyperparameter objects must not contain unknown keys; seed must "
        "be a nonnegative 32-bit integer."
    ),
)


def _parse_utc_instant(value: str) -> datetime | None:
    if not isinstance(value, str) or not _UTC_DATETIME.match(value):
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def validate_threshold(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append("threshold must be a finite number")
        return errors
    if not math.isfinite(value):
        errors.append("threshold must be finite")
        return errors
    if value < 0.0 or value > 1.0:
        errors.append("threshold must be within [0, 1]")
    return errors


def validate_ml_filter_training_request(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    features = payload.get("selected_features")
    if not isinstance(features, list) or not features:
        errors.append("selected_features must be a non-empty array")
    else:
        if len(features) != len(set(features)):
            errors.append("selected_features must not contain duplicates")
        unknown = [f for f in features if f not in FEATURE_ALLOWLIST]
        if unknown:
            errors.append(f"unknown features: {unknown}")
        if "side" not in features:
            errors.append("selected_features must include side")
        elif len(features) < 2:
            errors.append(
                "selected_features must include at least one feature besides side"
            )

    algorithms = payload.get("algorithms")
    if not isinstance(algorithms, list) or not algorithms:
        errors.append("algorithms must be a non-empty array")
    else:
        if len(algorithms) != len(set(algorithms)):
            errors.append("algorithms must not contain duplicates")
        unknown_alg = [a for a in algorithms if a not in ML_FILTER_ALGORITHMS]
        if unknown_alg:
            errors.append(f"unknown algorithms: {unknown_alg}")

    for field in ("train_end", "validation_end"):
        instant = _parse_utc_instant(payload.get(field, ""))
        if instant is None:
            errors.append(f"{field} must be a timezone-aware UTC datetime")

    train_end = _parse_utc_instant(payload.get("train_end", ""))
    validation_end = _parse_utc_instant(payload.get("validation_end", ""))
    if train_end and validation_end and train_end >= validation_end:
        errors.append("train_end must be strictly before validation_end")

    seed = payload.get("seed", 42)
    if not isinstance(seed, int) or isinstance(seed, bool):
        errors.append("seed must be an integer")
    elif seed < 0 or seed > 2**32 - 1:
        errors.append("seed must be a nonnegative 32-bit integer")

    threshold = payload.get("threshold")
    if threshold is not None:
        errors.extend(validate_threshold(threshold))

    return errors


def validate_backtest_ml_filter_binding(strategy: str, ml_filter: Any) -> list[str]:
    errors: list[str] = []
    if strategy == MACROSSOVER_ML_FILTER_STRATEGY:
        if not isinstance(ml_filter, dict):
            errors.append("ml_filter is required for MACrossoverMLFilter")
            return errors
    elif ml_filter is not None:
        errors.append("ml_filter is only allowed for MACrossoverMLFilter")
        return errors
    else:
        return errors

    if (
        not isinstance(ml_filter.get("model_version_id"), str)
        or not ml_filter["model_version_id"].strip()
    ):
        errors.append("ml_filter.model_version_id is required")
    threshold = ml_filter.get("threshold", 0.5)
    errors.extend(validate_threshold(threshold))
    return errors
