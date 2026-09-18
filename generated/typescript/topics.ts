// GENERATED FILE - DO NOT EDIT. Source schemas: schema/stream/topics.yaml

export interface TopicPolicy {
  name: string
  topic_class: "durable" | "ephemeral"
  retention_duration: string
  retention_entries: number
  coalesce_key: readonly string[]
  on_overflow: "lag" | "coalesce"
  replay: "unbounded" | "retention_only"
  payload_schema: string
}

export const TOPICS: Readonly<Record<string, TopicPolicy>> = {
  "bars.completed": {
    name: "bars.completed",
    topic_class: "ephemeral",
    retention_duration: "P1D",
    retention_entries: 100000,
    coalesce_key: [],
    on_overflow: "lag",
    replay: "retention_only",
    payload_schema: "schema/api/arrow/bars.schema.json",
  },
  "bars.forming": {
    name: "bars.forming",
    topic_class: "ephemeral",
    retention_duration: "PT1H",
    retention_entries: 10000,
    coalesce_key: ["symbol", "timeframe"],
    on_overflow: "coalesce",
    replay: "retention_only",
    payload_schema: "schema/api/arrow/bars.schema.json",
  },
  "decisions": {
    name: "decisions",
    topic_class: "durable",
    retention_duration: "P1D",
    retention_entries: 200000,
    coalesce_key: [],
    on_overflow: "lag",
    replay: "unbounded",
    payload_schema: "schema/stream/payloads/execution-decision.schema.json",
  },
  "deployments": {
    name: "deployments",
    topic_class: "durable",
    retention_duration: "P1D",
    retention_entries: 200000,
    coalesce_key: [],
    on_overflow: "lag",
    replay: "unbounded",
    payload_schema: "schema/stream/payloads/execution-deployment.schema.json",
  },
  "fills": {
    name: "fills",
    topic_class: "durable",
    retention_duration: "P1D",
    retention_entries: 200000,
    coalesce_key: [],
    on_overflow: "lag",
    replay: "unbounded",
    payload_schema: "schema/stream/payloads/execution-fill.schema.json",
  },
  "jobs.progress": {
    name: "jobs.progress",
    topic_class: "ephemeral",
    retention_duration: "P1D",
    retention_entries: 50000,
    coalesce_key: ["kind", "job_id"],
    on_overflow: "coalesce",
    replay: "retention_only",
    payload_schema: "schema/stream/payloads/job-progress.schema.json",
  },
  "jobs.terminal": {
    name: "jobs.terminal",
    topic_class: "durable",
    retention_duration: "P1D",
    retention_entries: 200000,
    coalesce_key: [],
    on_overflow: "lag",
    replay: "unbounded",
    payload_schema: "schema/stream/payloads/job-terminal.schema.json",
  },
  "ledger": {
    name: "ledger",
    topic_class: "durable",
    retention_duration: "P1D",
    retention_entries: 200000,
    coalesce_key: [],
    on_overflow: "lag",
    replay: "unbounded",
    payload_schema: "schema/stream/payloads/execution-ledger.schema.json",
  },
  "orders": {
    name: "orders",
    topic_class: "durable",
    retention_duration: "P1D",
    retention_entries: 200000,
    coalesce_key: [],
    on_overflow: "lag",
    replay: "unbounded",
    payload_schema: "schema/stream/payloads/execution-order.schema.json",
  },
  "quotes": {
    name: "quotes",
    topic_class: "ephemeral",
    retention_duration: "PT1H",
    retention_entries: 100000,
    coalesce_key: ["symbol"],
    on_overflow: "coalesce",
    replay: "retention_only",
    payload_schema: "schema/api/arrow/ticks.schema.json",
  },
  "risk": {
    name: "risk",
    topic_class: "durable",
    retention_duration: "P1D",
    retention_entries: 200000,
    coalesce_key: [],
    on_overflow: "lag",
    replay: "unbounded",
    payload_schema: "schema/stream/payloads/execution-risk.schema.json",
  },
}
