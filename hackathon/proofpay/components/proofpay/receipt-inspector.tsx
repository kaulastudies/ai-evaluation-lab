"use client";

import { useEffect, useState } from "react";
import { CircleAlert, FileCheck2, LoaderCircle, RefreshCw } from "lucide-react";
import type { VerificationRecord } from "../../lib/proofpay/types";

export type ReceiptOperation = {
  id: string; title: string; sku: string; merchantId: string; amountCents: number;
  currency: string; providerMode: "rehearsal" | "sandbox"; status: string;
  approvalVersion: number; approvalExpiresAt: number | null;
  orderId: string | null; captureId: string | null; updatedAt: number;
};
type ReceiptEvent = { id: string; type: string; detail: string; createdAt: number };
type Receipt = {
  operation: ReceiptOperation; approvalDigest: string | null;
  verificationRecords: VerificationRecord[]; events: ReceiptEvent[];
};
type Comparison = { field: string; expected: string; observed: string; result: "Same value" | "Different" | "Not recorded" | "Not comparable" };
type Load = { key: string; receipt?: Receipt; error?: string };

const object = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === "object" && !Array.isArray(value);
const strings = (value: Record<string, unknown>, fields: string[]) => fields.every(field => typeof value[field] === "string");
function validVerification(value: unknown): value is VerificationRecord {
  if (!object(value) || value.schemaVersion !== 1 || !["rehearsal", "sandbox"].includes(String(value.mode)) || typeof value.simulated !== "boolean" || !["simulated-provider-lookup", "paypal-sandbox-orders-get"].includes(String(value.source)) || typeof value.checkedAt !== "number" || !Number.isFinite(value.checkedAt) || typeof value.operationId !== "string") return false;
  if (!object(value.order) || !strings(value.order, ["id", "status", "referenceId", "customId", "payeeMerchantId"]) || !object(value.order.amount) || !strings(value.order.amount, ["value", "currency"])) return false;
  return object(value.capture) && strings(value.capture, ["id", "status"]) && typeof value.capture.finalCapture === "boolean" && object(value.capture.amount) && strings(value.capture.amount, ["value", "currency"]);
}
function parseReceipt(value: unknown): Receipt {
  if (!object(value) || !object(value.operation)) throw new Error("The receipt did not contain a purchase record.");
  const op = value.operation;
  if (!strings(op, ["id", "title", "sku", "merchantId", "currency", "status"]) || !["rehearsal", "sandbox"].includes(String(op.providerMode)) || !Number.isSafeInteger(op.amountCents) || Number(op.amountCents) < 0 || !Number.isSafeInteger(op.approvalVersion) || Number(op.approvalVersion) < 1 || typeof op.updatedAt !== "number" || !Number.isFinite(op.updatedAt) || !(op.approvalExpiresAt === null || typeof op.approvalExpiresAt === "number") || !(op.orderId === null || typeof op.orderId === "string") || !(op.captureId === null || typeof op.captureId === "string")) throw new Error("The stored purchase record is incomplete. No comparison was made.");
  if (!(value.approvalDigest === null || typeof value.approvalDigest === "string") || !Array.isArray(value.verificationRecords) || !value.verificationRecords.every(validVerification) || !Array.isArray(value.events)) throw new Error("The receipt format could not be validated. No comparison was made.");
  const events = value.events.filter((event): event is ReceiptEvent => object(event) && strings(event, ["id", "type", "detail"]) && typeof event.createdAt === "number");
  return { operation: op as ReceiptOperation, approvalDigest: value.approvalDigest, verificationRecords: value.verificationRecords, events };
}
export function operationFingerprint(op: ReceiptOperation): string {
  return JSON.stringify([op.id, op.title, op.sku, op.merchantId, op.amountCents, op.currency, op.providerMode, op.status, op.approvalVersion, op.approvalExpiresAt, op.orderId, op.captureId, op.updatedAt]);
}
function decimalMinor(value: string): number | null {
  const match = /^(\d+)\.(\d{2})$/.exec(value);
  if (!match) return null;
  const minor = Number(match[1]) * 100 + Number(match[2]);
  return Number.isSafeInteger(minor) ? minor : null;
}
export function receiptRows(op: ReceiptOperation, record: VerificationRecord | null): Comparison[] {
  const compare = (field: string, expected: string | null, observed: string | null, equal = expected === observed): Comparison => ({
    field, expected: expected ?? "Not assigned", observed: observed ?? "Not recorded",
    result: observed === null ? "Not recorded" : expected === null ? "Not comparable" : equal ? "Same value" : "Different",
  });
  const expectedAmount = `${(op.amountCents / 100).toFixed(2)} ${op.currency}`;
  return [
    compare("Catalogue item", `${op.title} · ${op.sku}`, null),
    compare("Seller", op.merchantId, record?.order.payeeMerchantId ?? null),
    compare("Order amount", expectedAmount, record ? `${record.order.amount.value} ${record.order.amount.currency}` : null, !!record && decimalMinor(record.order.amount.value) === op.amountCents && record.order.amount.currency === op.currency),
    compare("Capture amount", expectedAmount, record ? `${record.capture.amount.value} ${record.capture.amount.currency}` : null, !!record && decimalMinor(record.capture.amount.value) === op.amountCents && record.capture.amount.currency === op.currency),
    compare("Currency", op.currency, record ? `Order: ${record.order.amount.currency}\nCapture: ${record.capture.amount.currency}` : null, !!record && record.order.amount.currency === op.currency && record.capture.amount.currency === op.currency),
    compare("Provider order", op.orderId, record?.order.id ?? null),
    compare("Receipt operation", op.id, record?.operationId ?? null),
    compare("Order reference", op.id, record?.order.referenceId ?? null),
    compare("Order custom reference", op.id, record?.order.customId ?? null),
    compare("Capture reference", op.captureId, record?.capture.id ?? null),
    compare("Order status", "COMPLETED", record?.order.status ?? null),
    compare("Capture status", "COMPLETED", record?.capture.status ?? null),
    compare("Final capture", "Yes", record ? record.capture.finalCapture ? "Yes" : "No" : null),
  ];
}
function findRecordEvent(events: ReceiptEvent[], record: VerificationRecord): string | null {
  for (const event of events) {
    if (event.type !== "PROVIDER_VERIFIED") continue;
    try {
      const stored: unknown = JSON.parse(event.detail);
      if (validVerification(stored) && stored.operationId === record.operationId && stored.checkedAt === record.checkedAt && stored.order.id === record.order.id && stored.capture.id === record.capture.id && stored.source === record.source) return event.id;
    } catch { /* Legacy or malformed details are not a receipt identifier. */ }
  }
  return null;
}

export default function ReceiptInspector({ operation, refreshPurchase }: { operation: ReceiptOperation; refreshPurchase: () => void | Promise<void> }) {
  const [open, setOpen] = useState(false);
  const [generation, setGeneration] = useState(0);
  const [load, setLoad] = useState<Load | null>(null);
  const fingerprint = operationFingerprint(operation);
  const requestKey = `${fingerprint}:${generation}`;
  const operationId = operation.id;

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    let active = true;
    fetch(`/api/operations/${encodeURIComponent(operationId)}/evidence`, { cache: "no-store", signal: controller.signal })
      .then(async response => {
        const body: unknown = await response.json();
        if (!response.ok) throw new Error(object(body) && typeof body.error === "string" ? body.error : "The receipt could not be loaded.");
        const receipt = parseReceipt(body);
        if (receipt.operation.id !== operationId) throw new Error("The receipt belongs to a different purchase. No comparison was made.");
        if (active) setLoad({ key: requestKey, receipt });
      })
      .catch(error => { if (active && !controller.signal.aborted) setLoad({ key: requestKey, error: error instanceof Error ? error.message : "The receipt could not be loaded." }); });
    return () => { active = false; controller.abort(); };
  }, [open, operationId, requestKey]);

  const current = load?.key === requestKey ? load : null;
  const receipt = current?.receipt;
  const stale = !!receipt && operationFingerprint(receipt.operation) !== fingerprint;
  const latest = receipt?.verificationRecords.reduce<VerificationRecord | null>((chosen, record) => !chosen || record.checkedAt > chosen.checkedAt ? record : chosen, null) ?? null;
  const modeMismatch = !!latest && (latest.operationId !== operation.id || latest.mode !== operation.providerMode || latest.simulated !== (operation.providerMode === "rehearsal") || latest.source !== (operation.providerMode === "rehearsal" ? "simulated-provider-lookup" : "paypal-sandbox-orders-get"));
  const eventId = receipt && latest ? findRecordEvent(receipt.events, latest) : null;
  const rows = receipt && !stale && !modeMismatch ? receiptRows(receipt.operation, latest) : [];

  return <details className="record-timeline" open={open} onToggle={event => {
    if (event.target !== event.currentTarget) return;
    const expanded = event.currentTarget.open;
    setOpen(expanded);
    if (expanded) setGeneration(value => value + 1);
  }}>
    <summary style={{ fontSize: 14, fontWeight: 600, width: "100%", color: "var(--ink)" }}>Inspect approved vs observed receipt</summary>
    {open && <div style={{ padding: "8px 0 22px" }}>
      <p className="form-hint" style={{ marginTop: 0 }}>Reads stored evidence only. Opening this section does not call PayPal or change payment state.</p>
      {!current && <div className="inline-note" role="status" style={{ marginTop: 14 }}><LoaderCircle className="spin" size={18}/><p>Loading the stored receipt…</p></div>}
      {current?.error && <div className="inline-note warning" role="alert" style={{ marginTop: 14 }}><CircleAlert size={18}/><div><p>{current.error}</p><button className="text-button" onClick={() => setGeneration(value => value + 1)}><RefreshCw size={14}/>Retry receipt</button></div></div>}
      {receipt && <>
        <div className="record-topline" style={{ marginTop: 16, marginBottom: 12, flexWrap: "wrap", gap: 8 }}><span className="subtle-pill">{receipt.operation.providerMode === "rehearsal" ? "Rehearsal · simulated evidence" : "PayPal sandbox evidence"}</span><span className="subtle-pill">Approval version {receipt.operation.approvalVersion}</span></div>
        {stale ? <div className="inline-note warning"><CircleAlert size={18}/><div><p>The purchase changed after this drawer loaded. No values are marked as matching an older version.</p><button className="text-button" onClick={() => void refreshPurchase()}><RefreshCw size={14}/>Refresh purchase</button></div></div> : modeMismatch ? <div className="inline-note warning"><CircleAlert size={18}/><p>The stored verification has a different operation or evidence source. No comparison is shown.</p></div> : <>
          {receipt.operation.status === "CANCELLED" && <p className="form-hint">This request is cancelled. Any recorded approval has no remaining execution authority.</p>}
          {!receipt.approvalDigest && <p className="form-hint">Owner approval has not been recorded. Values below describe the requested purchase and required completion conditions.</p>}
          {latest ? <div className="inline-note neutral"><FileCheck2 size={18}/><div style={{ minWidth: 0 }}><p><strong>Latest stored verification</strong><br/>{new Date(latest.checkedAt).toLocaleString()}</p><p style={{ overflowWrap: "anywhere", marginTop: 6 }}>Source: {latest.source}<br/>Record: {eventId ?? "Event identifier not available"}</p><p style={{ marginTop: 8 }}>This receipt schema does not store the historical approval version or catalogue item. Equal field values do not establish which approval version was checked.</p></div></div> : <div className="inline-note neutral"><FileCheck2 size={18}/><p><strong>Not yet verified.</strong> No stored provider verification record exists for this purchase. A return URL or configured connection is not payment evidence.</p></div>}
          <div aria-label="Current purchase compared with stored provider fields">{rows.map(row => <section key={row.field} style={{ padding: "14px 0", borderBottom: "1px solid var(--line)" }}>
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 12, marginBottom: 9 }}><h4 style={{ margin: 0, fontSize: 13, fontWeight: 600 }}>{row.field}</h4><span style={{ fontSize: 11, color: row.result === "Different" ? "#8b424b" : "#53647b", textAlign: "right", flexShrink: 0 }}>{row.result}</span></div>
            <dl style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)", gap: 14, margin: 0 }}>
              <div style={{ minWidth: 0 }}><dt style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>{receipt.approvalDigest ? "Current approval / expected" : "Requested / expected"}</dt><dd style={{ margin: 0, fontSize: 13, whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{row.expected}</dd></div>
              <div style={{ minWidth: 0 }}><dt style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>Stored observation</dt><dd style={{ margin: 0, fontSize: 13, whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{row.observed}</dd></div>
            </dl>
          </section>)}</div>
          <p className="form-hint">{receipt.verificationRecords.length} stored verification {receipt.verificationRecords.length === 1 ? "record" : "records"}{receipt.verificationRecords.length > 0 ? "; the latest is shown." : "."} This is an application receipt, not a signed attestation or a new provider lookup.</p>
        </>}
        <button className="text-button" style={{ marginTop: 12 }} onClick={() => setGeneration(value => value + 1)}><RefreshCw size={14}/>Reload stored receipt</button>
      </>}
    </div>}
  </details>;
}
