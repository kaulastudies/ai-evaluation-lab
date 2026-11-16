"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowDownToLine, ArrowRight, ArrowUpRight, Check, CheckCheck, CircleAlert, FileCheck2, FlaskConical, LoaderCircle, LockKeyhole, LayoutDashboard, ListChecks, SlidersHorizontal, Cpu, Search, RefreshCw, RotateCcw, SearchCheck, ShieldCheck, ShoppingBag } from "lucide-react";
import ReceiptInspector from "./receipt-inspector";

type Status = "PROPOSED" | "BUDGET_BLOCKED" | "APPROVED" | "CREATE_DISPATCHED" | "CREATE_UNKNOWN" | "ORDER_READY" | "CAPTURE_DISPATCHED" | "UNKNOWN" | "REVIEW" | "CONFIRMED" | "CANCELLED";
type Purchase = {
  id: string; request: string; title: string; sku: string; merchantId: string;
  amountCents: number; currency: string; status: Status; providerMode: "rehearsal";
  approvalVersion: number; approvalExpiresAt: number | null; orderId: string | null;
  captureId: string | null; rationale: string; updatedAt: number;
};
type Event = { id: string; operationId: string | null; type: string; detail: string; createdAt: number };
type State = {
  workspace: { id: string; mode: "rehearsal"; budgetCents: number; reservedCents: number; committedCents: number; availableCents: number; currency: string };
  operations: Purchase[]; events: Event[]; catalogue: { sku: string; title: string; description: string; amountCents: number; currency: string }[];
};
type Judge = { simulated: true; expiresAt: number; resetLimit: number; mutationLimit: number };
type Envelope = { state?: State; judge?: Judge; error?: string; code?: string };
type View = "overview" | "purchases" | "approvals" | "evidence" | "controls" | "backend" | "lab";
const viewNames: Record<View, string> = { overview: "Overview", purchases: "Purchases", approvals: "Approvals", evidence: "Evidence", controls: "Controls", backend: "AI & backend", lab: "Evaluation lab" };
const navItems = [{ id: "overview", icon: LayoutDashboard }, { id: "purchases", icon: ShoppingBag }, { id: "approvals", icon: ListChecks }, { id: "evidence", icon: FileCheck2 }, { id: "controls", icon: SlidersHorizontal }, { id: "backend", icon: Cpu }, { id: "lab", icon: SearchCheck }] as const;
type Action = "approve" | "renew-approval" | "create-order" | "capture" | "reconcile" | "cancel";
const SOURCE = "https://github.com/kaulastudies/ai-evaluation-lab/tree/proofpay/purchase-desk-v0.1/hackathon/proofpay";
const TESTING = "https://github.com/kaulastudies/ai-evaluation-lab/blob/proofpay/purchase-desk-v0.1/hackathon/proofpay/docs/REPEATABLE_TESTING.md";
const LIVE_EVIDENCE = "https://github.com/kaulastudies/ai-evaluation-lab/blob/proofpay/purchase-desk-v0.1/hackathon/proofpay/evidence/configured-live-qa-2026-11-08.md";
const labels: Record<Status, string> = {
  PROPOSED: "Needs your approval", BUDGET_BLOCKED: "Over available allowance", APPROVED: "Allowance reserved",
  CREATE_DISPATCHED: "Creating simulated order", CREATE_UNKNOWN: "Order needs review", ORDER_READY: "Ready for simulated capture",
  CAPTURE_DISPATCHED: "Needs verification", UNKNOWN: "Needs verification", REVIEW: "Needs review",
  CONFIRMED: "Simulated payment confirmed", CANCELLED: "Request cancelled",
};
const money = (cents: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(cents / 100);
const readableEvent = (type: string) => type.toLowerCase().replaceAll("_", " ").replace(/^\w/, value => value.toUpperCase());
const time = (value: number) => new Date(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
function eventDetail(event: Event) {
  if (event.type !== "PROPOSAL_CREATED") return null;
  try {
    const detail = JSON.parse(event.detail) as { rationale?: unknown };
    return typeof detail.rationale === "string" ? detail.rationale : null;
  } catch { return null; }
}

export default function JudgeDesk() {
  const [view, setView] = useState<View>("overview");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [request, setRequest] = useState("");
  const [reloadObservation, setReloadObservation] = useState<{ workspaceId: string; operationId: string } | null>(null);
  const [repeatObservation, setRepeatObservation] = useState<{ workspaceId: string; operationId: string } | null>(null);
  const [data, setData] = useState<State | null>(null);
  const [judge, setJudge] = useState<Judge | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [dropResponse, setDropResponse] = useState(true);
  const [resetPrompt, setResetPrompt] = useState(false);
  const [cancelPrompt, setCancelPrompt] = useState<{ id: string; version: number } | null>(null);
  const [clock, setClock] = useState<number | null>(null);
  const busyRef = useRef(false);
  const proposalKey = useRef<{ request: string; id: string } | null>(null);
  const sequence = useRef(0);
  const selectedHeading = useRef<HTMLHeadingElement>(null);
  const apply = useCallback((body: Envelope) => {
    if (!body.state || !body.judge || body.judge.simulated !== true || body.state.workspace?.mode !== "rehearsal" || body.state.operations.some(operation => operation.providerMode !== "rehearsal")) throw new Error("The rehearsal response could not be validated. No payment controls are available.");
    const state = body.state;
    setData(state); setJudge(body.judge);
    setSelectedId(current => state.operations.some(operation => operation.id === current) ? current : state.operations.find(operation => operation.sku === "workflow-review")?.id ?? state.operations[0]?.id ?? null);
  }, []);
  const clearSession = useCallback(() => { setData(null); setJudge(null); setSelectedId(null); setResetPrompt(false); setCancelPrompt(null); }, []);
  const read = useCallback(async (signal?: AbortSignal) => {
    const current = ++sequence.current;
    const response = await fetch("/api/judge/state", { cache: "no-store", signal });
    const body = await response.json() as Envelope;
    if (current !== sequence.current || signal?.aborted) return;
    if (response.status === 401) { clearSession(); return; }
    if (!response.ok) throw new Error(body.error || "The evaluator rehearsal could not be loaded.");
    apply(body);
    try {
      const navigation = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
      const stored = sessionStorage.getItem("proofpay-judge-reload-check");
      if (navigation?.type === "reload" && stored && body.state) {
        const previous = JSON.parse(stored) as { workspaceId?: string; operationId?: string; orderId?: string; reservedCents?: number; paidCents?: number };
        const operation = body.state.operations.find(value => value.id === previous.operationId);
        if (previous.workspaceId === body.state.workspace.id && operation?.orderId === previous.orderId && ["UNKNOWN", "CAPTURE_DISPATCHED", "REVIEW"].includes(operation?.status || "") && body.state.workspace.reservedCents === previous.reservedCents && body.state.workspace.committedCents === previous.paidCents && operation) setReloadObservation({ workspaceId: body.state.workspace.id, operationId: operation.id });
        sessionStorage.removeItem("proofpay-judge-reload-check");
      }
    } catch { /* Storage is optional. Missing browser observation never counts as a passed check. */ }
  }, [apply, clearSession]);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const deadline = setTimeout(() => { if (active) { controller.abort(); setLoading(false); setError("Loading the saved workspace took too long. Retry loading, or open a judge workspace."); } }, 12000);
    const timer = setTimeout(() => {
      read(controller.signal).catch(error => { if (active && !controller.signal.aborted) setError(error instanceof Error ? error.message : "The rehearsal could not be loaded."); }).finally(() => { clearTimeout(deadline); if (active) setLoading(false); });
    }, 0);
    return () => { active = false; clearTimeout(timer); clearTimeout(deadline); controller.abort(); };
  }, [read]);
  useEffect(() => {
    const refreshOnFocus = () => { if (!busyRef.current) read().catch(error => setError(error instanceof Error ? error.message : "The rehearsal could not be refreshed.")); };
    window.addEventListener("focus", refreshOnFocus);
    return () => window.removeEventListener("focus", refreshOnFocus);
  }, [read]);
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const update = () => {
      const now = Date.now(); setClock(now);
      const future = [judge?.expiresAt, ...(data?.operations || []).map(operation => operation.approvalExpiresAt)].filter((value): value is number => typeof value === "number" && value > now);
      if (future.length) timer = setTimeout(update, Math.min(Math.max(0, Math.min(...future) - now) + 5, 2_147_483_647));
    };
    timer = setTimeout(update, 0);
    return () => clearTimeout(timer);
  }, [data?.operations, judge?.expiresAt]);
  const expired = !!judge && clock !== null && judge.expiresAt <= clock;
  const approvalQueue = (data?.operations || []).filter(operation => ["PROPOSED", "BUDGET_BLOCKED"].includes(operation.status) || (operation.approvalExpiresAt !== null && clock !== null && operation.approvalExpiresAt <= clock && !operation.captureId && ["APPROVED", "ORDER_READY"].includes(operation.status)));
  const needle = search.trim().toLowerCase();
  const operationPool = view === "approvals" ? approvalQueue : data?.operations || [];
  const visibleOperations = operationPool.filter(operation => (view !== "purchases" || ((!needle || [operation.title, operation.sku, operation.request, operation.id, operation.orderId, operation.captureId].filter(Boolean).join(" ").toLowerCase().includes(needle)) && (filter === "all" || filter === "approval" && operation.status === "PROPOSED" || filter === "reserved" && ["APPROVED", "ORDER_READY", "CREATE_DISPATCHED", "CREATE_UNKNOWN", "CAPTURE_DISPATCHED", "UNKNOWN", "REVIEW"].includes(operation.status) || filter === "attention" && ["CREATE_DISPATCHED", "CREATE_UNKNOWN", "CAPTURE_DISPATCHED", "UNKNOWN", "REVIEW"].includes(operation.status) || filter === "confirmed" && operation.status === "CONFIRMED" || filter === "cancelled" && operation.status === "CANCELLED"))));
  const selected = visibleOperations.find(operation => operation.id === selectedId) ?? visibleOperations[0];
  const approvalExpired = !!selected?.approvalExpiresAt && clock !== null && selected.approvalExpiresAt <= clock;
  const renewable = !!selected && approvalExpired && !selected.captureId && ["APPROVED", "ORDER_READY"].includes(selected.status);
  const canCancel = !!selected && ["PROPOSED", "BUDGET_BLOCKED", "APPROVED"].includes(selected.status) && !selected.orderId && !selected.captureId;
  const disabled = !!busy || expired;
  const unresolved = data?.operations.filter(operation => ["CREATE_DISPATCHED", "CREATE_UNKNOWN", "CAPTURE_DISPATCHED", "UNKNOWN", "REVIEW"].includes(operation.status)).length ?? 0;

  async function mutate(key: string, path: string, body: Record<string, unknown> = {}) {
    if (busyRef.current) return null;
    busyRef.current = true; ++sequence.current; setBusy(key); setError(""); setNotice("");
    try {
      const response = await fetch(`/api/judge/${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const result = await response.json() as Envelope;
      if (response.status === 401) clearSession();
      if (result.state && result.judge) apply(result);
      if (!response.ok) throw new Error(key === "session" && response.status === 401 ? "The previous guest session expired and its cookie was cleared. Select Open judge workspace again to begin a new rehearsal." : result.error || "The rehearsal action could not be completed.");
      if (!result.state) throw new Error("No saved rehearsal state was returned. Refresh before continuing.");
      return result;
    } catch (error) {
      setError(error instanceof Error ? error.message : "The rehearsal action could not be completed.");
      await read().catch(() => {});
      return null;
    } finally { busyRef.current = false; setBusy(null); }
  }
  async function action(operation: Purchase, actionName: Action) {
    const body = actionName === "reconcile" ? {} : { approvalVersion: operation.approvalVersion, ...(actionName === "capture" && dropResponse ? { fault: "drop-response" } : {}) };
    const success = await mutate(operation.id, `operations/${encodeURIComponent(operation.id)}/${actionName}`, body);
    if (success) {
      setCancelPrompt(null);
      if (actionName === "approve" && view === "approvals") { setView("purchases"); setSelectedId(operation.id); setSearch(""); setFilter("all"); }
      if (actionName === "reconcile" && operation.status === "CONFIRMED" && data && success.state) {
        const checked = success.state.operations.find(value => value.id === operation.id);
        if (success.state.workspace.id === data.workspace.id && checked?.status === "CONFIRMED" && checked.captureId === operation.captureId && success.state.workspace.committedCents === data.workspace.committedCents && success.state.workspace.reservedCents === data.workspace.reservedCents && success.state.workspace.availableCents === data.workspace.availableCents) setRepeatObservation({ workspaceId: data.workspace.id, operationId: operation.id });
      }
      if (actionName === "capture" && dropResponse) setNotice("Capture response deliberately dropped. The saved outcome is unverified and the allowance remains reserved. Reload the page, then check the simulated outcome.");
      if (actionName === "renew-approval") setNotice("Approval renewed for the same item, seller and amount. No simulated payment was dispatched by renewal.");
      if (actionName === "cancel") setNotice("Request cancelled before dispatch. Any reservation was released; this is not a refund.");
    }
  }
  async function begin() {
    if (await mutate("session", "session")) { setDropResponse(true); setResetPrompt(false); setCancelPrompt(null); setReloadObservation(null); setRepeatObservation(null); setView("overview"); setNotice("Your isolated rehearsal is ready. All requests and provider outcomes here are simulated."); }
  }
  async function reset() {
    if (await mutate("reset", "rehearsal/start")) { setResetPrompt(false); setCancelPrompt(null); setDropResponse(true); setReloadObservation(null); setRepeatObservation(null); setView("overview"); setSearch(""); setFilter("all"); setRequest(""); proposalKey.current = null; setNotice("A fresh $300 simulated workspace is ready. No live payment or AI request was made."); }
  }
  async function refresh() {
    if (busyRef.current) return;
    busyRef.current = true; setBusy("refresh"); setError("");
    try { await read(); } catch (error) { setError(error instanceof Error ? error.message : "The rehearsal could not be refreshed."); }
    finally { busyRef.current = false; setBusy(null); }
  }
  async function exportEvidence() {
    if (busyRef.current || !data || expired) return;
    busyRef.current = true; ++sequence.current; setBusy("export"); setError(""); setNotice("");
    try {
      const records = await Promise.all(data.operations.map(async operation => {
        const response = await fetch(`/api/judge/operations/${encodeURIComponent(operation.id)}/evidence`, { cache: "no-store" });
        const record = await response.json() as { operation?: { id?: string }; error?: string };
        if (response.status === 401) clearSession();
        if (!response.ok || record.operation?.id !== operation.id) throw new Error(record.error || "A rehearsal receipt could not be loaded.");
        return record;
      }));
      const artifact = { exportedAt: new Date().toISOString(), source: "ProofPay public evaluator rehearsal", simulated: true, claim: "Simulated provider records. No live AI, PayPal call or real-money payment occurred in this rehearsal.", state: data, records };
      const url = URL.createObjectURL(new Blob([JSON.stringify(artifact, null, 2)], { type: "application/json" }));
      const anchor = document.createElement("a"); anchor.href = url; anchor.download = `proofpay-simulated-rehearsal-${data.workspace.id.slice(0, 8)}.json`; anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setNotice(`Prepared a download containing ${records.length} simulated purchase receipts. It is application evidence, not a signed provider attestation.`);
    } catch (error) { setError(error instanceof Error ? error.message : "The evidence download could not be prepared."); }
    finally { busyRef.current = false; setBusy(null); }
  }
  async function proposeSample(value: string) {
    const text = value.trim();
    if (!text || busyRef.current || expired) return;
    if (!proposalKey.current || proposalKey.current.request !== text) proposalKey.current = { request: text, id: crypto.randomUUID() };
    const previous = new Set(data?.operations.map(operation => operation.id));
    const result = await mutate("proposal", "proposals", { request: text, mode: "rehearsal", idempotencyKey: proposalKey.current.id });
    if (result?.state) {
      const created = result.state.operations.find(operation => !previous.has(operation.id));
      if (created) setSelectedId(created.id);
      proposalKey.current = null; setRequest(""); setView("purchases"); setSearch(""); setFilter("all");
      setNotice("Sample proposal saved. A deterministic rule selected a catalogue item; review its price and approve it separately.");
    }
  }
  const alternative = () => proposeSample("Suggest a cheaper starter review within $90.");
  function inspect(operation: Purchase) {
    setSelectedId(operation.id); setCancelPrompt(null);
    requestAnimationFrame(() => { selectedHeading.current?.focus({ preventScroll: true }); if (window.innerWidth < 900) selectedHeading.current?.scrollIntoView({ behavior: "smooth", block: "start" }); });
  }
  function reloadForCheck() {
    if (!data || !selected) return;
    try { sessionStorage.setItem("proofpay-judge-reload-check", JSON.stringify({ workspaceId: data.workspace.id, operationId: selected.id, orderId: selected.orderId, reservedCents: data.workspace.reservedCents, paidCents: data.workspace.committedCents })); } catch { /* Reload still works without a browser comparison marker. */ }
    window.location.reload();
  }
  function navigate(next: View) {
    setView(next); setSearch(""); setFilter("all"); setCancelPrompt(null);
    requestAnimationFrame(() => { document.getElementById("judge-title")?.focus({ preventScroll: true }); window.scrollTo({ top: 0, behavior: "instant" }); });
  }
  const workflow = data?.operations.find(operation => operation.sku === "workflow-review" && operation.amountCents === 18000);
  const competing = data?.operations.find(operation => operation.sku === "design-review" && operation.amountCents === 16000);
  const hasEvent = (operationId: string | undefined, type: string) => !!operationId && !!data?.events.some(event => event.operationId === operationId && event.type === type);
  const checks = [
    { title: "Approve the $180 workflow review", complete: hasEvent(workflow?.id, "APPROVED"), detail: "Requires the saved approval event for the original $180 request." },
    { title: "Block the competing $160 request", complete: hasEvent(competing?.id, "BUDGET_BLOCKED"), detail: "Requires a saved budget-block event. No second approval is assumed." },
    { title: "Drop the simulated capture response", complete: hasEvent(workflow?.id, "RESPONSE_DROPPED"), detail: "Requires the application's recorded response-drop fault." },
    { title: "Reload and observe the same held outcome", complete: !!workflow && reloadObservation?.workspaceId === data?.workspace.id && reloadObservation?.operationId === workflow.id, detail: "Use Reload page to check persistence. This browser compares the original order and held totals after a server read; it is not a backend restart test." },
    { title: "Verify the original simulated outcome", complete: workflow?.status === "CONFIRMED" && hasEvent(workflow?.id, "PROVIDER_VERIFIED"), detail: "Requires a confirmed purchase and stored simulated verification event." },
    { title: "Check again without changing the recorded totals", complete: !!workflow && repeatObservation?.workspaceId === data?.workspace.id && repeatObservation?.operationId === workflow.id, detail: "This browser compares a repeated check's returned capture reference and workspace totals. It does not measure external request counts." },
  ];
  const confirmed = data?.operations.filter(operation => operation.status === "CONFIRMED") || [];
  const pending = data?.operations.filter(operation => operation.status === "PROPOSED") || [];
  const nextOperation = data?.operations.find(operation => ["UNKNOWN", "CAPTURE_DISPATCHED", "REVIEW", "APPROVED", "ORDER_READY"].includes(operation.status)) ?? pending.find(operation => operation.sku === "workflow-review") ?? pending[0] ?? data?.operations.find(operation => operation.status === "BUDGET_BLOCKED") ?? data?.operations[0];
  function continuePurchase(operation = nextOperation) {
    if (!operation) { navigate("purchases"); return; }
    setView("purchases"); setSearch(""); setFilter("all"); inspect(operation);
  }
  const descriptions: Record<View, string> = {
    overview: "Your allowance, purchase queue and next action in one place.", purchases: "Create requests and carry each approved purchase through to a checked outcome.",
    approvals: "Review exact items, sellers and amounts before spending is reserved.", evidence: "Inspect saved receipts and the decisions behind every purchase.",
    controls: "The rules and limits active in your isolated guest workspace.", backend: "Inspect how proposals, approvals and payment verification fit together.", lab: "Follow the recorded checks as you exercise the workflow.",
  };
  const operationBusy = selected && busy === selected.id;
  return <div className="judge-shell judge-portal">
    <a className="skip-link" href="#judge-main">Skip to judge workspace</a>
    <aside className="judge-sidebar"><button className="judge-brand" onClick={() => navigate("overview")} aria-label="ProofPay overview"><span className="brand-symbol"><CheckCheck size={25}/></span><span>ProofPay<small>PAYMENT OPERATIONS</small></span></button><div className="judge-sidebar-identity"><span className="workspace-monogram">JA</span><div><strong>Judge administrator</strong><small>Isolated rehearsal</small></div><ShieldCheck size={16}/></div><p className="nav-heading">WORKSPACE</p><nav aria-label="Judge workspace navigation">{navItems.map(({ id, icon: Icon }) => <button key={id} onClick={() => navigate(id)} className={`nav-item ${view === id ? "active" : ""}`} title={viewNames[id]} aria-label={viewNames[id]} aria-current={view === id ? "page" : undefined}><Icon size={19}/><span>{viewNames[id]}</span>{id === "approvals" && approvalQueue.length > 0 && <em>{approvalQueue.length}</em>}</button>)}</nav><div className="judge-sidebar-bottom"><FlaskConical size={20}/><strong>Free evaluator workspace</strong><p>Sample proposals. Simulated provider. No live AI or money.</p>{judge && <small>Session expires<br/>{time(judge.expiresAt)}</small>}</div></aside>
    <div className="judge-portal-content"><header className="judge-app-header"><div><span>Judge workspace</span><span>/</span><strong>{viewNames[view]}</strong></div><div><span className="judge-app-mode"><span/>Rehearsal</span><button className="icon-btn" title="Refresh saved state" aria-label="Refresh saved state" disabled={!!busy || loading} onClick={refresh}><RefreshCw size={18} className={busy === "refresh" ? "spin" : ""}/></button><span className="owner-avatar" title="Guest judge administrator">JA</span></div></header>
    <main id="judge-main" className="judge-main" tabIndex={-1} aria-busy={loading || !!busy}>
      <div className="judge-page-heading"><div><p className="eyebrow">JUDGE ADMINISTRATOR · ISOLATED REHEARSAL</p><h1 id="judge-title" tabIndex={-1}>{data ? viewNames[view] : "Your judge workspace"}</h1><p>{data ? descriptions[view] : "Open a working purchase desk. No owner login, account setup or payment details."}</p></div>{data && <button className="btn btn-outline" disabled={disabled || !data.operations.length} onClick={exportEvidence}>{busy === "export" ? <LoaderCircle size={17} className="spin"/> : <ArrowDownToLine size={17}/>}Export evidence</button>}</div>
      <div className="judge-quiet-banner" role="note"><FlaskConical size={18}/><span><strong>Interactive rehearsal</strong> · Simulated provider · No live AI or money</span></div>
      {error && <div className="message error" role="alert"><CircleAlert size={19}/><p>{error}</p><button aria-label="Dismiss error" onClick={() => setError("")}>×</button></div>}
      {notice && <div className="message success" role="status"><Check size={19}/><p>{notice}</p><button aria-label="Dismiss notice" onClick={() => setNotice("")}>×</button></div>}
      {expired && <div className="message info" role="status"><LockKeyhole size={19}/><div><strong>This guest session has expired.</strong><p>Open a new isolated workspace to continue.</p><button className="btn btn-primary" disabled={!!busy} onClick={begin}>Open judge workspace</button></div></div>}
      {loading ? <section className="card judge-welcome" role="status"><LoaderCircle size={28} className="spin"/><h2>Loading your workspace</h2><p>Checking for your saved guest session.</p></section> : !data ? <section className="card judge-open-workspace"><div><span className="queue-icon blue"><ShieldCheck size={27}/></span><h2>Start with a real workflow.</h2><p>Your own saved rehearsal starts with a $300 test allowance and two competing requests. Approve, capture, recover and inspect the evidence in this portal.</p><button className="btn btn-primary" disabled={!!busy} onClick={begin}>{busy === "session" ? <LoaderCircle size={19} className="spin"/> : <ArrowRight size={19}/>}Open judge workspace</button><small>No signup. A temporary secure cookie keeps your session separate.</small>{error && <button className="text-button" disabled={!!busy} onClick={refresh}><RefreshCw size={17}/>Retry loading saved workspace</button>}</div><div className="judge-open-map"><h3>Everything stays in the app</h3><div><ShoppingBag size={20}/><span><strong>Purchase desk</strong>Requests, approval and payment recovery</span></div><div><FileCheck2 size={20}/><span><strong>Evidence & controls</strong>Stored receipts and enforced limits</span></div><div><SearchCheck size={20}/><span><strong>Evaluation lab</strong>Checks that follow your saved workflow</span></div></div></section> : <>
        <section className={`judge-session-strip ${confirmed.length ? "has-completed" : ""}`} aria-label="Resume or restart rehearsal"><div><strong>{confirmed.length ? "This saved demo already has a confirmed purchase." : "Your saved workspace is ready."}</strong><p>{confirmed.length ? "Review its evidence, continue other requests, or start fresh to run every step again." : `${data.operations.length} requests · ${money(data.workspace.availableCents)} available · Session ends ${time(judge!.expiresAt)}`}</p></div><div><button className="btn btn-outline" disabled={!!busy || !nextOperation} onClick={() => continuePurchase()}>Continue workflow<ArrowRight size={16}/></button><button className="btn btn-primary" disabled={disabled} onClick={() => setResetPrompt(value => !value)}><RotateCcw size={16}/>Start fresh demo</button></div></section>
        {resetPrompt && <section className="card judge-reset-panel" role="group" aria-label="Confirm fresh rehearsal"><div><h2>Start a fresh $300 demo?</h2><p>This creates two new sample requests. Export the current evidence first; this view will move to the new simulated workspace.</p></div><div><button className="btn btn-primary" disabled={disabled} onClick={reset}>{busy === "reset" ? <LoaderCircle size={17} className="spin"/> : <RotateCcw size={17}/>}Confirm fresh demo</button><button className="btn btn-outline" disabled={!!busy} onClick={() => setResetPrompt(false)}>Keep current workspace</button></div></section>}
        {view === "overview" && <><section className="metric-grid judge-metrics" aria-label="Current simulated allowance">{[["Available", data.workspace.availableCents, "Unreserved test allowance"], ["Reserved", data.workspace.reservedCents, "Held for approved purchases"], ["Paid · simulated", data.workspace.committedCents, "Confirmed from simulated evidence"]].map(([label, value, description]) => <article className="metric-card" key={String(label)}><div>{label}</div><strong>{money(Number(value))}</strong><small>{description}</small></article>)}<button className="metric-card metric-link" onClick={() => { navigate("purchases"); setFilter("attention"); }}><div>Needs verification<SearchCheck size={18}/></div><strong>{unresolved}</strong><small>Uncertain outcomes remain held</small></button></section><div className="judge-overview-grid"><section className="card judge-overview-allocation"><div className="section-heading"><div><h2>Allowance allocation</h2><p>{money(data.workspace.budgetCents)} per workspace · USD</p></div><LockKeyhole size={20}/></div><div className="judge-allowance-bar" role="img" aria-label={`${money(data.workspace.availableCents)} available, ${money(data.workspace.reservedCents)} reserved, ${money(data.workspace.committedCents)} simulated paid`}><span style={{ flex: data.workspace.availableCents }} aria-hidden="true"/><span style={{ flex: data.workspace.reservedCents }} aria-hidden="true"/><span style={{ flex: data.workspace.committedCents }} aria-hidden="true"/></div><dl className="judge-allowance-legend">{[["Available", data.workspace.availableCents], ["Reserved", data.workspace.reservedCents], ["Paid · simulated", data.workspace.committedCents]].map(([label, value]) => <div key={String(label)}><dt>{label}</dt><dd>{money(Number(value))}</dd></div>)}</dl><p className="judge-card-note">An uncertain capture keeps its reservation until the original outcome is verified.</p></section><section className="card judge-next-actions"><div className="section-heading"><div><h2>Next actions</h2><p>Continue from the saved state.</p></div></div><button onClick={() => navigate("approvals")}><span className="queue-icon blue"><ListChecks size={20}/></span><span><strong>Review approvals</strong><small>New requests, budget blocks and renewals</small></span><b>{approvalQueue.length}</b><ArrowRight size={17}/></button><button onClick={() => continuePurchase()}><span className="queue-icon amber"><SearchCheck size={20}/></span><span><strong>Continue payment workflow</strong><small>{nextOperation ? `${nextOperation.title} · ${labels[nextOperation.status]}` : "No purchases yet"}</small></span><ArrowRight size={17}/></button><button onClick={() => navigate("lab")}><span className="queue-icon neutral"><ShieldCheck size={20}/></span><span><strong>Review lab observations</strong><small>{checks.filter(check => check.complete).length} of {checks.length} checks observed in this session</small></span><ArrowRight size={17}/></button></section></div><section className="card judge-overview-purchases"><div className="section-heading"><div><h2>Current purchases</h2><p>Open any record to continue or inspect it.</p></div><button className="text-button" onClick={() => navigate("purchases")}>View all<ArrowRight size={16}/></button></div>{data.operations.map(operation => <button key={operation.id} onClick={() => continuePurchase(operation)}><span className="purchase-icon"><ShoppingBag size={18}/></span><span><strong>{operation.title}</strong><small>{operation.id.slice(0, 8)} · Sample proposal</small></span><span className={`status ${operation.status.toLowerCase()}`}>{labels[operation.status]}</span><b>{money(operation.amountCents)}</b><ArrowRight size={17}/></button>)}</section><details className="card judge-flow-guide"><summary>Suggested evaluation sequence</summary><ol className="judge-walkthrough"><li><span>1</span><div><strong>Reserve $180</strong><p>Approve the workflow review.</p></div></li><li><span>2</span><div><strong>Try the competing $160</strong><p>Test the remaining $120 allowance.</p></div></li><li><span>3</span><div><strong>Drop the capture response</strong><p>Create and capture the simulated order.</p></div></li><li><span>4</span><div><strong>Reload, then verify</strong><p>Check the original order and inspect its receipt.</p></div></li></ol></details></>}
        {(view === "purchases" || view === "approvals") && <>
          {view === "purchases" ? <><div className="judge-purchase-toolbar"><label className="search-field"><Search size={18}/><span className="sr-only">Search purchases</span><input value={search} onChange={event => { setSearch(event.target.value); setCancelPrompt(null); }} placeholder="Search purchases or references"/></label><label className="status-select"><span className="sr-only">Filter purchases</span><select value={filter} onChange={event => { setFilter(event.target.value); setCancelPrompt(null); }}><option value="all">All statuses</option><option value="approval">Needs approval</option><option value="reserved">Reserved or uncertain</option><option value="attention">Needs verification</option><option value="confirmed">Simulated confirmed</option><option value="cancelled">Cancelled</option></select></label></div><details className="card judge-request-composer"><summary>New sample request</summary><form onSubmit={event => { event.preventDefault(); void proposeSample(request); }}><label className="form-label" htmlFor="judge-request">Describe the purchase</label><textarea id="judge-request" value={request} maxLength={2000} rows={3} onChange={event => setRequest(event.target.value)} placeholder="Find a workflow review within $180." disabled={disabled}/><div><p>Deterministic sample rules select a fixed catalogue item. No AI model is called.</p><button className="btn btn-primary" type="submit" disabled={disabled || !request.trim()}>{busy === "proposal" ? <LoaderCircle size={17} className="spin"/> : <ArrowRight size={17}/>}Create sample proposal</button></div></form></details></> : <div className="judge-review-summary"><ListChecks size={22}/><div><strong>{approvalQueue.length} requests to review</strong><p>Approval reserves the exact amount. Renewals preserve existing reservations.</p></div><span>Available<strong>{money(data.workspace.availableCents)}</strong></span></div>}
        <div className="judge-workspace"><section className="card judge-purchases" aria-labelledby="judge-purchases-heading"><div className="section-heading"><div><h2 id="judge-purchases-heading">{view === "approvals" ? "Review queue" : "Purchase requests"}</h2><p>Choose a request to review or continue.</p></div><span className="count-chip">{visibleOperations.length}</span></div><div className="judge-purchase-list">{visibleOperations.map(operation => <button className={`judge-purchase ${selected?.id === operation.id ? "is-selected" : ""}`} key={operation.id} onClick={() => inspect(operation)} aria-pressed={selected?.id === operation.id}><span className="judge-purchase-title"><ShoppingBag size={19}/><strong>{operation.title}</strong><b>{money(operation.amountCents)}</b></span><span className={`status ${operation.status.toLowerCase()}`}>{labels[operation.status]}</span><small>Sample proposal · {operation.id.slice(0, 8)}</small></button>)}{!visibleOperations.length && <div className="empty-state"><h3>{view === "approvals" ? "No approvals waiting" : "No matching purchases"}</h3><p>{view === "approvals" ? "Approved purchases continue in Purchases. Expired execution approvals will appear here for renewal." : "Try a different search or filter."}</p><button className="text-button" onClick={() => { setSearch(""); setFilter("all"); if (view === "approvals") navigate("purchases"); }}>View purchases<ArrowRight size={16}/></button></div>}</div><p className="judge-list-note">A fixed catalogue and deterministic sample rules supply these requests. The rehearsal does not call an AI model.</p></section>
          <section className="card judge-detail" aria-labelledby="judge-detail-heading">{selected ? <><div className="section-heading"><div><p className="eyebrow">SELECTED PURCHASE</p><h2 id="judge-detail-heading" ref={selectedHeading} tabIndex={-1}>{selected.title}</h2></div><span className={`status ${selected.status.toLowerCase()}`}>{labels[selected.status]}</span></div><div className="judge-detail-body"><div className="record-amount">{money(selected.amountCents)}<span>USD · simulated</span></div><p className="record-request">{selected.request}</p><dl className="record-facts"><div><dt>Seller</dt><dd>{selected.merchantId}</dd></div><div><dt>Catalogue item</dt><dd>{selected.sku}</dd></div><div><dt>Approval</dt><dd>{selected.approvalExpiresAt === null ? "Not granted" : `Version ${selected.approvalVersion} · ${selected.status === "CANCELLED" ? "cancelled" : approvalExpired ? "execution window expired" : `valid until ${time(selected.approvalExpiresAt)}`}`}</dd></div><div><dt>Operation</dt><dd className="mono">{selected.id}</dd></div>{selected.orderId && <div><dt>Simulated order</dt><dd className="mono">{selected.orderId}</dd></div>}{selected.captureId && <div><dt>Simulated capture</dt><dd className="mono">{selected.captureId}</dd></div>}</dl>
          <div className="record-actions" aria-label="Simulated purchase actions">
            {renewable && <><div className="inline-note warning"><CircleAlert size={19}/><p>Renew your approval for <strong>{selected.title}</strong> from <strong>{selected.merchantId}</strong> at <strong>{money(selected.amountCents)} USD</strong>. The existing reservation stays held.</p></div><button className="btn btn-primary full" disabled={disabled} onClick={() => action(selected, "renew-approval")}>Renew the same approval</button></>}
            {selected.status === "PROPOSED" && <><p className="action-description">Approve this exact item, seller and amount. The allowance is reserved before an order is created.</p><button className="btn btn-primary full" disabled={disabled} onClick={() => action(selected, "approve")}>{operationBusy ? <LoaderCircle size={17} className="spin"/> : <Check size={17}/>}Approve & reserve {money(selected.amountCents)}</button></>}
            {selected.status === "APPROVED" && <button className="btn btn-primary full" disabled={disabled || approvalExpired} onClick={() => action(selected, "create-order")}>{operationBusy ? <LoaderCircle size={17} className="spin"/> : <ArrowRight size={17}/>}Create simulated order</button>}
            {selected.status === "ORDER_READY" && <><p className="action-description">Buyer approval and provider capture are simulated. Keep the fault enabled to test recovery.</p><label className="fault-control"><input type="checkbox" checked={dropResponse} disabled={disabled} onChange={event => setDropResponse(event.target.checked)}/><span>Drop the capture response<small>Deliberate application fault; no live payment</small></span></label><button className="btn btn-primary full" disabled={disabled || approvalExpired} onClick={() => action(selected, "capture")}>{operationBusy ? <LoaderCircle size={17} className="spin"/> : <CheckCheck size={17}/>}Capture simulated payment</button></>}
            {["CAPTURE_DISPATCHED", "UNKNOWN", "REVIEW"].includes(selected.status) && <><div className="inline-note warning"><SearchCheck size={20}/><p>The outcome is unverified. Its amount stays reserved. Reload the page to check persistence, then verify the original simulated order.</p></div><button className="btn btn-outline full" disabled={!!busy} onClick={reloadForCheck}><RefreshCw size={17}/>Reload page to check persistence</button><button className="btn btn-primary full" disabled={disabled} onClick={() => action(selected, "reconcile")}>{operationBusy ? <LoaderCircle size={17} className="spin"/> : <SearchCheck size={17}/>}Check simulated outcome</button></>}
            {selected.status === "CONFIRMED" && <><div className="inline-note positive"><ShieldCheck size={20}/><p>Stored simulated evidence confirms this purchase. Its amount is recorded once in this workspace. Check again to inspect whether the totals remain unchanged.</p></div><button className="btn btn-outline full" disabled={disabled} onClick={() => action(selected, "reconcile")}><SearchCheck size={17}/>Check the same outcome again</button></>}
            {["CREATE_DISPATCHED", "CREATE_UNKNOWN"].includes(selected.status) && <div className="inline-note warning"><CircleAlert size={20}/><p>Order creation needs review. The reservation stays held. Export the evidence; this screen will not dispatch another order while its outcome is uncertain.</p></div>}
            {selected.status === "BUDGET_BLOCKED" && <><div className="inline-note warning"><LockKeyhole size={20}/><p>This request exceeds the available {money(data.workspace.availableCents)}. It has no reserved allowance. A smaller option needs a separate approval.</p></div><button className="btn btn-outline full" disabled={disabled} onClick={alternative}>Propose a $90 sample alternative<ArrowRight size={16}/></button></>}
            {selected.status === "CANCELLED" && <div className="inline-note neutral"><FileCheck2 size={20}/><p>This request was cancelled before provider dispatch. Its evidence is retained. No refund or provider-order cancellation occurred.</p></div>}
            {canCancel && (!(cancelPrompt?.id === selected.id && cancelPrompt.version === selected.approvalVersion) ? <button className="text-button cancel-link" disabled={disabled} onClick={() => setCancelPrompt({ id: selected.id, version: selected.approvalVersion })}>Cancel this request</button> : <div className="cancel-confirmation" role="group" aria-label="Confirm cancellation"><h3>Cancel this request?</h3><p>{selected.title} · {selected.merchantId} · {money(selected.amountCents)} USD. Any unused reservation will be released. This is not a refund.</p><div><button className="btn btn-danger" disabled={disabled} onClick={() => action(selected, "cancel")}>Confirm cancellation</button><button className="btn btn-outline" disabled={!!busy} onClick={() => setCancelPrompt(null)}>Keep request</button></div></div>)}
          </div><ReceiptInspector key={selected.id} operation={selected} refreshPurchase={refresh} apiBase="/api/judge"/><section className="record-timeline"><div className="section-heading"><h3>Saved activity</h3></div>{data.events.filter(event => event.operationId === selected.id).map(event => <article className="timeline-event" key={event.id}><span className="timeline-dot"/><div><strong>{readableEvent(event.type)}</strong><time dateTime={new Date(event.createdAt).toISOString()}>{time(event.createdAt)}</time>{eventDetail(event) ? <p>{eventDetail(event)}</p> : <details><summary>Inspect record</summary><pre>{event.detail}</pre></details>}</div></article>)}<p className="form-hint">This view shows up to 100 recent workspace events. Export the complete operation receipts to inspect their saved evidence.</p></section></div></> : <div className="empty-state"><h2 id="judge-detail-heading">Choose a purchase</h2><p>Select a request to inspect its amount, approval and recorded outcome.</p></div>}</section>
        </div>
        </>}
        {view === "evidence" && <><section className="judge-evidence-summary"><article className="card"><FileCheck2 size={23}/><div><strong>{data.operations.length} purchase records</strong><p>Complete receipts are available for export.</p></div></article><article className="card"><CheckCheck size={23}/><div><strong>{confirmed.length} simulated confirmations</strong><p>Current saved purchase status.</p></div></article><article className="card"><SearchCheck size={23}/><div><strong>{data.events.length} recent events</strong><p>Workspace view is capped at 100 events.</p></div></article></section><section className="card judge-evidence-inspector"><div className="section-heading"><div><h2>Inspect a saved receipt</h2><p>Compare the current purchase with stored observations.</p></div><button className="btn btn-outline" disabled={disabled || !data.operations.length} onClick={exportEvidence}><ArrowDownToLine size={17}/>Export all receipts</button></div><div className="judge-evidence-body"><label className="form-label" htmlFor="judge-evidence-purchase">Purchase record</label><select id="judge-evidence-purchase" value={selected?.id || ""} onChange={event => setSelectedId(event.target.value)}>{data.operations.map(operation => <option key={operation.id} value={operation.id}>{operation.title} · {money(operation.amountCents)} · {operation.id.slice(0, 8)}</option>)}</select>{selected ? <><div className="judge-evidence-record"><span className={`status ${selected.status.toLowerCase()}`}>{labels[selected.status]}</span><span className="mono">{selected.id}</span></div><ReceiptInspector key={selected.id} operation={selected} refreshPurchase={refresh} apiBase="/api/judge"/></> : <p>No purchase records are available yet.</p>}</div></section><section className="card judge-evidence-events"><div className="section-heading"><div><h2>Recent workspace activity</h2><p>Saved application events, latest first.</p></div></div>{data.events.map(event => <article key={event.id}><span className="queue-icon neutral"><FileCheck2 size={18}/></span><div><strong>{readableEvent(event.type)}</strong><time dateTime={new Date(event.createdAt).toISOString()}>{time(event.createdAt)}</time>{eventDetail(event) ? <p>{eventDetail(event)}</p> : <details><summary>Inspect record</summary><pre>{event.detail}</pre></details>}</div></article>)}</section></>}
        {view === "controls" && <><section className="card judge-module"><span className="subtle-pill">Read-only effective rules</span><h2>Your workspace limits</h2><div className="judge-control-grid">{[["Workspace allowance", `${money(data.workspace.budgetCents)} USD`], ["Available", money(data.workspace.availableCents)], ["Reserved", money(data.workspace.reservedCents)], ["Session expires", judge ? time(judge.expiresAt) : "Unavailable"], ["Reset limit", judge ? `${judge.resetLimit} additional resets` : "Unavailable"], ["Mutation limit", judge ? `${judge.mutationLimit} actions per session` : "Unavailable"]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div><p>Limits come from the active guest session. Remaining action counts are not exposed by the server.</p></section><section className="card judge-module"><h2>Approval and recovery rules</h2><ol className="judge-boundaries"><li><strong>Exact purchase approval</strong><span>Item, merchant, amount, currency and version are bound to the approval. Execution authority lasts 15 minutes; renewal needs your explicit decision.</span></li><li><strong>Reserve before dispatch</strong><span>Approval reserves the amount. Requests over the available allowance are blocked before a payment is dispatched.</span></li><li><strong>Keep uncertainty held</strong><span>A missing capture response keeps the reservation. Verification reads the original order; the interface does not retry capture.</span></li><li><strong>Cancel only before dispatch</strong><span>Untouched requests can be cancelled. A provider order, uncertain capture or confirmed payment cannot be refunded from this control.</span></li></ol><button className="btn btn-outline" onClick={() => navigate("approvals")}>Review approvals<ArrowRight size={17}/></button></section><section className="card judge-module"><h2>Permitted catalogue</h2><p>These items and USD prices come from the server. The model or request text cannot edit the seller or price.</p><div className="judge-catalogue">{data.catalogue.map(item => <article key={item.sku}><strong>{item.title}</strong><p>{item.description}</p><span>{money(item.amountCents)} {item.currency}</span><small>{item.sku}</small></article>)}</div></section></>}
        {view === "backend" && <section className="judge-backend-grid" aria-label="Read-only AI and backend architecture"><article className="card judge-module"><span className="subtle-pill">This guest deployment</span><h2>Rehearsal configuration</h2><dl><div><dt>Provider</dt><dd>Deterministic simulator</dd></div><div><dt>AI proposals</dt><dd>Sample rules only · no model called</dd></div><div><dt>Funds</dt><dd>Simulated USD allowance</dd></div><div><dt>Authority</dt><dd>Guest approval for this guest’s requests</dd></div><div><dt>Access</dt><dd>Temporary signed session · no owner account</dd></div></dl><p>These are effective limits, not configuration controls. This page cannot enable providers, view secrets or spend real money.</p></article><article className="card judge-module"><span className="subtle-pill">Published owner run · 8 November 2026</span><h2>Recorded AI-to-PayPal route</h2><dl><div><dt>Model</dt><dd>openai/gpt-4.1-mini</dd></div><div><dt>Routing</dt><dd>Vercel AI Gateway · project OIDC</dd></div><div><dt>Model authority</dt><dd>Suggest one permitted catalogue SKU</dd></div><div><dt>Payment path</dt><dd>PayPal sandbox Orders → buyer approval → capture → original-order verification</dd></div><div><dt>Funding scope</dt><dd>One bounded free-credit model attempt was recorded and consumed</dd></div></dl><p>This is the published historical run, not a live connection check in your guest session.</p></article><article className="card judge-module judge-module-wide"><span className="section-kicker">ENFORCED APPLICATION BOUNDARIES</span><h2>The model proposes. The application controls execution.</h2><ol className="judge-boundaries"><li><strong>Fixed catalogue</strong><span>The server fixes seller, USD price and permitted items. User text and model output cannot choose arbitrary merchants or prices.</span></li><li><strong>Exact approval</strong><span>Approval is bound to the operation, seller, item, amount, currency and version. Expired execution authority requires explicit renewal.</span></li><li><strong>Held uncertainty</strong><span>Durable intent and request identities precede provider dispatch. Missing responses retain reservations and use the original order for verification.</span></li><li><strong>Inspectable evidence</strong><span>Receipts retain checked provider fields and application events. They are unsigned records; historical approval-version and SKU limits remain documented.</span></li></ol></article></section>}

        {view === "lab" && <section className="judge-lab" aria-labelledby="judge-lab-heading"><div className="card judge-lab-summary"><div><span className="section-kicker">AI EVALUATION LAB · VERIFICATION</span><h2 id="judge-lab-heading">Current rehearsal observations</h2><p>The first checks use saved server records. Reload and repeat-check observations come from this browser session. An unchecked item means it has not been observed here—not that it failed.</p></div><span className="judge-lab-count">{checks.filter(check => check.complete).length}<small>of {checks.length} observed</small></span></div><ol className="judge-checklist">{checks.map((check, index) => <li key={check.title}><span className={check.complete ? "is-complete" : ""}>{check.complete ? <Check size={19}/> : index + 1}</span><div><h3>{check.title}</h3><p>{check.detail}</p></div><strong>{check.complete ? "Observed" : "Not yet observed"}</strong></li>)}</ol><button className="btn btn-primary" onClick={() => navigate("purchases")}>Continue in the purchase desk<ArrowRight size={17}/></button><div className="judge-lab-records"><article className="card judge-module"><span className="subtle-pill">Local source checkpoint · 8 November 2026</span><h2>210 automated checks passed</h2><p>The recorded local suite covers provider verification, approval and budget controls, uncertainty, owner/guest boundaries and related regressions. This count describes the dated source checkpoint, not tests run by this browser.</p></article><article className="card judge-module"><span className="subtle-pill">Published hosted evidence</span><h2>Actual AI + PayPal sandbox run</h2><p>The dated run records a genuine model proposal, sandbox buyer approval, response-drop recovery and unchanged totals after a repeated check. It used virtual funds; this guest session remains simulated.</p></article></div><p className="form-hint">Lab verification is project evidence, not an independent audit certificate, signed attestation, production settlement claim or general exactly-once guarantee. Browser observations reset when you start another rehearsal or leave this session.</p></section>}
      </>}
      <footer className="judge-footer"><span>ProofPay · AI Evaluation Lab</span><div><a href={SOURCE} target="_blank" rel="noopener noreferrer">Source<ArrowUpRight size={13}/></a><a href={TESTING} target="_blank" rel="noopener noreferrer">Repeatable tests<ArrowUpRight size={13}/></a><a href={LIVE_EVIDENCE} target="_blank" rel="noopener noreferrer">Recorded live evidence<ArrowUpRight size={13}/></a></div><p>Guest rehearsal only · simulated provider · unsigned application receipts</p></footer>
    </main></div>
  </div>;
}
