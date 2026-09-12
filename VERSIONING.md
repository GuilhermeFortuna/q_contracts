# Versioning Policy

This document defines the evolution and versioning rules for contracts in `q_contracts`.

## Core Principles

1. **Single Source of Truth:** `q_contracts` defines the single canonical representation of all cross-process payloads in the system.
2. **No Package Registry, No SemVer:** Contracts are not published to a package registry (such as PyPI or npm). There is no repository-level semantic version (e.g. `v1.2.3`).
3. **Commit-Hash Pinning:** Consumers vendor code generated from this repository and pin to an exact git commit hash. Upgrades occur by updating the pinned commit hash and re-running code generation.

## Additive by Default

All schema modifications must be additive (backward and forward compatible) whenever possible:

- **Optional Fields:** Adding a new optional field (or a field with a default value) is additive.
- **Payload Extensions:** Adding a new distinct message type, topic, or endpoint is additive.
- **Relaxed Constraints:** Broadening acceptance criteria without invalidating existing valid inputs is additive.
- **Non-Breaking Changes:** Additive changes do not require incrementing a major version. Existing consumers continue operating without interruption.

## Schema-Major Bumps (Breaking Changes)

A change is considered breaking when it disrupts existing consumers:

- Removing or renaming an existing field.
- Changing the type, format, or required semantics of an existing field.
- Adding a mandatory (required) field that existing producers cannot supply or existing consumers do not know how to handle.
- Tightening validation rules that cause previously accepted messages to be rejected.

When a breaking change is unavoidable:
1. **Schema-Major Increment:** The schema must undergo a major version bump (e.g. `schema_major` increment or a versioned path bump like `/v2/`).
2. **Parallel Serving / Dual Majors:** Both the previous major version and the new major version must be served simultaneously for at least **one full release cycle**.
3. **Deprecation Window:** Consumers migrate to the new major version during the transition window. The old major version is retired only after all consumers have upgraded.
