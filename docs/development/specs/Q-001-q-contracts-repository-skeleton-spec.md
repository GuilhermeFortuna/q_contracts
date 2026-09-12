# Q-001: `q_contracts` repository skeleton

**Status:** authoritative in the [Q project board](https://github.com/users/GuilhermeFortuna/projects/2)  
**Project direction:** `q/docs/system-architecture.md`  
**Depends on:** None  
**Implementation plan:** [`../plans/Q-001-q-contracts-repository-skeleton-plan.md`](../plans/Q-001-q-contracts-repository-skeleton-plan.md)

## Purpose

Every cross-process payload in the system is currently defined twice: once as a
Pydantic model in `q_backend` and once as a hand-written TypeScript interface in
`q_frontend`, with the Wine gateway's wire format described only in a module
docstring. The two copies drift silently, and neither is readable by the two
repositories that do not exist yet. This task creates the repository that will
hold the single definition of each payload, together with the rules for where a
schema lives, how it is named, and what makes it valid — before any schema is
written into it. It matters now because Q-002 through Q-005 each populate a
different subtree of that layout, and a layout invented four times in parallel
is four layouts.

## Requirements

### Repository identity

- The repository is self-contained: nothing in it imports from, reads from, or
  resolves a path into `q_backend`, `q_frontend`, or any sibling checkout.
- The repository declares the language and toolchain used to validate and later
  generate from its schemas, pinned to an exact version, so that two machines
  checking out the same commit run the same validator.
- The repository states, in its own README, that it is the single source of
  truth for cross-process payloads, and that consumers vendor generated code
  rather than depending on it as a package.

### Schema directory layout

- The schema files are organized by the boundary they describe, not by the
  repository that consumes them, because a payload's shape is a property of the
  boundary and several repositories read the same boundary.
- There is exactly one directory per boundary class established by the
  architecture: the control API, the event stream, the Wine edge processes, and
  the dataset catalog. Each is created in this task, empty but for a file
  stating what belongs in it and what does not.
- A schema file's path determines its identifier, so that an identifier can
  never disagree with the file it names.
- The layout distinguishes hand-authored schema sources from generated output,
  and the generated area is empty in this task. No consumer ever reads the
  hand-authored area directly.

### Schema validity

- Every hand-authored schema file is machine-checkable, and the check runs over
  the whole tree rather than over a list someone maintains, so a schema added
  without being registered still gets checked.
- A schema file that is syntactically invalid, that declares an unsupported
  schema dialect, or that sits in a directory whose rules it does not satisfy,
  fails the check with a message naming the file.
- The check passes on an empty tree. A repository with no schemas yet is valid,
  not broken.
- Adding a schema never requires editing a central registry file, because a
  registry that must be edited is a registry that will be forgotten.

### Validation suite

- The repository has a single documented command that runs every check, and that
  command is what CI runs. There is no second, longer sequence that only CI
  knows.
- The validation suite is fast enough to run on every save during authoring;
  cheapness here is a requirement because the alternative is that authors stop
  running it.
- CI runs the same command on every push and on every pull request, and fails
  the build on any non-zero exit.

### Versioning policy

- The repository records its policy on breaking changes — what counts as
  additive, what forces a schema-major bump, and how long both majors are served
  — as a document in the repository rather than as tribal knowledge.
- The policy states that consumers pin by commit hash and that no package
  registry or semantic version is published for contracts.

## Constraints and non-goals

- **No schemas.** Not the stream envelope, not the OpenAPI document, not the
  edge contracts, not the dataset manifest. Each is its own task (Q-002 through
  Q-005). The temptation is to write "just the envelope" while the layout is
  fresh in mind; doing so decides Q-002's design inside Q-001, unreviewed.
- **No code generation.** No generator, no generated output, no vendoring
  protocol, no `CONTRACTS_REV`. That is Q-006, and it needs schemas to generate
  from.
- **No changes to `q_backend` or `q_frontend`.** Neither repository learns about
  `q_contracts` in this task. The cross-repo relative links called out in §7.1 of
  the architecture are fixed when there is something to link to.
- **No `COMPAT.md` content.** The file recording known-good pins across
  repositories is created by Q-006, when there are pins to record.
- **No hosting decision.** Whether the repository has a remote, and where, is out
  of scope; the task is complete with a local repository and a working CI
  configuration file.

## Acceptance criteria

### Agent-verifiable

1. The repository exists as an independent git repository with an initial commit,
   and contains no path reference to a sibling checkout.
2. The four boundary directories exist, each carrying a document stating what
   belongs in it and what does not.
3. The validation command exits zero on the repository as delivered.
4. A deliberately malformed schema file placed in a boundary directory causes the
   validation command to exit non-zero with a message naming that file, and
   removing the file restores a zero exit.
5. A well-formed schema file added to a boundary directory is picked up by the
   validation command without any registry file being edited.
6. A schema file declaring an unsupported dialect fails the check, and the
   failure message names both the file and the dialect.
7. The versioning policy document exists and states the additive-by-default rule,
   the schema-major bump rule, and the commit-hash pinning rule.
8. The toolchain is pinned to an exact version, and the pin is recorded in a file
   under version control.
9. The full validation suite passes.

### Human-verifiable

1. The CI configuration runs the same single validation command that a developer
   runs locally, and a push to a branch produces a green run.
   Command: `git push -u origin <branch>` then inspect the run in the CI provider
2. The README is sufficient for someone who has never seen the repository to add
   a schema to the correct directory without asking a question.
   Command: `$EDITOR README.md`
