-- Business settings apply only when creating future workspaces. Historical
-- workspaces keep their exact budget and have no invented business identity.
CREATE TABLE proofpay_business_profiles (
  owner_id TEXT PRIMARY KEY,
  business_name TEXT NOT NULL CHECK (length(business_name) BETWEEN 1 AND 120),
  department TEXT NOT NULL CHECK (length(department) BETWEEN 1 AND 80),
  default_budget_cents INTEGER NOT NULL CHECK (default_budget_cents BETWEEN 100 AND 100000000),
  version INTEGER NOT NULL CHECK (version >= 1),
  updated_at BIGINT NOT NULL
);
ALTER TABLE proofpay_workspaces ADD COLUMN business_name TEXT;
ALTER TABLE proofpay_workspaces ADD COLUMN department TEXT;
ALTER TABLE proofpay_workspaces ADD COLUMN business_profile_version INTEGER;
