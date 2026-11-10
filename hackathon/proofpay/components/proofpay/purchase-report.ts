export type ReportWorkspace = {
  id: string; mode: string; profile?: string; currency: string; budgetCents: number;
  businessName?: string | null; department?: string | null;
};
type ReportOperation = {
  id: string; title: string; sku: string; request: string; aiSource: string;
  status: string; amountCents: number; currency: string; merchantId: string;
  providerMode: string; approvalVersion: number; approvalExpiresAt: number | null;
  orderId: string | null; captureId: string | null; createdAt: number; updatedAt: number;
};

/** Quote every field and neutralize spreadsheet formula prefixes, including hidden whitespace. */
export function csvCell(value: string | number | null | undefined): string {
  const text = value == null ? "" : String(value);
  const safe = /^[\s\u0000-\u001f]*[=+\-@]/.test(text) || /^[\t\r\n]/.test(text) ? `'${text}` : text;
  return `"${safe.replaceAll('"', '""')}"`;
}
const date = (value: number | null) => value !== null && Number.isFinite(value) ? new Date(value).toISOString() : "";
export function purchaseCsv(workspace: ReportWorkspace, operations: ReportOperation[], exportedAt: string): string {
  const headers = ["exported_at", "workspace_id", "business_name", "department", "workspace_mode", "workspace_profile", "workspace_allowance", "workspace_currency", "operation_id", "purchase", "catalogue_item", "request", "proposal_source", "status", "amount", "currency", "seller_id", "provider_mode", "approval_version", "approval_expires_at", "provider_order_id", "capture_id", "created_at", "updated_at"];
  const rows = operations.map(op => [exportedAt, workspace.id, workspace.businessName, workspace.department, workspace.mode, workspace.profile ?? "standard", (workspace.budgetCents / 100).toFixed(2), workspace.currency, op.id, op.title, op.sku, op.request, op.aiSource, op.status, (op.amountCents / 100).toFixed(2), op.currency, op.merchantId, op.providerMode, op.approvalVersion, date(op.approvalExpiresAt), op.orderId, op.captureId, date(op.createdAt), date(op.updatedAt)]);
  return "\uFEFF" + [headers, ...rows].map(row => row.map(csvCell).join(",")).join("\r\n") + "\r\n";
}
