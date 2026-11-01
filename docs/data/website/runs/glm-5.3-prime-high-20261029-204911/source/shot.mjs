import puppeteer from 'puppeteer-core';
const url = process.argv[2] || 'http://localhost:8931/index.html';
const out = process.argv[3] || 'shot';
const full = process.argv[4] === 'full';
const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  args: ['--no-sandbox', '--disable-gpu', '--force-color-profile=srgb'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 900, deviceScaleFactor: 1 });
await page.goto(url, { waitUntil: 'networkidle0' });
await new Promise(r => setTimeout(r, 1600));
if (full) {
  await page.screenshot({ path: `${out}.jpg`, fullPage: true, type: 'jpeg', quality: 70 });
} else {
  await page.screenshot({ path: `${out}.jpg`, type: 'jpeg', quality: 70 });
}
await browser.close();
console.log('saved', out);
