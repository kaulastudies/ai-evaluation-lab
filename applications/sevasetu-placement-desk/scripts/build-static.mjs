import { mkdir, readdir, copyFile, readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { digest } from '../web/domain.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const target=path.resolve(process.argv[2]||'live-results/static');
if(target===root||root.startsWith(target+path.sep))throw new Error('Choose a separate build directory');
await mkdir(target,{recursive:true});if((await readdir(target)).length)throw new Error('Build directory must be empty');
const files={};for(const name of await readdir(path.join(root,'web'))){await copyFile(path.join(root,'web',name),path.join(target,name));files[name]=await digest(await readFile(path.join(target,name),'utf8'));}
await copyFile(path.join(root,'fixtures/sample-data.json'),path.join(target,'sample-data.json'));files['sample-data.json']=await digest(await readFile(path.join(target,'sample-data.json'),'utf8'));
await writeFile(path.join(target,'deployment.json'),JSON.stringify({mode:'static_fixture_demo',source_commit:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),synthetic:true,files_sha256:files},null,2)+'\n');console.log('Built independent static sample demo: '+target);
