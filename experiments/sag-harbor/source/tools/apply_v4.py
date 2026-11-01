import re
P = 'scene_sh.html'
s = open(P, encoding='utf-8').read()
def R(a, b, cnt=1):
    global s
    assert a in s, 'MISSING: ' + a[:90]
    s = s.replace(a, b, cnt)
# --- lights / sky: daylight mode for the key cinema shot
R("scene.add(new THREE.HemisphereLight('#a8c6ec', '#7a6646', 1.6));", "const hemi = new THREE.HemisphereLight('#a8c6ec', '#7a6646', 1.6); scene.add(hemi);")
R("const U = { uTime:{value:0},", "const U = { uDay:{value:0}, uTime:{value:0},")
R("fragmentShader: `uniform float uTime,uKal; uniform vec3 uSun; varying vec3 vD;", "fragmentShader: `uniform float uTime,uKal,uDay; uniform vec3 uSun; varying vec3 vD;")
R("""    if (uKal > 0.) {
      vec2 p = d.xz/(d.y+.35);""", """    if (uDay > 0.) {
      vec3 dc = mix(vec3(.82,.9,.97), vec3(.36,.6,.9), smoothstep(.0,.55,y));
      float dcl = smoothstep(.5,.78, fbm(cp*1.3+vec2(3.,uTime*.01)));
      dc = mix(dc, vec3(.98,.98,1.), dcl*.85*smoothstep(.03,.2,d.y));
      col = mix(col, dc, uDay);
    }
    if (uKal > 0.) {
      vec2 p = d.xz/(d.y+.35);""")
# --- cinema rebuilt from the key-shot photo
R("  const {P, wallH} = special.cinema;", "  let {P, wallH} = special.cinema;")
a = s.index("  const grp = new THREE.Group(); grp.position.set(mx, 0, mz); grp.rotation.y = facing; scene.add(grp);")
b = s.index("  window.cinemaAt = [mx, mz, facing];\n") + len("  window.cinemaAt = [mx, mz, facing];\n")
s = s[:a] + open('tools/v4_cinema.js', encoding='utf-8').read() + s[b:]
# --- Old Whalers' Church: Egyptian Revival front + tower, stylized steeple on top
a = s.index("  const white = new THREE.MeshLambertMaterial({color:'#f6f2ea'}); steeple.userData.mat = white;")
b = s.index("  window.steepleAt = [tx, tz];")
s = s[:a] + open('tools/v4_church.js', encoding='utf-8').read() + s[b:]
# --- windmill: bigger, stone base, windows
R("  windmill.userData = {hub, sails, blades};", """  const stone = new THREE.Mesh(new THREE.CylinderGeometry(3.5, 3.8, 0.8, 10), new THREE.MeshLambertMaterial({color: '#8a8478', flatShading: true})); stone.position.y = 0.4; windmill.add(stone);
  for (const [a, y] of [[0.0, 5.2], [Math.PI, 3.6], [Math.PI/2, 6.4]]) { const w = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.9), new THREE.MeshLambertMaterial({color: '#f4efe4'})); w.position.set(Math.sin(a)*2.62, y, Math.cos(a)*2.62); w.rotation.y = a; windmill.add(w); }
  windmill.scale.setScalar(1.3);
  windmill.userData = {hub, sails, blades};""")
# --- shops: lock the v3 look
R("const shopGroups = [];", "seed = 1104476380; // lock the v3 storefront look (seed at this point in v3)\nconst shopGroups = [];", 1)
R("  const sid = shop.type === 'bank' ? 6 : shop.type === 'civic' ? 0 : pick([0,0,1,2,3,4,5,6,7,8]);", "  let sid = shop.type === 'bank' ? 6 : shop.type === 'civic' ? 0 : pick([0,0,1,2,3,4,5,6,7,8]);\n  if (shop.name === 'The American Hotel') sid = 6;")
R("        const val = new THREE.Mesh(new THREE.PlaneGeometry(wd - 0.6, 0.35), am); val.position.set(0, 2.38, 1.12); g.add(val);",
  "        const val = new THREE.Mesh(new THREE.PlaneGeometry(wd - 0.6, 0.35), am); val.position.set(0, 2.38, 1.12); g.add(val);\n        if (sh.name === 'The American Hotel') aw.visible = val.visible = false;")
R("        pole.position.set(wd*0.35, 5.2, 0.8); pole.rotation.x = 0.8; g.add(pole);", "        pole.position.set(wd*0.35, 6.9, 0.45); pole.rotation.x = 0.8; pole.scale.y = 0.6; g.add(pole);")
R("        fl.position.set(wd*0.35 + 0.75, 5.5, 1.4); fl.rotation.x = 0.8; g.add(fl);", "        fl.position.set(wd*0.35 + 0.75, 7.15, 0.85); fl.rotation.x = 0.8; g.add(fl);")
R("      const rec = {shop: sh, g, wd, ht, x: hit.x, z: hit.z, nx: hit.nx, nz: hit.nz};", open('tools/v4_hotel.js', encoding='utf-8').read() + "      const rec = {shop: sh, g, wd, ht, x: hit.x, z: hit.z, nx: hit.nx, nz: hit.nz};")
R("  occ.push({d: cinD, s: -1, w: 16});", "  occ.push({d: cinD, s: -1, w: 32});")
R("if (rnd() < 0.7 && !(f.z > 236 && f.z < 262) &&", "if (rnd() < 0.7 && !(Math.abs(f.z - cinemaPOI[1]) < 14) &&")
# --- landmarks + new camera replace the old camera section
a = s.index("// ---------- camera: walk past the shops, stop at the Wharf Shop, swoop down Long Wharf ----------")
b = s.index("  return [pos.x, pos.z];\n}\n", a) + len("  return [pos.x, pos.z];\n}\n")
lm = open('tools/v4_landmarks.js', encoding='utf-8').read().replace("weathervane(steepleAt[0], 53.2, steepleAt[1], 1.3);", "weathervane(steepleAt[0], 54.6, steepleAt[1], 1.3);")
s = s[:a] + lm + "\n" + open('tools/v4_camera.js', encoding='utf-8').read() + s[b:]
# --- timeline (45 s)
a = s.index("  U.uBreathe.value = ")
b = s.index("  updatePeds(t);")
s = s[:a] + open('tools/v4_timeline.js', encoding='utf-8').read() + s[b:]
R("  sun.position.set(cx + sunDir.x*400, sunDir.y*400, cz + sunDir.z*400); sun.target.position.set(cx, 0, cz - 60);",
  "  const sd = day ? DAYSUN : sunDir;\n  sun.position.set(cx + sd.x*400, sd.y*400, cz + sd.z*400); sun.target.position.set(cx, 0, cz);")
R("const sunDir = new THREE.Vector3(-0.93, 0.2, -0.3).normalize();", "const sunDir = new THREE.Vector3(-0.93, 0.2, -0.3).normalize();\nconst DAYSUN = new THREE.Vector3(0.55, 0.78, 0.3).normalize();")
R("marquee.seeds.forEach(([sx, ph, sp], i) => { const f = ((t*sp*0.35 + ph) % 1); p.setXYZ(i, sx*marquee.fw, 4.4 - f*4.4*Math.min(1, dr*2), 2.42 + 0.05*i%1); });",
  "marquee.seeds.forEach(([sx, ph, sp], i) => { const f = ((t*sp*0.35 + ph) % 1); p.setXYZ(i, sx*8, 5.0 - f*5.0*Math.min(1, dr*2), 0.4); });")
R("  const pw = smooth(16.0, 17.2, t);", "  const pw = smooth(28.6, 29.8, t);")
R("  hub.rotation.z = -(t*0.5 + pw*Math.pow(Math.max(0, t-16.0), 1.6)*1.6);", "  hub.rotation.z = -(t*0.35 + pw*Math.pow(Math.max(0, t-28.6), 1.5)*1.2);")
R("  hub.scale.setScalar(1 + pw*1.4);", "  hub.scale.setScalar(1 + pw*0.8);")
R("  const wr = smooth(20.2, 22.8, t), arc = Math.sin(Math.min(1, Math.max(0, (t-20.2)/7))*Math.PI);", "  const wr = smooth(36.4, 39.0, t);")
R("lerp(-30, 16, wr) - 6*smooth(25, 28, t)", "lerp(-30, 16, wr) - 8*smooth(42.5, 45, t)")
R("  whale.visible = t > 19.5;", "  whale.visible = t > 36;")
R("ring.visible = t > 20 && t < 27; ring.scale.setScalar(1 + (t-20)*0.35); ring.material.opacity = Math.max(0, 0.7 - (t-20)*0.1);",
  "ring.visible = t > 36.3 && t < 43; ring.scale.setScalar(1 + (t-36.3)*0.35); ring.material.opacity = Math.max(0, 0.7 - (t-36.3)*0.1);")
R("on = smooth(22.3, 23.0, t)*(1 - smooth(28, 29, t));", "on = smooth(39.3, 39.9, t)*(1 - smooth(44, 45, t));")
R("  const rn = smooth(26.5, 27.6, t);", "  const rn = smooth(41.8, 42.8, t);")
R("  finalMat.uniforms.uFlash.value = smooth(29.3, 30, t)*0.85;", "  finalMat.uniforms.uFlash.value = smooth(44.3, 45, t)*0.85;")
R("const trailAt = t => 0.25*smooth(4.5, 6.5, t) + 0.15*smooth(10.6, 11.6, t) - 0.25*smooth(13.6, 14.4, t) + 0.3*smooth(20, 22, t) - 0.45*smooth(26, 28, t);",
  "const trailAt = t => Math.max(0, (t >= 15 && t < 16.8 ? 0 : 1) * (0.12*smooth(10, 12, t) + 0.12*smooth(17, 18, t) + 0.08*smooth(27, 29, t) + 0.15*smooth(36, 38, t) - 0.5*smooth(43, 44.5, t)));")
s = re.sub(r"window\.dbg = t => \{.*?\};\n", "window.dbg = t => { setCamera(t); return {cam: camera.position.toArray().map(v=>+v.toFixed(1)), shot: shotAt(t)[2]}; };\n", s, flags=re.S)
open(P, 'w', encoding='utf-8').write(s)
print('ok')
