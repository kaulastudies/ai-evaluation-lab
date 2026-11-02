import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { digest } from '../web/domain.mjs';
test('all seven stable Option A web assets remain byte-for-byte unchanged',async()=>{
 const baseline=JSON.parse(await readFile(new URL('./option-a-baseline.json',import.meta.url)));
 for(const [name,hash]of Object.entries(baseline))assert.equal(await digest(await readFile(new URL('../../sevasetu-careers/web/'+name,import.meta.url),'utf8')),hash,name);
});
