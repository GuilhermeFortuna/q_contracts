// GENERATED FILE - DO NOT EDIT. Source schemas: schema/catalog/dataset-manifest.schema.json, schema/catalog/ml-entry-filter-manifest.schema.json
use serde::{Deserialize, Serialize};

pub type ChecksumHex = String;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DatasetManifest {
    pub arrow_schema: serde_json::Value,
    pub checksum_algorithm: String,
    pub dataset_id: String,
    pub files: Vec<serde_json::Value>,
    pub published_at: String,
    pub row_count: i64,
    pub state: String,
    pub subject: serde_json::Value,
    pub supersedes: Option<String>,
    pub time_range: serde_json::Value,
    pub tombstone: Option<serde_json::Value>,
    pub version: i64,
}

pub type FeatureDtype = String;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LabelDefinition {
    pub name: String,
    pub positive_class: String,
}

pub type MlEntryFilterManifest = serde_json::Value;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterDatasetManifest {
    pub bars_checksum: ChecksumHex,
    pub compatibility_fingerprint: ChecksumHex,
    pub dataset_content_id: ChecksumHex,
    pub dataset_id: String,
    pub engine_revision: String,
    pub format_version: String,
    pub kind: String,
    pub label: LabelDefinition,
    pub partition_counts: PartitionCounts,
    pub selected_features: Vec<OrderedFeature>,
    pub source_config_revision: String,
    pub source_run_id: String,
    pub trades_checksum: ChecksumHex,
    pub train_end: String,
    pub validation_end: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterModelManifest {
    pub algorithm: String,
    pub dataset_id: String,
    pub dependency_versions: serde_json::Value,
    pub fitted_artifact_checksum: ChecksumHex,
    pub format_version: String,
    pub hyperparameters: serde_json::Value,
    pub kind: String,
    pub model_content_id: ChecksumHex,
    pub model_version_id: String,
    pub preprocessing_recipe: Vec<PreprocessingStep>,
    pub seed: i64,
    pub selected_features: Vec<OrderedFeature>,
    pub training_label_availability_cutoff: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OrderedFeature {
    pub dtype: FeatureDtype,
    pub name: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PartitionCounts {
    pub lockbox: SamplePartitionCounts,
    pub train: SamplePartitionCounts,
    pub validation: SamplePartitionCounts,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PreprocessingStep {
    pub parameters: serde_json::Value,
    pub step: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SamplePartitionCounts {
    pub rejections: serde_json::Value,
    pub samples: i64,
}
