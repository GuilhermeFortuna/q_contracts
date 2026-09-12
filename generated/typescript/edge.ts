// GENERATED FILE - DO NOT EDIT. Source schemas: schema/edge/common/error.schema.json, schema/edge/common/health.schema.json, schema/edge/execution/check-request.schema.json, schema/edge/execution/check-response.schema.json, schema/edge/execution/deal.schema.json, schema/edge/execution/deals-request.schema.json, schema/edge/execution/deals-response.schema.json, schema/edge/execution/lookup-outcome.schema.json, schema/edge/execution/lookup-request.schema.json, schema/edge/execution/order.schema.json, schema/edge/execution/position.schema.json, schema/edge/execution/positions-request.schema.json, schema/edge/execution/positions-response.schema.json, schema/edge/execution/quote-request.schema.json, schema/edge/execution/quote-response.schema.json, schema/edge/execution/submit-outcome.schema.json, schema/edge/execution/submit-request.schema.json

export interface CheckRequest {
  intent_id: string
  order: ExecutionOrder
}

export interface CheckResponse {
  allowed: boolean
  margin: number
  reason?: string
  retcode: number
}

export interface DealsRequest {
  magic?: number
  symbol?: string
  window_end: string | number
  window_start: string | number
}

export type DealsResponse = Array<ExecutionDeal>

export interface EdgeErrorResponse {
  code: "invalid_timeframe" | "symbol_not_found" | "range_unavailable" | "tick_range_too_large" | "invalid_flags" | "mt5_unavailable" | "unauthorized" | "not_found" | "internal_error" | "duplicate_intent" | "schema_major_mismatch"
  error: string
}

export interface EdgeHealthResponse {
  mt5_connected: boolean
  schema_version: string
  status: string
  terminal_build: number | null
}

export interface ExecutionDeal {
  comment?: string
  commission?: number
  entry?: number
  fee?: number
  magic?: number
  order_ticket: number
  price: number
  profit?: number
  swap?: number
  symbol: string
  ticket: number
  time_msc?: number
  type?: number
  volume: number
}

export interface ExecutionOrder {
  comment?: string
  deviation?: number
  magic?: number
  price?: number
  side?: "buy" | "sell"
  sl?: number
  symbol: string
  tp?: number
  type?: number
  type_filling?: number
  type_time?: number
  volume: number
}

export interface ExecutionPosition {
  comment?: string
  magic?: number
  price_current?: number
  price_open: number
  profit?: number
  sl?: number
  symbol: string
  ticket: number
  time?: number
  tp?: number
  type: number
  volume: number
}

export type LookupOutcome = { closes_intent: true; deals: Array<ExecutionDeal>; outcome: "filled" } | { closes_intent: true; outcome: "rejected"; reason?: string; retcode: number } | { closes_intent: true; outcome: "not_found" } | { closes_intent: false; outcome: "unavailable"; reason: string }

export interface LookupRequest {
  intent_id: string
  magic?: number
  window_end: string | number
  window_start: string | number
}

export interface PositionsRequest {
  symbol?: string
}

export type PositionsResponse = Array<ExecutionPosition>

export interface QuoteRequest {
  symbol: string
}

export interface QuoteResponse {
  age_ms: number
  ask: number
  bid: number
  last: number
  symbol: string
  time_msc: number
}

export type SubmitOutcome = { order_ticket: number; outcome: "accepted"; retcode: number } | { outcome: "rejected"; reason: string; retcode: number } | { outcome: "indeterminate"; reason: string }

export interface SubmitRequest {
  intent_id: string
  order: ExecutionOrder
}
