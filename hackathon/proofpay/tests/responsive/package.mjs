import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=dirname(fileURLToPath(import.meta.url));
const archive=join(root,'proofpay-responsive-qa-static.tar.gz');
// Generated browser assets are self-contained. No node_modules, credentials,
// provider data, production backend, or source repository are packaged.
const args=['--sort=name','--mtime=@0','--owner=0','--group=0','--numeric-owner','-czf',archive,'-C',root,'dist','static','.openai/hosting.json','.gitignore','package.json','README.md','build.mjs','package.mjs','entry.jsx','link.jsx'];
const result=spawnSync('tar',args,{encoding:'utf8'});
if(result.status!==0)throw new Error(result.stderr||'Fixture packaging failed');
console.log(JSON.stringify({archive,sha256:createHash('sha256').update(await readFile(archive)).digest('hex'),synthetic:true,runRequiresNodeModules:false}));
