import {createHmac, randomUUID, timingSafeEqual} from "node:crypto";
import {assertRequestOrigin} from "./auth";
import {ProofPayError} from "./types";

export type JudgeConfiguration = {JUDGE_DEMO_ONLY?: string; JUDGE_SESSION_SECRET?: string; APP_ORIGIN?: string; NODE_ENV?: string};
export const JUDGE_COOKIE = "__Host-proofpay-judge";
export const JUDGE_SESSION_SECONDS = 2 * 60 * 60;
export type JudgeIdentity = {owner: string; expiresAt: number};
function denied() { return new ProofPayError("JUDGE_AUTH_REQUIRED", "Begin a new isolated judge rehearsal. Guest sessions expire after two hours.", 401); }
export function requireJudgeConfiguration(config: JudgeConfiguration) {
  if (config.JUDGE_DEMO_ONLY !== "true") throw new ProofPayError("NOT_FOUND", "Judge rehearsal is unavailable in this deployment.", 404);
  if (!config.JUDGE_SESSION_SECRET || !/^[A-Za-z0-9_-]{43,128}$/.test(config.JUDGE_SESSION_SECRET)) throw new ProofPayError("JUDGE_NOT_CONFIGURED", "Judge rehearsal sessions are not configured.", 503);
  let url: URL;
  try { url = new URL(config.APP_ORIGIN ?? ""); } catch { throw new ProofPayError("JUDGE_NOT_CONFIGURED", "Judge rehearsal origin is not configured.", 503); }
  if (url.protocol !== "https:" || url.username || url.password || url.pathname !== "/" || url.search || url.hash) throw new ProofPayError("JUDGE_NOT_CONFIGURED", "Judge rehearsal requires its configured HTTPS origin.", 503);
  return {secret: config.JUDGE_SESSION_SECRET, origin: url.origin};
}
function sign(payload: string, secret: string) { return createHmac("sha256", secret).update(`proofpay-judge-v1.${payload}`).digest("base64url"); }
export function hasJudgeCookie(request: Request): boolean { return (request.headers.get("cookie") ?? "").split(";").some(part => part.trim().startsWith(`${JUDGE_COOKIE}=`)); }
export function judgeCookie(value: string): string { return `${JUDGE_COOKIE}=${value}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${JUDGE_SESSION_SECONDS}`; }
export function issueJudgeSession(config: JudgeConfiguration, now = Date.now()) {
  const {secret, origin} = requireJudgeConfiguration(config);
  const iat = Math.floor(now / 1000);
  // ':' is forbidden in configured owner IDs, keeping identities disjoint even
  // if an operator mistakenly points this deployment at the owner database.
  const owner = `judge:${randomUUID()}`, expiresAt = (iat + JUDGE_SESSION_SECONDS) * 1000;
  const payload = Buffer.from(JSON.stringify({v: 1, kind: "judge-rehearsal", sub: owner, aud: origin, iat, exp: iat + JUDGE_SESSION_SECONDS})).toString("base64url");
  return {owner, expiresAt, token: `${payload}.${sign(payload, secret)}`};
}
export function authenticateJudgeRequest(request: Request, config: JudgeConfiguration, now = Date.now()): JudgeIdentity {
  const {secret, origin} = requireJudgeConfiguration(config);
  assertRequestOrigin(request, config);
  const tokens = (request.headers.get("cookie") ?? "").split(";").map(part => part.trim()).filter(part => part.startsWith(`${JUDGE_COOKIE}=`)).map(part => part.slice(JUDGE_COOKIE.length + 1));
  if (tokens.length !== 1 || tokens[0].length > 2048) throw denied();
  const [payload, signature, extra] = tokens[0].split(".");
  if (!payload || !/^[A-Za-z0-9_-]+$/.test(payload) || !signature || !/^[A-Za-z0-9_-]{43}$/.test(signature) || extra !== undefined) throw denied();
  const actual = Buffer.from(signature, "base64url"), expected = Buffer.from(sign(payload, secret), "base64url");
  if (actual.length !== expected.length || !timingSafeEqual(actual, expected)) throw denied();
  let value: {v?: unknown; kind?: unknown; sub?: unknown; aud?: unknown; iat?: unknown; exp?: unknown};
  try { value = JSON.parse(Buffer.from(payload, "base64url").toString("utf8")); } catch { throw denied(); }
  const current = Math.floor(now / 1000);
  if (!value || value.v !== 1 || value.kind !== "judge-rehearsal" || value.aud !== origin || typeof value.sub !== "string" || !/^judge:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(value.sub) || !Number.isSafeInteger(value.iat) || !Number.isSafeInteger(value.exp) || Number(value.iat) > current + 30 || Number(value.exp) <= current || Number(value.exp) - Number(value.iat) !== JUDGE_SESSION_SECONDS) throw denied();
  return {owner: value.sub, expiresAt: Number(value.exp) * 1000};
}
