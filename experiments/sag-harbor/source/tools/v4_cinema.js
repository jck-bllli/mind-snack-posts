  const grp = new THREE.Group(); grp.position.set(mx, 0, mz); grp.rotation.y = facing; scene.add(grp);
  // Sag Harbor Cinema, matched to Jack's key-shot photo: white streamline-moderne front with a rounded,
  // blue-trimmed top, big red stacked SAG / HARBOR letters, thin red band, blue glass doors and base, poster cases.
  const fw = 14, fh = 11.5;
  wallH = Math.max(wallH, fh); special.cinema.wallH = wallH;
  const roundedRect = (w, h, r) => { const s = new THREE.Shape(); s.moveTo(-w/2, 0); s.lineTo(w/2, 0); s.lineTo(w/2, h - r); s.quadraticCurveTo(w/2, h, w/2 - r, h); s.lineTo(-w/2 + r, h); s.quadraticCurveTo(-w/2, h, -w/2, h - r); s.lineTo(-w/2, 0); return s; };
  const cWhite = new THREE.MeshLambertMaterial({color: '#f3f1ea'}), cBlue = new THREE.MeshLambertMaterial({color: '#2a5aa8'});
  const fShape = new THREE.Mesh(new THREE.ExtrudeGeometry(roundedRect(fw, fh, 3.2), {depth: 1.0, bevelEnabled: false, curveSegments: 10}), cWhite);
  fShape.position.z = -1.0; fShape.castShadow = fShape.receiveShadow = true; grp.add(fShape);
  const trim = new THREE.Mesh(new THREE.ExtrudeGeometry(roundedRect(fw + 0.5, fh + 0.3, 3.4), {depth: 1.0, bevelEnabled: false, curveSegments: 10}), cBlue);
  trim.position.z = -1.12; grp.add(trim);
  const back = new THREE.Mesh(new THREE.BoxGeometry(fw, fh, 14), new THREE.MeshLambertMaterial({color: '#d8d4ca'})); back.position.set(0, fh/2, -8.2); back.castShadow = true; grp.add(back);
  // letters: stacked, red, own block lettering
  const lettersT = canvasTex(256, 192, (g, w, h) => {
    // matches the key-shot photo: smaller SAG with a red underline, bigger HARBOR below it, red rule under HARBOR
    g.clearRect(0, 0, w, h); g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = '#d42a24';
    g.font = '900 54px "Arial Black", Arial, sans-serif'; g.fillText('SAG', w/2, 44);
    g.fillRect(w/2 - 62, 74, 124, 6);
    g.font = '900 70px "Arial Black", Arial, sans-serif'; const hw = g.measureText('HARBOR').width;
    if (hw > w - 6) g.font = `900 ${Math.floor(70*(w - 6)/hw)}px "Arial Black", Arial, sans-serif`;
    g.fillText('HARBOR', w/2, 122);
    g.fillRect(4, 160, w - 8, 6);
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
  const letters = new THREE.Mesh(new THREE.PlaneGeometry(8.4, 6.3, 48, 30), marqueeMat); letters.position.set(0, 7.6, 0.06); grp.add(letters);
  const halo = new THREE.Mesh(new THREE.PlaneGeometry(9.6, 7.4), glowM); halo.position.set(0, 7.6, 0.12); grp.add(halo);
  const band = new THREE.Mesh(new THREE.BoxGeometry(9.4, 0.22, 0.25), new THREE.MeshLambertMaterial({color: '#c8221c', emissive: '#5a0a08'})); band.position.set(0, 4.15, 0.1); grp.add(band);
  // entrance: blue glass doors, blue base, poster cases
  const glassT = canvasTex(64, 32, (g, w, h) => { const gr = g.createLinearGradient(0, 0, w, h); gr.addColorStop(0, '#1d3f78'); gr.addColorStop(.5, '#6f9bd6'); gr.addColorStop(1, '#1a3466'); g.fillStyle = gr; g.fillRect(0, 0, w, h); g.fillStyle = '#c8d4e4'; for (let x = 0; x <= w; x += 8) g.fillRect(x, 0, 1, h); g.fillRect(0, 0, w, 1); g.fillRect(0, h - 1, w, 1); });
  const doors = new THREE.Mesh(new THREE.PlaneGeometry(6.4, 2.9), new THREE.MeshLambertMaterial({map: glassT})); doors.position.set(0, 1.75, 0.05); grp.add(doors);
  const base = new THREE.Mesh(new THREE.BoxGeometry(fw, 0.6, 0.25), cBlue); base.position.set(0, 0.3, 0.1); grp.add(base);
  const doorTop = new THREE.Mesh(new THREE.BoxGeometry(6.8, 0.3, 0.3), cBlue); doorTop.position.set(0, 3.25, 0.12); grp.add(doorTop);
  const posterT = canvasTex(24, 36, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#f2c230'); gr.addColorStop(1, '#c8402a'); g.fillStyle = gr; g.fillRect(0, 0, w, h); g.fillStyle = '#1d2b45'; g.beginPath(); g.arc(w/2, h*0.42, 6, 0, 7); g.fill(); g.fillRect(4, h - 9, w - 8, 3); });
  for (const sx of [-5.3, 5.3]) {
    const fr = new THREE.Mesh(new THREE.BoxGeometry(1.6, 2.3, 0.18), cBlue); fr.position.set(sx, 1.9, 0.12); grp.add(fr);
    const po = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 1.95), new THREE.MeshLambertMaterial({map: posterT})); po.position.set(sx, 1.9, 0.22); grp.add(po);
  }
  // neighbours: red-brick two-story with an orange awning on the viewer's left, lighter storefront on the right
  const nb = (x, w, h, map, tint) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, 10), [cWhite, cWhite, cWhite, cWhite, new THREE.MeshLambertMaterial({map, color: tint || '#ffffff'}), cWhite]); m.position.set(x, h/2, -5); m.castShadow = m.receiveShadow = true; grp.add(m); return m; };
  const brickT = canvasTex(64, 64, (g, w, h) => { sidingBase(g, SIDING[6], w, h); for (const x of [10, 38]) { g.fillStyle = '#efe6d6'; g.fillRect(x - 2, 6, 18, 22); glass(g, x, 8, 14, 18); } g.fillStyle = '#2b1d16'; g.fillRect(0, 36, w, 28); glass(g, 4, 40, 34, 22); g.fillStyle = '#3b2a1c'; g.fillRect(44, 38, 14, 26); });
  nb(-(fw/2 + 4.0), 8, 8.2, brickT);
  const awnO = new THREE.Mesh(new THREE.PlaneGeometry(7.4, 1.5), new THREE.MeshLambertMaterial({color: '#e0582a', side: THREE.DoubleSide})); awnO.position.set(-(fw/2 + 4.0), 3.0, 0.65); awnO.rotation.x = -1.0; grp.add(awnO);
  const lightT = canvasTex(64, 64, (g, w, h) => { sidingBase(g, SIDING[1], w, h); for (const x of [8, 36]) { g.fillStyle = '#ffffff'; g.fillRect(x - 2, 6, 20, 20); glass(g, x, 8, 16, 16); } g.fillStyle = '#f4f0e6'; g.fillRect(0, 34, w, 30); glass(g, 4, 38, 40, 24); g.fillStyle = '#1d2b45'; g.fillRect(48, 38, 12, 26); });
  nb(fw/2 + 4.0, 8, 7.4, lightT);
  // tall leafy trees either side
  const leaf = new THREE.MeshLambertMaterial({color: '#4f7a34', flatShading: true}), bark = new THREE.MeshLambertMaterial({color: '#4a3626'});
  for (const sx of [-(fw/2 + 0.6), fw/2 + 0.6]) {
    const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.32, 6, 6), bark); tr.position.set(sx, 3, 2.6); tr.castShadow = true; grp.add(tr);
    for (const [ox, oy, oz, r] of [[0, 8.2, 2.6, 2.6], [0.9, 9.6, 2.2, 2.0], [-1.0, 9.2, 3.0, 2.1], [0.2, 10.8, 2.6, 1.6], [-0.6, 7.0, 3.4, 1.9]]) {
      const c = new THREE.Mesh(new THREE.IcosahedronGeometry(r, 0), leaf); c.position.set(sx + ox, oy, oz); c.castShadow = true; grp.add(c);
    }
  }
  // falling paint drops
  const N = 140, dp = new Float32Array(N*3), dc = new Float32Array(N*3);
  for (let i=0;i<N;i++) { const c = new THREE.Color().setHSL(rnd(), 1, .55); dc.set([c.r,c.g,c.b], i*3); }
  const dg = new THREE.BufferGeometry(); dg.setAttribute('position', new THREE.BufferAttribute(dp, 3)); dg.setAttribute('color', new THREE.BufferAttribute(dc, 3));
  marquee = {grp, drops: new THREE.Points(dg, new THREE.PointsMaterial({size: 0.28, vertexColors: true})), N, fw, seeds: [...Array(N)].map(() => [R(-.5,.5), R(0,1), R(1.5,3.5)]), glowM, letters};
  marquee.drops.frustumCulled = false; grp.add(marquee.drops);
  window.cinemaAt = [mx, mz, facing];
