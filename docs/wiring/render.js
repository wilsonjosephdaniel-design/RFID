// Renders svg/W*.svg -> png/W*.png and a single multi-page PDF.
// node render.js   (needs playwright + chromium)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const dir = __dirname;
const sheets = fs.readdirSync(path.join(dir, 'svg')).filter(f => /^W\d\.svg$/.test(f)).sort();

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1700, height: 1100 }, deviceScaleFactor: 2 });
  fs.mkdirSync(path.join(dir, 'png'), { recursive: true });
  const bodies = [];
  for (const f of sheets) {
    const svg = fs.readFileSync(path.join(dir, 'svg', f), 'utf8');
    await page.setContent(`<html><body style="margin:0">${svg.replace('width="17in" height="11in"', 'width="1700" height="1100"')}</body></html>`);
    await page.screenshot({ path: path.join(dir, 'png', f.replace('.svg', '.png')), clip: { x: 0, y: 0, width: 1700, height: 1100 } });
    bodies.push(`<div class="pg">${svg.replace('width="17in" height="11in"', 'width="100%" height="100%"')}</div>`);
  }
  await page.setContent(`<html><head><style>@page{size:17in 11in;margin:0}body{margin:0}
    .pg{width:17in;height:11in;page-break-after:always;overflow:hidden}</style></head><body>${bodies.join('')}</body></html>`);
  await page.pdf({ path: path.join(dir, 'RFID_Panel_Box_Wiring_rev9.pdf'), width: '17in', height: '11in', printBackground: true });
  await browser.close();
  console.log('rendered', sheets.join(', '));
})();
