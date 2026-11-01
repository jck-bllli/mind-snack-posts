      if (sh.name === 'The American Hotel') {
        // front porch: deck, slim columns, roof with a balustrade, rockers, a hanging flag (no shared-rnd use)
        const wm = new THREE.MeshLambertMaterial({color: '#f4efe4'});
        const pf = new THREE.Mesh(new THREE.BoxGeometry(wd + 0.2, 0.35, 2.8), wm); pf.position.set(0, 0.18, 1.4); g.add(pf);
        const pr = new THREE.Mesh(new THREE.BoxGeometry(wd + 0.4, 0.3, 3.0), wm); pr.position.set(0, 3.5, 1.4); pr.castShadow = true; g.add(pr);
        for (let x = -wd/2 + 0.3; x <= wd/2 - 0.2; x += (wd - 0.5)/5) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.14, 3.2, 8), wm); c.position.set(x, 1.95, 2.7); c.castShadow = true; g.add(c); }
        for (let x = -wd/2 + 0.2; x <= wd/2; x += 0.35) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.55, 0.07), wm); b.position.set(x, 3.95, 2.8); g.add(b); }
        const rail = new THREE.Mesh(new THREE.BoxGeometry(wd + 0.3, 0.08, 0.1), wm); rail.position.set(0, 4.25, 2.8); g.add(rail);
        for (const x of [-wd/4, wd/4]) { const ch = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.9, 0.6), new THREE.MeshLambertMaterial({color: '#2f4a3a'})); ch.position.set(x, 0.8, 1.8); g.add(ch); }
        const fp = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 2.6, 4), wm); fp.position.set(0, 5.6, 0.9); fp.rotation.x = 0.7; g.add(fp);
        const hf = new THREE.Mesh(new THREE.PlaneGeometry(1.8, 1.1), new THREE.MeshLambertMaterial({map: flagTex, side: THREE.DoubleSide})); hf.position.set(0.9, 6.3, 1.7); hf.rotation.x = 0.7; g.add(hf);
      }
