import puppeteer from 'puppeteer-core';

const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
  args: ['--no-sandbox']
});
const page = await browser.newPage();
const errors = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => {
  if (message.type() === 'error') errors.push(message.text());
});
await page.setViewport({ width: 1440, height: 1000, deviceScaleFactor: 1 });
await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle0' });
await page.waitForSelector('.hero-copy.visible');
await page.screenshot({ path: 'desktop.jpg', type: 'jpeg', quality: 88 });

const initialOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
await page.click('[data-shift="repair"]');
const repair = await page.$eval('#shift-quote', el => el.textContent);
if (!repair.includes('interrupted')) throw new Error('Hero shift did not update');

await page.click('[data-scenario="meeting"]');
await page.click('#next-step');
await page.click('#feeling-choices [data-value="frustrated"]');
await page.click('#feeling-choices [data-value="hurt"]');
await page.click('#next-step');
await page.click('#need-choices [data-value="to be heard"]');
await page.click('#next-step');
await page.type('#request', 'let me finish my thought before you respond');
await page.click('#next-step');
await new Promise(resolve => setTimeout(resolve, 700));
const message = await page.$eval('#message-preview', el => el.textContent.replace(/\s+/g, ' ').trim());
if (!message.includes('I felt frustrated and hurt because I needed to be heard.')) throw new Error(`Unexpected draft: ${message}`);
await page.screenshot({ path: 'practice.jpg', type: 'jpeg', quality: 88 });

await page.click('#copy-message');
await new Promise(resolve => setTimeout(resolve, 150));
const copyFeedback = await page.$eval('#copy-feedback', el => el.textContent);
if (!copyFeedback) throw new Error('Copy interaction gave no feedback');

await page.evaluate(() => document.querySelector('#reset').scrollIntoView());
await new Promise(resolve => setTimeout(resolve, 500));
await page.screenshot({ path: 'reset.jpg', type: 'jpeg', quality: 88 });
await page.click('#breath-toggle');
await new Promise(resolve => setTimeout(resolve, 1200));
const breathPhase = await page.$eval('#breath-phase', el => el.textContent);
if (breathPhase !== 'Breathe in') throw new Error('Breathing timer did not start');
await page.click('#breath-toggle');
const pausedPhase = await page.$eval('#breath-phase', el => el.textContent);
if (pausedPhase !== 'Paused') throw new Error('Breathing timer did not pause');

await page.evaluate(() => document.querySelector('#field-guide').scrollIntoView());
await page.click('[data-guide="online"]');
const guide = await page.$eval('#guide-try', el => el.textContent);
if (!guide.includes('differently')) throw new Error('Guide tabs did not update');
await new Promise(resolve => setTimeout(resolve, 300));
await page.screenshot({ path: 'guide.jpg', type: 'jpeg', quality: 88 });

await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 });
await page.evaluate(() => window.scrollTo(0, 0));
await new Promise(resolve => setTimeout(resolve, 3400));
await page.screenshot({ path: 'mobile.jpg', type: 'jpeg', quality: 88 });
const mobileOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);

console.log(JSON.stringify({ initialOverflow, mobileOverflow, message, copyFeedback, errors }, null, 2));
if (initialOverflow || mobileOverflow || errors.length) process.exitCode = 1;
await browser.close();
