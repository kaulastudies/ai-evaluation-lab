"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Building2, Check, CircleAlert, History, LoaderCircle, LockKeyhole, RefreshCw, Save } from "lucide-react";

export type BusinessProfile = {
  businessName: string; department: string; defaultBudgetCents: number;
  currency: "USD"; version: number; updatedAt: number | null; configured: boolean;
};
type WorkspaceRecord = {
  id: string; mode: "rehearsal" | "sandbox"; profile: "standard" | "sandbox-diagnostic";
  currency: string; budgetCents: number; reservedCents: number; committedCents: number; availableCents: number;
  createdAt: number; businessName: string | null; department: string | null;
  businessProfileVersion: number | null; isActive: boolean; canSelect: boolean; selectionBlockedReason: string | null;
};
type WorkspaceHistoryData = { activeWorkspaceId: string | null; switchBlockedReason: string | null; workspaces: WorkspaceRecord[] };
type BusinessResult = { business?: BusinessProfile; error?: string; code?: string };
const money = (cents: number, currency = "USD") => new Intl.NumberFormat("en-US", { style: "currency", currency }).format(cents / 100);
const timestamp = (value: number) => new Date(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });

export function BusinessSettings({ busy, onSaved, onUnauthorized, onSavingChange }: {
  busy: boolean; onSaved: (business: BusinessProfile) => void; onUnauthorized: () => void; onSavingChange: (saving: boolean) => void;
}) {
  const [business, setBusiness] = useState<BusinessProfile | null>(null);
  const [name, setName] = useState("");
  const [department, setDepartment] = useState("");
  const [budget, setBudget] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [revision, setRevision] = useState(0);
  const mounted = useRef(false);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const apply = useCallback((value: BusinessProfile) => {
    setBusiness(value); setName(value.businessName); setDepartment(value.department);
    setBudget((value.defaultBudgetCents / 100).toFixed(2)); onSaved(value);
  }, [onSaved]);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/business", { cache: "no-store", signal: controller.signal }).then(async response => {
      const result = await response.json() as BusinessResult;
      if (controller.signal.aborted) return;
      if (response.status === 401) onUnauthorized();
      if (!response.ok || !result.business) throw new Error(result.error || "Business settings could not be loaded.");
      apply(result.business);
    }).catch(error => { if (!controller.signal.aborted) setError(error instanceof Error ? error.message : "Business settings could not be loaded."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [revision, apply, onUnauthorized]);
  const budgetValid = /^\d+(?:\.\d{1,2})?$/.test(budget.trim());
  const budgetCents = budgetValid ? Math.round(Number(budget) * 100) : 0;
  const valid = !!name.trim() && name.trim().length <= 120 && !!department.trim() && department.trim().length <= 80 && budgetValid && budgetCents >= 100 && budgetCents <= 100000000;
  const dirty = !!business && (name !== business.businessName || department !== business.department || budgetCents !== business.defaultBudgetCents || !budgetValid);
  async function save() {
    if (!business || !valid || saving || busy) return;
    onSavingChange(true); setSaving(true); setError(""); setNotice("");
    try {
      const response = await fetch("/api/business", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ businessName: name.trim(), department: department.trim(), defaultBudgetCents: budgetCents, version: business.version }) });
      const result = await response.json() as BusinessResult;
      if (!mounted.current) return;
      if (response.status === 401) { onUnauthorized(); return; }
      if (!response.ok || !result.business) throw new Error(result.code === "BUSINESS_VERSION" ? "These settings changed in another session. Your edits are still here. Reload saved settings before saving again." : result.error || "Business settings could not be saved.");
      apply(result.business); setNotice("Business settings saved. New workspaces will use this identity and allowance; existing workspaces are unchanged.");
    } catch (error) { if (mounted.current) setError(error instanceof Error ? error.message : "Business settings could not be saved."); }
    finally { onSavingChange(false); if (mounted.current) setSaving(false); }
  }
  return <div className="business-layout">
    <section className="card business-settings" aria-labelledby="business-settings-title" aria-busy={loading || saving}>
      <div className="section-heading"><div><h2 id="business-settings-title"><Building2 size={20}/>Business profile</h2><p>Defaults for future purchase workspaces.</p></div>{business?.configured && <span className="subtle-pill">Saved · v{business.version}</span>}</div>
      <div className="business-card-body">
        {error && <div className="message error" role="alert"><CircleAlert size={18}/><p>{error}</p></div>}
        {notice && <div className="message success" role="status"><Check size={18}/><p>{notice}</p></div>}
        {loading ? <p className="settings-loading" role="status"><LoaderCircle size={20} className="spin"/>Loading business settings…</p> : business ? <form onSubmit={event => { event.preventDefault(); void save(); }}>
          <div className="business-field"><label htmlFor="business-name">Business name</label><input id="business-name" autoComplete="organization" required maxLength={120} value={name} onChange={event => { setName(event.target.value); setNotice(""); }} disabled={busy || saving}/></div>
          <div className="business-field"><label htmlFor="business-department">Department or cost centre</label><input id="business-department" required maxLength={80} value={department} onChange={event => { setDepartment(event.target.value); setNotice(""); }} disabled={busy || saving} aria-describedby="department-help"/><p id="department-help">A reporting label for this owner’s purchases. It does not create users, roles or separate department budgets.</p></div>
          <div className="business-field"><label htmlFor="business-allowance">Default workspace allowance</label><div className="currency-input"><span>USD</span><input id="business-allowance" inputMode="decimal" required value={budget} onChange={event => { setBudget(event.target.value); setNotice(""); }} disabled={busy || saving} aria-describedby="allowance-help"/></div><p id="allowance-help">Enter $1.00 to $1,000,000.00, with up to two decimal places. This is a test spending limit, not a bank balance or deposit.</p></div>
          <div className="business-form-actions"><button className="btn btn-primary" type="submit" disabled={busy || saving || !valid || (!dirty && business.configured)}>{saving ? <LoaderCircle size={17} className="spin"/> : <Save size={17}/>} {saving ? "Saving…" : "Save business settings"}</button><span>{saving ? "Saving to your owner account" : dirty ? "Unsaved changes" : business.updatedAt ? `Saved ${timestamp(business.updatedAt)}` : "Not configured yet"}</span></div>
        </form> : null}
        {!loading && (error || !business) && <button className="text-button settings-reload" disabled={busy || saving} onClick={() => { setLoading(true); setError(""); setNotice(""); setRevision(value => value + 1); }}><RefreshCw size={16}/>{business ? "Reload saved settings (discard edits)" : "Try again"}</button>}
      </div>
    </section>
    <aside className="card settings-explainer"><span className="queue-icon blue"><LockKeyhole size={22}/></span><h2>One owner. Clear records.</h2><p>Each new workspace keeps a snapshot of your business name, department and allowance.</p><p>Editing these settings does not change earlier purchase approvals, reservations or receipts. Workspace history keeps those records available.</p><div className="inline-note neutral"><p>ProofPay currently supports rehearsal and PayPal sandbox only. No real-money payments or multiuser access are enabled.</p></div></aside>
  </div>;
}

export function WorkspaceHistory({ activeWorkspaceId, busy, onSelect, onUnauthorized }: {
  activeWorkspaceId: string | null; busy: boolean; onSelect: (id: string) => Promise<boolean>; onUnauthorized: () => void;
}) {
  const [history, setHistory] = useState<WorkspaceHistoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [selecting, setSelecting] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/workspaces/history", { cache: "no-store", signal: controller.signal }).then(async response => {
      const result = await response.json() as WorkspaceHistoryData & { error?: string };
      if (controller.signal.aborted) return;
      if (response.status === 401) onUnauthorized();
      if (!response.ok || !Array.isArray(result.workspaces)) throw new Error(result.error || "Workspace history could not be loaded.");
      setHistory(result);
    }).catch(error => { if (!controller.signal.aborted) setError(error instanceof Error ? error.message : "Workspace history could not be loaded."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [activeWorkspaceId, revision, onUnauthorized]);
  async function select(id: string) {
    if (busy || selecting) return;
    setSelecting(id);
    try { if (!await onSelect(id)) { setLoading(true); setRevision(value => value + 1); } }
    finally { setSelecting(null); }
  }
  return <section className="card workspace-history" aria-labelledby="workspace-history-title" aria-busy={loading || !!selecting}>
    <div className="section-heading"><div><h2 id="workspace-history-title"><History size={20}/>Saved workspaces</h2><p>Open an earlier workspace to review its purchases and continue eligible actions.</p></div><button className="btn btn-outline" disabled={busy || loading || !!selecting} onClick={() => { setLoading(true); setError(""); setRevision(value => value + 1); }}><RefreshCw size={16}/>Refresh history</button></div>
    <div className="history-content">
      {error && <div className="message error" role="alert"><CircleAlert size={18}/><p>{error}</p></div>}
      {loading ? <p className="settings-loading" role="status"><LoaderCircle size={20} className="spin"/>Loading saved workspaces…</p> : <>
        {history?.switchBlockedReason && <div className="inline-note warning" role="status"><LockKeyhole size={19}/><p>{history.switchBlockedReason} Review the active workspace before switching. Opening history does not release any reserved allowance.</p></div>}
        {!history?.workspaces.length && !error && <div className="empty-state"><History size={28}/><h3>No saved workspaces yet</h3><p>Start a rehearsal or a PayPal sandbox workspace from Connections. It will appear here with its saved business identity and allowance.</p></div>}
        <div className="workspace-history-list">{history?.workspaces.map(workspace => <article className={`workspace-history-record ${workspace.isActive ? "is-active" : ""}`} key={workspace.id}>
          <div className="history-record-heading"><div><div className="history-labels"><span className="subtle-pill">{workspace.mode === "rehearsal" ? "Rehearsal · simulated" : workspace.profile === "sandbox-diagnostic" ? "PayPal sandbox diagnostic · no AI" : "PayPal sandbox"}</span>{workspace.isActive && <span className="history-active"><Check size={14}/>Active workspace</span>}</div><h3>{workspace.businessName || "Unconfigured business"}</h3><p>{workspace.department || "No department recorded"} · Created <time dateTime={new Date(workspace.createdAt).toISOString()}>{timestamp(workspace.createdAt)}</time></p></div><button className="btn btn-outline" disabled={busy || !!selecting || workspace.isActive || !workspace.canSelect} aria-describedby={!workspace.isActive && workspace.selectionBlockedReason ? `workspace-block-${workspace.id}` : undefined} onClick={() => void select(workspace.id)}>{selecting === workspace.id ? <LoaderCircle size={16} className="spin"/> : null}{workspace.isActive ? "Currently open" : selecting === workspace.id ? "Opening…" : "Open workspace"}</button></div>
          <dl className="history-balances">{[["Allowance", workspace.budgetCents], ["Available", workspace.availableCents], ["Reserved", workspace.reservedCents], [workspace.mode === "rehearsal" ? "Paid · simulated" : "Paid · sandbox", workspace.committedCents]].map(([label, value]) => <div key={String(label)}><dt>{label}</dt><dd>{money(Number(value), workspace.currency)}</dd></div>)}</dl>
          <div className="history-record-footer"><span className="mono">{workspace.id}</span><span>{workspace.businessProfileVersion == null ? "No business snapshot recorded" : `Business profile v${workspace.businessProfileVersion}`}</span></div>
          {!workspace.isActive && workspace.selectionBlockedReason && <p className="history-block-reason" id={`workspace-block-${workspace.id}`}><LockKeyhole size={15}/>{workspace.selectionBlockedReason}</p>}
        </article>)}</div>
        {history && history.workspaces.length > 0 && <p className="form-hint">Workspace amounts are separate test allowances. They are not a combined business balance. Selection changes the active workspace; it does not create, cancel or refund a payment.</p>}
      </>}
    </div>
  </section>;
}
