// ---------- camera path: Main Street centerline from OSM, then Long Wharf ----------
const PATH = [[-21,600],[-40,540],[-30,470],[-9,420],[10,334],[15,330],[19,326],[22,319],[25,306],[28,288],[30,272],[35,238],[36,230],[37,222],[38,212],[38,175],[37,165],[36,160],[34,150],[32,145],[30,139],[27,132],[15,98],[13,93],[6,73],[2,62],[-1,54],[-2,38],[-3,26],[-3,19],[-2,13],[-1,6],[0,0],[2,-8],[4,-14],[8,-50],[10,-83],[12,-108],[16,-175],[18,-215]];
const cum = [0]; for (let i=1;i<PATH.length;i++) cum.push(cum[i-1] + Math.hypot(PATH[i][0]-PATH[i-1][0], PATH[i][1]-PATH[i-1][1]));
function along(d) {
  d = Math.max(0, Math.min(cum[cum.length-1], d));
  let i = 1; while (i < cum.length-1 && cum[i] < d) i++;
  const t = (d - cum[i-1]) / (cum[i] - cum[i-1]);
  return [PATH[i-1][0] + (PATH[i][0]-PATH[i-1][0])*t, PATH[i-1][1] + (PATH[i][1]-PATH[i-1][1])*t];
}
const dAtZ = z => { let best = 0, bd = 1e9; for (let d=0; d<cum[cum.length-1]; d+=0.25) { const e = Math.abs(along(d)[1] - z); if (along(d)[1] < 340 && e < bd) { bd = e; best = d; } } return best; };
function frame(d) { const [x, z] = along(d), [x2, z2] = along(d + 2); const l = Math.hypot(x2-x, z2-z) || 1; return {x, z, fx: (x2-x)/l, fz: (z2-z)/l, ex: -(z2-z)/l, ez: (x2-x)/l}; } // e = east-side normal when walking north
const lerp = (a,b,u) => a + (b-a)*u;
function angLerp(a, b, u) { let d = ((b - a + Math.PI*3) % (Math.PI*2)) - Math.PI; return a + d*u; }

// ---------- storefronts: one facade per real business ----------
const SHOPS = await (await fetch('http://local/shops.json')).json();
const ANCH = { east: [[1,5],[17,65],[45,137],[55,162],[63,203],[95,262],[103,307],[127,333],[133,345],[155,379]],
               west: [[2,9],[10,26],[16,61],[20,106],[48,158],[78,207],[90,230],[126,283],[144,334],[150,349]] };
function zForNum(n, side) { const A = ANCH[side]; if (n <= A[0][0]) return A[0][1]; for (let i=1;i<A.length;i++) if (n <= A[i][0]) return lerp(A[i-1][1], A[i][1], (n - A[i-1][0])/(A[i][0] - A[i-1][0])); return A[A.length-1][1]; }
const bMeshes = scene.children.filter(m => m.isMesh && m.geometry.attributes.bc);
const ray = new THREE.Raycaster();
function facadeHit(x, z, dx, dz) {
  ray.set(new THREE.Vector3(x, 1.6, z), new THREE.Vector3(dx, 0, dz)); ray.far = 26;
  const h = ray.intersectObjects(bMeshes, false)[0];
  if (!h) return null;
  let nx = h.face.normal.x, nz = h.face.normal.z; const l = Math.hypot(nx, nz) || 1; nx /= l; nz /= l;
  if (nx*dx + nz*dz > 0) { nx = -nx; nz = -nz; }
  return {x: h.point.x, z: h.point.z, nx, nz, dist: h.distance};
}
const SIGNBG = ['#1d2b45','#20402f','#121212','#7a1f1f','#f4f0e6','#2f5d6b','#5b3a24','#e9dcc0','#3e2a4f'];
const SIGNFG = {'#1d2b45':'#e8c873','#20402f':'#f2e6c8','#121212':'#ffffff','#7a1f1f':'#f6e6c8','#f4f0e6':'#1d2b45','#2f5d6b':'#ffffff','#5b3a24':'#f0d8a0','#e9dcc0':'#5b1f1f','#3e2a4f':'#f4d8a8'};
function drawDisplay(g, type, x, y, w, h) {
  const c = () => `hsl(${R(0,360)},${R(45,85)}%,${R(45,70)}%)`;
  g.save(); g.beginPath(); g.rect(x, y, w, h); g.clip();
  const floorY = y + h*0.82;
  g.fillStyle = 'rgba(60,40,30,.6)'; g.fillRect(x, floorY, w, h - (floorY - y));
  if (type === 'toys') { for (let i=0;i<14;i++){ g.fillStyle = c(); const s = R(4,9); g.fillRect(x+R(0,w-s), floorY - s - R(0,h*0.5), s, s); } g.fillStyle = c(); g.beginPath(); g.moveTo(x+w*0.7, y+4); g.lineTo(x+w*0.85, y+h*0.25); g.lineTo(x+w*0.7, y+h*0.45); g.lineTo(x+w*0.55, y+h*0.25); g.fill(); }
  else if (type === 'clothing' || type === 'jewelry') { for (let i=0;i<3;i++){ const px = x + w*(0.2+0.3*i); g.fillStyle = '#e8ddd0'; g.beginPath(); g.arc(px, y+h*0.22, 3, 0, 7); g.fill(); g.fillStyle = c(); g.beginPath(); g.moveTo(px-6, y+h*0.3); g.lineTo(px+6, y+h*0.3); g.lineTo(px+8, floorY-2); g.lineTo(px-8, floorY-2); g.fill(); } }
  else if (type === 'food') { g.fillStyle = '#fff6dc'; g.fillRect(x, y, w, h*0.8); g.fillStyle = 'rgba(255,190,90,.5)'; g.fillRect(x, y, w, h*0.8); for (let i=0;i<4;i++){ g.fillStyle = '#5b3a24'; g.fillRect(x+R(2,w-14), floorY-8, 12, 2); g.fillStyle = c(); g.fillRect(x+R(2,w-6), floorY-12, 4, 4);} }
  else if (type === 'gallery') { g.fillStyle = '#f6f2ea'; g.fillRect(x, y, w, h*0.82); for (let i=0;i<3;i++){ const fw = R(10,16), fh = R(10,18), px = x + 4 + i*(w-8)/3; g.fillStyle = '#2a2a2a'; g.fillRect(px, y+h*0.25, fw+2, fh+2); g.fillStyle = c(); g.fillRect(px+1, y+h*0.25+1, fw, fh); } }
  else if (type === 'books') { for (let r=0;r<3;r++) for (let i=0;i<w;i+=3){ g.fillStyle = c(); g.fillRect(x+i, y+h*(0.2+r*0.22), 2, h*0.16); } }
  else if (type === 'liquor') { for (let r=0;r<2;r++) for (let i=2;i<w;i+=5){ g.fillStyle = pick(['#2f5a2a','#5a1a22','#d8c48a','#6a3a12']); g.fillRect(x+i, y+h*(0.3+r*0.28), 3, h*0.18); g.fillRect(x+i+1, y+h*(0.24+r*0.28), 1, 4);} }
  else if (type === 'florist') { for (let i=0;i<40;i++){ g.fillStyle = c(); g.beginPath(); g.arc(x+R(0,w), floorY-R(2,h*0.5), R(1.5,3.5), 0, 7); g.fill(); } g.fillStyle = '#3a6a2a'; g.fillRect(x, floorY-4, w, 4); }
  else if (type === 'hardware' || type === 'variety') { for (let r=0;r<3;r++){ g.fillStyle = '#6a5040'; g.fillRect(x, y+h*(0.28+r*0.24), w, 1); for (let i=1;i<w;i+=6){ g.fillStyle = c(); g.fillRect(x+i, y+h*(0.28+r*0.24)-6, 5, 6);} } }
  else if (type === 'pharmacy') { g.fillStyle = '#eef6f2'; g.fillRect(x, y, w, h*0.82); g.fillStyle = '#2a8a5a'; g.fillRect(x+w/2-2, y+h*0.25, 4, 12); g.fillRect(x+w/2-6, y+h*0.25+4, 12, 4); }
  else if (type === 'bank') { glass(g, x, y, w, h); g.fillStyle = 'rgba(255,255,255,.15)'; g.fillRect(x, y+h*0.5, w, 1); }
  else if (type === 'home') { g.fillStyle = c(); g.fillRect(x+4, floorY-10, w*0.5, 8); g.fillStyle = '#e8c873'; g.fillRect(x+w*0.7, y+h*0.3, 3, floorY-y-h*0.3); g.beginPath(); g.moveTo(x+w*0.62, y+h*0.32); g.lineTo(x+w*0.8, y+h*0.32); g.lineTo(x+w*0.75, y+h*0.2); g.lineTo(x+w*0.67, y+h*0.2); g.fill(); }
  else if (type === 'pets') { g.fillStyle = '#c89a5a'; g.beginPath(); g.ellipse(x+w*0.4, floorY-6, 9, 5, 0, 0, 7); g.fill(); g.beginPath(); g.arc(x+w*0.4+9, floorY-12, 4, 0, 7); g.fill(); }
  else { glass(g, x, y, w, h); }
  // glass glare
  g.fillStyle = 'rgba(255,230,190,.18)'; g.beginPath(); g.moveTo(x, y); g.lineTo(x+w*0.35, y); g.lineTo(x, y+h*0.6); g.fill();
  g.restore();
}
function fitText(g, text, maxW, size, font) { let s = size; do { g.font = font.replace('#', s); s--; } while (g.measureText(text).width > maxW && s > 6); }
function facadeTex(shop, wd, ht) {
  const PX = 26, w = Math.round(wd*PX), h = Math.round(ht*PX);
  const sid = shop.type === 'bank' ? 6 : shop.type === 'civic' ? 0 : pick([0,0,1,2,3,4,5,6,7,8]);
  const s = SIDING[sid], bg = pick(SIGNBG), fg = SIGNFG[bg];
  return [canvasTex(w, h, (g) => {
    sidingBase(g, s, w, h);
    const gf = h - 4.3*PX; // top of ground floor
    // upper floor windows
    const floors = Math.max(1, Math.floor((gf - 0.6*PX) / (3.1*PX))), nwin = Math.max(1, Math.round(wd/2.6));
    for (let f=0; f<floors; f++) for (let i=0;i<nwin;i++) {
      const cx = (i+0.5)*w/nwin, cy = gf - (f+0.5)*3.1*PX, ww = 0.95*PX, wh = 1.7*PX;
      g.fillStyle = s.trim; g.fillRect(cx-ww/2-3, cy-wh/2-3, ww+6, wh+8);
      glass(g, cx-ww/2, cy-wh/2, ww, wh); g.fillStyle = s.trim; g.fillRect(cx-1, cy-wh/2, 2, wh); g.fillRect(cx-ww/2, cy-1, ww, 2);
      if (s.sh) { g.fillStyle = s.sh; g.fillRect(cx-ww/2-9, cy-wh/2, 6, wh); g.fillRect(cx+ww/2+3, cy-wh/2, 6, wh); }
    }
    // cornice
    g.fillStyle = s.trim; g.fillRect(0, 0, w, 0.35*PX); g.fillStyle = 'rgba(0,0,0,.25)'; for (let x=2;x<w;x+=8) g.fillRect(x, 0.35*PX, 4, 5);
    // storefront: pilasters, sign band, display windows, door
    g.fillStyle = bg; g.fillRect(0, gf, w, h - gf);
    g.fillStyle = s.trim; g.fillRect(0, gf, 0.25*PX, h-gf); g.fillRect(w-0.25*PX, gf, 0.25*PX, h-gf);
    const sb = gf + 0.15*PX, sh = 0.85*PX;
    g.fillStyle = bg; g.fillRect(0.3*PX, sb, w-0.6*PX, sh);
    g.strokeStyle = fg; g.lineWidth = 2; g.strokeRect(0.4*PX, sb+3, w-0.8*PX, sh-6);
    g.fillStyle = fg; g.textAlign = 'center'; g.textBaseline = 'middle';
    const label = shop.name.length > 18 ? shop.name : shop.name.toUpperCase();
    fitText(g, label, w-1.2*PX, Math.round(sh*0.62), pick(['bold #px Georgia, serif', 'bold #px Arial, sans-serif', '#px Georgia, serif']));
    g.fillText(label, w/2, sb + sh/2 + 1);
    const top = sb + sh + 0.15*PX, bot = h - 0.45*PX, doorW = 1.1*PX, doorX = shop.num % 3 === 0 ? 0.35*PX : w - 0.35*PX - doorW;
    g.fillStyle = s.trim; g.fillRect(0.3*PX, top-3, w-0.6*PX, bot-top+6);
    const dx0 = doorX < w/2 ? doorX + doorW + 0.2*PX : 0.45*PX, dx1 = doorX < w/2 ? w - 0.45*PX : doorX - 0.2*PX;
    drawDisplay(g, shop.type, dx0, top, dx1 - dx0, bot - top);
    g.fillStyle = '#3b2a1c'; g.fillRect(doorX, top, doorW, h - top); glass(g, doorX + 4, top + 4, doorW - 8, (h-top)*0.5);
    g.fillStyle = '#c9a24a'; g.fillRect(doorX + (doorX < w/2 ? doorW-7 : 4), top + (h-top)*0.6, 3, 3);
    g.fillStyle = 'rgba(0,0,0,.35)'; g.fillRect(0, h-0.45*PX, w, 0.45*PX);
  }, null), bg, s];
}
const shopGroups = [];
let WSHOP = null;
{
  const byKey = {};
  for (const sh of SHOPS) { const k = sh.street + sh.num + sh.side; (byKey[k] = byKey[k] || []).push(sh); }
  const used = [];
  const stripeTex = (a, b) => canvasTex(16, 16, (g,w,h) => { g.fillStyle = a; g.fillRect(0,0,w,h); g.fillStyle = b; for (let x=0;x<w;x+=8) g.fillRect(x+4,0,4,h); g.fillStyle='rgba(0,0,0,.25)'; g.fillRect(0,h-2,w,2); }, [1,1]);
  for (const k in byKey) {
    const group = byKey[k];
    group.forEach((sh, gi) => {
      if (sh.type === 'cinema') return;
      let px, pz, dx, dz;
      if (sh.street === 'Main St') {
        const z = zForNum(sh.num, sh.side) + (gi - (group.length-1)/2) * 7.5 * (sh.side === 'east' ? 1 : 1);
        const f = frame(dAtZ(z)); const s = sh.side === 'east' ? 1 : -1;
        px = f.x; pz = f.z; dx = f.ex*s; dz = f.ez*s;
      } else if (sh.street === 'Bay St') {
        const bx = {2: 14, 3: 100, 12: 170}[sh.num] || 60; px = bx; pz = bx*0.42; dx = -0.42; dz = 1; const l = Math.hypot(dx, dz); dx /= l; dz /= l;
      } else { px = 4 + gi*0.4; pz = -12 - gi*8; dx = 1; dz = 0.05; }
      let hit = facadeHit(px, pz, dx, dz);
      if (!hit || hit.dist < 4) hit = {x: px + dx*11, z: pz + dz*11, nx: -dx, nz: -dz, dist: 11};
      // avoid stacking two facades on the same spot
      for (const u of used) if (Math.hypot(u[0]-hit.x, u[1]-hit.z) < 6.5) { const tx = -hit.nz, tz = hit.nx; hit.x += tx*7; hit.z += tz*7; }
      used.push([hit.x, hit.z]);
      const wd = R(6.2, 8.2), ht = sh.name === 'The American Hotel' ? 12.5 : R(7.2, 10.8);
      const [tex, bg] = facadeTex(sh, wd, ht);
      const g = new THREE.Group(); g.position.set(hit.x + hit.nx*0.25, 0, hit.z + hit.nz*0.25); g.rotation.y = Math.atan2(hit.nx, hit.nz); scene.add(g);
      const side = new THREE.MeshLambertMaterial({color: '#cfc6b6'});
      const front = new THREE.MeshLambertMaterial({map: tex});
      const box = new THREE.Mesh(new THREE.BoxGeometry(wd, ht, 0.5), [side, side, side, side, front, side]); box.position.set(0, ht/2, -0.25); box.castShadow = box.receiveShadow = true; g.add(box);
      const corn = new THREE.Mesh(new THREE.BoxGeometry(wd + 0.4, 0.45, 0.9), new THREE.MeshLambertMaterial({color: '#efe9de'})); corn.position.set(0, ht + 0.1, 0); corn.castShadow = true; g.add(corn);
      if (rnd() < 0.5) { const p = new THREE.Mesh(new THREE.BoxGeometry(wd*0.4, R(0.6, 1.4), 0.4), corn.material); p.position.set(0, ht + 0.6, -0.1); g.add(p); }
      if (rnd() < 0.72 || sh.name === 'The Wharf Shop') {
        const [a, b] = pick(AWN);
        const am = new THREE.MeshLambertMaterial({map: stripeTex(a, b), side: THREE.DoubleSide}); am.map.repeat.set(wd/1.2, 1);
        const aw = new THREE.Mesh(new THREE.PlaneGeometry(wd - 0.6, 1.9), am); aw.position.set(0, 3.45, 0.85); aw.rotation.x = -1.05; aw.castShadow = true; g.add(aw);
        const val = new THREE.Mesh(new THREE.PlaneGeometry(wd - 0.6, 0.35), am); val.position.set(0, 2.88, 1.66); g.add(val);
      }
      if (rnd() < 0.3) {
        const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 2.4, 4), new THREE.MeshLambertMaterial({color: '#d8d0c0'}));
        pole.position.set(wd*0.35, 5.2, 0.8); pole.rotation.x = 0.8; g.add(pole);
        const fl = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 0.9), new THREE.MeshLambertMaterial({map: flagTex, side: THREE.DoubleSide}));
        fl.position.set(wd*0.35 + 0.75, 5.5, 1.4); fl.rotation.x = 0.8; g.add(fl);
      }
      const rec = {shop: sh, g, wd, ht, x: hit.x, z: hit.z, nx: hit.nx, nz: hit.nz};
      shopGroups.push(rec);
      if (sh.name === 'The Wharf Shop') WSHOP = rec;
    });
  }
  console.log('storefronts', shopGroups.length, 'wharf shop at', WSHOP && [WSHOP.x.toFixed(1), WSHOP.z.toFixed(1)]);
}
// tie-dye glow layer on the Wharf Shop
const wsGlow = new THREE.Mesh(new THREE.PlaneGeometry(WSHOP.wd + 0.8, WSHOP.ht + 0.8), new THREE.ShaderMaterial({
  uniforms: {...U, uGlow: {value: 0}}, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform float uTime, uGlow; varying vec2 vUv; vec3 pal(float t){ return .5+.5*cos(6.2832*(t+vec3(0.,.33,.67))); }
    void main(){ vec2 p = vUv - .5; float r = length(p*vec2(1., 1.4)), a = atan(p.y, p.x);
      vec3 c = pal(a/6.2832*2. + r*5. - uTime*.9 + sin(r*18. - uTime*3.)*.12);
      float edge = smoothstep(.35, .5, max(abs(p.x), abs(p.y)));
      gl_FragColor = vec4(pow(c, vec3(2.2)) * uGlow * (.35 + .9*edge), 1.); }`,
}));
wsGlow.position.set(0, WSHOP.ht/2, 0.3); WSHOP.g.add(wsGlow);

// ---------- Main Street: parked cars, lamps, benches, planters, pedestrians ----------
const PEDS = [];
{
  const carCols = ['#f4f1ea','#1d2b45','#8a1c1c','#2b2b2e','#9aa3ab','#2f5d4a','#c9b48a','#4a6f99'];
  const cars = [], lamps = [], benches = [], planters = [];
  const dA = dAtZ(330), dB = dAtZ(12);
  const wz = WSHOP.z;
  for (let d = dA; d < dB; d += 1) {
    const f = frame(d); const k = Math.round(d);
    if (k % 7 === 0) for (const s of [-1, 1]) if (rnd() < 0.7 && !(f.z > 236 && f.z < 262) && !(s < 0 && Math.abs(f.z - wz) < 14)) cars.push([f.x + f.ex*s*3.2, f.z + f.ez*s*3.2, Math.atan2(f.fx, f.fz), pick(carCols)]);
    if (k % 22 === 0) for (const s of [-1, 1]) lamps.push([f.x + f.ex*s*6.0, f.z + f.ez*s*6.0]);
    if (k % 19 === 5) benches.push([f.x + f.ex*-6.3, f.z + f.ez*-6.3, Math.atan2(f.fx, f.fz)]);
    if (k % 13 === 3) for (const s of [-1, 1]) if (!(s > 0 && Math.abs(f.z - wz) < 9)) planters.push([f.x + f.ex*s*6.7, f.z + f.ez*s*6.7]);
    if (k % 6 === 2) for (const s of [-1, 1]) if (rnd() < 0.55 && !(s > 0 && Math.abs(f.z - wz) < 10)) PEDS.push({d, s, off: s*R(7.6, 9.0), dir: rnd() < 0.5 ? 1 : -1, sp: R(0.9, 1.5), ph: R(0, 6), shirt: pick(['#f4f0e6','#1d3f6e','#c56a2a','#2f6b45','#a3262a','#f0c8d0','#5b8db8','#e8d06a','#202020']), pants: pick(['#2b2f3a','#d8cfb8','#4a5a7a','#3a3a3a','#f4f0e6']), skin: pick(['#f1c9a5','#d9a47a','#a8704a','#6b4a32','#e8b896']), h: R(1.55, 1.9)});
  }
  const M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), V = (x,y,z) => new THREE.Vector3(x,y,z);
  const n = cars.length;
  const body = new THREE.InstancedMesh(new THREE.BoxGeometry(1.8, 0.75, 4.4), new THREE.MeshLambertMaterial(), n);
  const cab = new THREE.InstancedMesh(new THREE.BoxGeometry(1.6, 0.6, 2.3), new THREE.MeshLambertMaterial({color:'#2a3440'}), n);
  const whl = new THREE.InstancedMesh(new THREE.BoxGeometry(1.9, 0.5, 3.0), new THREE.MeshLambertMaterial({color:'#151515'}), n);
  cars.forEach(([x, z, a, c], i) => {
    e.set(0, a, 0); q.setFromEuler(e);
    M.compose(V(x, 0.72, z), q, V(1,1,1)); body.setMatrixAt(i, M); body.setColorAt(i, new THREE.Color(c));
    const o = V(0, 0, -0.3).applyQuaternion(q);
    M.compose(V(x+o.x, 1.38, z+o.z), q, V(1,1,1)); cab.setMatrixAt(i, M);
    M.compose(V(x, 0.3, z), q, V(1,1,1)); whl.setMatrixAt(i, M);
  });
  for (const m of [body, cab, whl]) { m.castShadow = m.receiveShadow = true; scene.add(m); }
  const post = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.07, 0.11, 3.8, 5), new THREE.MeshLambertMaterial({color:'#1b2620'}), lamps.length);
  const head = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.28, 0.18, 0.55, 6), new THREE.MeshLambertMaterial({color:'#fff3c4', emissive:'#ffcf80', emissiveIntensity:.5}), lamps.length);
  lamps.forEach(([x, z], i) => { M.makeTranslation(x, 1.9, z); post.setMatrixAt(i, M); M.makeTranslation(x, 4.05, z); head.setMatrixAt(i, M); });
  post.castShadow = true; scene.add(post, head);
  const bench = new THREE.InstancedMesh(new THREE.BoxGeometry(1.8, 0.45, 0.5), new THREE.MeshLambertMaterial({color:'#2f4a3a'}), benches.length);
  const back = new THREE.InstancedMesh(new THREE.BoxGeometry(1.8, 0.5, 0.08), new THREE.MeshLambertMaterial({color:'#2f4a3a'}), benches.length);
  benches.forEach(([x, z, a], i) => { e.set(0, a + Math.PI/2, 0); q.setFromEuler(e); M.compose(V(x, 0.45, z), q, V(1,1,1)); bench.setMatrixAt(i, M); const o = V(0, 0, -0.25).applyQuaternion(q); M.compose(V(x+o.x, 0.85, z+o.z), q, V(1,1,1)); back.setMatrixAt(i, M); });
  bench.castShadow = back.castShadow = true; scene.add(bench, back);
  const pot = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.55, 0.42, 0.7, 7), new THREE.MeshLambertMaterial({color:'#7a4a32'}), planters.length);
  const fl = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(0.6, 0), new THREE.MeshLambertMaterial({flatShading: true}), planters.length);
  planters.forEach(([x, z], i) => { M.makeTranslation(x, 0.35, z); pot.setMatrixAt(i, M); M.compose(V(x, 0.95, z), q.identity(), V(1, 0.7, 1)); fl.setMatrixAt(i, M); fl.setColorAt(i, new THREE.Color(pick(['#e0407a','#f2c230','#e86a2a','#b050d0','#f4f0e6','#ff6b6b']))); });
  pot.castShadow = fl.castShadow = true; scene.add(pot, fl);
  // pedestrians: torso, head, two legs, all instanced and animated
  const np = PEDS.length;
  const mk = (geo, mat) => { const m = new THREE.InstancedMesh(geo, mat, np); m.castShadow = true; m.frustumCulled = false; scene.add(m); return m; };
  PEDS.torso = mk(new THREE.BoxGeometry(0.46, 0.62, 0.26), new THREE.MeshLambertMaterial());
  PEDS.head = mk(new THREE.BoxGeometry(0.24, 0.27, 0.24), new THREE.MeshLambertMaterial());
  PEDS.legL = mk(new THREE.BoxGeometry(0.17, 0.8, 0.18), new THREE.MeshLambertMaterial());
  PEDS.legR = mk(new THREE.BoxGeometry(0.17, 0.8, 0.18), new THREE.MeshLambertMaterial());
  PEDS.forEach((p, i) => { PEDS.torso.setColorAt(i, new THREE.Color(p.shirt)); PEDS.head.setColorAt(i, new THREE.Color(p.skin)); PEDS.legL.setColorAt(i, new THREE.Color(p.pants)); PEDS.legR.setColorAt(i, new THREE.Color(p.pants)); });
  console.log('cars', n, 'lamps', lamps.length, 'benches', benches.length, 'planters', planters.length, 'pedestrians', np);
}
function updatePeds(t) {
  const M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), V = new THREE.Vector3(), S = new THREE.Vector3(1,1,1);
  PEDS.forEach((p, i) => {
    const f = frame(p.d + p.dir*p.sp*t), sc = p.h/1.75;
    const x = f.x + f.ex*p.off, z = f.z + f.ez*p.off, yaw = Math.atan2(f.fx*p.dir, f.fz*p.dir), sw = Math.sin(t*p.sp*5 + p.ph)*0.45;
    e.set(0, yaw, 0); q.setFromEuler(e); S.setScalar(sc);
    M.compose(V.set(x, (0.8+0.31)*sc + Math.abs(sw)*0.03, z), q, S); PEDS.torso.setMatrixAt(i, M);
    M.compose(V.set(x, (0.8+0.62+0.16)*sc, z), q, S); PEDS.head.setMatrixAt(i, M);
    for (const [m, s] of [[PEDS.legL, 1], [PEDS.legR, -1]]) {
      e.set(sw*s, yaw, 0, 'YXZ'); const ql = new THREE.Quaternion().setFromEuler(e);
      const off = new THREE.Vector3(0.12*s, 0, 0).applyQuaternion(q);
      const down = new THREE.Vector3(0, -0.4*sc, 0).applyQuaternion(ql);
      M.compose(V.set(x + off.x*sc + down.x, 0.8*sc + down.y, z + off.z*sc + down.z), ql, S); m.setMatrixAt(i, M);
    }
  });
  for (const k of ['torso','head','legL','legR']) PEDS[k].instanceMatrix.needsUpdate = true;
}

// ---------- camera: walk past the shops, stop at the Wharf Shop, swoop down Long Wharf ----------
const D0 = dAtZ(318), DW = dAtZ(WSHOP.z) ;
const stopPos = new THREE.Vector3(WSHOP.x + WSHOP.nx*15.5, 1.65, WSHOP.z + WSHOP.nz*15.5);
const stopLook = new THREE.Vector3(WSHOP.x, 4.0, WSHOP.z);
const swoop = new THREE.CatmullRomCurve3([
  stopPos.clone(),
  new THREE.Vector3(...(() => { const f = frame(dAtZ(WSHOP.z - 30)); return [f.x, 9, f.z]; })()),
  new THREE.Vector3(...(() => { const f = frame(dAtZ(110)); return [f.x, 13, f.z]; })()),
  new THREE.Vector3(-2, 11, 30), new THREE.Vector3(5, 7, -40), new THREE.Vector3(13, 3.6, -140), new THREE.Vector3(17, 1.8, -212)
], false, 'centripetal');
const WHALE_AT = new THREE.Vector3(24, 0, -338);
const look = new THREE.Vector3(), tmp = new THREE.Vector3();
function setCamera(t) {
  let pos = new THREE.Vector3(), yaw, pitch = -0.03, fov = 68;
  // walk (0..10.4s), easing into the stop
  const wu = Math.min(1, t/10.4), d = lerp(D0, DW + 9, 1 - Math.pow(1 - wu, 1.6));
  const f = frame(d);
  const swayYaw = Math.atan2(f.fx, f.fz) + Math.sin(t*0.95)*0.32;
  pos.set(f.x + f.ex*5.0, 1.65 + Math.sin(t*2*Math.PI*0.9)*0.035, f.z + f.ez*5.0);
  yaw = swayYaw;
  // glance at the cinema marquee while passing
  const yc = Math.atan2(cinemaAt[0] - pos.x, cinemaAt[1] - pos.z), wc = smooth(5.6, 6.6, t)*(1 - smooth(7.6, 8.4, t));
  yaw = angLerp(yaw, yc, wc*0.8);
  // stop facing the Wharf Shop
  const ws = smooth(9.4, 10.8, t);
  pos.lerp(stopPos, ws);
  tmp.subVectors(stopLook, pos);
  yaw = angLerp(yaw, Math.atan2(tmp.x, tmp.z), ws); pitch = lerp(pitch, Math.atan2(tmp.y - 0, Math.hypot(tmp.x, tmp.z))*0.6, ws);
  // swoop down Main Street and the length of Long Wharf
  if (t > 13.4) {
    const u = Math.pow(smooth(13.6, 20.2, t), 1.25);
    const p = swoop.getPointAt(u), pa = swoop.getPointAt(Math.min(1, u + 0.03));
    const tw = smooth(13.4, 14.4, t);
    pos.lerp(p, tw);
    let sy = Math.atan2(pa.x - p.x, pa.z - p.z), sp = Math.atan2(pa.y - p.y, Math.hypot(pa.x - p.x, pa.z - p.z)) * 0.8 - 0.06;
    const wm = windmill.position, ww = smooth(16.6, 17.6, t)*(1 - smooth(18.2, 19.2, t));
    sy = angLerp(sy, Math.atan2(wm.x - p.x, wm.z - p.z), ww*0.45);
    yaw = angLerp(yaw, sy, tw); pitch = lerp(pitch, sp, tw);
    fov = lerp(68, 46, smooth(15.5, 18.5, t)) ;
    fov = lerp(fov, 64, smooth(19.5, 21, t));
  }
  // whale
  const wh = smooth(20, 21.2, t);
  tmp.set(WHALE_AT.x - pos.x, 26 - pos.y, WHALE_AT.z - pos.z);
  yaw = angLerp(yaw, Math.atan2(tmp.x, tmp.z), wh); pitch = lerp(pitch, Math.atan2(tmp.y, Math.hypot(tmp.x, tmp.z))*0.75, wh);
  pos.y += smooth(27, 30, t)*6;
  camera.position.copy(pos);
  camera.rotation.order = 'YXZ'; camera.rotation.set(pitch, yaw + Math.PI, 0);
  if (camera.fov !== fov) { camera.fov = fov; camera.updateProjectionMatrix(); }
  return [pos.x, pos.z];
}
