CREATE TABLE IF NOT EXISTS proofpay_auth_limits (
  id TEXT PRIMARY KEY NOT NULL,
  window_start INTEGER NOT NULL,
  attempts INTEGER NOT NULL
);
