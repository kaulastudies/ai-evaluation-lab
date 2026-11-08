import { assertRequestOrigin, issueSession, requireOwnerConfiguration, sessionCookie, verifyOwnerPassword } from "./auth";
import { API_SECURITY_HEADERS, readTextLimited } from "./request";
import { getDatabase, getRuntimeConfiguration } from "./runtime";
import { ProofPayError } from "./types";
import { claimLoginAttempt } from "./auth-rate-limit";

export async function ownerLogin(request: Request, logout = false): Promise<Response> {
  try {
    const config = getRuntimeConfiguration();
    assertRequestOrigin(request, config);
    if (request.method !== "POST") throw new ProofPayError("METHOD_NOT_ALLOWED", "Use POST for this action.", 405);
    const input: unknown = JSON.parse(await readTextLimited(request, 4096));
    if (!input || typeof input !== "object" || Array.isArray(input)) throw new ProofPayError("INVALID_JSON", "Send a JSON object.");
    const body = input as Record<string, unknown>;
    if (logout) {
      if (Object.keys(body).length) throw new ProofPayError("UNSUPPORTED_FIELD", "Logout accepts an empty object.");
      return Response.json({ok: true}, {headers: {...API_SECURITY_HEADERS, "Set-Cookie": sessionCookie("", 0)}});
    }
    requireOwnerConfiguration(config);
    if (Object.keys(body).length !== 1 || typeof body.password !== "string" || body.password.length > 256) throw new ProofPayError("INVALID_LOGIN", "Provide the owner key.");
    // One private desk has one owner. A global, durable cap avoids trusting a
    // forgeable forwarded-IP header and bounds scrypt work across instances.
    const admitted = await claimLoginAttempt(getDatabase(config));
    if (!admitted) throw new ProofPayError("LOGIN_RATE_LIMITED", "Too many sign-in attempts. Try again in one minute.", 429);
    if (!await verifyOwnerPassword(body.password, config)) throw new ProofPayError("AUTH_INVALID", "The owner key was not accepted.", 401);
    return Response.json({ok: true}, {headers: {...API_SECURITY_HEADERS, "Set-Cookie": sessionCookie(issueSession(config))}});
  } catch (error) {
    const safe = error instanceof ProofPayError ? error : error instanceof SyntaxError ? new ProofPayError("INVALID_JSON", "Send valid JSON.") : new ProofPayError("AUTH_UNAVAILABLE", "Owner sign-in is temporarily unavailable.", 503);
    return Response.json({error: safe.message, code: safe.code}, {status: safe.status, headers: {...API_SECURITY_HEADERS, ...(safe.status === 429 ? {"Retry-After": "60"} : {})}});
  }
}
