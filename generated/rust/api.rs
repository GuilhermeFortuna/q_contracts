// GENERATED FILE - DO NOT EDIT. Source schemas: schema/api/arrow/bars.schema.json, schema/api/arrow/ticks.schema.json, schema/api/arrow/trades.schema.json, schema/api/error.schema.json, schema/api/openapi.yaml
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AiModelOption {
    #[serde(default = "default_ai_model_option_available")]
    pub available: Option<bool>,
    pub id: String,
    pub label: String,
    pub provider: String,
}

fn default_ai_model_option_available() -> Option<bool> {
    Some(false)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AiProviderOption {
    pub id: String,
    pub label: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AiStrategyMetadata {
    pub assumptions: Option<Vec<String>>,
    pub capabilities_version: String,
    pub compiled_strategy: Option<serde_json::Value>,
    pub compiled_strategy_id: Option<String>,
    pub original_prompt: String,
    pub strategy_spec: serde_json::Value,
    pub strategy_spec_version: String,
    pub unsupported_requests_acknowledged: Option<Vec<String>>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AiStrategyModelsResponse {
    pub default_model: String,
    pub models: Option<Vec<AiModelOption>>,
    pub provider: String,
    pub providers: Option<Vec<AiProviderOption>>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AiStrategyResponse {
    pub assumptions: Option<Vec<String>>,
    pub change_notes: Option<Vec<String>>,
    pub compiled_strategy: Option<CompiledStrategy>,
    pub confidence: f64,
    pub questions: Option<Vec<String>>,
    pub strategy_spec: Option<serde_json::Value>,
    pub summary: String,
    pub unsupported_requests: Option<Vec<String>>,
    pub validation: Option<ValidationResult>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AiStrategyServiceErrorResponse {
    pub detail: Option<String>,
    pub message: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AlphaResearchComputeBudget {
    pub optimization_seeds: Option<i64>,
    pub study_n_trials: Option<i64>,
    pub walkforward: Option<WalkForwardConfig>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AlphaResearchRequest {
    pub catalog_version: Option<i64>,
    pub compute_budget: Option<AlphaResearchComputeBudget>,
    pub end: String,
    pub profile_id: String,
    pub profile_version: Option<i64>,
    pub start: String,
    #[serde(default = "default_alpha_research_request_target_name")]
    pub target_name: Option<String>,
}

fn default_alpha_research_request_target_name() -> Option<String> {
    Some("fwd_return".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AlphaResearchResult {
    pub acceptance: Option<serde_json::Value>,
    pub champion: Option<serde_json::Value>,
    pub coverage: Option<serde_json::Value>,
    pub feature_evidence_summary: Option<Vec<serde_json::Value>>,
    pub hypothesis_manifest: Option<Vec<serde_json::Value>>,
    pub inconclusive_reasons: Option<Vec<String>>,
    pub profile_id: String,
    pub provenance: Option<serde_json::Value>,
    pub split_manifest: Option<serde_json::Value>,
    pub stages: Option<Vec<AlphaResearchStageStatus>>,
    pub verdict: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AlphaResearchStageStatus {
    pub detail: Option<String>,
    pub name: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AlphaResearchStartResponse {
    pub job_id: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AlphaResearchStatusResponse {
    pub checkpoint: Option<serde_json::Value>,
    pub detail: Option<String>,
    pub error: Option<String>,
    pub job_id: String,
    #[serde(default = "default_alpha_research_status_response_progress")]
    pub progress: Option<f64>,
    pub result: Option<AlphaResearchResult>,
    pub stages: Option<Vec<AlphaResearchStageStatus>>,
    pub status: String,
}

fn default_alpha_research_status_response_progress() -> Option<f64> {
    Some(0.0)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ApiError {
    pub code: Option<String>,
    pub details: Option<serde_json::Value>,
    pub message: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AuditEventListResponse {
    pub items: Vec<AuditEventResponse>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AuditEventResponse {
    pub actor: Option<String>,
    pub created_at: String,
    pub deployment_id: Option<String>,
    pub event_type: String,
    pub id: String,
    pub message: String,
    pub payload: serde_json::Value,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestConfig {
    pub costs: Option<TransactionCostConfig>,
    #[serde(default = "default_backtest_config_day_trade")]
    pub day_trade: Option<bool>,
    #[serde(default = "default_backtest_config_day_trade_close_time")]
    pub day_trade_close_time: Option<String>,
    #[serde(default = "default_backtest_config_day_trade_end_time")]
    pub day_trade_end_time: Option<String>,
    #[serde(default = "default_backtest_config_day_trade_start_time")]
    pub day_trade_start_time: Option<String>,
    #[serde(default = "default_backtest_config_display_timeframe")]
    pub display_timeframe: Option<String>,
    pub end: String,
    #[serde(default = "default_backtest_config_engine")]
    pub engine: Option<String>,
    pub entries: Option<Vec<EntryInstance>>,
    pub entry_manager: Option<EntryManagerConfig>,
    pub exit_params: Option<serde_json::Value>,
    #[serde(default = "default_backtest_config_initial_capital")]
    pub initial_capital: Option<f64>,
    #[serde(default = "default_backtest_config_parallel_mode")]
    pub parallel_mode: Option<ParallelMode>,
    #[serde(default = "default_backtest_config_point_value")]
    pub point_value: Option<f64>,
    pub start: String,
    #[serde(default = "default_backtest_config_strategy")]
    pub strategy: Option<String>,
    pub symbol: String,
    pub tick_flags: Option<String>,
    #[serde(default = "default_backtest_config_timeframe")]
    pub timeframe: Option<String>,
}

fn default_backtest_config_day_trade() -> Option<bool> {
    Some(false)
}

fn default_backtest_config_day_trade_close_time() -> Option<String> {
    Some("17:00".to_owned())
}

fn default_backtest_config_day_trade_end_time() -> Option<String> {
    Some("16:00".to_owned())
}

fn default_backtest_config_day_trade_start_time() -> Option<String> {
    Some("09:00".to_owned())
}

fn default_backtest_config_display_timeframe() -> Option<String> {
    Some("M1".to_owned())
}

fn default_backtest_config_engine() -> Option<String> {
    Some("candle".to_owned())
}

fn default_backtest_config_initial_capital() -> Option<f64> {
    Some(100000.0)
}

fn default_backtest_config_parallel_mode() -> Option<ParallelMode> {
    Some("SEQUENTIAL".to_owned())
}

fn default_backtest_config_point_value() -> Option<f64> {
    Some(1.0)
}

fn default_backtest_config_strategy() -> Option<String> {
    Some("MACrossover".to_owned())
}

fn default_backtest_config_timeframe() -> Option<String> {
    Some("D1".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestConfigPayload {
    pub execution_assumptions: Option<serde_json::Value>,
    pub position_sizing: Option<serde_json::Value>,
    pub strategy: String,
    pub strategy_params: Option<serde_json::Value>,
    pub symbol: String,
    pub timeframe: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestEquityArtifactResponse {
    pub points: Vec<EquityArtifactPoint>,
    pub run_id: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestImportRequest {
    pub config: BacktestRequest,
    pub provenance: BacktestProvenance,
    pub result: BacktestResponse,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestImportResponse {
    pub run_id: String,
}

pub type BacktestOrigin = String;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestProvenance {
    pub git_dirty: Option<bool>,
    pub git_revision: Option<String>,
    pub script: String,
    pub strategy_class: String,
    pub strategy_source: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestRequest {
    pub costs: Option<TransactionCostConfig>,
    #[serde(default = "default_backtest_request_day_trade")]
    pub day_trade: Option<bool>,
    #[serde(default = "default_backtest_request_day_trade_close_time")]
    pub day_trade_close_time: Option<String>,
    #[serde(default = "default_backtest_request_day_trade_end_time")]
    pub day_trade_end_time: Option<String>,
    #[serde(default = "default_backtest_request_day_trade_start_time")]
    pub day_trade_start_time: Option<String>,
    #[serde(default = "default_backtest_request_display_timeframe")]
    pub display_timeframe: Option<String>,
    pub end: Option<String>,
    #[serde(default = "default_backtest_request_engine")]
    pub engine: Option<String>,
    pub entries: Option<Vec<EntryInstance>>,
    pub entry_manager: Option<EntryManagerConfig>,
    pub exit_params: Option<serde_json::Value>,
    #[serde(default = "default_backtest_request_initial_capital")]
    pub initial_capital: Option<f64>,
    pub ml_filter: Option<MlFilterConfig>,
    #[serde(default = "default_backtest_request_point_value")]
    pub point_value: Option<f64>,
    pub position_sizing: Option<serde_json::Value>,
    pub start: Option<String>,
    #[serde(default = "default_backtest_request_strategy")]
    pub strategy: Option<String>,
    pub strategy_params: Option<serde_json::Value>,
    pub symbol: String,
    pub tick_flags: Option<String>,
    #[serde(default = "default_backtest_request_timeframe")]
    pub timeframe: Option<String>,
}

fn default_backtest_request_day_trade() -> Option<bool> {
    Some(false)
}

fn default_backtest_request_day_trade_close_time() -> Option<String> {
    Some("17:00".to_owned())
}

fn default_backtest_request_day_trade_end_time() -> Option<String> {
    Some("16:00".to_owned())
}

fn default_backtest_request_day_trade_start_time() -> Option<String> {
    Some("09:00".to_owned())
}

fn default_backtest_request_display_timeframe() -> Option<String> {
    Some("M1".to_owned())
}

fn default_backtest_request_engine() -> Option<String> {
    Some("candle".to_owned())
}

fn default_backtest_request_initial_capital() -> Option<f64> {
    Some(100000.0)
}

fn default_backtest_request_point_value() -> Option<f64> {
    Some(1.0)
}

fn default_backtest_request_strategy() -> Option<String> {
    Some("MACrossover".to_owned())
}

fn default_backtest_request_timeframe() -> Option<String> {
    Some("D1".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestResponse {
    pub bars: Vec<OhlcvBarResponse>,
    pub indicators: Vec<ChartIndicatorSeries>,
    pub metrics: serde_json::Value,
    pub ml_filter_summary: Option<MlFilterBacktestSummary>,
    pub run_id: Option<String>,
    pub trades: Vec<serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestRunDetailResponse {
    pub config: serde_json::Value,
    pub created_at: String,
    pub error_message: Option<String>,
    pub finished_at: Option<String>,
    #[serde(default = "default_backtest_run_detail_response_is_saved")]
    pub is_saved: Option<bool>,
    #[serde(default = "default_backtest_run_detail_response_origin")]
    pub origin: Option<BacktestOrigin>,
    pub provenance: Option<BacktestProvenance>,
    pub result_summary: Option<serde_json::Value>,
    pub run_id: String,
    pub started_at: Option<String>,
    pub status: String,
    pub strategy: String,
    pub symbol: String,
    pub timeframe: String,
}

fn default_backtest_run_detail_response_is_saved() -> Option<bool> {
    Some(false)
}

fn default_backtest_run_detail_response_origin() -> Option<BacktestOrigin> {
    Some("stack".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestRunListItem {
    pub created_at: String,
    #[serde(default = "default_backtest_run_list_item_is_saved")]
    pub is_saved: Option<bool>,
    #[serde(default = "default_backtest_run_list_item_origin")]
    pub origin: Option<BacktestOrigin>,
    pub run_id: String,
    pub status: String,
    pub strategy: String,
    pub summary: Option<serde_json::Value>,
    pub symbol: String,
    pub timeframe: String,
}

fn default_backtest_run_list_item_is_saved() -> Option<bool> {
    Some(false)
}

fn default_backtest_run_list_item_origin() -> Option<BacktestOrigin> {
    Some("stack".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestRunListResponse {
    pub items: Vec<BacktestRunListItem>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestRunPatchRequest {
    pub is_saved: bool,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestStartResponse {
    pub run_id: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestStatusResponse {
    pub error: Option<String>,
    pub run_id: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BacktestTradesArtifactResponse {
    pub run_id: String,
    pub trades: Vec<serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BulkDeleteBacktestsRequest {
    pub run_ids: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BulkDeleteOptimizationsRequest {
    pub study_ids: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BulkDeleteResponse {
    pub deleted: i64,
    pub not_found: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CapabilityRegistry {
    pub condition_groups: Vec<String>,
    pub data: DataCapabilities,
    pub execution_assumptions: ExecutionAssumptions,
    pub exit_presets: Vec<ExitPreset>,
    pub exit_rules: Vec<ExitRuleInfo>,
    pub genome_limits: GenomeLimits,
    pub genome_nodes: Vec<GenomeNodeCapability>,
    pub genome_param_bounds: Vec<StrategyParamSpec>,
    pub operators: Vec<String>,
    pub risk_sizing: Vec<RiskSizingCapability>,
    #[serde(default = "default_capability_registry_schema_version")]
    pub schema_version: Option<String>,
    pub strategies: Vec<StrategyInfo>,
    pub unsupported: Vec<String>,
}

fn default_capability_registry_schema_version() -> Option<String> {
    Some("q_capabilities.v1".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CategoricalParam {
    pub choices: Vec<serde_json::Value>,
    #[serde(rename = "type")]
    #[serde(default = "default_categorical_param_type")]
    pub r#type: Option<String>,
}

fn default_categorical_param_type() -> Option<String> {
    Some("categorical".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ChartIndicatorSeries {
    pub color: Option<String>,
    pub key: String,
    pub label: String,
    pub pane: String,
    pub values: Vec<Option<f64>>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CompileStrategySpecErrorResponse {
    pub errors: Option<Vec<ValidationErrorDetail>>,
    #[serde(default = "default_compile_strategy_spec_error_response_status")]
    pub status: Option<String>,
}

fn default_compile_strategy_spec_error_response_status() -> Option<String> {
    Some("validation_failed".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CompileStrategySpecRequest {
    pub strategy_spec: serde_json::Value,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CompileStrategySpecResponse {
    pub compiled_strategy: CompiledStrategy,
    pub compiled_strategy_id: String,
    #[serde(default = "default_compile_strategy_spec_response_status")]
    pub status: Option<String>,
}

fn default_compile_strategy_spec_response_status() -> Option<String> {
    Some("compiled".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CompiledStrategy {
    pub backtest_config: BacktestConfigPayload,
    pub compiled_id: String,
    pub genome: Option<serde_json::Value>,
    pub schema_version: String,
    pub strategy_name: String,
    pub strategy_params: Option<serde_json::Value>,
    pub summary: CompiledStrategySummary,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CompiledStrategySummary {
    pub entry_summary: String,
    pub exit_summary: String,
    pub indicators: Option<Vec<String>>,
    pub mapping: String,
    pub market: String,
    pub name: String,
    pub strategy_label: String,
    pub timeframe: String,
    pub universe: Option<Vec<String>>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ConversationMessage {
    pub content: String,
    pub role: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CustomStrategySaveRequest {
    pub ai_metadata: Option<AiStrategyMetadata>,
    pub base_strategy: String,
    #[serde(default = "default_custom_strategy_save_request_description")]
    pub description: Option<String>,
    pub name: String,
    pub parameters: serde_json::Value,
}

fn default_custom_strategy_save_request_description() -> Option<String> {
    Some("".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DataCapabilities {
    pub data_sources: Vec<String>,
    pub engines: Vec<String>,
    pub markets: Vec<String>,
    pub ohlcv_columns: Vec<String>,
    pub tick_columns: Vec<String>,
    pub timeframes: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DataSourceResponse {
    pub active_provider: String,
    pub mt5_available: bool,
    pub source: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DataSourceUpdateRequest {
    pub source: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DatasetListResponse {
    pub datasets: Vec<DatasetManifestResponse>,
    pub root: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DatasetManifestResponse {
    pub arrow_schema: serde_json::Value,
    pub checksum_algorithm: String,
    pub dataset_id: String,
    pub files: Vec<ManifestFile>,
    pub published_at: String,
    pub row_count: i64,
    pub state: String,
    pub subject: serde_json::Value,
    pub supersedes: Option<String>,
    pub time_range: serde_json::Value,
    pub tombstone: Option<serde_json::Value>,
    pub version: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DecisionListResponse {
    pub items: Vec<DecisionResponse>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DecisionResponse {
    pub bar_close_time: String,
    pub config_hash: String,
    pub created_at: String,
    pub deployment_id: String,
    pub id: String,
    pub outcome: String,
    pub reason: Option<String>,
    pub requested_quantity: Option<String>,
    pub signal_action: String,
    pub strategy_name: String,
    pub strategy_version: i64,
    pub symbol: String,
    pub timeframe: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DeploymentActionRequest {
    pub action: String,
    pub actor: Option<String>,
    #[serde(default = "default_deployment_action_request_confirm")]
    pub confirm: Option<bool>,
}

fn default_deployment_action_request_confirm() -> Option<bool> {
    Some(false)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DeploymentActionResponse {
    pub accepted: bool,
    pub deployment_id: String,
    pub lifecycle: String,
    pub message: String,
    pub pending_action: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DeploymentChartBar {
    pub close: f64,
    pub high: f64,
    pub low: f64,
    pub open: f64,
    pub volume: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DeploymentChartIndicator {
    pub color: Option<String>,
    pub key: String,
    pub label: String,
    pub pane: String,
    pub values: Vec<Option<f64>>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DeploymentChartResponse {
    pub bars: Vec<DeploymentChartBar>,
    pub indicators: Vec<DeploymentChartIndicator>,
    pub last_bar_close_time: Option<String>,
    pub next_bar_close_time: Option<String>,
    pub symbol: String,
    pub timeframe: String,
    pub window_bound_bars: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DeploymentCreateRequest {
    #[serde(default = "default_deployment_create_request_broker_mode")]
    pub broker_mode: Option<String>,
    pub identity: Option<DeploymentIdentityInput>,
    #[serde(default = "default_deployment_create_request_live_activation_enabled")]
    pub live_activation_enabled: Option<bool>,
    pub name: String,
    pub paper_account_id: String,
    pub source_backtest_run_id: Option<String>,
}

fn default_deployment_create_request_broker_mode() -> Option<String> {
    Some("paper".to_owned())
}

fn default_deployment_create_request_live_activation_enabled() -> Option<bool> {
    Some(false)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DeploymentDetailResponse {
    pub broker_mode: String,
    pub compiled_config: serde_json::Value,
    pub config_hash: String,
    pub created_at: String,
    pub id: String,
    pub last_bar_close_time: Option<String>,
    pub latest_decision: Option<DecisionResponse>,
    pub lifecycle: String,
    pub live_activation_enabled: bool,
    pub name: String,
    pub open_position: Option<PositionResponse>,
    pub paper_account_id: String,
    pub pending_action: Option<String>,
    pub pending_action_requested_at: Option<String>,
    pub risk_config: serde_json::Value,
    pub sizing_config: serde_json::Value,
    pub started_at: Option<String>,
    pub stopped_at: Option<String>,
    pub strategy_name: String,
    pub strategy_version: i64,
    pub symbol: String,
    pub timeframe: String,
    #[serde(default = "default_deployment_detail_response_unknown_order_count")]
    pub unknown_order_count: Option<i64>,
    pub updated_at: String,
    pub worker_lease: Option<WorkerLeaseResponse>,
}

fn default_deployment_detail_response_unknown_order_count() -> Option<i64> {
    Some(0)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DeploymentHealthResponse {
    pub deployment_id: String,
    pub last_bar_close_time: Option<String>,
    pub latest_decision: Option<DecisionResponse>,
    pub lifecycle: String,
    pub pending_action: Option<String>,
    #[serde(default = "default_deployment_health_response_unknown_order_count")]
    pub unknown_order_count: Option<i64>,
    pub worker_lease: Option<WorkerLeaseResponse>,
}

fn default_deployment_health_response_unknown_order_count() -> Option<i64> {
    Some(0)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DeploymentIdentityInput {
    pub compiled_config: serde_json::Value,
    pub config_hash: String,
    pub risk_config: Option<serde_json::Value>,
    pub sizing_config: serde_json::Value,
    pub strategy_name: String,
    pub strategy_version: i64,
    pub symbol: String,
    pub timeframe: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DeploymentListResponse {
    pub items: Vec<DeploymentSummaryResponse>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DeploymentSummaryResponse {
    pub broker_mode: String,
    pub config_hash: String,
    pub created_at: String,
    pub id: String,
    pub last_bar_close_time: Option<String>,
    pub lifecycle: String,
    pub live_activation_enabled: bool,
    pub name: String,
    pub paper_account_id: String,
    pub pending_action: Option<String>,
    pub pending_action_requested_at: Option<String>,
    pub started_at: Option<String>,
    pub stopped_at: Option<String>,
    pub strategy_name: String,
    pub strategy_version: i64,
    pub symbol: String,
    pub timeframe: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DiscoveryAbArmSummary {
    pub mean: Option<f64>,
    pub values: Vec<f64>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DiscoveryAbPairedDelta {
    pub cohens_d: Option<f64>,
    pub mean: Option<f64>,
    pub p_value: Option<f64>,
    pub values: Vec<f64>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DiscoveryAbRequest {
    pub config: StrategySearchConfig,
    #[serde(default = "default_discovery_ab_request_minimum_complete_pairs")]
    pub minimum_complete_pairs: Option<i64>,
    pub seeds: Vec<i64>,
}

fn default_discovery_ab_request_minimum_complete_pairs() -> Option<i64> {
    Some(2)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DiscoveryAbResult {
    pub child_runs: Option<Vec<serde_json::Value>>,
    pub complete_pairs: i64,
    pub control: DiscoveryAbArmSummary,
    pub dropped_pair_reasons: Option<Vec<String>>,
    pub metric: String,
    #[serde(default = "default_discovery_ab_result_minimum_complete_pairs")]
    pub minimum_complete_pairs: Option<i64>,
    pub n_seeds: i64,
    pub paired_delta: DiscoveryAbPairedDelta,
    pub requested_seeds: i64,
    pub treatment: DiscoveryAbArmSummary,
    pub verdict: String,
}

fn default_discovery_ab_result_minimum_complete_pairs() -> Option<i64> {
    Some(2)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DiscoveryAbStartResponse {
    pub job_id: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DiscoveryAbStatusResponse {
    pub detail: Option<String>,
    pub error: Option<String>,
    pub job_id: String,
    #[serde(default = "default_discovery_ab_status_response_progress")]
    pub progress: Option<f64>,
    pub result: Option<DiscoveryAbResult>,
    pub status: String,
}

fn default_discovery_ab_status_response_progress() -> Option<f64> {
    Some(0.0)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EdgeStatusResponse {
    pub checked_at: Option<String>,
    pub mt5_connected: Option<bool>,
    pub reachable: bool,
    pub terminal_build: Option<i64>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EncoderAblationRequest {
    pub configs: Vec<EncoderConfigSpec>,
    #[serde(default = "default_encoder_ablation_request_horizon")]
    pub horizon: Option<i64>,
    pub input_features: Option<Vec<String>>,
    #[serde(default = "default_encoder_ablation_request_n_latents")]
    pub n_latents: Option<i64>,
    pub symbol: String,
    #[serde(default = "default_encoder_ablation_request_target")]
    pub target: Option<String>,
    pub timeframe: String,
    pub train_end: String,
    pub train_start: String,
}

fn default_encoder_ablation_request_horizon() -> Option<i64> {
    Some(5)
}

fn default_encoder_ablation_request_n_latents() -> Option<i64> {
    Some(2)
}

fn default_encoder_ablation_request_target() -> Option<String> {
    Some("fwd_return".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EncoderAblationResult {
    pub best_label: Option<String>,
    pub horizon: i64,
    pub rows: Vec<EncoderAblationRow>,
    pub symbol: String,
    pub target: String,
    pub timeframe: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EncoderAblationRow {
    pub baseline_ic: Option<f64>,
    pub best_latent_ic: Option<f64>,
    pub encoder_kind: String,
    pub gate_error: Option<String>,
    pub ic_delta_vs_baseline: Option<f64>,
    pub label: String,
    pub model_hash: Option<String>,
    pub passed: Option<bool>,
    pub recon_r2: Option<f64>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EncoderAblationStartResponse {
    pub job_id: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EncoderAblationStatusResponse {
    pub error: Option<String>,
    pub job_id: String,
    pub progress: Option<String>,
    pub result: Option<EncoderAblationResult>,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EncoderConfigSpec {
    pub encoder_kind: String,
    pub hyperparams: Option<serde_json::Value>,
    pub label: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EntryInstance {
    pub params: Option<serde_json::Value>,
    pub strategy: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EntryManagerConfig {
    #[serde(default = "default_entry_manager_config_kind")]
    pub kind: Option<String>,
    pub params: Option<serde_json::Value>,
}

fn default_entry_manager_config_kind() -> Option<String> {
    Some("or".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EpochMismatchResponse {
    pub current_epoch: String,
    pub requested_epoch: String,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EquityArtifactPoint {
    pub equity: f64,
    pub time: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ErrorResponse {
    pub code: Option<String>,
    pub details: Option<serde_json::Value>,
    pub message: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExecutionAssumptions {
    #[serde(default = "default_execution_assumptions_ai_builder_mvp_long_only")]
    pub ai_builder_mvp_long_only: Option<bool>,
    pub allow_short: bool,
    pub supported_entry_timing: Vec<String>,
    pub supported_signal_timing: Vec<String>,
}

fn default_execution_assumptions_ai_builder_mvp_long_only() -> Option<bool> {
    Some(true)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExecutionHealthResponse {
    pub api_status: String,
    pub checked_at: String,
    pub deployments: Vec<DeploymentHealthResponse>,
    pub edge: Option<EdgeStatusResponse>,
    pub kill_switch_enabled: bool,
    pub live_capability_locked: bool,
    pub market_data_status: String,
    pub unknown_order_count: i64,
    pub worker_heartbeat_age_s: Option<f64>,
    pub worker_started_at: Option<String>,
    pub worker_status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExecutionSnapshotLimits {
    pub recent_decisions: i64,
    pub recent_fills: i64,
    pub recent_orders: i64,
    pub recent_risk: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExecutionSnapshotRecent {
    pub decisions: Vec<serde_json::Value>,
    pub fills: Vec<serde_json::Value>,
    pub risk: Vec<serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExecutionSnapshotResponse {
    pub accounts: Vec<serde_json::Value>,
    pub control: serde_json::Value,
    pub deployments: Vec<serde_json::Value>,
    pub limits: ExecutionSnapshotLimits,
    pub orders: Vec<serde_json::Value>,
    pub positions: Vec<serde_json::Value>,
    pub recent: ExecutionSnapshotRecent,
    pub watermark: serde_json::Value,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExitPreset {
    pub description: String,
    pub id: String,
    pub label: String,
    pub parameters: serde_json::Value,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExitPresetSearchConfig {
    #[serde(default = "default_exit_preset_search_config_enabled")]
    pub enabled: Option<bool>,
    #[serde(default = "default_exit_preset_search_config_include_baseline")]
    pub include_baseline: Option<bool>,
    #[serde(default = "default_exit_preset_search_config_pin_non_preset_exits_off")]
    pub pin_non_preset_exits_off: Option<bool>,
    pub preset_ids: Option<Vec<String>>,
}

fn default_exit_preset_search_config_enabled() -> Option<bool> {
    Some(false)
}

fn default_exit_preset_search_config_include_baseline() -> Option<bool> {
    Some(true)
}

fn default_exit_preset_search_config_pin_non_preset_exits_off() -> Option<bool> {
    Some(true)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExitQualityScoringConfig {
    #[serde(default = "default_exit_quality_scoring_config_enabled")]
    pub enabled: Option<bool>,
    pub max_profit_giveback_pct: Option<f64>,
    pub min_mfe_capture_ratio: Option<f64>,
}

fn default_exit_quality_scoring_config_enabled() -> Option<bool> {
    Some(false)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExitRuleCatalogResponse {
    pub exit_presets: Vec<ExitPreset>,
    pub exit_rules: Vec<ExitRuleInfo>,
    pub shared_exit_params: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExitRuleInfo {
    pub description: String,
    pub enable_param: String,
    pub enable_value: serde_json::Value,
    pub exit_group: String,
    pub id: String,
    pub label: String,
    pub param_names: Vec<String>,
    pub required_param_names: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExogenousSeriesConfig {
    #[serde(default = "default_exogenous_series_config_availability_lag_bars")]
    pub availability_lag_bars: Option<i64>,
    #[serde(default = "default_exogenous_series_config_corr_window")]
    pub corr_window: Option<i64>,
    #[serde(default = "default_exogenous_series_config_lookback_bars")]
    pub lookback_bars: Option<i64>,
    pub recipes: Option<Vec<String>>,
    #[serde(default = "default_exogenous_series_config_resampling_rule")]
    pub resampling_rule: Option<String>,
    pub source_timeframe: String,
    pub symbol: String,
    pub target_timeframe: Option<String>,
    #[serde(default = "default_exogenous_series_config_vol_percentile_window")]
    pub vol_percentile_window: Option<i64>,
    #[serde(default = "default_exogenous_series_config_vol_regime_threshold")]
    pub vol_regime_threshold: Option<f64>,
    #[serde(default = "default_exogenous_series_config_vol_window")]
    pub vol_window: Option<i64>,
}

fn default_exogenous_series_config_availability_lag_bars() -> Option<i64> {
    Some(0)
}

fn default_exogenous_series_config_corr_window() -> Option<i64> {
    Some(20)
}

fn default_exogenous_series_config_lookback_bars() -> Option<i64> {
    Some(8)
}

fn default_exogenous_series_config_resampling_rule() -> Option<String> {
    Some("none".to_owned())
}

fn default_exogenous_series_config_vol_percentile_window() -> Option<i64> {
    Some(60)
}

fn default_exogenous_series_config_vol_regime_threshold() -> Option<f64> {
    Some(0.6)
}

fn default_exogenous_series_config_vol_window() -> Option<i64> {
    Some(20)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureEvalClusterItem {
    pub cluster_id: i64,
    pub feature_ids: Vec<String>,
    pub representative: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureEvalCreateRequest {
    pub end: String,
    pub features: Vec<FeatureEvalFeatureRequest>,
    pub start: String,
    pub symbol: String,
    pub target: FeatureEvalTargetRequest,
    pub timeframe: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureEvalFeatureRequest {
    pub name: String,
    pub params: Option<serde_json::Value>,
    pub version: Option<i64>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureEvalHeatmap {
    pub metrics: Vec<String>,
    pub rows: Vec<FeatureEvalHeatmapRow>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureEvalHeatmapRow {
    pub feature_id: String,
    pub feature_name: String,
    pub ic: Option<f64>,
    pub mutual_info: Option<f64>,
    pub rank_ic: Option<f64>,
    pub stability: Option<f64>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureEvalLeaderboardItem {
    pub cluster_id: i64,
    pub feature_id: String,
    pub feature_name: String,
    pub global_score: Option<f64>,
    pub ic: Option<f64>,
    pub is_representative: bool,
    pub leakage_status: String,
    pub mutual_info: Option<f64>,
    pub rank_ic: Option<f64>,
    pub regime_ics: serde_json::Value,
    pub stability: Option<f64>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureEvalRunResponse {
    pub clusters: Vec<FeatureEvalClusterItem>,
    pub end: String,
    pub error_message: Option<String>,
    pub feature_count: i64,
    pub finished_at: Option<String>,
    pub heatmap: FeatureEvalHeatmap,
    pub leaderboard: Vec<FeatureEvalLeaderboardItem>,
    pub matrix_id: String,
    pub result_summary: Option<serde_json::Value>,
    pub run_id: String,
    pub start: String,
    pub started_at: Option<String>,
    pub status: String,
    pub symbol: String,
    pub target_horizon: i64,
    pub target_name: String,
    pub timeframe: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureEvalStartResponse {
    pub run_id: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureEvalTargetRequest {
    pub horizon: i64,
    pub name: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureLeaderboardItem {
    pub feature_name: String,
    pub global_score: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureLeaderboardResponse {
    pub features: Vec<FeatureLeaderboardItem>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureListItem {
    pub category: String,
    pub latest_version: i64,
    pub name: String,
    pub score: Option<f64>,
    pub status: String,
    pub usage_count: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureListResponse {
    pub features: Vec<FeatureListItem>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeaturePassportResponse {
    pub category: String,
    pub description: Option<String>,
    pub evaluation_history: Vec<serde_json::Value>,
    pub name: String,
    pub score: Option<f64>,
    pub usage_count: i64,
    pub versions: Vec<FeatureVersionDetail>,
}

pub type FeatureStatus = String;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureStatusUpdateRequest {
    pub status: FeatureStatus,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FeatureVersionDetail {
    pub default_params: serde_json::Value,
    pub forward_window: i64,
    pub leakage_status: String,
    pub node_kind: String,
    pub param_keys: Vec<String>,
    pub provenance: serde_json::Value,
    pub status: String,
    pub version: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FillListResponse {
    pub items: Vec<FillResponse>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FillResponse {
    pub broker_mode: String,
    pub created_at: String,
    pub deployment_id: String,
    pub external_fill_id: String,
    pub fee: String,
    pub filled_at: String,
    pub id: String,
    pub order_id: String,
    pub price: String,
    pub quantity: String,
    pub side: String,
    pub slippage: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FixedQuantityPositionSizing {
    #[serde(default = "default_fixed_quantity_position_sizing_quantity")]
    pub quantity: Option<f64>,
    #[serde(default = "default_fixed_quantity_position_sizing_scale_by_signal_strength")]
    pub scale_by_signal_strength: Option<bool>,
    #[serde(rename = "type")]
    #[serde(default = "default_fixed_quantity_position_sizing_type")]
    pub r#type: Option<String>,
}

fn default_fixed_quantity_position_sizing_quantity() -> Option<f64> {
    Some(1.0)
}

fn default_fixed_quantity_position_sizing_scale_by_signal_strength() -> Option<bool> {
    Some(false)
}

fn default_fixed_quantity_position_sizing_type() -> Option<String> {
    Some("fixed_quantity".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FixedSafetyMarginPositionSizing {
    pub max_contracts: Option<i64>,
    #[serde(default = "default_fixed_safety_margin_position_sizing_min_contracts")]
    pub min_contracts: Option<i64>,
    #[serde(default = "default_fixed_safety_margin_position_sizing_safety_margin_per_contract")]
    pub safety_margin_per_contract: Option<f64>,
    #[serde(default = "default_fixed_safety_margin_position_sizing_scale_by_signal_strength")]
    pub scale_by_signal_strength: Option<bool>,
    #[serde(rename = "type")]
    #[serde(default = "default_fixed_safety_margin_position_sizing_type")]
    pub r#type: Option<String>,
}

fn default_fixed_safety_margin_position_sizing_min_contracts() -> Option<i64> {
    Some(1)
}

fn default_fixed_safety_margin_position_sizing_safety_margin_per_contract() -> Option<f64> {
    Some(5000.0)
}

fn default_fixed_safety_margin_position_sizing_scale_by_signal_strength() -> Option<bool> {
    Some(false)
}

fn default_fixed_safety_margin_position_sizing_type() -> Option<String> {
    Some("fixed_safety_margin".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FloatParam {
    pub high: f64,
    pub low: f64,
    pub step: Option<f64>,
    #[serde(rename = "type")]
    #[serde(default = "default_float_param_type")]
    pub r#type: Option<String>,
}

fn default_float_param_type() -> Option<String> {
    Some("float".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GateConfig {
    #[serde(default = "default_gate_config_efficiency_high")]
    pub efficiency_high: Option<f64>,
    #[serde(default = "default_gate_config_efficiency_low")]
    pub efficiency_low: Option<f64>,
    #[serde(default = "default_gate_config_min_completed_windows")]
    pub min_completed_windows: Option<i64>,
    #[serde(default = "default_gate_config_min_oos_trades")]
    pub min_oos_trades: Option<i64>,
}

fn default_gate_config_efficiency_high() -> Option<f64> {
    Some(1.5)
}

fn default_gate_config_efficiency_low() -> Option<f64> {
    Some(0.3)
}

fn default_gate_config_min_completed_windows() -> Option<i64> {
    Some(2)
}

fn default_gate_config_min_oos_trades() -> Option<i64> {
    Some(10)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GeneticSearchConfig {
    #[serde(default = "default_genetic_search_config_adaptive_operator_weights")]
    pub adaptive_operator_weights: Option<bool>,
    #[serde(default = "default_genetic_search_config_complexity_lambda")]
    pub complexity_lambda: Option<f64>,
    #[serde(default = "default_genetic_search_config_complexity_mu")]
    pub complexity_mu: Option<f64>,
    #[serde(default = "default_genetic_search_config_crossover_rate")]
    pub crossover_rate: Option<f64>,
    #[serde(default = "default_genetic_search_config_elite_count")]
    pub elite_count: Option<i64>,
    #[serde(default = "default_genetic_search_config_error_floor")]
    pub error_floor: Option<f64>,
    pub exit_policy_preset_ids: Option<Vec<String>>,
    #[serde(default = "default_genetic_search_config_exit_policy_seed_fraction")]
    pub exit_policy_seed_fraction: Option<f64>,
    #[serde(default = "default_genetic_search_config_gate_penalty_efficiency")]
    pub gate_penalty_efficiency: Option<f64>,
    #[serde(default = "default_genetic_search_config_gate_penalty_trades")]
    pub gate_penalty_trades: Option<f64>,
    #[serde(default = "default_genetic_search_config_gate_penalty_windows")]
    pub gate_penalty_windows: Option<f64>,
    #[serde(default = "default_genetic_search_config_generations")]
    pub generations: Option<i64>,
    pub init_seed: Option<i64>,
    #[serde(default = "default_genetic_search_config_max_depth")]
    pub max_depth: Option<i64>,
    #[serde(default = "default_genetic_search_config_max_nodes")]
    pub max_nodes: Option<i64>,
    pub max_workers: Option<i64>,
    #[serde(default = "default_genetic_search_config_min_seed_signals")]
    pub min_seed_signals: Option<i64>,
    #[serde(default = "default_genetic_search_config_mutation_rate")]
    pub mutation_rate: Option<f64>,
    #[serde(default = "default_genetic_search_config_mutation_rate_max")]
    pub mutation_rate_max: Option<f64>,
    #[serde(default = "default_genetic_search_config_mutation_rate_min")]
    pub mutation_rate_min: Option<f64>,
    #[serde(default = "default_genetic_search_config_no_result_floor")]
    pub no_result_floor: Option<f64>,
    #[serde(default = "default_genetic_search_config_population_size")]
    pub population_size: Option<i64>,
    #[serde(default = "default_genetic_search_config_prescreen_min_signals")]
    pub prescreen_min_signals: Option<i64>,
    #[serde(default = "default_genetic_search_config_repair_max_attempts")]
    pub repair_max_attempts: Option<i64>,
    #[serde(default = "default_genetic_search_config_seed_exit_policies")]
    pub seed_exit_policies: Option<bool>,
    #[serde(default = "default_genetic_search_config_stagnation_patience")]
    pub stagnation_patience: Option<i64>,
    #[serde(default = "default_genetic_search_config_tournament_size")]
    pub tournament_size: Option<i64>,
}

fn default_genetic_search_config_adaptive_operator_weights() -> Option<bool> {
    Some(true)
}

fn default_genetic_search_config_complexity_lambda() -> Option<f64> {
    Some(0.001)
}

fn default_genetic_search_config_complexity_mu() -> Option<f64> {
    Some(0.0005)
}

fn default_genetic_search_config_crossover_rate() -> Option<f64> {
    Some(0.7)
}

fn default_genetic_search_config_elite_count() -> Option<i64> {
    Some(4)
}

fn default_genetic_search_config_error_floor() -> Option<f64> {
    Some(-4.0)
}

fn default_genetic_search_config_exit_policy_seed_fraction() -> Option<f64> {
    Some(0.25)
}

fn default_genetic_search_config_gate_penalty_efficiency() -> Option<f64> {
    Some(0.5)
}

fn default_genetic_search_config_gate_penalty_trades() -> Option<f64> {
    Some(0.5)
}

fn default_genetic_search_config_gate_penalty_windows() -> Option<f64> {
    Some(0.5)
}

fn default_genetic_search_config_generations() -> Option<i64> {
    Some(12)
}

fn default_genetic_search_config_max_depth() -> Option<i64> {
    Some(12)
}

fn default_genetic_search_config_max_nodes() -> Option<i64> {
    Some(24)
}

fn default_genetic_search_config_min_seed_signals() -> Option<i64> {
    Some(1)
}

fn default_genetic_search_config_mutation_rate() -> Option<f64> {
    Some(0.15)
}

fn default_genetic_search_config_mutation_rate_max() -> Option<f64> {
    Some(0.5)
}

fn default_genetic_search_config_mutation_rate_min() -> Option<f64> {
    Some(0.1)
}

fn default_genetic_search_config_no_result_floor() -> Option<f64> {
    Some(-2.0)
}

fn default_genetic_search_config_population_size() -> Option<i64> {
    Some(48)
}

fn default_genetic_search_config_prescreen_min_signals() -> Option<i64> {
    Some(1)
}

fn default_genetic_search_config_repair_max_attempts() -> Option<i64> {
    Some(8)
}

fn default_genetic_search_config_seed_exit_policies() -> Option<bool> {
    Some(true)
}

fn default_genetic_search_config_stagnation_patience() -> Option<i64> {
    Some(2)
}

fn default_genetic_search_config_tournament_size() -> Option<i64> {
    Some(3)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GenomeLimits {
    pub max_depth: i64,
    pub max_node_count: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GenomeNodeCapability {
    pub allowed_param_keys: Vec<String>,
    pub input_series_types: Option<Vec<String>>,
    pub kind: String,
    pub max_inputs: i64,
    pub min_inputs: i64,
    pub output_ports: Vec<String>,
    pub port_types: serde_json::Value,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HTTPValidationError {
    pub detail: Option<Vec<ValidationError>>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HistoryExpiredResponse {
    pub oldest_available_seq: Option<i64>,
    pub requested_from_seq: i64,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct HistoryPageResponse {
    pub entries: Vec<serde_json::Value>,
    pub epoch: String,
    pub next_seq: Option<i64>,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct IngestJobRequest {
    pub end: String,
    #[serde(default = "default_ingest_job_request_kind")]
    pub kind: Option<String>,
    pub start: String,
    pub symbol: String,
    pub timeframes: Option<Vec<String>>,
}

fn default_ingest_job_request_kind() -> Option<String> {
    Some("bars".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct InstrumentInfoResponse {
    pub contractSize: f64,
    pub currencyBase: String,
    pub currencyProfit: String,
    pub description: String,
    pub digits: i64,
    pub exchange: String,
    pub point: f64,
    pub spreadFloating: bool,
    pub symbol: String,
    pub tickSize: f64,
    pub tickValue: f64,
    pub volumeMax: f64,
    pub volumeMin: f64,
    pub volumeStep: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct InstrumentResponse {
    pub assetClass: String,
    pub exchange: String,
    pub name: String,
    pub symbol: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct IntParam {
    pub high: i64,
    pub low: i64,
    #[serde(default = "default_int_param_step")]
    pub step: Option<i64>,
    #[serde(rename = "type")]
    #[serde(default = "default_int_param_type")]
    pub r#type: Option<String>,
}

fn default_int_param_step() -> Option<i64> {
    Some(1)
}

fn default_int_param_type() -> Option<String> {
    Some("int".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct InverseVolatilityPositionSizing {
    pub max_contracts: Option<i64>,
    #[serde(default = "default_inverse_volatility_position_sizing_min_contracts")]
    pub min_contracts: Option<i64>,
    #[serde(default = "default_inverse_volatility_position_sizing_scale_by_signal_strength")]
    pub scale_by_signal_strength: Option<bool>,
    #[serde(default = "default_inverse_volatility_position_sizing_target_volatility_pct")]
    pub target_volatility_pct: Option<f64>,
    #[serde(rename = "type")]
    #[serde(default = "default_inverse_volatility_position_sizing_type")]
    pub r#type: Option<String>,
}

fn default_inverse_volatility_position_sizing_min_contracts() -> Option<i64> {
    Some(0)
}

fn default_inverse_volatility_position_sizing_scale_by_signal_strength() -> Option<bool> {
    Some(false)
}

fn default_inverse_volatility_position_sizing_target_volatility_pct() -> Option<f64> {
    Some(10.0)
}

fn default_inverse_volatility_position_sizing_type() -> Option<String> {
    Some("inverse_volatility".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct JobSnapshotItem {
    pub job_id: String,
    pub kind: String,
    pub message: Option<String>,
    pub progress: Option<f64>,
    pub progress_epoch: Option<String>,
    pub progress_seq: Option<i64>,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct JobSnapshotResponse {
    pub jobs: Vec<JobSnapshotItem>,
    pub watermark: serde_json::Value,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct KillSwitchResponse {
    pub enabled: bool,
    pub reason: Option<String>,
    pub updated_at: Option<String>,
    pub updated_by: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct KillSwitchUpdateRequest {
    #[serde(default = "default_kill_switch_update_request_confirm")]
    pub confirm: Option<bool>,
    pub enabled: bool,
    pub reason: Option<String>,
    pub updated_by: Option<String>,
}

fn default_kill_switch_update_request_confirm() -> Option<bool> {
    Some(false)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct KillSwitchUpdateResponse {
    pub accepted: bool,
    pub audit_event_id: String,
    pub kill_switch: KillSwitchResponse,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LatentGateResultResponse {
    pub baseline_ic: f64,
    pub best_latent_ic: f64,
    pub evaluation_run_id: String,
    pub n_latents_beating_baseline: i64,
    pub passed: bool,
    pub target_horizon: Option<i64>,
    pub target_name: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LatestResponse {
    pub entries: serde_json::Value,
    pub topic: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LedgerEntryListResponse {
    pub items: Vec<LedgerEntryResponse>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LedgerEntryResponse {
    pub amount: String,
    pub balance_after: String,
    pub created_at: String,
    pub deployment_id: String,
    pub description: Option<String>,
    pub entry_type: String,
    pub fill_id: Option<String>,
    pub id: String,
    pub paper_account_id: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LockboxConfig {
    #[serde(default = "default_lockbox_config_enabled")]
    pub enabled: Option<bool>,
    pub lockbox_days: Option<i64>,
    #[serde(default = "default_lockbox_config_lockbox_pct")]
    pub lockbox_pct: Option<f64>,
    pub max_drawdown_pct: Option<f64>,
    #[serde(default = "default_lockbox_config_min_trades")]
    pub min_trades: Option<i64>,
}

fn default_lockbox_config_enabled() -> Option<bool> {
    Some(false)
}

fn default_lockbox_config_lockbox_pct() -> Option<f64> {
    Some(0.15)
}

fn default_lockbox_config_min_trades() -> Option<i64> {
    Some(5)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LogFloatParam {
    pub high: f64,
    pub low: f64,
    #[serde(rename = "type")]
    #[serde(default = "default_log_float_param_type")]
    pub r#type: Option<String>,
}

fn default_log_float_param_type() -> Option<String> {
    Some("log-float".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ManifestFile {
    pub checksum: String,
    pub path: String,
    pub size_bytes: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MarketSnapshotResponse {
    #[serde(default = "default_market_snapshot_response_ask")]
    pub ask: Option<f64>,
    #[serde(default = "default_market_snapshot_response_bid")]
    pub bid: Option<f64>,
    #[serde(default = "default_market_snapshot_response_change_abs")]
    pub changeAbs: Option<f64>,
    pub changePct: f64,
    #[serde(default = "default_market_snapshot_response_day_high")]
    pub dayHigh: Option<f64>,
    #[serde(default = "default_market_snapshot_response_day_low")]
    pub dayLow: Option<f64>,
    #[serde(default = "default_market_snapshot_response_day_open")]
    pub dayOpen: Option<f64>,
    #[serde(default = "default_market_snapshot_response_digits")]
    pub digits: Option<i64>,
    pub last: f64,
    #[serde(default = "default_market_snapshot_response_prev_close")]
    pub prevClose: Option<f64>,
    #[serde(default = "default_market_snapshot_response_spread")]
    pub spread: Option<f64>,
    pub symbol: String,
    pub tickTime: Option<String>,
    pub volume: i64,
}

fn default_market_snapshot_response_ask() -> Option<f64> {
    Some(0.0)
}

fn default_market_snapshot_response_bid() -> Option<f64> {
    Some(0.0)
}

fn default_market_snapshot_response_change_abs() -> Option<f64> {
    Some(0.0)
}

fn default_market_snapshot_response_day_high() -> Option<f64> {
    Some(0.0)
}

fn default_market_snapshot_response_day_low() -> Option<f64> {
    Some(0.0)
}

fn default_market_snapshot_response_day_open() -> Option<f64> {
    Some(0.0)
}

fn default_market_snapshot_response_digits() -> Option<i64> {
    Some(0)
}

fn default_market_snapshot_response_prev_close() -> Option<f64> {
    Some(0.0)
}

fn default_market_snapshot_response_spread() -> Option<f64> {
    Some(0.0)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MarketSnapshotsResponse {
    pub snapshots: Vec<MarketSnapshotResponse>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MarketTapeTickResponse {
    pub ask: f64,
    pub bid: f64,
    pub last: f64,
    pub side: Option<String>,
    pub volume: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MarketTicksResponse {
    pub ticks: Vec<MarketTapeTickResponse>,
}

pub type MlFilterAlgorithm = String;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterAlgorithmHyperparams {
    pub lightgbm: Option<MlFilterLightgbmHyperparams>,
    pub logistic_regression: Option<MlFilterLogisticRegressionHyperparams>,
    pub random_forest: Option<MlFilterRandomForestHyperparams>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterBacktestSummary {
    pub candidates_accepted: Option<i64>,
    pub candidates_not_ready: Option<i64>,
    pub candidates_rejected: Option<i64>,
    pub candidates_scored: Option<i64>,
    pub dataset_id: Option<String>,
    pub model_version_id: String,
    pub threshold: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterComparisonRequest {
    pub dataset_id: String,
    pub model_version_ids: Vec<String>,
    #[serde(default = "default_ml_filter_comparison_request_threshold")]
    pub threshold: Option<f64>,
}

fn default_ml_filter_comparison_request_threshold() -> Option<f64> {
    Some(0.5)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterComparisonResultEntry {
    pub acceptance_counts: Option<serde_json::Value>,
    pub baseline: Option<MlFilterEngineMetrics>,
    pub classification: Option<MlFilterValidationMetrics>,
    pub dataset_id: String,
    pub equity_artifact_ref: Option<String>,
    pub filtered: Option<MlFilterEngineMetrics>,
    pub model_version_id: String,
    pub threshold: f64,
    pub trades_artifact_ref: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterComparisonStartResponse {
    pub job_id: String,
    pub status: MlFilterJobStatus,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterComparisonStatusResponse {
    pub error: Option<MlFilterError>,
    pub job_id: String,
    pub results: Option<Vec<MlFilterComparisonResultEntry>>,
    pub status: MlFilterJobStatus,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterConfig {
    pub model_version_id: String,
    #[serde(default = "default_ml_filter_config_threshold")]
    pub threshold: Option<f64>,
}

fn default_ml_filter_config_threshold() -> Option<f64> {
    Some(0.5)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterEngineMetrics {
    pub max_drawdown: f64,
    pub net_pnl: f64,
    pub profit_factor: Option<MlFilterNullableFloat>,
    pub trade_count: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterError {
    pub code: MlFilterErrorCode,
    pub details: Option<serde_json::Value>,
    pub message: String,
}

pub type MlFilterErrorCode = String;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterEvaluationRequest {
    pub dataset_id: String,
    pub model_version_id: String,
    #[serde(default = "default_ml_filter_evaluation_request_threshold")]
    pub threshold: Option<f64>,
}

fn default_ml_filter_evaluation_request_threshold() -> Option<f64> {
    Some(0.5)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterEvaluationResult {
    pub baseline: MlFilterEngineMetrics,
    pub filtered: MlFilterEngineMetrics,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterEvaluationStartResponse {
    pub job_id: String,
    pub status: MlFilterJobStatus,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterEvaluationStatusResponse {
    pub dataset_id: Option<String>,
    pub error: Option<MlFilterError>,
    pub job_id: String,
    pub model_version_id: Option<String>,
    pub result: Option<MlFilterEvaluationResult>,
    pub status: MlFilterJobStatus,
    pub threshold: Option<f64>,
}

pub type MlFilterFeatureName = String;

pub type MlFilterJobStage = String;

pub type MlFilterJobStatus = String;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterLightgbmHyperparams {
    #[serde(default = "default_ml_filter_lightgbm_hyperparams_learning_rate")]
    pub learning_rate: Option<f64>,
    #[serde(default = "default_ml_filter_lightgbm_hyperparams_n_estimators")]
    pub n_estimators: Option<i64>,
    #[serde(default = "default_ml_filter_lightgbm_hyperparams_num_leaves")]
    pub num_leaves: Option<i64>,
}

fn default_ml_filter_lightgbm_hyperparams_learning_rate() -> Option<f64> {
    Some(0.1)
}

fn default_ml_filter_lightgbm_hyperparams_n_estimators() -> Option<i64> {
    Some(100)
}

fn default_ml_filter_lightgbm_hyperparams_num_leaves() -> Option<i64> {
    Some(31)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterLogisticRegressionHyperparams {
    #[serde(default = "default_ml_filter_logistic_regression_hyperparams_c")]
    pub C: Option<f64>,
    #[serde(default = "default_ml_filter_logistic_regression_hyperparams_max_iter")]
    pub max_iter: Option<i64>,
}

fn default_ml_filter_logistic_regression_hyperparams_c() -> Option<f64> {
    Some(1.0)
}

fn default_ml_filter_logistic_regression_hyperparams_max_iter() -> Option<i64> {
    Some(1000)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterModelDetailResponse {
    pub algorithm: MlFilterAlgorithm,
    pub dataset_id: String,
    pub manifest_identity: Option<serde_json::Value>,
    pub model_version_id: String,
    pub pipeline_versions: Option<serde_json::Value>,
    pub provenance: Option<serde_json::Value>,
    pub selected_features: Option<Vec<MlFilterFeatureName>>,
    pub validation_metrics: Option<MlFilterValidationMetrics>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterModelListResponse {
    pub items: Vec<MlFilterModelSummary>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterModelSummary {
    pub algorithm: MlFilterAlgorithm,
    pub compatibility_reasons: Option<Vec<String>>,
    pub dataset_id: String,
    pub model_version_id: String,
    pub ready: bool,
    pub selected_features: Option<Vec<MlFilterFeatureName>>,
    pub symbol: Option<String>,
    pub timeframe: Option<String>,
    pub train_end: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterNullableFloat {
    pub unavailable_reason: Option<String>,
    pub value: Option<f64>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterProgressCount {
    pub current: i64,
    pub total: Option<i64>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterRandomForestHyperparams {
    pub max_depth: Option<i64>,
    #[serde(default = "default_ml_filter_random_forest_hyperparams_min_samples_leaf")]
    pub min_samples_leaf: Option<i64>,
    #[serde(default = "default_ml_filter_random_forest_hyperparams_n_estimators")]
    pub n_estimators: Option<i64>,
}

fn default_ml_filter_random_forest_hyperparams_min_samples_leaf() -> Option<i64> {
    Some(1)
}

fn default_ml_filter_random_forest_hyperparams_n_estimators() -> Option<i64> {
    Some(200)
}

pub type MlFilterSourceDetailResponse = serde_json::Value;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterSourceListResponse {
    pub items: Vec<MlFilterSourceSummary>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterSourceSummary {
    pub available_features: Option<Vec<MlFilterFeatureName>>,
    pub date_range_end: Option<String>,
    pub date_range_start: Option<String>,
    pub eligibility_reason: Option<String>,
    pub eligible: bool,
    pub run_id: String,
    pub source_sample_count: i64,
    pub strategy: Option<String>,
    pub symbol: String,
    pub timeframe: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterSplitSuggestion {
    pub train_end: String,
    pub validation_end: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterTrainingRequest {
    pub algorithms: Vec<MlFilterAlgorithm>,
    pub hyperparameters: Option<MlFilterAlgorithmHyperparams>,
    #[serde(default = "default_ml_filter_training_request_seed")]
    pub seed: Option<i64>,
    pub selected_features: Vec<MlFilterFeatureName>,
    pub source_run_id: String,
    pub train_end: String,
    pub validation_end: String,
}

fn default_ml_filter_training_request_seed() -> Option<i64> {
    Some(42)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterTrainingStartResponse {
    pub job_id: String,
    pub status: MlFilterJobStatus,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterTrainingStatusResponse {
    pub comparison_id: Option<String>,
    pub dataset_id: Option<String>,
    pub error: Option<MlFilterError>,
    pub job_id: String,
    pub model_version_ids: Option<Vec<String>>,
    pub progress: Option<MlFilterProgressCount>,
    pub rejections: Option<serde_json::Value>,
    pub stage: Option<MlFilterJobStage>,
    pub status: MlFilterJobStatus,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MlFilterValidationMetrics {
    pub confusion_matrix: Option<Vec<Vec<i64>>>,
    pub roc_auc: Option<MlFilterNullableFloat>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NeuralModelDetailResponse {
    pub created_at: String,
    pub gate_result: Option<LatentGateResultResponse>,
    pub latent_names: Vec<String>,
    pub model_hash: String,
    pub model_key: String,
    pub n_latents: i64,
    pub status: String,
    pub symbol: String,
    pub timeframe: String,
    pub train_end: String,
    pub train_start: String,
    pub val_metrics: serde_json::Value,
    pub version: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NeuralModelListItem {
    pub created_at: String,
    pub model_hash: String,
    pub model_key: String,
    pub n_latents: i64,
    pub status: String,
    pub symbol: String,
    pub timeframe: String,
    pub val_metrics: serde_json::Value,
    pub version: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NeuralModelListResponse {
    pub models: Vec<NeuralModelListItem>,
}

pub type NeuralModelStatus = String;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NeuralModelStatusUpdateRequest {
    pub status: NeuralModelStatus,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NeuralTrainEvaluateRequest {
    pub horizon: i64,
    pub target: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NeuralTrainRequest {
    pub evaluate: Option<NeuralTrainEvaluateRequest>,
    pub hyperparams: Option<serde_json::Value>,
    pub input_features: Vec<String>,
    #[serde(default = "default_neural_train_request_kind")]
    pub kind: Option<String>,
    pub model_key: Option<String>,
    pub n_latents: i64,
    pub symbol: String,
    pub timeframe: String,
    pub train_end: String,
    pub train_start: String,
}

fn default_neural_train_request_kind() -> Option<String> {
    Some("pca".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NeuralTrainStartResponse {
    pub job_id: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NeuralTrainStatusResponse {
    pub error: Option<String>,
    pub gate: Option<serde_json::Value>,
    pub gate_error: Option<String>,
    pub job_id: String,
    pub model_hash: Option<String>,
    pub progress: Option<String>,
    pub status: String,
    pub val_metrics: Option<serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NewsArticleResponse {
    pub content: String,
    pub id: String,
    pub imageUrl: Option<String>,
    pub publishedAt: String,
    pub source: String,
    pub summary: String,
    pub title: String,
    pub videoUrl: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OHLCV {
    pub close: f64,
    pub high: f64,
    pub low: f64,
    pub open: f64,
    pub real_volume: Option<i64>,
    pub spread: Option<i64>,
    pub tick_volume: i64,
    pub time: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ObjectiveConfig {
    pub mode: ObjectiveMode,
}

pub type ObjectiveMode = String;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OhlcvAvailableRangeResponse {
    pub bar_count: i64,
    pub end: String,
    pub start: String,
    pub symbol: String,
    pub timeframe: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OhlcvBarResponse {
    pub close: f64,
    pub high: f64,
    pub low: f64,
    pub open: f64,
    pub volume: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OptimizationAnalyticsResponse {
    pub is_multi_objective: bool,
    pub n_complete_trials: i64,
    pub objective_labels: Vec<String>,
    pub parallel_coordinate: ParallelCoordinatePayload,
    pub param_importances: Option<serde_json::Value>,
    pub pareto_front: ParetoFrontPayload,
    pub status: String,
    pub study_id: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OptimizationConfig {
    pub backtest: BacktestConfig,
    pub fixed_params: Option<serde_json::Value>,
    pub objective: ObjectiveConfig,
    pub search_space: SearchSpaceConfig,
    pub study: StudyConfig,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OptimizationResultsResponse {
    pub best_params: serde_json::Value,
    pub best_trial: Option<serde_json::Value>,
    pub failures: Vec<serde_json::Value>,
    pub is_multi_objective: bool,
    pub objective_mode: String,
    pub pareto_trials: Vec<serde_json::Value>,
    pub study_id: String,
    pub trials: Vec<serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OptimizationStartResponse {
    pub status: String,
    pub study_id: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OptimizationStatusResponse {
    pub backtest_config: Option<serde_json::Value>,
    pub best_params: Option<serde_json::Value>,
    pub best_trial: Option<serde_json::Value>,
    pub best_value: Option<f64>,
    pub completed_trials: i64,
    pub error: Option<String>,
    pub n_trials: i64,
    pub optimization_config: Option<serde_json::Value>,
    pub status: String,
    pub study_id: String,
    pub trials: Option<Vec<serde_json::Value>>,
    #[serde(default = "default_optimization_status_response_workers")]
    pub workers: Option<i64>,
}

fn default_optimization_status_response_workers() -> Option<i64> {
    Some(1)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OptimizationStudyListItem {
    pub best_value: Option<f64>,
    pub completed_trials: i64,
    pub created_at: String,
    pub n_trials: i64,
    pub name: String,
    pub status: String,
    pub study_id: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OptimizationStudyListResponse {
    pub items: Vec<OptimizationStudyListItem>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OrderListResponse {
    pub items: Vec<OrderResponse>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OrderResolutionRequest {
    pub actor: String,
    pub external_fill_id: Option<String>,
    pub fee: Option<serde_json::Value>,
    pub filled_at: Option<String>,
    pub outcome: String,
    pub price: Option<serde_json::Value>,
    pub quantity: Option<serde_json::Value>,
    pub reason: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OrderResolutionResponse {
    pub accepted: bool,
    pub message: String,
    pub order: OrderResponse,
    pub resolution: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OrderResponse {
    pub broker_mode: String,
    pub completed_at: Option<String>,
    pub created_at: String,
    pub decision_id: Option<String>,
    pub deployment_id: String,
    pub id: String,
    pub intent_committed_at: Option<String>,
    pub order_type: String,
    pub quantity: String,
    pub reconciled_at: Option<String>,
    pub reconciled_by: Option<String>,
    pub reconciliation_attempted_at: Option<String>,
    pub reconciliation_detail: Option<String>,
    pub reconciliation_error: Option<String>,
    pub reconciliation_state: String,
    pub rejection_reason: Option<String>,
    pub side: String,
    pub status: String,
    pub submitted_at: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PaperAccountCreateRequest {
    #[serde(default = "default_paper_account_create_request_currency")]
    pub currency: Option<String>,
    pub initial_balance: serde_json::Value,
    pub name: String,
    pub risk_config: Option<serde_json::Value>,
    pub sizing_config: Option<serde_json::Value>,
}

fn default_paper_account_create_request_currency() -> Option<String> {
    Some("BRL".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PaperAccountListResponse {
    pub items: Vec<PaperAccountResponse>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PaperAccountResponse {
    pub cash_balance: String,
    pub created_at: String,
    pub currency: String,
    pub id: String,
    pub initial_balance: String,
    pub name: String,
    pub risk_config: serde_json::Value,
    pub sizing_config: serde_json::Value,
    pub updated_at: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParallelCoordinatePayload {
    pub objectives: Vec<String>,
    pub params: Vec<String>,
    pub rows: Vec<ParallelCoordinateRow>,
    pub rows_capped: Option<bool>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParallelCoordinateRow {
    pub number: i64,
    pub params: serde_json::Value,
    pub values: Vec<f64>,
}

pub type ParallelMode = String;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParamImportanceEntry {
    pub importance: f64,
    pub param: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParetoFrontPayload {
    pub is_multi_objective: bool,
    pub objectives: Vec<String>,
    pub points: Vec<ParetoPoint>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ParetoPoint {
    pub number: i64,
    pub params: serde_json::Value,
    pub values: Vec<f64>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PendingReconciliationListResponse {
    pub items: Vec<OrderResponse>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PositionListResponse {
    pub items: Vec<PositionResponse>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PositionResponse {
    pub average_entry_price: Option<String>,
    pub closed_at: Option<String>,
    pub deployment_id: String,
    pub id: String,
    pub is_open: bool,
    pub opened_at: Option<String>,
    pub quantity: String,
    pub side: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RiskEventListResponse {
    pub items: Vec<RiskEventResponse>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RiskEventResponse {
    pub context: serde_json::Value,
    pub created_at: String,
    pub decision_id: Option<String>,
    pub deployment_id: String,
    pub id: String,
    pub message: String,
    pub order_id: Option<String>,
    pub rejection_code: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RiskSizingCapability {
    pub description: String,
    pub label: String,
    #[serde(rename = "type")]
    pub r#type: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SearchSpaceConfig {
    pub manager_params: Option<serde_json::Value>,
    pub risk_params: Option<serde_json::Value>,
    pub strategy_params: Option<serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SignalManagerCatalogResponse {
    pub managers: Vec<SignalManagerInfo>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SignalManagerInfo {
    pub description: String,
    pub id: String,
    pub label: String,
    pub param_names: Vec<String>,
    pub params: Option<Vec<StrategyParamSpec>>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StorageConfig {
    pub path: Option<String>,
    #[serde(rename = "type")]
    #[serde(default = "default_storage_config_type")]
    pub r#type: Option<String>,
    pub url: Option<String>,
}

fn default_storage_config_type() -> Option<String> {
    Some("memory".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StorageDeleteResponse {
    pub deleted: bool,
    pub symbol: String,
    pub timeframe: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StorageIngestStartResponse {
    pub job_id: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StorageIngestStatusResponse {
    pub detail: String,
    pub error: Option<String>,
    pub job_id: String,
    pub progress: f64,
    pub results: Option<Vec<serde_json::Value>>,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StorageInventoryItem {
    pub bytes: i64,
    pub end: String,
    #[serde(default = "default_storage_inventory_item_kind")]
    pub kind: Option<String>,
    pub rows: i64,
    pub start: String,
    pub symbol: String,
    pub timeframe: Option<String>,
    pub updated_at: String,
}

fn default_storage_inventory_item_kind() -> Option<String> {
    Some("bars".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StorageInventoryResponse {
    pub items: Vec<StorageInventoryItem>,
    pub root: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StorageServiceStatus {
    pub error: Option<String>,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StorageStatusResponse {
    pub postgres: StorageServiceStatus,
    pub redis: StorageServiceStatus,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategiesResponse {
    pub strategies: Vec<StrategyInfo>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategyInfo {
    #[serde(default = "default_strategy_info_category")]
    pub category: Option<String>,
    pub description: String,
    #[serde(default = "default_strategy_info_engine")]
    pub engine: Option<String>,
    pub label: String,
    pub name: String,
    pub params: Vec<StrategyParamSpec>,
    pub research_only: Option<bool>,
    #[serde(default = "default_strategy_info_strong_in")]
    pub strong_in: Option<String>,
    pub supports_discovery: Option<bool>,
    pub supports_optimization: Option<bool>,
    pub supports_walkforward: Option<bool>,
    #[serde(default = "default_strategy_info_thesis")]
    pub thesis: Option<String>,
    #[serde(default = "default_strategy_info_weak_in")]
    pub weak_in: Option<String>,
}

fn default_strategy_info_category() -> Option<String> {
    Some("other".to_owned())
}

fn default_strategy_info_engine() -> Option<String> {
    Some("candle".to_owned())
}

fn default_strategy_info_strong_in() -> Option<String> {
    Some("".to_owned())
}

fn default_strategy_info_thesis() -> Option<String> {
    Some("".to_owned())
}

fn default_strategy_info_weak_in() -> Option<String> {
    Some("".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategyInterpretRequest {
    #[serde(default = "default_strategy_interpret_request_capabilities_version")]
    pub capabilities_version: Option<String>,
    pub conversation: Option<Vec<ConversationMessage>>,
    pub current_spec: Option<serde_json::Value>,
    pub message: String,
    pub model: Option<String>,
    pub provider: Option<String>,
    pub validation_errors: Option<Vec<ValidationErrorDetail>>,
}

fn default_strategy_interpret_request_capabilities_version() -> Option<String> {
    Some("q_capabilities.v1".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategyParamSpec {
    pub choices: Option<Vec<String>>,
    pub default: serde_json::Value,
    pub exit_group: Option<String>,
    pub hint: Option<String>,
    pub label: String,
    pub max: Option<f64>,
    pub min: Option<f64>,
    pub name: String,
    pub search_max: Option<f64>,
    pub search_min: Option<f64>,
    pub search_scale: Option<String>,
    pub search_step: Option<f64>,
    #[serde(default = "default_strategy_param_spec_searchable")]
    pub searchable: Option<bool>,
    pub step: Option<f64>,
    #[serde(rename = "type")]
    pub r#type: String,
}

fn default_strategy_param_spec_searchable() -> Option<bool> {
    Some(true)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategySearchCandidateEquityArtifactResponse {
    pub candidate_id: String,
    pub points: Vec<EquityArtifactPoint>,
    pub run_id: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategySearchCandidateGenomeResponse {
    pub candidate_id: String,
    pub genome: serde_json::Value,
    pub run_id: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategySearchCandidateResponse {
    pub best_params: Option<serde_json::Value>,
    pub candidate_id: String,
    #[serde(default = "default_strategy_search_candidate_response_completed_windows")]
    pub completed_windows: Option<i64>,
    pub complexity_penalty: Option<f64>,
    pub diagnostics: Option<serde_json::Value>,
    pub dsr: Option<f64>,
    pub efficiency: Option<f64>,
    pub error: Option<String>,
    pub exit_param_names: Option<Vec<String>>,
    pub exit_policy_id: Option<String>,
    pub exit_policy_label: Option<String>,
    pub exit_preset_id: Option<String>,
    pub exit_preset_label: Option<String>,
    pub exit_quality: Option<serde_json::Value>,
    pub gate_flags: Option<Vec<String>>,
    pub generation: Option<i64>,
    pub genome: Option<serde_json::Value>,
    pub genome_node_count: Option<i64>,
    pub hypothesis_id: Option<String>,
    pub hypothesis_rationale: Option<String>,
    pub hypothesis_required_features: Option<Vec<String>>,
    pub hypothesis_template_hash: Option<String>,
    pub is_metrics_summary: Option<serde_json::Value>,
    pub last_exit_mutation_op: Option<String>,
    pub objective_value: Option<f64>,
    pub oos_metrics: Option<serde_json::Value>,
    #[serde(default = "default_strategy_search_candidate_response_passed_gates")]
    pub passed_gates: Option<bool>,
    pub profile_version: Option<i64>,
    pub rank: Option<i64>,
    pub robustness_score: Option<f64>,
    pub status: String,
    pub strategy: String,
    #[serde(default = "default_strategy_search_candidate_response_window_count")]
    pub window_count: Option<i64>,
}

fn default_strategy_search_candidate_response_completed_windows() -> Option<i64> {
    Some(0)
}

fn default_strategy_search_candidate_response_passed_gates() -> Option<bool> {
    Some(false)
}

fn default_strategy_search_candidate_response_window_count() -> Option<i64> {
    Some(0)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategySearchConfig {
    pub backtest: BacktestConfig,
    pub exit_presets: Option<ExitPresetSearchConfig>,
    pub exit_quality_scoring: Option<ExitQualityScoringConfig>,
    pub exogenous_provenance: Option<Vec<serde_json::Value>>,
    pub exogenous_series: Option<Vec<ExogenousSeriesConfig>>,
    pub gates: Option<GateConfig>,
    pub genetic: Option<GeneticSearchConfig>,
    #[serde(default = "default_strategy_search_config_include_risk_search")]
    pub include_risk_search: Option<bool>,
    #[serde(default = "default_strategy_search_config_latents_enabled")]
    pub latents_enabled: Option<bool>,
    pub lockbox: Option<LockboxConfig>,
    pub objective: ObjectiveConfig,
    pub strategies: Option<Vec<String>>,
    pub study: StudyConfig,
    pub walkforward: WalkForwardConfig,
}

fn default_strategy_search_config_include_risk_search() -> Option<bool> {
    Some(true)
}

fn default_strategy_search_config_latents_enabled() -> Option<bool> {
    Some(true)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategySearchResultsResponse {
    pub best: Option<StrategySearchCandidateResponse>,
    pub candidates: Vec<StrategySearchCandidateResponse>,
    pub lake_paths: Option<serde_json::Value>,
    pub objective_mode: Option<String>,
    pub run_id: String,
    pub search_config: Option<serde_json::Value>,
    pub status: String,
    pub summary: Option<serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategySearchRunListItem {
    pub best_objective_value: Option<f64>,
    pub best_strategy: Option<String>,
    #[serde(default = "default_strategy_search_run_list_item_candidate_count")]
    pub candidate_count: Option<i64>,
    pub created_at: String,
    pub name: String,
    pub run_id: String,
    pub status: String,
    pub symbol: Option<String>,
}

fn default_strategy_search_run_list_item_candidate_count() -> Option<i64> {
    Some(0)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategySearchRunListResponse {
    pub items: Vec<StrategySearchRunListItem>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategySearchStartResponse {
    pub run_id: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StrategySearchStatusResponse {
    pub backtest_config: Option<serde_json::Value>,
    pub candidate_id: Option<String>,
    pub current_candidate: f64,
    pub error: Option<String>,
    pub generation: Option<i64>,
    pub logs: Option<Vec<String>>,
    pub phase: Option<String>,
    pub run_id: String,
    pub search_config: Option<serde_json::Value>,
    pub status: String,
    pub strategy: Option<String>,
    pub total_candidates: i64,
    pub total_generations: Option<i64>,
    pub total_windows: Option<i64>,
    pub window_index: Option<i64>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StudyConfig {
    #[serde(default = "default_study_config_continue_on_trial_error")]
    pub continue_on_trial_error: Option<bool>,
    pub direction: Option<String>,
    pub max_workers: Option<i64>,
    #[serde(default = "default_study_config_n_trials")]
    pub n_trials: Option<i64>,
    pub name: String,
    #[serde(default = "default_study_config_pruner")]
    pub pruner: Option<String>,
    pub sampler: Option<String>,
    #[serde(default = "default_study_config_seed")]
    pub seed: Option<i64>,
    pub storage: Option<StorageConfig>,
}

fn default_study_config_continue_on_trial_error() -> Option<bool> {
    Some(false)
}

fn default_study_config_n_trials() -> Option<i64> {
    Some(50)
}

fn default_study_config_pruner() -> Option<String> {
    Some("none".to_owned())
}

fn default_study_config_seed() -> Option<i64> {
    Some(42)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SystemHealthResponse {
    pub active_provider: String,
    pub backendVersion: String,
    pub dataLakeStatus: String,
    pub lastSyncAt: String,
    pub market_data_inventory_count: i64,
    pub market_data_root: String,
    pub mt5_available: bool,
    pub status: String,
    pub storageStatus: StorageStatusResponse,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Tick {
    pub ask: f64,
    pub bid: f64,
    #[serde(default = "default_tick_flags")]
    pub flags: Option<i64>,
    #[serde(default = "default_tick_last")]
    pub last: Option<f64>,
    pub time: String,
    #[serde(default = "default_tick_time_msc")]
    pub time_msc: Option<i64>,
    #[serde(default = "default_tick_volume")]
    pub volume: Option<f64>,
}

fn default_tick_flags() -> Option<i64> {
    Some(0)
}

fn default_tick_last() -> Option<f64> {
    Some(0.0)
}

fn default_tick_time_msc() -> Option<i64> {
    Some(0)
}

fn default_tick_volume() -> Option<f64> {
    Some(0.0)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TradeHistoryPending {
    pub status: String,
    pub status_token: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TradeSnapshotResponse {
    pub coverage: TradeSourceStatus,
    pub exchange_timezone: String,
    pub expires_at: String,
    pub first_page_url: String,
    pub frozen_watermark: serde_json::Value,
    pub invalid_trade_count: i64,
    pub provider_id: String,
    pub session_from: serde_json::Value,
    pub session_key: String,
    pub session_to: serde_json::Value,
    pub snapshot_id: String,
    pub source_generation: String,
    pub symbol: String,
    pub trade_count: i64,
    pub volume_field: String,
    pub volume_unit: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TradeSourceStatus {
    pub classification_coverage: String,
    pub coverage_reason: serde_json::Value,
    pub coverage_state: String,
    pub covered_from: serde_json::Value,
    pub covered_to: serde_json::Value,
    pub last_trade_watermark: serde_json::Value,
    pub provider_id: String,
    pub source_generation: String,
    pub symbol: String,
    pub volume_field: String,
    pub volume_unit: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TransactionCostConfig {
    #[serde(default = "default_transaction_cost_config_cost_bps")]
    pub cost_bps: Option<f64>,
    #[serde(default = "default_transaction_cost_config_cost_per_contract")]
    pub cost_per_contract: Option<f64>,
}

fn default_transaction_cost_config_cost_bps() -> Option<f64> {
    Some(0.0)
}

fn default_transaction_cost_config_cost_per_contract() -> Option<f64> {
    Some(0.0)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ValidateStrategySpecRequest {
    pub strategy_spec: serde_json::Value,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ValidationError {
    pub ctx: Option<serde_json::Value>,
    pub input: Option<serde_json::Value>,
    pub loc: Vec<serde_json::Value>,
    pub msg: String,
    #[serde(rename = "type")]
    pub r#type: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ValidationErrorDetail {
    pub code: String,
    pub message: String,
    pub path: String,
    pub suggestions: Option<Vec<String>>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ValidationResult {
    pub errors: Option<Vec<ValidationErrorDetail>>,
    pub valid: bool,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WalkForwardConfig {
    pub max_workers: Option<i64>,
    #[serde(default = "default_walk_forward_config_min_windows")]
    pub min_windows: Option<i64>,
    #[serde(default = "default_walk_forward_config_mode")]
    pub mode: Option<String>,
    pub test_days: i64,
    pub train_days: i64,
}

fn default_walk_forward_config_min_windows() -> Option<i64> {
    Some(2)
}

fn default_walk_forward_config_mode() -> Option<String> {
    Some("rolling".to_owned())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WalkForwardRequest {
    pub optimization: OptimizationConfig,
    pub walkforward: WalkForwardConfig,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WalkForwardResultsResponse {
    pub efficiency: Option<f64>,
    pub equity_curve: Vec<EquityArtifactPoint>,
    pub lake_paths: Option<serde_json::Value>,
    pub oos_metrics: serde_json::Value,
    pub optimization_config: Option<serde_json::Value>,
    pub run_id: String,
    pub status: String,
    pub walkforward_config: Option<serde_json::Value>,
    pub windows: Vec<WalkForwardWindowResultResponse>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WalkForwardRunListItem {
    pub created_at: String,
    pub efficiency: Option<f64>,
    pub name: String,
    pub run_id: String,
    pub status: String,
    pub strategy: Option<String>,
    pub symbol: Option<String>,
    #[serde(default = "default_walk_forward_run_list_item_window_count")]
    pub window_count: Option<i64>,
}

fn default_walk_forward_run_list_item_window_count() -> Option<i64> {
    Some(0)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WalkForwardRunListResponse {
    pub items: Vec<WalkForwardRunListItem>,
    pub limit: i64,
    pub offset: i64,
    pub total: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WalkForwardStartResponse {
    pub run_id: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WalkForwardStatusResponse {
    pub backtest_config: Option<serde_json::Value>,
    pub current_window: i64,
    pub error: Option<String>,
    pub optimization_config: Option<serde_json::Value>,
    pub phase: Option<String>,
    pub run_id: String,
    pub status: String,
    pub total_windows: i64,
    pub walkforward_config: Option<serde_json::Value>,
    pub windows_completed: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WalkForwardWindowResultResponse {
    pub best_params: Option<serde_json::Value>,
    pub index: i64,
    pub is_metrics: Option<serde_json::Value>,
    pub oos_metrics: Option<serde_json::Value>,
    pub status: String,
    pub test_end: String,
    pub test_start: String,
    pub train_end: String,
    pub train_start: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WorkerLeaseResponse {
    pub acquired_at: String,
    pub expires_at: String,
    pub heartbeat_at: String,
    pub is_active: bool,
    pub worker_id: String,
}
