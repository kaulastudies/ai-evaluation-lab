import https from 'node:https';
import { lookup } from 'node:dns/promises';
import { BlockList, isIP } from 'node:net';
import { readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { canonicalURL, prepareFeed, text } from '../web/core.mjs';

const blocked4 = new BlockList(), blocked6 = new BlockList(), global6 = new BlockList();
global6.addSubnet('2000::', 3, 'ipv6');
for (const [ip, bits] of [['0.0.0.0', 8], ['10.0.0.0', 8], ['100.64.0.0', 10], ['127.0.0.0', 8], ['169.254.0.0', 16], ['172.16.0.0', 12], ['192.0.0.0', 24], ['192.0.2.0', 24], ['192.168.0.0', 16], ['198.18.0.0', 15], ['198.51.100.0', 24], ['203.0.113.0', 24], ['224.0.0.0', 4], ['240.0.0.0', 4]]) blocked4.addSubnet(ip, bits, 'ipv4');
for (const [ip, bits] of [['::', 96], ['::ffff:0:0', 96], ['64:ff9b::', 96], ['100::', 64], ['2001::', 32], ['2001:db8::', 32], ['2002::', 16], ['fc00::', 7], ['fe80::', 10], ['ff00::', 8]]) blocked6.addSubnet(ip, bits, 'ipv6');
export const publicIP = address => isIP(address) === 4 ? !blocked4.check(address, 'ipv4') : isIP(address) === 6 ? global6.check(address, 'ipv6') && !blocked6.check(address, 'ipv6') : false;
export async function resolveSource(config, resolve = lookup) {
  const u = new URL(canonicalURL(config.url));
  if (!Array.isArray(config.allowed_hosts) || !config.allowed_hosts.includes(u.hostname) || u.port && u.port !== '443') throw new Error('Source host/port is not explicitly approved');
  if (isIP(u.hostname.replace(/^\[|\]$/g, '')) || /(^|\.)localhost$|\.local$|\.internal$/i.test(u.hostname)) throw new Error('IP literals and local hosts are not permitted');
  const addresses = await resolve(u.hostname, { all: true, verbatim: true });
  if (!addresses.length || addresses.some(x => !publicIP(x.address))) throw new Error('Source resolves to a non-public address');
  return { url: u, address: addresses[0] };
}
export async function fetchSource(config) {
  const { url, address } = await resolveSource(config);
  // Pin the checked DNS address to prevent a second resolution / DNS rebinding.
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      headers: { 'User-Agent': 'SevaSetuCareers/0.1 (public-source prototype)', Accept: 'application/json,text/html', 'Accept-Encoding': 'identity' },
      lookup: (_host, opts, cb) => opts.all ? cb(null, [address]) : cb(null, address.address, address.family),
      timeout: 10000,
    }, res => {
      if (res.statusCode !== 200) { res.resume(); reject(new Error(`Source returned HTTP ${res.statusCode}; redirects are not followed`)); return; }
      const contentType = String(res.headers['content-type'] || '');
      if (!/application\/(?:ld\+)?json|text\/html/i.test(contentType)) { res.destroy(); reject(new Error('Unsupported source content type')); return; }
      const chunks = []; let bytes = 0;
      res.on('data', chunk => { bytes += chunk.length; if (bytes > 2_000_000) res.destroy(new Error('Source exceeds 2 MB')); else chunks.push(chunk); });
      res.on('error', reject);
      res.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    });
    req.on('timeout', () => req.destroy(new Error('Source timed out')));
    req.on('error', reject);
  });
}
function expand(value) {
  if (Array.isArray(value)) return value.flatMap(expand);
  if (!value || typeof value !== 'object') return [];
  return [value, ...expand(value['@graph']), ...expand(value.itemListElement?.map(x => x.item || x))];
}
function schemaJob(j, sourceURL) {
  const location = (Array.isArray(j.jobLocation) ? j.jobLocation : [j.jobLocation]).filter(Boolean)
    .map(l => typeof l.address === 'string' ? l.address : [l.address?.addressLocality, l.address?.addressRegion, l.address?.addressCountry].filter(Boolean).join(', ')).join(' / ');
  return {
    id: typeof j.identifier === 'object' ? String(j.identifier.value || '') : String(j.identifier || ''),
    title: j.title, employer: j.hiringOrganization?.name, url: j.url || sourceURL,
    location: location || 'Not specified', remote: j.jobLocationType === 'TELECOMMUTE',
    description: text(j.description), posted_at: j.datePosted, valid_until: j.validThrough || null,
    skills: typeof j.skills === 'string' ? j.skills.split(',').map(s => s.trim()) : [],
    esm: null, requirements: { review_required: true },
  };
}
export function parseSource(body, config, observedAt = new Date().toISOString()) {
  let raw, jobs, upstreamSynthetic = false;
  if (config.format === 'json') {
    raw = JSON.parse(body); jobs = Array.isArray(raw) ? raw : raw.jobs;
    upstreamSynthetic = raw.synthetic === true || raw.source?.synthetic === true;
  } else if (config.format === 'jsonld') {
    const scripts = [...body.matchAll(/<script\b[^>]*\btype\s*=\s*["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script\s*>/gi)];
    const values = scripts.flatMap(m => expand(JSON.parse(m[1])));
    jobs = values.filter(j => (Array.isArray(j['@type']) ? j['@type'] : [j['@type']]).includes('JobPosting')).map(j => schemaJob(j, config.url));
  } else throw new Error('Choose json or jsonld source format');
  const source = { name: config.name, url: config.url, observed_at: observedAt, synthetic: config.synthetic === true || upstreamSynthetic };
  const result = prepareFeed({ jobs, source });
  // Retain source timestamps in the exported normalized interchange format.
  return { ...result, normalized_jobs: result.jobs.map(j => ({ ...j, source_url: config.url, source: source.name })) };
}
export async function ingest(configs, fetcher = fetchSource, asOf = new Date().toISOString()) {
  if (!Array.isArray(configs) || configs.length > 20) throw new Error('Configure at most 20 explicitly approved sources');
  const jobs = [], failures = [], rejected = [];
  for (const config of configs) {
    try {
      const result = parseSource(await fetcher(config), config, asOf);
      jobs.push(...result.normalized_jobs); rejected.push(...result.rejected.map(x => ({ source: config.name, ...x })));
    } catch (err) { failures.push({ source: config.name, reason: err.message }); }
  }
  return { schema_version: '0.1', observed_at: asOf, jobs, rejected, failures,
    status: failures.length ? jobs.length ? 'partial' : 'failed' : 'ok' };
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [configPath, outputPath] = process.argv.slice(2);
  if (!configPath || !outputPath) { console.error('Usage: node scripts/ingest.mjs sources.json output.json'); process.exitCode = 2; }
  else {
    const report = await ingest(JSON.parse(await readFile(configPath, 'utf8')));
    await writeFile(outputPath, JSON.stringify(report, null, 2) + '\n', { mode: 0o600 });
    console.log(JSON.stringify({ status: report.status, jobs: report.jobs.length, rejected: report.rejected.length, failures: report.failures }));
    if (report.status !== 'ok' || report.rejected.length) process.exitCode = 1;
  }
}
