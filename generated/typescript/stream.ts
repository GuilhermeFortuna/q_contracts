// GENERATED FILE - DO NOT EDIT. Source schemas: schema/stream/control/cursor-expired.schema.json, schema/stream/control/epoch-changed.schema.json, schema/stream/control/lagging.schema.json, schema/stream/control/rejected.schema.json, schema/stream/control/subscribe.schema.json, schema/stream/control/subscribed.schema.json, schema/stream/envelope.schema.json, schema/stream/payloads/execution-common.schema.json, schema/stream/payloads/execution-decision.schema.json, schema/stream/payloads/execution-deployment.schema.json, schema/stream/payloads/execution-fill.schema.json, schema/stream/payloads/execution-ledger.schema.json, schema/stream/payloads/execution-order.schema.json, schema/stream/payloads/execution-risk.schema.json, schema/stream/payloads/job-progress.schema.json, schema/stream/payloads/job-terminal.schema.json, schema/stream/replay/execution-snapshot.schema.json, schema/stream/replay/history-expired.schema.json, schema/stream/replay/history-page.schema.json, schema/stream/replay/latest.schema.json, schema/stream/replay/watermark.schema.json

export type BrokerMode = "paper" | "mt5_live"

export interface CursorExpiredFrame {
  cursor?: string
  topic: string
  type: "cursor_expired"
}

export type Decimal = string

export type DecisionOutcome = "hold" | "signal" | "risk_rejected" | "order_intent" | "order_filled" | "order_rejected" | "order_unknown" | "error"

export type DeploymentLifecycle = "draft" | "running" | "paused" | "stopped" | "error"

export interface EpochChangedFrame {
  new_epoch: string
  previous_epoch?: string
  topic: string
  type: "epoch_changed"
}

export interface ExecutionAccount {
  cash_balance: Decimal
  created_at?: string
  currency: string
  id: UUID
  initial_balance: Decimal
  name: string
  realized_pnl: Decimal
  risk_config?: Record<string, unknown>
  sizing_config?: Record<string, unknown>
  updated_at: string
}

export interface ExecutionCommon {
}

export interface ExecutionControl {
  kill_switch_enabled: boolean
  kill_switch_reason?: string | null
  updated_at: string
  updated_by?: string | null
}

export interface ExecutionDecisionState {
  account_id: UUID
  bar_close_time: string
  compiled_config?: Record<string, unknown>
  config_hash: string
  context?: Record<string, unknown>
  created_at?: string
  deployment_id: UUID
  entity: "decision"
  id: UUID
  outcome: DecisionOutcome
  reason?: string | null
  requested_quantity?: Decimal | null
  risk_config?: Record<string, unknown>
  signal_action: SignalAction
  sizing_config?: Record<string, unknown>
  strategy_name: string
  strategy_version: number
  symbol: string
  timeframe: string
  updated_at: string
}

export interface ExecutionDeploymentState {
  account_id: UUID
  broker_mode: BrokerMode
  compiled_config?: Record<string, unknown>
  config_hash: string
  created_at?: string
  deployment_id: UUID
  entity: "deployment"
  id: UUID
  last_bar_close_time?: string | null
  lifecycle: DeploymentLifecycle
  live_activation_enabled: boolean
  name: string
  paper_account_id?: UUID
  pending_action?: string | null
  pending_action_requested_at?: string | null
  risk_config?: Record<string, unknown>
  sizing_config?: Record<string, unknown>
  started_at?: string | null
  stopped_at?: string | null
  strategy_name: string
  strategy_version: number
  symbol: string
  timeframe: string
  updated_at: string
}

export interface ExecutionFillEvent {
  account_id: UUID
  broker_mode: BrokerMode
  created_at?: string
  deployment_id: UUID
  details?: Record<string, unknown>
  entity: "fill"
  external_fill_id: string
  fee: Decimal
  filled_at: string
  id: UUID
  order_id: UUID
  position_after: ExecutionPosition
  price: Decimal
  quantity: Decimal
  quote_ask?: Decimal | null
  quote_bid?: Decimal | null
  quote_timestamp?: string | null
  side: ExecutionSide
  slippage: Decimal
  updated_at: string
}

export interface ExecutionLedgerEvent {
  account_after: ExecutionAccount
  account_id: UUID
  amount: Decimal
  balance_after: Decimal
  created_at?: string
  deployment_id?: UUID | null
  description?: string | null
  entity: "ledger_entry"
  entry_type: LedgerEntryType
  fill_id?: UUID | null
  id: UUID
  paper_account_id?: UUID
  updated_at: string
}

export interface ExecutionOrderState {
  account_id: UUID
  broker_mode: BrokerMode
  completed_at?: string | null
  created_at?: string
  decision_id?: UUID | null
  deployment_id: UUID
  details?: Record<string, unknown>
  entity: "order"
  external_order_id?: string | null
  id: UUID
  intent_committed_at?: string | null
  intent_id: UUID
  order_type: ExecutionOrderType
  quantity: Decimal
  reconciled_at?: string | null
  reconciled_by?: string | null
  reconciliation_attempted_at?: string | null
  reconciliation_detail?: string | null
  reconciliation_error?: string | null
  reconciliation_state: ReconciliationState
  rejection_reason?: string | null
  side: ExecutionSide
  status: ExecutionOrderStatus
  submitted_at?: string | null
  updated_at: string
}

export type ExecutionOrderStatus = "intent" | "submitted" | "filled" | "rejected" | "unknown" | "cancelled"

export type ExecutionOrderType = "market"

export interface ExecutionPosition {
  average_entry_price?: Decimal | null
  closed_at?: string | null
  deployment_id: UUID
  id: UUID
  is_open: boolean
  opened_at?: string | null
  quantity: Decimal
  side: PositionSide
  updated_at: string
}

export type ExecutionRiskEvent = { account_id: UUID; context?: Record<string, unknown>; created_at?: string; decision_id?: UUID | null; deployment_id: UUID; entity: "risk" | "risk_rejection"; id: UUID; kind: "risk_rejection"; message: string; order_id?: UUID | null; rejection_code: RiskRejectionCode; updated_at: string } | { account_id?: string | null; actor?: string | null; created_at?: string; deployment_id: null; enabled?: boolean; entity: "risk" | "kill_switch"; id: UUID; kill_switch_enabled: boolean; kill_switch_reason?: string | null; kind: "kill_switch"; reason?: string | null; updated_at: string; updated_by?: string | null }

export type ExecutionSide = "buy" | "sell"

export interface ExecutionSnapshot {
  accounts: Array<ExecutionAccount>
  control: ExecutionControl
  deployments: Array<ExecutionDeploymentState>
  limits: { recent_decisions: number; recent_fills: number; recent_orders: number; recent_risk: number }
  orders: Array<ExecutionOrderState>
  positions: Array<ExecutionPosition>
  recent: { decisions: Array<ExecutionDecisionState>; fills: Array<ExecutionFillEvent>; risk: Array<ExecutionRiskEvent> }
  watermark: { decisions: { epoch: string; seq: number }; deployments: { epoch: string; seq: number }; fills: { epoch: string; seq: number }; ledger: { epoch: string; seq: number }; orders: { epoch: string; seq: number }; risk: { epoch: string; seq: number } }
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

export type LedgerEntryType = "initial_balance" | "fill_cash" | "realized_pnl" | "fee" | "adjustment"

export type PositionSide = "long" | "short" | "flat"

export type ReconciliationState = "not_applicable" | "pending" | "reconciled" | "ambiguous"

export interface RejectedFrame {
  detail?: string
  reason: "unknown_topic" | "unsupported_schema_major" | "stream_unavailable" | "invalid_frame"
  topic?: string
  type: "rejected"
}

export type RiskRejectionCode = "kill_switch" | "lifecycle" | "lease_lost" | "stale_bar" | "stale_quote" | "symbol_unavailable" | "invalid_quantity" | "notional_limit" | "one_position_violation" | "insufficient_equity" | "daily_loss_limit" | "database_unavailable" | "broker_unavailable" | "unknown_prior_order"

export type SignalAction = "buy" | "sell" | "hold" | "close"

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

export type UUID = string
