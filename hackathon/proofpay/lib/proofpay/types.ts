export type Mode = "rehearsal" | "sandbox";
export type Status = "PROPOSED" | "BUDGET_BLOCKED" | "APPROVED" | "CREATE_DISPATCHED" | "CREATE_UNKNOWN" | "ORDER_READY" | "CAPTURE_DISPATCHED" | "UNKNOWN" | "REVIEW" | "CONFIRMED";
export const RESERVED_STATUSES = ["APPROVED", "CREATE_DISPATCHED", "CREATE_UNKNOWN", "ORDER_READY", "CAPTURE_DISPATCHED", "UNKNOWN", "REVIEW"] as const;
export const HELD_SQL = "'APPROVED','CREATE_DISPATCHED','CREATE_UNKNOWN','ORDER_READY','CAPTURE_DISPATCHED','UNKNOWN','REVIEW','CONFIRMED'";
export type SqlResult<T = Record<string, unknown>> = { results?: T[]; meta?: { changes?: number }; success?: boolean };
export interface SqlStatement { bind(...values: unknown[]): SqlStatement; first<T = Record<string, unknown>>(column?: string): Promise<T | null>; all<T = Record<string, unknown>>(): Promise<SqlResult<T>>; run(): Promise<SqlResult> }
export interface SqlDatabase { prepare(sql: string): SqlStatement; batch(statements: SqlStatement[]): Promise<SqlResult[]> }
export type Configuration = { PAYPAL_CLIENT_ID?: string; PAYPAL_CLIENT_SECRET?: string; PAYPAL_MERCHANT_ID?: string; AI_API_KEY?: string; AI_BASE_URL?: string; AI_MODEL?: string };
export type WorkspaceRow = { id: string; owner_id: string; mode: Mode; currency: string; budget_cents: number; created_at: number };
export type OperationRow = { id: string; workspace_id: string; idempotency_key: string; request: string; agent_label: string; sku: string; title: string; amount_cents: number; currency: string; merchant_id: string; mode: Mode; ai_source: string; rationale: string; status: Status; approval_version: number; approval_expires_at: number | null; approval_digest: string | null; create_request_id: string; capture_request_id: string; order_id: string | null; capture_id: string | null; approval_url: string | null; created_at: number; updated_at: number };
export type ProviderAmount = { currency_code?: string; value?: string };
export type ProviderCapture = { id?: string; status?: string; amount?: ProviderAmount; final_capture?: boolean };
export type ProviderOrder = { id?: string; status?: string; purchase_units?: Array<{reference_id?: string; custom_id?: string; payee?: {merchant_id?: string}; amount?: ProviderAmount; payments?: {captures?: ProviderCapture[]; refunds?: unknown[]}}>; links?: Array<{href?: string; rel?: string}> };
export interface PaymentProvider { create(op: OperationRow, returnOrigin: string): Promise<ProviderOrder>; capture(op: OperationRow): Promise<ProviderOrder>; get(op: OperationRow): Promise<ProviderOrder> }
export type ProposalProvenance = {providerResponseId?: string; returnedModel?: string; requestedModel: string; providerOrigin: string; receivedAt: number};
export type ProposalChoice = { sku: string; rationale: string; source: "model" | "rehearsal-rule" | "rehearsal-seed"; provenance?: ProposalProvenance };
export type VerificationRecord = {
  schemaVersion: 1; mode: Mode; simulated: boolean;
  source: "simulated-provider-lookup" | "paypal-sandbox-orders-get";
  checkedAt: number; operationId: string;
  order: {id: string; status: string; referenceId: string; customId: string; payeeMerchantId: string; amount: {value: string; currency: string}};
  capture: {id: string; status: string; finalCapture: boolean; amount: {value: string; currency: string}};
};
export class ProofPayError extends Error { constructor(public code: string, message: string, public status = 400) { super(message); this.name = "ProofPayError"; } }
