import puppeteer from 'puppeteer-core';
const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  args: ['--no-sandbox', '--disable-gpu'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 900, deviceScaleFactor: 1 });
await page.goto('http://localhost:8931/index.html', { waitUntil: 'networkidle0' });
await new Promise(r => setTimeout(r, 2500));
await page.screenshot({ path: 'desktop-full.jpg', fullPage: true, type: 'jpeg', quality: 70 });
// wait for malaria counter to show something & interactions done
const m = await page.evaluate(() => document.querySelector('#malaria-count').textContent);
await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 });
await new Promise(r => setTimeout(r, 800));
await page.screenshot({ path: 'mobile.jpg', fullPage: true, type: 'jpeg', quality: 70 });
const mob = await page.evaluate(() => ({ overflow: document.body.scrollWidth - innerWidth, dots: document.querySelector('#dots').getBoundingClientRect().toJSON() }));
console.log('malaria count after 2.5s:', m, '| mobile:', JSON.stringify(mob));
await browser.close();
