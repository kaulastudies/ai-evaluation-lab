import {ProofPayError} from "./types";
import type {SqlDatabase} from "./types";

export const JUDGE_RESET_LIMIT = 10;
export const JUDGE_MUTATION_LIMIT = 100;
// Fixed deployment ceilings bound storage use, including guests who deliberately
// discard their cookies. They never reset any payment or AI funding allowance.
export const JUDGE_SESSION_HOURLY_LIMIT = 60;
export const JUDGE_SESSION_TOTAL_LIMIT = 300;
async function claim(db: SqlDatabase, id: string, window: number, limit: number) {
  return await db.prepare("INSERT INTO proofpay_auth_limits (id,window_start,attempts) VALUES (?,?,1) ON CONFLICT(id) DO UPDATE SET attempts = CASE WHEN proofpay_auth_limits.window_start = excluded.window_start THEN proofpay_auth_limits.attempts + 1 ELSE 1 END, window_start = excluded.window_start WHERE proofpay_auth_limits.window_start != excluded.window_start OR proofpay_auth_limits.attempts < ? RETURNING attempts").bind(id, window, limit).first() !== null;
}
export async function claimJudgeSession(db: SqlDatabase, now = Date.now()) {
  if (!await claim(db, "judge-new-hour", Math.floor(now / 3600000), JUDGE_SESSION_HOURLY_LIMIT)) throw new ProofPayError("JUDGE_SESSION_LIMIT", "The public rehearsal session limit has been reached for this hour. Try again later.", 429);
  if (!await claim(db, "judge-new-total", 0, JUDGE_SESSION_TOTAL_LIMIT)) throw new ProofPayError("JUDGE_SESSION_LIMIT", "This public rehearsal has reached its total session allowance. Use the documented local test setup or contact the project owner.", 429);
}
export async function claimJudgeMutation(db: SqlDatabase, owner: string, reset = false) {
  if (!await claim(db, `judge-mutations:${owner}`, 0, JUDGE_MUTATION_LIMIT)) throw new ProofPayError("JUDGE_MUTATION_LIMIT", "This guest session has used its rehearsal action allowance. Use the documented local test setup for further testing.", 429);
  if (reset && !await claim(db, `judge-resets:${owner}`, 0, JUDGE_RESET_LIMIT)) throw new ProofPayError("JUDGE_RESET_LIMIT", "This guest session has used its ten simulation resets. Existing rehearsal evidence is retained.", 429);
}
