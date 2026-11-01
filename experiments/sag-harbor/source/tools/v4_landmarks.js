// ---------- v4 landmarks and whaling-town details (no shared rnd use, so shop looks stay locked) ----------
let seed2 = 2026;
const rnd2 = () => { seed2 = (seed2 * 16807) % 2147483647; return (seed2 - 1) / 2147483646; };
const copper = new THREE.MeshLambertMaterial({color: '#4f8f7a'});
const boneM = new THREE.MeshLambertMaterial({color: '#efe6d0'});
const whiteM = new THREE.MeshLambertMaterial({color: '#f4efe4'});
const ironM = new THREE.MeshLambertMaterial({color: '#2a2a2e'});
function weathervane(x, y, z, sc = 1, ry = 0) {
  const g = new THREE.Group(); g.position.set(x, y, z); g.rotation.y = ry; g.scale.setScalar(sc); scene.add(g);
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.05, 1.6, 4), ironM); post.position.y = 0.8; g.add(post);
  const ws = new THREE.Shape(); // whale silhouette (original)
  ws.moveTo(-1.0, 0); ws.quadraticCurveTo(-0.9, 0.35, -0.2, 0.32); ws.quadraticCurveTo(0.5, 0.28, 0.75, 0.05);
  ws.lineTo(1.05, 0.28); ws.lineTo(0.98, -0.02); ws.lineTo(1.08, -0.26); ws.lineTo(0.74, -0.06);
  ws.quadraticCurveTo(0.2, -0.3, -0.6, -0.22); ws.quadraticCurveTo(-1.0, -0.15, -1.0, 0);
  const wm = new THREE.Mesh(new THREE.ExtrudeGeometry(ws, {depth: 0.05, bevelEnabled: false}), copper); wm.position.set(0, 1.7, -0.025); g.add(wm);
  const arrow = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.04, 0.04), ironM); arrow.position.y = 1.25; g.add(arrow);
  for (const [a, b] of [[0.9, 0], [0, 0.9]]) { const c = new THREE.Mesh(new THREE.BoxGeometry(a || 0.04, 0.04, b || 0.04), ironM); c.position.y = 1.0; g.add(c); }
  return g;
}
function anchor(x, z, ry = 0, sc = 1) {
  const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = ry; g.scale.setScalar(sc); scene.add(g);
  const shank = new THREE.Mesh(new THREE.BoxGeometry(0.22, 2.6, 0.22), ironM); shank.position.y = 1.5; g.add(shank);
  const stock = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.16, 1.9), ironM); stock.position.y = 2.6; g.add(stock);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.05, 4, 10), ironM); ring.position.y = 3.0; g.add(ring);
  const arms = new THREE.Mesh(new THREE.TorusGeometry(0.95, 0.1, 4, 12, Math.PI), ironM); arms.rotation.z = Math.PI; arms.position.y = 1.15; g.add(arms);
  for (const s of [-1, 1]) { const f = new THREE.Mesh(new THREE.ConeGeometry(0.28, 0.6, 4), ironM); f.position.set(s*0.95, 1.4, 0); g.add(f); }
  g.traverse(m => { if (m.isMesh) m.castShadow = true; });
  return g;
}
function shipBell(x, z) {
  const g = new THREE.Group(); g.position.set(x, 0, z); scene.add(g);
  for (const s of [-1, 1]) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.2, 2.6, 0.2), pierMat); p.position.set(s*0.7, 1.3, 0); g.add(p); }
  const beam = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.2, 0.25), pierMat); beam.position.y = 2.6; g.add(beam);
  const bell = new THREE.Mesh(new THREE.LatheGeometry([[0.05, 0], [0.42, 0.02], [0.36, 0.2], [0.28, 0.6], [0.3, 0.75], [0.0, 0.8]].map(([r, y]) => new THREE.Vector2(r, -y)), 10),
    new THREE.MeshLambertMaterial({color: '#c9a24a', emissive: '#4a3010', side: THREE.DoubleSide}));
  bell.position.y = 2.5; g.add(bell);
  g.traverse(m => { if (m.isMesh) m.castShadow = true; });
}
// nautical signal-flag bunting
const sigTex = [...Array(10)].map((_, k) => canvasTex(8, 8, (g, w, h) => {
  const C = ['#f2c230', '#1d3f9e', '#c8202a', '#ffffff', '#111111'];
  const a = C[k % 5], b = C[(k * 3 + 1) % 5];
  g.fillStyle = a; g.fillRect(0, 0, w, h); g.fillStyle = b;
  if (k % 4 === 0) g.fillRect(0, 0, w / 2, h); else if (k % 4 === 1) g.fillRect(2, 2, 4, 4); else if (k % 4 === 2) { g.fillRect(0, 0, w / 2, h / 2); g.fillRect(w / 2, h / 2, w / 2, h / 2); } else g.fillRect(0, 3, w, 2);
}));
function bunting(a, b, sag = 0.8) {
  const n = Math.max(4, Math.round(a.distanceTo(b) / 0.9));
  const pts = [];
  for (let i = 0; i <= n; i++) { const u = i / n; pts.push(new THREE.Vector3().lerpVectors(a, b, u).add(new THREE.Vector3(0, -sag * 4 * u * (1 - u), 0))); }
  scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({color: '#3a3a3a'})));
  const yaw = Math.atan2(b.x - a.x, b.z - a.z) + Math.PI / 2;
  for (let i = 1; i < n; i++) {
    const f = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.5), new THREE.MeshLambertMaterial({map: sigTex[(i * 7) % 10], side: THREE.DoubleSide}));
    f.position.copy(pts[i]).add(new THREE.Vector3(0, -0.3, 0)); f.rotation.y = yaw; scene.add(f);
  }
}
const streetPt = (z, off, y = 0) => { const f = frame(dAtZ(z)); return new THREE.Vector3(f.x + f.ex * off, y, f.z + f.ez * off); };
// strings of signal flags across Main Street and along Long Wharf
for (const z of [262, 196, 120, 60]) bunting(streetPt(z, -(WALL - 1), 7.4), streetPt(z + 3, WALL - 1, 7.4), 1.0);
{
  const L = Math.hypot(wharfB[0] - wharfA[0], wharfB[1] - wharfA[1]), ux = (wharfB[0] - wharfA[0]) / L, uz = (wharfB[1] - wharfA[1]) / L, px = -uz, pz = ux;
  const at = (s, off, y) => new THREE.Vector3(wharfA[0] + ux * s + px * off, y, wharfA[1] + uz * s + pz * off);
  for (let s = 8; s < L - 60 - 16; s += 16) for (const off of [-10.5, 10.5]) bunting(at(s, off, 4.6), at(s + 16, off, 4.6), 0.7);
}
// windmill surroundings: anchor, ship's bell, low picket fence, weathervane on the cap
anchor(-16, -33, 0.6, 1.2);
shipBell(-44, -33);
weathervane(windmill.position.x, windmill.position.y + 11.4 * windmill.scale.y, windmill.position.z, 1.4);
{
  const W = windmill.position;
  for (let a = 0; a < Math.PI * 2; a += Math.PI / 14) {
    if (Math.abs(Math.sin(a - 0.2)) < 0.12 && Math.cos(a - 0.2) > 0) continue; // gap facing the wharf
    const p = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.9, 0.12), whiteM); p.position.set(W.x + Math.cos(a) * 7, 0.75, W.z + Math.sin(a) * 7); scene.add(p);
  }
}
// American Hotel weathervane
{ const H = shopGroups.find(r => r.shop.name === 'The American Hotel'); if (H) weathervane(H.x - H.nx * 6, H.ht + 0.4, H.z - H.nz * 6, 1.6); }
// a few cupolas with whale vanes along Main Street
shopGroups.filter((r, i) => i % 9 === 4).forEach(r => {
  const c = new THREE.Mesh(new THREE.BoxGeometry(1.4, 1.4, 1.4), whiteM); c.position.set(r.x - r.nx * 4, r.ht + 0.9, r.z - r.nz * 4); scene.add(c);
  const roof = new THREE.Mesh(new THREE.ConeGeometry(1.1, 1.0, 4), new THREE.MeshLambertMaterial({color: '#4f8f7a'})); roof.rotation.y = Math.PI / 4; roof.position.set(c.position.x, r.ht + 2.1, c.position.z); scene.add(roof);
  weathervane(c.position.x, r.ht + 2.5, c.position.z, 0.9, rnd2() * 6);
});
// Old Whalers' Church vane
weathervane(steepleAt[0], 53.2, steepleAt[1], 1.3);

// ---------- Sag Harbor Whaling & Historical Museum (200 Main St): Greek Revival front + whalebone gate ----------
let MUS;
{
  const f = frame(dAtZ(528)), s = -1, dx = f.ex * s, dz = f.ez * s;
  ray.set(new THREE.Vector3(f.x, 1.6, f.z), new THREE.Vector3(dx, 0, dz)); ray.far = 70;
  const h = ray.intersectObjects(bMeshes, false)[0];
  const dist = h ? Math.min(h.distance, 32) : 26;
  const g = new THREE.Group(); g.position.set(f.x + dx * dist, 0, f.z + dz * dist); g.rotation.y = Math.atan2(-dx, -dz); scene.add(g);
  const cream = new THREE.MeshLambertMaterial({color: '#f2ead8'});
  const add = (geo, mat, x, y, z) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; g.add(m); return m; };
  add(new THREE.BoxGeometry(18, 11, 14), cream, 0, 5.5, -7);
  for (const x of [-6, -2, 2, 6]) { add(new THREE.CylinderGeometry(0.5, 0.6, 9.6, 10), whiteM, x, 5.2, 2.6); add(new THREE.BoxGeometry(1.5, 0.5, 1.5), whiteM, x, 10.2, 2.6); add(new THREE.BoxGeometry(1.4, 0.4, 1.4), whiteM, x, 0.2, 2.6); }
  add(new THREE.BoxGeometry(16, 1.2, 4.4), whiteM, 0, 11.0, 1.4);
  const ped = new THREE.Shape(); ped.moveTo(-8.4, 0); ped.lineTo(8.4, 0); ped.lineTo(0, 3.0); ped.lineTo(-8.4, 0);
  const pm = new THREE.Mesh(new THREE.ExtrudeGeometry(ped, {depth: 4.4, bevelEnabled: false}), whiteM); pm.position.set(0, 11.6, -0.8); pm.castShadow = true; g.add(pm);
  add(new THREE.BoxGeometry(18.6, 0.4, 14.6), new THREE.MeshLambertMaterial({color: '#6a6660'}), 0, 11.2, -7);
  for (let x = -8.5; x <= 8.5; x += 0.8) add(new THREE.BoxGeometry(0.18, 0.8, 0.18), whiteM, x, 11.8, -13.8);
  // frieze of blubber spades and harpoons (stylized)
  const fr = canvasTex(256, 16, (gg, w, hh) => { gg.fillStyle = '#f4efe4'; gg.fillRect(0, 0, w, hh); gg.fillStyle = '#6a6458'; for (let x = 6; x < w; x += 22) { gg.fillRect(x, 3, 12, 2); gg.fillRect(x + 12, 1, 4, 6); } });
  const frieze = new THREE.Mesh(new THREE.PlaneGeometry(16, 1.0), new THREE.MeshLambertMaterial({map: fr})); frieze.position.set(0, 11.0, 3.62); g.add(frieze);
  const dark = new THREE.MeshLambertMaterial({color: '#2b2622'});
  add(new THREE.PlaneGeometry(2.2, 3.8), dark, 0, 1.9, 0.02);
  for (const x of [-6.5, -3.4, 3.4, 6.5]) for (const y of [2.6, 7.2]) { const w = add(new THREE.PlaneGeometry(1.3, 2.4), new THREE.MeshLambertMaterial({map: wallTex[0]}), x, y, 0.02); }
  add(new THREE.BoxGeometry(14, 0.3, 2.6), whiteM, 0, 0.15, 1.6); add(new THREE.BoxGeometry(12, 0.3, 1.6), whiteM, 0, 0.45, 2.0);
  // sign
  const st = canvasTex(256, 64, (gg, w, hh) => { gg.fillStyle = '#1d2b45'; gg.fillRect(0, 0, w, hh); gg.fillStyle = '#e8c873'; gg.textAlign = 'center'; gg.font = 'bold 22px Georgia, serif'; gg.fillText('SAG HARBOR WHALING', w / 2, 28); gg.font = '18px Georgia, serif'; gg.fillText('& HISTORICAL MUSEUM', w / 2, 52); });
  // whalebone gateway near the sidewalk
  const gz = dist - 9.6;
  for (const sd of [-1, 1]) {
    const c = new THREE.CatmullRomCurve3([new THREE.Vector3(sd * 1.7, 0, 0), new THREE.Vector3(sd * 1.85, 1.6, 0), new THREE.Vector3(sd * 1.55, 3.3, 0), new THREE.Vector3(sd * 0.75, 4.5, 0), new THREE.Vector3(sd * 0.05, 4.95, 0)]);
    const b = new THREE.Mesh(new THREE.TubeGeometry(c, 16, 0.2, 6), boneM); b.position.z = gz; b.castShadow = true; g.add(b);
  }
  const sign = add(new THREE.PlaneGeometry(2.6, 0.65), new THREE.MeshLambertMaterial({map: st}), 3.6, 1.6, gz + 0.1);
  add(new THREE.BoxGeometry(0.12, 1.4, 0.12), ironM, 2.4, 0.7, gz); add(new THREE.BoxGeometry(0.12, 1.4, 0.12), ironM, 4.8, 0.7, gz);
  for (let x = -9; x <= 9; x += 0.5) if (Math.abs(x) > 1.9) add(new THREE.BoxGeometry(0.1, 0.9, 0.08), whiteM, x, 0.45, gz);
  add(new THREE.BoxGeometry(7.2, 0.08, 0.06), whiteM, -5.5, 0.75, gz); add(new THREE.BoxGeometry(7.2, 0.08, 0.06), whiteM, 5.5, 0.75, gz);
  add(new THREE.BoxGeometry(3.4, 0.05, gz - 3), new THREE.MeshLambertMaterial({color: '#cfc4ae'}), 0, 0.06, 3 + (gz - 3) / 2);
  const wv = weathervane(0, 0, 0, 1.6); g.add(wv); wv.position.set(0, 14.6, -7);
  MUS = {g, x: g.position.x, z: g.position.z, nx: -dx, nz: -dz, gateZ: gz};
  console.log('museum at', g.position.x.toFixed(1), g.position.z.toFixed(1), 'setback', dist.toFixed(1));
}
