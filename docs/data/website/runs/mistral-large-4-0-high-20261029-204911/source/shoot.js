// Screenshot helper: loads the local page in headless Chrome, captures sections as .jpg
const fs = require('fs');
const puppeteer = require('puppeteer-core');

const CANDIDATES = [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
];
const exe = CANDIDATES.find((p) => fs.existsSync(p));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: exe,
    headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });

  const errors = [];
  page.on('pageerror', (e) => errors.push('PAGEERROR: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('CONSOLE: ' + m.text()); });
  page.on('requestfailed', (r) => errors.push('REQFAIL: ' + r.url()));
  page.on('request', (r) => { if (!r.url().startsWith('http://127.0.0.1')) errors.push('EXTERNAL REQ: ' + r.url()); });

  await page.goto('http://127.0.0.1:8123/bundle-test.html', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise((r) => setTimeout(r, 3000));

  const shots = process.argv[2] ? JSON.parse(process.argv[2]) : [
    { name: '01-hero', y: 0 },
    { name: '02-idea', sel: '#idea' },
    { name: '03-math', sel: '#math' },
    { name: '04-interventions', sel: '#interventions' },
    { name: '05-objections', sel: '#objections' },
    { name: '06-givewell-pledge', sel: '#give-well' },
    { name: '07-pledge', sel: '#pledge' },
    { name: '08-footer', sel: '.footer' },
  ];

  for (const s of shots) {
    if (s.sel) {
      await page.evaluate((sel) => {
        const el = document.querySelector(sel);
        window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 70, behavior: 'instant' });
      }, s.sel);
    } else {
      await page.evaluate((y) => window.scrollTo({ top: y, behavior: 'instant' }), s.y || 0);
    }
    await new Promise((r) => setTimeout(r, 1400));
    await page.screenshot({ path: `${s.name}.jpg`, type: 'jpeg', quality: 78 });
    console.log('saved', s.name + '.jpg');
  }

  // interaction test: move the scenario slider to $10 and allocation, screenshot math again
  await page.evaluate(() => {
    const amt = document.querySelector('#amt');
    amt.value = 25; amt.dispatchEvent(new Event('input', { bubbles: true }));
    const nets = document.querySelector('#alloc-nets');
    nets.value = 70; nets.dispatchEvent(new Event('input', { bubbles: true }));
    const cash = document.querySelector('#alloc-cash');
    cash.value = 0; cash.dispatchEvent(new Event('input', { bubbles: true }));
    const el = document.querySelector('#math');
    window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 70, behavior: 'instant' });
  });
  await new Promise((r) => setTimeout(r, 1200));
  await page.screenshot({ path: '09-math-interacted.jpg', type: 'jpeg', quality: 78 });
  console.log('saved 09-math-interacted.jpg');

  // quiz interaction
  await page.evaluate(() => {
    const q = document.querySelector('#quiz');
    window.scrollTo({ top: q.getBoundingClientRect().top + window.scrollY - 200, behavior: 'instant' });
    const btn = document.querySelector('#quiz [data-pick="deworm"]');
    btn.click();
  });
  await new Promise((r) => setTimeout(r, 800));
  await page.screenshot({ path: '10-quiz.jpg', type: 'jpeg', quality: 78 });
  console.log('saved 10-quiz.jpg');

  // pledge interaction
  await page.evaluate(() => {
    const el = document.querySelector('#pledge');
    window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 70, behavior: 'instant' });
    const p = document.querySelector('#pAmt');
    p.value = 25; p.dispatchEvent(new Event('input', { bubbles: true }));
    const y = document.querySelector('#pYears');
    y.value = 30; y.dispatchEvent(new Event('input', { bubbles: true }));
    const d = document.querySelectorAll('.obj')[2];
    d.open = true;
  });
  await new Promise((r) => setTimeout(r, 1200));
  await page.screenshot({ path: '11-pledge-interacted.jpg', type: 'jpeg', quality: 78 });
  console.log('saved 11-pledge-interacted.jpg');

  console.log(errors.length ? 'ERRORS:\n' + errors.join('\n') : 'NO PAGE ERRORS, NO EXTERNAL REQUESTS');
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
