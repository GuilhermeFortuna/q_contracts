# Q-006: Contract code generation and consumer vendoring

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Project direction:** `q/docs/system-architecture.md`  
**Depends on:** Q-002, Q-003, Q-004, Q-005  
**Implementation plan:** [`../plans/Q-006-contract-codegen-and-vendoring-plan.md`](../plans/Q-006-contract-codegen-and-vendoring-plan.md)

## Purpose

Four tasks have put every cross-process payload into one repository, and so far
not one line of running code reads any of it. This task closes that loop: it
generates typed code from the schemas in each consumer language, defines how a
consumer repository carries that code and records which contracts commit it came
from, and makes a consumer's build fail when its carried copy no longer matches
the commit it claims. Without it the schemas are documentation, the hand-written
mirrors in the frontend stay authoritative, and the two repositories built after
this one have nothing to type against.

## Requirements

### Generation

- Generated code is produced from the schemas by a command in the contracts
  repository, and that command is the only way generated code comes into
  existence.
- Generation is deterministic: the same commit produces byte-identical output on
  any machine with the pinned toolchain, so that a difference in output always
  means a difference in input.
- Generated files are marked as generated and name the source schema they came
  from, so that someone who opens one and starts editing is told not to.
- Generation covers the languages that have a consumer today. A language with no
  consumer is not generated, and the reason is recorded, because unused generated
  code is code that is never compiled and therefore never known to be wrong.
- Generated output for each language is idiomatic enough to be used directly:
  types a consumer can import without writing an adapter layer over them.
- Regenerating over existing output is safe and produces no change when the
  schemas have not changed.

### Vendoring

- A consumer repository carries the generated code for its own language inside
  its own tree, so that building the consumer requires no sibling checkout and no
  network access.
- A consumer records the exact contracts commit its carried code was generated
  from, in a file, so that the question "which contracts is this consumer on" has
  a single answer.
- A consumer has a command that regenerates its carried code from the recorded
  commit, and running it when nothing has changed produces no diff.
- A consumer's CI fails when its carried code differs from a clean regeneration
  at its recorded commit, because the failure mode being prevented is a
  hand-edited generated file that works locally and is wrong everywhere else.
- Updating a consumer to a newer contracts commit is a deliberate act: changing
  the recorded commit and regenerating, in one change, reviewable as a diff.

### Cross-repository bookkeeping

- One document records the set of pins known to work together across every
  repository, and it is the only cross-repository bookkeeping the project has.
- Updating that document is part of any change that moves a pin, so that the
  known-good set is never behind the repositories it describes.
- The document records what "known to work together" was verified by, rather than
  asserting it.

### Adoption

- At least one consumer actually adopts generated types for at least one real
  payload, replacing a hand-written mirror, so that the pipeline is proven by use
  rather than by the generator exiting zero.
- The adopted payload is one whose hand-written mirror exists today, and the
  mirror is deleted rather than left beside its replacement.
- Adoption does not change runtime behavior; it changes where the types come
  from.

### Scope discipline

- The generator handles the schema dialects the repository actually contains, and
  fails loudly on one it does not, rather than skipping it silently.
- A schema that cannot be generated for a given language fails the generation
  command with the schema and the language named.

## Constraints and non-goals

- **No new schemas.** If generation reveals that a schema is unrepresentable in a
  target language, that is a finding and, where warranted, a change to the schema
  in its own task — not an improvised edit inside this one.
- **No wholesale frontend migration.** One payload adopts generated types. The
  remaining hand-written mirrors in the frontend are replaced incrementally, each
  in the task that touches its surface. Converting all twelve here would put a
  large, untestable diff in the same change as the pipeline that produced it.
- **No package registry.** Contracts are not published to PyPI, npm, or crates.io.
  Pins are commit hashes.
- **No semantic versioning of contracts.** The versioning rules already written
  govern compatibility; a second version number would be a second source of truth
  about it.
- **No C++ generation.** This narrows the language list in §7 of the architecture
  and nothing else: C++ remains a language of the system, written by hand inside
  `q_terminal` for custom scene-graph render nodes and the generated side of the
  `cxx-qt` bridge. It is not a *generation target*, because that C++ receives
  buffers already decoded by the core and never touches a wire payload, so
  generated payload types for it would be headers nothing compiles. The narrowing
  is recorded with its reason and is revisited if C++ acquires a payload-handling
  role.
- **No runtime schema validation.** Generated types describe shapes. Whether a
  process validates a payload against its schema at runtime is that process's
  decision, made where the cost is paid.
- **No changes to `q_backend`'s API behavior or `q_frontend`'s rendering.**

## Acceptance criteria

### Agent-verifiable

1. A generation command exists in the contracts repository and produces output for
   each generated language into the designated output area.
2. Running generation twice in a row produces no change on the second run.
3. Generation run from a clean checkout on a different working directory produces
   byte-identical output to the committed output, verified by a diff that must be
   empty.
4. Every generated file carries a marker identifying it as generated and naming
   its source schema.
5. A schema in an unsupported dialect causes generation to fail with the schema
   path and the target language named.
6. Each consumer repository carries generated code for its language and a file
   recording the contracts commit it came from.
7. Each consumer has a regeneration command, and running it against the recorded
   commit produces no diff.
8. Each consumer's CI fails when a generated file is modified by hand, verified by
   modifying one, observing the failure, and reverting it.
9. The known-good pin document exists, records a pin for every repository, and
   states what the combination was verified by.
10. One hand-written type mirror in a consumer is deleted and replaced by a
    generated type, and that consumer's existing test suite passes unchanged.
11. The contracts repository's full validation suite passes, and every consumer's
    full validation suite passes.

### Human-verifiable

1. A generated type from each language is read and confirmed to be usable without
   an adapter layer: idiomatic naming, sensible optionality, and no leaked schema
   artifacts.
   Command: `$EDITOR q_contracts/generated/`
2. The pin-update flow is exercised end to end: a trivial additive change is made
   to a schema, committed, and one consumer is advanced to the new commit by
   changing its recorded pin and regenerating, with the resulting diff reviewed.
   Command: `cd q_contracts && git log -1 --format=%H` then, in the consumer,
   `make contracts && git diff`
3. The consumer that adopted a generated type is run and the affected surface is
   confirmed to behave as it did before.
   Command: `cd q_frontend && pnpm tauri:dev`
