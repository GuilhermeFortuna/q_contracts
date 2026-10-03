// GENERATED FILE - DO NOT EDIT. Source schemas: schema/catalog/dataset-manifest.schema.json, schema/catalog/ml-entry-filter-manifest.schema.json

export type ChecksumHex = string

export interface DatasetManifest {
  arrow_schema: { fields: Array<{ doc?: string; name: string; nullable?: boolean; type: string; tz?: string; unit?: string }>; name?: string }
  checksum_algorithm: "sha256" | "sha512" | "blake3" | "md5"
  dataset_id: string
  files: Array<{ checksum: string; path: string; size_bytes: number }>
  published_at: string
  row_count: number
  state: "publishing" | "published" | "tombstoned" | "deleted"
  subject: { kind: string; symbol: string; timeframe?: string }
  supersedes: null | string
  time_range: { end: string; start: string }
  tombstone: null | { deletable_after: string; tombstoned_at: string }
  version: number
}

export type FeatureDtype = "float64" | "int64" | "int8"

export interface LabelDefinition {
  name: "net_profitable_v1"
  positive_class: 1
}

export type MlEntryFilterManifest = MlFilterDatasetManifest | MlFilterModelManifest

export interface MlFilterDatasetManifest {
  bars_checksum: ChecksumHex
  compatibility_fingerprint: ChecksumHex
  dataset_content_id: ChecksumHex
  dataset_id: string
  engine_revision: string
  format_version: 1
  kind: "ml_filter_dataset"
  label: LabelDefinition
  partition_counts: PartitionCounts
  selected_features: Array<OrderedFeature>
  source_config_revision: string
  source_run_id: string
  trades_checksum: ChecksumHex
  train_end: string
  validation_end: string
}

export interface MlFilterModelManifest {
  algorithm: "lightgbm" | "random_forest" | "logistic_regression"
  dataset_id: string
  dependency_versions: Record<string, unknown>
  fitted_artifact_checksum: ChecksumHex
  format_version: 1
  hyperparameters: Record<string, unknown>
  kind: "ml_filter_model"
  model_content_id: ChecksumHex
  model_version_id: string
  preprocessing_recipe: Array<PreprocessingStep>
  seed: number
  selected_features: Array<OrderedFeature>
  training_label_availability_cutoff: string
}

export interface OrderedFeature {
  dtype: FeatureDtype
  name: "open" | "high" | "low" | "close" | "tick_volume" | "real_volume" | "ma_short" | "ma_long" | "delta" | "prev_delta" | "side"
}

export interface PartitionCounts {
  lockbox: SamplePartitionCounts
  train: SamplePartitionCounts
  validation: SamplePartitionCounts
}

export interface PreprocessingStep {
  parameters: Record<string, unknown>
  step: string
}

export interface SamplePartitionCounts {
  rejections: Record<string, unknown>
  samples: number
}
