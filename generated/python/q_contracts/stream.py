# GENERATED FILE - DO NOT EDIT. Source schemas: schema/stream/control/cursor-expired.schema.json, schema/stream/control/epoch-changed.schema.json, schema/stream/control/lagging.schema.json, schema/stream/control/subscribe.schema.json, schema/stream/control/subscribed.schema.json, schema/stream/control/subscription-rejected.schema.json, schema/stream/envelope.schema.json, schema/stream/framing.schema.json, schema/stream/jobs/progress.schema.json, schema/stream/jobs/terminal.schema.json, schema/stream/replay/history.schema.json, schema/stream/replay/latest.schema.json, schema/stream/replay/watermark.schema.json, schema/stream/topics.yaml
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class CursorExpiredFrame:
    topic: str
    cursor: str | None = None


@dataclass(frozen=True)
class EpochChangedFrame:
    new_epoch: str
    topic: str
    previous_epoch: str | None = None


@dataclass(frozen=True)
class HistoryResponse:
    entries: list[StreamEnvelope]
    epoch: str
    from_seq: int
    to_seq: int
    topic: str


@dataclass(frozen=True)
class JobProgressPayload:
    job_id: str
    progress: float
    status: Literal["queued", "running", "progress"]
    detail: str | None = None
    error: str | None = None
    timestamp: str | None = None


@dataclass(frozen=True)
class JobTerminalPayload:
    job_id: str
    status: Literal["completed", "failed", "cancelled"]
    completed_at: str | None = None
    error: str | None = None
    result: dict[str, Any] | None = None


@dataclass(frozen=True)
class LaggingFrame:
    from_seq: int
    topic: str


@dataclass(frozen=True)
class LatestResponse:
    epoch: str
    payload: str | dict[str, Any]
    seq: int
    topic: str
    origin_ts: str | None = None
    producer_id: str | None = None
    routing_key: str | None = None


@dataclass(frozen=True)
class StreamEnvelope:
    epoch: str
    origin_ts: str
    payload: str | dict[str, Any]
    payload_kind: Literal["arrow_ipc", "control"]
    payload_schema: str
    producer_id: str
    schema_major: int
    seq: int
    topic: Literal[
        "bars.completed",
        "bars.forming",
        "decisions",
        "deployments",
        "fills",
        "jobs.progress",
        "jobs.terminal",
        "ledger",
        "orders",
        "quotes",
        "risk",
    ]
    routing_key: str | None = None


@dataclass(frozen=True)
class SubscribeFrame:
    topics: list[str]
    cursors: dict[str, Any] | None = None


@dataclass(frozen=True)
class SubscribedFrame:
    topics: dict[str, Any]


@dataclass(frozen=True)
class SubscriptionRejectedFrame:
    reason: str
    topics: list[str]
    code: str | None = None


@dataclass(frozen=True)
class WatermarkResponse:
    watermarks: dict[str, Any]
    epoch: str | None = None


@dataclass(frozen=True)
class WebSocketBinaryHeader:
    epoch: str
    origin_ts: str
    payload_kind: Literal["arrow_ipc", "control"]
    payload_length: int
    payload_schema: str
    producer_id: str
    schema_major: int
    seq: int
    topic: Literal[
        "bars.completed",
        "bars.forming",
        "decisions",
        "deployments",
        "fills",
        "jobs.progress",
        "jobs.terminal",
        "ledger",
        "orders",
        "quotes",
        "risk",
    ]
    routing_key: str | None = None


@dataclass(frozen=True)
class TopicRetention:
    duration: str
    entries: int


@dataclass(frozen=True)
class TopicBackpressure:
    coalesce: bool
    on_overflow: str
    coalesce_key: list[str] | None = None


@dataclass(frozen=True)
class TopicPolicy:
    backpressure: TopicBackpressure
    class_: str
    payload_schema: str
    replay: str
    retention: TopicRetention
    notes: str | None = None


TOPIC_NAMES: tuple[str, ...] = (
    "bars.completed",
    "bars.forming",
    "decisions",
    "deployments",
    "fills",
    "jobs.progress",
    "jobs.terminal",
    "ledger",
    "orders",
    "quotes",
    "risk",
)


TOPIC_POLICIES: dict[str, TopicPolicy] = {
    "bars.completed": TopicPolicy(
        backpressure=TopicBackpressure(
            coalesce=False,
            on_overflow="lag",
            coalesce_key=None,
        ),
        class_="ephemeral",
        notes="Completed OHLCV bars. Ephemeral live stream but never coalesced; on backpressure overflow consumer is marked lagging to fetch gap from REST history. Bounded to Redis retention window (~24h).",
        payload_schema="schema/api/arrow/bars.schema.json",
        replay="retention_only",
        retention=TopicRetention(
            duration="P1D",
            entries=100000,
        ),
    ),
    "bars.forming": TopicPolicy(
        backpressure=TopicBackpressure(
            coalesce=True,
            on_overflow="coalesce",
            coalesce_key=["symbol", "timeframe"],
        ),
        class_="ephemeral",
        notes="Live forming OHLCV bars; coalesced per (symbol, timeframe) keeping latest forming bar. Bounded to Redis retention window (~1h).",
        payload_schema="schema/api/arrow/bars.schema.json",
        replay="retention_only",
        retention=TopicRetention(
            duration="PT1H",
            entries=10000,
        ),
    ),
    "decisions": TopicPolicy(
        backpressure=TopicBackpressure(
            coalesce=False,
            on_overflow="lag",
            coalesce_key=None,
        ),
        class_="durable",
        notes="Durable trading decisions; replayable unbounded via REST history.",
        payload_schema="schema/stream/envelope.schema.json",
        replay="unbounded",
        retention=TopicRetention(
            duration="P1D",
            entries=200000,
        ),
    ),
    "deployments": TopicPolicy(
        backpressure=TopicBackpressure(
            coalesce=False,
            on_overflow="lag",
            coalesce_key=None,
        ),
        class_="durable",
        notes="Durable strategy deployment lifecycle states; replayable unbounded via REST history.",
        payload_schema="schema/stream/envelope.schema.json",
        replay="unbounded",
        retention=TopicRetention(
            duration="P1D",
            entries=200000,
        ),
    ),
    "fills": TopicPolicy(
        backpressure=TopicBackpressure(
            coalesce=False,
            on_overflow="lag",
            coalesce_key=None,
        ),
        class_="durable",
        notes="Durable fill events; must never be coalesced or dropped; replayable unbounded via REST history.",
        payload_schema="schema/stream/envelope.schema.json",
        replay="unbounded",
        retention=TopicRetention(
            duration="P1D",
            entries=200000,
        ),
    ),
    "jobs.progress": TopicPolicy(
        backpressure=TopicBackpressure(
            coalesce=True,
            on_overflow="coalesce",
            coalesce_key=["job_id"],
        ),
        class_="ephemeral",
        notes="Ephemeral job progress updates; coalesced per job_id keeping latest. Paired with durable jobs.terminal for non-droppable terminal states.",
        payload_schema="schema/stream/jobs/progress.schema.json",
        replay="retention_only",
        retention=TopicRetention(
            duration="P1D",
            entries=50000,
        ),
    ),
    "jobs.terminal": TopicPolicy(
        backpressure=TopicBackpressure(
            coalesce=False,
            on_overflow="lag",
            coalesce_key=None,
        ),
        class_="durable",
        notes="Terminal states of jobs (completed, failed). Sourced durably from Postgres outbox; paired with ephemeral jobs.progress. Unlike progress updates, terminal job states are never coalesced or dropped.",
        payload_schema="schema/stream/jobs/terminal.schema.json",
        replay="unbounded",
        retention=TopicRetention(
            duration="P1D",
            entries=200000,
        ),
    ),
    "ledger": TopicPolicy(
        backpressure=TopicBackpressure(
            coalesce=False,
            on_overflow="lag",
            coalesce_key=None,
        ),
        class_="durable",
        notes="Durable ledger balance entries and cash movements; replayable unbounded via REST history.",
        payload_schema="schema/stream/envelope.schema.json",
        replay="unbounded",
        retention=TopicRetention(
            duration="P1D",
            entries=200000,
        ),
    ),
    "orders": TopicPolicy(
        backpressure=TopicBackpressure(
            coalesce=False,
            on_overflow="lag",
            coalesce_key=None,
        ),
        class_="durable",
        notes="Durable order lifecycle events; replayable unbounded via REST history.",
        payload_schema="schema/stream/envelope.schema.json",
        replay="unbounded",
        retention=TopicRetention(
            duration="P1D",
            entries=200000,
        ),
    ),
    "quotes": TopicPolicy(
        backpressure=TopicBackpressure(
            coalesce=True,
            on_overflow="coalesce",
            coalesce_key=["symbol"],
        ),
        class_="ephemeral",
        notes="Live market quotes; coalesced per symbol keeping latest. Replay bounded to Redis retention window (~1h).",
        payload_schema="schema/api/arrow/ticks.schema.json",
        replay="retention_only",
        retention=TopicRetention(
            duration="PT1H",
            entries=100000,
        ),
    ),
    "risk": TopicPolicy(
        backpressure=TopicBackpressure(
            coalesce=False,
            on_overflow="lag",
            coalesce_key=None,
        ),
        class_="durable",
        notes="Durable risk events and limit evaluations; replayable unbounded via REST history.",
        payload_schema="schema/stream/envelope.schema.json",
        replay="unbounded",
        retention=TopicRetention(
            duration="P1D",
            entries=200000,
        ),
    ),
}
