P = 'scene_sh.html'
s = open(P, encoding='utf-8').read()
def R(a, b):
    global s
    assert a in s, 'MISSING: ' + a[:90]
    s = s.replace(a, b, 1)
# OSM maps the windmill itself as building 679365502: skip its plain extrusion (keeps rnd use) and put the model there
R("function tri(b, a, c, d, ua, uc, ud, bc, hint) {", "let SKIPB = false;\nfunction tri(b, a, c, d, ua, uc, ud, bc, hint) {\n  if (SKIPB) return;")
R("  const dMain = distToLines(cx, cz, mainSt);", "  SKIPB = B.id === 679365502;\n  const dMain = distToLines(cx, cz, mainSt);")
R("console.log('buildings', nBuild);", "SKIPB = false;\nconsole.log('buildings', nBuild);")
R("windmill = new THREE.Group(); windmill.position.set(-30, 0.3, -42);", "windmill = new THREE.Group(); windmill.position.set(-24, 0.3, -41);")
R("windmill.rotation.y = Math.atan2(8 - -30, -50 - -42); // sails face the wharf", "windmill.rotation.y = Math.atan2(8 - -24, -50 - -41); // sails face the wharf")
# keep the church view clear of aerial trees
R("&& !(jz < 20 && jx > -75 && jx < 45)) spots.push([jx, jz, R(6, 13)]);", "&& !(jz < 20 && jx > -75 && jx < 45) && !inChurchView(jx, jz)) spots.push([jx, jz, R(6, 13)]);")
R("// ---------- trees from the aerial", """function inChurchView(x, z) {
  const {ob} = special.church, sg = (ob.uz < 0) ? 1 : -1;
  const tx = ob.cx + ob.ux*sg*(ob.ha - 3), tz = ob.cz + ob.uz*sg*(ob.ha - 3), nx = ob.ux*sg, nz = ob.uz*sg;
  const a = (x - tx)*nx + (z - tz)*nz, l = Math.abs(-(x - tx)*nz + (z - tz)*nx);
  return a > 2 && a < 50 && l < 12;
}
// ---------- trees from the aerial""")
# remove the old dark backing box from the cinema move (it z-fought the new white front)
R("    const back = new THREE.Mesh(new THREE.BoxGeometry(marquee.fw, special.cinema.wallH, 2), new THREE.MeshLambertMaterial({color: '#2a2228'})); back.position.set(0, special.cinema.wallH/2, -1); marquee.grp.add(back);\n", "")
# named shops that fell inside the cinema + neighbours slot slide just outside it
R("        const z = zForNum(sh.num, sh.side) + (gi - (group.length-1)/2) * 7.5 * (sh.side === 'east' ? 1 : 1);",
  "        let z = zForNum(sh.num, sh.side) + (gi - (group.length-1)/2) * 7.5 * (sh.side === 'east' ? 1 : 1);\n        if (sh.side === 'west' && Math.abs(z - cinemaPOI[1]) < 19) z = cinemaPOI[1] + (z < cinemaPOI[1] ? -19.5 : 19.5);")
# no parked cars in front of the American Hotel
R("  const wz = WSHOP.z;", "  const wz = WSHOP.z, hz = (shopGroups.find(r => r.shop.name === 'The American Hotel') || {z: -999}).z;")
R("&& !(s > 0 && f.z > 270)) cars.push(", "&& !(s > 0 && f.z > 270) && !(Math.abs(f.z - hz) < 12)) cars.push(")
# framing
R("  [0, 5, 'whaling museum', u => ({ pos: streetPt(lerp(552, 546, u), 6.0, 1.65), look: new THREE.Vector3(MUS.x, 5.5, MUS.z).lerp(streetPt(500, 0, 3), 0.15), fov: 64 })],",
  "  [0, 5, 'whaling museum', u => ({ pos: streetPt(lerp(MUS.z + 4, MUS.z - 2, u), 6.5, 1.65), look: new THREE.Vector3(MUS.x, 6.0, MUS.z), fov: 66 })],")
R("  [31.5, 36, 'long wharf + harbor', u => ({ pos: new THREE.Vector3(lerp(126, 112, u), lerp(46, 40, u), lerp(-470, -440, u)), look: new THREE.Vector3(lerp(112, 100, u), 0, -20), fov: 66 })],",
  "  [31.5, 36, 'long wharf + harbor', u => ({ pos: new THREE.Vector3(lerp(66, 56, u), lerp(40, 36, u), lerp(-440, -420, u)), look: new THREE.Vector3(lerp(60, 55, u), 0, lerp(-40, -30, u)), fov: 72 })],")
open(P, 'w', encoding='utf-8').write(s)
print('ok')
