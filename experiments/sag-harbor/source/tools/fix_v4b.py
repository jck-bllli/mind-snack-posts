# Match the cinema to Jack's key-shot photo (reference/key_shot_cinema.png) more closely.
P = 'scene_sh.html'
s = open(P, encoding='utf-8').read()
a = s.index("  const fw = 14, fh = 11.5;")
b = s.index("  // falling paint drops", a)
block = s[a:b]
def R(x, y):
    global block
    assert x in block, x[:80]
    block = block.replace(x, y, 1)
R("  const fw = 14, fh = 11.5;", "  const fw = 10.6, fh = 13.5;   // narrow and tall, like the photo")
R("  const roundedRect = (w, h, r) => { const s = new THREE.Shape(); s.moveTo(-w/2, 0); s.lineTo(w/2, 0); s.lineTo(w/2, h - r); s.quadraticCurveTo(w/2, h, w/2 - r, h); s.lineTo(-w/2 + r, h); s.quadraticCurveTo(-w/2, h, -w/2, h - r); s.lineTo(-w/2, 0); return s; };",
  "  // rounded top-left corner, nearly square top-right (as in the photo)\n  const roundedRect = (w, h, r) => { const rr = 0.5; const s = new THREE.Shape(); s.moveTo(-w/2, 0); s.lineTo(w/2, 0); s.lineTo(w/2, h - rr); s.quadraticCurveTo(w/2, h, w/2 - rr, h); s.lineTo(-w/2 + r, h); s.quadraticCurveTo(-w/2, h, -w/2, h - r); s.lineTo(-w/2, 0); return s; };")
R("roundedRect(fw, fh, 3.2)", "roundedRect(fw, fh, 2.4)")
R("roundedRect(fw + 0.5, fh + 0.3, 3.4)", "roundedRect(fw + 0.4, fh + 0.35, 2.6)")
la = block.index("  const lettersT = canvasTex(256, 192, (g, w, h) => {")
lb = block.index("}, null, false);", la) + len("}, null, false);")
block = block[:la] + """  const lettersT = canvasTex(256, 192, (g, w, h) => {
    // as in the photo: medium-weight red SAG over a short maroon shelf, wider HARBOR over a long maroon shelf
    g.clearRect(0, 0, w, h); g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillStyle = '#d23a32'; g.font = 'bold 50px Arial, sans-serif'; g.fillText('SAG', w/2, 40);
    g.fillStyle = '#6e1f2c'; g.fillRect(w/2 - 58, 68, 116, 12);
    g.fillStyle = '#d23a32'; g.font = 'bold 62px Arial, sans-serif'; const hw = g.measureText('HARBOR').width;
    if (hw > w - 10) g.font = `bold ${Math.floor(62*(w - 10)/hw)}px Arial, sans-serif`;
    g.fillText('HARBOR', w/2, 118);
    g.fillStyle = '#6e1f2c'; g.fillRect(2, 150, w - 4, 14);
  }, null, false);""" + block[lb:]
R("letters.position.set(0, 7.6, 0.06);", "letters.position.set(0, 8.9, 0.06);")
R("PlaneGeometry(8.4, 6.3, 48, 30)", "PlaneGeometry(9.2, 6.9, 48, 30)")
R("halo.position.set(0, 7.6, 0.12);", "halo.position.set(0, 8.9, 0.12);")
R("band.position.set(0, 4.15, 0.1); grp.add(band);", "band.position.set(0, 4.15, 0.1); band.visible = false; grp.add(band);")
gi = block.index("  const glassT = canvasTex(64, 32,"); ge = block.index("\n", gi)
block = block[:gi] + """  const glassT = canvasTex(64, 32, (g, w, h) => { // four blue-framed glass doors
    g.fillStyle = '#1f4fa0'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 4; i++) { const x = 2 + i*15.5; const gr = g.createLinearGradient(x, 0, x + 12, h); gr.addColorStop(0, '#20304a'); gr.addColorStop(.55, '#7d97b8'); gr.addColorStop(1, '#1c2a40'); g.fillStyle = gr; g.fillRect(x, 3, 12, h - 5); g.fillStyle = '#c9a24a'; g.fillRect(x + (i % 2 ? 1 : 10), h/2, 1, 3); }
  });""" + block[ge:]
R("const doors = new THREE.Mesh(new THREE.PlaneGeometry(6.4, 2.9),", "const doors = new THREE.Mesh(new THREE.PlaneGeometry(6.2, 3.0),")
R("doors.position.set(0, 1.75, 0.05);", "doors.position.set(0, 1.9, 0.05);\n  const strip = new THREE.Mesh(new THREE.PlaneGeometry(6.4, 0.55), new THREE.MeshLambertMaterial({map: canvasTex(64, 8, (g, w, h) => { g.fillStyle = '#f6f4ee'; g.fillRect(0, 0, w, h); g.fillStyle = '#3a3a44'; for (let x = 6; x < w - 6; x += 5) g.fillRect(x, 3, 3, 2); })})); strip.position.set(0, 3.75, 0.06); grp.add(strip);")
R("doorTop.position.set(0, 3.25, 0.12);", "doorTop.position.set(0, 3.45, 0.12);")
R("  for (const sx of [-5.3, 5.3]) {\n    const fr = new THREE.Mesh(new THREE.BoxGeometry(1.6, 2.3, 0.18), cBlue); fr.position.set(sx, 1.9, 0.12); grp.add(fr);\n    const po = new THREE.Mesh(new THREE.PlaneGeometry(1.3, 1.95), new THREE.MeshLambertMaterial({map: posterT})); po.position.set(sx, 1.9, 0.22); grp.add(po);",
  "  for (const sx of [-4.4, 4.4]) {\n    const fr = new THREE.Mesh(new THREE.BoxGeometry(1.1, 1.6, 0.16), cWhite); fr.position.set(sx, 2.1, 0.12); grp.add(fr);\n    const po = new THREE.Mesh(new THREE.PlaneGeometry(0.85, 1.3), new THREE.MeshLambertMaterial({map: posterT})); po.position.set(sx, 2.1, 0.21); grp.add(po);")
na = block.index("  // neighbours:"); nbE = block.index("  // tall leafy trees either side")
block = block[:na] + """  // neighbours, as in the photo: tan-brick two-story with a red-orange awning on the left, red-brick storefront on the right
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
""" + block[nbE:]
R("  for (const sx of [-(fw/2 + 0.6), fw/2 + 0.6]) {\n    const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.32, 6, 6), bark); tr.position.set(sx, 3, 2.6); tr.castShadow = true; grp.add(tr);\n    for (const [ox, oy, oz, r] of [[0, 8.2, 2.6, 2.6], [0.9, 9.6, 2.2, 2.0], [-1.0, 9.2, 3.0, 2.1], [0.2, 10.8, 2.6, 1.6], [-0.6, 7.0, 3.4, 1.9]]) {\n      const c = new THREE.Mesh(new THREE.IcosahedronGeometry(r, 0), leaf); c.position.set(sx + ox, oy, oz); c.castShadow = true; grp.add(c);",
  "  for (const [sx, k] of [[-(fw/2 + 7.0), 1.1], [fw/2 + 3.6, 1.35]]) {\n    const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.32, 7, 6), bark); tr.position.set(sx, 3.5, 3.0); tr.castShadow = true; grp.add(tr);\n    for (const [ox, oy, oz, r] of [[0, 8.6, 3.0, 2.6], [1.2, 10.2, 2.6, 2.2], [-1.3, 9.8, 3.4, 2.2], [0.3, 11.8, 3.0, 1.9], [-0.8, 7.4, 3.6, 1.9], [1.6, 8.0, 3.2, 1.7]]) {\n      const c = new THREE.Mesh(new THREE.IcosahedronGeometry(r*k, 0), leaf); c.position.set(sx + ox*k, 1 + (oy - 1)*k*0.95, oz); c.castShadow = true; grp.add(c);")
s = s[:a] + block + s[b:]
# crosswalk to the lower left of the frame, as in the photo
x = "s.position.set(f.x + f.ex*o, 0.12, f.z + f.ez*o);"
assert x in s; s = s.replace(x, "s.position.set(f.x + f.ex*o - f.fx*6, 0.12, f.z + f.ez*o - f.fz*6);")
x = "for (const along of [-4.6, 4.6])"
assert x in s; s = s.replace(x, "for (const along of [-10.6, -1.4])")
open(P, 'w', encoding='utf-8').write(s)
# keep the reusable block file in sync
c = open('tools/v4_cinema.js', encoding='utf-8').read()
ca = c.index("  const fw = "); cb = c.index("  // falling paint drops", ca)
open('tools/v4_cinema.js', 'w', encoding='utf-8').write(c[:ca] + block + c[cb:])
print('ok')
