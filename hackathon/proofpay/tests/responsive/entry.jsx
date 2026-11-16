import React from 'react';
import {createRoot} from 'react-dom/client';
import PurchaseDesk from 'proofpay-component';

// This module exists only in the isolated QA harness. No production modules
// except the unmodified rendered component are imported. There is no backend.
const params=new URLSearchParams(window.location.search);
const scenario=params.get('scenario')||'rehearsal';
const sandbox=['checkout','manual-review'].includes(scenario);
const now=Date.now(),mode=sandbox?'sandbox':'rehearsal';
const catalogue=[
  {sku:'workflow-review',title:'Workflow Review',description:'Synthetic layout sample of the controlled workflow review.',amountCents:18000,currency:'USD'},
  {sku:'design-review',title:'Design Review',description:'Synthetic layout sample of the controlled design review.',amountCents:16000,currency:'USD'},
  {sku:'starter-review',title:'Starter Review',description:'Synthetic layout sample of the smaller review package.',amountCents:9000,currency:'USD'},
];
function operation(id,status,sku='starter-review',extra={}) {
  const item=catalogue.find(x=>x.sku===sku);
  return {id,request:'Synthetic QA fixture: a long studio purchase request used to inspect wrapping and readable controls.',agentLabel:'Synthetic QA agent',sku,title:item.title,amountCents:item.amountCents,currency:'USD',merchantId:'QA-SYNTHETIC-MERCHANT-REFERENCE-123456789',status,approvalVersion:2,approvalExpiresAt:['PROPOSED','BUDGET_BLOCKED','CANCELLED'].includes(status)?null:now+600000,orderId:null,captureId:null,approvalUrl:null,providerMode:mode,aiSource:sandbox?'model':'rehearsal-rule',rationale:'Synthetic visual fixture only. No model, PayPal, buyer approval or payment execution took place.',createdAt:now-120000,updatedAt:now-30000,...extra};
}
let operations;
if(scenario==='checkout') operations=[
  operation('qa-checkout-operation-0001','ORDER_READY','workflow-review',{orderId:'QA-ORDER-NOT-A-REAL-PAYPAL-ORDER',approvalUrl:'https://www.sandbox.paypal.com/checkoutnow?token=QA-NOT-REAL'}),
  operation('qa-proposed-operation-0002','PROPOSED','starter-review'),
  operation('qa-blocked-operation-0003','BUDGET_BLOCKED','design-review'),
];
else if(scenario==='manual-review') operations=[operation('qa-manual-review-0001','CREATE_UNKNOWN','workflow-review'),operation('qa-proposed-operation-0002','PROPOSED')];
else if(['empty','no-workspace'].includes(scenario)) operations=[];
else operations=[
  operation('qa-proposed-operation-0001','PROPOSED','workflow-review'),
  operation('qa-blocked-operation-0002','BUDGET_BLOCKED','design-review'),
  operation('qa-expired-operation-0003','APPROVED','starter-review',{approvalExpiresAt:now-60000}),
  operation('qa-unknown-operation-0004','UNKNOWN','starter-review',{orderId:'QA-REHEARSAL-ORDER-0004'}),
  operation('qa-confirmed-operation-0005','CONFIRMED','starter-review',{orderId:'QA-REHEARSAL-ORDER-0005',captureId:'QA-REHEARSAL-CAPTURE-0005'}),
  operation('qa-cancelled-operation-0006','CANCELLED','design-review'),
];
const held=['APPROVED','CREATE_DISPATCHED','CREATE_UNKNOWN','ORDER_READY','CAPTURE_DISPATCHED','UNKNOWN','REVIEW'];
const reservedCents=operations.filter(x=>held.includes(x.status)).reduce((a,x)=>a+x.amountCents,0);
const committedCents=operations.filter(x=>x.status==='CONFIRMED').reduce((a,x)=>a+x.amountCents,0);
const events=operations.map((op,index)=>({id:`qa-event-${index}`,operationId:op.id,type:index===0?'PROPOSAL_CREATED':'QA_FIXTURE_STATE',detail:index===0?JSON.stringify({schemaVersion:1,source:op.aiSource,sku:op.sku,rationale:op.rationale}):`Synthetic visual fixture: ${op.status}. No provider operation occurred.`,createdAt:now-index*10000}));
const business={businessName:'Synthetic QA Business',department:'Operations and service purchasing',defaultBudgetCents:45000,currency:'USD',version:2,updatedAt:now-60000,configured:true};
const state={workspace:scenario==='no-workspace'?null:{id:'qa-workspace-not-production',mode,profile:'standard',businessName:business.businessName,department:business.department,businessProfileVersion:1,currency:'USD',budgetCents:30000,reservedCents,committedCents,availableCents:30000-reservedCents-committedCents,createdAt:now},capabilities:{sandboxReady:sandbox,aiReady:sandbox},catalogue,operations,events};
const switchBlockedReason=reservedCents>0?'Synthetic QA fixture: resolve the active workspace reservations before switching.':null;
const history={activeWorkspaceId:state.workspace?.id??null,switchBlockedReason,workspaces:scenario==='no-workspace'?[]:[
  {...state.workspace,isActive:true,canSelect:true,selectionBlockedReason:null},
  {id:'qa-prior-workspace-not-production-0002',mode:'rehearsal',profile:'standard',currency:'USD',budgetCents:45000,reservedCents:0,committedCents:18000,availableCents:27000,createdAt:now-86400000,businessName:'Synthetic QA Business — prior workspace',department:'Operations and service purchasing',businessProfileVersion:1,isActive:false,canSelect:!switchBlockedReason,selectionBlockedReason:switchBlockedReason},
]};
const requests=[];
window.__proofpayQa={synthetic:true,scenario,requests,state,blockedActions:[],networkPolicy:'All fetch is handled here. External navigation and downloads are blocked.'};
window.fetch=async(input,init={})=>{
  const url=new URL(input instanceof Request?input.url:String(input),window.location.href);
  const method=init.method||(input instanceof Request?input.method:'GET');
  requests.push({method,path:url.pathname,body:init.body||null,at:Date.now()});
  await new Promise(resolve=>setTimeout(resolve,150));
  if(url.pathname==='/api/state'&&method==='GET') {
    if(scenario==='setup-pending')return Response.json({error:'Synthetic QA fixture: secure owner sign-in is not configured.',code:'AUTH_NOT_CONFIGURED'},{status:503});
    return Response.json({state});
  }
  if(url.pathname==='/api/business'&&method==='GET')return Response.json({business,synthetic:true});
  if(url.pathname==='/api/workspaces/history'&&method==='GET')return Response.json({...history,synthetic:true});
  if(url.pathname.endsWith('/evidence')&&method==='GET') {
    const op=operations.find(x=>url.pathname.includes(x.id));
    if(!op)return Response.json({error:'Synthetic fixture purchase missing.'},{status:404});
    const verificationRecords=op.status==='CONFIRMED'?[{
      schemaVersion:1,mode:op.providerMode,simulated:true,source:'simulated-provider-lookup',checkedAt:now-15000,operationId:op.id,
      order:{id:op.orderId,status:'COMPLETED',referenceId:op.id,customId:op.id,payeeMerchantId:op.merchantId,amount:{value:(op.amountCents/100).toFixed(2),currency:op.currency}},
      capture:{id:op.captureId,status:'COMPLETED',finalCapture:true,amount:{value:(op.amountCents/100).toFixed(2),currency:op.currency}},
    }]:[];
    const receiptEvents=events.filter(event=>event.operationId===op.id);
    if(verificationRecords.length)receiptEvents.push({id:'qa-verification-event',type:'PROVIDER_VERIFIED',detail:JSON.stringify(verificationRecords[0]),createdAt:now-15000});
    return Response.json({synthetic:true,claim:'LOCAL VISUAL QA FIXTURE. Not execution evidence.',operation:op,approvalDigest:op.approvalExpiresAt?'0'.repeat(64):null,verificationRecords,events:receiptEvents});
  }
  return Response.json({error:'Local visual QA fixture: mutations are disabled. No payment or backend request was sent.',code:'QA_READ_ONLY',state},{status:409});
};
function blockAnchor(anchor) {
  if(!anchor)return false;
  let url;try{url=new URL(anchor.href,window.location.href)}catch{return false}
  const kind=anchor.hasAttribute('download')?'download':url.origin!==window.location.origin?'external-navigation':null;
  if(!kind)return false;
  const action={kind,label:anchor.getAttribute('download')||anchor.textContent?.trim()||'external link',at:Date.now()};
  window.__proofpayQa.blockedActions.push(action);
  window.parent.postMessage({type:'proofpay-qa-blocked-action',...action},window.location.origin);
  return true;
}
document.addEventListener('click',event=>{
  if(blockAnchor(event.target.closest?.('a'))){event.preventDefault();event.stopImmediatePropagation();}
},true);
// Export creates a detached anchor, so its synthetic .click() does not bubble
// through document. Intercept only in this fixture to keep downloads local-only.
const originalAnchorClick=HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click=function(){if(!blockAnchor(this))return originalAnchorClick.call(this)};
createRoot(document.getElementById('root')).render(<PurchaseDesk/>);
