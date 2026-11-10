import { createHmac, randomBytes, scrypt, timingSafeEqual } from "node:crypto";
import { ProofPayError } from "./types";

export type OwnerConfiguration = {OWNER_ID?: string; OWNER_PASSWORD_HASH?: string; SESSION_SECRET?: string; APP_ORIGIN?: string; NODE_ENV?: string};
export const SESSION_COOKIE = "__Host-proofpay-session";
export const SESSION_SECONDS = 8 * 60 * 60;
const passwordPattern = /^scrypt\$16384\$8\$1\$([A-Za-z0-9_-]{22})\$([A-Za-z0-9_-]{43})$/;

function originOf(config: OwnerConfiguration): string {
  let url: URL;
  try { url = new URL(config.APP_ORIGIN ?? ""); } catch { throw new ProofPayError("AUTH_NOT_CONFIGURED", "Owner sign-in is not configured.", 503); }
  const local = config.NODE_ENV !== "production" && url.protocol === "http:" && ["localhost", "127.0.0.1"].includes(url.hostname);
  if ((!local && url.protocol !== "https:") || url.username || url.password || url.pathname !== "/" || url.search || url.hash) throw new ProofPayError("AUTH_NOT_CONFIGURED", "Owner sign-in is not configured.", 503);
  return url.origin;
}
export function requireOwnerConfiguration(config: OwnerConfiguration): {owner: string; secret: string; passwordHash: string; origin: string} {
  const origin = originOf(config);
  if (!config.OWNER_ID || !/^[A-Za-z0-9_-]{1,128}$/.test(config.OWNER_ID) || !config.SESSION_SECRET || !/^[A-Za-z0-9_-]{43,128}$/.test(config.SESSION_SECRET) || !config.OWNER_PASSWORD_HASH || !passwordPattern.test(config.OWNER_PASSWORD_HASH)) throw new ProofPayError("AUTH_NOT_CONFIGURED", "Owner sign-in is not configured.", 503);
  return {owner: config.OWNER_ID, secret: config.SESSION_SECRET, passwordHash: config.OWNER_PASSWORD_HASH, origin};
}
export function assertRequestOrigin(request: Request, config: OwnerConfiguration): void {
  const origin = originOf(config);
  if (new URL(request.url).origin !== origin) throw new ProofPayError("ORIGIN_REJECTED", "Use the configured purchase desk address.", 403);
  if (request.method !== "GET" && request.method !== "HEAD") {
    if (request.headers.get("origin") !== origin) throw new ProofPayError("ORIGIN_REJECTED", "Mutations must come from this purchase desk.", 403);
    if (request.headers.get("content-type")?.split(";", 1)[0].trim().toLowerCase() !== "application/json") throw new ProofPayError("JSON_REQUIRED", "Send an application/json request.", 415);
    const site = request.headers.get("sec-fetch-site");
    if (site && !["same-origin", "none"].includes(site)) throw new ProofPayError("ORIGIN_REJECTED", "Cross-site mutations are not allowed.", 403);
  }
}
function sign(value: string, secret: string): string { return createHmac("sha256", secret).update(value).digest("base64url"); }
export function issueSession(config: OwnerConfiguration, now = Date.now()): string {
  const owner = requireOwnerConfiguration(config);
  const iat = Math.floor(now / 1000);
  const payload = Buffer.from(JSON.stringify({v: 1, sub: owner.owner, iat, exp: iat + SESSION_SECONDS, nonce: randomBytes(16).toString("base64url")})).toString("base64url");
  return `${payload}.${sign(payload, owner.secret)}`;
}
export function sessionCookie(value: string, maxAge = SESSION_SECONDS): string { return `${SESSION_COOKIE}=${value}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${maxAge}`; }

/** Identity comes only from a verified session. Browser-supplied Sites/Vercel
 * identity headers never authorize the owner on this runtime. */
export async function authenticateRequest(request: Request, config: OwnerConfiguration = process.env, now = Date.now()): Promise<string> {
  const owner = requireOwnerConfiguration(config);
  assertRequestOrigin(request, config);
  const tokens = (request.headers.get("cookie") ?? "").split(";").map(part => part.trim()).filter(part => part.startsWith(`${SESSION_COOKIE}=`)).map(part => part.slice(SESSION_COOKIE.length + 1));
  const denied = () => new ProofPayError("AUTH_REQUIRED", "Sign in with the owner key to use this purchase desk.", 401);
  if (tokens.length !== 1 || tokens[0].length > 2048) throw denied();
  const [payload, signature, extra] = tokens[0].split(".");
  if (!payload || !signature || extra !== undefined || !/^[A-Za-z0-9_-]+$/.test(payload) || !/^[A-Za-z0-9_-]{43}$/.test(signature)) throw denied();
  const expected = Buffer.from(sign(payload, owner.secret), "base64url"), actual = Buffer.from(signature, "base64url");
  if (actual.length !== expected.length || !timingSafeEqual(actual, expected)) throw denied();
  let value: {v?: unknown; sub?: unknown; iat?: unknown; exp?: unknown; nonce?: unknown};
  try { value = JSON.parse(Buffer.from(payload, "base64url").toString("utf8")); } catch { throw denied(); }
  const current = Math.floor(now / 1000);
  if (!value || value.v !== 1 || value.sub !== owner.owner || !Number.isSafeInteger(value.iat) || !Number.isSafeInteger(value.exp) || Number(value.iat) > current + 30 || Number(value.exp) <= current || Number(value.exp) - Number(value.iat) !== SESSION_SECONDS || typeof value.nonce !== "string" || !/^[A-Za-z0-9_-]{22}$/.test(value.nonce)) throw denied();
  return owner.owner;
}
export async function verifyOwnerPassword(password: string, config: OwnerConfiguration): Promise<boolean> {
  const {passwordHash} = requireOwnerConfiguration(config);
  if (password.length < 16 || password.length > 256) return false;
  const match = passwordPattern.exec(passwordHash)!;
  const expected = Buffer.from(match[2], "base64url"), salt = Buffer.from(match[1], "base64url");
  const actual = await new Promise<Buffer>((resolve, reject) => scrypt(password, salt, 32, {N: 16384, r: 8, p: 1, maxmem: 64 * 1024 * 1024}, (error, key) => error ? reject(error) : resolve(key)));
  return expected.length === actual.length && timingSafeEqual(actual, expected);
}
