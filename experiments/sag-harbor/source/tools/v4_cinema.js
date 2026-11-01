  const grp = new THREE.Group(); grp.position.set(mx, 0, mz); grp.rotation.y = facing; scene.add(grp);
  // Sag Harbor Cinema, matched to Jack's key-shot photo: white streamline-moderne front with a rounded,
  // blue-trimmed top, big red stacked SAG / HARBOR letters, thin red band, blue glass doors and base, poster cases.
  const fw = 10.6, fh = 13.5;   // narrow and tall, like the photo
  wallH = Math.max(wallH, fh); special.cinema.wallH = wallH;
  // rounded top-left corner, nearly square top-right (as in the photo)
  const roundedRect = (w, h, r) => { const rr = 0.5; const s = new THREE.Shape(); s.moveTo(-w/2, 0); s.lineTo(w/2, 0); s.lineTo(w/2, h - rr); s.quadraticCurveTo(w/2, h, w/2 - rr, h); s.lineTo(-w/2 + r, h); s.quadraticCurveTo(-w/2, h, -w/2, h - r); s.lineTo(-w/2, 0); return s; };
  const cWhite = new THREE.MeshLambertMaterial({color: '#f3f1ea'}), cBlue = new THREE.MeshLambertMaterial({color: '#2a5aa8'});
  const fShape = new THREE.Mesh(new THREE.ExtrudeGeometry(roundedRect(fw, fh, 2.4), {depth: 1.0, bevelEnabled: false, curveSegments: 10}), cWhite);
  fShape.position.z = -1.0; fShape.castShadow = fShape.receiveShadow = true; grp.add(fShape);
  const trim = new THREE.Mesh(new THREE.ExtrudeGeometry(roundedRect(fw + 0.4, fh + 0.35, 2.6), {depth: 1.0, bevelEnabled: false, curveSegments: 10}), cBlue);
  trim.position.z = -1.12; grp.add(trim);
  const back = new THREE.Mesh(new THREE.BoxGeometry(fw, fh, 14), new THREE.MeshLambertMaterial({color: '#d8d4ca'})); back.position.set(0, fh/2, -8.2); back.castShadow = true; grp.add(back);
  // letters: stacked, red, own block lettering
  const lettersT = canvasTex(256, 192, (g, w, h) => {
    // as in the photo: medium-weight red SAG over a short maroon shelf, wider HARBOR over a long maroon shelf
    g.clearRect(0, 0, w, h); g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillStyle = '#d23a32'; g.font = 'bold 50px Arial, sans-serif'; g.fillText('SAG', w/2, 40);
    g.fillStyle = '#6e1f2c'; g.fillRect(w/2 - 58, 68, 116, 12);
    g.fillStyle = '#d23a32'; g.font = 'bold 62px Arial, sans-serif'; const hw = g.measureText('HARBOR').width;
    if (hw > w - 10) g.font = `bold ${Math.floor(62*(w - 10)/hw)}px Arial, sans-serif`;
    g.fillText('HARBOR', w/2, 118);
    g.fillStyle = '#6e1f2c'; g.fillRect(2, 150, w - 4, 14);
  }, null, false);
  const glowM = new THREE.MeshBasicMaterial({map: lettersT, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, color: '#ff4030'});
  marqueeMat = new THREE.ShaderMaterial({
    uniforms: { map: {value: lettersT}, ...U },
    transparent: true,
    vertexShader: `uniform float uDrip, uTime; varying vec2 vUv; varying float vD;
      float h(float x){ return fract(sin(x*91.7)*437.5); }
      void main(){ vUv = uv; vec3 p = position;
        float col = floor(uv.x*48.); float len = (.3 + 1.7*h(col)) * uDrip;
        float k = 1. - uv.y;
        p.y -= k*k*len*3.6; p.x += sin(uTime*3. + col)*.06*uDrip*k; vD = k*len;
        gl_Position = projectionMatrix*modelViewMatrix*vec4(p,1.); }`,
    fragmentShader: `uniform sampler2D map; uniform float uTime, uDrip; varying vec2 vUv; varying float vD;
      vec3 pal(float t){ return .5+.5*cos(6.2832*(t+vec3(0.,.33,.67))); }
      void main(){ vec4 c = texture2D(map, vUv); if (c.a < .45) discard;
        vec3 col = mix(c.rgb, pal(vUv.y*2. + vD - uTime*.7), clamp(vD*1.2 + uDrip*.35, 0., 1.));
        gl_FragColor = vec4(pow(col, vec3(2.2)), 1.); }`,
  });
  const letters = new THREE.Mesh(new THREE.PlaneGeometry(9.2, 6.9, 48, 30), marqueeMat); letters.position.set(0, 8.9, 0.06); grp.add(letters);
  const halo = new THREE.Mesh(new THREE.PlaneGeometry(9.6, 7.4), glowM); halo.position.set(0, 8.9, 0.12); grp.add(halo);
  const band = new THREE.Mesh(new THREE.BoxGeometry(9.4, 0.22, 0.25), new THREE.MeshLambertMaterial({color: '#c8221c', emissive: '#5a0a08'})); band.position.set(0, 4.15, 0.1); band.visible = false; grp.add(band);
  // entrance: blue glass doors, blue base, poster cases
  const glassT = canvasTex(64, 32, (g, w, h) => { // four blue-framed glass doors
    g.fillStyle = '#1f4fa0'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 4; i++) { const x = 2 + i*15.5; const gr = g.createLinearGradient(x, 0, x + 12, h); gr.addColorStop(0, '#20304a'); gr.addColorStop(.55, '#7d97b8'); gr.addColorStop(1, '#1c2a40'); g.fillStyle = gr; g.fillRect(x, 3, 12, h - 5); g.fillStyle = '#c9a24a'; g.fillRect(x + (i % 2 ? 1 : 10), h/2, 1, 3); }
  });
  const doors = new THREE.Mesh(new THREE.PlaneGeometry(6.2, 3.0), new THREE.MeshLambertMaterial({map: glassT})); doors.position.set(0, 1.9, 0.05);
  const strip = new THREE.Mesh(new THREE.PlaneGeometry(6.4, 0.55), new THREE.MeshLambertMaterial({map: canvasTex(64, 8, (g, w, h) => { g.fillStyle = '#f6f4ee'; g.fillRect(0, 0, w, h); g.fillStyle = '#3a3a44'; for (let x = 6; x < w - 6; x += 5) g.fillRect(x, 3, 3, 2); })})); strip.position.set(0, 3.75, 0.06); grp.add(strip); grp.add(doors);
  const base = new THREE.Mesh(new THREE.BoxGeometry(fw, 0.6, 0.25), cBlue); base.position.set(0, 0.3, 0.1); grp.add(base);
  const doorTop = new THREE.Mesh(new THREE.BoxGeometry(6.8, 0.3, 0.3), cBlue); doorTop.position.set(0, 3.45, 0.12); grp.add(doorTop);
  const posterT = canvasTex(24, 36, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#f2c230'); gr.addColorStop(1, '#c8402a'); g.fillStyle = gr; g.fillRect(0, 0, w, h); g.fillStyle = '#1d2b45'; g.beginPath(); g.arc(w/2, h*0.42, 6, 0, 7); g.fill(); g.fillRect(4, h - 9, w - 8, 3); });
  for (const sx of [-4.4, 4.4]) {
    const fr = new THREE.Mesh(new THREE.BoxGeometry(1.1, 1.6, 0.16), cWhite); fr.position.set(sx, 2.1, 0.12); grp.add(fr);
    const po = new THREE.Mesh(new THREE.PlaneGeometry(0.85, 1.3), new THREE.MeshLambertMaterial({map: posterT})); po.position.set(sx, 2.1, 0.21); grp.add(po);
  }
  // neighbours, as in the photo: tan-brick two-story with a red-orange awning on the left, red-brick storefront on the right
  const nb = (x, w, h, map) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, 10), [cWhite, cWhite, cWhite, cWhite, new THREE.MeshLambertMaterial({map}), cWhite]); m.position.set(x, h/2, -5); m.castShadow = m.receiveShadow = true; grp.add(m); return m; };
  const brickFace = (base, mortar, draw) => canvasTex(80, 72, (g, w, h) => { g.fillStyle = base; g.fillRect(0, 0, w, h); for (let y = 0; y < h; y += 3) { g.fillStyle = mortar; g.fillRect(0, y + 2, w, 1); for (let x = (y/3 % 2)*3; x < w; x += 6) g.fillRect(x, y, 1, 2); } draw(g, w, h); });
  const leftT = brickFace('#a8805e', '#cdb89c', (g, w, h) => {
    g.fillStyle = '#f4f0e6'; g.fillRect(0, 0, w, 4);
    for (const x of [8, 32, 56]) { g.fillStyle = '#f4f0e6'; g.fillRect(x - 2, 8, 16, 22); glass(g, x, 10, 12, 18); }
    g.fillStyle = '#f4f0e6'; g.fillRect(0, 40, w, 32); glass(g, 6, 50, 40, 20); g.fillStyle = '#2b2b2b'; g.fillRect(52, 48, 12, 24);
  });
  nb(-(fw/2 + 5.2), 10, 9.4, leftT);
  const awnO = new THREE.Mesh(new THREE.PlaneGeometry(9.2, 1.7), new THREE.MeshLambertMaterial({color: '#d4502a', side: THREE.DoubleSide})); awnO.position.set(-(fw/2 + 5.2), 3.5, 0.75); awnO.rotation.x = -1.0; grp.add(awnO);
  const valO = new THREE.Mesh(new THREE.PlaneGeometry(9.2, 0.4), awnO.material); valO.position.set(-(fw/2 + 5.2), 2.95, 1.5); grp.add(valO);
  const rightT = brickFace('#8e4a36', '#b98a72', (g, w, h) => {
    for (const x of [10, 44]) { g.fillStyle = '#e8dcc8'; g.fillRect(x - 2, 8, 22, 18); glass(g, x, 10, 18, 14); }
    g.fillStyle = '#e8dcc8'; g.fillRect(0, 36, w, 3); glass(g, 4, 42, 30, 28); glass(g, 46, 42, 30, 28); g.fillStyle = '#3b2a1c'; g.fillRect(35, 42, 10, 30);
  });
  nb(fw/2 + 4.8, 9, 8.8, rightT);
  // tall leafy trees either side
  const leaf = new THREE.MeshLambertMaterial({color: '#4f7a34', flatShading: true}), bark = new THREE.MeshLambertMaterial({color: '#4a3626'});
  for (const [sx, k] of [[-(fw/2 + 3.8), 1.1], [fw/2 + 2.4, 1.3]]) {
    const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.32, 7, 6), bark); tr.position.set(sx, 3.5, 3.0); tr.castShadow = true; grp.add(tr);
    for (const [ox, oy, oz, r] of [[0, 8.6, 3.0, 2.6], [1.2, 10.2, 2.6, 2.2], [-1.3, 9.8, 3.4, 2.2], [0.3, 11.8, 3.0, 1.9], [-0.8, 7.4, 3.6, 1.9], [1.6, 8.0, 3.2, 1.7]]) {
      const c = new THREE.Mesh(new THREE.IcosahedronGeometry(r*k, 0), leaf); c.position.set(sx + ox*k, 1 + (oy - 1)*k*0.95, oz); c.castShadow = true; grp.add(c);
    }
  }
  // falling paint drops
  const N = 140, dp = new Float32Array(N*3), dc = new Float32Array(N*3);
  for (let i=0;i<N;i++) { const c = new THREE.Color().setHSL(rnd(), 1, .55); dc.set([c.r,c.g,c.b], i*3); }
  const dg = new THREE.BufferGeometry(); dg.setAttribute('position', new THREE.BufferAttribute(dp, 3)); dg.setAttribute('color', new THREE.BufferAttribute(dc, 3));
  marquee = {grp, drops: new THREE.Points(dg, new THREE.PointsMaterial({size: 0.28, vertexColors: true})), N, fw, seeds: [...Array(N)].map(() => [R(-.5,.5), R(0,1), R(1.5,3.5)]), glowM, letters};
  marquee.drops.frustumCulled = false; grp.add(marquee.drops);
  window.cinemaAt = [mx, mz, facing];
