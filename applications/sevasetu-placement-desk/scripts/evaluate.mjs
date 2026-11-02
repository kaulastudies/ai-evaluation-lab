import { readFile, mkdir, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { FixtureService } from '../web/service.mjs';
import { digest } from '../web/domain.mjs';
const raw=await readFile(new URL('../fixtures/sample-data.json',import.meta.url),'utf8'),data=JSON.parse(raw),service=new FixtureService(data);
const cases=[['ESM-DEMO-1001','warehouse-assistant','documented_checks_met'],['ESM-DEMO-1001','warehouse-supervisor','recorded_gap'],['ESM-DEMO-1002','network-support','documented_checks_met'],['ESM-DEMO-1001','graduate-analyst','recorded_gap'],['ESM-DEMO-1003','driver','needs_review'],['ESM-DEMO-1004','warehouse-assistant','recorded_gap'],['ESM-DEMO-1001','closed','not_open']];
const results=[];for(const [candidate_id,role_id,expected]of cases){const outcome=await service.assess(candidate_id,role_id);assert.equal(outcome.state,expected);results.push({candidate_id,role_id,expected,actual:outcome.state,status:'PASS'});}
await mkdir('live-results',{recursive:true});const report={tested_at:new Date().toISOString(),mode:'deterministic_synthetic_evaluation',fixture_sha256:await digest(raw),cases:results,status:'PASS'};await writeFile('live-results/evaluation.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
