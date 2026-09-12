// GENERATED FILE - DO NOT EDIT. Source schemas: schema/stream/control/cursor-expired.schema.json, schema/stream/control/epoch-changed.schema.json, schema/stream/control/lagging.schema.json, schema/stream/control/subscribe.schema.json, schema/stream/control/subscribed.schema.json, schema/stream/control/subscription-rejected.schema.json, schema/stream/envelope.schema.json, schema/stream/framing.schema.json, schema/stream/jobs/progress.schema.json, schema/stream/jobs/terminal.schema.json, schema/stream/replay/history.schema.json, schema/stream/replay/latest.schema.json, schema/stream/replay/watermark.schema.json, schema/stream/topics.yaml

export interface CursorExpiredFrame {
  cursor?: string
  topic: string
}

export interface EpochChangedFrame {
  new_epoch: string
  previous_epoch?: string
  topic: string
}

export interface HistoryResponse {
  entries: Array<StreamEnvelope>
  epoch: string
  from_seq: number
  to_seq: number
  topic: string
}

export interface JobProgressPayload {
  detail?: string
  error?: string | null
  job_id: string
  progress: number
  status: "queued" | "running" | "progress"
  timestamp?: string
}

export interface JobTerminalPayload {
  completed_at?: string
  error?: string | null
  job_id: string
  result?: Record<string, unknown>
  status: "completed" | "failed" | "cancelled"
}

export interface LaggingFrame {
  from_seq: number
  topic: string
}

export interface LatestResponse {
  epoch: string
  origin_ts?: string
  payload: string | Record<string, unknown>
  producer_id?: string
  routing_key?: string
  seq: number
  topic: string
}

export interface StreamEnvelope {
  epoch: string
  origin_ts: string
  payload: string | Record<string, unknown>
  payload_kind: "arrow_ipc" | "control"
  payload_schema: string
  producer_id: string
  routing_key?: string
  schema_major: number
  seq: number
  topic: "bars.completed" | "bars.forming" | "decisions" | "deployments" | "fills" | "jobs.progress" | "jobs.terminal" | "ledger" | "orders" | "quotes" | "risk"
}

export interface SubscribeFrame {
  cursors?: Record<string, unknown>
  topics: Array<string>
}

export interface SubscribedFrame {
  topics: Record<string, unknown>
}

export interface SubscriptionRejectedFrame {
  code?: string
  reason: string
  topics: Array<string>
}

export interface WatermarkResponse {
  epoch?: string
  watermarks: Record<string, unknown>
}

export interface WebSocketBinaryHeader {
  epoch: string
  origin_ts: string
  payload_kind: "arrow_ipc" | "control"
  payload_length: number
  payload_schema: string
  producer_id: string
  routing_key?: string
  schema_major: number
  seq: number
  topic: "bars.completed" | "bars.forming" | "decisions" | "deployments" | "fills" | "jobs.progress" | "jobs.terminal" | "ledger" | "orders" | "quotes" | "risk"
}

export interface TopicRetention {
  duration: string
  entries: number
}

export interface TopicBackpressure {
  coalesce: boolean
  coalesce_key?: Array<string>
  on_overflow: string
}

export interface TopicPolicy {
  backpressure: TopicBackpressure
  class: string
  notes?: string
  payload_schema: string
  replay: string
  retention: TopicRetention
}

export const TOPIC_NAMES: Array<string> = [
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

export const TOPIC_POLICIES: Record<string, TopicPolicy> = {
  "bars.completed": {
    backpressure: {
      coalesce: false,
      on_overflow: "lag"
    },
    class: "ephemeral",
    notes: "Completed OHLCV bars. Ephemeral live stream but never coalesced; on backpressure overflow consumer is marked lagging to fetch gap from REST history. Bounded to Redis retention window (~24h).",
    payload_schema: "schema/api/arrow/bars.schema.json",
    replay: "retention_only",
    retention: {
      duration: "P1D",
      entries: 100000
    }
  },
  "bars.forming": {
    backpressure: {
      coalesce: true,
      coalesce_key: ["symbol", "timeframe"],
      on_overflow: "coalesce"
    },
    class: "ephemeral",
    notes: "Live forming OHLCV bars; coalesced per (symbol, timeframe) keeping latest forming bar. Bounded to Redis retention window (~1h).",
    payload_schema: "schema/api/arrow/bars.schema.json",
    replay: "retention_only",
    retention: {
      duration: "PT1H",
      entries: 10000
    }
  },
  "decisions": {
    backpressure: {
      coalesce: false,
      on_overflow: "lag"
    },
    class: "durable",
    notes: "Durable trading decisions; replayable unbounded via REST history.",
    payload_schema: "schema/stream/envelope.schema.json",
    replay: "unbounded",
    retention: {
      duration: "P1D",
      entries: 200000
    }
  },
  "deployments": {
    backpressure: {
      coalesce: false,
      on_overflow: "lag"
    },
    class: "durable",
    notes: "Durable strategy deployment lifecycle states; replayable unbounded via REST history.",
    payload_schema: "schema/stream/envelope.schema.json",
    replay: "unbounded",
    retention: {
      duration: "P1D",
      entries: 200000
    }
  },
  "fills": {
    backpressure: {
      coalesce: false,
      on_overflow: "lag"
    },
    class: "durable",
    notes: "Durable fill events; must never be coalesced or dropped; replayable unbounded via REST history.",
    payload_schema: "schema/stream/envelope.schema.json",
    replay: "unbounded",
    retention: {
      duration: "P1D",
      entries: 200000
    }
  },
  "jobs.progress": {
    backpressure: {
      coalesce: true,
      coalesce_key: ["job_id"],
      on_overflow: "coalesce"
    },
    class: "ephemeral",
    notes: "Ephemeral job progress updates; coalesced per job_id keeping latest. Paired with durable jobs.terminal for non-droppable terminal states.",
    payload_schema: "schema/stream/jobs/progress.schema.json",
    replay: "retention_only",
    retention: {
      duration: "P1D",
      entries: 50000
    }
  },
  "jobs.terminal": {
    backpressure: {
      coalesce: false,
      on_overflow: "lag"
    },
    class: "durable",
    notes: "Terminal states of jobs (completed, failed). Sourced durably from Postgres outbox; paired with ephemeral jobs.progress. Unlike progress updates, terminal job states are never coalesced or dropped.",
    payload_schema: "schema/stream/jobs/terminal.schema.json",
    replay: "unbounded",
    retention: {
      duration: "P1D",
      entries: 200000
    }
  },
  "ledger": {
    backpressure: {
      coalesce: false,
      on_overflow: "lag"
    },
    class: "durable",
    notes: "Durable ledger balance entries and cash movements; replayable unbounded via REST history.",
    payload_schema: "schema/stream/envelope.schema.json",
    replay: "unbounded",
    retention: {
      duration: "P1D",
      entries: 200000
    }
  },
  "orders": {
    backpressure: {
      coalesce: false,
      on_overflow: "lag"
    },
    class: "durable",
    notes: "Durable order lifecycle events; replayable unbounded via REST history.",
    payload_schema: "schema/stream/envelope.schema.json",
    replay: "unbounded",
    retention: {
      duration: "P1D",
      entries: 200000
    }
  },
  "quotes": {
    backpressure: {
      coalesce: true,
      coalesce_key: ["symbol"],
      on_overflow: "coalesce"
    },
    class: "ephemeral",
    notes: "Live market quotes; coalesced per symbol keeping latest. Replay bounded to Redis retention window (~1h).",
    payload_schema: "schema/api/arrow/ticks.schema.json",
    replay: "retention_only",
    retention: {
      duration: "PT1H",
      entries: 100000
    }
  },
  "risk": {
    backpressure: {
      coalesce: false,
      on_overflow: "lag"
    },
    class: "durable",
    notes: "Durable risk events and limit evaluations; replayable unbounded via REST history.",
    payload_schema: "schema/stream/envelope.schema.json",
    replay: "unbounded",
    retention: {
      duration: "P1D",
      entries: 200000
    }
  }
}
