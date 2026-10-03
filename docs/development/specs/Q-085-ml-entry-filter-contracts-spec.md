# Q-085: ML entry filter contracts

**Status:** written spec and plan awaiting human review; status of record is the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2).
**Batch:** 14 — ML entry filters for research
**Depends on:** Q-006
**Implementation plan:** [Plan](../plans/Q-085-ml-entry-filter-contracts-plan.md)

## Purpose and ownership

Define the versioned boundary for training interchangeable supervised entry classifiers from an existing MA Crossover backtest, comparing saved models, and applying one to a new research strategy. Own API types in q_contracts; Q-086 implements training/evaluation and Q-087 backtest integration; Q-088 implements the UI. Extend existing OpenAPI components and generated Python/TypeScript/Rust outputs additively. Add `schema/catalog/ml-entry-filter-manifest.schema.json` for internal immutable dataset/model manifests. Do not repurpose neural encoder contracts: classifiers predict trade outcomes, encoders produce features.

## Fixed domain rules

- Strategy identifier `MACrossoverMLFilter`, label `MA Crossover · ML Filter`; original `MACrossover` remains unchanged. Exactly one entry with manager `or` and empty manager params is supported. Candle sequential engine only; the existing `day_trade` scheduling flag is supported.
- Algorithm identifiers: `lightgbm`, `random_forest`, `logistic_regression`. Type the algorithm-specific hyperparameter allowlists/defaults/ranges from Q-086; reject unknown keys and seed values outside nonnegative 32-bit integers. A model version is one fitted pipeline, never a mutable latest alias.
- Ordered feature allowlist: `open`, `high`, `low`, `close`, `tick_volume`, `real_volume`, `ma_short`, `ma_long`, `delta`, `prev_delta`, `side`. Default all available OHLCV fields plus all four MA indicators and side. Side is mandatory; optional OHLCV/indicator fields can be deselected, but at least one other feature must remain. A missing or entirely zero real_volume is omitted by default and explained; legitimate zero tick volume remains valid. No actual entry price or future/outcome field is a feature.
- Binary target `net_profitable_v1`: 1 when completed source trade net PnL > 0, otherwise 0. Features come from signal candle i; execution is at candle i+1 open. Score means predicted probability of class 1, not calibrated certainty or expected return.
- Threshold default 0.50; finite range [0,1], inclusive acceptance `score >= threshold`. Scores must be finite and in [0,1]. Gate changes entries only, preserves exit arrays and position sizing strength, and never delays rejected entries.
- Normalize API times to timezone-aware UTC using the existing backend exchange-time conversion; artifact mapping uses source bar positions, not fixed timestamp subtraction.

## API surface

Use `/api/v1/ml-filters` as the namespace. Paginated lists use existing limit/offset conventions. No new streaming topics: persisted jobs are polled through these endpoints.

| Method/path | Contract |
|---|---|
| GET `/sources` | Completed backtest sources with eligibility/reason, symbol/timeframe, date range, strategy/exit/cost/sizing context, available features and source sample count |
| GET `/sources/{run_id}` | Same source details plus bar-count-based 60/20/20 split suggestion, volume readiness and eligibility errors; no fitting |
| POST `/training` | Source run id, explicit train_end and validation_end, ordered selected features, distinct nonempty algorithm list, per-algorithm hyperparameters, seed (default 42); returns 202 job_id/status |
| GET `/training/{job_id}` | Durable state, stage, counts/rejections, dataset_id, model_version_ids, validation comparison_id on completion, structured error on failure |
| GET `/models` | Filter by symbol/timeframe/base config compatibility and dataset_id; summaries include algorithm/version/features/training boundary, selectable readiness and incompatibility reasons |
| GET `/models/{model_version_id}` | Full provenance, pipeline/runtime versions, validation metrics and manifest identity; never returns serialized executable model data |
| POST `/comparisons` | Dataset id, distinct model version ids from that dataset, threshold; async full baseline/filtered validation engine reruns |
| GET `/comparisons/{job_id}` | Status and results keyed by model version, threshold, dataset/split identity; acceptance counts plus engine metrics and equity/trade artifact references |
| POST `/evaluations` | Dataset id, one model version id and threshold; async one-time final lockbox evaluation, idempotent for that exact tuple |
| GET `/evaluations/{job_id}` | Frozen evaluation tuple, status, baseline/filtered lockbox results and honest error state |

States are `queued`, `running`, `completed`, `failed`; stages include `dataset`, `fitting`, `validation`, `evaluation`, `persisting`. Progress counts have declared totals or null when unknown; terminal results survive Redis TTL. Errors use a typed code/message/details envelope, with at least missing_source, incompatible_source, invalid_split, insufficient_training_samples, missing_features, incompatible_model, artifact_unavailable, lockbox_consumed, and training_failed. HTTP 404 for missing ids, 422 for invalid request values, 409 for eligibility/compatibility/lockbox conflicts. Worker-discovered errors persist on failed jobs. No misleading success if one selected algorithm fails.

## Backtest and artifact contracts

Add optional registry capability fields `research_only`, `supports_optimization`, `supports_walkforward`, and `supports_discovery`; absence preserves current original-strategy eligibility. The filtered variant advertises research_only=true and all three supports fields false. Live execution checks research_only independently of UI.

Add optional `ml_filter` configuration to BacktestRequest: `{model_version_id, threshold}`. It is required for MACrossoverMLFilter and rejected for other strategies. It is persisted/restored with backtest history; strategy params remain MA params, not model paths or algorithm names. Add optional `ml_filter_summary` to the result for model version, threshold, scored/accepted/rejected/not-ready candidate counts and provenance. Preserve existing result fields.

Manifest discriminant `kind` is `ml_filter_dataset` or `ml_filter_model`, format version 1. Dataset manifests contain source run/config/engine revision, immutable full-content bar and trade checksums, selected ordered features and dtypes, UTC cutoffs, label definition, sample/rejection counts by partition, compatibility fingerprint, and dataset content identity. Model manifests additionally contain dataset id, algorithm, canonical hyperparameters/seed, ordered preprocessing recipe, training-label availability cutoff, dependency versions, fitted artifact checksum and immutable model_version_id. Feature order is significant; full artifact bytes participate in identity. Local filesystem paths are not public identifiers.

Comparisons distinguish classification diagnostics from actual trading metrics: confusion matrix and ROC AUC (null with reason for single-class data); net PnL, max drawdown, profit factor (null with reason if undefined), trade count and equity. Acceptance counts refer to candidate signals, not necessarily executed trades. Evaluation records freeze the tuple before dispatch, with one lockbox consumption per dataset; identical retries return the same record, conflicting selections return 409.

## Acceptance criteria

1. Existing OpenAPI fixtures and generated consumer shapes remain valid when new optional fields are absent.
2. Python, TypeScript and Rust outputs express the same feature order, algorithm enums, UTC timestamps, readiness/error states, jobs, backtest configuration and manifests.
3. Fixtures reject invalid thresholds, duplicate algorithms/features, missing side, invalid cutoffs, mismatched manifests and missing conditional filter configuration at the appropriate schema/service boundary.
4. Manifest fixtures include actual content checksums and preprocessing identity; changing feature order or fitted bytes changes version identity.
5. Offline `make check` passes; document any runtime cross-field rules the emitter cannot represent. No live API capture is required before the consumers exist.

## Delivery boundary

Written specification and plan await human review. No implementation is authorized by this documentation session. Integrate/publish the documentation before launch; the human approves plans and sets Todo. Start only with `./work start Q-085 --agent <agent> --worktree` after dependencies are Done. Implement natively; delegation requires separate authorization. Never push, merge, edit vendored contracts, or change board status outside the workspace workflow.

Batch 14 is research-only: no live deployment, q_terminal integration, automatic walk-forward retraining, optimizer/discovery support, multi-entry ML combinations, custom uploads, or GPU requirement. Existing MACrossover behavior and saved configurations remain compatible. Python orchestrates model inference; existing q_core indicator and execution semantics are reused without another fill/indicator implementation.
