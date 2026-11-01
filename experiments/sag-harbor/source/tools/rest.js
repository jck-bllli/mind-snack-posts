// flush building buckets
for (const [key, b] of buckets) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(b.pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(b.nrm, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(b.uv, 2));
  g.setAttribute('bc', new THREE.Float32BufferAttribute(b.bc, 4));
  const m = new THREE.Mesh(g, b.mat); m.castShadow = m.receiveShadow = true; m.customDepthMaterial = depthMat;
  m.frustumCulled = false; scene.add(m);
}
console.log('buildings', nBuild);

// ---------- land from the OSM coastline, clipped to a box ----------
function chainCoast(ws) {
  ws = ws.map(w => w.slice()); let ring = ws.shift();
  while (ws.length) {
    const e = ring[ring.length-1];
    const i = ws.findIndex(w => Math.hypot(w[0][0]-e[0], w[0][1]-e[1]) < 0.5);
    if (i < 0) break;
    ring = ring.concat(ws.splice(i,1)[0].slice(1));
  }
  return ring;
}
const CLIP = [-1400, -1200, 1600, 2200];
function clipPoly(P, [x0,z0,x1,z1]) {
  const edges = [[p=>p[0]>=x0,(a,b)=>{const t=(x0-a[0])/(b[0]-a[0]);return [x0,a[1]+t*(b[1]-a[1])];}],
                 [p=>p[0]<=x1,(a,b)=>{const t=(x1-a[0])/(b[0]-a[0]);return [x1,a[1]+t*(b[1]-a[1])];}],
                 [p=>p[1]>=z0,(a,b)=>{const t=(z0-a[1])/(b[1]-a[1]);return [a[0]+t*(b[0]-a[0]),z0];}],
                 [p=>p[1]<=z1,(a,b)=>{const t=(z1-a[1])/(b[1]-a[1]);return [a[0]+t*(b[0]-a[0]),z1];}]];
  for (const [inside, cut] of edges) {
    const out = [];
    for (let i=0;i<P.length;i++) { const a = P[i], b = P[(i+1)%P.length];
      if (inside(b)) { if (!inside(a)) out.push(cut(a,b)); out.push(b); } else if (inside(a)) out.push(cut(a,b)); }
    P = out;
  }
  return P;
}
{
  const start = D.coast.reduce((a, w) => Math.abs(w[0][0]) > Math.abs(a[0][0]) ? w : a); // far eastern start
  const rest = D.coast.filter(w => w !== start);
  let ring = chainCoast([start, ...rest]);
  const s = ring[0], e = ring[ring.length-1];
  // land lies to the south of the shore: close the ring round the south
  ring = ring.concat([[e[0], 6000], [-8000, 6000], [-8000, 9000], [12000, 9000], [12000, s[1]]]);
  let P = clipPoly(ring, CLIP);
  let A = 0; for (let i=0;i<P.length;i++){ const [x1,z1]=P[i],[x2,z2]=P[(i+1)%P.length]; A += x1*z2-x2*z1; }
  const idx = THREE.ShapeUtils.triangulateShape(P.map(([x,z]) => new THREE.Vector2(x,z)), []);
  const pos = [], uv = [];
  for (const t of idx) { const tt = A > 0 ? t : [t[0], t[2], t[1]]; for (const i of tt) { pos.push(P[i][0], 0, P[i][1]); uv.push(...aUV(P[i][0], P[i][1])); } }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.computeVertexNormals();
  const land = new THREE.Mesh(g, new THREE.MeshLambertMaterial({map: groundTex, side: THREE.DoubleSide}));
  land.receiveShadow = true; scene.add(land);
  // shore edge
  const sh = new THREE.Mesh(new THREE.BoxGeometry(1,1,1), new THREE.MeshLambertMaterial({color:'#d9c49a'}));
  sh.visible = false; scene.add(sh);
  console.log('land verts', P.length);
}

// ---------- water ----------
const waterTex = canvasTex(64, 64, (g,w,h) => {
  g.fillStyle = '#2b6f86'; g.fillRect(0,0,w,h);
  for (let i=0;i<70;i++) { g.fillStyle = pick(['#3f8aa0','#1f5a70','#5aa5b5','#ffd08a']); g.fillRect(R(0,w), R(0,h), R(4,12), 1); }
}, [300, 300]);
const water = new THREE.Mesh(new THREE.PlaneGeometry(9000, 9000), new THREE.MeshPhongMaterial({map: waterTex, color: '#9fd0e0', specular: '#ffb860', shininess: 40}));
water.rotation.x = -Math.PI/2; water.position.y = -0.6; water.receiveShadow = true; scene.add(water);

// ---------- roads and sidewalks over the aerial ----------
const RW = {primary: 10, secondary: 9, tertiary: 8, residential: 6.5, unclassified: 6.5, service: 4, tertiary_link: 6, primary_link: 6, footway: 1.8, pedestrian: 4, path: 1.4, steps: 1.8};
const asphalt = canvasTex(32, 32, (g,w,h) => { g.fillStyle = '#4b4a4c'; g.fillRect(0,0,w,h); speckle(g,w,h,250,['#3d3c3e','#5c5a5a','#57534d']); }, [1,1]);
const walkT = canvasTex(32, 32, (g,w,h) => { g.fillStyle = '#b9b0a2'; g.fillRect(0,0,w,h); g.fillStyle = '#9d958a'; for (let y=0;y<h;y+=8) g.fillRect(0,y,w,1); speckle(g,w,h,80,['#a8a093','#c8c0b2']); }, [1,1]);
const roadB = {pos:[], uv:[]}, walkB = {pos:[], uv:[]}, lineB = {pos:[], uv:[]};
function ribbon(B, P, w, y, ux=4) {
  let run = 0;
  for (let i=0;i<P.length-1;i++) {
    const [ax,az] = P[i], [bx,bz] = P[i+1], L = Math.hypot(bx-ax,bz-az) || 1;
    const nx = -(bz-az)/L*w/2, nz = (bx-ax)/L*w/2, ex = (bx-ax)/L*w*0.25, ez = (bz-az)/L*w*0.25;
    const v = [[ax-nx-ex,az-nz-ez],[bx-nx+ex,bz-nz+ez],[bx+nx+ex,bz+nz+ez],[ax+nx-ex,az+nz-ez]];
    const u0 = run/ux, u1 = (run+L)/ux; run += L;
    for (const k of [0,2,1,0,3,2]) { B.pos.push(v[k][0], y, v[k][1]); B.uv.push(k===0||k===3?u0:u1, k<2?0:1); }
  }
}
const mainW = 11;
for (const r of D.roads) {
  const w = RW[r.k]; if (!w || r.br) continue;
  if (r.k === 'footway' || r.k === 'path' || r.k === 'steps') ribbon(walkB, r.p, w, 0.09);
  else {
    ribbon(roadB, r.p, w, 0.06);
    if (r.n === 'Main Street') { ribbon(walkB, r.p.map(p=>p), mainW + 6, 0.04); ribbon(lineB, r.p, 0.25, 0.1); }
  }
}
for (const [B, map, col] of [[walkB, walkT, '#ffffff'], [roadB, asphalt, '#ffffff'], [lineB, null, '#e8c040']]) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(B.pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(B.uv, 2));
  g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshLambertMaterial({map, color: col, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2}));
  m.receiveShadow = true; if (OVERHEAD && NOAERIAL) m.visible = true; scene.add(m);
}

// ---------- Long Wharf + piers + breakwater ----------
const wood = canvasTex(32, 32, (g,w,h) => { g.fillStyle = '#8c6c4c'; g.fillRect(0,0,w,h); for (let y=0;y<h;y+=4){ g.fillStyle = `rgba(0,0,0,${R(.1,.35)})`; g.fillRect(0,y+3,w,1);} speckle(g,w,h,60,['#6e5238','#a88a64']); }, [1,1]);
const pierMat = new THREE.MeshLambertMaterial({map: wood});
const pileMat = new THREE.MeshLambertMaterial({color: '#3d3024'});
function boxAlong(a, b, w, y0, y1, mat, cast = true) {
  const L = Math.hypot(b[0]-a[0], b[1]-a[1]);
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, y1-y0, L), mat);
  m.position.set((a[0]+b[0])/2, (y0+y1)/2, (a[1]+b[1])/2); m.rotation.y = Math.atan2(b[0]-a[0], b[1]-a[1]);
  m.castShadow = cast; m.receiveShadow = true; scene.add(m); return m;
}
// Long Wharf: the end of Wharf Street, a broad timber/asphalt pier
const wharfA = [7, -58], wharfB = [20, -242];
{
  const L = Math.hypot(wharfB[0]-wharfA[0], wharfB[1]-wharfA[1]);
  const g = new THREE.BoxGeometry(24, 1.4, L);
  const uvA = g.attributes.uv, pA = g.attributes.position;
  const m = new THREE.Mesh(g, [pierMat, pierMat, new THREE.MeshLambertMaterial({map: groundTex}), pierMat, pierMat, pierMat]);
  m.position.set((wharfA[0]+wharfB[0])/2, -0.1, (wharfA[1]+wharfB[1])/2); m.rotation.y = Math.atan2(wharfB[0]-wharfA[0], wharfB[1]-wharfA[1]);
  m.updateMatrixWorld();
  // top face uses aerial UVs
  const v = new THREE.Vector3();
  for (let i=0;i<pA.count;i++) { if (pA.getY(i) > 0) { v.fromBufferAttribute(pA, i).applyMatrix4(m.matrixWorld); const [u, vv] = aUV(v.x, v.z); uvA.setXY(i, u, vv); } }
  m.receiveShadow = m.castShadow = true; scene.add(m);
  for (let s=0; s<=L; s+=4) for (const off of [-12, 12]) {
    const t = s/L, x = wharfA[0]+(wharfB[0]-wharfA[0])*t, z = wharfA[1]+(wharfB[1]-wharfA[1])*t;
    const ang = Math.atan2(wharfB[0]-wharfA[0], wharfB[1]-wharfA[1]);
    const p = new THREE.Mesh(new THREE.BoxGeometry(0.5, 2.6, 0.5), pileMat);
    p.position.set(x + Math.cos(ang)*off, -0.4, z - Math.sin(ang)*off); scene.add(p);
  }
  // bollards + lamp posts on the wharf
  for (let s=8; s<L; s+=16) for (const off of [-10.5, 10.5]) {
    const t = s/L, ang = Math.atan2(wharfB[0]-wharfA[0], wharfB[1]-wharfA[1]);
    const x = wharfA[0]+(wharfB[0]-wharfA[0])*t + Math.cos(ang)*off, z = wharfA[1]+(wharfB[1]-wharfA[1])*t - Math.sin(ang)*off;
    const lp = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.1, 4, 5), new THREE.MeshLambertMaterial({color:'#1d2a24'}));
    lp.position.set(x, 2.6, z); lp.castShadow = true; scene.add(lp);
    const lh = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.45, 0.35), new THREE.MeshLambertMaterial({color:'#fff1c0', emissive:'#ffcf80', emissiveIntensity:.4}));
    lh.position.set(x, 4.7, z); scene.add(lh);
  }
}
const boatSpots = [];
for (const p of D.piers) {
  if (p.k === 'bridge') {
    for (let i=0;i<p.p.length-1;i++) boxAlong(p.p[i], p.p[i+1], 3, 2.2, 3.2, new THREE.MeshLambertMaterial({color:'#9a9a94'}));
    continue;
  }
  const brk = p.k !== 'pier';
  for (let i=0;i<p.p.length-1;i++) {
    const a = p.p[i], b = p.p[i+1], L = Math.hypot(b[0]-a[0], b[1]-a[1]);
    if (Math.hypot((a[0]+b[0])/2 - 13, (a[1]+b[1])/2 + 150) < 30 && Math.abs(a[0]) < 30) continue; // inside Long Wharf
    boxAlong(a, b, brk ? 5 : 1.8, brk ? -1 : 0.1, brk ? 1.2 : 0.5, brk ? new THREE.MeshLambertMaterial({color:'#8d8a82'}) : pierMat, false);
    if (!brk) for (let s=3; s<L-2; s+=R(5.5,8)) {
      const t = s/L, x = a[0]+(b[0]-a[0])*t, z = a[1]+(b[1]-a[1])*t, ang = Math.atan2(b[0]-a[0], b[1]-a[1]);
      for (const side of [-1, 1]) if (rnd() < 0.62) {
        const len = R(7, 15), off = side*(0.9 + len/2 + 0.3);
        const bx = x + Math.cos(ang)*off, bz = z - Math.sin(ang)*off;
        if (bz > -50 && Math.abs(bx) < 260 && bx > -150) continue;
        boatSpots.push([bx, bz, ang + Math.PI/2 + (side<0?Math.PI:0), len]);
      }
    }
  }
}
// moored boats out in the harbor
for (let i=0;i<70;i++) { const x = R(-420, 520), z = R(-700, -260); boatSpots.push([x, z, R(0, 6.28), R(7, 16)]); }

// ---------- boats (instanced) ----------
{
  const s = new THREE.Shape(); s.moveTo(0, 0.5); s.quadraticCurveTo(0.35, 0.25, 0.42, -0.15); s.lineTo(0.38, -0.5); s.lineTo(-0.38, -0.5); s.lineTo(-0.42, -0.15); s.quadraticCurveTo(-0.35, 0.25, 0, 0.5);
  const hullG = new THREE.ExtrudeGeometry(s, {depth: 0.12, bevelEnabled: false, curveSegments: 3}); hullG.rotateX(-Math.PI/2);
  const n = boatSpots.length, cols = ['#ffffff','#ffffff','#f4f0e8','#ffffff','#1d3557','#8a1c1c','#e9e2cf'];
  const hull = new THREE.InstancedMesh(hullG, new THREE.MeshLambertMaterial(), n);
  const cab = new THREE.InstancedMesh(new THREE.BoxGeometry(1,1,1), new THREE.MeshLambertMaterial({color:'#f8f6f0'}), n);
  const mast = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.06, 0.08, 1, 4), new THREE.MeshLambertMaterial({color:'#d8d8d0'}), n);
  const M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
  boatSpots.forEach(([x, z, a, len], i) => {
    e.set(0, a, 0); q.setFromEuler(e);
    M.compose(new THREE.Vector3(x, -0.6, z), q, new THREE.Vector3(len*0.38, len*0.12, len)); hull.setMatrixAt(i, M);
    hull.setColorAt(i, new THREE.Color(pick(cols)));
    const off = new THREE.Vector3(0, 0, -len*0.08).applyQuaternion(q);
    M.compose(new THREE.Vector3(x+off.x, 1.4, z+off.z), q, new THREE.Vector3(len*0.22, 1.1, len*0.3)); cab.setMatrixAt(i, M);
    const sail = rnd() < 0.4, mh = sail ? len*1.3 : 0.01;
    M.compose(new THREE.Vector3(x, 0.8 + mh/2, z), q, new THREE.Vector3(1, mh, 1)); mast.setMatrixAt(i, M);
  });
  for (const m of [hull, cab, mast]) { m.castShadow = true; m.receiveShadow = true; scene.add(m); }
}

// ---------- trees from the aerial (dark green pixels that are not roofs or roads) ----------
{
  const mask = document.createElement('canvas'); mask.width = AW; mask.height = AH;
  const mg = mask.getContext('2d'); mg.fillStyle = '#fff'; mg.strokeStyle = '#fff'; mg.lineCap = 'round';
  for (const B of D.buildings) { mg.beginPath(); B.p.forEach(([x,z],i) => { const [px,py] = toPx(x,z); i ? mg.lineTo(px,py) : mg.moveTo(px,py); }); mg.fill(); }
  for (const r of D.roads) { const w = RW[r.k]; if (!w) continue; mg.lineWidth = Math.max(2, (w+2)/((AX1-AX0)/AW)); mg.beginPath(); r.p.forEach(([x,z],i) => { const [px,py] = toPx(x,z); i ? mg.lineTo(px,py) : mg.moveTo(px,py); }); mg.stroke(); }
  const md = mg.getImageData(0,0,AW,AH).data;
  const spots = [];
  for (let z = AZ0+3; z < AZ1-3; z += 5.5) for (let x = AX0+3; x < AX1-3; x += 5.5) {
    const jx = x + R(-2,2), jz = z + R(-2,2);
    const [px, py] = toPx(jx, jz).map(Math.floor); const o = (py*AW+px)*4;
    if (md[o] > 0) continue;
    const r = aerialData[o], g = aerialData[o+1], b = aerialData[o+2];
    if (g > r*1.04 && g > b*1.08 && (r+g+b)/3 < 105 && rnd() < 0.8) spots.push([jx, jz, R(6, 13)]);
  }
  const n = spots.length;
  const crown = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 0), new THREE.MeshLambertMaterial({flatShading: true}), n);
  const trunk = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.15, 0.25, 1, 5), new THREE.MeshLambertMaterial({color:'#4a3626'}), n);
  const M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
  spots.forEach(([x, z, h], i) => {
    e.set(R(-.2,.2), R(0,6), R(-.2,.2)); q.setFromEuler(e);
    const cw = h*R(0.32, 0.45);
    M.compose(new THREE.Vector3(x, h*0.62, z), q, new THREE.Vector3(cw, h*0.42, cw)); crown.setMatrixAt(i, M);
    crown.setColorAt(i, new THREE.Color().setHSL(R(0.2, 0.3), R(0.35, 0.55), R(0.2, 0.32)));
    M.compose(new THREE.Vector3(x, h*0.25, z), new THREE.Quaternion(), new THREE.Vector3(1, h*0.5, 1)); trunk.setMatrixAt(i, M);
  });
  for (const m of [crown, trunk]) { m.castShadow = true; m.receiveShadow = true; scene.add(m); }
  console.log('trees', n);
  window.treeCount = n;
}

// ---------- Sag Harbor Cinema: sign + marquee (melts) ----------
function textTex(w, h, draw) { return canvasTex(w, h, draw, null, true); }
let marquee, marqueeMat;
{
  const {P, wallH} = special.cinema;
  // facade = edge closest to Main Street
  let bi = 0, bd = 1e9;
  for (let i=0;i<P.length;i++){ const [ax,az]=P[i],[bx,bz]=P[(i+1)%P.length]; if (Math.hypot(bx-ax,bz-az)<5) continue; const d = distToLines((ax+bx)/2,(az+bz)/2, mainSt); if (d<bd){bd=d;bi=i;} }
  const [ax,az] = P[bi], [bx,bz] = P[(bi+1)%P.length], L = Math.hypot(bx-ax,bz-az);
  const nx = (bz-az)/L, nz = -(bx-ax)/L, mx = (ax+bx)/2, mz = (az+bz)/2;
  const facing = Math.atan2(nx, nz);
  const grp = new THREE.Group(); grp.position.set(mx, 0, mz); grp.rotation.y = facing; scene.add(grp);
  // dark facade with glowing "SAG HARBOR" sign letters (own blocky lettering)
  const fw = Math.min(L, 14);
  const signT = textTex(256, 64, (g,w,h) => {
    g.fillStyle = '#16121a'; g.fillRect(0,0,w,h);
    g.font = 'bold italic 40px Georgia, serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.shadowColor = '#ff2a2a'; g.shadowBlur = 12; g.fillStyle = '#ff5a4a'; g.fillText('Sag Harbor', w/2, h/2+2);
    g.shadowBlur = 0; g.fillStyle = '#ffd0c8'; g.fillText('Sag Harbor', w/2, h/2+2);
  });
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(fw*0.9, fw*0.22), new THREE.MeshBasicMaterial({map: signT, fog: true}));
  sign.position.set(0, wallH - fw*0.14, 0.15); grp.add(sign);
  const front = new THREE.Mesh(new THREE.PlaneGeometry(fw, wallH), new THREE.MeshLambertMaterial({color:'#2a2228'}));
  front.position.set(0, wallH/2, 0.08); front.receiveShadow = true; grp.add(front);
  const doors = new THREE.Mesh(new THREE.PlaneGeometry(fw*0.7, 2.6), new THREE.MeshLambertMaterial({map: storeTex[2]}));
  doors.position.set(0, 1.3, 0.12); grp.add(doors);
  // marquee box
  const box = new THREE.Mesh(new THREE.BoxGeometry(fw*0.95, 0.5, 2.4), new THREE.MeshLambertMaterial({color:'#c8b27a', emissive:'#ffb050', emissiveIntensity:.25}));
  box.position.set(0, 4.35, 1.2); box.castShadow = true; grp.add(box);
  const bulbs = new THREE.Mesh(new THREE.BoxGeometry(fw*0.96, 0.12, 2.45), new THREE.MeshBasicMaterial({color:'#fff2b8'}));
  bulbs.position.set(0, 4.62, 1.2); grp.add(bulbs);
  const mt = textTex(256, 64, (g,w,h) => {
    g.fillStyle = '#fdf6e0'; g.fillRect(0,0,w,h); g.fillStyle = '#d23a2a'; g.fillRect(0,0,w,4); g.fillRect(0,h-4,w,4);
    g.fillStyle = '#16121a'; g.font = 'bold 22px Arial, sans-serif'; g.textAlign = 'center';
    g.fillText('NOW SHOWING', w/2, 26); g.fillStyle = '#b81e5a'; g.fillText('SUMMER DAZE  7 & 9', w/2, 52);
  });
  marqueeMat = new THREE.ShaderMaterial({
    uniforms: { map: {value: mt}, ...U },
    vertexShader: `uniform float uDrip, uTime; varying vec2 vUv; varying float vD;
      float h(float x){ return fract(sin(x*91.7)*437.5); }
      void main(){ vUv = uv; vec3 p = position;
        float col = floor(uv.x*40.); float len = (.4 + 1.6*h(col)) * uDrip;
        float wob = sin(uTime*3. + col)*.08*uDrip;
        float k = 1. - uv.y;
        p.y -= k*k*len*3.2; p.x += wob*k; vD = k*len;
        gl_Position = projectionMatrix*modelViewMatrix*vec4(p,1.); }`,
    fragmentShader: `uniform sampler2D map; uniform float uTime, uDrip; varying vec2 vUv; varying float vD;
      vec3 pal(float t){ return .5+.5*cos(6.2832*(t+vec3(0.,.33,.67))); }
      void main(){ vec4 c = texture2D(map, vUv);
        vec3 col = mix(c.rgb, pal(vUv.x*2. - uTime*.6 + vD), smoothstep(.0,.5,uDrip) * (1. - c.r*.4) );
        col = mix(col, pal(vUv.y*3. + uTime), clamp(vD*.8, 0., 1.));
        gl_FragColor = vec4(col, 1.); }`,
    side: THREE.DoubleSide,
  });
  for (const side of [1]) {
    const mq = new THREE.Mesh(new THREE.PlaneGeometry(fw*0.95, 1.5, 40, 24), marqueeMat);
    mq.position.set(0, 5.1, 2.42); grp.add(mq);
  }
  // side panels angled toward the street
  for (const s of [-1, 1]) {
    const sp = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 1.5, 12, 24), marqueeMat);
    sp.position.set(s*fw*0.475, 5.1, 1.2); sp.rotation.y = s*Math.PI/2; grp.add(sp);
  }
  // falling paint drops
  const N = 140, dp = new Float32Array(N*3), dc = new Float32Array(N*3);
  for (let i=0;i<N;i++) { const c = new THREE.Color().setHSL(rnd(), 1, .55); dc.set([c.r,c.g,c.b], i*3); }
  const dg = new THREE.BufferGeometry(); dg.setAttribute('position', new THREE.BufferAttribute(dp, 3)); dg.setAttribute('color', new THREE.BufferAttribute(dc, 3));
  marquee = {grp, drops: new THREE.Points(dg, new THREE.PointsMaterial({size: 0.28, vertexColors: true})), N, fw, seeds: [...Array(N)].map(() => [R(-.5,.5), R(0,1), R(1.5,3.5)])};
  marquee.drops.frustumCulled = false; grp.add(marquee.drops);
  window.cinemaAt = [mx, mz, facing];
}

// ---------- Old Whalers' Church steeple (lost in 1938; rebuilt here in stylized form) ----------
let steeple;
{
  const {ob, wallH, cx, cz} = special.church;
  // tower on the end of the long axis that faces Union Street (north)
  const s = (ob.uz < 0) ? 1 : -1;
  const tx = ob.cx + ob.ux*s*(ob.ha - 3), tz = ob.cz + ob.uz*s*(ob.ha - 3);
  steeple = new THREE.Group(); steeple.position.set(tx, 0, tz); scene.add(steeple);
  const white = new THREE.MeshLambertMaterial({color:'#f6f2ea'});
  const tiers = [[7, 7, 0, 18], [5.4, 5.4, 18, 8], [4.2, 4.2, 26, 6], [3, 3, 32, 5]];
  for (const [w, d, y, h] of tiers) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), white); m.position.y = y + h/2; m.castShadow = m.receiveShadow = true; steeple.add(m);
    for (const ang of [0, 1, 2, 3]) {
      const win = new THREE.Mesh(new THREE.PlaneGeometry(w*0.35, h*0.5), new THREE.MeshLambertMaterial({color:'#2a2a30'}));
      const a = ang*Math.PI/2; win.position.set(Math.sin(a)*(w/2+0.02), y + h*0.55, Math.cos(a)*(d/2+0.02)); win.rotation.y = a; steeple.add(win);
    }
  }
  const spire = new THREE.Mesh(new THREE.ConeGeometry(1.6, 16, 8), white); spire.position.y = 37 + 8; spire.castShadow = true; steeple.add(spire);
  const ball = new THREE.Mesh(new THREE.OctahedronGeometry(0.5, 0), new THREE.MeshLambertMaterial({color:'#d8b04a', emissive:'#6a4a10'})); ball.position.y = 53.5; steeple.add(ball);
  window.steepleAt = [tx, tz];
}

// ---------- windmill at the foot of Long Wharf ----------
let windmill;
{
  windmill = new THREE.Group(); windmill.position.set(-30, 0.3, -42); scene.add(windmill);
  const shingle = new THREE.MeshLambertMaterial({map: wallTex[3], flatShading: true});
  const tower = new THREE.Mesh(new THREE.CylinderGeometry(2.0, 3.0, 9, 8), shingle); tower.position.y = 4.5; tower.castShadow = true; windmill.add(tower);
  const cap = new THREE.Mesh(new THREE.ConeGeometry(2.6, 2.4, 8), new THREE.MeshLambertMaterial({color:'#5d5348', flatShading: true})); cap.position.y = 10.2; windmill.add(cap);
  const door = new THREE.Mesh(new THREE.PlaneGeometry(1, 2), new THREE.MeshLambertMaterial({color:'#5b3a24'})); door.position.set(0, 1, 2.9); windmill.add(door);
  const hub = new THREE.Group(); hub.position.set(0, 9.4, 2.6); windmill.add(hub);
  const lattice = canvasTex(16, 64, (g,w,h) => { g.clearRect(0,0,w,h); g.fillStyle = '#efe8d8'; g.fillRect(0,0,2,h); g.fillRect(w-2,0,2,h); for (let y=0;y<h;y+=6) g.fillRect(0,y,w,1); for (let x=0;x<w;x+=5) g.fillRect(x,0,1,h); });
  const sailM = new THREE.MeshLambertMaterial({map: lattice, transparent: true, alphaTest: .5, side: THREE.DoubleSide});
  const rainbowM = new THREE.ShaderMaterial({ uniforms: U, side: THREE.DoubleSide,
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
    fragmentShader: `uniform float uTime; varying vec2 vUv; vec3 pal(float t){ return .5+.5*cos(6.2832*(t+vec3(0.,.33,.67))); }
      void main(){ gl_FragColor = vec4(pal(vUv.x*.25 + vUv.y*.5 - uTime*.8), 1.); }` });
  const sails = [], blades = [];
  for (let i=0;i<4;i++) {
    const arm = new THREE.Group(); arm.rotation.z = i*Math.PI/2; hub.add(arm);
    const s = new THREE.Mesh(new THREE.PlaneGeometry(1.8, 7.5), sailM); s.position.set(0.9, 4.2, 0); arm.add(s); sails.push(s);
    const tg = new THREE.BufferGeometry();
    tg.setAttribute('position', new THREE.Float32BufferAttribute([0,0,0, 0,9,0, 5,7,0, 0,0,0, 5,7,0, 6,3,0], 3));
    tg.setAttribute('uv', new THREE.Float32BufferAttribute([i,0, i,1, i+.8,1, i,0, i+.8,1, i+.9,.4], 2));
    const b = new THREE.Mesh(tg, rainbowM); b.visible = false; arm.add(b); blades.push(b);
  }
  windmill.userData = {hub, sails, blades};
  windmill.rotation.y = Math.atan2(20 - -30, -150 - -42); // sails face up the wharf
}

// ---------- original tie-dye whale ----------
let whale, spout;
{
  const tie = canvasTex(256, 256, (g,w,h) => {
    const im = g.createImageData(w, h);
    for (let y=0;y<h;y++) for (let x=0;x<w;x++) {
      const u = x/w*2-1, v = y/h*2-1, r = Math.hypot(u, v), a = Math.atan2(v, u);
      const t = a/6.2832*3 + r*4 + Math.sin(r*12 + a*3)*.15;
      const hue = ((t % 1) + 1) % 1, c = new THREE.Color().setHSL(hue, .9, .55 + .12*Math.sin(r*30));
      const o = (y*w+x)*4; im.data[o] = c.r*255; im.data[o+1] = c.g*255; im.data[o+2] = c.b*255; im.data[o+3] = 255;
    }
    g.putImageData(im, 0, 0);
  }, null, false);
  tie.wrapS = tie.wrapT = THREE.MirroredRepeatWrapping; tie.repeat.set(2, 1);
  const prof = [[0,0],[1.2,.6],[2.6,2],[3.4,4.5],[3.6,7],[3.3,10],[2.6,13],[1.7,16],[1.0,18.5],[0.6,20.5],[0.4,22]].map(([r,y]) => new THREE.Vector2(r, y));
  const bodyG = new THREE.LatheGeometry(prof, 10); bodyG.rotateX(Math.PI/2); bodyG.scale(1, 0.85, 1);
  const mat = new THREE.MeshLambertMaterial({map: tie, flatShading: true, emissive: '#301040', emissiveIntensity: .35});
  whale = new THREE.Group(); scene.add(whale);
  const body = new THREE.Mesh(bodyG, mat); body.castShadow = true; whale.add(body);
  const belly = new THREE.Mesh(new THREE.LatheGeometry(prof.slice(0, 8).map(p => new THREE.Vector2(p.x*0.75, p.y)), 8), new THREE.MeshLambertMaterial({color:'#fff4e0', flatShading: true}));
  belly.geometry.rotateX(Math.PI/2); belly.position.y = -0.8; belly.scale.set(1, 0.6, 1); whale.add(belly);
  const fl = new THREE.Shape(); fl.moveTo(0,0); fl.quadraticCurveTo(3, 1.5, 5.5, 3.2); fl.quadraticCurveTo(4, 0.8, 5.8, -0.6); fl.quadraticCurveTo(2.5, 0.3, 0, -0.5);
  for (const s of [-1, 1]) {
    const fg = new THREE.ExtrudeGeometry(fl, {depth: .3, bevelEnabled: false}); fg.rotateX(Math.PI/2);
    const f = new THREE.Mesh(fg, mat); f.position.set(0, 0, 21.5); f.scale.set(s, 1, 1); f.rotation.y = s*0.15; whale.add(f);
    const pf = new THREE.Mesh(fg, mat); pf.scale.set(s*0.8, 1, 0.8); pf.position.set(s*2.6, -1.5, 6); pf.rotation.set(0.3, s*-0.9, s*0.5); whale.add(pf);
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.45, 6, 4), new THREE.MeshBasicMaterial({color:'#ffffff'})); eye.position.set(s*2.85, 0.3, 3.4); whale.add(eye);
    const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.22, 6, 4), new THREE.MeshBasicMaterial({color:'#101018'})); pupil.position.set(s*3.15, 0.35, 3.3); whale.add(pupil);
  }
  const smile = new THREE.Mesh(new THREE.TorusGeometry(2.6, 0.12, 4, 12, Math.PI*0.7), new THREE.MeshBasicMaterial({color:'#3a1050'}));
  smile.rotation.set(Math.PI/2, 0, Math.PI*0.15); smile.position.set(0, -0.9, 1.6); whale.add(smile);
  // spout particles
  const N = 900, sp = new Float32Array(N*3), sc = new Float32Array(N*3);
  for (let i=0;i<N;i++){ const c = new THREE.Color().setHSL(i/N, 1, .6); sc.set([c.r,c.g,c.b], i*3); }
  const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.BufferAttribute(sp, 3)); sg.setAttribute('color', new THREE.BufferAttribute(sc, 3));
  spout = new THREE.Points(sg, new THREE.PointsMaterial({size: 0.9, vertexColors: true, fog: false})); spout.frustumCulled = false; scene.add(spout);
  spout.userData.seeds = [...Array(N)].map(() => [R(0, 1), R(0, 6.283), R(0.5, 1.2), R(14, 24)]);
  // splash ring
  whale.userData.ring = new THREE.Mesh(new THREE.RingGeometry(10, 13, 24), new THREE.MeshBasicMaterial({color:'#ffffff', transparent: true, opacity: .7, side: THREE.DoubleSide}));
  whale.userData.ring.rotation.x = -Math.PI/2; scene.add(whale.userData.ring);
}
const WHALE_AT = new THREE.Vector3(30, 0, -330);

// ---------- color rain ----------
const RAIN_N = 2600;
const rain = new THREE.LineSegments(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({vertexColors: true, fog: false}));
{
  rain.geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(RAIN_N*6), 3));
  const c = new Float32Array(RAIN_N*6);
  for (let i=0;i<RAIN_N;i++){ const k = new THREE.Color().setHSL(rnd(), 1, .6); c.set([k.r,k.g,k.b,k.r,k.g,k.b], i*6); }
  rain.geometry.setAttribute('color', new THREE.BufferAttribute(c, 3));
  rain.userData.s = [...Array(RAIN_N)].map(() => [R(-40,40), R(-60,30), R(0,1), R(14,22)]);
  rain.frustumCulled = false; rain.visible = false; scene.add(rain);
}

// ---------- camera path: Main Street centerline from OSM, then Long Wharf ----------
const PATH = [[10,334],[15,330],[19,326],[22,319],[25,306],[28,288],[30,272],[35,238],[36,230],[37,222],[38,212],[38,175],[37,165],[36,160],[34,150],[32,145],[30,139],[27,132],[15,98],[13,93],[6,73],[2,62],[-1,54],[-2,38],[-3,26],[-3,19],[-2,13],[-1,6],[0,0],[2,-8],[4,-14],[8,-50],[10,-83],[12,-108],[16,-175],[18,-215]];
const cum = [0]; for (let i=1;i<PATH.length;i++) cum.push(cum[i-1] + Math.hypot(PATH[i][0]-PATH[i-1][0], PATH[i][1]-PATH[i-1][1]));
function along(d) {
  d = Math.max(0, Math.min(cum[cum.length-1], d));
  let i = 1; while (i < cum.length-1 && cum[i] < d) i++;
  const t = (d - cum[i-1]) / (cum[i] - cum[i-1]);
  return [PATH[i-1][0] + (PATH[i][0]-PATH[i-1][0])*t, PATH[i-1][1] + (PATH[i][1]-PATH[i-1][1])*t];
}
const dAtZ = z => { for (let d=0; d<cum[cum.length-1]; d+=0.5) if (along(d)[1] < z) return d; return cum[cum.length-1]; };
// distance keys (seconds -> meters along the path)
const KEYS = [[0, 0], [4, 38], [8, 72], [12, dAtZ(250)], [12.6, dAtZ(240)], [15.4, dAtZ(-14)], [16, dAtZ(-20)], [20, dAtZ(-85)], [21.5, dAtZ(-140)], [30, dAtZ(-200)]];
function dist(t) { for (let i=1;i<KEYS.length;i++) if (t <= KEYS[i][0]) { const [t0,d0] = KEYS[i-1], [t1,d1] = KEYS[i]; const u = (t-t0)/(t1-t0); return d0 + (d1-d0)*(i===5 ? smooth(0,1,u) : u); } return KEYS[KEYS.length-1][1]; }
const lerp = (a,b,u) => a + (b-a)*u;
function angLerp(a, b, u) { let d = ((b - a + Math.PI*3) % (Math.PI*2)) - Math.PI; return a + d*u; }
function setCamera(t) {
  const d = dist(t), [x, z] = along(d), [x2, z2] = along(d + 6);
  let yaw = Math.atan2(x2 - x, z2 - z), pitch = 0;
  const bob = Math.sin(t*2*Math.PI*0.9)*0.035;
  // 8-12: look left at the marquee
  const [cmx, cmz] = cinemaAt;
  const yawCin = Math.atan2(cmx - x, cmz - z);
  const wc = smooth(7.2, 9.2, t) * (1 - smooth(11.6, 12.6, t));
  yaw = angLerp(yaw, yawCin, wc*0.85); pitch = lerp(pitch, 0.1, wc);
  // 12-16: turn round to the steeple and tilt up into the kaleidoscope sky (glide happens while looking up)
  const [sx, sz] = steepleAt;
  const yawSt = Math.atan2(sx - x, sz - z);
  const ws = smooth(12, 12.8, t) * (1 - smooth(15.4, 16, t));
  yaw = angLerp(yaw, yawSt, ws);
  pitch = lerp(pitch, lerp(0.42, 1.25, smooth(13.6, 15, t)), ws);
  // 16-20: windmill on the left
  const wm = windmill.position, yawW = Math.atan2(wm.x - x, wm.z - z);
  const ww = smooth(16, 16.8, t) * (1 - smooth(19.2, 20.5, t));
  yaw = angLerp(yaw, yawW, ww*0.8); pitch = lerp(pitch, 0.18, ww);
  // 20-27: whale
  const yawWh = Math.atan2(WHALE_AT.x - x, WHALE_AT.z - z);
  const wh = smooth(20, 21, t);
  yaw = angLerp(yaw, yawWh, wh); pitch = lerp(pitch, 0.12 + 0.12*smooth(22, 25, t), wh);
  // 27-30: drift up into the rain
  const up = smooth(27, 30, t)*6;
  camera.position.set(x, 1.65 + bob + up, z);
  camera.rotation.set(0, 0, 0); camera.rotation.order = 'YXZ';
  camera.rotation.y = yaw + Math.PI; camera.rotation.x = pitch;
  return [x, z];
}

// ---------- post: color trails + tie-dye grade + crunch ----------
const rtA = new THREE.WebGLRenderTarget(W, H, {samples: 0}), rtB = rtA.clone(), rtS = rtA.clone();
rtS.depthBuffer = true;
const postScene = new THREE.Scene(), postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const blendMat = new THREE.ShaderMaterial({
  uniforms: {cur: {value: null}, prev: {value: null}, trail: {value: 0}, ...U},
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }`,
  fragmentShader: `uniform sampler2D cur, prev; uniform float trail, uTime; varying vec2 vUv;
    vec3 hue(vec3 c, float a){ const vec3 k = vec3(.57735); float ca = cos(a); return c*ca + cross(k,c)*sin(a) + k*dot(k,c)*(1.-ca); }
    void main(){ vec3 c = texture2D(cur, vUv).rgb;
      vec2 o = (vUv - .5)*.012*trail; vec3 p = texture2D(prev, vUv - o).rgb;
      vec3 m = max(c, hue(p, .55)*.98);
      gl_FragColor = vec4(mix(c, mix(m, hue(p,.55), .5), trail), 1.); }`,
});
const finalMat = new THREE.ShaderMaterial({
  uniforms: {src: {value: null}, ...U, uFlash: {value: 0}},
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }`,
  fragmentShader: `uniform sampler2D src; uniform float uTrip, uTime, uFlash; varying vec2 vUv;
    vec3 pal(float t){ return .5+.5*cos(6.2832*(t+vec3(0.,.33,.67))); }
    float bay(vec2 p){ ivec2 q = ivec2(mod(p, 4.)); int i = q.x + q.y*4;
      float m[16]; m[0]=0.;m[1]=8.;m[2]=2.;m[3]=10.;m[4]=12.;m[5]=4.;m[6]=14.;m[7]=6.;m[8]=3.;m[9]=11.;m[10]=1.;m[11]=9.;m[12]=15.;m[13]=7.;m[14]=13.;m[15]=5.;
      for (int k=0;k<16;k++) if (k==i) return m[k]/16.; return 0.; }
    void main(){
      vec2 uv = vUv;
      uv.x += sin(uv.y*18. + uTime*2.)*.004*uTrip;
      vec3 c = texture2D(src, uv).rgb;
      float l = dot(c, vec3(.299,.587,.114));
      vec3 dye = pal(l*1.6 + sin(uv.x*6.+uTime*.7)*.25 + cos(uv.y*5.-uTime*.5)*.25 - uTime*.15);
      c = mix(c, mix(c, dye*(.5+l), .55), uTrip*.6);
      c = mix(vec3(l), c, 1. + uTrip*.6);
      c = mix(c, vec3(1.), uFlash);
      // warm golden grade + slight vignette
      c *= vec3(1.04, 1., .93);
      float v = smoothstep(1.1, .35, length(vUv-.5)); c *= mix(.78, 1., v);
      c = floor(c*28. + bay(gl_FragCoord.xy)) / 28.;
      gl_FragColor = vec4(c, 1.); }`,
});
const quadM = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), blendMat); postScene.add(quadM);
let acc = [rtA, rtB], lastT = -99;

function updateWorld(t) {
  U.uTime.value = t;
  U.uBreathe.value = smooth(4, 5.5, t) * (1 - smooth(26, 28, t)) * (0.6 + 0.4*smooth(8, 12, t));
  U.uDrip.value = smooth(8.6, 11.8, t) * (1 - smooth(15, 17, t)) + 0.15*smooth(17, 20, t);
  U.uKal.value = smooth(12.8, 14.6, t) * (1 - smooth(15.6, 16.4, t)) + 0.25*smooth(16.4, 20, t);
  U.uTrip.value = smooth(4, 8, t)*0.55 + smooth(12, 16, t)*0.3 + smooth(20, 24, t)*0.15;
  const [cx, cz] = setCamera(t);
  // sun follows camera for shadows
  sun.position.set(cx + sunDir.x*400, sunDir.y*400, cz + sunDir.z*400); sun.target.position.set(cx, 0, cz - 60);
  // marquee drops
  {
    const p = marquee.drops.geometry.attributes.position, dr = U.uDrip.value;
    marquee.seeds.forEach(([sx, ph, sp], i) => { const f = ((t*sp*0.35 + ph) % 1); p.setXYZ(i, sx*marquee.fw, 4.4 - f*4.4*Math.min(1, dr*2), 2.42 + 0.05*i%1); });
    p.needsUpdate = true; marquee.drops.visible = dr > 0.05;
  }
  // steeple stretch + twist
  const st = smooth(12.6, 15.2, t) * (1 - smooth(16, 18, t));
  steeple.scale.set(1 - 0.35*st, 1 + 5.5*st, 1 - 0.35*st); steeple.rotation.y = st*t*0.9;
  // windmill: slow turn, then rainbow pinwheel
  const pw = smooth(16.3, 17.8, t);
  const {hub, sails, blades} = windmill.userData;
  hub.rotation.z = -(t*0.5 + pw*Math.pow(Math.max(0, t-16.3), 1.6)*1.6);
  hub.scale.setScalar(1 + pw*1.4);
  sails.forEach(s => s.visible = pw < 0.5); blades.forEach(b => b.visible = pw >= 0.5);
  // whale
  const wr = smooth(20.2, 24.5, t), arc = Math.sin(Math.min(1, Math.max(0, (t-20.2)/7))*Math.PI);
  whale.position.set(WHALE_AT.x, lerp(-14, 3.5, wr) + Math.sin(t*1.3)*0.4, WHALE_AT.z);
  whale.rotation.set(-0.55*(1-wr) - 0.25*arc + 0.15, 0.9 + Math.sin(t*0.5)*0.1, Math.sin(t*0.8)*0.06);
  whale.scale.setScalar(1.35);
  whale.visible = t > 19.5;
  const ring = whale.userData.ring; ring.position.set(WHALE_AT.x, -0.4, WHALE_AT.z); ring.visible = t > 20 && t < 27; ring.scale.setScalar(1 + (t-20)*0.35); ring.material.opacity = Math.max(0, 0.7 - (t-20)*0.1);
  {
    const sp = spout.geometry.attributes.position, on = smooth(22.5, 23.3, t)*(1 - smooth(28, 29, t));
    const head = new THREE.Vector3(0, 3.6, 5).multiplyScalar(1.35).applyEuler(whale.rotation).add(whale.position);
    spout.userData.seeds.forEach(([ph, a, r, v], i) => {
      const age = ((t*0.6 + ph) % 1) * 2.2;
      const x = Math.cos(a)*r*age*3, z = Math.sin(a)*r*age*3, y = v*age - 9.8*age*age*0.5;
      sp.setXYZ(i, head.x + x, head.y + Math.max(y, -3), head.z + z);
    });
    sp.needsUpdate = true; spout.visible = on > 0.02; spout.material.size = 0.9*on + 0.1;
  }
  // rain
  const rn = smooth(26.5, 27.6, t);
  rain.visible = rn > 0.01;
  if (rain.visible) {
    const p = rain.geometry.attributes.position, c = camera.position;
    rain.userData.s.forEach(([x, z, ph, sp], i) => {
      if (i/RAIN_N > rn) { p.setXYZ(i*2, 0, -999, 0); p.setXYZ(i*2+1, 0, -999, 0); return; }
      const y = 30 - ((t*sp + ph*40) % 40);
      p.setXYZ(i*2, c.x + x, c.y + y, c.z + z); p.setXYZ(i*2+1, c.x + x, c.y + y + 1.8, c.z + z);
    });
    p.needsUpdate = true;
  }
  finalMat.uniforms.uFlash.value = smooth(29.3, 30, t)*0.85;
}

function draw(t, trail) {
  updateWorld(t);
  renderer.setRenderTarget(rtS); renderer.render(scene, camera);
  quadM.material = blendMat; blendMat.uniforms.cur.value = rtS.texture; blendMat.uniforms.prev.value = acc[0].texture; blendMat.uniforms.trail.value = trail;
  renderer.setRenderTarget(acc[1]); renderer.render(postScene, postCam);
  acc = [acc[1], acc[0]];
}
const trailAt = t => 0.72*smooth(4, 6, t)*(1 - smooth(26, 28, t));

window.renderAt = (t) => {
  if (OVERHEAD) return renderOverhead();
  const tr = trailAt(t);
  if (tr > 0.01 && Math.abs(t - lastT - 1/30) > 1e-4) {
    // warm up the trail history so stills match a running render
    for (let k = 14; k >= 1; k--) draw(t - k/30, trailAt(t - k/30));
  }
  draw(t, tr); lastT = t;
  quadM.material = finalMat; finalMat.uniforms.src.value = acc[0].texture;
  renderer.setRenderTarget(null); renderer.render(postScene, postCam);
  return renderer.domElement.toDataURL('image/png');
};

// overhead orthographic view of the same window as the aerial crop
const OV = (Q.get('ov') || '-240,-330,300,630').split(',').map(Number);
function renderOverhead() {
  updateWorld(0);
  scene.fog = null; sky.visible = false; whale.visible = false; spout.visible = false;
  const oc = new THREE.OrthographicCamera(OV[0], OV[2], -OV[1], -OV[3], 1, 2000);
  oc.position.set(0, 800, 0); oc.up.set(0, 0, -1); oc.lookAt(0, 0, 0);
  sun.position.set(sunDir.x*400, sunDir.y*400 + 300, sunDir.z*400); sun.target.position.set(0, 0, 0);
  renderer.setRenderTarget(null); renderer.render(scene, oc);
  return renderer.domElement.toDataURL('image/png');
}
window.ready = true;
