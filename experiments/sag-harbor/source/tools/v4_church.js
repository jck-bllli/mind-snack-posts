  const white = new THREE.MeshLambertMaterial({color:'#f6f2ea'}); steeple.userData.mat = white;
  // Old Whalers' Church: battered Egyptian Revival temple front and tapered tower, stylized steeple on top
  const whiteF = new THREE.MeshLambertMaterial({color:'#f4efe4', flatShading: true}), darkW = new THREE.MeshLambertMaterial({color:'#2a2a30'});
  steeple.rotation.y = Math.atan2(ob.ux*s, ob.uz*s); // local +z faces Union Street
  const frustum = (wb, wt, h, db, dt) => { const g = new THREE.CylinderGeometry(Math.SQRT1_2, Math.SQRT1_2, h, 4, 1); g.rotateY(Math.PI/4);
    const p = g.attributes.position; for (let i=0;i<p.count;i++){ const top = p.getY(i) > 0; p.setX(i, p.getX(i)*(top?wt:wb)); p.setZ(i, p.getZ(i)*(top?dt:db)); } return g; };
  const put = (geo, mat, x, y, z) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; steeple.add(m); return m; };
  const FW = Math.max(16, ob.hb*2 + 1);
  put(frustum(FW, FW*0.93, 13, 3, 2.6), whiteF, 0, 6.5, -1.5);
  put(frustum(FW*0.93, FW*1.0, 1.4, 2.6, 3.4), whiteF, 0, 13.7, -1.5);
  put(frustum(9, 7, 18, 9, 7), whiteF, 0, 9, 0);
  put(frustum(7, 8.4, 1.6, 7, 8.4), whiteF, 0, 18.8, 0);
  put(new THREE.PlaneGeometry(2.6, 4.2), darkW, 0, 2.1, 4.52);
  for (const x of [-1.6, 1.6]) put(new THREE.PlaneGeometry(0.9, 6.5), darkW, x, 10.5, 4.06);
  for (const x of [-(FW/2 - 2.6), FW/2 - 2.6]) { put(new THREE.PlaneGeometry(1.1, 6.2), darkW, x, 6.0, 0.02); put(new THREE.PlaneGeometry(1.4, 2.4), darkW, x, 1.2, 0.02); }
  const winged = canvasTex(64, 16, (g, w, h) => { g.clearRect(0,0,w,h); g.fillStyle = '#d8c48a'; g.beginPath(); g.ellipse(w/2, h/2, 6, 5, 0, 0, 7); g.fill(); g.fillRect(4, h/2 - 2, w - 8, 3); });
  const disc = new THREE.Mesh(new THREE.PlaneGeometry(5, 1.25), new THREE.MeshLambertMaterial({map: winged, transparent: true, alphaTest: .4})); disc.position.set(0, 17.2, 3.62); steeple.add(disc);
  const tiers = [[5.4, 5.4, 19.6, 8], [4.2, 4.2, 27.6, 6], [3, 3, 33.6, 5]];
  for (const [w, d, y, h] of tiers) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), white); m.position.y = y + h/2; m.castShadow = m.receiveShadow = true; steeple.add(m);
    for (const ang of [0, 1, 2, 3]) {
      const win = new THREE.Mesh(new THREE.PlaneGeometry(w*0.35, h*0.5), darkW);
      const a = ang*Math.PI/2; win.position.set(Math.sin(a)*(w/2+0.02), y + h*0.55, Math.cos(a)*(d/2+0.02)); win.rotation.y = a; steeple.add(win);
    }
  }
  const spire = new THREE.Mesh(new THREE.ConeGeometry(1.6, 16, 8), white); spire.position.y = 38.6 + 8; spire.castShadow = true; steeple.add(spire);
