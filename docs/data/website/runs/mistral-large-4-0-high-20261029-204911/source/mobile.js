const fs = require('fs');
const puppeteer = require('puppeteer-core');
(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true });
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.goto('http://127.0.0.1:8123/bundle-test.html', { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 2500));
  await page.screenshot({ path: '12-mobile-hero.jpg', type: 'jpeg', quality: 75 });
  await page.evaluate(() => document.querySelector('#math').scrollIntoView());
  await new Promise((r) => setTimeout(r, 1200));
  await page.screenshot({ path: '13-mobile-math.jpg', type: 'jpeg', quality: 75 });
  await page.evaluate(() => document.querySelector('#pledge').scrollIntoView());
  await new Promise((r) => setTimeout(r, 1200));
  await page.screenshot({ path: '14-mobile-pledge.jpg', type: 'jpeg', quality: 75 });
  console.log(errs.length ? 'ERRORS: ' + errs.join(' | ') : 'MOBILE OK, NO ERRORS');
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
