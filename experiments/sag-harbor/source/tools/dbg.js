const { chromium } = require('playwright'); const path = require('path');
(async () => { const b = await chromium.launch({args:['--use-angle=d3d11','--enable-gpu','--ignore-gpu-blocklist']}); const p = await b.newPage({viewport:{width:540,height:960}});
 await p.route('http://local/**', r => { const f = r.request().url().replace('http://local/','').split('?')[0]; const fp = f==='three.module.js'?path.join(__dirname,'../node_modules/three/build/three.module.js'):f==='three.core.js'?path.join(__dirname,'../node_modules/three/build/three.core.js'):path.join(__dirname,'..',f); r.fulfill({path:fp, contentType: fp.endsWith('.js')?'text/javascript':fp.endsWith('.json')?'application/json':fp.endsWith('.jpg')?'image/jpeg':'text/html'}); });
 await p.goto('http://local/scene_sh.html'); await p.waitForFunction('window.ready===true',null,{timeout:60000});
 for (const t of process.argv.slice(2)) console.log(t, JSON.stringify(await p.evaluate(t => window.dbg(+t), t)));
 await b.close(); })();
