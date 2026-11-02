import { createRequire } from 'node:module';
import { mkdir, writeFile } from 'node:fs/promises';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.SEVASETU_BASE_URL || 'http://127.0.0.1:8090/';
const output = process.env.SEVASETU_SCREENSHOTS || 'live-results/compact';
await mkdir(output, { recursive: true });
const proxy = process.env.SEVASETU_PROXY_SERVER ? { server: process.env.SEVASETU_PROXY_SERVER } : undefined;
const args = process.env.SEVASETU_SINGLE_PROCESS === '1' ? ['--no-sandbox', '--disable-gpu', '--no-zygote', '--single-process'] : [];
const browser = await chromium.launch({ headless: true, proxy, args, executablePath: process.env.CHROMIUM_PATH || undefined });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 675 } });
  await page.goto(base);
  await page.getByRole('heading', { name: '10 sample roles to review', exact: true }).waitFor();
  await page.getByRole('button', { name: 'Build CV for this role', exact: true }).click({ timeout: 10000 });
  await page.getByRole('dialog').waitFor();
  if (!(await page.locator('#cv-preview').innerText()).includes('Completed 10+2.')) throw new Error('Qualifications missing from preview');
  await page.screenshot({ path: `${output}/compact-cv.png` });
  const result = { tested_at: new Date().toISOString(), base_url: base, viewport: { width: 1440, height: 675 },
    environment: new URL(base).hostname === '127.0.0.1' ? 'local_candidate' : 'public_deployment',
    build_cv_reachable: true, qualifications_visible: true, status: 'PASS' };
  await writeFile(`${output}/compact-browser.json`, JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result));
} finally { await browser.close(); }
