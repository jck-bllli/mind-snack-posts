const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [,, outDir, fps = '30', secs = '5', only] = process.argv;
(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ args: (process.env.NT_GL === 'sw' ? ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist']) });
  const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
  page.on('console', m => console.log('page:', m.text()));
  page.on('pageerror', e => console.log('err:', e.message));
  await page.route('http://local/**', r => {
    const f = r.request().url().replace('http://local/', '').split('?')[0];
    const p = f === 'three.module.js' ? path.join(__dirname, 'node_modules/three/build/three.module.js')
      : f === 'three.core.js' ? path.join(__dirname, 'node_modules/three/build/three.core.js')
      : path.join(__dirname, f);
    r.fulfill({ path: p, contentType: p.endsWith('.js') ? 'text/javascript' : p.endsWith('.json') ? 'application/json' : p.endsWith('.jpg') ? 'image/jpeg' : p.endsWith('.png') ? 'image/png' : 'text/html' });
  });
  await page.goto('http://local/' + (process.env.NT_SCENE || 'scene.html'));
  await page.waitForFunction('window.ready === true', null, { timeout: 60000 });
  console.log('GL:', await page.evaluate(() => { const g = document.createElement('canvas').getContext('webgl2') || document.createElement('canvas').getContext('webgl'); if (!g) return 'none'; const e = g.getExtension('WEBGL_debug_renderer_info'); return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER); }));
  const n = Math.round(+fps * +secs);
  const frames = only ? only.split(',').map(Number) : [...Array(n).keys()];
  for (const i of frames) {
    const url = await page.evaluate(t => window.renderAt(t), i / +fps);
    fs.writeFileSync(path.join(outDir, `f${String(i).padStart(4, '0')}.png`), Buffer.from(url.split(',')[1], 'base64'));
    if (i % 15 === 0) console.log('frame', i);
  }
  await browser.close();
})();


