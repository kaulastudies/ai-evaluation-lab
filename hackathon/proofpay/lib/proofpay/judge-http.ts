import {assertRequestOrigin} from "./auth";
import {authenticateJudgeRequest, hasJudgeCookie, issueJudgeSession, judgeCookie, requireJudgeConfiguration} from "./judge-auth";
import type {JudgeIdentity} from "./judge-auth";
import {claimJudgeMutation, claimJudgeSession, JUDGE_MUTATION_LIMIT, JUDGE_RESET_LIMIT} from "./judge-limits";
import {API_SECURITY_HEADERS, allowedMethods, parseApiRequest} from "./request";
import type {ApiAction} from "./request";
import {getDatabase, getJudgeRuntimeConfiguration} from "./runtime";
import {ProofPayService} from "./service";
import {RehearsalProvider} from "./provider";
import {ProofPayError} from "./types";
import type {OperationRow, SqlDatabase} from "./types";

type JudgeRoute = {action: ApiAction; session?: boolean; id?: string};
function resolveRoute(path: string[]): JudgeRoute {
  const exact = path.join("/");
  if (exact === "session") return {action: "start-rehearsal", session: true};
  if (exact === "state") return {action: "state"};
  if (exact === "rehearsal/start") return {action: "start-rehearsal"};
  if (exact === "proposals") return {action: "propose"};
  const allowed = ["approve", "cancel", "renew-approval", "create-order", "capture", "reconcile", "evidence"] as const;
  const action = allowed.find(value => value === path[2]);
  if (path.length === 3 && path[0] === "operations" && action) return {action, id: path[1]};
  throw new ProofPayError("NOT_FOUND", "This action is unavailable in judge rehearsal.", 404);
}
function requireRehearsal(op: OperationRow) {
  if (op.mode !== "rehearsal" || op.merchant_id !== "rehearsal-seller") throw new ProofPayError("JUDGE_REHEARSAL_ONLY", "Judge sessions can only use the simulated rehearsal provider.", 403);
}
/** This factory cannot construct a network provider or model. The production
 * environment and request-scoped Vercel identity are never passed to it. */
function judgeService(db: SqlDatabase): ProofPayService {
  const simulated = new RehearsalProvider(db, Date.now);
  return new ProofPayService({db, env: {}, provider: {
    async create(op) { requireRehearsal(op); return simulated.create(op); },
    async capture(op) { requireRehearsal(op); return simulated.capture(op); },
    async get(op) { requireRehearsal(op); return simulated.get(op); },
  }, ai: async (request, mode) => {
    if (mode !== "rehearsal") throw new ProofPayError("JUDGE_REHEARSAL_ONLY", "Judge proposals use deterministic rehearsal rules only.", 403);
    return {sku: /cheaper|starter|smaller|budget|90/i.test(request) ? "starter-review" : /design|160/i.test(request) ? "design-review" : "workflow-review", rationale: "Deterministic judge rehearsal selection. No AI model was called.", source: "rehearsal-rule"};
  }});
}
function metadata(identity: JudgeIdentity) { return {simulated: true, expiresAt: identity.expiresAt, resetLimit: JUDGE_RESET_LIMIT, mutationLimit: JUDGE_MUTATION_LIMIT}; }
async function rehearsalState(service: ProofPayService, identity: JudgeIdentity) {
  const state = await service.state(identity.owner);
  if ((state.workspace && state.workspace.mode !== "rehearsal") || state.operations.some(op => op.providerMode !== "rehearsal")) throw new ProofPayError("JUDGE_REHEARSAL_ONLY", "This guest workspace is not a rehearsal. No payment action is available.", 403);
  return state;
}

export async function handleJudge(request: Request, path: string[]): Promise<Response> {
  let service: ProofPayService | undefined, identity: JudgeIdentity | undefined, route: JudgeRoute | undefined;
  try {
    const config = getJudgeRuntimeConfiguration();
    requireJudgeConfiguration(config);
    assertRequestOrigin(request, config);
    route = resolveRoute(path);
    const input = await parseApiRequest(request, route.action, route.id);
    // Explicitly reject sandbox requests before selecting any database/provider.
    if (route.action === "propose" && input.mode !== "rehearsal") throw new ProofPayError("JUDGE_REHEARSAL_ONLY", "Judge sessions only accept rehearsal proposals. No model or PayPal calls are available.", 403);
    if (!route.session || hasJudgeCookie(request)) identity = authenticateJudgeRequest(request, config);
    const db = getDatabase(config);
    service = judgeService(db);
    if (route.session && !identity) {
      await claimJudgeSession(db);
      const issued = issueJudgeSession(config);
      identity = {owner: issued.owner, expiresAt: issued.expiresAt};
      const state = await service.start(identity.owner, "rehearsal", true);
      return Response.json({state, judge: metadata(identity)}, {headers: {...API_SECURITY_HEADERS, "Set-Cookie": judgeCookie(issued.token)}});
    }
    if (!identity) throw new ProofPayError("JUDGE_AUTH_REQUIRED", "Begin a judge rehearsal first.", 401);
    await rehearsalState(service, identity);
    if (route.session) return Response.json({state: await rehearsalState(service, identity), judge: metadata(identity)}, {headers: API_SECURITY_HEADERS});
    if (route.id) {
      const op = await db.prepare("SELECT o.* FROM proofpay_operations o JOIN proofpay_workspaces w ON o.workspace_id = w.id WHERE o.id = ? AND w.owner_id = ?").bind(route.id, identity.owner).first<OperationRow>();
      if (!op) throw new ProofPayError("NOT_FOUND", "The operation was not found in your guest rehearsal.", 404);
      requireRehearsal(op);
    }
    if (request.method === "POST") await claimJudgeMutation(db, identity.owner, route.action === "start-rehearsal");
    const owner = identity.owner;
    switch (route.action) {
      case "state": break;
      case "start-rehearsal": await service.start(owner, "rehearsal", true); break;
      case "propose": await service.propose(owner, {request: input.request as string, mode: "rehearsal", idempotencyKey: input.idempotencyKey as string}); break;
      case "approve": await service.approve(owner, route.id!, input.approvalVersion as number); break;
      case "cancel": await service.cancelBeforeDispatch(owner, route.id!, input.approvalVersion as number); break;
      case "renew-approval": await service.renewApproval(owner, route.id!, input.approvalVersion as number); break;
      case "create-order": await service.createOrder(owner, route.id!, input.approvalVersion as number, new URL(request.url).origin); break;
      case "capture":
        if (input.fault !== undefined && input.fault !== "drop-response") throw new ProofPayError("INVALID_FAULT", "The only supported fault is drop-response.");
        await service.capture(owner, route.id!, input.approvalVersion as number, input.fault as "drop-response" | undefined); break;
      case "reconcile": await service.reconcile(owner, route.id!); break;
      case "evidence": return Response.json(await service.evidence(owner, route.id!), {headers: API_SECURITY_HEADERS});
      default: throw new ProofPayError("NOT_FOUND", "This action is unavailable in judge rehearsal.", 404);
    }
    return Response.json({state: await rehearsalState(service, identity), judge: metadata(identity)}, {headers: API_SECURITY_HEADERS, status: route.action === "capture" && input.fault === "drop-response" ? 202 : 200});
  } catch (error) {
    const safe = error instanceof ProofPayError ? error : new ProofPayError("JUDGE_UNAVAILABLE", "Judge rehearsal could not complete this action. Existing simulated records are retained.", 503);
    let state;
    if (service && identity) { try { state = await rehearsalState(service, identity); } catch { /* Never expose a foreign or non-rehearsal record. */ } }
    return Response.json({error: safe.message, code: safe.code, ...(state && identity ? {state, judge: metadata(identity)} : {})}, {status: safe.status, headers: {...API_SECURITY_HEADERS, ...(safe.status === 405 && route ? {Allow: allowedMethods(route.action)} : {}), ...(safe.code === "JUDGE_AUTH_REQUIRED" ? {"Set-Cookie": "__Host-proofpay-judge=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0"} : {})}});
  }
}
