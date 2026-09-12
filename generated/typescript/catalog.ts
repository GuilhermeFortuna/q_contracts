// GENERATED FILE - DO NOT EDIT. Source schemas: schema/catalog/dataset-manifest.schema.json

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
