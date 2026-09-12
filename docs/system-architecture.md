# Q System Architecture — languages, repos, and planes

**Status:** Decided 2026-09-12, revised the same day after review. Supersedes the
single-frontend assumption in `q-frontend-tech-stack.md` §1–§2 and the "live trading
stays native-MT5-on-Windows" constraint in `mt5-remote-gateway.md` and
`paper-live-execution.md`. Those documents remain valid for the components they describe;
where they conflict with this one on topology, language, or platform, this document wins.
**Scope:** the whole Q system. Individual components keep their own design docs.
**Platform:** Linux (Fedora, Wayland, NVIDIA) is the primary and only supported desktop
platform. Windows is not a target.

---

## 1. Goals and constraints

Q started as a strategy research tool. Two new goals change its shape:

1. **Automated strategy execution**, where latency, determinism, and fail-closed behavior
   are first-class requirements rather than research conveniences.
2. **Large, real-time visualizations** that use the local GPU directly and are fed by
   streaming data, not by request/response JSON.

Constraints that shape every decision below:

- The research engine in `q_backend` (candle and tick engines, genome DSL, walk-forward,
  feature store, neural latents, and the causality/parity/determinism test suites) is the
  project's main asset. It is preserved and built on, not rewritten.
- The developer stays on Linux. MetaTrader 5 is Windows software, so it runs under Wine
  (or, as a fallback, in a Windows VM). No Linux-side process may depend on it directly.
- `q_backend` and `q_frontend` already exist as separate repositories. The architecture
  stays multi-repo and minimizes cross-repo coordination rather than pretending it away.
- Solo development. Boundaries must reduce coordination cost, not add ceremony.

## 2. Assessment of the current system

What exists today (2026-09) and how it measures against the goals:

| Area | State | Verdict |
| --- | --- | --- |
| Research engine | ~56k lines Python. Rich strategy, exit-rule, genome, optimization, feature and neural layers; strong causality and parity tests | Keep. This is the asset |
| Candle backtest loop | Per-bar Python loop over `pandas` rows in `backtesting/engine.py` | Largest throughput cost; moves to Rust |
| Tick backtest loop | `numba` kernel in `backtesting/tick/kernel.py` | Good shape; moves to Rust with the candle loop so there is one kernel family |
| Execution | Dedicated single-process worker, closed-bar evaluation, intent persisted before submission, fail-closed Postgres ledger, lease and kill-switch | Design is correct. Keep it in Python; move only deterministic evaluation to Rust |
| Data transport | REST + JSON; UI polls with React Query timers (the execution workspace alone runs ~11 polling queries at 1–2 s) | Replace with an event stream and binary columnar payloads |
| Charts | SVG via `visx`; WO70/WO71 already document render cost | Fine to a few thousand points; larger research surfaces need a WebGL2 canvas path |
| Desktop shell | Tauri 2 on WebKitGTK; the Rust shell spawns `docker compose` and `uv` | WebKitGTK has no usable WebGPU and uneven WebRTC on Linux. Shell should not own backend processes |
| MT5 on Linux | Read-only data gateway under Wine (WO183–186), stdlib Python + `MetaTrader5` only | Correct pattern; generalize it to execution |
| Repos | `q_backend` and `q_frontend` cross-reference each other (backend README links into frontend docs; Tauri bundles the sibling checkout) | Symptom of a missing contracts layer |

## 3. Target architecture

### 3.1 Three planes

```
┌──────────────────────────────── Linux workstation ────────────────────────────────┐
│                                                                                    │
│  EXECUTION PLANE                 RESEARCH / CONTROL PLANE        PRESENTATION      │
│                                                                                    │
│  ┌───────── Wine prefix ──────┐  ┌──────────────────────────┐  ┌───────────────┐   │
│  │ MT5 terminal               │  │ q_backend API (FastAPI)  │  │ q_terminal    │   │
│  │ mt5 data gateway (stdlib)  │  │  · REST control API      │◄─┤  Qt/QML       │   │
│  │ mt5 execution edge (stdlib)│  │  · Arrow WebSocket stream│  │  q_core       │   │
│  │ [tier B: MQL5 EA]          │  │ Dramatiq research workers│  │  live trading │   │
│  └──────────┬─────────────────┘  │ Redis Streams (fan-out + │  │  + operations │   │
│             │ loopback, contract │   bounded replay)        │  └───────────────┘   │
│             │ from q_contracts   │ Postgres (ledger, runs,  │  ┌───────────────┐   │
│  ┌──────────▼─────────────────┐  │   outbox, catalog)       │  │ q_frontend    │   │
│  │ execution worker (Python)  │  │ Parquet lake + DuckDB    │  │  Tauri/React  │◄──┤
│  │  orchestration, ledger,    │  └─────────▲────────────────┘  │  research UI  │   │
│  │  leases, reconciliation    │            │                   └───────────────┘   │
│  │  q_core for evaluation     ├──outbox────┘                                       │
│  └────────────────────────────┘                                                    │
│                                                                                    │
│  q_core (Rust) is linked into: q_backend and the execution worker (wheel) · q_terminal │
└────────────────────────────────────────────────────────────────────────────────────┘
```

- **Execution plane.** Owns every MT5 call and every order. The only place the
  `MetaTrader5` Python module is imported is inside the Wine prefix, in stdlib-only edge
  processes that implement wire contracts defined in `q_contracts` (the existing data
  gateway, plus a new execution edge for quotes, `order_check`, `order_send`, positions,
  and deal history). The execution worker is a Python process that keeps today's
  orchestration (closed-bar scheduling, intent-before-submission, Postgres ledger,
  leases, reconciliation, kill switch) and calls `q_core` for deterministic evaluation.
- **Research / control plane.** `q_backend` as today, minus the loops that move to Rust,
  plus a transactional outbox, an event bus, a binary stream endpoint, a dataset catalog,
  and DuckDB over the Parquet lake.
- **Presentation plane.** Two UIs with a semantic ownership boundary (§5.1):
  `q_frontend` for research, `q_terminal` for live trading and operations.

### 3.2 Latency tiers

| Tier | Strategy class | Decision loop | Where the logic runs | Status |
| --- | --- | --- | --- | --- |
| A | Closed-bar, M15 and slower | Seconds | Python execution worker; `q_core` evaluation; Postgres ledger | Today's design |
| B | Tick-reactive, tens of ms | 10–50 ms | MQL5 Expert Advisor inside the terminal with **pre-authorized local limits**; Linux worker supervises, updates limits, reconciles, holds the kill switch (§6.4) | Only if a strategy demands it |
| C | Sub-millisecond | < 1 ms | Not reachable through MT5. Requires DMA/FIX access to B3 | Out of scope |

The loopback hop to the Wine edge adds ~1 ms. The MT5 terminal and the broker round trip
dominate at tens to hundreds of milliseconds. Staying on Linux does not change the tier
picture.

### 3.3 Rust scope in execution

Rust owns **deterministic computational semantics**: indicator math, signal evaluation
over a completed-bar window, exit-rule state transitions, position sizing, and bar
aggregation from ticks. These are the semantics that backtest and live must agree on, and
the parity suite proves they do.

Rust does **not** own execution orchestration for tier A: Postgres transactions, lease
acquisition and heartbeat, order-state transitions, reconciliation, recovery, supervision,
and broker-edge calls stay in Python. The execution worker's measured budget today is a
p95 of 500 ms per bar decision, most of it I/O; moving orchestration to Rust would not move
that number. Any later move is gated on a profile that shows Python orchestration, not I/O
or the broker, as the bottleneck.

## 4. Data, events, and streaming

### 4.1 Topic classes

Every stream topic is one Redis Stream. Topics fall into two classes with different
guarantees:

| Class | Topics | Source of truth | Sequence assigned by | Replay |
| --- | --- | --- | --- | --- |
| **Durable** | `decisions`, `orders`, `fills`, `risk`, `ledger`, `deployments`, `jobs.terminal` | Postgres (transactional outbox) | Postgres sequence per topic, in the same transaction as the state change | Unbounded via REST history; bounded via Redis |
| **Ephemeral** | `quotes`, `bars.forming`, `bars.completed`, `jobs.progress` | The single publisher process for that topic | Publisher-local monotonic counter per topic, reset on publisher restart with a new `publisher_epoch` | Redis retention only; older data via REST market-data endpoints, not via the stream |

Each stream entry carries: `topic`, `seq` (per-topic, monotonic within an epoch),
`epoch` (Postgres outbox epoch for durable topics; publisher epoch for ephemeral),
`producer_id`, `origin_ts` (producer clock, UTC), and the payload (Arrow IPC batch or JSON
control frame). The Redis stream ID is the **replay cursor**; `seq` is the **ordering and
deduplication watermark**. They are different things and clients track both.

### 4.2 Snapshot then delta, without the race

The protocol is subscribe-first, then snapshot, then reconcile:

1. Client opens the WebSocket and sends `subscribe {topics}`.
2. Server replies `subscribed {topic → {cursor, epoch, last_seq}}` and begins forwarding
   entries after `cursor`. The client buffers them without applying.
3. Client requests the snapshot over REST. For durable topics the snapshot is read in one
   `REPEATABLE READ` transaction and returns `{state, watermark: {topic → seq}}`, where the
   watermark is `max(seq)` of the outbox rows visible to that transaction. Because the
   outbox row and the state change commit together, the watermark is exactly the last
   event reflected in the state. For ephemeral topics the "snapshot" is the publisher's
   `latest` endpoint, which returns the current value plus its `seq` and `epoch`.
4. Client applies the snapshot, discards buffered entries with `seq ≤ watermark[topic]`,
   applies the rest in `seq` order, and continues live.

Gaps are detected by `seq`. If the client observes `seq > expected + 1` on a durable topic
it fetches the missing range from REST history by `seq`; on an ephemeral topic it simply
resynchronizes from `latest`. An `epoch` change on any topic forces a full re-snapshot of
that topic.

### 4.3 Redis retention and recovery

- Retention is per topic via approximate `MAXLEN`: durable topics keep roughly 24 hours or
  200k entries, whichever is smaller; `quotes` and `bars.forming` keep roughly one hour;
  `bars.completed` and `jobs.progress` keep roughly 24 hours. Values live in
  `q_contracts/stream/topics.yaml` and are tuned by measurement, not by this document.
- A `subscribe` with a cursor older than retention is answered `cursor_expired {topic}`.
  The client re-runs §4.2 for that topic. For durable topics nothing is lost because the
  outbox in Postgres is retained for 30 days and served by REST history; for ephemeral
  topics the client resumes from `latest`.
- Redis is not persistent. A Redis restart empties every stream. The API detects this by a
  `stream_epoch` key it writes at startup and re-checks on each publish; a change is
  broadcast as `epoch_changed` to every subscriber and clients re-snapshot. The outbox
  relay resumes from the last relayed `seq` recorded in Postgres, so durable topics are
  fully republished; ephemeral publishers start a new `publisher_epoch`.
- The outbox relay is a single process (one per topic class is acceptable) that reads
  unrelayed outbox rows in `seq` order and `XADD`s them. It is at-least-once; consumers
  deduplicate on `(topic, epoch, seq)`.

### 4.4 Backpressure, per topic

The server keeps a bounded outbound queue per client per topic. Behavior on pressure is a
property of the topic, declared in `q_contracts`:

| Topic | Policy | On overflow |
| --- | --- | --- |
| `quotes` | Coalesce per symbol: keep the latest, drop superseded | Nothing lost that matters; latest always delivered |
| `bars.forming` | Coalesce per `(symbol, timeframe)`: keep the latest forming bar | Same |
| `bars.completed` | Never coalesced; bounded queue | Mark client `lagging {topic, from_seq}`; client fetches the gap from REST history |
| `jobs.progress` | Coalesce per job | Terminal job states go on `jobs.terminal` and are never dropped |
| All durable topics | Never coalesced, never dropped | Close that topic's subscription with `lagging`; client re-runs §4.2. Durable topics are replayable, so this loses nothing |

Clients coalesce again on their side to one render per frame (§4.6). No client-side logic
may assume every quote is delivered; every client-side logic may assume every durable
event is delivered exactly once in `seq` order.

### 4.5 Control path

Commands (start, pause, stop, flatten, kill switch, resolve unknown order, deploy strategy
version) go over REST because they need acknowledgement and audit. Each command carries a
client-generated idempotency key; the API stores the result keyed by it for 24 hours and
returns the stored result on retry.

### 4.6 Visualization data path

Semantics: **columnar, no per-row objects** from the lake or stream to the GPU buffer.
Downsampling, binning, and level-of-detail run in `q_core` on the CPU or in shaders on the
GPU, never on a UI thread. Stream updates are coalesced to one buffer upload per frame.

This is not a literal zero-copy requirement. Bounded contiguous copies are allowed where
they simplify ownership or lifetimes across a language boundary (Arrow IPC decode into a
`q_core` buffer; a delta slice copied into a Qt scene-graph buffer; a `numpy` view
materialized for PyO3), provided they stay inside the measured budget: p95 frame time under
16 ms in `q_terminal` with one full-rate symbol and one dense chart, measured on the
target machine. Copies of whole datasets per frame are not bounded and are not allowed.

### 4.7 Persistence boundary and direct Parquet access

- `q_backend` owns **dataset lifecycle**: what a dataset is, its ID, its files, its
  schema, cataloguing, paths, retention, tombstoning, and every write. The Parquet lake
  layout in `market_data/local_store.py` and the run artifacts in `storage/lake/` become
  entries in a **dataset catalog** in Postgres, keyed by an immutable `dataset_id`.
- `q_core` owns **codecs and computational primitives**: Parquet and Arrow readers,
  columnar buffers, kernels. It has no notion of a catalog, a root directory, or a
  retention policy. It reads the files it is handed.
- Datasets are **immutable once published**: written to a temporary path, fsynced,
  atomically renamed, and never rewritten. New data is a new dataset version with a new
  ID. Tombstoned datasets keep their files for a grace period (default 7 days) so an open
  reader never sees a file vanish.
- `q_terminal` reads local Parquet **only through the catalog**: it asks the API for a
  `dataset_id`, receives a manifest (file list with sizes and checksums, Arrow schema, row
  counts, time range, `published_at`), verifies checksums on first open, and reads the
  listed files with `q_core`. It never lists directories or guesses paths. If the manifest
  is gone or a file fails its checksum, it falls back to fetching the same dataset as Arrow
  over HTTP.

## 5. Languages

| Language | Role | Not allowed |
| --- | --- | --- |
| **Rust** | Deterministic computational semantics: indicators, candle and tick kernels, fill model, exit-rule state machines, position sizing, bar aggregation, columnar buffers, Parquet/Arrow codecs and readers | UI code, orchestration, transactions, dataset lifecycle or persistence policy |
| **Python** | Research orchestration and the control plane: strategy search, Optuna, genome operators, neural training, API, job queue, Postgres, outbox relay, stream endpoint, dataset catalog, and the whole tier A execution worker minus evaluation. Also the stdlib-only MT5 edge processes under Wine | Loops over bars or ticks. If Python iterates over market data, that code belongs in Rust |
| **QML + thin C++** | `q_terminal` UI. QML for every screen; C++ only for custom scene-graph render nodes and the generated side of the `cxx-qt` bridge | Business logic. C++ never computes; it moves buffers |
| **TypeScript / React** | `q_frontend`, the actively maintained research UI (§5.1) | Live trading and operations surfaces |
| **MQL5** | Tier B only: an Expert Advisor with pre-authorized local limits (§6.4) | Nothing today |

Rust over C++ for the core is decided on integration, not speed: PyO3/maturin for the
wheel, `cxx-qt` for Qt, `arrow-rs`/`parquet` for the lake. C++ enters only if a required
library ships C++-only.

**Binding surfaces are exactly two**, each with a real consumer: PyO3 (`q-py`) for
`q_backend` and the execution worker, and `cxx-qt` for `q_terminal`. There is no generic
C ABI. One is added only when a third consumer appears, and the first candidate is a
tier B DLL for the MQL5 EA, which is a decision for that phase.

### 5.1 UI ownership boundary

The boundary is **semantic**:

- **`q_frontend` is the research UI.** Backtests, optimization, discovery, walk-forward,
  feature and neural research, the AI strategy builder, storage and dataset management,
  system settings. It is actively maintained and new research surfaces go there. Its scope
  is bounded: it does not host live trading or operations, and it does not take on
  real-time market streams beyond what a research surface needs (for example a current
  quote next to a symbol picker).
- **`q_terminal` is the live trading and operations UI.** Quotes, forming bars,
  deployments, positions, orders, risk state, kill switch, worker and edge health, service
  status. It never grows a strategy editor, an optimizer, or a research result browser.

**Data size does not move a surface between UIs; it only chooses the rendering
technology.** A large optimization surface or a million-trade scatter is a research
visualization and stays in `q_frontend`, rendered on a WebGL2 canvas from Arrow-decoded
typed arrays instead of SVG. A dense live tape is an operations visualization and lives
in `q_terminal` on the Qt scene graph. WebGL2 in WebKitGTK is the known ceiling for
research visualizations; if a specific research surface exceeds it, that is a new decision
taken then, not a pre-authorized move into `q_terminal`.

The single seam between the two UIs is an **immutable saved strategy version**: research
produces it, the terminal deploys it (today's promote-to-deployment flow). A feature that
needs both an editor and a live view is split at that seam rather than built twice.

The existing execution workspace in `q_frontend` is removed the moment `q_terminal` has a
working one.

## 6. Execution safety

### 6.1 Fail-closed, restated

Unchanged from `paper-live-execution.md`: intent is durable before submission; ambiguous
broker outcomes block new orders for that deployment until reconciled; stale data, a lost
lease, or an unavailable ledger blocks new orders; reconciliation never resubmits.

### 6.2 Intent identity and idempotency

- Every order attempt has an **intent ID**: a UUID minted when the decision is recorded,
  stored in Postgres before any edge call, immutable for the life of the intent.
- The intent ID is carried to MT5 in the `magic` and `comment` fields (today's
  `intent_magic` / `intent_comment`), and the edge's `submit` request carries it
  explicitly.
- **At most one submission attempt per intent, ever.** A timeout, a transport error, an
  edge restart, or an unknown retcode moves the intent to `UNKNOWN`; it is never retried.
  Resolution is by lookup only: the edge's `lookup {intent_id, window}` searches active
  orders, positions, and deal history within the intent's time window for the magic and
  comment. Outcomes are `filled` (with deal details), `rejected`, `not_found`, or
  `unavailable`. Only `filled`, `rejected`, or `not_found` close the intent;
  `unavailable` leaves it pending and blocking.
- A new order for the same signal is a **new intent**, minted only after the prior intent
  is closed as `rejected` or `not_found`, and only if the strategy still wants it on a
  later bar. There is no automatic resend.
- The edge is stateless across restarts but idempotent within a process lifetime: it keeps
  a table of intent IDs it has attempted and answers a duplicate `submit` with
  `duplicate_intent` rather than calling `order_send`. The authoritative deduplication is
  still the lookup path.

### 6.3 Edge process contract

The data gateway and the execution edge are separate processes with separate contracts in
`q_contracts/edge/`. Both are stdlib Python plus `MetaTrader5` and `numpy`, never import
`q_backend`, expose `/v1/health` with `mt5_connected` and `terminal_build`, and refuse
mismatched schema majors. The execution edge additionally exposes `quote`, `check`,
`submit`, `lookup`, `positions`, and `deals`, and is bound to loopback only. A Windows VM
running the same processes is a drop-in fallback for Wine.

### 6.4 Tier B risk model

A 10–50 ms decision path cannot make a synchronous round trip to Linux for every action.
The EA therefore enforces **pre-authorized local limits** on every action without asking:

- allowed symbols and session hours;
- maximum order size, maximum net position, maximum orders per minute;
- maximum daily realized loss and maximum open loss, computed locally from deal history;
- a local kill flag;
- a **heartbeat deadline**: if no supervisor heartbeat arrives within a configured window
  (default 5 s), the EA stops opening new positions; whether it also flattens is a
  per-deployment setting, default off.

The Linux worker's role becomes supervision: it pushes signed limit updates and heartbeats
through the edge, reads deals for reconciliation into the same Postgres ledger, sets the
kill flag, and can flatten through the tier A path. Limits only tighten without a fresh
signed update; a missing or malformed update never loosens anything. The EA logs every
decision and every rejection locally and the worker ingests those logs into the ledger.
The EA is not a strategy DSL; a tier B strategy is compiled from the same `q_core`
semantics into MQL5 by a generator that is itself tested against the parity suite.

## 7. Repositories

Five repositories. Dependencies flow strictly downward.

```
q_contracts     schemas and generated types; single source of truth for every cross-process payload
     │
q_core          Rust workspace; publishes a wheel; consumed as a git dependency by q_terminal
     │
     ├── q_backend      Python; depends on the q_core wheel; implements the edge contracts
     │        │
     │        └── q_frontend    research UI; REST + stream from q_backend
     │
     └── q_terminal     Qt; links q_core via cxx-qt; stream + control API from q_backend
```

| Repo | Language | Owns | Publishes |
| --- | --- | --- | --- |
| `q_contracts` | schema files | OpenAPI for the control API; Arrow schemas for every columnar payload; stream topics, envelope, retention and backpressure policy; **the Wine edge wire contracts**; the dataset manifest schema | Generated types for Python, TypeScript, Rust, and C++, committed to the repo by its own CI |
| `q_core` | Rust | Crates: `q-indicators`, `q-engine` (candle + tick kernels, fills, exits, sizing), `q-buffers` (columnar ring buffers, Arrow), `q-io` (Parquet/Arrow codecs and readers), `q-py` (PyO3) | Wheel built by maturin, tagged; the golden determinism, causality, and backtest↔live parity suites port here and gate every kernel |
| `q_backend` | Python | Research orchestration; control API; outbox and relay; stream endpoint; dataset catalog and lake lifecycle; Dramatiq workers; the execution worker; the Wine gateway and edge scripts (implementations of `q_contracts/edge/`) | Container image; systemd unit files |
| `q_frontend` | TypeScript | Research UI (§5.1), including WebGL2 rendering for large research visualizations | Tauri desktop bundle |
| `q_terminal` | QML, Rust, thin C++ | Live trading and operations UI; direct catalog-driven Parquet reads via `q_core` | Native Linux desktop app |

### 7.1 Keeping multi-repo overhead low

The rules are chosen so that the common case, a change inside one repo, touches one repo.

- **Contracts are vendored, not installed.** Each consumer repo carries the generated code
  for its language under a `contracts/` directory plus a `CONTRACTS_REV` file holding the
  `q_contracts` commit hash. A `make contracts` target regenerates from that commit. CI in
  each consumer fails if the vendored code differs from a clean generation at the pinned
  commit. There is no package registry for contracts and no semver ceremony; the pin is a
  commit hash and the diff is reviewable.
- **Additive changes are the default.** New fields are optional, new topics are ignored by
  old subscribers, new endpoints do not change old ones. Consumers update their pin when
  they want the new thing. Breaking changes bump the schema major in the envelope, and the
  API serves both majors for one release cycle.
- **`q_core` is pinned by git tag** in `q_backend` (`uv` dependency on a tagged wheel from
  a local index or a git source) and in `q_terminal` (Cargo git dependency by tag). Tags
  are `vYYYY.MM.DD[.n]`, not semver; the parity suite is the compatibility check.
- **A compatibility file** at `q_contracts/COMPAT.md` lists the last known good pins of
  every repo together. Updating it is part of any cross-repo change and is the only
  cross-repo bookkeeping.
- **Cross-repo docs link by URL to a pinned commit**, never by relative path into a sibling
  checkout. The existing relative links from `q_backend/README.md` into `q_frontend/docs`
  are updated in phase 1, and the Tauri bundle stops reaching into `../../q_backend`.

## 8. Service lifecycle

All backend services run as **systemd user units**, as the Wine gateway already does.
No UI process launches, supervises, or stops a backend service.

| Unit | Depends on | Readiness |
| --- | --- | --- |
| `postgres.service` (podman quadlet) | — | `pg_isready` |
| `redis.service` (podman quadlet) | — | `redis-cli ping` |
| `q-api.service` | `Requires=postgres` `Wants=redis` `After=` both | `Type=notify`, `sd_notify(READY=1)` after migrations check and Postgres connection |
| `q-outbox-relay.service` | `Requires=postgres redis` | `Type=notify` after first successful `XADD` or confirmed empty backlog |
| `q-research-worker.service` | `Requires=postgres redis` | `Type=notify` after broker connection |
| `mt5-terminal.service` | — | health-wait loop (existing) |
| `mt5-gateway.service`, `mt5-edge.service` | `BindsTo=mt5-terminal` `After=mt5-terminal` | `/v1/health` returns `mt5_connected: true` |
| `q-execution-worker.service` | `Requires=postgres` `Wants=redis mt5-edge` `After=` all | `Type=notify` after recovery completes and a lease is acquired or confirmed idle |

`Restart=on-failure` with backoff on every unit. `Wants=` rather than `Requires=` where
the service can run degraded, as defined below.

### 8.1 Degraded behavior

| Unavailable | API | Execution worker | `q_frontend` | `q_terminal` |
| --- | --- | --- | --- | --- |
| Redis | REST works; stream endpoint answers `503 stream_unavailable`; publishes are skipped and the relay catches up later | Keeps trading. Redis is fan-out only; the outbox in Postgres is authoritative | Falls back to bounded polling for job progress, shows a "live updates unavailable" pill | Shows disconnected stream, keeps last state, controls stay enabled because commands go over REST |
| Postgres | Every persistence-backed route answers `503`; health reports it | **Fails closed:** no new orders, existing positions retained, lease heartbeat stops and the lease expires | Error state per surface, no error wall | Marks all deployments unknown, disables start and deploy, keeps flatten and kill switch enabled if the edge is reachable |
| API | — | Unaffected; the worker does not depend on the API | Offline state, cached last results read-only | Offline state; direct-Parquet views still work from cached manifests; no commands |
| Execution worker | Health shows stale worker heartbeat | — | Execution surfaces are gone from `q_frontend` after phase 4 | Shows worker down, disables start and deploy, keeps kill switch which is a Postgres flag the worker honors on return |
| MT5 edge or terminal | Health shows `mt5_connected: false` | No quotes → quote freshness gate fails → no new orders; pending unknowns stay pending | Market data routes fall back to the local store as today | Quotes marked stale with age shown; flatten disabled because it cannot be executed; kill switch still settable |
| Outbox relay | Stream falls behind; `seq` gaps appear to clients | Unaffected | Progress stalls, polling fallback engages after a timeout | Detects the gap by `seq`, fetches from REST history, shows stream lag |

Every client reconnects to the stream with exponential backoff capped at 30 s and re-runs
the snapshot protocol (§4.2) on every reconnect. No client trusts a cached view older than
the age it displays.

## 9. Invariant rules

1. **One implementation of shared semantics.** Any semantic that both research and
   execution depend on exists once, in `q_core`. No Python, QML, C++, or MQL5
   reimplementation, including temporary ones; tier B MQL5 is generated from `q_core`
   semantics and tested against the parity suite.
2. **Every cross-process payload has a `q_contracts` schema**, including the Wine edge
   contracts, the dataset manifest, and the stream envelope. No ad hoc JSON, no
   hand-written type mirrors.
3. **No Linux-side process imports `MetaTrader5`.** It exists only inside the Wine prefix
   in stdlib-only edge processes behind contracts.
4. **Execution fails closed** (§6.1) and **an intent is submitted at most once** (§6.2).
5. **Columnar, no per-row objects, bounded copies** (§4.6). Zero-copy is a tool, not a
   rule.
6. **Datasets are immutable and catalog-addressed** (§4.7). No process discovers data by
   listing directories.
7. **Durable events are never dropped; ephemeral events may be coalesced** (§4.4).
8. **No UI process owns a backend process** (§8).
9. **Ownership of a surface is semantic, not size-based** (§5.1).

## 10. Roadmap

| Phase | Work | Why in this position |
| --- | --- | --- |
| 1 | `q_contracts` with today's REST and job payloads, the stream envelope, the topic policy file, and the existing gateway contract moved in. Vendoring targets and `CONTRACTS_REV` in `q_backend` and `q_frontend`. Outbox table and relay, Redis Streams, Arrow WebSocket endpoint in `q_backend`; `q_frontend` adopts it for job progress with polling kept as the degraded fallback. Dataset catalog over the existing lake layout. DuckDB over the lake. systemd units replace the Tauri-spawned compose stack. | Validates transport and lifecycle before `q_terminal` exists; removes most polling and the shell coupling immediately |
| 2 | `q_core` bootstrapped: `q-indicators`, `q-buffers`, `q-io`, then the candle and tick kernels behind PyO3. Parity, causality, and determinism suites become the gate. The execution worker's `StrategyEvaluator` calls `q_core` for evaluation and nothing else changes in it. | The candle loop is the largest research win, and the evaluator swap proves the Rust scope in execution without touching orchestration |
| 3 | `q_terminal` vertical slice: one live symbol, forming bars, fed only by the stream, rendered by a custom scene-graph node from a `q_core` buffer, plus a catalog-driven historical load. No controls yet. | Proves the data path, the snapshot protocol, and the FFI end to end before any product surface |
| 4 | Wine execution edge implementing `q_contracts/edge/execution`. Intent idempotency and lookup semantics in the worker. Execution and operations workspace in `q_terminal`; remove it from `q_frontend`. | Live trading lands where it will live; the boundary is enforced at once |
| 5 | WebGL2 canvas path in `q_frontend` for large research visualizations. Further `q_terminal` operations views as needed. | Incremental, no architectural change |
| 6 (conditional) | Tier B: EA with local limits, supervisor protocol, MQL5 generator from `q_core`, and only then a decision on a C ABI. | Only when a strategy demands tick-reactive execution |

## 11. Explicitly dropped or deferred

- **Monorepo:** not now. The two existing repos stay; §7.1 bounds the overhead. Folding
  into a monorepo later would keep the same five directories and boundaries.
- **UE5 Pixel Streaming background (WO210–WO214):** dropped. It spends the GPU and decode
  budget the visualizations need, and its transport spike existed to work around
  WebKitGTK, which `q_terminal` does not use. The offline UE5/Blender asset pipeline is
  unaffected.
- **Windows as a desktop target:** dropped. MT5 runs under Wine, or in a VM as a fallback.
- **Electron or any Chromium shell:** rejected. `q_terminal` is native; `q_frontend` stays
  on Tauri.
- **Native Rust GUI (egui/iced) for `q_terminal`:** rejected in favor of Qt. Revisit only
  if a visualization outgrows the Qt scene graph, in which case a single native `wgpu`
  window is added, not a toolkit migration.
- **A `q-execution` Rust crate and any Rust orchestration in the execution worker:**
  dropped pending a profile that shows Python orchestration as the bottleneck.
- **A generic C ABI from `q_core`:** deferred until a third consumer exists.
- **Sub-millisecond execution (tier C):** out of scope through MT5.

## 12. Risks

| Risk | Mitigation |
| --- | --- |
| Wine proves unreliable for order submission | Edge contract is VM-portable; validate under Wine in paper mode and through the existing live gates before any live activation |
| Kernel port changes results | Byte-identical determinism suite and backtest↔live parity suite gate each kernel; port one module at a time |
| Two UIs drift | Semantic ownership rule, single strategy-version seam, removal of duplicated surfaces on arrival, vendored contracts as the only type source |
| Multi-repo pinning slows a solo developer | Commit-hash pins, vendored generation, additive-by-default schemas, one `COMPAT.md`; no registry, no semver ceremony |
| Snapshot/stream inconsistency | Outbox watermark read in the same transaction as the snapshot; per-topic `seq` and `epoch`; gap detection and re-snapshot are the same code path as first connect |
| Redis loss or retention overrun | Durable topics replay from Postgres; `stream_epoch` and `cursor_expired` force re-snapshot; ephemeral topics resume from `latest` |
| Duplicate orders on timeout or retry | One submission per intent, lookup-only resolution, edge-side duplicate rejection, intent ID in `magic` and `comment` |
| Tier B EA acts outside supervision | Pre-authorized local limits that only tighten, heartbeat deadline, local kill flag, full local decision log ingested into the ledger |
| `cxx-qt` gaps for custom render nodes | C++ is budgeted for scene-graph nodes and nothing else |
| `q_terminal` becomes a second research UI | The "never grows an editor, optimizer, or result browser" rule; size never moves a surface |

## 13. Related documents

- `q-frontend-tech-stack.md` — research UI stack; §1–§2 superseded on topology.
- `paper-live-execution.md` — execution domain and invariants; extended by §6 here.
- `mt5-remote-gateway.md`, `q_backend/docs/mt5-wine-gateway.md` — the Wine data gateway
  pattern that the execution edge generalizes; its contract moves to `q_contracts/edge/`.
- `runtime-performance.md` — WebKitGTK budgets, still applicable to `q_frontend`.
