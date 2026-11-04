const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [,, outDir, fps = '30', secs = '17', only] = process.argv;
(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=d3d11', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
  page.on('console', m => console.log('page:', m.text()));
  page.on('pageerror', e => console.log('err:', e.message));
  await page.route('http://local/**', r => {
    const f = r.request().url().replace('http://local/', '');
    const p = f === 'three.module.js' ? path.join(__dirname, 'node_modules/three/build/three.module.js')
      : f === 'three.core.js' ? path.join(__dirname, 'node_modules/three/build/three.core.js')
      : path.join(__dirname, f);
    r.fulfill({ path: p, contentType: p.endsWith('.js') ? 'text/javascript' : 'text/html' });
  });
  await page.goto('http://local/scene.html');
  await page.waitForFunction('window.ready === true', null, { timeout: 60000 });
  const n = Math.round(+fps * +secs);
  const frames = only ? only.split(',').map(Number) : [...Array(n).keys()];
  for (const i of frames) {
    const url = await page.evaluate(t => window.renderAt(t), i / +fps);
    fs.writeFileSync(path.join(outDir, `f${String(i).padStart(4, '0')}.png`), Buffer.from(url.split(',')[1], 'base64'));
    if (i % 30 === 0) console.log('frame', i);
  }
  await browser.close();
})();
