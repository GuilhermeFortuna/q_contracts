# ML entry filter service validations (Q-085)

OpenAPI and JSON Schema in `q_contracts` define wire shapes and many field-level
constraints. The following rules are enforced by `q_backend` at request handling
time and are mirrored in `tools/ml_filter_contracts.py` for contract tests:

1. `BacktestRequest.ml_filter` is **required** when `strategy` is
   `MACrossoverMLFilter` and must be **absent** for all other strategies.
2. `MlFilterTrainingRequest.train_end` must be strictly before
   `validation_end` (chronological UTC instants with explicit offset or `Z`).
3. `selected_features` must be duplicate-free; order is significant; `side` is
   mandatory and at least one additional feature must remain.
4. `algorithms` must be duplicate-free and non-empty.
5. Per-algorithm hyperparameter objects reject unknown keys; `seed` must be a
   nonnegative 32-bit integer.
6. Manifest `dataset_content_id` and `model_content_id` digest the canonical
   serialized manifest bytes including ordered features and checksum fields;
   recomputing hashes is service-owned (schemas do not derive digests).
