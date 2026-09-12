// GENERATED FILE - DO NOT EDIT. Source schemas: schema/stream/control/cursor-expired.schema.json, schema/stream/control/epoch-changed.schema.json, schema/stream/control/lagging.schema.json, schema/stream/control/subscribe.schema.json, schema/stream/control/subscribed.schema.json, schema/stream/control/subscription-rejected.schema.json, schema/stream/envelope.schema.json, schema/stream/framing.schema.json, schema/stream/jobs/progress.schema.json, schema/stream/jobs/terminal.schema.json, schema/stream/replay/history.schema.json, schema/stream/replay/latest.schema.json, schema/stream/replay/watermark.schema.json, schema/stream/topics.yaml
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CursorExpiredFrame {
    pub cursor: Option<String>,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EpochChangedFrame {
    pub new_epoch: String,
    pub previous_epoch: Option<String>,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HistoryResponse {
    pub entries: Vec<StreamEnvelope>,
    pub epoch: String,
    pub from_seq: i64,
    pub to_seq: i64,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct JobProgressPayload {
    pub detail: Option<String>,
    pub error: Option<String>,
    pub job_id: String,
    pub progress: f64,
    pub status: String,
    pub timestamp: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct JobTerminalPayload {
    pub completed_at: Option<String>,
    pub error: Option<String>,
    pub job_id: String,
    pub result: Option<serde_json::Value>,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LaggingFrame {
    pub from_seq: i64,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LatestResponse {
    pub epoch: String,
    pub origin_ts: Option<String>,
    pub payload: serde_json::Value,
    pub producer_id: Option<String>,
    pub routing_key: Option<String>,
    pub seq: i64,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StreamEnvelope {
    pub epoch: String,
    pub origin_ts: String,
    pub payload: serde_json::Value,
    pub payload_kind: String,
    pub payload_schema: String,
    pub producer_id: String,
    pub routing_key: Option<String>,
    pub schema_major: i64,
    pub seq: i64,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SubscribeFrame {
    pub cursors: Option<serde_json::Value>,
    pub topics: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SubscribedFrame {
    pub topics: serde_json::Value,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SubscriptionRejectedFrame {
    pub code: Option<String>,
    pub reason: String,
    pub topics: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WatermarkResponse {
    pub epoch: Option<String>,
    pub watermarks: serde_json::Value,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WebSocketBinaryHeader {
    pub epoch: String,
    pub origin_ts: String,
    pub payload_kind: String,
    pub payload_length: i64,
    pub payload_schema: String,
    pub producer_id: String,
    pub routing_key: Option<String>,
    pub schema_major: i64,
    pub seq: i64,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TopicRetention {
    pub duration: String,
    pub entries: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TopicBackpressure {
    pub coalesce: bool,
    pub coalesce_key: Option<Vec<String>>,
    pub on_overflow: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TopicPolicy {
    pub backpressure: TopicBackpressure,
    #[serde(rename = "class")]
    pub r#class: String,
    pub notes: Option<String>,
    pub payload_schema: String,
    pub replay: String,
    pub retention: TopicRetention,
}

pub const TOPIC_NAMES: &[&str] = &[
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
];

pub fn get_topic_policy(topic: &str) -> Option<TopicPolicy> {
    match topic {
        "bars.completed" => Some(TopicPolicy {
            backpressure: TopicBackpressure {
                coalesce: false,
                coalesce_key: None,
                on_overflow: "lag".to_string(),
            },
            r#class: "ephemeral".to_string(),
            notes: Some("Completed OHLCV bars. Ephemeral live stream but never coalesced; on backpressure overflow consumer is marked lagging to fetch gap from REST history. Bounded to Redis retention window (~24h).".to_string()),
            payload_schema: "schema/api/arrow/bars.schema.json".to_string(),
            replay: "retention_only".to_string(),
            retention: TopicRetention {
                duration: "P1D".to_string(),
                entries: 100000,
            },
        }),
        "bars.forming" => Some(TopicPolicy {
            backpressure: TopicBackpressure {
                coalesce: true,
                coalesce_key: Some(vec!["symbol".to_string(), "timeframe".to_string()]),
                on_overflow: "coalesce".to_string(),
            },
            r#class: "ephemeral".to_string(),
            notes: Some("Live forming OHLCV bars; coalesced per (symbol, timeframe) keeping latest forming bar. Bounded to Redis retention window (~1h).".to_string()),
            payload_schema: "schema/api/arrow/bars.schema.json".to_string(),
            replay: "retention_only".to_string(),
            retention: TopicRetention {
                duration: "PT1H".to_string(),
                entries: 10000,
            },
        }),
        "decisions" => Some(TopicPolicy {
            backpressure: TopicBackpressure {
                coalesce: false,
                coalesce_key: None,
                on_overflow: "lag".to_string(),
            },
            r#class: "durable".to_string(),
            notes: Some("Durable trading decisions; replayable unbounded via REST history.".to_string()),
            payload_schema: "schema/stream/envelope.schema.json".to_string(),
            replay: "unbounded".to_string(),
            retention: TopicRetention {
                duration: "P1D".to_string(),
                entries: 200000,
            },
        }),
        "deployments" => Some(TopicPolicy {
            backpressure: TopicBackpressure {
                coalesce: false,
                coalesce_key: None,
                on_overflow: "lag".to_string(),
            },
            r#class: "durable".to_string(),
            notes: Some("Durable strategy deployment lifecycle states; replayable unbounded via REST history.".to_string()),
            payload_schema: "schema/stream/envelope.schema.json".to_string(),
            replay: "unbounded".to_string(),
            retention: TopicRetention {
                duration: "P1D".to_string(),
                entries: 200000,
            },
        }),
        "fills" => Some(TopicPolicy {
            backpressure: TopicBackpressure {
                coalesce: false,
                coalesce_key: None,
                on_overflow: "lag".to_string(),
            },
            r#class: "durable".to_string(),
            notes: Some("Durable fill events; must never be coalesced or dropped; replayable unbounded via REST history.".to_string()),
            payload_schema: "schema/stream/envelope.schema.json".to_string(),
            replay: "unbounded".to_string(),
            retention: TopicRetention {
                duration: "P1D".to_string(),
                entries: 200000,
            },
        }),
        "jobs.progress" => Some(TopicPolicy {
            backpressure: TopicBackpressure {
                coalesce: true,
                coalesce_key: Some(vec!["job_id".to_string()]),
                on_overflow: "coalesce".to_string(),
            },
            r#class: "ephemeral".to_string(),
            notes: Some("Ephemeral job progress updates; coalesced per job_id keeping latest. Paired with durable jobs.terminal for non-droppable terminal states.".to_string()),
            payload_schema: "schema/stream/jobs/progress.schema.json".to_string(),
            replay: "retention_only".to_string(),
            retention: TopicRetention {
                duration: "P1D".to_string(),
                entries: 50000,
            },
        }),
        "jobs.terminal" => Some(TopicPolicy {
            backpressure: TopicBackpressure {
                coalesce: false,
                coalesce_key: None,
                on_overflow: "lag".to_string(),
            },
            r#class: "durable".to_string(),
            notes: Some("Terminal states of jobs (completed, failed). Sourced durably from Postgres outbox; paired with ephemeral jobs.progress. Unlike progress updates, terminal job states are never coalesced or dropped.".to_string()),
            payload_schema: "schema/stream/jobs/terminal.schema.json".to_string(),
            replay: "unbounded".to_string(),
            retention: TopicRetention {
                duration: "P1D".to_string(),
                entries: 200000,
            },
        }),
        "ledger" => Some(TopicPolicy {
            backpressure: TopicBackpressure {
                coalesce: false,
                coalesce_key: None,
                on_overflow: "lag".to_string(),
            },
            r#class: "durable".to_string(),
            notes: Some("Durable ledger balance entries and cash movements; replayable unbounded via REST history.".to_string()),
            payload_schema: "schema/stream/envelope.schema.json".to_string(),
            replay: "unbounded".to_string(),
            retention: TopicRetention {
                duration: "P1D".to_string(),
                entries: 200000,
            },
        }),
        "orders" => Some(TopicPolicy {
            backpressure: TopicBackpressure {
                coalesce: false,
                coalesce_key: None,
                on_overflow: "lag".to_string(),
            },
            r#class: "durable".to_string(),
            notes: Some("Durable order lifecycle events; replayable unbounded via REST history.".to_string()),
            payload_schema: "schema/stream/envelope.schema.json".to_string(),
            replay: "unbounded".to_string(),
            retention: TopicRetention {
                duration: "P1D".to_string(),
                entries: 200000,
            },
        }),
        "quotes" => Some(TopicPolicy {
            backpressure: TopicBackpressure {
                coalesce: true,
                coalesce_key: Some(vec!["symbol".to_string()]),
                on_overflow: "coalesce".to_string(),
            },
            r#class: "ephemeral".to_string(),
            notes: Some("Live market quotes; coalesced per symbol keeping latest. Replay bounded to Redis retention window (~1h).".to_string()),
            payload_schema: "schema/api/arrow/ticks.schema.json".to_string(),
            replay: "retention_only".to_string(),
            retention: TopicRetention {
                duration: "PT1H".to_string(),
                entries: 100000,
            },
        }),
        "risk" => Some(TopicPolicy {
            backpressure: TopicBackpressure {
                coalesce: false,
                coalesce_key: None,
                on_overflow: "lag".to_string(),
            },
            r#class: "durable".to_string(),
            notes: Some("Durable risk events and limit evaluations; replayable unbounded via REST history.".to_string()),
            payload_schema: "schema/stream/envelope.schema.json".to_string(),
            replay: "unbounded".to_string(),
            retention: TopicRetention {
                duration: "P1D".to_string(),
                entries: 200000,
            },
        }),
        _ => None,
    }
}

pub fn all_topic_policies() -> Vec<(&'static str, TopicPolicy)> {
    TOPIC_NAMES
        .iter()
        .filter_map(|&name| get_topic_policy(name).map(|policy| (name, policy)))
        .collect()
}
