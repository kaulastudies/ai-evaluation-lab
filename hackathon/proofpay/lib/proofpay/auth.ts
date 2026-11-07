import { ProofPayError } from "./types";

/** The private Sites ingress strips/splices this authenticated identity header.
 * Never expose this worker directly behind an ingress that trusts caller headers. */
export function authenticateRequest(request: Request): string {
  const owner = request.headers.get("oai-authenticated-user-id");
  if (!owner || owner.length > 256) throw new ProofPayError("AUTH_REQUIRED", "Sign in to use your private purchase desk.", 401);
  if (request.method !== "GET" && request.method !== "HEAD") {
    const origin = request.headers.get("origin");
    if (!origin || origin !== new URL(request.url).origin) throw new ProofPayError("ORIGIN_REJECTED", "Mutations must come from this purchase desk.", 403);
    if (!request.headers.get("content-type")?.toLowerCase().startsWith("application/json")) throw new ProofPayError("JSON_REQUIRED", "Send an application/json request.", 415);
    const site = request.headers.get("sec-fetch-site");
    if (site && !["same-origin", "none"].includes(site)) throw new ProofPayError("ORIGIN_REJECTED", "Cross-site mutations are not allowed.", 403);
  }
  return owner;
}
