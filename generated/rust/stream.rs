// GENERATED FILE - DO NOT EDIT. Source schemas: schema/stream/control/cursor-expired.schema.json, schema/stream/control/epoch-changed.schema.json, schema/stream/control/lagging.schema.json, schema/stream/control/subscribe.schema.json, schema/stream/control/subscribed.schema.json, schema/stream/envelope.schema.json, schema/stream/payloads/job-progress.schema.json, schema/stream/payloads/job-terminal.schema.json
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
    pub topics: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SubscribedFrame {
    pub topics: serde_json::Value,
}
