// GENERATED FILE - DO NOT EDIT. Source schemas: schema/api/arrow/bars.schema.json, schema/api/arrow/ticks.schema.json, schema/api/error.schema.json, schema/api/openapi.yaml

export interface AiModelOption {
  available?: boolean
  id: string
  label: string
  provider: string
}

export interface AiProviderOption {
  id: string
  label: string
}

export interface AiStrategyMetadata {
  assumptions?: Array<string>
  capabilities_version: string
  compiled_strategy?: Record<string, unknown> | null
  compiled_strategy_id?: string | null
  original_prompt: string
  strategy_spec: Record<string, unknown>
  strategy_spec_version: string
  unsupported_requests_acknowledged?: Array<string>
}

export interface AiStrategyModelsResponse {
  default_model: string
  models?: Array<AiModelOption>
  provider: string
  providers?: Array<AiProviderOption>
}

export interface AiStrategyResponse {
  assumptions?: Array<string>
  change_notes?: Array<string>
  compiled_strategy?: CompiledStrategy | null
  confidence: number
  questions?: Array<string>
  strategy_spec?: Record<string, unknown> | null
  summary: string
  unsupported_requests?: Array<string>
  validation?: ValidationResult | null
}

export interface AiStrategyServiceErrorResponse {
  detail?: string | null
  message: string
  status: "ai_disabled" | "ai_misconfigured" | "provider_error" | "parse_error"
}

export interface AlphaResearchComputeBudget {
  optimization_seeds?: number | null
  study_n_trials?: number | null
  walkforward?: WalkForwardConfig | null
}

export interface AlphaResearchRequest {
  catalog_version?: number | null
  compute_budget?: AlphaResearchComputeBudget | null
  end: string
  profile_id: string
  profile_version?: number | null
  start: string
  target_name?: string
}

export interface AlphaResearchResult {
  acceptance?: Record<string, unknown> | null
  champion?: Record<string, unknown> | null
  coverage?: Record<string, unknown>
  feature_evidence_summary?: Array<Record<string, unknown>>
  hypothesis_manifest?: Array<Record<string, unknown>>
  inconclusive_reasons?: Array<string>
  profile_id: string
  provenance?: Record<string, unknown>
  split_manifest?: Record<string, unknown> | null
  stages?: Array<AlphaResearchStageStatus>
  verdict: "ready_for_paper" | "inconclusive" | "rejected"
}

export interface AlphaResearchStageStatus {
  detail?: string | null
  name: string
  status: "pending" | "running" | "completed" | "failed" | "skipped"
}

export interface AlphaResearchStartResponse {
  job_id: string
  status: string
}

export interface AlphaResearchStatusResponse {
  checkpoint?: Record<string, unknown> | null
  detail?: string | null
  error?: string | null
  job_id: string
  progress?: number
  result?: AlphaResearchResult | null
  stages?: Array<AlphaResearchStageStatus>
  status: "queued" | "running" | "completed" | "failed" | "cancelled"
}

export interface ApiError {
  code?: string
  details?: unknown
  message: string
}

export interface AuditEventListResponse {
  items: Array<AuditEventResponse>
  limit: number
  offset: number
  total: number
}

export interface AuditEventResponse {
  actor?: string | null
  created_at: string
  deployment_id?: string | null
  event_type: string
  id: string
  message: string
  payload: Record<string, unknown>
}

export interface BacktestConfig {
  costs?: TransactionCostConfig | null
  day_trade?: boolean
  day_trade_close_time?: string
  day_trade_end_time?: string
  day_trade_start_time?: string
  display_timeframe?: string
  end: string
  engine?: "candle" | "tick"
  entries?: Array<EntryInstance> | null
  entry_manager?: EntryManagerConfig
  exit_params?: Record<string, unknown>
  initial_capital?: number
  parallel_mode?: ParallelMode
  point_value?: number
  start: string
  strategy?: string
  symbol: string
  tick_flags?: string | null
  timeframe?: string
}

export interface BacktestConfigPayload {
  execution_assumptions?: Record<string, unknown>
  position_sizing?: Record<string, unknown>
  strategy: string
  strategy_params?: Record<string, unknown>
  symbol: string
  timeframe: string
}

export interface BacktestEquityArtifactResponse {
  points: Array<EquityArtifactPoint>
  run_id: string
}

export interface BacktestRequest {
  costs?: TransactionCostConfig | null
  day_trade?: boolean
  day_trade_close_time?: string
  day_trade_end_time?: string
  day_trade_start_time?: string
  display_timeframe?: string
  end?: string | null
  engine?: "candle" | "tick"
  entries?: Array<EntryInstance> | null
  entry_manager?: EntryManagerConfig
  exit_params?: Record<string, unknown>
  initial_capital?: number
  point_value?: number
  position_sizing?: FixedQuantityPositionSizing | FixedSafetyMarginPositionSizing | InverseVolatilityPositionSizing | null
  start?: string | null
  strategy?: string
  strategy_params?: Record<string, unknown>
  symbol: string
  tick_flags?: string | null
  timeframe?: string
}

export interface BacktestResponse {
  bars: Array<OhlcvBarResponse>
  indicators: Array<ChartIndicatorSeries>
  metrics: Record<string, unknown>
  run_id?: string | null
  trades: Array<Record<string, unknown>>
}

export interface BacktestRunDetailResponse {
  config: Record<string, unknown>
  created_at: string
  error_message?: string | null
  finished_at?: string | null
  is_saved?: boolean
  result_summary?: Record<string, unknown> | null
  run_id: string
  started_at?: string | null
  status: string
  strategy: string
  symbol: string
  timeframe: string
}

export interface BacktestRunListItem {
  created_at: string
  is_saved?: boolean
  run_id: string
  status: string
  strategy: string
  summary?: Record<string, unknown> | null
  symbol: string
  timeframe: string
}

export interface BacktestRunListResponse {
  items: Array<BacktestRunListItem>
  limit: number
  offset: number
  total: number
}

export interface BacktestRunPatchRequest {
  is_saved: boolean
}

export interface BacktestStartResponse {
  run_id: string
  status: string
}

export interface BacktestStatusResponse {
  error?: string | null
  run_id: string
  status: string
}

export interface BacktestTradesArtifactResponse {
  run_id: string
  trades: Array<Record<string, unknown>>
}

export interface BulkDeleteBacktestsRequest {
  run_ids: Array<string>
}

export interface BulkDeleteOptimizationsRequest {
  study_ids: Array<string>
}

export interface BulkDeleteResponse {
  deleted: number
  not_found: Array<string>
}

export interface CapabilityRegistry {
  condition_groups: Array<string>
  data: DataCapabilities
  execution_assumptions: ExecutionAssumptions
  exit_presets: Array<ExitPreset>
  exit_rules: Array<ExitRuleInfo>
  genome_limits: GenomeLimits
  genome_nodes: Array<GenomeNodeCapability>
  genome_param_bounds: Array<StrategyParamSpec>
  operators: Array<string>
  risk_sizing: Array<RiskSizingCapability>
  schema_version?: "q_capabilities.v1"
  strategies: Array<StrategyInfo>
  unsupported: Array<string>
}

export interface CategoricalParam {
  choices: Array<string | number | number>
  type?: "categorical"
}

export interface ChartIndicatorSeries {
  color?: string | null
  key: string
  label: string
  pane: "price" | "oscillator"
  values: Array<number | null>
}

export interface CompileStrategySpecErrorResponse {
  errors?: Array<ValidationErrorDetail>
  status?: "validation_failed" | "compile_failed"
}

export interface CompileStrategySpecRequest {
  strategy_spec: Record<string, unknown>
}

export interface CompileStrategySpecResponse {
  compiled_strategy: CompiledStrategy
  compiled_strategy_id: string
  status?: "compiled"
}

export interface CompiledStrategy {
  backtest_config: BacktestConfigPayload
  compiled_id: string
  genome?: Record<string, unknown> | null
  schema_version: string
  strategy_name: string
  strategy_params?: Record<string, unknown>
  summary: CompiledStrategySummary
}

export interface CompiledStrategySummary {
  entry_summary: string
  exit_summary: string
  indicators?: Array<string>
  mapping: string
  market: string
  name: string
  strategy_label: string
  timeframe: string
  universe?: Array<string>
}

export interface ConversationMessage {
  content: string
  role: "user" | "assistant" | "system"
}

export interface CustomStrategySaveRequest {
  ai_metadata?: AiStrategyMetadata | null
  base_strategy: string
  description?: string | null
  name: string
  parameters: Record<string, unknown>
}

export interface DataCapabilities {
  data_sources: Array<string>
  engines: Array<"candle" | "tick">
  markets: Array<string>
  ohlcv_columns: Array<string>
  tick_columns: Array<string>
  timeframes: Array<string>
}

export interface DataSourceResponse {
  active_provider: "mt5" | "remote" | "local"
  mt5_available: boolean
  source: "auto" | "mt5" | "remote" | "local"
}

export interface DataSourceUpdateRequest {
  source: "auto" | "mt5" | "remote" | "local"
}

export interface DatasetListResponse {
  datasets: Array<DatasetManifestResponse>
  root: string
}

export interface DatasetManifestResponse {
  arrow_schema: Record<string, unknown>
  checksum_algorithm: "sha256" | "sha512" | "blake3" | "md5"
  dataset_id: string
  files: Array<ManifestFile>
  published_at: string
  row_count: number
  state: "publishing" | "published" | "tombstoned" | "deleted"
  subject: Record<string, unknown>
  supersedes?: string | null
  time_range: Record<string, unknown>
  tombstone?: Record<string, unknown> | null
  version: number
}

export interface DecisionListResponse {
  items: Array<DecisionResponse>
  limit: number
  offset: number
  total: number
}

export interface DecisionResponse {
  bar_close_time: string
  config_hash: string
  created_at: string
  deployment_id: string
  id: string
  outcome: string
  reason?: string | null
  requested_quantity?: string | null
  signal_action: string
  strategy_name: string
  strategy_version: number
  symbol: string
  timeframe: string
}

export interface DeploymentActionRequest {
  action: "start" | "pause" | "stop" | "flatten"
  actor?: string | null
  confirm?: boolean
}

export interface DeploymentActionResponse {
  accepted: boolean
  deployment_id: string
  lifecycle: string
  message: string
  pending_action?: string | null
}

export interface DeploymentChartBar {
  close: number
  high: number
  low: number
  open: number
  volume: number
}

export interface DeploymentChartIndicator {
  color?: string | null
  key: string
  label: string
  pane: "price" | "oscillator"
  values: Array<number | null>
}

export interface DeploymentChartResponse {
  bars: Array<DeploymentChartBar>
  indicators: Array<DeploymentChartIndicator>
  last_bar_close_time?: string | null
  next_bar_close_time?: string | null
  symbol: string
  timeframe: string
  window_bound_bars: number
}

export interface DeploymentCreateRequest {
  broker_mode?: "paper" | "mt5_live"
  identity?: DeploymentIdentityInput | null
  live_activation_enabled?: boolean
  name: string
  paper_account_id: string
  source_backtest_run_id?: string | null
}

export interface DeploymentDetailResponse {
  broker_mode: string
  compiled_config: Record<string, unknown>
  config_hash: string
  created_at: string
  id: string
  last_bar_close_time?: string | null
  latest_decision?: DecisionResponse | null
  lifecycle: string
  live_activation_enabled: boolean
  name: string
  open_position?: PositionResponse | null
  paper_account_id: string
  pending_action?: string | null
  pending_action_requested_at?: string | null
  risk_config: Record<string, unknown>
  sizing_config: Record<string, unknown>
  started_at?: string | null
  stopped_at?: string | null
  strategy_name: string
  strategy_version: number
  symbol: string
  timeframe: string
  unknown_order_count?: number
  updated_at: string
  worker_lease?: WorkerLeaseResponse | null
}

export interface DeploymentHealthResponse {
  deployment_id: string
  last_bar_close_time?: string | null
  latest_decision?: DecisionResponse | null
  lifecycle: string
  pending_action?: string | null
  unknown_order_count?: number
  worker_lease?: WorkerLeaseResponse | null
}

export interface DeploymentIdentityInput {
  compiled_config: Record<string, unknown>
  config_hash: string
  risk_config?: Record<string, unknown>
  sizing_config: Record<string, unknown>
  strategy_name: string
  strategy_version: number
  symbol: string
  timeframe: string
}

export interface DeploymentListResponse {
  items: Array<DeploymentSummaryResponse>
  limit: number
  offset: number
  total: number
}

export interface DeploymentSummaryResponse {
  broker_mode: string
  config_hash: string
  created_at: string
  id: string
  last_bar_close_time?: string | null
  lifecycle: string
  live_activation_enabled: boolean
  name: string
  paper_account_id: string
  pending_action?: string | null
  pending_action_requested_at?: string | null
  started_at?: string | null
  stopped_at?: string | null
  strategy_name: string
  strategy_version: number
  symbol: string
  timeframe: string
  updated_at: string
}

export interface DiscoveryAbArmSummary {
  mean?: number | null
  values: Array<number>
}

export interface DiscoveryAbPairedDelta {
  cohens_d?: number | null
  mean?: number | null
  p_value?: number | null
  values: Array<number>
}

export interface DiscoveryAbRequest {
  config: StrategySearchConfig
  minimum_complete_pairs?: number
  seeds: Array<number>
}

export interface DiscoveryAbResult {
  child_runs?: Array<Record<string, unknown>>
  complete_pairs: number
  control: DiscoveryAbArmSummary
  dropped_pair_reasons?: Array<string>
  metric: "lockbox_objective" | "oos_objective"
  minimum_complete_pairs?: number
  n_seeds: number
  paired_delta: DiscoveryAbPairedDelta
  requested_seeds: number
  treatment: DiscoveryAbArmSummary
  verdict: "helps" | "no_effect" | "hurts" | "inconclusive"
}

export interface DiscoveryAbStartResponse {
  job_id: string
  status: string
}

export interface DiscoveryAbStatusResponse {
  detail?: string | null
  error?: string | null
  job_id: string
  progress?: number
  result?: DiscoveryAbResult | null
  status: "queued" | "running" | "completed" | "failed"
}

export interface EncoderAblationRequest {
  configs: Array<EncoderConfigSpec>
  horizon?: number
  input_features?: Array<string>
  n_latents?: number
  symbol: string
  target?: string
  timeframe: string
  train_end: string
  train_start: string
}

export interface EncoderAblationResult {
  best_label?: string | null
  horizon: number
  rows: Array<EncoderAblationRow>
  symbol: string
  target: string
  timeframe: string
}

export interface EncoderAblationRow {
  baseline_ic?: number | null
  best_latent_ic?: number | null
  encoder_kind: "pca" | "ae"
  gate_error?: string | null
  ic_delta_vs_baseline?: number | null
  label: string
  model_hash?: string | null
  passed?: boolean | null
  recon_r2?: number | null
}

export interface EncoderAblationStartResponse {
  job_id: string
  status: string
}

export interface EncoderAblationStatusResponse {
  error?: string | null
  job_id: string
  progress?: string | null
  result?: EncoderAblationResult | null
  status: string
}

export interface EncoderConfigSpec {
  encoder_kind: "pca" | "ae"
  hyperparams?: Record<string, unknown>
  label: string
}

export interface EntryInstance {
  params?: Record<string, unknown>
  strategy: string
}

export interface EntryManagerConfig {
  kind?: string
  params?: Record<string, unknown>
}

export interface EpochMismatchResponse {
  current_epoch: string
  requested_epoch: string
  topic: string
}

export interface EquityArtifactPoint {
  equity: number
  time: string
}

export interface ErrorResponse {
  code?: string | null
  details?: unknown | null
  message: string
}

export interface ExecutionAssumptions {
  ai_builder_mvp_long_only?: boolean
  allow_short: boolean
  supported_entry_timing: Array<string>
  supported_signal_timing: Array<string>
}

export interface ExecutionHealthResponse {
  api_status: "ok" | "degraded" | "unavailable"
  checked_at: string
  deployments: Array<DeploymentHealthResponse>
  kill_switch_enabled: boolean
  live_capability_locked: boolean
  market_data_status: "online" | "offline" | "stale"
  unknown_order_count: number
  worker_status: "healthy" | "stale" | "offline"
}

export interface ExitPreset {
  description: string
  id: string
  label: string
  parameters: Record<string, unknown>
}

export interface ExitPresetSearchConfig {
  enabled?: boolean
  include_baseline?: boolean
  pin_non_preset_exits_off?: boolean
  preset_ids?: Array<string> | null
}

export interface ExitQualityScoringConfig {
  enabled?: boolean
  max_profit_giveback_pct?: number | null
  min_mfe_capture_ratio?: number | null
}

export interface ExitRuleCatalogResponse {
  exit_presets: Array<ExitPreset>
  exit_rules: Array<ExitRuleInfo>
  shared_exit_params: Array<string>
}

export interface ExitRuleInfo {
  description: string
  enable_param: string
  enable_value: number | number
  exit_group: "stop_loss" | "trailing" | "target" | "time" | "general"
  id: string
  label: string
  param_names: Array<string>
  required_param_names: Array<string>
}

export interface ExogenousSeriesConfig {
  availability_lag_bars?: number
  corr_window?: number
  lookback_bars?: number
  recipes?: Array<"close" | "return" | "return_zscore" | "rolling_corr" | "relative_strength" | "vol_regime" | "direction_regime">
  resampling_rule?: "none" | "last_completed"
  source_timeframe: string
  symbol: string
  target_timeframe?: string | null
  vol_percentile_window?: number
  vol_regime_threshold?: number
  vol_window?: number
}

export interface FeatureEvalClusterItem {
  cluster_id: number
  feature_ids: Array<string>
  representative: string
}

export interface FeatureEvalCreateRequest {
  end: string
  features: Array<FeatureEvalFeatureRequest>
  start: string
  symbol: string
  target: FeatureEvalTargetRequest
  timeframe: string
}

export interface FeatureEvalFeatureRequest {
  name: string
  params?: Record<string, unknown>
  version?: number | null
}

export interface FeatureEvalHeatmap {
  metrics: Array<string>
  rows: Array<FeatureEvalHeatmapRow>
}

export interface FeatureEvalHeatmapRow {
  feature_id: string
  feature_name: string
  ic?: number | null
  mutual_info?: number | null
  rank_ic?: number | null
  stability?: number | null
}

export interface FeatureEvalLeaderboardItem {
  cluster_id: number
  feature_id: string
  feature_name: string
  global_score?: number | null
  ic?: number | null
  is_representative: boolean
  leakage_status: string
  mutual_info?: number | null
  rank_ic?: number | null
  regime_ics: Record<string, unknown>
  stability?: number | null
}

export interface FeatureEvalRunResponse {
  clusters: Array<FeatureEvalClusterItem>
  end: string
  error_message?: string | null
  feature_count: number
  finished_at?: string | null
  heatmap: FeatureEvalHeatmap
  leaderboard: Array<FeatureEvalLeaderboardItem>
  matrix_id: string
  result_summary?: Record<string, unknown> | null
  run_id: string
  start: string
  started_at?: string | null
  status: string
  symbol: string
  target_horizon: number
  target_name: string
  timeframe: string
}

export interface FeatureEvalStartResponse {
  run_id: string
  status: string
}

export interface FeatureEvalTargetRequest {
  horizon: number
  name: string
}

export interface FeatureLeaderboardItem {
  feature_name: string
  global_score: number
}

export interface FeatureLeaderboardResponse {
  features: Array<FeatureLeaderboardItem>
}

export interface FeatureListItem {
  category: string
  latest_version: number
  name: string
  score?: number | null
  status: string
  usage_count: number
}

export interface FeatureListResponse {
  features: Array<FeatureListItem>
}

export interface FeaturePassportResponse {
  category: string
  description?: string | null
  evaluation_history: Array<unknown>
  name: string
  score?: number | null
  usage_count: number
  versions: Array<FeatureVersionDetail>
}

export type FeatureStatus = "experimental" | "candidate" | "production"

export interface FeatureStatusUpdateRequest {
  status: FeatureStatus
}

export interface FeatureVersionDetail {
  default_params: Record<string, unknown>
  forward_window: number
  leakage_status: string
  node_kind: string
  param_keys: Array<string>
  provenance: Record<string, unknown>
  status: string
  version: number
}

export interface FillListResponse {
  items: Array<FillResponse>
  limit: number
  offset: number
  total: number
}

export interface FillResponse {
  broker_mode: string
  created_at: string
  deployment_id: string
  external_fill_id: string
  fee: string
  filled_at: string
  id: string
  order_id: string
  price: string
  quantity: string
  side: string
  slippage: string
}

export interface FixedQuantityPositionSizing {
  quantity?: number
  scale_by_signal_strength?: boolean
  type?: "fixed_quantity"
}

export interface FixedSafetyMarginPositionSizing {
  max_contracts?: number | null
  min_contracts?: number
  safety_margin_per_contract?: number
  scale_by_signal_strength?: boolean
  type?: "fixed_safety_margin"
}

export interface FloatParam {
  high: number
  low: number
  step?: number | null
  type?: "float"
}

export interface GateConfig {
  efficiency_high?: number
  efficiency_low?: number
  min_completed_windows?: number
  min_oos_trades?: number
}

export interface GeneticSearchConfig {
  adaptive_operator_weights?: boolean
  complexity_lambda?: number
  complexity_mu?: number
  crossover_rate?: number
  elite_count?: number
  error_floor?: number
  exit_policy_preset_ids?: Array<string> | null
  exit_policy_seed_fraction?: number
  gate_penalty_efficiency?: number
  gate_penalty_trades?: number
  gate_penalty_windows?: number
  generations?: number
  init_seed?: number | null
  max_depth?: number
  max_nodes?: number
  max_workers?: number | null
  min_seed_signals?: number
  mutation_rate?: number
  mutation_rate_max?: number
  mutation_rate_min?: number
  no_result_floor?: number
  population_size?: number
  prescreen_min_signals?: number
  repair_max_attempts?: number
  seed_exit_policies?: boolean
  stagnation_patience?: number
  tournament_size?: number
}

export interface GenomeLimits {
  max_depth: number
  max_node_count: number
}

export interface GenomeNodeCapability {
  allowed_param_keys: Array<string>
  input_series_types: Array<"price_series" | "oscillator"> | null
  kind: string
  max_inputs: number
  min_inputs: number
  output_ports: Array<string>
  port_types: Record<string, unknown>
}

export interface HTTPValidationError {
  detail?: Array<ValidationError>
}

export interface HistoryExpiredResponse {
  oldest_available_seq?: number | null
  requested_from_seq: number
  topic: string
}

export interface HistoryPageResponse {
  entries: Array<Record<string, unknown>>
  epoch: string
  next_seq: number | null
  topic: string
}

export interface IngestJobRequest {
  end: string
  kind?: "bars" | "ticks"
  start: string
  symbol: string
  timeframes?: Array<string>
}

export interface InstrumentInfoResponse {
  contractSize: number
  currencyBase: string
  currencyProfit: string
  description: string
  digits: number
  exchange: string
  point: number
  spreadFloating: boolean
  symbol: string
  tickSize: number
  tickValue: number
  volumeMax: number
  volumeMin: number
  volumeStep: number
}

export interface InstrumentResponse {
  assetClass: string
  exchange: string
  name: string
  symbol: string
}

export interface IntParam {
  high: number
  low: number
  step?: number
  type?: "int"
}

export interface InverseVolatilityPositionSizing {
  max_contracts?: number | null
  min_contracts?: number
  scale_by_signal_strength?: boolean
  target_volatility_pct?: number
  type?: "inverse_volatility"
}

export interface JobSnapshotItem {
  job_id: string
  kind: string
  message?: string | null
  progress?: number | null
  progress_epoch?: string | null
  progress_seq?: number | null
  status: "queued" | "running" | "completed" | "failed" | "cancelled"
}

export interface JobSnapshotResponse {
  jobs: Array<JobSnapshotItem>
  watermark: Record<string, unknown>
}

export interface KillSwitchResponse {
  enabled: boolean
  reason?: string | null
  updated_at?: string | null
  updated_by?: string | null
}

export interface KillSwitchUpdateRequest {
  confirm?: boolean
  enabled: boolean
  reason?: string | null
  updated_by?: string | null
}

export interface KillSwitchUpdateResponse {
  accepted: boolean
  audit_event_id: string
  kill_switch: KillSwitchResponse
}

export interface LatentGateResultResponse {
  baseline_ic: number
  best_latent_ic: number
  evaluation_run_id: string
  n_latents_beating_baseline: number
  passed: boolean
  target_horizon?: number | null
  target_name?: string | null
}

export interface LatestResponse {
  entries: Record<string, unknown>
  topic: string
}

export interface LedgerEntryListResponse {
  items: Array<LedgerEntryResponse>
  limit: number
  offset: number
  total: number
}

export interface LedgerEntryResponse {
  amount: string
  balance_after: string
  created_at: string
  deployment_id: string
  description?: string | null
  entry_type: string
  fill_id?: string | null
  id: string
  paper_account_id: string
}

export interface LockboxConfig {
  enabled?: boolean
  lockbox_days?: number | null
  lockbox_pct?: number | null
  max_drawdown_pct?: number | null
  min_trades?: number
}

export interface LogFloatParam {
  high: number
  low: number
  type?: "log-float"
}

export interface ManifestFile {
  checksum: string
  path: string
  size_bytes: number
}

export interface MarketSnapshotResponse {
  ask?: number
  bid?: number
  changeAbs?: number
  changePct: number
  dayHigh?: number
  dayLow?: number
  dayOpen?: number
  digits?: number
  last: number
  prevClose?: number
  spread?: number
  symbol: string
  tickTime?: string | null
  volume: number
}

export interface MarketSnapshotsResponse {
  snapshots: Array<MarketSnapshotResponse>
}

export interface MarketTapeTickResponse {
  ask: number
  bid: number
  last: number
  side?: "buy" | "sell" | null
  volume: number
}

export interface MarketTicksResponse {
  ticks: Array<MarketTapeTickResponse>
}

export interface NeuralModelDetailResponse {
  created_at: string
  gate_result?: LatentGateResultResponse | null
  latent_names: Array<string>
  model_hash: string
  model_key: string
  n_latents: number
  status: string
  symbol: string
  timeframe: string
  train_end: string
  train_start: string
  val_metrics: Record<string, unknown>
  version: number
}

export interface NeuralModelListItem {
  created_at: string
  model_hash: string
  model_key: string
  n_latents: number
  status: string
  symbol: string
  timeframe: string
  val_metrics: Record<string, unknown>
  version: number
}

export interface NeuralModelListResponse {
  models: Array<NeuralModelListItem>
}

export type NeuralModelStatus = "trained" | "candidate" | "production" | "archived"

export interface NeuralModelStatusUpdateRequest {
  status: NeuralModelStatus
}

export interface NeuralTrainEvaluateRequest {
  horizon: number
  target: string
}

export interface NeuralTrainRequest {
  evaluate?: NeuralTrainEvaluateRequest | null
  hyperparams?: Record<string, unknown>
  input_features: Array<string>
  kind?: "pca" | "autoencoder"
  model_key?: string | null
  n_latents: number
  symbol: string
  timeframe: string
  train_end: string
  train_start: string
}

export interface NeuralTrainStartResponse {
  job_id: string
  status: string
}

export interface NeuralTrainStatusResponse {
  error?: string | null
  gate?: Record<string, unknown> | null
  gate_error?: string | null
  job_id: string
  model_hash?: string | null
  progress?: string | null
  status: string
  val_metrics?: Record<string, unknown> | null
}

export interface NewsArticleResponse {
  content: string
  id: string
  imageUrl?: string | null
  publishedAt: string
  source: string
  summary: string
  title: string
  videoUrl?: string | null
}

export interface OHLCV {
  close: number
  high: number
  low: number
  open: number
  real_volume?: number | null
  spread?: number | null
  tick_volume: number
  time: string
}

export interface ObjectiveConfig {
  mode: ObjectiveMode
}

export type ObjectiveMode = "maximize_net_profit" | "maximize_sharpe" | "minimize_drawdown" | "maximize_return_drawdown" | "multi_objective_return_drawdown"

export interface OhlcvAvailableRangeResponse {
  bar_count: number
  end: string
  start: string
  symbol: string
  timeframe: string
}

export interface OhlcvBarResponse {
  close: number
  high: number
  low: number
  open: number
  volume: number
}

export interface OptimizationAnalyticsResponse {
  is_multi_objective: boolean
  n_complete_trials: number
  objective_labels: Array<string>
  parallel_coordinate: ParallelCoordinatePayload
  param_importances?: Record<string, unknown> | null
  pareto_front: ParetoFrontPayload
  status: string
  study_id: string
}

export interface OptimizationConfig {
  backtest: BacktestConfig
  fixed_params?: Record<string, unknown>
  objective: ObjectiveConfig
  search_space: SearchSpaceConfig
  study: StudyConfig
}

export interface OptimizationResultsResponse {
  best_params: Record<string, unknown>
  best_trial?: Record<string, unknown> | null
  failures: Array<Record<string, unknown>>
  is_multi_objective: boolean
  objective_mode: string
  pareto_trials: Array<Record<string, unknown>>
  study_id: string
  trials: Array<Record<string, unknown>>
}

export interface OptimizationStartResponse {
  status: string
  study_id: string
}

export interface OptimizationStatusResponse {
  backtest_config?: Record<string, unknown> | null
  best_params?: Record<string, unknown>
  best_trial?: Record<string, unknown> | null
  best_value?: number | null
  completed_trials: number
  error?: string | null
  n_trials: number
  optimization_config?: Record<string, unknown> | null
  status: string
  study_id: string
  trials?: Array<Record<string, unknown>> | null
  workers?: number
}

export interface OptimizationStudyListItem {
  best_value?: number | null
  completed_trials: number
  created_at: string
  n_trials: number
  name: string
  status: string
  study_id: string
}

export interface OptimizationStudyListResponse {
  items: Array<OptimizationStudyListItem>
  limit: number
  offset: number
  total: number
}

export interface OrderListResponse {
  items: Array<OrderResponse>
  limit: number
  offset: number
  total: number
}

export interface OrderResolutionRequest {
  actor: string
  external_fill_id?: string | null
  fee?: number | string | null
  filled_at?: string | null
  outcome: "filled" | "not_filled"
  price?: number | string | null
  quantity?: number | string | null
  reason: string
}

export interface OrderResolutionResponse {
  accepted: boolean
  message: string
  order: OrderResponse
  resolution: string
}

export interface OrderResponse {
  broker_mode: string
  completed_at?: string | null
  created_at: string
  decision_id?: string | null
  deployment_id: string
  id: string
  intent_committed_at?: string | null
  order_type: string
  quantity: string
  reconciled_at?: string | null
  reconciled_by?: string | null
  reconciliation_attempted_at?: string | null
  reconciliation_detail?: string | null
  reconciliation_error?: string | null
  reconciliation_state: string
  rejection_reason?: string | null
  side: string
  status: string
  submitted_at?: string | null
}

export interface PaperAccountCreateRequest {
  currency?: string
  initial_balance: number | string
  name: string
  risk_config?: Record<string, unknown>
  sizing_config?: Record<string, unknown>
}

export interface PaperAccountListResponse {
  items: Array<PaperAccountResponse>
  limit: number
  offset: number
  total: number
}

export interface PaperAccountResponse {
  cash_balance: string
  created_at: string
  currency: string
  id: string
  initial_balance: string
  name: string
  risk_config: Record<string, unknown>
  sizing_config: Record<string, unknown>
  updated_at: string
}

export interface ParallelCoordinatePayload {
  objectives: Array<string>
  params: Array<string>
  rows: Array<ParallelCoordinateRow>
  rows_capped?: boolean | null
}

export interface ParallelCoordinateRow {
  number: number
  params: Record<string, unknown>
  values: Array<number>
}

export type ParallelMode = "SEQUENTIAL" | "DAY_TRADE"

export interface ParamImportanceEntry {
  importance: number
  param: string
}

export interface ParetoFrontPayload {
  is_multi_objective: boolean
  objectives: Array<string>
  points: Array<ParetoPoint>
}

export interface ParetoPoint {
  number: number
  params: Record<string, unknown>
  values: Array<number>
}

export interface PendingReconciliationListResponse {
  items: Array<OrderResponse>
  limit: number
  offset: number
  total: number
}

export interface PositionListResponse {
  items: Array<PositionResponse>
  limit: number
  offset: number
  total: number
}

export interface PositionResponse {
  average_entry_price?: string | null
  closed_at?: string | null
  deployment_id: string
  id: string
  is_open: boolean
  opened_at?: string | null
  quantity: string
  side: string
  updated_at: string
}

export interface RiskEventListResponse {
  items: Array<RiskEventResponse>
  limit: number
  offset: number
  total: number
}

export interface RiskEventResponse {
  context: Record<string, unknown>
  created_at: string
  decision_id?: string | null
  deployment_id: string
  id: string
  message: string
  order_id?: string | null
  rejection_code: string
}

export interface RiskSizingCapability {
  description: string
  label: string
  type: string
}

export interface SearchSpaceConfig {
  manager_params?: Record<string, unknown>
  risk_params?: Record<string, unknown>
  strategy_params?: Record<string, unknown>
}

export interface SignalManagerCatalogResponse {
  managers: Array<SignalManagerInfo>
}

export interface SignalManagerInfo {
  description: string
  id: string
  label: string
  param_names: Array<string>
  params?: Array<StrategyParamSpec>
}

export interface StorageConfig {
  path?: string | null
  type?: "memory" | "sqlite" | "url" | "shared"
  url?: string | null
}

export interface StorageDeleteResponse {
  deleted: boolean
  symbol: string
  timeframe: string
}

export interface StorageIngestStartResponse {
  job_id: string
  status: "queued"
}

export interface StorageIngestStatusResponse {
  detail: string
  error?: string | null
  job_id: string
  progress: number
  results?: Array<Record<string, unknown>> | null
  status: "queued" | "running" | "completed" | "failed"
}

export interface StorageInventoryItem {
  bytes: number
  end: string
  kind?: "bars" | "ticks"
  rows: number
  start: string
  symbol: string
  timeframe?: string | null
  updated_at: string
}

export interface StorageInventoryResponse {
  items: Array<StorageInventoryItem>
  root: string
}

export interface StorageServiceStatus {
  error?: string | null
  status: "ok" | "error"
}

export interface StorageStatusResponse {
  postgres: StorageServiceStatus
  redis: StorageServiceStatus
}

export interface StrategiesResponse {
  strategies: Array<StrategyInfo>
}

export interface StrategyInfo {
  category?: "trend" | "mean_reversion" | "breakout" | "momentum" | "other"
  description: string
  engine?: "candle" | "tick"
  label: string
  name: string
  params: Array<StrategyParamSpec>
  strong_in?: string
  thesis?: string
  weak_in?: string
}

export interface StrategyInterpretRequest {
  capabilities_version?: string
  conversation?: Array<ConversationMessage>
  current_spec?: Record<string, unknown> | null
  message: string
  model?: string | null
  provider?: string | null
  validation_errors?: Array<ValidationErrorDetail>
}

export interface StrategyParamSpec {
  choices?: Array<string> | null
  default: number | number | string
  exit_group?: "stop_loss" | "trailing" | "target" | "time" | "general" | null
  hint?: string | null
  label: string
  max?: number | null
  min?: number | null
  name: string
  search_max?: number | null
  search_min?: number | null
  search_scale?: "linear" | "log" | null
  search_step?: number | null
  searchable?: boolean
  step?: number | null
  type: "int" | "float" | "categorical"
}

export interface StrategySearchCandidateEquityArtifactResponse {
  candidate_id: string
  points: Array<EquityArtifactPoint>
  run_id: string
}

export interface StrategySearchCandidateGenomeResponse {
  candidate_id: string
  genome: Record<string, unknown>
  run_id: string
}

export interface StrategySearchCandidateResponse {
  best_params?: Record<string, unknown> | null
  candidate_id: string
  completed_windows?: number
  complexity_penalty?: number | null
  diagnostics?: Record<string, unknown> | null
  dsr?: number | null
  efficiency?: number | null
  error?: string | null
  exit_param_names?: Array<string> | null
  exit_policy_id?: string | null
  exit_policy_label?: string | null
  exit_preset_id?: string | null
  exit_preset_label?: string | null
  exit_quality?: Record<string, unknown> | null
  gate_flags?: Array<string>
  generation?: number | null
  genome?: Record<string, unknown> | null
  genome_node_count?: number | null
  hypothesis_id?: string | null
  hypothesis_rationale?: string | null
  hypothesis_required_features?: Array<string> | null
  hypothesis_template_hash?: string | null
  is_metrics_summary?: Record<string, unknown> | null
  last_exit_mutation_op?: string | null
  objective_value?: number | null
  oos_metrics?: Record<string, unknown> | null
  passed_gates?: boolean
  profile_version?: number | null
  rank?: number | null
  robustness_score?: number | null
  status: string
  strategy: string
  window_count?: number
}

export interface StrategySearchConfig {
  backtest: BacktestConfig
  exit_presets?: ExitPresetSearchConfig
  exit_quality_scoring?: ExitQualityScoringConfig
  exogenous_provenance?: Array<Record<string, unknown>> | null
  exogenous_series?: Array<ExogenousSeriesConfig>
  gates?: GateConfig
  genetic?: GeneticSearchConfig | null
  include_risk_search?: boolean
  latents_enabled?: boolean
  lockbox?: LockboxConfig
  objective: ObjectiveConfig
  strategies?: Array<string> | null
  study: StudyConfig
  walkforward: WalkForwardConfig
}

export interface StrategySearchResultsResponse {
  best?: StrategySearchCandidateResponse | null
  candidates: Array<StrategySearchCandidateResponse>
  lake_paths?: Record<string, unknown> | null
  objective_mode?: string | null
  run_id: string
  search_config?: Record<string, unknown> | null
  status: string
  summary?: Record<string, unknown>
}

export interface StrategySearchRunListItem {
  best_objective_value?: number | null
  best_strategy?: string | null
  candidate_count?: number
  created_at: string
  name: string
  run_id: string
  status: string
  symbol?: string | null
}

export interface StrategySearchRunListResponse {
  items: Array<StrategySearchRunListItem>
  limit: number
  offset: number
  total: number
}

export interface StrategySearchStartResponse {
  run_id: string
  status: string
}

export interface StrategySearchStatusResponse {
  backtest_config?: Record<string, unknown> | null
  candidate_id?: string | null
  current_candidate: number
  error?: string | null
  generation?: number | null
  logs?: Array<string> | null
  phase?: "optimizing" | "testing" | "done" | null
  run_id: string
  search_config?: Record<string, unknown> | null
  status: string
  strategy?: string | null
  total_candidates: number
  total_generations?: number | null
  total_windows?: number | null
  window_index?: number | null
}

export interface StudyConfig {
  continue_on_trial_error?: boolean
  direction?: "maximize" | "minimize" | null
  max_workers?: number | null
  n_trials?: number
  name: string
  pruner?: "none" | "median" | "hyperband"
  sampler?: "tpe" | "random" | "nsgaii" | null
  seed?: number
  storage?: StorageConfig
}

export interface SystemHealthResponse {
  active_provider: "mt5" | "remote" | "local"
  backendVersion: string
  dataLakeStatus: string
  lastSyncAt: string
  market_data_inventory_count: number
  market_data_root: string
  mt5_available: boolean
  status: string
  storageStatus: StorageStatusResponse
}

export interface Tick {
  ask: number
  bid: number
  flags?: number | null
  last?: number | null
  time: string
  time_msc?: number | null
  volume?: number | null
}

export interface TransactionCostConfig {
  cost_bps?: number
  cost_per_contract?: number
}

export interface ValidateStrategySpecRequest {
  strategy_spec: Record<string, unknown>
}

export interface ValidationError {
  ctx?: Record<string, unknown>
  input?: unknown
  loc: Array<string | number>
  msg: string
  type: string
}

export interface ValidationErrorDetail {
  code: string
  message: string
  path: string
  suggestions?: Array<string>
}

export interface ValidationResult {
  errors?: Array<ValidationErrorDetail>
  valid: boolean
}

export interface WalkForwardConfig {
  max_workers?: number | null
  min_windows?: number
  mode?: "rolling" | "anchored"
  test_days: number
  train_days: number
}

export interface WalkForwardRequest {
  optimization: OptimizationConfig
  walkforward: WalkForwardConfig
}

export interface WalkForwardResultsResponse {
  efficiency?: number | null
  equity_curve: Array<EquityArtifactPoint>
  lake_paths?: Record<string, unknown> | null
  oos_metrics: Record<string, unknown>
  optimization_config?: Record<string, unknown> | null
  run_id: string
  status: string
  walkforward_config?: Record<string, unknown> | null
  windows: Array<WalkForwardWindowResultResponse>
}

export interface WalkForwardRunListItem {
  created_at: string
  efficiency?: number | null
  name: string
  run_id: string
  status: string
  strategy?: string | null
  symbol?: string | null
  window_count?: number
}

export interface WalkForwardRunListResponse {
  items: Array<WalkForwardRunListItem>
  limit: number
  offset: number
  total: number
}

export interface WalkForwardStartResponse {
  run_id: string
  status: string
}

export interface WalkForwardStatusResponse {
  backtest_config?: Record<string, unknown> | null
  current_window: number
  error?: string | null
  optimization_config?: Record<string, unknown> | null
  phase?: "optimizing" | "testing" | null
  run_id: string
  status: string
  total_windows: number
  walkforward_config?: Record<string, unknown> | null
  windows_completed: number
}

export interface WalkForwardWindowResultResponse {
  best_params?: Record<string, unknown>
  index: number
  is_metrics?: Record<string, unknown> | null
  oos_metrics?: Record<string, unknown> | null
  status: string
  test_end: string
  test_start: string
  train_end: string
  train_start: string
}

export interface WorkerLeaseResponse {
  acquired_at: string
  expires_at: string
  heartbeat_at: string
  is_active: boolean
  worker_id: string
}
