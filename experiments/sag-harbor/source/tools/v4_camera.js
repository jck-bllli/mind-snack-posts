// ---------- key-shot dressing at the cinema: crosswalk, yellow curb paint, red vintage convertible ----------
const CIN_D = dAtZ(cinemaPOI[1]);
{
  const f = frame(CIN_D), yaw = Math.atan2(f.fx, f.fz);
  const zebra = new THREE.MeshLambertMaterial({color: '#f4f2ea', polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4});
  for (let o = -CURB + 0.6; o <= CURB - 0.6; o += 1.2) {
    const s = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.02, 3.2), zebra);
    s.position.set(f.x + f.ex*o, 0.12, f.z + f.ez*o); s.rotation.y = yaw; s.receiveShadow = true; scene.add(s);
  }
  const yel = new THREE.MeshLambertMaterial({color: '#f2c230'});
  for (const sd of [-1, 1]) for (const along of [-4.6, 4.6]) {
    const c = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.22, 4.5), yel);
    c.position.set(f.x + f.ex*sd*(CURB + 0.1) + f.fx*along, 0.11, f.z + f.ez*sd*(CURB + 0.1) + f.fz*along); c.rotation.y = yaw; scene.add(c);
  }
  // red vintage convertible at the cinema-side curb
  const car = new THREE.Group(); car.position.set(f.x - f.ex*(CURB - 1.2) - f.fx*6.8, 0, f.z - f.ez*(CURB - 1.2) - f.fz*6.8); car.rotation.y = yaw; scene.add(car);
  const red = new THREE.MeshPhongMaterial({color: '#c41a1a', specular: '#ffffff', shininess: 60}), chrome = new THREE.MeshPhongMaterial({color: '#d8dce2', specular: '#ffffff', shininess: 90});
  const tan = new THREE.MeshLambertMaterial({color: '#d8c49a'}), tyre = new THREE.MeshLambertMaterial({color: '#151515'}), wall = new THREE.MeshLambertMaterial({color: '#f4f2ea'});
  const part = (geo, mat, x, y, z, rx = 0) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.rotation.x = rx; m.castShadow = true; car.add(m); return m; };
  part(new THREE.BoxGeometry(1.95, 0.6, 5.0), red, 0, 0.75, 0);
  part(new THREE.BoxGeometry(1.9, 0.25, 1.6), red, 0, 1.12, 1.6);           // hood
  part(new THREE.BoxGeometry(1.9, 0.25, 1.3), red, 0, 1.12, -1.8);          // trunk deck
  for (const sx of [-1, 1]) part(new THREE.BoxGeometry(0.18, 0.28, 2.0), red, sx*0.86, 1.12, -0.1); // doors' top line
  part(new THREE.BoxGeometry(1.5, 0.5, 0.5), tan, 0, 1.15, -0.7); part(new THREE.BoxGeometry(1.5, 0.35, 0.9), tan, 0, 0.95, -0.4);
  part(new THREE.BoxGeometry(1.5, 0.5, 0.5), tan, 0, 1.15, 0.5); part(new THREE.BoxGeometry(1.5, 0.35, 0.9), tan, 0, 0.95, 0.8);
  part(new THREE.BoxGeometry(1.7, 0.5, 0.05), new THREE.MeshLambertMaterial({color: '#a8c8e0', transparent: true, opacity: 0.55}), 0, 1.5, 0.95, -0.35);
  part(new THREE.BoxGeometry(2.0, 0.16, 0.16), chrome, 0, 0.55, 2.55); part(new THREE.BoxGeometry(2.0, 0.16, 0.16), chrome, 0, 0.55, -2.55);
  for (const sx of [-0.65, 0.65]) part(new THREE.CylinderGeometry(0.14, 0.14, 0.08, 10), new THREE.MeshBasicMaterial({color: '#fff6d8'}), sx, 0.92, 2.52, Math.PI/2);
  for (const sx of [-1, 1]) for (const sz of [-1.6, 1.6]) {
    const w = part(new THREE.CylinderGeometry(0.38, 0.38, 0.26, 12), tyre, sx*0.9, 0.38, sz); w.rotation.z = Math.PI/2;
    const ww = part(new THREE.CylinderGeometry(0.24, 0.24, 0.28, 12), wall, sx*0.9, 0.38, sz); ww.rotation.z = Math.PI/2;
  }
}

// ---------- camera: a held beat per landmark, gentle strolls and glides, cuts on the music ----------
const WHALE_AT = new THREE.Vector3(22, 0, -308);
const tmp = new THREE.Vector3();
const HOTEL = shopGroups.find(r => r.shop.name === 'The American Hotel');
const facadeView = (rec, back, y = 1.65) => new THREE.Vector3(rec.x + rec.nx*back, y, rec.z + rec.nz*back);
const CIN = (() => { const f = frame(CIN_D); return {x: marquee.grp.position.x, z: marquee.grp.position.z, nx: f.ex, nz: f.ez}; })();
const CH = (() => { const [tx, tz] = steepleAt; const {ob} = special.church; const s = (ob.uz < 0) ? 1 : -1; return {x: tx, z: tz, nx: ob.ux*s, nz: ob.uz*s}; })();
const WMILL = windmill.position.clone();
// shot list: [start, end, name, pose(u, t) -> {pos, look, fov}]
const SHOTS = [
  [0, 5, 'whaling museum', u => ({ pos: streetPt(lerp(552, 546, u), 6.0, 1.65), look: new THREE.Vector3(MUS.x, 5.5, MUS.z).lerp(streetPt(500, 0, 3), 0.15), fov: 64 })],
  [5, 10, "old whalers' church", u => { const lx = -CH.nz, lz = CH.nx; return { pos: new THREE.Vector3(CH.x + CH.nx*40 + lx*lerp(-3, 3, u), 1.5, CH.z + CH.nz*40 + lz*lerp(-3, 3, u)), look: new THREE.Vector3(CH.x, lerp(12, 24, u), CH.z), fov: 66 }; }],
  [10, 15, 'main street stroll', (u, t) => { const f = frame(dAtZ(lerp(292, 286, u))); const yaw = Math.atan2(f.fx, f.fz) + Math.sin(t*0.55)*0.38; return { pos: new THREE.Vector3(f.x + f.ex*7.6, 1.65 + Math.sin(t*2*Math.PI*0.75)*0.03, f.z + f.ez*7.6), look: new THREE.Vector3(f.x + f.ex*7.6 + Math.sin(yaw)*10, 1.6, f.z + f.ez*7.6 + Math.cos(yaw)*10), fov: 68 }; }],
  [15, 19, 'KEY: sag harbor cinema', u => { const f = frame(CIN_D); const p = new THREE.Vector3(f.x + f.ex*(8.2 - 0.6*u), 1.25, f.z + f.ez*(8.2 - 0.6*u)); return { pos: p, look: new THREE.Vector3(CIN.x, 5.6, CIN.z), fov: 68 }; }],
  [19, 23, 'the wharf shop', u => ({ pos: facadeView(WSHOP, lerp(15.5, 12.5, u)), look: new THREE.Vector3(WSHOP.x, 4.0, WSHOP.z), fov: 66 })],
  [23, 27, 'the american hotel', u => { const lx = -HOTEL.nz, lz = HOTEL.nx; return { pos: facadeView(HOTEL, 17).add(new THREE.Vector3(lx*lerp(-2.4, 2.4, u), 0, lz*lerp(-2.4, 2.4, u))), look: new THREE.Vector3(HOTEL.x, 6.0, HOTEL.z), fov: 66 }; }],
  [27, 31.5, 'windmill + bridge', u => { const a = lerp(-0.55, 0.15, u); const dir = new THREE.Vector3(Math.cos(a), 0, Math.sin(a)); return { pos: WMILL.clone().add(dir.multiplyScalar(26)).setY(lerp(3.2, 5.0, u)), look: new THREE.Vector3(WMILL.x, 9.5, WMILL.z), fov: 62 }; }],
  [31.5, 36, 'long wharf + harbor', u => ({ pos: new THREE.Vector3(lerp(126, 112, u), lerp(46, 40, u), lerp(-470, -440, u)), look: new THREE.Vector3(lerp(112, 100, u), 0, -20), fov: 66 })],
  [36, 42, 'whale off long wharf', u => ({ pos: new THREE.Vector3(17, 1.8, lerp(-204, -209, u)), look: new THREE.Vector3(WHALE_AT.x, 24, WHALE_AT.z), fov: 64 })],
  [42, 45, 'color rain', u => ({ pos: new THREE.Vector3(17, 1.8 + u*3, -209), look: new THREE.Vector3(WHALE_AT.x, 24 + u*60, WHALE_AT.z), fov: 64 })],
];
const TOTAL = 45;
function shotAt(t) { for (const s of SHOTS) if (t >= s[0] && t < s[1]) return s; return SHOTS[SHOTS.length - 1]; }
function setCamera(t) {
  const [a, b, , fn] = shotAt(t), u = smooth(0, 1, (t - a) / (b - a)) * 0.6 + 0.4 * (t - a) / (b - a);
  const {pos, look, fov} = fn(u, t);
  camera.position.copy(pos); camera.up.set(0, 1, 0); camera.lookAt(look);
  if (camera.fov !== fov) { camera.fov = fov; camera.updateProjectionMatrix(); }
  return [pos.x, pos.z];
}
window.SHOTS = SHOTS.map(s => [s[0], s[1], s[2]]);
