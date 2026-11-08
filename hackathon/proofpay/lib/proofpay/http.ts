import { env } from "cloudflare:workers";
import { authenticateRequest } from "./auth";
import { ProofPayService } from "./service";
import { Configuration, Mode, ProofPayError, SqlDatabase } from "./types";
import { allowedMethods, ApiAction, API_SECURITY_HEADERS, parseApiRequest } from "./request";

export async function handle(request: Request, action: ApiAction, id?: string): Promise<Response> {
  let service: ProofPayService | undefined;
  let owner: string | undefined;
  const headers = API_SECURITY_HEADERS;
  try {
    owner = authenticateRequest(request);
    const input = await parseApiRequest(request, action, id);
    if (!env.DB) throw new ProofPayError("DATABASE_UNAVAILABLE", "The durable database is not configured. No action was taken.", 503);
    service = new ProofPayService({db: env.DB as unknown as SqlDatabase, env: env as Configuration});
    let state;
    switch (action) {
      case "state": state = await service.state(owner); break;
      case "start-rehearsal": state = await service.start(owner, "rehearsal", true); break;
      case "start-diagnostic": state = await service.startSandboxDiagnostic(owner); break;
      case "start": state = await service.start(owner, input.mode as Mode); break;
      case "propose": state = await service.propose(owner, {request: input.request as string, mode: input.mode as Mode, idempotencyKey: input.idempotencyKey as string}); break;
      case "approve": state = await service.approve(owner, id!, input.approvalVersion as number); break;
      case "cancel": state = await service.cancelBeforeDispatch(owner, id!, input.approvalVersion as number); break;
      case "renew-approval": state = await service.renewApproval(owner, id!, input.approvalVersion as number); break;
      case "create-order": state = await service.createOrder(owner, id!, input.approvalVersion as number, new URL(request.url).origin); break;
      case "capture":
        if (input.fault !== undefined && input.fault !== "drop-response") throw new ProofPayError("INVALID_FAULT", "The only supported fault is drop-response.");
        state = await service.capture(owner, id!, input.approvalVersion as number, input.fault as "drop-response" | undefined); break;
      case "reconcile": state = await service.reconcile(owner, id!); break;
      case "evidence": return Response.json(await service.evidence(owner, id!), {headers});
    }
    return Response.json({state}, {headers, status: action === "capture" && input.fault === "drop-response" ? 202 : 200});
  } catch (error) {
    const safe = error instanceof ProofPayError ? error : new ProofPayError("SERVICE_UNAVAILABLE", "The purchase desk could not complete this request. Existing durable reservations are retained.", 503);
    let state;
    if (service && owner) { try { state = await service.state(owner); } catch { /* Never leak database or credential internals. */ } }
    return Response.json({error: safe.message, code: safe.code, ...(state ? {state} : {})}, {status: safe.status, headers: {...headers, ...(safe.status === 405 ? {Allow: allowedMethods(action)} : {})}});
  }
}
