import { chromium } from '@playwright/test';

const baseURL = process.env.E2E_BASE_URL || 'http://127.0.0.1:5173';
const username = process.env.E2E_USERNAME;
const password = process.env.E2E_PASSWORD;

if (!username || !password) {
  throw new Error('Defina E2E_USERNAME y E2E_PASSWORD; no se guardan credenciales en el repositorio.');
}

const profiles = {
  '4G': { latency: 20, down: 4 * 1024 * 1024, up: 3 * 1024 * 1024, type: 'cellular4g' },
  'Fast 3G': { latency: 150, down: 1.6 * 1024 * 1024, up: 750 * 1024, type: 'cellular3g' },
  'Slow 3G': { latency: 400, down: 500 * 1024, up: 500 * 1024, type: 'cellular3g' },
  '3G': { latency: 300, down: 700 * 1024, up: 700 * 1024, type: 'cellular3g' },
};

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();
await page.goto(baseURL, { waitUntil: 'networkidle' });

const token = await page.evaluate(async ({ username, password }) => {
  const response = await fetch('/api/v1/auth/token/', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new Error(`Login falló: ${response.status}`);
  return (await response.json()).token;
}, { username, password });

const cdp = await context.newCDPSession(page);
await cdp.send('Network.enable');
const results = {};
for (const [name, profile] of Object.entries(profiles)) {
  await cdp.send('Network.emulateNetworkConditions', {
    offline: false, latency: profile.latency,
    downloadThroughput: profile.down, uploadThroughput: profile.up,
    connectionType: profile.type,
  });
  const samples = [];
  for (let attempt = 0; attempt < 5; attempt += 1) {
    samples.push(await page.evaluate(async (authToken) => {
      const start = performance.now();
      const response = await fetch('/api/v1/farms/', { headers: { Authorization: `Token ${authToken}` } });
      await response.arrayBuffer();
      const total = performance.now() - start;
      const timing = response.headers.get('server-timing') || '';
      const match = timing.match(/dur=([0-9.]+)/);
      return { status: response.status, total, server: match ? Number(match[1]) : null };
    }, token));
  }
  const median = (values) => values.slice().sort((a, b) => a - b)[Math.floor(values.length / 2)];
  results[name] = {
    status: samples[0].status,
    total_ms_median: Number(median(samples.map((sample) => sample.total)).toFixed(2)),
    server_ms_median: median(samples.map((sample) => sample.server).filter((value) => value !== null)),
  };
}
console.log(JSON.stringify(results, null, 2));
await browser.close();
