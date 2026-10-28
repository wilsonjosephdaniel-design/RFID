// Renders controls_concept.html boards -> png/*.png
// node render.js   (needs playwright + chromium)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const names = { b1: '1_dock_door_concept', b2: '2_operator_station_CS1', b3: '3_light_storyboard', b4: '4_dashboard_mockup' };

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1.5 });
  await page.goto('file://' + path.join(__dirname, 'controls_concept.html'));
  fs.mkdirSync(path.join(__dirname, 'png'), { recursive: true });
  for (const [id, name] of Object.entries(names)) {
    await page.locator('#' + id).screenshot({ path: path.join(__dirname, 'png', name + '.png') });
  }
  await browser.close();
  console.log('rendered', Object.values(names).join(', '));
})();
