// GENERATED FILE - DO NOT EDIT. Source schemas: schema/stream/control/cursor-expired.schema.json, schema/stream/control/epoch-changed.schema.json, schema/stream/control/lagging.schema.json, schema/stream/control/subscribe.schema.json, schema/stream/control/subscribed.schema.json, schema/stream/envelope.schema.json, schema/stream/payloads/job-progress.schema.json, schema/stream/payloads/job-terminal.schema.json

export interface CursorExpiredFrame {
  cursor?: string
  topic: string
}

export interface EpochChangedFrame {
  new_epoch: string
  previous_epoch?: string
  topic: string
}

export interface JobProgressPayload {
  job_id: string
  kind: "alpha_research" | "backtest" | "discovery_ab" | "encoder_ablation" | "neural_training" | "optimization" | "storage_ingest" | "strategy_search" | "walkforward"
  message?: string
  progress: number | null
  status: "queued" | "running"
}

export interface JobTerminalPayload {
  error?: string
  finished_at: string
  job_id: string
  kind: "alpha_research" | "backtest" | "discovery_ab" | "encoder_ablation" | "neural_training" | "optimization" | "storage_ingest" | "strategy_search" | "walkforward"
  status: "completed" | "failed" | "cancelled"
}

export interface LaggingFrame {
  from_seq: number
  topic: string
}

export interface StreamEnvelope {
  epoch: string
  key?: { job_id?: string; kind?: string; symbol?: string; timeframe?: string }
  origin_ts: string
  payload: string | Record<string, unknown>
  payload_kind: "arrow_ipc" | "control"
  payload_schema: string
  producer_id: string
  schema_major: number
  seq: number
  topic: "bars.completed" | "bars.forming" | "decisions" | "deployments" | "fills" | "jobs.progress" | "jobs.terminal" | "ledger" | "orders" | "quotes" | "risk"
}

export interface SubscribeFrame {
  topics: Array<string>
}

export interface SubscribedFrame {
  topics: Record<string, unknown>
}
