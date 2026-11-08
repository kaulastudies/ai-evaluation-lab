import { CATALOGUE } from "./catalogue";
import { propose as defaultPropose } from "./ai";
import { aiFundingReady, requireAiFunding } from "./ai-funding";
import { approvalLink, completedCapture, PayPalSandboxProvider, RehearsalProvider, sandboxReady, verifyOrder } from "./provider";
import { Configuration, HELD_SQL, Mode, OperationRow, PaymentProvider, ProposalChoice, ProposalProvenance, ProofPayError, RESERVED_STATUSES, SqlDatabase, VerificationRecord, WorkspaceRow } from "./types";

type ServiceOptions = { db: SqlDatabase; env: Configuration; provider?: PaymentProvider; ai?: (request: string, mode: Mode, env: Configuration) => Promise<ProposalChoice>; now?: () => number };
const APPROVAL_TTL = 15 * 60 * 1000;
function ownerRequired(owner: string): void { if (!owner) throw new ProofPayError("AUTH_REQUIRED", "Sign in to use your private purchase desk.", 401); }
function modeRequired(mode: unknown): asserts mode is Mode { if (mode !== "rehearsal" && mode !== "sandbox") throw new ProofPayError("INVALID_MODE", "Choose rehearsal or sandbox."); }
function safeProvenance(value: ProposalProvenance | undefined): ProposalProvenance | undefined {
  if (!value || typeof value.requestedModel !== "string" || !/^[A-Za-z0-9._:/-]{1,200}$/.test(value.requestedModel) || typeof value.providerOrigin !== "string" || value.providerOrigin.length > 512 || !Number.isSafeInteger(value.receivedAt) || value.receivedAt <= 0) return undefined;
  let origin: URL;
  try { origin = new URL(value.providerOrigin); } catch { return undefined; }
  if (origin.protocol !== "https:" || origin.username || origin.password || origin.origin.length > 256) return undefined;
  const boundedIdentifier = (candidate: unknown) => typeof candidate === "string" && /^[A-Za-z0-9._:/-]{1,200}$/.test(candidate) ? candidate : undefined;
  return {requestedModel: value.requestedModel, providerOrigin: origin.origin, receivedAt: value.receivedAt, ...(boundedIdentifier(value.providerResponseId) ? {providerResponseId: boundedIdentifier(value.providerResponseId)} : {}), ...(boundedIdentifier(value.returnedModel) ? {returnedModel: boundedIdentifier(value.returnedModel)} : {})};
}
const APPROVAL_BINDING_FIELDS = ["operationId", "workspaceId", "sku", "title", "amountCents", "currency", "merchantId", "mode", "approvalVersion", "approvalExpiresAt"] as const;
function approvalBindingValues(op: OperationRow) { return [op.id, op.workspace_id, op.sku, op.title, op.amount_cents, op.currency, op.merchant_id, op.mode, op.approval_version, op.approval_expires_at]; }
async function digest(op: OperationRow): Promise<string> {
  const data = JSON.stringify(approvalBindingValues(op));
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(data));
  return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, "0")).join("");
}
function expose(op: OperationRow) {
  return {id: op.id, request: op.request, agentLabel: op.agent_label, sku: op.sku, title: op.title, amountCents: op.amount_cents, currency: op.currency, merchantId: op.merchant_id, status: op.status, approvalVersion: op.approval_version, approvalExpiresAt: op.approval_expires_at, orderId: op.order_id, captureId: op.capture_id, approvalUrl: op.approval_url, providerMode: op.mode, aiSource: op.ai_source, rationale: op.rationale, createdAt: op.created_at, updatedAt: op.updated_at};
}

export class ProofPayService {
  readonly db: SqlDatabase;
  private env: Configuration;
  private now: () => number;
  private injectedProvider?: PaymentProvider;
  private proposer: NonNullable<ServiceOptions["ai"]>;
  constructor(options: ServiceOptions) { this.db = options.db; this.env = options.env; this.now = options.now ?? Date.now; this.injectedProvider = options.provider; this.proposer = options.ai ?? defaultPropose; }
  capabilities() { return {sandboxReady: sandboxReady(this.env), aiReady: aiFundingReady(this.env)}; }
  private provider(op: OperationRow): PaymentProvider { if (this.injectedProvider) return this.injectedProvider; return op.mode === "rehearsal" ? new RehearsalProvider(this.db, this.now) : new PayPalSandboxProvider(this.env); }
  private async workspace(owner: string): Promise<WorkspaceRow | null> { ownerRequired(owner); return this.db.prepare("SELECT w.*, CASE WHEN EXISTS (SELECT 1 FROM proofpay_events e WHERE e.workspace_id = w.id AND e.type = 'SANDBOX_DIAGNOSTIC_STARTED') THEN 'sandbox-diagnostic' ELSE 'standard' END AS profile FROM proofpay_workspaces w JOIN proofpay_sessions s ON w.id = s.workspace_id WHERE s.owner_id = ? AND w.owner_id = ?").bind(owner, owner).first<WorkspaceRow>(); }
  private async operation(owner: string, id: string): Promise<OperationRow> {
    ownerRequired(owner);
    const op = await this.db.prepare("SELECT o.* FROM proofpay_operations o JOIN proofpay_workspaces w ON o.workspace_id = w.id WHERE o.id = ? AND w.owner_id = ?").bind(id, owner).first<OperationRow>();
    if (!op) throw new ProofPayError("NOT_FOUND", "The operation was not found in your workspace.", 404);
    return op;
  }
  private async event(workspaceId: string, operationId: string | null, type: string, detail: string): Promise<void> { await this.db.prepare("INSERT INTO proofpay_events (id,workspace_id,operation_id,type,detail,created_at) VALUES (?,?,?,?,?,?)").bind(crypto.randomUUID(), workspaceId, operationId, type, detail, this.now()).run(); }
  async state(owner: string) {
    const workspace = await this.workspace(owner);
    if (!workspace) return {workspace: null, capabilities: this.capabilities(), catalogue: CATALOGUE, operations: [], events: []};
    const operations = (await this.db.prepare("SELECT * FROM proofpay_operations WHERE workspace_id = ? ORDER BY created_at,id").bind(workspace.id).all<OperationRow>()).results ?? [];
    const events = (await this.db.prepare("SELECT id,operation_id AS operationId,type,detail,created_at AS createdAt FROM proofpay_events WHERE workspace_id = ? ORDER BY created_at DESC,rowid DESC LIMIT 100").bind(workspace.id).all()).results ?? [];
    const reservedCents = operations.filter(op => (RESERVED_STATUSES as readonly string[]).includes(op.status)).reduce((sum, op) => sum + op.amount_cents, 0);
    const committedCents = operations.filter(op => op.status === "CONFIRMED").reduce((sum, op) => sum + op.amount_cents, 0);
    return {workspace: {id: workspace.id, mode: workspace.mode, profile: workspace.profile ?? "standard", currency: workspace.currency, budgetCents: workspace.budget_cents, reservedCents, committedCents, availableCents: workspace.budget_cents - reservedCents - committedCents, createdAt: workspace.created_at}, capabilities: this.capabilities(), catalogue: CATALOGUE, operations: operations.map(expose), events};
  }
  private insertStatement(workspace: WorkspaceRow, request: string, key: string, choice: ProposalChoice, label: string, operationId = crypto.randomUUID()) {
    const item = CATALOGUE.find(item => item.sku === choice.sku);
    if (!item) throw new ProofPayError("INVALID_SKU", "The proposal must select a server catalogue item.");
    return this.db.prepare("INSERT INTO proofpay_operations (id,workspace_id,idempotency_key,request,agent_label,sku,title,amount_cents,currency,merchant_id,mode,ai_source,rationale,status,approval_version,create_request_id,capture_request_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'PROPOSED',1,?,?,?,?) ON CONFLICT(workspace_id,idempotency_key) DO NOTHING").bind(operationId, workspace.id, key, request, label, item.sku, item.title, item.amountCents, item.currency, workspace.mode === "rehearsal" ? "rehearsal-seller" : this.env.PAYPAL_MERCHANT_ID, workspace.mode, choice.source, choice.rationale, crypto.randomUUID(), crypto.randomUUID(), this.now(), this.now());
  }
  async start(owner: string, mode: Mode, seed = false) {
    return this.startWorkspace(owner, mode, seed, false);
  }
  async startSandboxDiagnostic(owner: string) {
    return this.startWorkspace(owner, "sandbox", false, true);
  }
  private async startWorkspace(owner: string, mode: Mode, seed: boolean, diagnostic: boolean) {
    ownerRequired(owner); modeRequired(mode);
    const active = await this.workspace(owner);
    const pending = active?.mode === "sandbox" ? await this.db.prepare(`SELECT id FROM proofpay_operations WHERE workspace_id = ? AND status IN (${RESERVED_STATUSES.map(status => `'${status}'`).join(",")}) LIMIT 1`).bind(active.id).first() : null;
    if (pending) throw new ProofPayError("SANDBOX_WORKSPACE_HELD", "Resolve the active sandbox's reserved or uncertain operations before starting another workspace. Its evidence must stay visible.", 409);
    if (mode === "sandbox" && !sandboxReady(this.env)) throw new ProofPayError("PAYPAL_NOT_CONFIGURED", "Configure PayPal sandbox credentials before starting a sandbox workspace.", 503);
    if (seed && mode !== "rehearsal") throw new ProofPayError("SEED_MODE", "Seeded proposals are only available in rehearsal.");
    const workspace: WorkspaceRow = {id: crypto.randomUUID(), owner_id: owner, mode, currency: "USD", budget_cents: 30000, created_at: this.now()};
    const statements = [this.db.prepare("INSERT INTO proofpay_workspaces (id,owner_id,mode,currency,budget_cents,created_at) VALUES (?,?,?,?,?,?)").bind(workspace.id, owner, mode, "USD", 30000, workspace.created_at)];
    if (seed) {
      statements.push(this.insertStatement(workspace, "Find a workflow review for our team.", "seed-workflow", {sku: "workflow-review", rationale: "Seeded rehearsal proposal; no AI model was called.", source: "rehearsal-seed"}, "Workflow agent"));
      statements.push(this.insertStatement(workspace, "Find a design review for our team.", "seed-design", {sku: "design-review", rationale: "Seeded rehearsal proposal; no AI model was called.", source: "rehearsal-seed"}, "Design agent"));
    }
    if (diagnostic) {
      const operationId = crypto.randomUUID();
      const choice: ProposalChoice = {sku: "workflow-review", source: "sandbox-diagnostic", rationale: "Fixed server catalogue selection for a PayPal sandbox diagnostic. No AI model was called. Owner and PayPal buyer approvals are still required."};
      statements.push(this.insertStatement(workspace, "Test the PayPal sandbox payment path with the fixed workflow review catalogue item. No AI proposal is requested.", "sandbox-diagnostic-workflow-v1", choice, "Sandbox diagnostic", operationId));
      statements.push(this.db.prepare("INSERT INTO proofpay_events (id,workspace_id,operation_id,type,detail,created_at) VALUES (?,?,?,'PROPOSAL_CREATED',?,?)").bind(crypto.randomUUID(), workspace.id, operationId, JSON.stringify({schemaVersion: 1, source: choice.source, sku: choice.sku, rationale: choice.rationale, manual: true, aiCalled: false, diagnosticProfile: "paypal-sandbox-v1"}), this.now()));
      statements.push(this.db.prepare("INSERT INTO proofpay_events (id,workspace_id,operation_id,type,detail,created_at) VALUES (?,?,NULL,'SANDBOX_DIAGNOSTIC_STARTED',?,?)").bind(crypto.randomUUID(), workspace.id, "Explicit PayPal sandbox diagnostic with a fixed server catalogue proposal. No AI model was called and no provider request was dispatched by workspace creation. This does not establish an AI-to-payment journey.", this.now()));
    }
    const sessionIndex = statements.length;
    statements.push(this.db.prepare(`INSERT INTO proofpay_sessions (owner_id,workspace_id) VALUES (?,?) ON CONFLICT(owner_id) DO UPDATE SET workspace_id = excluded.workspace_id WHERE NOT EXISTS (SELECT 1 FROM proofpay_workspaces w JOIN proofpay_operations o ON o.workspace_id = w.id WHERE w.id = proofpay_sessions.workspace_id AND w.mode = 'sandbox' AND o.status IN (${RESERVED_STATUSES.map(status => `'${status}'`).join(",")}))`).bind(owner, workspace.id));
    statements.push(this.db.prepare("INSERT INTO proofpay_events (id,workspace_id,operation_id,type,detail,created_at) VALUES (?,?,NULL,'WORKSPACE_CREATED',?,?)").bind(crypto.randomUUID(), workspace.id, mode === "rehearsal" ? "Isolated $300 rehearsal. Simulated provider and deterministic proposals; no PayPal or model calls." : "Isolated $300 sandbox allowance. Buyer approval and verified provider evidence required.", this.now()));
    const results = await this.db.batch(statements);
    if (results[sessionIndex].meta?.changes !== 1) throw new ProofPayError("SANDBOX_WORKSPACE_HELD", "The active sandbox acquired a reservation. Resolve it before switching workspaces.", 409);
    return this.state(owner);
  }
  async propose(owner: string, input: {request: string; mode: Mode; idempotencyKey: string}) {
    modeRequired(input.mode);
    if (typeof input.request !== "string" || !input.request.trim() || input.request.length > 2000 || typeof input.idempotencyKey !== "string" || !/^[A-Za-z0-9_-]{8,128}$/.test(input.idempotencyKey)) throw new ProofPayError("INVALID_PROPOSAL", "Supply a purchase request and an idempotency key (8–128 letters, numbers, dashes or underscores).");
    const workspace = await this.workspace(owner);
    if (!workspace || workspace.mode !== input.mode) throw new ProofPayError("WORKSPACE_MODE", "Start a workspace in the requested mode first.", 409);
    if (workspace.profile === "sandbox-diagnostic") throw new ProofPayError("DIAGNOSTIC_FIXED_CATALOGUE", "This diagnostic uses one fixed catalogue proposal and never calls an AI model. Start a standard workspace for AI proposals.", 409);
    if (workspace.mode === "sandbox" && !sandboxReady(this.env)) throw new ProofPayError("PAYPAL_NOT_CONFIGURED", "PayPal sandbox is not configured.", 503);
    const prior = await this.db.prepare("SELECT * FROM proofpay_operations WHERE workspace_id = ? AND idempotency_key = ?").bind(workspace.id, input.idempotencyKey).first<OperationRow>();
    if (prior) { if (prior.request !== input.request.trim()) throw new ProofPayError("KEY_REUSED", "That idempotency key is already bound to another request.", 409); return this.state(owner); }
    const funding = input.mode === "sandbox" ? requireAiFunding(this.env) : undefined;
    let fundingAttemptId: string | undefined;
    if (funding) {
      fundingAttemptId = crypto.randomUUID();
      // A unique grant slot bounds aggregate calls across workspaces/processes;
      // the unique workspace constraint allows only one attempt per workspace.
      // A concurrent loser stops before inference, even when the grant has room.
      // Failures are never refunded: the remote outcome may already be billable.
      const claim = await this.db.batch([
        this.db.prepare("INSERT INTO proofpay_ai_attempts (id,workspace_id,grant_id,slot,idempotency_key,model,provider,created_at,grant_expires_at) SELECT ?,?,?,COALESCE(MAX(slot),0)+1,?,?,?,?,? FROM proofpay_ai_attempts WHERE grant_id = ? HAVING COALESCE(MAX(slot),0) < ? ON CONFLICT DO NOTHING RETURNING id").bind(fundingAttemptId, workspace.id, funding.grantId, input.idempotencyKey, funding.model, funding.provider, this.now(), funding.expiresAt, funding.grantId, funding.maxRequests),
        this.db.prepare("INSERT INTO proofpay_events (id,workspace_id,operation_id,type,detail,created_at) SELECT ?,?,NULL,'AI_FREE_ATTEMPT_CLAIMED',?,? WHERE EXISTS (SELECT 1 FROM proofpay_ai_attempts WHERE id = ?)").bind(crypto.randomUUID(), workspace.id, JSON.stringify({schemaVersion:1, grantId:funding.grantId, attemptId:fundingAttemptId, model:funding.model, provider:funding.provider, allowanceConsumed:true, billingVerified:false}), this.now(), fundingAttemptId),
      ]);
      if (claim[0].results?.length !== 1) throw new ProofPayError("AI_ALLOWANCE_USED", "This workspace's free AI attempt or the grant allowance is already used. No additional model request was sent; automatic retries are disabled.", 409);
    }
    const choice = await this.proposer(input.request.trim(), input.mode, this.env);
    if (input.mode === "sandbox" && choice.source !== "model") throw new ProofPayError("MODEL_REQUIRED", "Sandbox proposals require a genuine model response.", 503);
    const operationId = crypto.randomUUID();
    const provenance = choice.source === "model" ? safeProvenance(choice.provenance) : undefined;
    const proposalDetail = JSON.stringify({schemaVersion: 1, source: choice.source, sku: choice.sku, rationale: choice.rationale.slice(0, 500), ...(provenance ? {provenance} : {}), ...(funding ? {funding: {mode:"vercel-free-credit", grantId:funding.grantId, attemptId:fundingAttemptId, billingVerified:false}} : {})});
    // A proposal without its source record is incomplete. Commit both together;
    // a competing idempotency-key winner makes this candidate's event a no-op.
    await this.db.batch([
      this.insertStatement(workspace, input.request.trim(), input.idempotencyKey, choice, input.mode === "rehearsal" ? "Rehearsal agent" : "Purchase agent", operationId),
      this.db.prepare("INSERT INTO proofpay_events (id,workspace_id,operation_id,type,detail,created_at) SELECT ?,?,?,'PROPOSAL_CREATED',?,? WHERE EXISTS (SELECT 1 FROM proofpay_operations WHERE id = ?)").bind(crypto.randomUUID(), workspace.id, operationId, proposalDetail, this.now(), operationId),
    ]);
    const stored = await this.db.prepare("SELECT * FROM proofpay_operations WHERE workspace_id = ? AND idempotency_key = ?").bind(workspace.id, input.idempotencyKey).first<OperationRow>();
    if (stored!.request !== input.request.trim()) throw new ProofPayError("KEY_REUSED", "That idempotency key is already bound to another request.", 409);
    return this.state(owner);
  }
  private async validApproval(op: OperationRow, version: number): Promise<void> {
    if (version !== op.approval_version) throw new ProofPayError("APPROVAL_VERSION", "Refresh this operation before approving or executing it.", 409);
    if (!op.approval_digest || !op.approval_expires_at || op.approval_expires_at <= this.now()) throw new ProofPayError("APPROVAL_EXPIRED", "Approval expired. Explicitly renew the unchanged approval before execution. Existing reservations remain held.", 409);
    if (await digest(op) !== op.approval_digest) throw new ProofPayError("APPROVAL_MISMATCH", "The operation no longer matches its immutable approval.", 409);
    if (op.mode === "sandbox" && op.merchant_id !== this.env.PAYPAL_MERCHANT_ID) throw new ProofPayError("MERCHANT_CHANGED", "The configured seller no longer matches this approval.", 409);
  }
  async approve(owner: string, id: string, version: number) {
    const op = await this.operation(owner, id);
    if (version !== op.approval_version) throw new ProofPayError("APPROVAL_VERSION", "Refresh this proposal before approving.", 409);
    if (op.status !== "PROPOSED") { if (op.status === "APPROVED") return this.state(owner); throw new ProofPayError("APPROVAL_STATE", "This proposal cannot be approved in its current state.", 409); }
    const expires = this.now() + APPROVAL_TTL;
    const hash = await digest({...op, approval_expires_at: expires});
    const eligible = `id = ? AND status = 'PROPOSED' AND approval_version = ? AND workspace_id = (SELECT workspace_id FROM proofpay_sessions WHERE owner_id = ?) AND amount_cents + (SELECT COALESCE(SUM(amount_cents),0) FROM proofpay_operations WHERE workspace_id = ? AND status IN (${HELD_SQL})) <= (SELECT budget_cents FROM proofpay_workspaces WHERE id = ?)`;
    const bindings = [id, version, owner, op.workspace_id, op.workspace_id];
    // The same serial transaction checks the budget, records the owner's
    // decision and reserves funds. Audit failure cannot leave an orphan hold.
    const results = await this.db.batch([
      this.db.prepare(`INSERT INTO proofpay_events (id,workspace_id,operation_id,type,detail,created_at) SELECT ?,?,?,'APPROVED',?,? WHERE EXISTS (SELECT 1 FROM proofpay_operations WHERE ${eligible})`).bind(crypto.randomUUID(), op.workspace_id, id, "Owner approved the exact catalogue item, merchant, amount and currency. Funds are reserved for 15-minute execution authority; ambiguity never releases them automatically.", this.now(), ...bindings),
      this.db.prepare(`UPDATE proofpay_operations SET status = 'APPROVED', approval_expires_at = ?, approval_digest = ?, updated_at = ? WHERE ${eligible}`).bind(expires, hash, this.now(), ...bindings),
    ]);
    if (results[1].meta?.changes !== 1) {
      if ((await this.workspace(owner))?.id !== op.workspace_id) throw new ProofPayError("WORKSPACE_CHANGED", "This proposal belongs to an earlier workspace. Start from the active purchase desk.", 409);
      const blocked = await this.db.prepare("UPDATE proofpay_operations SET status = 'BUDGET_BLOCKED', updated_at = ? WHERE id = ? AND status = 'PROPOSED' RETURNING id").bind(this.now(), id).first();
      if (blocked) { await this.event(op.workspace_id, id, "BUDGET_BLOCKED", "Approval denied: the shared workspace allowance cannot cover this proposal. No payment was dispatched."); throw new ProofPayError("BUDGET_EXCEEDED", "The shared allowance cannot cover this purchase. Ask for a smaller catalogue option.", 409); }
      return this.state(owner);
    }
    return this.state(owner);
  }
  async cancelBeforeDispatch(owner: string, id: string, version: number) {
    const op = await this.operation(owner, id);
    if (version !== op.approval_version) throw new ProofPayError("APPROVAL_VERSION", "Refresh this request before cancelling it.", 409);
    if ((await this.workspace(owner))?.id !== op.workspace_id) throw new ProofPayError("WORKSPACE_CHANGED", "Cancel requests from the active purchase desk.", 409);
    if (op.order_id !== null || op.capture_id !== null) throw new ProofPayError("CANCEL_STATE", "This operation already has a provider order or capture. Cancellation before dispatch is no longer available.", 409);
    if (op.status === "CANCELLED") return this.state(owner);
    if (!["PROPOSED", "BUDGET_BLOCKED", "APPROVED"].includes(op.status)) throw new ProofPayError("CANCEL_STATE", "Cancellation is only available before any provider dispatch. Uncertain or completed payments must retain their existing accounting.", 409);
    // Expiry blocks new execution, not withdrawal of unused local authority.
    // Check the stored approval itself without requiring unexpired authority or
    // consulting a provider; nothing has been dispatched in an eligible state.
    if (op.status === "APPROVED" && (!op.approval_digest || !op.approval_expires_at || await digest(op) !== op.approval_digest)) throw new ProofPayError("APPROVAL_MISMATCH", "The request no longer matches its stored approval. No reservation was released.", 409);
    const cancelledAt = this.now();
    const eligible = "id = ? AND status = ? AND approval_version = ? AND approval_digest IS ? AND approval_expires_at IS ? AND order_id IS NULL AND capture_id IS NULL AND workspace_id = (SELECT workspace_id FROM proofpay_sessions WHERE owner_id = ?)";
    const bindings = [id, op.status, op.approval_version, op.approval_digest, op.approval_expires_at, owner];
    const detail = op.status === "APPROVED"
      ? "Owner cancelled this request before provider dispatch. Its local allowance reservation was released once. Purchase details and request IDs are retained. No provider cancellation or refund was requested."
      : "Owner cancelled this request before approval or provider dispatch. No funds were reserved or released. Purchase details and request IDs are retained. No provider cancellation or refund was requested.";
    // The audit event and status transition share one transaction and the exact
    // observed row predicate. If approval, renewal or dispatch wins first, both
    // statements become no-ops, so cancellation cannot release dispatched funds.
    const results = await this.db.batch([
      this.db.prepare(`INSERT INTO proofpay_events (id,workspace_id,operation_id,type,detail,created_at) SELECT ?,?,?,'REQUEST_CANCELLED',?,? WHERE EXISTS (SELECT 1 FROM proofpay_operations WHERE ${eligible})`).bind(crypto.randomUUID(), op.workspace_id, id, detail, cancelledAt, ...bindings),
      this.db.prepare(`UPDATE proofpay_operations SET status = 'CANCELLED', updated_at = ? WHERE ${eligible}`).bind(cancelledAt, ...bindings),
    ]);
    if (results[1].meta?.changes !== 1) {
      // A concurrent identical cancellation is an idempotent retry. Every other
      // state/version change needs a fresh owner decision against current state.
      const current = await this.operation(owner, id);
      if (current.status === "CANCELLED" && current.approval_version === version && current.order_id === null && current.capture_id === null && (await this.workspace(owner))?.id === current.workspace_id) return this.state(owner);
      throw new ProofPayError("CANCEL_CHANGED", "The request changed while cancellation was being applied. Refresh before taking another action; no reservation was released by this request.", 409);
    }
    return this.state(owner);
  }
  async renewApproval(owner: string, id: string, version: number) {
    const op = await this.operation(owner, id);
    if (version !== op.approval_version) throw new ProofPayError("APPROVAL_VERSION", "Refresh this operation before renewing its approval.", 409);
    if (!["APPROVED", "ORDER_READY"].includes(op.status) || op.capture_id) throw new ProofPayError("RENEWAL_STATE", "Approval can only be renewed before capture dispatch. Uncertain or completed payments cannot be re-authorized.", 409);
    if ((op.status === "APPROVED" && op.order_id) || (op.status === "ORDER_READY" && !op.order_id)) throw new ProofPayError("RENEWAL_STATE", "The stored order state requires review; approval was not changed.", 409);
    if ((await this.workspace(owner))?.id !== op.workspace_id) throw new ProofPayError("WORKSPACE_CHANGED", "Renew approval from the active purchase desk.", 409);
    if (!op.approval_digest || !op.approval_expires_at || await digest(op) !== op.approval_digest) throw new ProofPayError("APPROVAL_MISMATCH", "The operation no longer matches its stored approval. Renewal is not allowed.", 409);
    if (op.mode === "sandbox" && op.merchant_id !== this.env.PAYPAL_MERCHANT_ID) throw new ProofPayError("MERCHANT_CHANGED", "The configured seller no longer matches this approval.", 409);
    const renewedAt = this.now();
    if (op.approval_expires_at > renewedAt) throw new ProofPayError("APPROVAL_NOT_EXPIRED", "This approval is still valid; renewal is not needed.", 409);
    const nextVersion = op.approval_version + 1;
    const expires = renewedAt + APPROVAL_TTL;
    const hash = await digest({...op, approval_version: nextVersion, approval_expires_at: expires});
    const eligible = "id = ? AND status = ? AND approval_version = ? AND approval_digest = ? AND approval_expires_at = ? AND approval_expires_at <= ? AND capture_id IS NULL AND workspace_id = (SELECT workspace_id FROM proofpay_sessions WHERE owner_id = ?)";
    const bindings = [id, op.status, op.approval_version, op.approval_digest, op.approval_expires_at, renewedAt, owner];
    // The same CAS guards both audit and renewal in one transaction. A dispatch
    // winner makes both statements no-ops; a renewal winner invalidates stale
    // dispatch requests without changing the reservation or provider identity.
    const results = await this.db.batch([
      this.db.prepare(`INSERT INTO proofpay_events (id,workspace_id,operation_id,type,detail,created_at) SELECT ?,?,?,'APPROVAL_RENEWED',?,? WHERE EXISTS (SELECT 1 FROM proofpay_operations WHERE ${eligible})`).bind(crypto.randomUUID(), op.workspace_id, id, `Owner explicitly renewed unchanged purchase approval from version ${op.approval_version} to ${nextVersion}. The existing reservation, merchant, amount, item, order and provider request IDs are preserved. Execution authority expires at ${new Date(expires).toISOString()}. No payment was dispatched by renewal.`, renewedAt, ...bindings),
      this.db.prepare(`UPDATE proofpay_operations SET approval_version = ?, approval_expires_at = ?, approval_digest = ?, updated_at = ? WHERE ${eligible}`).bind(nextVersion, expires, hash, renewedAt, ...bindings),
    ]);
    if (results[1].meta?.changes !== 1) throw new ProofPayError("APPROVAL_CHANGED", "The operation changed while approval was being renewed. Refresh before taking another action.", 409);
    return this.state(owner);
  }
  async createOrder(owner: string, id: string, version: number, origin: string) {
    const op = await this.operation(owner, id);
    if (op.status === "ORDER_READY") return this.state(owner);
    if (op.status !== "APPROVED") throw new ProofPayError("ORDER_STATE", "An approved operation is required; uncertain create requests are never repeated automatically.", 409);
    await this.validApproval(op, version); const provider = this.provider(op);
    const claimed = await this.db.prepare("UPDATE proofpay_operations SET status = 'CREATE_DISPATCHED', updated_at = ? WHERE id = ? AND status = 'APPROVED' AND approval_version = ? AND approval_digest = ? AND approval_expires_at = ? AND approval_expires_at > ? RETURNING id").bind(this.now(), id, op.approval_version, op.approval_digest, op.approval_expires_at, this.now()).first();
    if (!claimed) return this.state(owner);
    await this.event(op.workspace_id, id, "CREATE_DISPATCHED", "Durable create intent stored before provider dispatch. The request ID is fixed to this operation.");
    try {
      const order = await provider.create(op, origin); verifyOrder(op, order, false);
      const url = op.mode === "sandbox" ? approvalLink(order) : null;
      await this.db.prepare("UPDATE proofpay_operations SET status = 'ORDER_READY', order_id = ?, approval_url = ?, updated_at = ? WHERE id = ? AND status = 'CREATE_DISPATCHED'").bind(order.id, url, this.now(), id).run();
      await this.event(op.workspace_id, id, "ORDER_READY", op.mode === "sandbox" ? "PayPal sandbox order stored. Complete PayPal buyer approval before capture." : "Simulated provider order stored; rehearsal buyer approval is simulated.");
    } catch {
      await this.db.prepare("UPDATE proofpay_operations SET status = 'CREATE_UNKNOWN', updated_at = ? WHERE id = ? AND status = 'CREATE_DISPATCHED'").bind(this.now(), id).run();
      await this.event(op.workspace_id, id, "CREATE_UNKNOWN", "Create outcome could not be verified. Reservation retained. No new create ID or automatic retry.");
      throw new ProofPayError("CREATE_UNKNOWN", "Order creation needs review. The allowance remains reserved.", 502);
    }
    return this.state(owner);
  }
  async capture(owner: string, id: string, version: number, fault?: "drop-response") {
    const op = await this.operation(owner, id);
    if (op.status === "CONFIRMED") return this.state(owner);
    if (op.status !== "ORDER_READY" || !op.order_id) throw new ProofPayError("CAPTURE_STATE", "Capture is available once per approved order. Use verification after an uncertain result.", 409);
    await this.validApproval(op, version); const provider = this.provider(op);
    const before = await provider.get(op); verifyOrder(op, before);
    if (before.status !== "APPROVED") throw new ProofPayError("BUYER_APPROVAL_REQUIRED", "Complete buyer approval in PayPal before capture.", 409);
    const claimed = await this.db.prepare("UPDATE proofpay_operations SET status = 'CAPTURE_DISPATCHED', updated_at = ? WHERE id = ? AND status = 'ORDER_READY' AND approval_version = ? AND approval_digest = ? AND approval_expires_at = ? AND approval_expires_at > ? RETURNING id").bind(this.now(), id, op.approval_version, op.approval_digest, op.approval_expires_at, this.now()).first();
    if (!claimed) return this.state(owner);
    await this.event(op.workspace_id, id, "CAPTURE_DISPATCHED", "Durable capture intent stored. Only this request may dispatch capture; later requests can only read provider status.");
    try {
      await provider.capture(op);
      if (fault === "drop-response") {
        await this.db.prepare("UPDATE proofpay_operations SET status = 'UNKNOWN', updated_at = ? WHERE id = ? AND status = 'CAPTURE_DISPATCHED'").bind(this.now(), id).run();
        await this.event(op.workspace_id, id, "RESPONSE_DROPPED", "Injected application fault: discarded the provider capture response before business confirmation. This is not a PayPal outage. Reservation retained.");
        return this.state(owner);
      }
    } catch {
      await this.db.prepare("UPDATE proofpay_operations SET status = 'UNKNOWN', updated_at = ? WHERE id = ? AND status = 'CAPTURE_DISPATCHED'").bind(this.now(), id).run();
      await this.event(op.workspace_id, id, "CAPTURE_UNKNOWN", "Capture response is uncertain. No second capture is permitted; verify the original order.");
      throw new ProofPayError("CAPTURE_UNKNOWN", "The payment outcome is uncertain. The allowance remains reserved until verification.", 502);
    }
    return this.reconcile(owner, id);
  }
  async reconcile(owner: string, id: string) {
    const op = await this.operation(owner, id);
    if (!op.order_id || !["CAPTURE_DISPATCHED", "UNKNOWN", "REVIEW", "CONFIRMED"].includes(op.status)) throw new ProofPayError("RECONCILE_STATE", "Verification requires a stored order with a dispatched capture. A lost create response requires manual review.", 409);
    if (!op.approval_digest || await digest(op) !== op.approval_digest) throw new ProofPayError("APPROVAL_MISMATCH", "Stored approval fields do not match; no financial state changed.", 409);
    try {
      const order = await this.provider(op).get(op);
      const captureId = completedCapture(op, order);
      if (!captureId) {
        if (op.status !== "CONFIRMED") await this.db.prepare("UPDATE proofpay_operations SET status = 'UNKNOWN', updated_at = ? WHERE id = ? AND status != 'CONFIRMED'").bind(this.now(), id).run();
        await this.event(op.workspace_id, id, "VERIFICATION_PENDING", "Provider lookup has not proved a completed matching capture. Reservation retained.");
        return this.state(owner);
      }
      const unit = order.purchase_units![0];
      const capture = unit.payments!.captures![0];
      const checkedAt = this.now();
      // Persist only the fields used by our verifier. Never retain payer details,
      // credentials, links or the full provider response in the evidence receipt.
      const verification: VerificationRecord = {
        schemaVersion: 1,
        mode: op.mode,
        simulated: op.mode === "rehearsal",
        source: op.mode === "rehearsal" ? "simulated-provider-lookup" : "paypal-sandbox-orders-get",
        checkedAt,
        operationId: op.id,
        order: {
          id: order.id!, status: order.status!,
          referenceId: unit.reference_id!, customId: unit.custom_id!,
          payeeMerchantId: unit.payee!.merchant_id!,
          amount: {value: unit.amount!.value!, currency: unit.amount!.currency_code!},
        },
        capture: {
          id: capture.id!, status: capture.status!, finalCapture: capture.final_capture!,
          amount: {value: capture.amount!.value!, currency: capture.amount!.currency_code!},
        },
      };
      const eligible = "id = ? AND status IN ('CAPTURE_DISPATCHED','UNKNOWN','REVIEW')";
      // D1 batch is transactional. Conditional inserts occur before the state
      // update, so concurrent/repeated verification records a single receipt.
      // A unique-capture conflict rolls back both the receipt and confirmation.
      await this.db.batch([
        this.db.prepare(`INSERT INTO proofpay_events (id,workspace_id,operation_id,type,detail,created_at) SELECT ?,?,?,'PROVIDER_VERIFIED',?,? WHERE EXISTS (SELECT 1 FROM proofpay_operations WHERE ${eligible})`).bind(crypto.randomUUID(), op.workspace_id, id, JSON.stringify(verification), checkedAt, id),
        this.db.prepare(`INSERT INTO proofpay_events (id,workspace_id,operation_id,type,detail,created_at) SELECT ?,?,?,'PAYMENT_CONFIRMED',?,? WHERE EXISTS (SELECT 1 FROM proofpay_operations WHERE ${eligible})`).bind(crypto.randomUUID(), op.workspace_id, id, "Read the original provider order and matched order identity, merchant, amount, currency and completed capture. Reserved funds moved to paid exactly once.", checkedAt, id),
        this.db.prepare(`UPDATE proofpay_operations SET status = 'CONFIRMED', capture_id = ?, updated_at = ? WHERE ${eligible}`).bind(captureId, checkedAt, id),
      ]);
    } catch (error) {
      const mismatch = error instanceof ProofPayError && ["PROVIDER_MISMATCH", "PROVIDER_REVIEW"].includes(error.code);
      await this.db.prepare("UPDATE proofpay_operations SET status = ?, updated_at = ? WHERE id = ? AND status != 'CONFIRMED'").bind(mismatch ? "REVIEW" : "UNKNOWN", this.now(), id).run();
      await this.event(op.workspace_id, id, mismatch ? "VERIFICATION_REVIEW" : "VERIFICATION_UNAVAILABLE", mismatch ? "Provider evidence does not prove the exact approved purchase; reservation retained for review." : "Provider lookup was unavailable; no capture was retried and no funds were released.");
      throw new ProofPayError(mismatch ? "VERIFICATION_REVIEW" : "VERIFICATION_UNAVAILABLE", mismatch ? "Provider evidence needs review. No financial state was released." : "Verification is unavailable. The existing financial state is retained.", 502);
    }
    return this.state(owner);
  }
  async evidence(owner: string, id: string) {
    const op = await this.operation(owner, id);
    const events = (await this.db.prepare("SELECT id,type,detail,created_at AS createdAt FROM proofpay_events WHERE operation_id = ? ORDER BY created_at,rowid").bind(id).all<{id: string; type: string; detail: string; createdAt: number}>()).results ?? [];
    const verificationRecords = events.filter(event => event.type === "PROVIDER_VERIFIED").map(event => JSON.parse(event.detail) as VerificationRecord);
    const approvalBinding = op.approval_digest ? {profile: "proofpay-approval-v1", algorithm: "SHA-256", encoding: "UTF-8", serialization: "JSON-array", fields: APPROVAL_BINDING_FIELDS, values: approvalBindingValues(op)} : null;
    return {receiptSchemaVersion: 1, operation: {...expose(op), workspaceId: op.workspace_id}, createRequestId: op.create_request_id, captureRequestId: op.capture_request_id, approvalDigest: op.approval_digest, approvalBinding, verificationRecords, events, claim: op.mode === "rehearsal" ? "Simulated provider and deterministic proposal. No PayPal sandbox or model execution evidence." : op.ai_source === "sandbox-diagnostic" ? "Manually selected fixed catalogue diagnostic using the PayPal sandbox adapter. No AI model was called. Inspect recorded provider outcomes; virtual accounts and funds only, with no real-money or production claim." : "PayPal sandbox adapter; inspect recorded outcomes. Sandbox uses virtual accounts and funds. No real-money or production claim."};
  }
}
