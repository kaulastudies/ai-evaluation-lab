import { ProofPayError } from "./types";

export type ApiAction = "state" | "start-rehearsal" | "start-diagnostic" | "start" | "propose" | "approve" | "cancel" | "renew-approval" | "create-order" | "capture" | "reconcile" | "evidence";
export const API_SECURITY_HEADERS = {
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "Cross-Origin-Resource-Policy": "same-origin",
  "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
};
export const MAX_REQUEST_BYTES = 10_000;
const fields: Record<ApiAction, readonly string[]> = {
  state: [], evidence: [], "start-rehearsal": [], "start-diagnostic": [], start: ["mode"],
  propose: ["request", "mode", "idempotencyKey"],
  approve: ["approvalVersion"], cancel: ["approvalVersion"], "renew-approval": ["approvalVersion"],
  "create-order": ["approvalVersion"], capture: ["approvalVersion", "fault"], reconcile: [],
};
export function allowedMethods(action: ApiAction): string { return action === "state" || action === "evidence" ? "GET, HEAD" : "POST"; }

/** Bound bytes while streaming, including chunked or misleading-length bodies.
 * Cancel without awaiting an untrusted stream's cancellation handler. */
export async function readTextLimited(message: Request | Response, limit: number): Promise<string> {
  const declared = message.headers.get("content-length");
  if (declared && /^\d+$/.test(declared) && Number(declared) > limit) {
    void message.body?.cancel().catch(() => {});
    throw new ProofPayError("PAYLOAD_TOO_LARGE", "The payload exceeds the allowed size.", 413);
  }
  if (!message.body) return "";
  const reader = message.body.getReader();
  const decoder = new TextDecoder("utf-8", {fatal: true});
  let size = 0, text = "";
  try {
    while (true) {
      const result = await reader.read();
      if (result.done) break;
      size += result.value.byteLength;
      if (size > limit) throw new ProofPayError("PAYLOAD_TOO_LARGE", "The payload exceeds the allowed size.", 413);
      text += decoder.decode(result.value, {stream: true});
    }
    return text + decoder.decode();
  } catch (error) {
    void reader.cancel().catch(() => {});
    if (error instanceof ProofPayError) throw error;
    throw new ProofPayError("INVALID_PAYLOAD", "The payload could not be read as UTF-8 text.", 400);
  } finally { reader.releaseLock(); }
}

export async function parseApiRequest(request: Request, action: ApiAction, id?: string): Promise<Record<string, unknown>> {
  if (!allowedMethods(action).split(", ").includes(request.method)) throw new ProofPayError("METHOD_NOT_ALLOWED", "This HTTP method is not supported for this action.", 405);
  const operationAction = ["approve", "cancel", "renew-approval", "create-order", "capture", "reconcile", "evidence"].includes(action);
  if (operationAction && (typeof id !== "string" || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id))) throw new ProofPayError("INVALID_OPERATION", "The operation identifier is invalid.");
  if (request.method !== "POST") return {};
  if (request.headers.has("content-encoding") && request.headers.get("content-encoding")?.toLowerCase() !== "identity") throw new ProofPayError("ENCODING_UNSUPPORTED", "Compressed request bodies are not supported.", 415);
  let input: unknown;
  try { input = JSON.parse((await readTextLimited(request, MAX_REQUEST_BYTES)) || "{}"); }
  catch (error) { if (error instanceof ProofPayError) throw error; throw new ProofPayError("INVALID_JSON", "Send a valid JSON object."); }
  if (!input || typeof input !== "object" || Array.isArray(input)) throw new ProofPayError("INVALID_JSON", "Send a JSON object.");
  const value = input as Record<string, unknown>;
  if (Object.keys(value).some(key => !fields[action].includes(key))) throw new ProofPayError("UNSUPPORTED_FIELD", "The request contains fields this action does not accept.");
  if (fields[action].includes("approvalVersion") && (!Number.isSafeInteger(value.approvalVersion) || Number(value.approvalVersion) < 1)) throw new ProofPayError("INVALID_VERSION", "Provide the current positive integer approval version.");
  return value;
}
