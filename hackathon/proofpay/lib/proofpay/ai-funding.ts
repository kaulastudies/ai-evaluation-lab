import { Configuration, ProofPayError } from "./types";

export const FREE_GATEWAY_MODEL = "openai/gpt-4.1-mini";
export const FREE_GATEWAY_PROVIDER = "openai";
export const FREE_GATEWAY_ENDPOINT = "https://ai-gateway.vercel.sh/v1/chat/completions";
export type AiFundingGrant = {grantId: string; expiresAt: number; maxRequests: number; model: string; provider: string};

/** An operator's reviewed free-credit grant, not a live billing attestation.
 * No personal provider key, Gateway API key, BYOK or direct-provider path exists.
 * A durable service claim is also required before each sandbox proposal attempt.
 */
export function requireAiFunding(config: Configuration, now = Date.now()): AiFundingGrant {
  if (config.AI_FUNDING_MODE !== "vercel-free-credit" || config.AI_GATEWAY_FREE_ONLY_CONFIRMED !== "true") throw new ProofPayError("AI_NOT_CONFIGURED", "A reviewed free AI allowance must be enabled first. Paid inference is disabled.", 503);
  if (config.AI_API_KEY || config.AI_BASE_URL || config.AI_MODEL || config.AI_GATEWAY_API_KEY) throw new ProofPayError("AI_FUNDING_RESTRICTED", "Direct-provider and API-key inference are disabled. Use the reviewed free allowance with Vercel identity only.", 503);
  if (config.AI_GATEWAY_MODEL !== FREE_GATEWAY_MODEL) throw new ProofPayError("AI_FUNDING_RESTRICTED", "The requested model is outside the reviewed free-credit configuration.", 503);
  if (!config.AI_GATEWAY_GRANT_ID || !/^[A-Za-z0-9_-]{1,80}$/.test(config.AI_GATEWAY_GRANT_ID)) throw new ProofPayError("AI_NOT_CONFIGURED", "The free AI allowance needs a valid grant reference.", 503);
  const expiry = config.AI_GATEWAY_GRANT_EXPIRES_AT ?? "";
  const expiresAt = Date.parse(expiry);
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(expiry) || !Number.isSafeInteger(expiresAt) || new Date(expiresAt).toISOString() !== expiry.replace(/Z$/, expiry.includes(".") ? "Z" : ".000Z") || expiresAt <= now) throw new ProofPayError("AI_FUNDING_EXPIRED", "The reviewed free AI allowance has expired or has no valid expiry. No model request was sent.", 503);
  if (!/^(?:[1-9]|10)$/.test(config.AI_GATEWAY_MAX_REQUESTS ?? "")) throw new ProofPayError("AI_NOT_CONFIGURED", "Set an explicit free AI attempt limit from 1 to 10. Paid inference is disabled.", 503);
  if (!config.VERCEL_OIDC_TOKEN || config.VERCEL_OIDC_TOKEN.length > 16384 || !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(config.VERCEL_OIDC_TOKEN)) throw new ProofPayError("AI_NOT_CONFIGURED", "A current Vercel identity token is required for the free AI allowance.", 503);
  return {grantId: config.AI_GATEWAY_GRANT_ID, expiresAt, maxRequests: Number(config.AI_GATEWAY_MAX_REQUESTS), model: FREE_GATEWAY_MODEL, provider: FREE_GATEWAY_PROVIDER};
}

export function aiFundingReady(config: Configuration): boolean {
  try { requireAiFunding(config); return true; } catch { return false; }
}
