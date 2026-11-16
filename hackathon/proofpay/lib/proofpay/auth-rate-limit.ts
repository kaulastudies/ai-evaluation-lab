import type { SqlDatabase } from "./types";
export async function claimLoginAttempt(db: SqlDatabase, now = Date.now()): Promise<boolean> {
  const bucket = Math.floor(now / 60000);
  const admitted = await db.prepare("INSERT INTO proofpay_auth_limits (id,window_start,attempts) VALUES ('owner-login',?,1) ON CONFLICT(id) DO UPDATE SET attempts = CASE WHEN proofpay_auth_limits.window_start = excluded.window_start THEN proofpay_auth_limits.attempts + 1 ELSE 1 END, window_start = excluded.window_start WHERE proofpay_auth_limits.window_start != excluded.window_start OR proofpay_auth_limits.attempts < 10 RETURNING attempts").bind(bucket).first();
  return admitted !== null;
}
