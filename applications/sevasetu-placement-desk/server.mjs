import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { randomBytes } from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import { FixtureService } from './web/service.mjs';
import { DeskError, actorFor } from './web/domain.mjs';

const ROOT=path.dirname(fileURLToPath(import.meta.url));
const DATA=JSON.parse(await readFile(path.join(ROOT,'fixtures/sample-data.json'),'utf8'));
const FILES={'/':'index.html','/index.html':'index.html','/style.css':'style.css','/app.mjs':'app.mjs','/domain.mjs':'domain.mjs','/service.mjs':'service.mjs'};
const MIME={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.mjs':'text/javascript; charset=utf-8'};
export function createDeskServer() {
  const sessions=new Map();
  const write=(res,status,value)=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify(value));};
  const body=async req=>{
    if(!String(req.headers['content-type']||'').startsWith('application/json'))throw new DeskError('JSON requests are required',415);
    let chunks=[],bytes=0;for await(const c of req){bytes+=c.length;if(bytes>100000)throw new DeskError('Request is too large',413);chunks.push(c);}
    try{return JSON.parse(Buffer.concat(chunks).toString('utf8'));}catch{throw new DeskError('Invalid JSON request');}
  };
  return http.createServer(async(req,res)=>{
    res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');
    res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'");
    try {
      const host=req.headers.host||'';
      if(!/^(127\.0\.0\.1|localhost):\d+$/.test(host))throw new DeskError('Only a loopback demonstration host is accepted',403);
      if(req.headers.origin&&req.headers.origin!==`http://${host}`)throw new DeskError('Cross-origin requests are not accepted',403);
      const url=new URL(req.url,`http://${host}`);
      if(url.pathname==='/deployment.json'&&req.method==='GET')return write(res,200,{mode:'local_fixture_api',synthetic:true,source_commit:process.env.DESK_SOURCE_COMMIT||'local'});
      const token=(req.headers.cookie||'').split(';').map(x=>x.trim()).find(x=>x.startsWith('desk_demo='))?.slice(10);
      const old=sessions.get(token);
      if(url.pathname==='/api/session'&&req.method==='POST') {
        const input=await body(req),actor=actorFor(input.role);
        const workspace=old&&old.expires>Date.now()?old.workspace:{data:structuredClone(DATA),ledger:[],auditState:{queue:Promise.resolve()},requests:[]};
        if(token)sessions.delete(token);
        const next=randomBytes(24).toString('hex');sessions.set(next,{actor,workspace,expires:Date.now()+3600000});
        res.setHeader('Set-Cookie',`desk_demo=${next}; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600`);
        return write(res,200,actor);
      }
      if(url.pathname.startsWith('/api/')) {
        if(!old||old.expires<=Date.now())throw new DeskError('Create a sample session first',401);
        const workspace=old.workspace;workspace.requests=workspace.requests.filter(t=>Date.now()-t<60000);
        if(workspace.requests.length>=120)throw new DeskError('Sample request limit reached; try again in a minute',429);
        workspace.requests.push(Date.now());
        const service=new FixtureService(workspace.data,{shared:true,actor:old.actor,ledger:workspace.ledger,auditState:workspace.auditState});
        if(url.pathname==='/api/catalog'&&req.method==='GET')return write(res,200,await service.catalog());
        if(req.method!=='POST')throw new DeskError('Use the documented POST operation',405);
        const x=await body(req);let result;
        if(url.pathname==='/api/lookup')result=await service.lookup(x.id,x.purpose,x.cutoff||DATA.reference_date);
        else if(url.pathname==='/api/assess')result=await service.assess(x.id,x.roleID,x.purpose);
        else if(url.pathname==='/api/submit')result=await service.submit(x.id,x.input,x.purpose);
        else if(url.pathname==='/api/verify')result=await service.verify(x.id,x.qualificationID,x.purpose);
        else if(url.pathname==='/api/cv')result=await service.cv(x.id,x.roleID,x.purpose);
        else if(url.pathname==='/api/history')result=await service.history(x.id,x.purpose);
        else throw new DeskError('API operation unavailable',404);
        return write(res,200,result);
      }
      if(req.method!=='GET'&&req.method!=='HEAD')throw new DeskError('Method unavailable',405);
      const name=FILES[url.pathname];if(!name)throw new DeskError('Not found',404);
      const content=await readFile(path.join(ROOT,'web',name));res.writeHead(200,{'Content-Type':MIME[path.extname(name)]});res.end(req.method==='HEAD'?undefined:content);
    } catch(e){write(res,e instanceof DeskError?e.status:500,{error:e instanceof DeskError?e.message:'Sample service unavailable'});}
  });
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){const port=Number(process.env.PORT||8092);createDeskServer().listen(port,'127.0.0.1',()=>console.log(`SevaSetu Placement Desk: http://127.0.0.1:${port} · synthetic API demonstration`));}
