"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowDownToLine, ArrowRight, ArrowUpRight, Check, CheckCheck, ChevronRight, CircleAlert, FileCheck2, FlaskConical, ListChecks, LoaderCircle, LockKeyhole, Plus, RefreshCw, SearchCheck, ShieldCheck, ShoppingBag, SlidersHorizontal, Sparkles, WalletCards, X } from "lucide-react";

type Mode = "rehearsal" | "sandbox";
type Status = "PROPOSED" | "BUDGET_BLOCKED" | "APPROVED" | "CREATE_DISPATCHED" | "CREATE_UNKNOWN" | "ORDER_READY" | "CAPTURE_DISPATCHED" | "UNKNOWN" | "REVIEW" | "CONFIRMED";
type Operation = {
  id: string; request: string; agentLabel: string; sku: string; title: string;
  amountCents: number; currency: string; merchantId: string; status: Status;
  approvalVersion: number; approvalExpiresAt: number | null; orderId: string | null;
  captureId: string | null; approvalUrl: string | null; providerMode: Mode;
  aiSource: "rehearsal-seed" | "rehearsal-rule" | "model"; rationale: string;
  createdAt: number; updatedAt: number;
};
type EvidenceEvent = { id: string; operationId: string | null; type: string; detail: string; createdAt: number };
type DeskState = {
  workspace: { id: string; mode: Mode; currency: string; budgetCents: number; reservedCents: number; committedCents: number; availableCents: number } | null;
  capabilities: { sandboxReady: boolean; aiReady: boolean };
  catalogue: { sku: string; title: string; description: string; amountCents: number; currency: string }[];
  operations: Operation[]; events: EvidenceEvent[];
};
type ApiEnvelope = { state?: DeskState; error?: string; code?: string };
const labels: Record<Status, string> = {
  PROPOSED: "Needs approval", BUDGET_BLOCKED: "Over allowance", APPROVED: "Allowance reserved",
  CREATE_DISPATCHED: "Creating order", CREATE_UNKNOWN: "Needs verification", ORDER_READY: "Awaiting buyer approval",
  CAPTURE_DISPATCHED: "Needs verification", UNKNOWN: "Needs verification", REVIEW: "Needs review", CONFIRMED: "Payment confirmed",
};
const uncertainStates: Status[] = ["CREATE_DISPATCHED", "CREATE_UNKNOWN", "CAPTURE_DISPATCHED", "UNKNOWN", "REVIEW"];
const statusLabel = (op: Operation) => op.status === "CONFIRMED" && op.providerMode === "rehearsal" ? "Simulated payment confirmed" : op.status === "ORDER_READY" && op.providerMode === "rehearsal" ? "Ready for simulated capture" : labels[op.status];
const time = (v: number) => new Date(v).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
const money = (v: number, currency = "USD") => new Intl.NumberFormat("en-US", { style: "currency", currency }).format(v / 100);
const titleCase = (s: string) => s.toLowerCase().replaceAll("_", " ").replace(/^\w/, x => x.toUpperCase());
class WorkspaceError extends Error {
  constructor(message: string, public status: number) { super(message); }
}
async function readWorkspace(): Promise<DeskState> {
  const response = await fetch("/api/state", { cache: "no-store" });
  const result = await response.json() as ApiEnvelope;
  if (!response.ok || !result.state) throw new WorkspaceError(result.error || "Unable to load the workspace.", response.status);
  return result.state;
}
function safeApprovalUrl(value?: string | null) {
  if (!value) return null;
  try { const u = new URL(value); return u.protocol === "https:" && u.hostname === "www.sandbox.paypal.com" ? u.href : null; }
  catch { return null; }
}

export default function PurchaseDesk() {
  const [data, setData] = useState<DeskState | null>(null);
  const [mode, setMode] = useState<Mode>("rehearsal");
  const [view, setView] = useState("desk");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [request, setRequest] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [fault, setFault] = useState(false);
  const [showSetup, setShowSetup] = useState(false);
  const [filter, setFilter] = useState("all");
  const [authRequired, setAuthRequired] = useState(false);
  const dialogRef = useRef<HTMLElement>(null);
  const busyRef = useRef(false);
  const draftKey = useRef<{ request: string; key: string } | null>(null);
  const requestSequence = useRef(0);

  const refresh = useCallback(async () => {
    const sequence = ++requestSequence.current;
    const state = await readWorkspace();
    if (sequence === requestSequence.current) {
      setData(state); setAuthRequired(false);
      if (state.workspace) setMode(state.workspace.mode);
    }
    return state;
  }, []);
  useEffect(() => {
    let active = true;
    readWorkspace().then(state => {
      if (!active) return;
      setData(state);
      if (state.workspace) setMode(state.workspace.mode);
    }).catch((e: Error) => {
      if (!active) return;
      setError(e.message); setAuthRequired(e instanceof WorkspaceError && e.status === 401);
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    const onFocus = () => { if (!busyRef.current) refresh().catch(() => {}); };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [refresh]);
  useEffect(() => {
    if (!showSetup) return;
    const previous = document.activeElement as HTMLElement | null;
    const dialog = dialogRef.current;
    const buttons = dialog?.querySelectorAll<HTMLElement>('button, a[href], input, textarea, [tabindex="0"]');
    buttons?.[0]?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setShowSetup(false);
      if (event.key !== "Tab" || !buttons?.length) return;
      const first = buttons[0], last = buttons[buttons.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", onKey); document.body.style.overflow = previousOverflow; previous?.focus(); };
  }, [showSetup]);

  const ops = data?.operations || [];
  const selected = ops.find(o => o.id === selectedId) || ops[0];
  const paypalReady = data?.capabilities.sandboxReady ?? false;
  const aiReady = data?.capabilities.aiReady ?? false;
  const sandboxReady = paypalReady && aiReady;
  const ws = data?.workspace;
  const total = ws?.budgetCents ?? 0;
  const reserved = ws?.reservedCents ?? 0;
  const paid = ws?.committedCents ?? 0;
  const available = ws?.availableCents ?? 0;
  const unresolved = ops.filter(o => uncertainStates.includes(o.status));
  const pending = ops.filter(o => o.status === "PROPOSED");
  const displayed = ops.filter(o => filter === "all" || (filter === "approval" ? o.status === "PROPOSED" : filter === "attention" ? uncertainStates.includes(o.status) : o.status === "CONFIRMED"));
  const eventList = selected ? (data?.events || []).filter(e => e.operationId === selected.id) : [];
  const selectedUrl = safeApprovalUrl(selected?.approvalUrl);

  async function act(key: string, path: string, body: Record<string, unknown> = {}) {
    if (busyRef.current) return;
    busyRef.current = true; ++requestSequence.current;
    setBusy(key); setError(""); setNotice("");
    try {
      const payload = path.includes("/operations/") && !path.endsWith("/reconcile") ? { approvalVersion: selected?.approvalVersion, ...body } : body;
      const res = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const json = await res.json() as ApiEnvelope;
      if (json.state) {
        setData(json.state);
        if (json.state.workspace) setMode(json.state.workspace.mode);
        const newOperation = json.state.operations.find(op => !ops.some(previous => previous.id === op.id));
        if (newOperation) setSelectedId(newOperation.id);
      }
      if (!res.ok) {
        if (res.status === 401) setAuthRequired(true);
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
  const propose = () => {
    if (!draftKey.current || draftKey.current.request !== request) draftKey.current = { request, key: crypto.randomUUID() };
    return act("propose", "/api/proposals", { request, mode, idempotencyKey: draftKey.current.key }).then(result => {
      if (result) { setRequest(""); draftKey.current = null; }
    });
  };
  const start = () => act("start", "/api/rehearsal/start").then(j => { if (j) { setView("desk"); setFilter("all"); setFault(false); setNotice("A new rehearsal workspace is ready. All purchases and provider outcomes in this workspace are simulated."); } });
  const exportEvidence = async () => {
    if (busyRef.current || !ops.length) return;
    busyRef.current = true; setBusy("export"); setError("");
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

  return <div className="desk-shell">
    <a className="skip-link" href="#main-content">Skip to workspace</a>
    <aside className="sidebar">
      <Link className="brand" href="/" aria-label="ProofPay home"><span className="brand-symbol"><CheckCheck size={25}/></span><span>ProofPay<span className="brand-caption">PURCHASE DESK</span></span></Link>
      <div className="workspace-label"><span className="workspace-monogram">ST</span><div>Studio team<small>Owner workspace</small></div><LockKeyhole size={13}/></div>
      <p className="nav-section">WORKSPACE</p>
      <nav aria-label="Main navigation">
        <button className={view === "desk" ? "nav-item active" : "nav-item"} onClick={() => setView("desk")}><WalletCards size={18}/>Purchase desk{pending.length > 0 && <span className="nav-count">{pending.length}</span>}</button>
        <button className={view === "evidence" ? "nav-item active" : "nav-item"} onClick={() => setView("evidence")}><FileCheck2 size={18}/>Evidence ledger</button>
        <button className={view === "readiness" ? "nav-item active" : "nav-item"} onClick={() => setView("readiness")}><SlidersHorizontal size={18}/>Connections<span className="nav-status-dot"/></button>
      </nav>
      <div className="sidebar-note"><ShieldCheck size={22}/><p>You approve.<br/>The ledger keeps track.</p><span>Every purchase stays tied to its approval and recorded outcome.</span></div>
      <div className="sidebar-bottom"><span className="mini-dot"/> Sandbox prototype<small>Controlled sample catalogue</small></div>
    </aside>

    <div className="main-shell">
      <header className="topbar"><div className="breadcrumb">Workspace <ChevronRight size={13}/><strong>{view === "desk" ? "Purchase desk" : view === "evidence" ? "Evidence ledger" : "Connections"}</strong></div><div className="topbar-right"><span className={`environment-pill ${mode}`}><span/>{mode === "rehearsal" ? "Rehearsal · simulated" : "PayPal sandbox"}</span><span className="owner-avatar" title="Workspace owner">O</span></div></header>
      <main id="main-content" aria-busy={loading || !!busy}>
        <div className="page-heading"><div><p className="eyebrow">CONTROLLED PURCHASING</p><h1>{view === "desk" ? "Your purchase desk." : view === "evidence" ? "Follow the evidence." : "Ready for the real run?"}</h1><p className="page-subtitle">{view === "desk" ? "A shared allowance for your studio. Every purchase stays accountable." : view === "evidence" ? "The original request, owner decision and payment record — together." : "Connection status is separate from a verified end-to-end payment."}</p></div><button className="btn btn-outline export-button" onClick={exportEvidence} disabled={!ops.length || !!busy}>{busy === "export" ? <LoaderCircle className="spin" size={16}/> : <ArrowDownToLine size={16}/>}Export evidence</button></div>

        {error && <div className="message error" role="alert"><CircleAlert size={19}/><div><strong>Action needs attention</strong><p>{error}</p>{authRequired && <a className="btn btn-outline" href="/signin-with-chatgpt?return_to=%2F" target="_top">Sign in to your workspace<ArrowUpRight size={14}/></a>}</div><button aria-label="Dismiss error" onClick={() => setError("")}><X size={17}/></button></div>}
        {notice && <div className="message success" role="status"><Check size={19}/><p>{notice}</p><button aria-label="Dismiss message" onClick={() => setNotice("")}><X size={17}/></button></div>}
        <div className="readiness-strip"><div className="readiness-icon"><FlaskConical size={21}/></div><div><strong>{mode === "rehearsal" ? "A safe space to test the workflow" : "Sandbox payments only"}</strong><p>{mode === "rehearsal" ? "Rehearsal uses sample requests and a simulated provider. No real money moves; these are not live AI or PayPal results." : "The catalogue is a demonstration from one sandbox merchant. Owner approval is required before capture."}</p></div><button onClick={() => setView("readiness")}>View connections<ArrowUpRight size={15}/></button></div>

        {view === "readiness" ? <section className="connection-grid">
          <article className="card connection-card"><div className="connection-logo paypal-word">PayPal</div><span className={`status ${paypalReady ? "confirmed" : "proposed"}`}>{paypalReady ? "Configured" : "Not connected"}</span><h2>Sandbox merchant</h2><p>Orders and captures from a single test seller. Buyer approval happens on PayPal.</p><ul className="plain-checks"><li><Check size={15}/>Production payments disabled</li><li><LockKeyhole size={15}/>Credentials remain on the server</li><li><SearchCheck size={15}/>Captured amounts checked before confirmation</li></ul></article>
          <article className="card connection-card"><div className="connection-logo ai-logo"><Sparkles size={24}/></div><span className={`status ${aiReady ? "confirmed" : "proposed"}`}>{aiReady ? "Configured" : "Not connected"}</span><h2>AI proposal service</h2><p>Turns a buying request into a catalogue proposal. The application validates item, quantity and price.</p><ul className="plain-checks"><li><Check size={15}/>AI can propose, not authorize</li><li><LockKeyhole size={15}/>No access to payment credentials</li><li><ListChecks size={15}/>Every alternative needs a fresh approval</li></ul></article>
          <article className="card connection-setup"><div><span className="eyebrow">INTEGRATION CHECKPOINT</span><h2>{sandboxReady ? "Configuration is present." : "The real sandbox run is still pending."}</h2><p>{sandboxReady ? "Configuration alone does not verify a purchase. Run the complete owner approval and capture journey, then inspect the evidence." : "A configured PayPal sandbox merchant and an AI provider are required for the live path. You can exercise the controls in an explicitly labelled rehearsal now."}</p></div><button className="btn btn-primary" onClick={sandboxReady ? ()=>act("sandbox-start","/api/workspaces",{mode:"sandbox"}).then(j=>{if(j){setView("desk");setFilter("all");setSelectedId(null);setFault(false);}}) : start} disabled={!!busy}>{busy ? <LoaderCircle className="spin" size={16}/> : <FlaskConical size={16}/>}{sandboxReady ? "Start PayPal sandbox workspace" : "Start rehearsal"}</button></article>
        </section> : <>
        <section className="budget-row" aria-label="Allowance summary">
          <div className="budget-card available"><div className="metric-label">Available to spend<WalletCards size={16}/></div><div className="money-value">{loading || !ws ? "—" : money(available)}<span>USD</span></div><div className="allowance-bar"><span style={{width: `${total ? Math.max(0, Math.min(100, available/total*100)) : 0}%`}}/></div><small>{total ? `of ${money(total)} shared allowance` : "Start a workspace to set the allowance"}</small></div>
          <div className="budget-card"><div className="metric-label">Reserved<LockKeyhole size={16}/></div><div className="money-value">{loading || !ws ? "—" : money(reserved)}</div><small>Committed to approved purchases</small></div>
          <div className="budget-card"><div className="metric-label">Paid<CheckCheck size={16}/></div><div className="money-value">{loading || !ws ? "—" : money(paid)}</div><small>{mode === "rehearsal" ? "Confirmed by simulated provider" : "Confirmed from provider evidence"}</small></div>
          <div className={`budget-card ${unresolved.length ? "attention" : "verification"}`}><div className="metric-label">Needs verification<SearchCheck size={17}/></div><div className="money-value">{loading || !ws ? "—" : unresolved.length}<span>{unresolved.length === 1 ? "purchase" : "purchases"}</span></div><small>Allowance stays reserved until checked</small></div>
        </section>

        {view === "desk" && <section className="composer card"><div className="composer-heading"><span className="ai-symbol"><Sparkles size={20}/></span><div><h2>What does your team need?</h2><p>Describe the need. You decide what gets approved.</p></div><span className="small-label">SAMPLE CATALOGUE · USD</span></div><form onSubmit={e => { e.preventDefault(); void propose(); }}><label className="sr-only" htmlFor="purchase-request">Buying request</label><textarea id="purchase-request" value={request} disabled={!!busy || authRequired} onChange={e=>setRequest(e.target.value)} placeholder="For example: Our studio needs a workflow review, within the available allowance." maxLength={2000} rows={2}/><div className="composer-footer"><span><ShieldCheck size={14}/>{mode === "rehearsal" ? "Sample proposals. You authorize." : "AI proposes. You authorize."}</span><button className="btn btn-primary" disabled={!!busy || !request.trim() || (mode === "sandbox" && !sandboxReady) || !data?.workspace} type="submit">{busy === "propose" ? <LoaderCircle size={15} className="spin"/> : <Sparkles size={15}/>} {mode === "rehearsal" ? "Create sample proposal" : "Ask AI for a proposal"}<ArrowRight size={15}/></button></div></form><div className="example-row"><span>Try a request</span><button disabled={!!busy} onClick={()=>setRequest("Our studio needs a workflow review within $180.")}>Workflow review</button><button disabled={!!busy} onClick={()=>setRequest("Our studio needs a design review within $160.")}>Design review</button><button disabled={!!busy} onClick={()=>setRequest(`Suggest a cheaper option within ${money(available)} of available allowance.`)}>Find a cheaper option</button></div></section>}

        <div className="workspace-grid"><section className="card requests-panel"><div className="panel-heading"><div><h2>{view === "evidence" ? "Recorded purchases" : "Purchase requests"}<span className="count-chip">{ops.length}</span></h2><p>Each request keeps its own approval and outcome.</p></div><button className="icon-btn" title="Refresh workspace" aria-label="Refresh workspace" disabled={!!busy} onClick={()=>{setBusy("refresh");refresh().catch(e=>setError(e.message)).finally(()=>setBusy(null));}}><RefreshCw className={busy === "refresh" ? "spin" : ""} size={16}/></button></div><div className="filter-tabs" aria-label="Filter purchases">{[["all","All requests"],["approval","For approval"],["attention","Needs verification"],["paid","Confirmed"]].map(([v,l])=><button key={v} aria-pressed={filter===v} className={filter===v?"active":""} onClick={()=>setFilter(v)}>{l}</button>)}</div>
          {loading ? <div className="empty-state"><LoaderCircle className="spin" size={25}/><h3>Loading your workspace</h3><p>Retrieving saved requests and ledger records.</p></div> : !displayed.length ? <div className="empty-state"><div className="empty-illustration"><ShoppingBag size={31}/><span><Check size={14}/></span></div><h3>{ops.length ? "Nothing in this view." : "A purchase starts with a request."}</h3><p>{ops.length ? "Choose another filter to see the remaining purchases." : "Start the $300 rehearsal to compare two sample requests and explore a payment whose response goes missing."}</p>{!ops.length && <button className="btn btn-primary" onClick={start} disabled={!!busy || authRequired || loading}>{busy === "start" ? <LoaderCircle size={15} className="spin"/> : <FlaskConical size={15}/>}Start $300 rehearsal<ArrowRight size={15}/></button>}</div> : <div className="operation-list">{displayed.map((op,index)=><button className={`operation-row ${selected?.id===op.id?"selected":""}`} key={op.id} aria-pressed={selected?.id===op.id} onClick={()=>{setSelectedId(op.id);setFault(false);}}><span className={`item-icon item-${index%3}`}><ShoppingBag size={19}/></span><span className="operation-body"><strong>{op.title}</strong><span>{op.request || op.rationale || "Owner approval required before payment"}</span><em><span className={`status ${op.status.toLowerCase()}`}>{statusLabel(op)}</span><span className="row-time">{time(op.createdAt)}</span></em></span><span className="operation-amount">{money(op.amountCents,op.currency)}<ChevronRight size={16}/></span></button>)}</div>}
          <div className="panel-bottom"><span><LockKeyhole size={12}/>Allowances are enforced on the server.</span>{ops.length>0 && <button onClick={start} disabled={!!busy || authRequired || loading}>New rehearsal<Plus size={13}/></button>}</div>
        </section>

        <aside className="card detail-panel"><div className="panel-heading"><div><p className="eyebrow">PURCHASE RECORD</p><h2>{selected ? "From intent to outcome" : "Every decision leaves a record."}</h2></div><FileCheck2 size={20}/></div>{selected ? <>
          <div className="detail-summary"><span className={`status ${selected.status.toLowerCase()}`}>{statusLabel(selected)}</span><h3>{selected.title}</h3><div className="detail-price">{money(selected.amountCents, selected.currency)}<span>{selected.currency || "USD"}</span></div><p>{selected.rationale || selected.request}</p><dl><div><dt>Operation</dt><dd title={selected.id}>{selected.id.slice(0,12)}…</dd></div><div><dt>Proposal</dt><dd>{selected.aiSource === "model" ? "AI model" : selected.aiSource === "rehearsal-seed" ? "Rehearsal sample" : "Rehearsal rule"}</dd></div><div><dt>Provider</dt><dd>{selected.providerMode==="rehearsal"?"Simulated provider":"PayPal sandbox"}</dd></div>{selected.orderId && <div><dt>Order</dt><dd>{selected.orderId}</dd></div>}{selected.captureId && <div><dt>Capture</dt><dd>{selected.captureId}</dd></div>}</dl></div>
          <div className="operation-actions">
            {selected.status==="PROPOSED" && <><p>Approval reserves this exact amount from the shared allowance.</p><button className="btn btn-primary full" disabled={!!busy} onClick={()=>act(selected.id,"/api/operations/"+selected.id+"/approve")}>{busy===selected.id?<LoaderCircle className="spin" size={16}/>:<Check size={16}/>}Approve & reserve {money(selected.amountCents)}</button></>}
            {selected.status === "APPROVED" && <button className="btn btn-primary full" disabled={!!busy} onClick={()=>act(selected.id,"/api/operations/"+selected.id+"/create-order")}>{busy===selected.id?<LoaderCircle className="spin" size={16}/>:<ArrowRight size={16}/>}Create {selected.providerMode==="rehearsal"?"simulated":"PayPal"} order</button>}
            {selected.status === "ORDER_READY" && <><p>{mode==="rehearsal"?"The rehearsal simulates buyer approval and capture. No PayPal request is made.":"Open PayPal and approve as the sandbox buyer, then capture the approved order."}</p>{selectedUrl && <a className="btn btn-outline full" href={selectedUrl} target="_blank" rel="noopener noreferrer">Open PayPal approval<ArrowUpRight size={16}/></a>}<label className="fault-control"><input type="checkbox" disabled={!!busy} checked={fault} onChange={e=>setFault(e.target.checked)}/><span>Drop the capture response<small>Deliberate fault for recovery testing</small></span></label><button className="btn btn-primary full" disabled={!!busy} onClick={()=>act(selected.id,"/api/operations/"+selected.id+"/capture",{fault:fault?"drop-response":undefined})}>{busy===selected.id?<LoaderCircle className="spin" size={16}/>:<CheckCheck size={16}/>}Capture {mode==="rehearsal"?"simulated payment":"approved order"}</button></>}
            {uncertainStates.includes(selected.status) && <><div className="uncertain-explanation"><CircleAlert size={17}/><p>{selected.status === "REVIEW" ? "The provider record needs review before this purchase can be confirmed." : "The outcome is not yet verified. A missing response does not mean payment failed."} The allowance stays reserved.</p></div><button className="btn btn-primary full" disabled={!!busy} onClick={()=>act(selected.id,"/api/operations/"+selected.id+"/reconcile")}>{busy===selected.id?<LoaderCircle className="spin" size={16}/>:<SearchCheck size={17}/>}Check {mode==="rehearsal"?"simulated":"PayPal"} outcome</button></>}
            {selected.status === "CONFIRMED" && <><div className="confirmed-explanation"><ShieldCheck size={18}/><p>{mode === "rehearsal" ? "Simulated evidence confirms this rehearsal purchase." : "Matched PayPal evidence confirms this purchase."} Its amount is recorded once in the ledger.</p></div><button className="btn btn-outline full" disabled={!!busy} onClick={()=>act(selected.id,"/api/operations/"+selected.id+"/reconcile")}><SearchCheck size={16}/>Check outcome again</button></>}
            {selected.status === "BUDGET_BLOCKED" && <><p>{`This request does not fit the available allowance. A new proposal needs a new approval.`}</p><button className="btn btn-outline full" disabled={!!busy} onClick={()=>{setRequest(`Suggest a cheaper alternative to ${selected.title||selected.sku||"this purchase"} within ${money(available)}. Use only the permitted catalogue.`);setView("desk");requestAnimationFrame(()=>document.getElementById("purchase-request")?.focus());}}><Sparkles size={16}/>Request an alternative</button></>}
          </div>
          <div className="evidence-timeline"><h4>Activity & evidence<span>{eventList.length}</span></h4>{eventList.length ? eventList.map(e=><div className="timeline-event" key={e.id}><span className="timeline-dot"/><div><strong>{titleCase(e.type)}</strong><small>{time(e.createdAt)}</small>{e.detail!=null && <details><summary>Inspect record</summary><pre>{typeof e.detail==="string"?e.detail:JSON.stringify(e.detail,null,2)}</pre></details>}</div></div>) : <p className="muted-text">Select an action to add its record to the timeline.</p>}</div>
        </> : <div className="evidence-empty"><div className="steps-diagram"><span><Sparkles size={18}/>Request</span><i/><span><Check size={18}/>Approve</span><i/><span><SearchCheck size={18}/>Verify</span></div><p>Select a purchase to inspect its approval, provider reference and outcome.</p><div className="principle"><LockKeyhole size={19}/><div><strong>Uncertain is a valid state.</strong><p>A missing response keeps the allowance reserved until the original outcome is checked.</p></div></div></div>}</aside></div>
        </>}
        <footer className="workspace-footer"><span><ShieldCheck size={14}/>ProofPay · AI Evaluation Lab</span><p>Single-merchant sandbox prototype. Rehearsal records are simulated.</p><button onClick={()=>setShowSetup(true)}>About this workspace<ArrowUpRight size={13}/></button></footer>
      </main>
    </div>
    {showSetup && <div className="modal-backdrop" onClick={()=>setShowSetup(false)}><section className="about-modal" ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="about-title" onClick={e=>e.stopPropagation()}><button className="icon-btn modal-close" aria-label="Close about" onClick={()=>setShowSetup(false)}><X size={19}/></button><span className="brand-symbol"><CheckCheck size={24}/></span><h2 id="about-title">A clear answer after an uncertain payment.</h2><p>ProofPay connects a buying request, owner approval, shared allowance and checked provider outcome. This is a single-seller prototype by AI Evaluation Lab for the PayPal AI Hackathon.</p><p>Rehearsal uses sample inputs and simulated payment records. A configured connection is not proof of a live integration. Actual PayPal sandbox and model results must be verified separately.</p><button className="btn btn-primary" onClick={()=>setShowSetup(false)}>Back to the desk<ArrowRight size={16}/></button></section></div>}
  </div>;
}
