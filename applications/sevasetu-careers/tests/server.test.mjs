import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from '../scripts/serve.mjs';

test('local server serves browser assets and data with browser security headers', async () => {
  const server = createServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    for (const [path, contentType] of [['/', 'text/html'], ['/app.mjs', 'text/javascript'], ['/data/jobs.json', 'application/json']]) {
      const response = await fetch(base + path); assert.equal(response.status, 200, path);
      assert.ok(response.headers.get('content-type').includes(contentType)); assert.ok(response.headers.get('content-security-policy').includes("connect-src 'self'"));
    }
    assert.ok((await (await fetch(base)).text()).includes('SevaSetu Careers'));
  } finally { await new Promise(resolve => server.close(resolve)); }
});
test('local server rejects non-public paths and write methods', async () => {
  const server = createServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    for (const path of ['/scripts/cv.mjs', '/%2e%2e%2fscripts/serve.mjs', '/../../README.md', '/profile.txt']) assert.equal((await fetch(base + path)).status, 404, path);
    assert.equal((await fetch(base, { method: 'POST', body: 'private' })).status, 405);
  } finally { await new Promise(resolve => server.close(resolve)); }
});
