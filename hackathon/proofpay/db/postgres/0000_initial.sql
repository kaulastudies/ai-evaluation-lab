CREATE TABLE proofpay_workspaces (
  id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, mode TEXT NOT NULL,
  currency TEXT NOT NULL, budget_cents INTEGER NOT NULL CHECK (budget_cents >= 0), created_at BIGINT NOT NULL
);
CREATE INDEX proofpay_workspace_owner ON proofpay_workspaces(owner_id);
CREATE TABLE proofpay_sessions (
  owner_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES proofpay_workspaces(id)
);
CREATE TABLE proofpay_operations (
  id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES proofpay_workspaces(id),
  idempotency_key TEXT NOT NULL, request TEXT NOT NULL, agent_label TEXT NOT NULL,
  sku TEXT NOT NULL, title TEXT NOT NULL, amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
  currency TEXT NOT NULL, merchant_id TEXT NOT NULL, mode TEXT NOT NULL,
  ai_source TEXT NOT NULL, rationale TEXT NOT NULL, status TEXT NOT NULL,
  approval_version INTEGER NOT NULL DEFAULT 1 CHECK (approval_version >= 1),
  approval_expires_at BIGINT, approval_digest TEXT,
  create_request_id TEXT NOT NULL UNIQUE, capture_request_id TEXT NOT NULL UNIQUE,
  order_id TEXT UNIQUE, capture_id TEXT UNIQUE, approval_url TEXT,
  created_at BIGINT NOT NULL, updated_at BIGINT NOT NULL,
  UNIQUE(workspace_id,idempotency_key)
);
CREATE INDEX proofpay_operation_workspace ON proofpay_operations(workspace_id);
CREATE TABLE proofpay_events (
  id TEXT PRIMARY KEY, sequence BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
  workspace_id TEXT NOT NULL REFERENCES proofpay_workspaces(id), operation_id TEXT,
  type TEXT NOT NULL, detail TEXT NOT NULL, created_at BIGINT NOT NULL
);
CREATE INDEX proofpay_event_workspace ON proofpay_events(workspace_id);
CREATE TABLE proofpay_rehearsal_orders (
  id TEXT PRIMARY KEY, operation_id TEXT NOT NULL UNIQUE, payload TEXT NOT NULL,
  capture_calls INTEGER NOT NULL DEFAULT 0 CHECK (capture_calls >= 0), created_at BIGINT NOT NULL
);
CREATE TABLE proofpay_auth_limits (
  id TEXT PRIMARY KEY, window_start BIGINT NOT NULL, attempts INTEGER NOT NULL CHECK (attempts >= 0)
);
