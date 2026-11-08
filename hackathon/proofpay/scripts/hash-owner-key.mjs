// Read the dedicated owner key from stdin; print only its salted password hash.
import {randomBytes,scrypt} from 'node:crypto';
let input='';for await(const chunk of process.stdin){input+=chunk;if(input.length>512)throw Error('Owner key is too long');}
const password=input.replace(/\r?\n$/,'');
if(password.length<16||password.length>256)throw Error('Use a dedicated owner key of 16 to 256 characters');
const salt=randomBytes(16);
const hash=await new Promise((resolve,reject)=>scrypt(password,salt,32,{N:16384,r:8,p:1,maxmem:64*1024*1024},(error,key)=>error?reject(error):resolve(key)));
process.stdout.write(`scrypt$16384$8$1$${salt.toString('base64url')}$${hash.toString('base64url')}\n`);
