import puppeteer from 'puppeteer-core';
const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  args: ['--no-sandbox', '--disable-gpu'],
});
const page = await browser.newPage();
const errors = [];
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', e => errors.push(String(e)));
await page.setViewport({ width: 1280, height: 900 });
await page.goto('http://localhost:8931/index.html', { waitUntil: 'networkidle0' });
await new Promise(r => setTimeout(r, 1200));

const data = await page.evaluate(() => {
  const t = (s) => document.querySelector(s)?.textContent?.trim();
  const rect = (s) => { const el = document.querySelector(s); if (!el) return null; const r = el.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) }; };
  return {
    malaria: t('#malaria-count'),
    standLead: t('#stand-lead'),
    rank: t('#rank'),
    richer: t('#richer-count') + ' / ' + t('#richer-pct') + '%',
    donation: t('#donation-annual'),
    pct: t('#pct-display'),
    livesDecade: t('#r-lives-decade'),
    lives40: t('#r-lives-40'),
    nets: t('#r-nets'),
    protected: t('#r-protected'),
    deworm: t('#r-deworm'),
    dalys: t('#r-dalys'),
    dalysNote: t('#r-dalys-note'),
    tr: [t('#tr-nets'), t('#tr-people'), t('#tr-deworm'), t('#tr-life')],
    cert: [t('#cert-name'), t('#cert-pct'), t('#cert-amount'), t('#cert-lives')],
    canvas: rect('#dots'),
    bodyScrollW: document.body.scrollWidth,
    innerW: window.innerWidth,
  };
});
console.log(JSON.stringify(data, null, 1));
console.log('ERRORS:', JSON.stringify(errors));

// interact: raise income, set 10% pledge, type name, open a details
await page.evaluate(() => {
  document.querySelector('#income-input').value = '120000';
  document.querySelector('#income-input').dispatchEvent(new Event('change'));
});
await page.click('#pledge-10');
await page.type('#name-input', 'Ada');
await page.evaluate(() => document.querySelectorAll('.objections details')[0].open = true);
await page.click('#pledge-1'); // then back down
await new Promise(r => setTimeout(r, 900));
const data2 = await page.evaluate(() => {
  const t = (s) => document.querySelector(s)?.textContent?.trim();
  return { standLead: t('#stand-lead'), rank: t('#rank'), pct: t('#pct-display'),
    donation: t('#donation-annual'), lives40: t('#r-lives-40'),
    cert: [t('#cert-name'), t('#cert-pct'), t('#cert-amount'), t('#cert-lives')],
    sliderVal: document.querySelector('#pct-slider').value };
});
console.log(JSON.stringify(data2, null, 1));

// mobile viewport check
await page.setViewport({ width: 390, height: 800 });
await new Promise(r => setTimeout(r, 600));
const mob = await page.evaluate(() => ({
  overflow: document.body.scrollWidth - window.innerWidth,
  canvas: (() => { const c = document.querySelector('#dots'); const r = c.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })(),
}));
console.log('MOBILE:', JSON.stringify(mob));
await browser.close();
