-- Consumed dispatch allowances. Never remove a failed or uncertain attempt.
CREATE TABLE proofpay_ai_attempts (
  id TEXT PRIMARY KEY NOT NULL,
  workspace_id TEXT NOT NULL UNIQUE REFERENCES proofpay_workspaces(id),
  grant_id TEXT NOT NULL,
  slot INTEGER NOT NULL CHECK (slot BETWEEN 1 AND 10),
  idempotency_key TEXT NOT NULL,
  model TEXT NOT NULL,
  provider TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  grant_expires_at INTEGER NOT NULL,
  UNIQUE (grant_id, slot)
);
