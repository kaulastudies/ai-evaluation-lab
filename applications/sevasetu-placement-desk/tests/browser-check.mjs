import { createRequire } from 'node:module';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { digest } from '../web/domain.mjs';
const require=createRequire(import.meta.url),{chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.DESK_BASE_URL||'http://127.0.0.1:8092/',output=process.env.DESK_RESULTS||'live-results/browser';
await mkdir(output,{recursive:true});
const args=process.env.SEVASETU_SINGLE_PROCESS==='1'?['--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-zygote','--single-process']:[];
const browser=await chromium.launch({headless:true,args,executablePath:process.env.CHROMIUM_PATH||undefined});
const observations=[],errors=[];let manifest;
const ready=page=>page.waitForFunction(()=>!document.body.classList.contains('busy')&&document.querySelector('#notice').textContent.length>0);
const tab=(page,name)=>page.locator(`.nav[data-tab="${name}"]`).click();
const select=async(page,id,value)=>{await page.locator(id).selectOption(value);await ready(page);};
const lookup=async(page,id)=>{await page.locator('#candidate-id').fill(id);await page.getByRole('button',{name:'Retrieve record',exact:true}).click();await ready(page);};
const text=async(page,selector)=>await page.locator(selector).textContent();
const save=async(page,name)=>{const pending=page.waitForEvent('download');await page.getByRole('button',{name,exact:true}).click();const d=await pending;return await readFile(await d.path(),'utf8');};
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base);await page.getByRole('heading',{name:'Arun Kumar (sample)',exact:true}).waitFor();await ready(page);
 manifest=await(await page.request.get(new URL('deployment.json',base).href)).json();
 assert(['local_fixture_api','static_fixture_demo'].includes(manifest.mode));
 if(process.env.DESK_EXPECT_COMMIT)assert.equal(manifest.source_commit,process.env.DESK_EXPECT_COMMIT);
 for(const [name,hash]of Object.entries(manifest.files_sha256||{})){const response=await page.request.get(new URL(name,base).href);assert(response.ok(),name);assert.equal(await digest(await response.text()),hash,name);}
 const record=await text(page,'#record');assert(record.includes('Withheld in this view'));assert(!record.includes('1982-06-14'));assert(!record.includes('72,000'));
 await page.screenshot({path:output+'/desktop-record.png',fullPage:true});observations.push('record lookup with masked DOB and pay');
 await tab(page,'roles');await select(page,'#job','warehouse-supervisor');assert((await text(page,'#role-result')).includes('Recorded requirement gap'));
 await tab(page,'qualifications');await page.getByRole('button',{name:'Fill sample certificate',exact:true}).click();await page.getByRole('button',{name:'Submit for sample verification',exact:true}).click();await ready(page);
 assert((await text(page,'#qualification-list')).includes('Awaiting verification'));
 await tab(page,'roles');assert((await text(page,'#role-result')).includes('Evidence review needed'));
 await page.getByRole('button',{name:'Prepare verified-facts CV',exact:true}).click();await page.getByRole('dialog').waitFor();assert(!(await text(page,'#cv-text')).includes('Warehouse supervision certificate.'));await page.getByRole('button',{name:'Close CV preview',exact:true}).click();observations.push('submitted qualification stays pending and is excluded from CV');
 await select(page,'#actor','verifier');await tab(page,'qualifications');await page.getByRole('button',{name:'Check sample issuer',exact:true}).click();await ready(page);
 assert((await text(page,'#qualification-list')).includes('SAMPLE-ISSUER-CHECK:WS-DEMO-1001'));
 await tab(page,'roles');assert((await text(page,'#role-result')).includes('Documented checks met'));await page.screenshot({path:output+'/desktop-verified-role.png',fullPage:true});
 await page.getByRole('button',{name:'Prepare verified-facts CV',exact:true}).click();await page.getByRole('dialog').waitFor();const cv=await save(page,'Download CV'),receipt=JSON.parse(await save(page,'Download evidence'));
 assert(cv.includes('Warehouse supervision certificate.'));assert.equal(await digest(cv),receipt.cv_sha256);assert(!cv.includes('1982-06-14'));assert(!cv.includes('72000'));assert(receipt.claims.every(c=>c.reference));await page.getByRole('button',{name:'Close CV preview',exact:true}).click();
 const caseReview=JSON.parse(await save(page,'Download case review'));assert.equal(caseReview.synthetic,true);assert(!JSON.stringify(caseReview).includes('72000'));assert(!JSON.stringify(caseReview).includes('1982-06-14'));let previous='0'.repeat(64);for(const event of caseReview.audit){const {hash,...payload}=event;assert.equal(payload.previous,previous);assert.equal(await digest(payload),hash);previous=hash;}
 observations.push('issuer-confirmed qualification credited in explicit role rules; CV and evidence exports match SHA-256');
 await select(page,'#purpose','pay_reference');assert((await text(page,'#record')).includes('72,000'));await select(page,'#actor','counsellor');assert(!(await text(page,'#record')).includes('72,000'));assert(!(await text(page,'#record')).includes('1982-06-14'));observations.push('pay-purpose access is removed when role changes');
 await select(page,'#actor','candidate');await lookup(page,'ESM-DEMO-1002');assert((await text(page,'#notice')).includes('only its own record'));assert((await text(page,'#record')).includes('No case open'));await lookup(page,'ESM-DEMO-1001');assert((await text(page,'#record')).includes('Arun Kumar'));
 await select(page,'#actor','counsellor');await lookup(page,'ESM-DEMO-9999');assert((await text(page,'#notice')).includes('unavailable'));assert((await text(page,'#record')).includes('No case open'));
 await lookup(page,'ESM-DEMO-1005');assert((await text(page,'#notice')).includes('not enabled'));await lookup(page,'ESM-DEMO-1003');await select(page,'#job','driver');assert((await text(page,'#role-result')).includes('Evidence review needed'));assert((await text(page,'#qualification-list')).includes('Revoked in sample source'));
 await lookup(page,'ESM-DEMO-1001');await select(page,'#job','graduate-analyst');assert((await text(page,'#role-result')).includes('Recorded requirement gap'));await select(page,'#job','closed');assert((await text(page,'#role-result')).includes('Application window closed'));observations.push('cross-candidate denial, unknown ID, consent denial, stale source, revoked licence, degree gap and closed vacancy');
 if(process.env.SEVASETU_SINGLE_PROCESS!=='1')await page.close();
 for(const viewport of [{width:1440,height:675},{width:390,height:844}]){
  const p=process.env.SEVASETU_SINGLE_PROCESS==='1'?page:await browser.newPage({viewport,acceptDownloads:true});await p.setViewportSize(viewport);p.on('pageerror',e=>errors.push(e.message));await p.goto(base);await p.getByRole('heading',{name:'Arun Kumar (sample)',exact:true}).waitFor();await ready(p);await tab(p,'roles');await p.getByRole('button',{name:'Prepare verified-facts CV',exact:true}).click({timeout:10000});await p.getByRole('dialog').waitFor();assert((await text(p,'#cv-text')).includes('Completed 10+2.'));await p.getByRole('button',{name:'Close CV preview',exact:true}).click();assert(await p.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));await p.screenshot({path:`${output}/${viewport.width===390?'mobile':'compact'}-role.png`,fullPage:true});if(process.env.SEVASETU_SINGLE_PROCESS!=='1')await p.close();
 }
 assert.deepEqual(errors,[]);observations.push('CV action reachable at 1440×675 and 390×844 without horizontal overflow');
 const report={tested_at:new Date().toISOString(),base_url:base,mode:manifest.mode,source_commit:manifest.source_commit,scope:'Fictional records and issuer responses only; no real defence system or issuer accessed',checks:observations,status:'PASS'};await writeFile(output+'/browser-report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
}catch(error){await writeFile(output+'/failure.json',JSON.stringify({base_url:base,status:'FAIL',error:error.stack,errors},null,2));throw error;}finally{await browser.close();}
