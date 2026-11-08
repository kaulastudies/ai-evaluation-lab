import { amountString, parseAmount } from "./catalogue";
import { Configuration, OperationRow, PaymentProvider, ProofPayError, ProviderOrder, SqlDatabase } from "./types";
import { readTextLimited } from "./request";

export function sandboxReady(config: Configuration): boolean { return Boolean(config.PAYPAL_CLIENT_ID && config.PAYPAL_CLIENT_SECRET && config.PAYPAL_MERCHANT_ID); }

/** Verify business identity separately from transport success or the redirect. */
export function verifyOrder(op: OperationRow, order: ProviderOrder, requireKnownId = true): void {
  if (!order.id || (requireKnownId && order.id !== op.order_id)) throw new ProofPayError("PROVIDER_MISMATCH", "The provider returned a different order.", 409);
  if (!Array.isArray(order.purchase_units) || order.purchase_units.length !== 1) throw new ProofPayError("PROVIDER_MISMATCH", "Expected exactly one purchase unit.", 409);
  const unit = order.purchase_units[0];
  if (unit.reference_id !== op.id || unit.custom_id !== op.id || unit.payee?.merchant_id !== op.merchant_id || unit.amount?.currency_code !== op.currency || parseAmount(unit.amount?.value) !== op.amount_cents) throw new ProofPayError("PROVIDER_MISMATCH", "The provider's merchant, amount, currency or operation identity did not match the approval.", 409);
}

export function completedCapture(op: OperationRow, order: ProviderOrder): string | null {
  verifyOrder(op, order);
  const unit = order.purchase_units![0];
  if (unit.payments?.refunds?.length) throw new ProofPayError("PROVIDER_REVIEW", "Refund activity requires review; the original payment history is retained.", 409);
  const captures = unit.payments?.captures ?? [];
  if (captures.length > 1) throw new ProofPayError("PROVIDER_REVIEW", "Unexpected multiple captures require review.", 409);
  if (!captures.length) return null;
  const capture = captures[0];
  if (!capture.id || capture.amount?.currency_code !== op.currency || parseAmount(capture.amount?.value) !== op.amount_cents) throw new ProofPayError("PROVIDER_MISMATCH", "Capture evidence does not match the approved amount and currency.", 409);
  if (capture.status === "PENDING") return null;
  if (capture.status !== "COMPLETED") throw new ProofPayError("PROVIDER_REVIEW", `Capture status ${capture.status ?? "missing"} requires review.`, 409);
  if (order.status !== "COMPLETED" || capture.final_capture !== true) throw new ProofPayError("PROVIDER_REVIEW", "Only a completed order with a final full capture is supported.", 409);
  if (op.capture_id && op.capture_id !== capture.id) throw new ProofPayError("PROVIDER_MISMATCH", "The provider returned a different capture.", 409);
  return capture.id;
}

export function approvalLink(order: ProviderOrder): string | null {
  const href = order.links?.find(link => link.rel === "payer-action" || link.rel === "approve")?.href;
  if (!href) return null;
  try { const url = new URL(href); if (url.protocol === "https:" && ["www.sandbox.paypal.com", "sandbox.paypal.com"].includes(url.hostname) && !url.username && !url.password) return url.toString(); } catch { /* Reject malformed or foreign links. */ }
  throw new ProofPayError("PROVIDER_LINK", "The provider approval link was not a PayPal sandbox URL.", 502);
}

export class PayPalSandboxProvider implements PaymentProvider {
  private token: string | null = null;
  constructor(private config: Configuration) { if (!sandboxReady(config)) throw new ProofPayError("PAYPAL_NOT_CONFIGURED", "PayPal sandbox credentials are missing. Sandbox execution is disabled.", 503); }
  private async accessToken(): Promise<string> {
    if (this.token) return this.token;
    const response = await fetch("https://api-m.sandbox.paypal.com/v1/oauth2/token", {method: "POST", redirect: "manual", headers: {Authorization: `Basic ${btoa(`${this.config.PAYPAL_CLIENT_ID}:${this.config.PAYPAL_CLIENT_SECRET}`)}`, "Content-Type": "application/x-www-form-urlencoded"}, body: "grant_type=client_credentials", signal: AbortSignal.timeout(20000)});
    if (!response.ok) throw new ProofPayError("PAYPAL_AUTH", "PayPal sandbox authentication failed.", 502);
    const json = JSON.parse(await readTextLimited(response, 16384)) as {access_token?: string};
    if (typeof json.access_token !== "string" || !json.access_token || json.access_token.length > 8192 || /[\x00-\x20\x7f]/.test(json.access_token)) throw new ProofPayError("PAYPAL_AUTH", "PayPal sandbox did not return a valid access token.", 502);
    this.token = json.access_token; return this.token;
  }
  private async call(path: string, method: "GET" | "POST", body?: unknown, key?: string): Promise<ProviderOrder> {
    const token = await this.accessToken();
    const response = await fetch(`https://api-m.sandbox.paypal.com${path}`, {method, redirect: "manual", headers: {Authorization: `Bearer ${token}`, "Content-Type": "application/json", Prefer: "return=representation", ...(key ? {"PayPal-Request-Id": key} : {})}, ...(method === "POST" ? {body: JSON.stringify(body ?? {})} : {}), signal: AbortSignal.timeout(25000)});
    if (!response.ok) throw new ProofPayError("PAYPAL_UNCERTAIN", "PayPal sandbox did not return a successful response. Any dispatched payment stays reserved until verified.", 502);
    return JSON.parse(await readTextLimited(response, 262144)) as ProviderOrder;
  }
  async create(op: OperationRow, origin: string): Promise<ProviderOrder> {
    if (op.merchant_id !== this.config.PAYPAL_MERCHANT_ID) throw new ProofPayError("MERCHANT_CHANGED", "The configured seller no longer matches this proposal.", 409);
    return this.call("/v2/checkout/orders", "POST", {intent: "CAPTURE", payment_source: {paypal: {experience_context: {user_action: "PAY_NOW", shipping_preference: "NO_SHIPPING", return_url: `${origin}/?paypal_return=${encodeURIComponent(op.id)}`, cancel_url: `${origin}/?paypal_cancel=${encodeURIComponent(op.id)}`}}}, purchase_units: [{reference_id: op.id, custom_id: op.id, payee: {merchant_id: op.merchant_id}, amount: {currency_code: op.currency, value: amountString(op.amount_cents)}}]}, op.create_request_id);
  }
  async capture(op: OperationRow): Promise<ProviderOrder> { return this.call(`/v2/checkout/orders/${encodeURIComponent(op.order_id!)}/capture`, "POST", {}, op.capture_request_id); }
  async get(op: OperationRow): Promise<ProviderOrder> { return this.call(`/v2/checkout/orders/${encodeURIComponent(op.order_id!)}`, "GET"); }
}

/** Durable, explicitly simulated provider. It never contacts PayPal. */
export class RehearsalProvider implements PaymentProvider {
  constructor(private db: SqlDatabase, private now: () => number) {}
  async create(op: OperationRow): Promise<ProviderOrder> {
    const payload: ProviderOrder = {id: `REH-${crypto.randomUUID()}`, status: "APPROVED", purchase_units: [{reference_id: op.id, custom_id: op.id, payee: {merchant_id: op.merchant_id}, amount: {currency_code: op.currency, value: amountString(op.amount_cents)}}]};
    await this.db.prepare("INSERT INTO proofpay_rehearsal_orders (id, operation_id, payload, capture_calls, created_at) VALUES (?, ?, ?, 0, ?) ON CONFLICT(operation_id) DO NOTHING").bind(payload.id, op.id, JSON.stringify(payload), this.now()).run();
    const row = await this.db.prepare("SELECT payload FROM proofpay_rehearsal_orders WHERE operation_id = ?").bind(op.id).first<{payload: string}>();
    return JSON.parse(row!.payload);
  }
  async capture(op: OperationRow): Promise<ProviderOrder> {
    const current = await this.get(op);
    current.status = "COMPLETED";
    current.purchase_units![0].payments = {captures: [{id: `REH-CAP-${crypto.randomUUID()}`, status: "COMPLETED", amount: {currency_code: op.currency, value: amountString(op.amount_cents)}, final_capture: true}]};
    await this.db.prepare("UPDATE proofpay_rehearsal_orders SET payload = ?, capture_calls = capture_calls + 1 WHERE id = ? AND capture_calls = 0").bind(JSON.stringify(current), op.order_id).run();
    return this.get(op);
  }
  async get(op: OperationRow): Promise<ProviderOrder> {
    const row = await this.db.prepare("SELECT payload FROM proofpay_rehearsal_orders WHERE id = ? AND operation_id = ?").bind(op.order_id, op.id).first<{payload: string}>();
    if (!row) throw new ProofPayError("REHEARSAL_ORDER_MISSING", "The simulated provider has no matching order.", 404);
    return JSON.parse(row.payload);
  }
}
