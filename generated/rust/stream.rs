// GENERATED FILE - DO NOT EDIT. Source schemas: schema/stream/control/cursor-expired.schema.json, schema/stream/control/epoch-changed.schema.json, schema/stream/control/lagging.schema.json, schema/stream/control/rejected.schema.json, schema/stream/control/subscribe.schema.json, schema/stream/control/subscribed.schema.json, schema/stream/envelope.schema.json, schema/stream/payloads/job-progress.schema.json, schema/stream/payloads/job-terminal.schema.json, schema/stream/replay/history-expired.schema.json, schema/stream/replay/history-page.schema.json, schema/stream/replay/latest.schema.json, schema/stream/replay/watermark.schema.json
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
pub struct HistoryExpiredResponse {
    pub oldest_available_seq: Option<serde_json::Value>,
    pub requested_from_seq: i64,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HistoryPageResponse {
    pub entries: Vec<StreamEnvelope>,
    pub epoch: String,
    pub next_seq: serde_json::Value,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct JobProgressPayload {
    pub job_id: String,
    pub kind: String,
    pub message: Option<String>,
    pub progress: serde_json::Value,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct JobTerminalPayload {
    pub error: Option<String>,
    pub finished_at: String,
    pub job_id: String,
    pub kind: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LaggingFrame {
    pub from_seq: i64,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LatestValuesResponse {
    pub entries: serde_json::Value,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RejectedFrame {
    pub detail: Option<String>,
    pub reason: String,
    pub topic: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SnapshotWatermark {
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StreamEnvelope {
    pub epoch: String,
    pub key: Option<serde_json::Value>,
    pub origin_ts: String,
    pub payload: serde_json::Value,
    pub payload_kind: String,
    pub payload_schema: String,
    pub producer_id: String,
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
