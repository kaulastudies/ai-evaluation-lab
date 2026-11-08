import { authenticateRequest } from "./auth";
import { ProofPayService } from "./service";
import { Mode, ProofPayError } from "./types";
import { allowedMethods, ApiAction, API_SECURITY_HEADERS, parseApiRequest } from "./request";
import { getDatabase, getRequestConfiguration, getRuntimeConfiguration } from "./runtime";

export async function handle(request: Request, action: ApiAction, id?: string): Promise<Response> {
  let service: ProofPayService | undefined;
  let owner: string | undefined;
  const headers = API_SECURITY_HEADERS;
  try {
    const config = getRuntimeConfiguration();
    if (config.JUDGE_DEMO_ONLY === "true") throw new ProofPayError("NOT_FOUND", "This route is unavailable in the judge rehearsal deployment.", 404);
    owner = await authenticateRequest(request, config);
    const input = await parseApiRequest(request, action, id);
    service = new ProofPayService({db: getDatabase(config), env: await getRequestConfiguration(config)});
    let state;
    switch (action) {
      case "business": return Response.json({business: await service.business(owner)}, {headers});
      case "save-business": return Response.json({business: await service.saveBusiness(owner, {businessName: input.businessName as string, department: input.department as string, defaultBudgetCents: input.defaultBudgetCents as number, version: input.version as number})}, {headers});
      case "workspace-history": return Response.json(await service.workspaceHistory(owner), {headers});
      case "select-workspace": state = await service.selectWorkspace(owner, input.workspaceId as string); break;
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
