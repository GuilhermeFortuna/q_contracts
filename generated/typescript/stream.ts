// GENERATED FILE - DO NOT EDIT. Source schemas: schema/stream/control/cursor-expired.schema.json, schema/stream/control/epoch-changed.schema.json, schema/stream/control/lagging.schema.json, schema/stream/control/rejected.schema.json, schema/stream/control/subscribe.schema.json, schema/stream/control/subscribed.schema.json, schema/stream/envelope.schema.json, schema/stream/payloads/job-progress.schema.json, schema/stream/payloads/job-terminal.schema.json, schema/stream/replay/history-expired.schema.json, schema/stream/replay/history-page.schema.json, schema/stream/replay/latest.schema.json, schema/stream/replay/watermark.schema.json

export interface CursorExpiredFrame {
  cursor?: string
  topic: string
  type: "cursor_expired"
}

export interface EpochChangedFrame {
  new_epoch: string
  previous_epoch?: string
  topic: string
  type: "epoch_changed"
}

export interface HistoryExpiredResponse {
  oldest_available_seq?: number | null
  requested_from_seq: number
  topic: string
}

export interface HistoryPageResponse {
  entries: Array<StreamEnvelope>
  epoch: string
  next_seq: number | null
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
  type: "lagging"
}

export interface LatestValuesResponse {
  entries: Record<string, unknown>
  topic: string
}

export interface RejectedFrame {
  detail?: string
  reason: "unknown_topic" | "unsupported_schema_major" | "stream_unavailable" | "invalid_frame"
  topic?: string
  type: "rejected"
}

export interface SnapshotWatermark {
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
  cursors?: Record<string, unknown>
  topics: Array<string>
}

export interface SubscribedFrame {
  topics: Record<string, unknown>
  type: "subscribed"
}
