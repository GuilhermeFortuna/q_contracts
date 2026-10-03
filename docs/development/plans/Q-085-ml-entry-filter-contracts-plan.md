# Q-085 implementation plan: ML entry filter contracts

> **For implementation agents:** Read the linked specification and repository instructions. Use superpowers:executing-plans when available. Launch only through `./work start Q-085 --agent <agent> --worktree` after written-plan approval and completed dependencies. Implement natively; delegation requires separate authorization.

**Goal:** Deliver the behavior and acceptance criteria in the linked specification.
**Architecture:** Versioned additive API and immutable-manifest contracts; generated types flow to consumers.
**Tech stack:** JSON Schema, OpenAPI, Python generators, Python/TypeScript/Rust outputs.
**Spec:** [Specification](../specs/Q-085-ml-entry-filter-contracts-spec.md)
**Status:** written plan awaiting human review.

## Global constraints

- Batch 14 is research-only; original MACrossover remains compatible. No live, GPU, automatic retraining or multi-entry ML support.
- Use Q-085 generated contracts, canonical repo tooling and existing execution semantics; never hand-edit vendored/generated consumer types.
- Tests use frozen/fake sources and small CPU models; production evaluation uses actual engine reruns and immutable data.
- Follow the linked spec's exact defaults, timing, split, feature, threshold, compatibility and error rules.
- Commit only focused task changes; no push, merge or protected-branch checkout. Missing prerequisites use the documented board workflow.

## Review focus

- Backward-compatible absent optional fields.
- Feature order and explicit positive-class/threshold meaning.
- UTC boundary and conditional cross-field validation.
- Immutable manifest identity includes actual contents.
- Unavailable/undefined results are distinct from zero and success.

## Ordered implementation

### 1. Define API and capability schemas

**Files:** Modify schema/api/openapi.yaml; create tests/test_ml_filter_contracts.py.
**Interfaces:** Generated training/comparison/evaluation/source/model DTOs; optional BacktestRequest.ml_filter and BacktestResponse.ml_filter_summary; additive strategy registry capabilities research_only/supports_optimization/supports_walkforward/supports_discovery.

- [x] Add focused failing tests: Assert existing requests without filter remain valid; threshold -0.1/1.1/NaN, duplicated algorithms/features, missing side and malformed UTC cutoffs reject; score/undefined-metric/state fixtures preserve meaning. Cross-field conditional requirements that OpenAPI cannot express are documented as service validations.
- [x] Run `uv run pytest tests/test_ml_filter_contracts.py tests/test_api_consistency.py tests/test_generate.py` and confirm the new behavior is missing before implementation; do not count import/setup failures as behavioral evidence.
- [x] Implement the specified interfaces and behavior, keeping public types aligned with Q-085 and preserving the existing patterns named above.
- [x] Run `uv run pytest tests/test_ml_filter_contracts.py tests/test_api_consistency.py tests/test_generate.py` and confirm the focused suite passes.
- [x] Commit this independently reviewable unit on the task branch with a conventional, focused message.

### 2. Define immutable manifests and generate outputs

**Files:** Create schema/catalog/ml-entry-filter-manifest.schema.json; extend tests/test_catalog_schemas.py and tests/test_generate.py; modify generated/ via tools/generate.py and VERSIONING.md/COMPAT.md as appropriate.
**Interfaces:** Discriminated format_version=1 dataset/model manifests with ordered features, data checksums, runtime/preprocessing/compatibility identity and artifact references; generated outputs consumed by Q-086/Q-088.

- [x] Add focused failing tests: Validate complete dataset/model fixtures and reject wrong kind/version/missing hashes; reordered features remain ordered across emitters; existing manifests still validate. Record service-owned hashing rules rather than pretending JSON Schema computes hashes.
- [x] Run `make check` and confirm the new behavior is missing before implementation; do not count import/setup failures as behavioral evidence.
- [x] Implement the specified interfaces and behavior, keeping public types aligned with Q-085 and preserving the existing patterns named above.
- [x] Run `make check` and confirm the focused suite passes.
- [x] Commit this independently reviewable unit on the task branch with a conventional, focused message.

## Verification and handoff

- [x] Review spec coverage and all five review-focus conditions against the focused tests above; fill any gaps before completion.
- [x] Run `make check` once after the final change. Do not wrap canonical CI in resource-slice commands. No Wine, GPU or desktop run is required.
- [x] Update task documentation with actual checks/results and any blocked prerequisites; do not claim unrun checks passed.
- [x] Commit final docs/code and use `./work board set Q-085 in-review -m "<changes; checks/results; follow-ups>"`. Human review/finish owns integration and publication.
