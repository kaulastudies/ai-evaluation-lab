import {createHmac,scryptSync} from 'node:crypto';
export const TEST_OWNER_PASSWORD='synthetic-owner-key-for-local-tests-only';
const salt=Buffer.alloc(16,7);
const hash=scryptSync(TEST_OWNER_PASSWORD,salt,32,{N:16384,r:8,p:1,maxmem:64*1024*1024});
export function ownerConfig(overrides={}){return {OWNER_ID:'test-owner',OWNER_PASSWORD_HASH:`scrypt$16384$8$1$${salt.toString('base64url')}$${hash.toString('base64url')}`,SESSION_SECRET:'s'.repeat(43),APP_ORIGIN:'https://proofpay.example',NODE_ENV:'production',...overrides};}
export function ownerCookie(config=ownerConfig(),now=Date.now()){
  const iat=Math.floor(now/1000);const payload=Buffer.from(JSON.stringify({v:1,sub:config.OWNER_ID,iat,exp:iat+28800,nonce:'a'.repeat(22)})).toString('base64url');
  return `__Host-proofpay-session=${payload}.${createHmac('sha256',config.SESSION_SECRET).update(payload).digest('base64url')}`;
}
