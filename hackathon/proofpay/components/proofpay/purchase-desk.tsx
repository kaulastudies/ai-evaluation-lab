"use client";

import Link from "next/link";
import ReceiptInspector from "./receipt-inspector";
import { BusinessSettings, WorkspaceHistory, type BusinessProfile } from "./business-workspace";
import { purchaseCsv } from "./purchase-report";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowDownToLine, ArrowRight, ArrowUpRight, Check, CheckCheck, Building2, History, ChevronRight, CircleAlert, FileCheck2, FlaskConical, LayoutDashboard, ListChecks, LoaderCircle, LockKeyhole, LogOut, PlugZap, Plus, RefreshCw, Search, SearchCheck, ShieldCheck, ShoppingBag, SlidersHorizontal, Sparkles, WalletCards, X } from "lucide-react";

type Mode = "rehearsal" | "sandbox";
type Status = "PROPOSED" | "BUDGET_BLOCKED" | "APPROVED" | "CREATE_DISPATCHED" | "CREATE_UNKNOWN" | "ORDER_READY" | "CAPTURE_DISPATCHED" | "UNKNOWN" | "REVIEW" | "CONFIRMED" | "CANCELLED";
type Operation = {
  id: string; request: string; agentLabel: string; sku: string; title: string;
  amountCents: number; currency: string; merchantId: string; status: Status;
  approvalVersion: number; approvalExpiresAt: number | null; orderId: string | null;
  captureId: string | null; approvalUrl: string | null; providerMode: Mode;
  aiSource: "rehearsal-seed" | "rehearsal-rule" | "sandbox-diagnostic" | "model"; rationale: string;
  createdAt: number; updatedAt: number;
};
type EvidenceEvent = { id: string; operationId: string | null; type: string; detail: string; createdAt: number };
type DeskState = {
  workspace: { id: string; mode: Mode; profile?: "standard" | "sandbox-diagnostic"; currency: string; budgetCents: number; reservedCents: number; committedCents: number; availableCents: number; businessName: string | null; department: string | null; businessProfileVersion: number | null } | null;
  capabilities: { sandboxReady: boolean; aiReady: boolean };
  catalogue: { sku: string; title: string; description: string; amountCents: number; currency: string }[];
  operations: Operation[]; events: EvidenceEvent[];
};
type ApiEnvelope = { state?: DeskState; error?: string; code?: string };
type PayPalRedirect = { kind: "returned" | "cancelled" | "unmatched"; operationId: string | null; title: string; message: string };
const labels: Record<Status, string> = {
  CANCELLED: "Request cancelled", PROPOSED: "Needs approval", BUDGET_BLOCKED: "Over allowance", APPROVED: "Allowance reserved",
  CREATE_DISPATCHED: "Creating order", CREATE_UNKNOWN: "Needs verification", ORDER_READY: "Awaiting buyer approval",
  CAPTURE_DISPATCHED: "Needs verification", UNKNOWN: "Needs verification", REVIEW: "Needs review", CONFIRMED: "Payment confirmed",
};
type View = "overview" | "purchases" | "approvals" | "evidence" | "controls" | "connections" | "business" | "history";
const viewNames: Record<View, string> = { overview: "Overview", purchases: "Purchases", approvals: "Approvals", evidence: "Evidence", controls: "Controls", connections: "Connections", business: "Business settings", history: "Workspace history" };
const heldStates: Status[] = ["APPROVED", "CREATE_DISPATCHED", "CREATE_UNKNOWN", "ORDER_READY", "CAPTURE_DISPATCHED", "UNKNOWN", "REVIEW"];
const uncertainStates: Status[] = ["CREATE_DISPATCHED", "CREATE_UNKNOWN", "CAPTURE_DISPATCHED", "UNKNOWN", "REVIEW"];
const statusLabel = (op: Operation) => op.status === "CONFIRMED" && op.providerMode === "rehearsal" ? "Simulated payment confirmed" : op.status === "ORDER_READY" && op.providerMode === "rehearsal" ? "Ready for simulated capture" : labels[op.status];
const time = (v: number) => new Date(v).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
const money = (v: number, currency = "USD") => new Intl.NumberFormat("en-US", { style: "currency", currency }).format(v / 100);
const titleCase = (s: string) => s.toLowerCase().replaceAll("_", " ").replace(/^\w/, x => x.toUpperCase());
class WorkspaceError extends Error {
  constructor(message: string, public status: number, public code?: string) { super(message); }
}
async function readWorkspace(): Promise<DeskState> {
  const response = await fetch("/api/state", { cache: "no-store" });
  const result = await response.json() as ApiEnvelope;
  if (!response.ok || !result.state) throw new WorkspaceError(result.error || "Unable to load the workspace.", response.status, result.code);
  return result.state;
}
function safeApprovalUrl(value?: string | null) {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" && ["sandbox.paypal.com", "www.sandbox.paypal.com"].includes(url.hostname) && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}
function resolvePayPalRedirect(search: string, operations: Operation[]): PayPalRedirect | null {
  const params = new URLSearchParams(search);
  const returned = params.getAll("paypal_return"), cancelled = params.getAll("paypal_cancel");
  if (!returned.length && !cancelled.length) return null;
  const ambiguous = returned.length + cancelled.length !== 1;
  const operationId = returned[0] ?? cancelled[0];
  const operation = ambiguous ? undefined : operations.find(op => op.id === operationId && op.providerMode === "sandbox");
  if (!operation) return {
    kind: "unmatched", operationId: null, title: "PayPal return could not be matched",
    message: "This link does not identify one sandbox purchase in the current workspace. No purchase was selected or changed. Review your purchase records before continuing.",
  };
  return cancelled.length ? {
    kind: "cancelled", operationId: operation.id, title: "Cancellation return received",
    message: `Selected ${operation.title}. This link does not prove that an order or payment was cancelled. The recorded status and any reservation are unchanged.`,
  } : {
    kind: "returned", operationId: operation.id, title: "PayPal return received",
    message: `Selected ${operation.title}. Returning from PayPal does not confirm buyer approval or payment. Follow the recorded status below; only verified provider evidence can confirm payment.`,
  };
}
function canRenewApproval(operation: Operation, now: number | null): boolean {
  return now !== null && operation.approvalExpiresAt !== null && operation.approvalExpiresAt <= now && !operation.captureId && (operation.status === "APPROVED" || operation.status === "ORDER_READY");
}


function proposalEventSummary(detail: string): string | null {
  try {
    const record: unknown = JSON.parse(detail);
    if (!record || typeof record !== "object" || Array.isArray(record)) return null;
    const proposal = record as Record<string, unknown>;
    const sources: Record<string, string> = { model: "AI model", "rehearsal-rule": "Rehearsal rule", "rehearsal-seed": "Rehearsal sample", "sandbox-diagnostic": "Sandbox diagnostic (no AI)" };
    if (typeof proposal.source !== "string" || !Object.hasOwn(sources, proposal.source) || typeof proposal.sku !== "string" || typeof proposal.rationale !== "string") return null;
    return `${sources[proposal.source]} selected ${proposal.sku}. ${proposal.rationale}`;
  } catch { return null; }
}
function EvidenceDetail({ event }: { event: EvidenceEvent }) {
  const summary = event.type === "PROPOSAL_CREATED" ? proposalEventSummary(event.detail) : null;
  if (summary) return <p className="muted-text">{summary}</p>;
  return <details><summary>Inspect record</summary><pre>{event.detail}</pre></details>;
}

export default function PurchaseDesk() {
  const [data, setData] = useState<DeskState | null>(null);
  const [business, setBusiness] = useState<BusinessProfile | null>(null);
  const [mode, setMode] = useState<Mode>("rehearsal");
  const [view, setView] = useState<View>("overview");
  const [search, setSearch] = useState("");
  const [overlay, setOverlay] = useState<"purchase" | "request" | "about" | null>(null);
  const [cancelConfirm, setCancelConfirm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [request, setRequest] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [fault, setFault] = useState(false);
  const [filter, setFilter] = useState("all");
  const [authRequired, setAuthRequired] = useState(false);
  const [setupPending, setSetupPending] = useState(false);
  const [ownerKey, setOwnerKey] = useState("");
  const [payPalRedirect, setPayPalRedirect] = useState<PayPalRedirect | null>(null);
  const [clock, setClock] = useState<number | null>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const busyRef = useRef(false);
  const draftKey = useRef<{ request: string; key: string } | null>(null);
  const requestSequence = useRef(0);
  const redirectHandled = useRef(false);
  const clearSessionView = useCallback(() => {
    setData(null); setBusiness(null); setAuthRequired(true); setSetupPending(false); setSelectedId(null); setOverlay(null);
    setOwnerKey(""); setRequest(""); setSearch(""); setCancelConfirm(false);
    setPayPalRedirect(null); draftKey.current = null; redirectHandled.current = false;
  }, []);
  const setSettingsSaving = useCallback((saving: boolean) => {
    busyRef.current = saving;
    if (saving) ++requestSequence.current;
    setBusy(saving ? "business-save" : null);
  }, []);
  const applyLoadedState = useCallback((state: DeskState) => {
    setData(state); setAuthRequired(false); setSetupPending(false);
    if (state.workspace) setMode(state.workspace.mode);
    if (!redirectHandled.current) {
      redirectHandled.current = true;
      const redirect = resolvePayPalRedirect(window.location.search, state.operations);
      if (redirect) {
        setPayPalRedirect(redirect);
        setSelectedId(redirect.operationId ?? "");
        setView("purchases"); setFilter("all");
        if (redirect.operationId) setOverlay("purchase");
      }
    }
  }, []);

  const refresh = useCallback(async () => {
    const sequence = ++requestSequence.current;
    try {
      const state = await readWorkspace();
      if (sequence === requestSequence.current) applyLoadedState(state);
      return state;
    } catch (error) {
      if (sequence === requestSequence.current && error instanceof WorkspaceError) {
        if (error.status === 401) clearSessionView();
        if (error.code === "AUTH_NOT_CONFIGURED") { setData(null); setBusiness(null); setAuthRequired(false); setSetupPending(true); }
      }
      throw error;
    }
  }, [applyLoadedState, clearSessionView]);
  useEffect(() => {
    let active = true;
    const sequence = ++requestSequence.current;
    readWorkspace().then(state => {
      if (!active || sequence !== requestSequence.current) return;
      applyLoadedState(state);
    }).catch((e: Error) => {
      if (!active || sequence !== requestSequence.current) return;
      setError(e.message); setAuthRequired(e instanceof WorkspaceError && e.status === 401); setSetupPending(e instanceof WorkspaceError && e.code === "AUTH_NOT_CONFIGURED");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [applyLoadedState]);
  const authenticated = !!data && !authRequired;
  useEffect(() => {
    if (!authenticated) return;
    const controller = new AbortController();
    fetch("/api/business", { cache: "no-store", signal: controller.signal }).then(async response => {
      const result = await response.json() as { business?: BusinessProfile };
      if (controller.signal.aborted) return;
      if (response.status === 401) clearSessionView();
      if (response.ok && result.business) setBusiness(current => !current || result.business!.version >= current.version ? result.business! : current);
    }).catch(() => {});
    return () => controller.abort();
  }, [authenticated, clearSessionView]);
  useEffect(() => {
    const onFocus = () => { if (!busyRef.current) refresh().catch(() => {}); };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [refresh]);
  useEffect(() => {
    if (!overlay) return;
    const previous = document.activeElement as HTMLElement | null;
    const dialog = dialogRef.current;
    const focusable = () => dialog?.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input:not([disabled]), textarea:not([disabled]), select:not([disabled]), summary, [tabindex="0"]');
    focusable()?.[0]?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOverlay(null);
      const buttons = focusable();
      if (event.key !== "Tab" || !buttons?.length) return;
      const first = buttons[0], last = buttons[buttons.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", onKey); document.body.style.overflow = previousOverflow; requestAnimationFrame(() => { if (!dialog?.isConnected) { if (previous?.isConnected) previous.focus(); else document.getElementById("page-title")?.focus(); } }); };
  }, [overlay]);

  const ops = data?.operations || [];
  const selected = ops.find(o => o.id === selectedId);
  const approvalExpiry = selected?.approvalExpiresAt;
  const approvalExpired = approvalExpiry != null && clock !== null && approvalExpiry <= clock;
  const approvalRenewable = selected ? canRenewApproval(selected, clock) : false;
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const updateClock = () => {
      const now = Date.now();
      setClock(now);
      const futureExpiries = (data?.operations || [])
        .filter(op => (op.status === "APPROVED" || op.status === "ORDER_READY") && op.approvalExpiresAt !== null && op.approvalExpiresAt > now)
        .map(op => op.approvalExpiresAt as number);
      if (futureExpiries.length) timer = setTimeout(updateClock, Math.min(Math.max(0, Math.min(...futureExpiries) - now) + 5, 2_147_483_647));
    };
    timer = setTimeout(updateClock, 0);
    return () => clearTimeout(timer);
  }, [data?.operations]);
  const paypalReady = data?.capabilities.sandboxReady ?? false;
  const aiReady = data?.capabilities.aiReady ?? false;
  const sandboxReady = paypalReady && aiReady;
  const ws = data?.workspace;
  const businessName = ws ? ws.businessName || "Your business" : business?.businessName || "Your business";
  const businessDepartment = ws ? ws.department : business?.department;
  const businessInitials = businessName === "Your business" ? "PP" : businessName.trim().split(/\s+/).slice(0, 2).map(word => word[0]).join("").toUpperCase();
  const isDiagnostic = ws?.profile === "sandbox-diagnostic";
  const total = ws?.budgetCents ?? 0;
  const reserved = ws?.reservedCents ?? 0;
  const paid = ws?.committedCents ?? 0;
  const available = ws?.availableCents ?? 0;
  const unresolved = ops.filter(o => uncertainStates.includes(o.status));
  const pending = ops.filter(o => o.status === "PROPOSED");
  const renewals = ops.filter(op => canRenewApproval(op, clock));
  const blocked = ops.filter(op => op.status === "BUDGET_BLOCKED");
  const approvalQueue = ops.filter(op => op.status === "PROPOSED" || op.status === "BUDGET_BLOCKED" || canRenewApproval(op, clock));
  const needle = search.trim().toLowerCase();
  const pool = view === "approvals" ? approvalQueue : ops;
  const displayed = pool.filter(op => (!needle || [op.title, op.request, op.sku, op.id, op.orderId, op.captureId, statusLabel(op)].filter(Boolean).join(" ").toLowerCase().includes(needle)) && (filter === "all" || (filter === "approval" ? op.status === "PROPOSED" : filter === "attention" ? uncertainStates.includes(op.status) : filter === "reserved" ? heldStates.includes(op.status) : filter === "renewal" ? canRenewApproval(op, clock) : filter === "blocked" ? op.status === "BUDGET_BLOCKED" : filter === "cancelled" ? op.status === "CANCELLED" : op.status === "CONFIRMED")));
  const hasSandboxHold = ws?.mode === "sandbox" && ops.some(op => heldStates.includes(op.status));
  const canCancel = !!selected && ["PROPOSED", "BUDGET_BLOCKED", "APPROVED"].includes(selected.status) && !selected.orderId && !selected.captureId;
  const events = data?.events || [];
  const displayedEvents = events.filter(event => !needle || [event.type, event.detail, ops.find(op => op.id === event.operationId)?.title].filter(Boolean).join(" ").toLowerCase().includes(needle));
  const eventList = selected ? (data?.events || []).filter(e => e.operationId === selected.id) : [];
  const selectedUrl = safeApprovalUrl(selected?.approvalUrl);

  async function signIn() {
    if (busyRef.current || !ownerKey) return;
    const password = ownerKey;
    setOwnerKey(""); setError(""); setNotice(""); setBusy("login");
    busyRef.current = true; ++requestSequence.current;
    try {
      const response = await fetch("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password }) });
      const result = await response.json() as { ok?: boolean; error?: string };
      if (!response.ok || result.ok !== true) throw new Error(result.error || "Owner sign-in could not be completed.");
      setAuthRequired(false); setView("overview"); setFilter("all");
      await refresh();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Owner sign-in could not be completed.");
    } finally { busyRef.current = false; setBusy(null); }
  }
  async function signOut() {
    if (busyRef.current) return;
    busyRef.current = true; ++requestSequence.current;
    setBusy("logout"); setError(""); setNotice("");
    try {
      const response = await fetch("/api/auth/logout", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      const result = await response.json() as { ok?: boolean; error?: string };
      if (!response.ok || result.ok !== true) throw new Error(result.error || "Sign-out could not be completed. Your session may still be active.");
      clearSessionView(); setNotice("Signed out of the owner workspace.");
    } catch (error) { setError(error instanceof Error ? error.message : "Sign-out could not be completed."); }
    finally { busyRef.current = false; setBusy(null); }
  }
  async function act(key: string, path: string, body: Record<string, unknown> = {}) {
    if (busyRef.current) return;
    busyRef.current = true; ++requestSequence.current;
    setBusy(key); setError(""); setNotice("");
    try {
      const payload = body;
      const res = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const json = await res.json() as ApiEnvelope;
      if (json.state) {
        setData(json.state);
        if (json.state.workspace) setMode(json.state.workspace.mode);
        const newOperation = json.state.operations.find(op => !ops.some(previous => previous.id === op.id));
        if (newOperation) setSelectedId(newOperation.id);
      }
      if (!res.ok) {
        if (res.status === 401) clearSessionView();
        throw new Error(json.error || "The action could not be completed.");
      }
      if (!json.state) await refresh();
      setAuthRequired(false);
      return json;
    } catch (e) {
      setError(e instanceof Error ? e.message : "The action could not be completed.");
      await refresh().catch(() => {});
    } finally { busyRef.current = false; setBusy(null); }
  }
  const operationAction = (operation: Operation, action: string, extra: Record<string, unknown> = {}) => act(operation.id, `/api/operations/${encodeURIComponent(operation.id)}/${action}`, action === "reconcile" ? {} : { approvalVersion: operation.approvalVersion, ...extra });
  const renewApproval = () => {
    if (!selected || !approvalRenewable) return;
    return operationAction(selected, "renew-approval").then(result => {
      if (result) setNotice("Owner approval renewed for the same item, seller, amount and currency. The reservation is unchanged; no payment was dispatched by renewal.");
    });
  };
  const propose = () => {
    if (isDiagnostic) { setError("This diagnostic uses its fixed catalogue request. Start a standard sandbox workspace for AI proposals."); return; }
    if (!draftKey.current || draftKey.current.request !== request) draftKey.current = { request, key: crypto.randomUUID() };
    return act("propose", "/api/proposals", { request, mode, idempotencyKey: draftKey.current.key }).then(result => {
      if (result) { setRequest(""); draftKey.current = null; setView("purchases"); setFilter("all"); setSearch(""); setOverlay("purchase"); }
    });
  };
  const start = () => act("start", "/api/rehearsal/start").then(j => { if (j) { setView("purchases"); setFilter("all"); setSearch(""); setOverlay(null); setFault(false); setPayPalRedirect(null); setNotice("A new rehearsal workspace is ready. All purchases and provider outcomes in this workspace are simulated."); } });
  const exportEvidence = async () => {
    if (busyRef.current || !ops.length) return;
    busyRef.current = true; ++requestSequence.current; setBusy("export"); setError("");
    try {
      const records = await Promise.all(ops.map(async operation => {
        const response = await fetch(`/api/operations/${encodeURIComponent(operation.id)}/evidence`, { cache: "no-store" });
        const record = await response.json() as { error?: string };
        if (!response.ok) throw new Error(record.error || "Unable to export the complete evidence.");
        return record;
      }));
      const artifact = {
        exportedAt: new Date().toISOString(), source: "ProofPay Purchase Desk", mode,
        evidenceScope: mode === "rehearsal" ? "Simulated provider. Not PayPal sandbox evidence." : "Provider evidence must be checked against the recorded outcome.",
        state: data, records,
      };
      const url = URL.createObjectURL(new Blob([JSON.stringify(artifact, null, 2)], { type: "application/json" }));
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = `proofpay-${mode}-evidence.json`; anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setNotice(`Exported ${records.length} purchase records with request IDs and approval digests. ${mode === "rehearsal" ? "These are simulated records." : "Review each recorded provider outcome."}`);
    } catch (e) { setError(e instanceof Error ? e.message : "Evidence export failed."); }
    finally { busyRef.current = false; setBusy(null); }
  };

  const exportPurchaseReport = () => {
    if (busyRef.current || !ws || !ops.length) return;
    const exportedAt = new Date().toISOString();
    const url = URL.createObjectURL(new Blob([purchaseCsv(ws, ops, exportedAt)], { type: "text/csv;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = url; anchor.download = `proofpay-${ws.mode}-purchases-${ws.id.slice(0, 8)}.csv`; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setNotice(`Prepared a CSV download with ${ops.length} purchases from this ${ws.mode === "rehearsal" ? "simulated rehearsal" : "PayPal sandbox"} workspace. The report uses the current loaded records, includes all statuses, and is not a provider receipt or invoice.`);
  };
  const selectWorkspace = async (id: string): Promise<boolean> => {
    const result = await act("workspace-select", "/api/workspaces/select", { workspaceId: id });
    if (!result) return false;
    setSelectedId(null); setRequest(""); draftKey.current = null; setFault(false); setPayPalRedirect(null);
    navigate("overview"); setNotice("Saved workspace opened. Its original allowance, purchases and business snapshot are unchanged.");
    return true;
  };

  const navigate = (next: View, nextFilter = "all") => {
    setView(next); setFilter(nextFilter); setSearch(""); setOverlay(null); setCancelConfirm(false);
    requestAnimationFrame(() => {
      window.scrollTo({ top: 0, behavior: "instant" });
      document.getElementById("page-title")?.focus({ preventScroll: true });
    });
  };
  const inspect = (operation: Operation) => { setSelectedId(operation.id); setFault(false); setCancelConfirm(false); setOverlay("purchase"); };
  const newRequest = () => { setOverlay("request"); setCancelConfirm(false); };
  const refreshNow = async () => {
    if (busyRef.current) return;
    busyRef.current = true; setBusy("refresh");
    try { await refresh(); setError(""); } catch (e) { setError(e instanceof Error ? e.message : "Unable to refresh."); }
    finally { busyRef.current = false; setBusy(null); }
  };
  const cancelRequest = async () => {
    if (!selected || !canCancel) return;
    const result = await operationAction(selected, "cancel");
    if (result) { setCancelConfirm(false); setNotice("Request cancelled before provider dispatch. Any reservation for this request was released; its evidence is retained. No refund or provider-order cancellation was performed."); }
  };
  const navItems = [{id:"overview", icon:LayoutDashboard}, {id:"purchases", icon:ShoppingBag}, {id:"approvals", icon:ListChecks}, {id:"evidence", icon:FileCheck2}, {id:"controls", icon:ShieldCheck}, {id:"connections", icon:PlugZap}, {id:"business", icon:Building2}, {id:"history", icon:History}] as const;
  const descriptions: Record<View,string> = {
    overview:"A clear view of what’s requested, reserved and paid.", purchases:"Every purchase, from the original request to a verified outcome.",
    approvals:"Review the exact item, seller and amount before you authorize spending.", evidence:"Trace each decision and provider outcome back to its purchase.",
    controls:"The rules currently enforced by this purchase desk. Read only.", connections:"Provider configuration, workspace mode and integration evidence.",
    business:"Manage the business identity and default allowance for new workspaces.", history:"Saved purchase workspaces, each with its own allowance and records.",
  };
  const renderRows = (rows: Operation[]) => <>
    <div className="mobile-purchase-list" role="list" aria-label="Purchase records">{rows.map(op => <div role="listitem" key={op.id}><button className="mobile-purchase-card" onClick={() => inspect(op)} aria-label={`View ${op.title}, ${money(op.amountCents, op.currency)}, ${statusLabel(op)}`}>
      <span className="mobile-purchase-heading"><span className="purchase-icon"><ShoppingBag size={18}/></span><strong>{op.title}</strong><ChevronRight size={18}/></span>
      <span className="mobile-purchase-meta">{op.aiSource === "model" ? "AI proposal" : op.aiSource === "sandbox-diagnostic" ? "Diagnostic · no AI" : "Rehearsal"} · {new Date(op.createdAt).toLocaleDateString(undefined, {month:"short", day:"numeric"})} · {op.id.slice(0,8)}</span>
      <span className="mobile-purchase-result"><span className={`status ${op.status.toLowerCase()}`}>{statusLabel(op)}</span><strong>{money(op.amountCents, op.currency)}</strong></span>
    </button></div>)}</div>
    <div className="purchase-table-wrap" role="region" aria-label="Purchase records, scroll horizontally for all columns" tabIndex={0}><table className="purchase-table"><thead><tr><th>Purchase</th><th className="source-column">Source</th><th>Status</th><th className="amount-cell">Amount</th><th><span className="sr-only">Open record</span></th></tr></thead><tbody>{rows.map(op=><tr key={op.id}><td><button className="purchase-name" onClick={()=>inspect(op)}><span className="purchase-icon"><ShoppingBag size={17}/></span><span><strong>{op.title}</strong><small>{op.id.slice(0,8)} · {new Date(op.createdAt).toLocaleDateString(undefined,{month:"short",day:"numeric"})}</small></span></button></td><td className="source-column"><span className="source-label">{op.aiSource==="model"?<Sparkles size={13}/>:<FlaskConical size={13}/>} {op.aiSource==="model"?"AI proposal":op.aiSource==="sandbox-diagnostic"?"Diagnostic · no AI":"Rehearsal"}</span></td><td><span className={`status ${op.status.toLowerCase()}`}>{statusLabel(op)}</span></td><td className="amount-cell">{money(op.amountCents,op.currency)}</td><td><button className="icon-btn" aria-label={`View ${op.title} purchase ${op.id.slice(0,8)}`} onClick={()=>inspect(op)}><ChevronRight size={17}/></button></td></tr>)}</tbody></table></div></>;
  const empty = (title: string, description: string) => <div className="empty-state"><span className="empty-symbol"><ShoppingBag size={26}/></span><h3>{title}</h3><p>{description}</p></div>;
  const alerts = <>{error && <div className="message error" role="alert"><CircleAlert size={18}/><div><strong>{authRequired?"Owner sign-in required":"Action needs attention"}</strong><p>{error}</p></div><button aria-label="Dismiss error" onClick={()=>setError("")}><X size={16}/></button></div>}{notice && <div className="message success" role="status"><Check size={18}/><p>{notice}</p><button aria-label="Dismiss notice" onClick={()=>setNotice("")}><X size={16}/></button></div>}</>;
  return <div className="desk-shell">
    <a className="skip-link" href="#main-content">Skip to workspace</a>
    <aside className="sidebar" inert={overlay !== null}>
      <Link className="brand" href="/" aria-label="ProofPay home"><span className="brand-symbol"><CheckCheck size={25}/></span><span>ProofPay<small>PAYMENT OPERATIONS</small></span></Link>
      <div className="workspace-switch"><span className="workspace-monogram">{businessInitials}</span><div><strong title={businessName}>{businessName}</strong><small title={businessDepartment || "Owner workspace"}>{businessDepartment || "Owner workspace"}</small></div><LockKeyhole size={14}/></div>
      <p className="nav-heading">WORKSPACE</p>
      <nav aria-label="Workspace navigation">{navItems.map(({id,icon:Icon})=><button key={id} title={viewNames[id]} aria-label={viewNames[id]} className={`nav-item ${view===id?"active":""}`} aria-current={view===id?"page":undefined} disabled={busy==="business-save"} onClick={()=>navigate(id)}><Icon size={18}/><span>{viewNames[id]}</span>{id==="approvals" && approvalQueue.length>0 && <em>{approvalQueue.length}</em>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-principle"><ShieldCheck size={20}/><strong>Intent. Approval. Evidence.</strong><p>Every payment stays connected to the decision behind it.</p></div><button onClick={()=>setOverlay("about")}><span className="team-avatar">AL</span><span>AI Evaluation Lab<small>ProofPay prototype</small></span><ArrowUpRight size={14}/></button></div>
    </aside>
    <div className="main-shell" inert={overlay !== null}>
      <header className="topbar"><div className="breadcrumb"><span title={businessName}>{businessName}</span><ChevronRight size={14}/><strong>{viewNames[view]}</strong></div><div className="topbar-right"><span className={`environment-pill ${mode}`}><span/>{ws ? isDiagnostic?"PayPal diagnostic":mode==="rehearsal"?"Rehearsal · simulated":"PayPal sandbox":"Sandbox prototype"}</span><button className="icon-btn" aria-label="Refresh workspace" title="Refresh workspace" disabled={!!busy || loading} onClick={refreshNow}><RefreshCw size={16} className={busy==="refresh"?"spin":""}/></button>{data && !authRequired && <button className="icon-btn" aria-label="Sign out of owner workspace" title="Sign out" disabled={!!busy} onClick={signOut}>{busy==="logout"?<LoaderCircle className="spin" size={16}/>:<LogOut size={17}/>}</button>}{data && !authRequired && <span className="owner-avatar" title="Workspace owner">{businessInitials}</span>}</div></header>
      <main id="main-content" tabIndex={-1} aria-busy={loading || !!busy}>
        <div className="page-heading"><div><p className="eyebrow">BUSINESS PURCHASE DESK</p><h1 id="page-title" tabIndex={-1}>{view==="overview"?businessName:viewNames[view]}</h1><p>{descriptions[view]}</p></div><div className="heading-actions"><button className="btn btn-outline" onClick={exportEvidence} disabled={!ops.length || !!busy}>{busy==="export"?<LoaderCircle size={16} className="spin"/>:<ArrowDownToLine size={16}/>}<span>Export evidence</span></button>{ws && !isDiagnostic && <button className="btn btn-primary" onClick={newRequest} disabled={!!busy || authRequired}><Plus size={17}/>New request</button>}</div></div>
        {alerts}
        {payPalRedirect && <div className="message info" role="status"><SearchCheck size={19}/><div><strong>{payPalRedirect.title}</strong><p>{payPalRedirect.message}</p></div><button aria-label="Dismiss PayPal return notice" onClick={()=>setPayPalRedirect(null)}><X size={16}/></button></div>}
        {ws && <div className={`mode-banner ${mode}`}><FlaskConical size={17}/><p><strong>{isDiagnostic?"PayPal sandbox diagnostic":mode==="rehearsal"?"Rehearsal workspace":"PayPal sandbox workspace"}</strong><span>{isDiagnostic?"Fixed-catalogue payment test. No AI model was called. Virtual funds only; owner approval and verified PayPal evidence are still required.":mode==="rehearsal"?"Sample proposals and simulated payments. No live AI or PayPal results.":"Virtual test funds only. Payment confirmation requires verified provider evidence."}</span></p><button onClick={()=>navigate("connections")}>Connections<ArrowUpRight size={14}/></button></div>}
        {loading ? <section className="card loading-state" role="status"><LoaderCircle size={27} className="spin"/><h2>Loading your workspace</h2><p>Retrieving requests, allowance and saved evidence.</p></section> : !data ? authRequired ? <section className="card owner-login" aria-labelledby="owner-login-title"><span className="queue-icon blue"><LockKeyhole size={23}/></span><h2 id="owner-login-title">Sign in to your workspace</h2><p>Only the workspace owner can view purchase records and authorize payments.</p><form onSubmit={event=>{event.preventDefault();void signIn();}}><label className="form-label" htmlFor="owner-access-key">Owner access key</label><input id="owner-access-key" name="password" type="password" autoComplete="off" autoCapitalize="none" spellCheck={false} value={ownerKey} onChange={event=>setOwnerKey(event.target.value)} aria-describedby="owner-key-help" required disabled={!!busy}/><p id="owner-key-help" className="form-hint">Use the owner key configured for this workspace.</p><button type="submit" className="btn btn-primary full" disabled={!!busy || !ownerKey}>{busy==="login"?<LoaderCircle className="spin" size={16}/>:<LockKeyhole size={16}/>} {busy==="login"?"Signing in…":"Sign in"}</button></form></section> : <section className="card">{empty(setupPending?"Workspace setup pending":"Workspace unavailable",setupPending?"Secure owner sign-in must be configured before records can load. Setup is completed by the deployment owner; no access keys or purchase records can be added here.":"Your saved records could not be loaded. Check the message above, then refresh to try again.")}<div className="empty-actions"><button className="btn btn-outline" onClick={refreshNow}>{setupPending?"Check setup again":"Try again"}<RefreshCw size={15}/></button></div></section> : <>
        {view==="business" && <BusinessSettings busy={!!busy} onSaved={setBusiness} onUnauthorized={clearSessionView} onSavingChange={setSettingsSaving}/>}
        {view==="history" && <WorkspaceHistory activeWorkspaceId={ws?.id || null} busy={!!busy} onSelect={selectWorkspace} onUnauthorized={clearSessionView}/>}
        {view==="overview" && <>
          <div className="business-context"><div><Building2 size={18}/><span>{ws ? ws.businessProfileVersion == null ? "This workspace has no saved business profile." : `${businessDepartment} · Business profile v${ws.businessProfileVersion}` : business?.configured ? `${business.department} · Saved business profile` : "Set up your business identity and default allowance."}</span></div><button className="text-button" onClick={()=>navigate("business")}>{business?.configured?"Business settings":"Set up business"}<ArrowRight size={15}/></button></div>
          <section className={`metric-grid ${total >= 1000000 ? "large-allowance" : ""}`} aria-label="Current allowance and purchase status">
            <article className="metric-card featured"><div><span>Available</span><WalletCards size={17}/></div><strong>{ws?money(available):"—"}</strong><small>{ws?`of ${money(total)} shared allowance`:"No workspace started"}</small></article>
            <article className="metric-card"><div><span>Reserved</span><LockKeyhole size={17}/></div><strong>{ws?money(reserved):"—"}</strong><small>Held for approved purchases</small></article>
            <article className="metric-card"><div><span>Paid</span><CheckCheck size={18}/></div><strong>{ws?money(paid):"—"}</strong><small>{mode==="rehearsal"?"Confirmed by simulated provider":"Confirmed from provider evidence"}</small></article>
            <button className={`metric-card metric-link ${unresolved.length?"needs-attention":""}`} onClick={()=>navigate("purchases","attention")}><div><span>Needs verification</span><SearchCheck size={18}/></div><strong>{ws?unresolved.length:"—"}<ArrowUpRight size={19}/></strong><small>Uncertain outcomes stay reserved</small></button>
          </section>
          {!ws ? <section className="card onboarding"><div><span className="section-kicker">YOUR FIRST WORKSPACE</span><h2>Start with a controlled purchase.</h2><p>Two sample requests with your saved default allowance. Walk through approval, a missing capture response and a checked outcome.</p><div className="onboarding-steps"><span><span>1</span>Review requests</span><span><span>2</span>Reserve allowance</span><span><span>3</span>Verify the outcome</span></div><button className="btn btn-primary" onClick={start} disabled={!!busy || authRequired}><FlaskConical size={16}/>{busy==="start"?"Starting rehearsal…":"Start rehearsal"}<ArrowRight size={16}/></button><small>All rehearsal proposals and payment records are simulated.</small></div><div className="onboarding-art" aria-hidden="true"><span className="art-orbit"/><span className="art-card"><ShieldCheck size={35}/><i/><i/><b><Check size={15}/>Approval recorded</b></span></div></section> : <div className="overview-grid">
            <section className="card allowance-card"><div className="section-heading"><div><h2>Allowance allocation</h2><p>Every dollar has a recorded state.</p></div><span className="subtle-pill">{ws.currency}</span></div><div className="allocation-content"><div className="allocation-ring" role="img" aria-label={`Allowance: ${money(available)} available, ${money(reserved)} reserved, ${money(paid)} paid, of ${money(total)} total.`} style={{background:total?`conic-gradient(var(--blue) 0 ${available/total*100}%, var(--amber) ${available/total*100}% ${(available+reserved)/total*100}%, var(--teal) ${(available+reserved)/total*100}% 100%)`:"var(--line)"}}><div><small>Total allowance</small><strong className={total >= 1000000 ? "large-allowance-total" : undefined}>{money(total)}</strong></div></div><div className="allocation-legend">{[["Available",available,"available"],["Reserved",reserved,"reserved"],["Paid",paid,"paid"]].map(([label,value,tone])=><div key={String(label)}><span><i className={`legend-dot ${tone}`}/>{label}</span><strong>{money(Number(value))}</strong></div>)}<p><LockKeyhole size={13}/>Uncertain payments never return to available automatically.</p></div></div></section>
            <section className="card action-queue"><div className="section-heading"><div><h2>Next actions</h2><p>Work that needs your attention.</p></div></div><button onClick={()=>navigate("approvals")}><span className="queue-icon blue"><ListChecks size={19}/></span><span><strong>Review approvals</strong><small>{pending.length} new · {renewals.length} expired</small></span><b>{pending.length+renewals.length}</b><ChevronRight size={17}/></button><button onClick={()=>navigate("purchases","attention")}><span className="queue-icon amber"><SearchCheck size={19}/></span><span><strong>Verify outcomes</strong><small>Reservations remain held</small></span><b>{unresolved.length}</b><ChevronRight size={17}/></button><button onClick={()=>navigate("purchases","blocked")}><span className="queue-icon neutral"><CircleAlert size={19}/></span><span><strong>Review allowance limits</strong><small>Requests over the available amount</small></span><b>{blocked.length}</b><ChevronRight size={17}/></button></section>
          </div>}
          <section className="card"><div className="section-heading"><div><h2>Recent purchases <span className="count-chip">{ops.length}</span></h2><p>The latest requests in this workspace.</p></div><button className="text-button" onClick={()=>navigate("purchases")}>View all<ArrowRight size={15}/></button></div>{ops.length?renderRows([...ops].reverse().slice(0,5)):empty("No purchases yet",ws?"Create a request to propose an item from the sample catalogue.":"Start a rehearsal or configure a sandbox workspace to begin.")}</section>
        </>}
        {(view==="purchases" || view==="approvals") && <>
          {view==="approvals" && <div className="review-summary"><span className="queue-icon blue"><ListChecks size={22}/></span><div><strong>{approvalQueue.length} {approvalQueue.length===1?"request":"requests"} to review</strong><p>Approval reserves the exact amount. Renewal preserves the existing reservation.</p></div><div className="review-available"><small>Available allowance</small><strong>{ws?money(available):"—"}</strong></div></div>}
          <section className="card purchases-card"><div className="section-heading"><div><h2>{view==="approvals"?"Review queue":"All purchases"}<span className="count-chip">{pool.length}</span></h2><p>{view==="approvals"?"Owner decisions, expired approvals and requests over allowance.":"Search by purchase, request, operation or provider reference."}</p></div>{view==="purchases" && <button className="btn btn-outline" disabled={!ws || !ops.length || !!busy} onClick={exportPurchaseReport} title="Export all current workspace purchase records, including mode and business snapshot"><ArrowDownToLine size={16}/>Export CSV</button>}</div><div className="table-toolbar"><label className="search-field"><Search size={16}/><span className="sr-only">Search purchases</span><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search purchases…"/>{search && <button aria-label="Clear search" onClick={()=>setSearch("")}><X size={14}/></button>}</label><label className="status-select"><SlidersHorizontal size={15}/><span className="sr-only">Filter purchase status</span><select value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All statuses</option><option value="approval">Needs approval</option><option value="renewal">Expired approval</option><option value="blocked">Over allowance</option>{view==="purchases" && <><option value="reserved">Reserved</option><option value="attention">Needs verification</option><option value="paid">Confirmed</option><option value="cancelled">Cancelled</option></>}</select></label></div>{displayed.length?renderRows(displayed):empty(search||filter!=="all"?"No matching purchases":view==="approvals"?"Nothing waiting for review":"No purchases yet",search||filter!=="all"?"Try another search or choose all statuses.":view==="approvals"?"New requests and expired approvals will appear here.":"Create a request to select an item from the permitted catalogue.")}<div className="table-footer"><span>{displayed.length} of {pool.length} purchases</span><span><LockKeyhole size={12}/>Allowance enforced on the server</span></div></section>
        </>}
        {view==="evidence" && <><div className="evidence-summary"><div><FileCheck2 size={21}/><span><strong>{events.length} recorded events</strong><small>{events.length===100?"Latest 100 events shown":"Events from the current workspace"}</small></span></div><div><ShoppingBag size={20}/><span><strong>{ops.length} purchase records</strong><small>Request, approval and provider references</small></span></div><div><FlaskConical size={20}/><span><strong>{isDiagnostic?"Sandbox diagnostic evidence":mode==="rehearsal"?"Simulated evidence":"Sandbox evidence"}</strong><small>Export includes complete operation receipts</small></span></div></div><section className="card evidence-ledger"><div className="section-heading"><div><h2>Activity ledger</h2><p>Newest first. A return URL never counts as payment evidence.</p></div></div><div className="table-toolbar"><label className="search-field"><Search size={16}/><span className="sr-only">Search evidence</span><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search events, purchases or references…"/>{search && <button aria-label="Clear evidence search" onClick={()=>setSearch("")}><X size={14}/></button>}</label><span className="small-note">{displayedEvents.length} events shown</span></div>{displayedEvents.length?<div className="ledger-list">{displayedEvents.map(event=>{const op=ops.find(item=>item.id===event.operationId);return <article className="ledger-event" key={event.id}><span className={`event-symbol ${event.type==="PAYMENT_CONFIRMED"?"verified":""}`}><FileCheck2 size={16}/></span><div><div className="ledger-event-heading"><strong>{titleCase(event.type)}</strong><time dateTime={new Date(event.createdAt).toISOString()}>{new Date(event.createdAt).toLocaleDateString(undefined,{month:"short",day:"numeric"})} · {time(event.createdAt)}</time></div>{op?<button className="event-purchase" onClick={()=>inspect(op)}>{op.title}<ArrowUpRight size={12}/></button>:<span className="event-purchase">Workspace</span>}<EvidenceDetail event={event}/></div></article>;})}</div>:empty("No matching evidence",events.length?"Try another search to find a recorded event.":"Events appear as you propose, approve and verify purchases.")}</section></>}
        {view==="controls" && <><div className="controls-banner"><ShieldCheck size={22}/><div><strong>Effective workspace rules</strong><p>These controls are enforced in application code. They are not editable switches.</p></div><span className="subtle-pill">Read only</span></div><section className="card rules-card">{[
          ["Shared allowance",ws?`${money(total)} ${ws.currency}`:"Set when a workspace starts","Approval atomically reserves funds. Proposed requests do not reduce the available allowance."],
          ["Owner authorization","Required before execution","The owner approves the exact item, seller, amount and currency. AI proposals carry no payment authority."],
          ["Execution window","15 minutes","Expired approval can be renewed for the unchanged purchase before capture dispatch. Existing reservations remain held."],
          ["Seller and catalogue","One controlled sample seller","Only server catalogue items and prices are permitted. Arbitrary merchants and production payments are not supported."],
          ["Uncertain outcomes","Reservation retained","A missing capture response requires checking the original order. No second capture is offered; a lost order-creation response needs manual review."],
          ["Request cancellation","Before provider dispatch only","Proposed, blocked or approved requests without provider orders can be cancelled. This releases an approved reservation; it is not a refund."],
          ["Payment confirmation","Matched provider evidence","Confirmation requires the original order, seller, amount, currency and completed final capture to match the approval."],
          ["Workspace changes","Held sandbox work stays visible","A new workspace cannot start while the current sandbox has reserved or uncertain purchases."],
        ].map(([name,value,detail])=><article className="rule-row" key={name}><span className="rule-check"><Check size={15}/></span><div><h3>{name}</h3><p>{detail}</p></div><strong>{value}</strong></article>)}</section><section className="card catalogue-card"><div className="section-heading"><div><h2>Permitted catalogue</h2><p>Sample digital services from a single seller. Prices come from the server.</p></div><span className="subtle-pill">{data.catalogue.length} items</span></div><div className="catalogue-grid">{data.catalogue.map(item=><article key={item.sku}><span className="purchase-icon"><ShoppingBag size={19}/></span><h3>{item.title}</h3><p>{item.description}</p><strong>{money(item.amountCents,item.currency)}</strong><small>{item.sku}</small></article>)}</div></section></>}
        {view==="connections" && <><div className="connection-grid"><section className="card connection-card"><div className="connection-brand paypal-word">PayPal</div><span className={`status ${paypalReady?"configured":"unconfigured"}`}>{paypalReady?"Configured":"Not configured"}</span><h2>Sandbox payments</h2><p>Orders, buyer approval and capture through one test merchant. All credentials stay on the server.</p><div className="connection-facts"><span>Environment<strong>Sandbox only</strong></span><span>Buyer approval<strong>Required on PayPal</strong></span><span>Confirmation<strong>Provider evidence checked</strong></span></div></section><section className="card connection-card"><div className="connection-brand"><Sparkles size={29}/><span>AI proposals</span></div><span className={`status ${aiReady?"configured":"unconfigured"}`}>{aiReady?"Configured":"Not configured"}</span><h2>Catalogue selection</h2><p>A model proposes one permitted item. The application fixes the merchant, price and approval requirements.</p><div className="connection-facts"><span>Permission<strong>Proposal only</strong></span><span>Payment credentials<strong>No model access</strong></span><span>Rehearsal mode<strong>Deterministic sample rules</strong></span></div></section></div><section className="card connection-checkpoint"><div><span className="section-kicker">CONFIGURATION ≠ VERIFIED EXECUTION</span><h2>{sandboxReady?"Ready to test the full journey.":"The AI purchase journey needs configuration."}</h2><p>{sandboxReady?"Configuration is present. Complete buyer approval, capture and verification, then inspect the recorded evidence.":"A configured PayPal sandbox merchant and an AI service are required. The rehearsal remains available with explicitly simulated records."}</p><p className="small-note">{ops.filter(op=>op.providerMode==="sandbox"&&op.status==="CONFIRMED").length} verified PayPal sandbox {ops.filter(op=>op.providerMode==="sandbox"&&op.status==="CONFIRMED").length===1?"purchase":"purchases"} in the current workspace.</p></div><button className="btn btn-primary" disabled={!!busy || !sandboxReady || hasSandboxHold || authRequired} onClick={()=>act("sandbox-start","/api/workspaces",{mode:"sandbox"}).then(result=>{if(result){navigate("purchases");setSelectedId(null);setPayPalRedirect(null);}})}>Start PayPal sandbox workspace<ArrowRight size={15}/></button></section><section className="card rehearsal-card" style={{marginBottom:22}}><span className="queue-icon blue"><SearchCheck size={23}/></span><div><h2>Test PayPal without AI</h2><p>Start a fixed-catalogue sandbox diagnostic with one $180 workflow review request. No AI model is called. You must approve the request and approve on PayPal before capture; only virtual test funds are used.</p><p className="small-note">Starting the diagnostic creates a request, not a verified payment result.</p></div><button className="btn btn-outline" disabled={!!busy || !paypalReady || authRequired || hasSandboxHold} onClick={()=>act("sandbox-diagnostic","/api/sandbox/diagnostic/start",{}).then(result=>{if(result){navigate("purchases");setFault(false);setPayPalRedirect(null);setNotice("PayPal sandbox diagnostic started with one fixed catalogue request. No AI model was called. Review and approve the request to continue with virtual test funds; no payment result is confirmed yet.");}})}>{busy==="sandbox-diagnostic"?<LoaderCircle size={16} className="spin"/>:<SearchCheck size={16}/>}Test PayPal sandbox</button></section><section className="card rehearsal-card"><span className="queue-icon neutral"><FlaskConical size={23}/></span><div><h2>Rehearse the controls</h2><p>Start a fresh simulation with two sample requests and your saved default allowance. Earlier workspaces remain in history. No model or PayPal calls are made.</p></div><button className="btn btn-outline" onClick={start} disabled={!!busy || authRequired || hasSandboxHold}>{busy==="start"?<LoaderCircle size={16} className="spin"/>:<Plus size={16}/>} {ws?.mode==="rehearsal"?"Reset simulated workspace":"Start rehearsal"}</button></section>{hasSandboxHold && <div className="message info"><LockKeyhole size={18}/><div><strong>Current sandbox allowance is still held</strong><p>Resolve reserved or uncertain purchases before starting another workspace.</p><button className="text-button" onClick={()=>navigate("purchases","reserved")}>Review held purchases<ArrowRight size={14}/></button></div></div>}</>}
        </>}
        <footer className="workspace-footer"><span><ShieldCheck size={14}/>ProofPay by AI Evaluation Lab</span><p>Single-seller sandbox prototype · {isDiagnostic?"PayPal diagnostic · no AI · virtual funds":mode==="rehearsal"?"Rehearsal records are simulated":"Virtual accounts and funds"}</p><button onClick={()=>setOverlay("about")}>About ProofPay<ArrowUpRight size={13}/></button></footer>
      </main>
    </div>
    {overlay && <div className={`modal-backdrop ${overlay==="purchase"?"drawer-backdrop":""}`} onClick={event=>{if(event.target===event.currentTarget){setOverlay(null);setCancelConfirm(false);}}}><section className={overlay==="purchase"?"purchase-drawer":"modal-card"} ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="dialog-title"><div className="dialog-heading"><div><p className="eyebrow">{overlay==="purchase"?"PURCHASE RECORD":overlay==="request"?"CONTROLLED CATALOGUE":"ABOUT THE WORKSPACE"}</p><h2 id="dialog-title">{overlay==="purchase"?selected?.title||"Purchase record":overlay==="request"?"What does your team need?":"Built around a clear outcome."}</h2></div><button className="icon-btn" aria-label="Close dialog" onClick={()=>{setOverlay(null);setCancelConfirm(false);}}><X size={20}/></button></div>
      <div className="dialog-body">{alerts}
      {overlay==="request" && <><p className="dialog-intro">{mode==="rehearsal"?"Create a sample proposal using the rehearsal rules. No AI model is called.":"Describe the need. AI may suggest a catalogue item; you decide what gets approved."}</p><form onSubmit={event=>{event.preventDefault();void propose();}}><label className="form-label" htmlFor="purchase-request">Purchase request</label><textarea id="purchase-request" aria-describedby="purchase-request-help" value={request} onChange={event=>setRequest(event.target.value)} placeholder="Our business needs a workflow review within the available allowance." maxLength={2000} rows={5} disabled={!!busy || authRequired}/><div className="field-help"><p id="purchase-request-help">Describe the business need. The catalogue fixes the seller and price.</p><span aria-label={`${request.length} of 2000 characters`}>{request.length}/2,000</span></div><div className="example-row"><span>Try a request</span><button type="button" disabled={!!busy} onClick={()=>setRequest("Our business needs a workflow review within $180.")}>Workflow review</button><button type="button" disabled={!!busy} onClick={()=>setRequest("Our business needs a design review within $160.")}>Design review</button><button type="button" disabled={!!busy} onClick={()=>setRequest(`Suggest a cheaper option within ${money(available)} of available allowance.`)}>Cheaper option</button></div><div className="request-allowance"><LockKeyhole size={15}/><span>Available allowance<strong>{ws?money(available):"No workspace"}</strong></span></div>{mode==="sandbox"&&!sandboxReady && <p className="form-hint">Configure both providers in Connections before asking for an AI proposal.</p>}<button type="submit" className="btn btn-primary full" disabled={!!busy || !request.trim() || !ws || isDiagnostic || authRequired || (mode==="sandbox"&&!sandboxReady)}>{busy==="propose"?<LoaderCircle size={16} className="spin"/>:<Sparkles size={16}/>} {mode==="rehearsal"?"Create sample proposal":"Ask AI for a proposal"}<ArrowRight size={16}/></button></form><p className="form-hint">One sample seller · USD · Every alternative needs its own approval.</p></>}
      {overlay==="purchase" && (selected ? <><div className="record-topline"><span className={`status ${selected.status.toLowerCase()}`}>{statusLabel(selected)}</span><span className="subtle-pill">{selected.aiSource==="sandbox-diagnostic"?"PayPal sandbox diagnostic":selected.providerMode==="rehearsal"?"Simulated provider":"PayPal sandbox"}</span></div><div className="record-amount">{money(selected.amountCents,selected.currency)}<span>{selected.currency}</span></div><p className="record-request">{selected.request}</p><dl className="record-facts"><div><dt>Seller</dt><dd>{selected.merchantId}</dd></div><div><dt>Catalogue item</dt><dd>{selected.sku}</dd></div><div><dt>Proposal source</dt><dd>{selected.aiSource==="model"?"AI model":selected.aiSource==="sandbox-diagnostic"?"Sandbox diagnostic · no AI":selected.aiSource==="rehearsal-seed"?"Rehearsal sample":"Rehearsal rule"}</dd></div><div><dt>Owner approval</dt><dd>{selected.approvalExpiresAt===null?"Not granted":`Version ${selected.approvalVersion} · ${selected.status==="CANCELLED"?"cancelled — no execution authority":approvalExpired?"execution window expired":`valid until ${time(selected.approvalExpiresAt)}`}`}</dd></div><div><dt>Operation</dt><dd className="mono">{selected.id}</dd></div>{selected.orderId && <div><dt>Provider order</dt><dd className="mono">{selected.orderId}</dd></div>}{selected.captureId && <div><dt>Capture</dt><dd className="mono">{selected.captureId}</dd></div>}</dl>{selected.rationale && <div className="rationale"><Sparkles size={15}/><p>{selected.rationale}</p></div>}
        <section className="record-actions" aria-label="Purchase actions">
          {approvalRenewable && <><div className="inline-note warning"><CircleAlert size={18}/><p>Owner approval expired. Renew the same <strong>{selected.title}</strong> from <strong>{selected.merchantId}</strong> for <strong>{money(selected.amountCents,selected.currency)} {selected.currency}</strong>. The reservation stays held.</p></div><button className="btn btn-primary full" disabled={!!busy} onClick={renewApproval}>{busy===selected.id?<LoaderCircle className="spin" size={16}/>:<Check size={16}/>}Renew owner approval</button><p className="form-hint">Another 15-minute execution window. Renewal does not dispatch a payment.</p></>}
          {selected.status==="PROPOSED" && <><p className="action-description">Approve this exact item, seller, amount and currency. The allowance is reserved before any provider request.</p><button className="btn btn-primary full" disabled={!!busy} onClick={()=>operationAction(selected,"approve")}>{busy===selected.id?<LoaderCircle className="spin" size={16}/>:<Check size={16}/>}Approve & reserve {money(selected.amountCents,selected.currency)}</button></>}
          {selected.status==="APPROVED" && <button className="btn btn-primary full" disabled={!!busy || approvalExpired} onClick={()=>operationAction(selected,"create-order")}>{busy===selected.id?<LoaderCircle className="spin" size={16}/>:<ArrowRight size={16}/>}Create {selected.providerMode==="rehearsal"?"simulated":"PayPal"} order</button>}
          {selected.status==="ORDER_READY" && <><p className="action-description">{selected.providerMode==="rehearsal"?"Rehearsal simulates buyer approval and capture. No PayPal request is made.":"Approve on PayPal as the sandbox buyer, then capture below. The server checks buyer approval; a return link alone is not proof."}</p>{selectedUrl && <a className="btn btn-outline full" href={selectedUrl} target="_blank" rel="noopener noreferrer">Open PayPal approval<ArrowUpRight size={16}/></a>}<label className="fault-control"><input type="checkbox" checked={fault} onChange={event=>setFault(event.target.checked)} disabled={!!busy}/><span>Drop the capture response<small>Deliberate application fault for recovery testing</small></span></label><button className="btn btn-primary full" disabled={!!busy || approvalExpired} onClick={()=>operationAction(selected,"capture",{fault:fault?"drop-response":undefined})}>{busy===selected.id?<LoaderCircle className="spin" size={16}/>:<CheckCheck size={16}/>}Capture {selected.providerMode==="rehearsal"?"simulated payment":"approved order"}</button></>}
          {(["CREATE_DISPATCHED","CREATE_UNKNOWN"] as Status[]).includes(selected.status) && <div className="inline-note warning"><CircleAlert size={19}/><p>Order creation needs manual review. A verified order reference is not available for capture verification. The reservation stays held; export the evidence for review. No new order is dispatched here.</p></div>}
          {(["CAPTURE_DISPATCHED","UNKNOWN","REVIEW"] as Status[]).includes(selected.status) && <><div className="inline-note warning"><SearchCheck size={19}/><p>{selected.status==="REVIEW"?"The provider record needs review before confirmation.":"The capture outcome is not yet verified. A missing response does not mean payment failed."} The reservation stays held.</p></div><button className="btn btn-primary full" disabled={!!busy} onClick={()=>operationAction(selected,"reconcile")}>{busy===selected.id?<LoaderCircle className="spin" size={16}/>:<SearchCheck size={16}/>}Check {selected.providerMode==="rehearsal"?"simulated":"PayPal"} outcome</button></>}
          {selected.status==="CONFIRMED" && <><div className="inline-note positive"><ShieldCheck size={19}/><p>{selected.providerMode==="rehearsal"?"Simulated evidence confirms this rehearsal purchase.":"Matched PayPal evidence confirms this purchase."} Its amount is recorded once in the ledger.</p></div><button className="btn btn-outline full" disabled={!!busy} onClick={()=>operationAction(selected,"reconcile")}><SearchCheck size={16}/>Check outcome again</button></>}
          {selected.status==="BUDGET_BLOCKED" && <><div className="inline-note warning"><CircleAlert size={19}/><p>This request exceeds the available allowance. A smaller catalogue option requires a new proposal and approval.</p></div><button className="btn btn-outline full" disabled={!!busy} onClick={()=>{setRequest(`Suggest a cheaper alternative to ${selected.title} within ${money(available)}. Use only the permitted catalogue.`);setOverlay("request");setCancelConfirm(false);}}><Sparkles size={16}/>Request an alternative</button></>}
          {selected.status==="CANCELLED" && <div className="inline-note neutral"><FileCheck2 size={19}/><p>This request was cancelled before provider dispatch. Its evidence is retained. This is not a refund or a provider-order cancellation.</p></div>}
          {canCancel && (!cancelConfirm ? <button className="text-button cancel-link" disabled={!!busy} onClick={()=>setCancelConfirm(true)}>Cancel request</button> : <div className="cancel-confirmation" role="group" aria-label="Confirm request cancellation"><h3>Cancel this request?</h3><p><strong>{selected.title}</strong> · {selected.merchantId} · <strong>{money(selected.amountCents,selected.currency)} {selected.currency}</strong></p><p>{selected.status==="APPROVED"?`${money(selected.amountCents,selected.currency)} will return to available allowance.`:"This request has no reserved allowance to release."} No refund or provider cancellation is sent.</p><div><button className="btn btn-danger" disabled={!!busy} onClick={cancelRequest}>{busy===selected.id?<LoaderCircle className="spin" size={15}/>:<X size={15}/>}Confirm cancellation</button><button className="btn btn-outline" disabled={!!busy} onClick={()=>setCancelConfirm(false)}>Keep request</button></div></div>)}
        </section><ReceiptInspector key={selected.id} operation={selected} refreshPurchase={refreshNow}/><section className="record-timeline"><div className="section-heading"><h3>Activity & evidence</h3><span className="count-chip">{eventList.length}</span></div>{eventList.length?eventList.map(event=><article className="timeline-event" key={event.id}><span className="timeline-dot"/><div><strong>{titleCase(event.type)}</strong><time dateTime={new Date(event.createdAt).toISOString()}>{time(event.createdAt)}</time><EvidenceDetail event={event}/></div></article>):<p className="muted-text">No operation events are available in the current workspace snapshot.</p>}<p className="form-hint">The workspace snapshot contains up to 100 recent events. Export evidence for the complete operation receipt.</p></section>
      </> : empty("Purchase not available","Select a purchase from the current workspace to inspect its record."))}
      {overlay==="about" && <><span className="about-mark"><ShieldCheck size={40}/></span><p className="dialog-intro">ProofPay connects a buying request, owner approval, shared allowance and checked provider outcome. Built by AI Evaluation Lab for the PayPal AI Hackathon.</p><p className="dialog-intro">Rehearsal uses sample inputs and a simulated provider. Sandbox uses virtual accounts and funds. Configuration alone is not evidence of a verified payment.</p><button className="btn btn-primary full" onClick={()=>setOverlay(null)}>Back to the workspace<ArrowRight size={16}/></button></>}
      </div></section></div>}
</div>;
}
