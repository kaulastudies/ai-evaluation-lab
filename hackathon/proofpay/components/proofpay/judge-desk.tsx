"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowDownToLine, ArrowRight, ArrowUpRight, Check, CheckCheck, CircleAlert, FileCheck2, FlaskConical, LoaderCircle, LockKeyhole, RefreshCw, RotateCcw, SearchCheck, ShieldCheck, ShoppingBag } from "lucide-react";
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
  operations: Purchase[]; events: Event[];
};
type Judge = { simulated: true; expiresAt: number; resetLimit: number; mutationLimit: number };
type Envelope = { state?: State; judge?: Judge; error?: string; code?: string };
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
  const [view, setView] = useState<"desk" | "backend" | "lab">("desk");
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
  const [cancelPrompt, setCancelPrompt] = useState(false);
  const [clock, setClock] = useState<number | null>(null);
  const busyRef = useRef(false);
  const sequence = useRef(0);
  const selectedHeading = useRef<HTMLHeadingElement>(null);
  const apply = useCallback((body: Envelope) => {
    if (!body.state || !body.judge || body.judge.simulated !== true || body.state.workspace?.mode !== "rehearsal" || body.state.operations.some(operation => operation.providerMode !== "rehearsal")) throw new Error("The rehearsal response could not be validated. No payment controls are available.");
    const state = body.state;
    setData(state); setJudge(body.judge);
    setSelectedId(current => state.operations.some(operation => operation.id === current) ? current : state.operations.find(operation => operation.sku === "workflow-review")?.id ?? state.operations[0]?.id ?? null);
  }, []);
  const clearSession = useCallback(() => { setData(null); setJudge(null); setSelectedId(null); setResetPrompt(false); setCancelPrompt(false); }, []);
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
    const timer = setTimeout(() => {
      read(controller.signal).catch(error => { if (active && !controller.signal.aborted) setError(error instanceof Error ? error.message : "The rehearsal could not be loaded."); }).finally(() => { if (active) setLoading(false); });
    }, 0);
    return () => { active = false; clearTimeout(timer); controller.abort(); };
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
  const selected = data?.operations.find(operation => operation.id === selectedId);
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
      if (!response.ok) throw new Error(key === "session" && response.status === 401 ? "The previous guest session expired and its cookie was cleared. Select Try the demo again to begin a new rehearsal." : result.error || "The rehearsal action could not be completed.");
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
      setCancelPrompt(false);
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
    if (await mutate("session", "session")) { setDropResponse(true); setResetPrompt(false); setCancelPrompt(false); setReloadObservation(null); setRepeatObservation(null); setView("desk"); setNotice("Your isolated rehearsal is ready. All requests and provider outcomes here are simulated."); }
  }
  async function reset() {
    if (await mutate("reset", "rehearsal/start")) { setResetPrompt(false); setCancelPrompt(false); setDropResponse(true); setReloadObservation(null); setRepeatObservation(null); setNotice("A fresh $300 simulated workspace is ready. No live payment or AI request was made."); }
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
  async function alternative() {
    if (await mutate("alternative", "proposals", { request: "Suggest a cheaper starter review within $90.", mode: "rehearsal", idempotencyKey: crypto.randomUUID() })) {
      setNotice("A deterministic sample rule proposed the smaller catalogue option. No AI model was called; review and approve it separately.");
    }
  }
  function inspect(operation: Purchase) {
    setSelectedId(operation.id); setCancelPrompt(false);
    requestAnimationFrame(() => { selectedHeading.current?.focus({ preventScroll: true }); if (window.innerWidth < 900) selectedHeading.current?.scrollIntoView({ behavior: "smooth", block: "start" }); });
  }
  function reloadForCheck() {
    if (!data || !selected) return;
    try { sessionStorage.setItem("proofpay-judge-reload-check", JSON.stringify({ workspaceId: data.workspace.id, operationId: selected.id, orderId: selected.orderId, reservedCents: data.workspace.reservedCents, paidCents: data.workspace.committedCents })); } catch { /* Reload still works without a browser comparison marker. */ }
    window.location.reload();
  }
  function navigate(next: "desk" | "backend" | "lab") {
    setView(next);
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
  const operationBusy = selected && busy === selected.id;
  return <div className="judge-shell">
    <a className="skip-link" href="#judge-main">Skip to evaluator rehearsal</a>
    <header className="judge-header"><a className="judge-brand" href="/judge"><span className="brand-symbol"><CheckCheck size={25}/></span><span>ProofPay<small>Evaluator workspace</small></span></a><nav aria-label="Project evidence"><a href={LIVE_EVIDENCE} target="_blank" rel="noopener noreferrer">Recorded AI + PayPal run<ArrowUpRight size={16}/></a><a href={TESTING} target="_blank" rel="noopener noreferrer">Source & repeatable tests<ArrowUpRight size={16}/></a></nav></header>
    <div className="judge-simulation" role="note"><FlaskConical size={20}/><div><strong>Interactive rehearsal · simulated provider</strong><span>No live AI, PayPal requests or real money. Published live sandbox evidence is linked separately.</span></div></div>
    <main id="judge-main" className="judge-main" tabIndex={-1} aria-busy={loading || !!busy}>
      <div className={`judge-intro ${!data ? "judge-landing-intro" : ""}`}><div><p className="eyebrow">{data ? "YOUR INTERACTIVE REHEARSAL" : "OWNER-APPROVED AGENT PURCHASES"}</p><h1 id="judge-title" tabIndex={-1}>{data ? view === "backend" ? "AI and backend, with clear boundaries." : view === "lab" ? "Inspect the workflow as you run it." : "A missing response is not a failed payment." : <>Approve the purchase.<br/><span>Keep control of the payment.</span></>}</h1><p>{data ? "Approve a purchase, deliberately lose its capture response, then recover the original outcome without releasing its reserved allowance." : "An AI proposal is only the beginning. ProofPay connects the exact purchase, your spending authority and the evidence behind its outcome—even when a response goes missing."}</p>{!data && <div className="judge-hero-actions"><button className="btn btn-primary" disabled={loading || !!busy} onClick={begin}>{busy === "session" ? <LoaderCircle size={19} className="spin"/> : <ArrowRight size={19}/>}Try the demo</button><a className="btn btn-outline" href={LIVE_EVIDENCE} target="_blank" rel="noopener noreferrer">See the recorded live run<ArrowUpRight size={17}/></a><p>Free, isolated rehearsal · no account or payment details · no live AI calls</p></div>}</div>{data ? <div className="judge-session"><span><LockKeyhole size={15}/>Isolated guest session</span><small>{expired ? "Session expired" : judge ? `Expires ${time(judge.expiresAt)}` : ""}</small></div> : <section className="judge-sample" aria-label="Illustrative purchase control example, not live records"><div className="judge-sample-top"><span><ShieldCheck size={18}/>Purchase desk</span><small>ILLUSTRATIVE EXAMPLE</small></div><div className="judge-sample-balances"><div><span>Available</span><strong>$120<span>.00</span></strong></div><div><span>Reserved</span><strong>$180<span>.00</span></strong></div><div><span>Paid</span><strong>$0<span>.00</span></strong></div></div><div className="judge-sample-bar" aria-hidden="true"><span/><span/></div><p className="judge-sample-allowance">$300 sample allowance · $180 held pending verification</p><div className="judge-sample-purchase"><span className="queue-icon blue"><ShoppingBag size={19}/></span><div><strong>Workflow review</strong><span>Approved for the exact seller and amount</span></div><b>$180</b></div><div className="judge-sample-warning"><SearchCheck size={18}/><div><strong>Capture response missing</strong><p>Keep funds reserved. Check the original order.</p></div></div><div className="judge-sample-foot"><span><LockKeyhole size={15}/>Approval recorded</span><span><FileCheck2 size={15}/>Evidence retained</span></div><p className="judge-sample-caption">Sample values explain the flow. Your own saved rehearsal starts when you choose Try the demo.</p></section>}</div>
      {error && <div className="message error" role="alert"><CircleAlert size={19}/><p>{error}</p></div>}
      {notice && <div className="message success" role="status"><Check size={19}/><p>{notice}</p></div>}
      {expired && <div className="message info" role="status"><LockKeyhole size={19}/><div><strong>This guest session has expired.</strong><p>Payment controls and receipt access are disabled. Begin a new isolated rehearsal to continue.</p><button className="btn btn-outline" disabled={!!busy} onClick={begin}>Begin a new rehearsal</button></div></div>}
      {loading ? <section className="card judge-welcome" role="status"><LoaderCircle size={28} className="spin"/><h2>Loading the rehearsal</h2><p>Checking for your existing guest workspace.</p></section> : !data ? <><section className="judge-value-grid" aria-label="What ProofPay controls"><article><span className="queue-icon blue"><CheckCheck size={23}/></span><p className="section-kicker">01 · AUTHORITY</p><h2>Approve what will be bought.</h2><p>The item, seller, amount and currency stay tied to your approval. A model may propose; it cannot authorize spending.</p></article><article><span className="queue-icon amber"><LockKeyhole size={23}/></span><p className="section-kicker">02 · RECOVERY</p><h2>Hold uncertain payments.</h2><p>A lost capture response keeps the allowance reserved. Recovery checks the original order before updating the recorded outcome.</p></article><article><span className="queue-icon neutral"><FileCheck2 size={23}/></span><p className="section-kicker">03 · EVIDENCE</p><h2>Inspect the decision trail.</h2><p>Follow the request, approval and provider observations in one record. Export application receipts with their stated limits.</p></article></section><section className="judge-demo-guide"><div><p className="section-kicker">WHAT YOU CAN TRY</p><h2>Two requests. One $300 limit.<br/>A deliberate missing response.</h2><p>Your guest workspace starts with $180 and $160 sample requests. Reserve one, test the competing request, drop a capture response and verify the saved outcome after a reload.</p></div><div><span><Check size={18}/>No owner login or provider credentials</span><span><Check size={18}/>A separate workspace for your session</span><span><Check size={18}/>Repeatable simulation and inspectable records</span><p>A temporary secure cookie keeps your workspace separate. The session lasts two hours. All provider behavior in this demo is simulated.</p></div></section></> : <>
        <div className="judge-role"><ShieldCheck size={18}/><div><strong>Judge administrator · isolated rehearsal</strong><span>Control this guest’s simulated requests. Owner accounts, real provider configuration and live model calls are not accessible here.</span></div></div>
        <nav className="judge-view-nav" aria-label="Evaluator sections">{([["desk", "Purchase desk"], ["backend", "AI & backend"], ["lab", "Evaluation lab"]] as const).map(([id, label]) => <button key={id} className={view === id ? "active" : ""} aria-current={view === id ? "page" : undefined} onClick={() => navigate(id)}>{label}</button>)}</nav>
        {view === "desk" && <><ol className="judge-walkthrough" aria-label="Suggested evaluation sequence"><li><span>1</span><div><strong>Reserve $180</strong><p>Approve the workflow review.</p></div></li><li><span>2</span><div><strong>Try the competing $160</strong><p>Its approval should exceed $120 available.</p></div></li><li><span>3</span><div><strong>Drop the capture response</strong><p>Create the $180 order, then capture with the fault on.</p></div></li><li><span>4</span><div><strong>Reload, then verify</strong><p>The $180 stays held until the original outcome is checked.</p></div></li></ol>
        <section className="metric-grid judge-metrics" aria-label="Current simulated allowance">{[["Available", data.workspace.availableCents, "Unreserved test allowance"], ["Reserved", data.workspace.reservedCents, "Includes uncertain outcomes"], ["Paid · simulated", data.workspace.committedCents, "Confirmed by the simulated provider"]].map(([label, value, description]) => <article className="metric-card" key={String(label)}><div>{label}</div><strong>{money(Number(value))}</strong><small>{description}</small></article>)}<article className="metric-card"><div>Needs verification</div><strong>{unresolved}</strong><small>Outcome is not yet confirmed</small></article></section>
        <div className="judge-toolbar"><p>Workspace allowance: <strong>{money(data.workspace.budgetCents)} USD</strong></p><div><button className="btn btn-outline" disabled={!!busy} onClick={refresh}><RefreshCw size={16} className={busy === "refresh" ? "spin" : ""}/>Refresh saved state</button><button className="btn btn-outline" disabled={disabled || !data.operations.length} onClick={exportEvidence}>{busy === "export" ? <LoaderCircle size={16} className="spin"/> : <ArrowDownToLine size={16}/>}Export simulated evidence</button></div></div>
        <div className="judge-workspace"><section className="card judge-purchases" aria-labelledby="judge-purchases-heading"><div className="section-heading"><div><h2 id="judge-purchases-heading">Purchase requests</h2><p>Choose a request to review or continue.</p></div><span className="count-chip">{data.operations.length}</span></div><div className="judge-purchase-list">{data.operations.map(operation => <button className={`judge-purchase ${selected?.id === operation.id ? "is-selected" : ""}`} key={operation.id} onClick={() => inspect(operation)} aria-pressed={selected?.id === operation.id}><span className="judge-purchase-title"><ShoppingBag size={19}/><strong>{operation.title}</strong><b>{money(operation.amountCents)}</b></span><span className={`status ${operation.status.toLowerCase()}`}>{labels[operation.status]}</span><small>Sample proposal · {operation.id.slice(0, 8)}</small></button>)}</div><p className="judge-list-note">A fixed catalogue and deterministic sample rules supply these requests. The rehearsal does not call an AI model.</p></section>
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
            {canCancel && (!cancelPrompt ? <button className="text-button cancel-link" disabled={disabled} onClick={() => setCancelPrompt(true)}>Cancel this request</button> : <div className="cancel-confirmation" role="group" aria-label="Confirm cancellation"><h3>Cancel this request?</h3><p>{selected.title} · {selected.merchantId} · {money(selected.amountCents)} USD. Any unused reservation will be released. This is not a refund.</p><div><button className="btn btn-danger" disabled={disabled} onClick={() => action(selected, "cancel")}>Confirm cancellation</button><button className="btn btn-outline" disabled={!!busy} onClick={() => setCancelPrompt(false)}>Keep request</button></div></div>)}
          </div><ReceiptInspector key={selected.id} operation={selected} refreshPurchase={refresh} apiBase="/api/judge"/><section className="record-timeline"><div className="section-heading"><h3>Saved activity</h3></div>{data.events.filter(event => event.operationId === selected.id).map(event => <article className="timeline-event" key={event.id}><span className="timeline-dot"/><div><strong>{readableEvent(event.type)}</strong><time dateTime={new Date(event.createdAt).toISOString()}>{time(event.createdAt)}</time>{eventDetail(event) ? <p>{eventDetail(event)}</p> : <details><summary>Inspect record</summary><pre>{event.detail}</pre></details>}</div></article>)}<p className="form-hint">This view shows up to 100 recent workspace events. Export the complete operation receipts to inspect their saved evidence.</p></section></div></> : <div className="empty-state"><h2 id="judge-detail-heading">Choose a purchase</h2><p>Select a request to inspect its amount, approval and recorded outcome.</p></div>}</section>
        </div>
        <section className="card judge-reset"><div><h2>Repeat the rehearsal</h2><p>A reset creates a new $300 simulated workspace with the two original requests. Export the current evidence first; this view will move to the new workspace.</p><small>{judge ? `This guest session permits up to ${judge.resetLimit} resets and ${judge.mutationLimit} mutations. Limits are enforced by the server.` : ""}</small></div>{!resetPrompt ? <button className="btn btn-outline" disabled={disabled} onClick={() => setResetPrompt(true)}><RotateCcw size={17}/>Reset simulated workspace</button> : <div className="judge-reset-confirm" role="group" aria-label="Confirm simulation reset"><strong>Start a fresh simulation?</strong><p>No live payment will be created, cancelled or refunded.</p><button className="btn btn-primary" disabled={disabled} onClick={reset}>{busy === "reset" ? <LoaderCircle size={17} className="spin"/> : <RotateCcw size={17}/>}Confirm simulated reset</button><button className="text-button" disabled={!!busy} onClick={() => setResetPrompt(false)}>Keep this workspace</button></div>}</section></>}
        {view === "backend" && <section className="judge-backend-grid" aria-label="Read-only AI and backend architecture"><article className="card judge-module"><span className="subtle-pill">This guest deployment</span><h2>Rehearsal configuration</h2><dl><div><dt>Provider</dt><dd>Deterministic simulator</dd></div><div><dt>AI proposals</dt><dd>Sample rules only · no model called</dd></div><div><dt>Funds</dt><dd>Simulated USD allowance</dd></div><div><dt>Authority</dt><dd>Guest approval for this guest’s requests</dd></div><div><dt>Access</dt><dd>Temporary signed session · no owner account</dd></div></dl><p>These are effective limits, not configuration controls. This page cannot enable providers, view secrets or spend real money.</p></article><article className="card judge-module"><span className="subtle-pill">Published owner run · 8 November 2026</span><h2>Recorded AI-to-PayPal route</h2><dl><div><dt>Model</dt><dd>openai/gpt-4.1-mini</dd></div><div><dt>Routing</dt><dd>Vercel AI Gateway · project OIDC</dd></div><div><dt>Model authority</dt><dd>Suggest one permitted catalogue SKU</dd></div><div><dt>Payment path</dt><dd>PayPal sandbox Orders → buyer approval → capture → original-order verification</dd></div><div><dt>Funding scope</dt><dd>One bounded free-credit model attempt was recorded and consumed</dd></div></dl><p>This is the published historical run, not a live connection check in your guest session.</p><a className="text-button" href={LIVE_EVIDENCE} target="_blank" rel="noopener noreferrer">Inspect the dated run<ArrowUpRight size={16}/></a></article><article className="card judge-module judge-module-wide"><span className="section-kicker">ENFORCED APPLICATION BOUNDARIES</span><h2>The model proposes. The application controls execution.</h2><ol className="judge-boundaries"><li><strong>Fixed catalogue</strong><span>The server fixes seller, USD price and permitted items. User text and model output cannot choose arbitrary merchants or prices.</span></li><li><strong>Exact approval</strong><span>Approval is bound to the operation, seller, item, amount, currency and version. Expired execution authority requires explicit renewal.</span></li><li><strong>Held uncertainty</strong><span>Durable intent and request identities precede provider dispatch. Missing responses retain reservations and use the original order for verification.</span></li><li><strong>Inspectable evidence</strong><span>Receipts retain checked provider fields and application events. They are unsigned records; historical approval-version and SKU limits remain documented.</span></li></ol><a className="text-button" href={TESTING} target="_blank" rel="noopener noreferrer">Review source and repeatable checks<ArrowUpRight size={16}/></a></article></section>}
        {view === "lab" && <section className="judge-lab" aria-labelledby="judge-lab-heading"><div className="card judge-lab-summary"><div><span className="section-kicker">AI EVALUATION LAB · VERIFICATION</span><h2 id="judge-lab-heading">Current rehearsal observations</h2><p>The first checks use saved server records. Reload and repeat-check observations come from this browser session. An unchecked item means it has not been observed here—not that it failed.</p></div><span className="judge-lab-count">{checks.filter(check => check.complete).length}<small>of {checks.length} observed</small></span></div><ol className="judge-checklist">{checks.map((check, index) => <li key={check.title}><span className={check.complete ? "is-complete" : ""}>{check.complete ? <Check size={19}/> : index + 1}</span><div><h3>{check.title}</h3><p>{check.detail}</p></div><strong>{check.complete ? "Observed" : "Not yet observed"}</strong></li>)}</ol><button className="btn btn-primary" onClick={() => navigate("desk")}>Continue in the purchase desk<ArrowRight size={17}/></button><div className="judge-lab-records"><article className="card judge-module"><span className="subtle-pill">Local source checkpoint · 8 November 2026</span><h2>210 automated checks passed</h2><p>The recorded local suite covers provider verification, approval and budget controls, uncertainty, owner/guest boundaries and related regressions. This count describes the dated source checkpoint, not tests run by this browser.</p><a className="text-button" href={TESTING} target="_blank" rel="noopener noreferrer">Commands, scope and limits<ArrowUpRight size={16}/></a></article><article className="card judge-module"><span className="subtle-pill">Published hosted evidence</span><h2>Actual AI + PayPal sandbox run</h2><p>The dated run records a genuine model proposal, sandbox buyer approval, response-drop recovery and unchanged totals after a repeated check. It used virtual funds; this guest session remains simulated.</p><a className="text-button" href={LIVE_EVIDENCE} target="_blank" rel="noopener noreferrer">Inspect hosted observations<ArrowUpRight size={16}/></a></article></div><p className="form-hint">Lab verification is project evidence, not an independent audit certificate, signed attestation, production settlement claim or general exactly-once guarantee. Browser observations reset when you start another rehearsal or leave this session.</p></section>}
      </>}
      <section className="judge-evidence-links" aria-labelledby="judge-evidence-heading"><div><span className="section-kicker">REVIEW THE TWO EVIDENCE SOURCES</span><h2 id="judge-evidence-heading">Interactive simulation here. Recorded live sandbox run there.</h2><p>The published 8 November run records an actual runtime AI proposal and PayPal sandbox purchase with virtual funds. This public rehearsal does not repeat that model call or provider transaction.</p></div><div><a href={LIVE_EVIDENCE} target="_blank" rel="noopener noreferrer"><FileCheck2 size={20}/><span>Recorded AI + PayPal sandbox evidence<small>Hosted run, verification fields and stated limits</small></span><ArrowUpRight size={18}/></a><a href={TESTING} target="_blank" rel="noopener noreferrer"><ShieldCheck size={20}/><span>Source and repeatable testing<small>Review the implementation, local checks and scope</small></span><ArrowUpRight size={18}/></a></div></section>
      <footer className="judge-footer"><span>ProofPay · AI Evaluation Lab</span><a href={SOURCE} target="_blank" rel="noopener noreferrer">View source ↗</a><p>Single-seller prototype · guest rehearsal only · unsigned application receipts</p></footer>
    </main>
  </div>;
}
