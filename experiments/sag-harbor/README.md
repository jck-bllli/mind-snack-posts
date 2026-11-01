# Sag Harbor trip (real-place 3D walk)

Psychedelic first-person walk through Sag Harbor village, built from real map data.
Not tied to an account and not posted. Renders happen on the home PC; this folder only backs up the source.

## How it is built
1. **Map:** OpenStreetMap buildings, streets, wharf, piers and shoreline from the Overpass API
   (`osm.json`, processed to `sh_data.json`). Map data (c) OpenStreetMap contributors, ODbL.
2. **Aerial:** USGS NAIP summer imagery (public domain) as the ground texture and to place trees
   (`aerial.jpg`, bounds in `aerial_naip.json`). NYS 2023 ortho only to check alignment.
   Never Google or Bing imagery.
3. **Shops:** 55 real businesses from the Sag Harbor Chamber of Commerce directory, OSM and guides
   (`shops.json`, `shops.csv`). Plain-font name signs, no logos.
4. **Reference photos:** 90 Wikimedia Commons photos kept on the PC only, credits in `photo_credits.csv`.
   Reference only, never used as textures.
5. **Scene:** `scene_sh.html` (three.js, 540x960 internal, nearest upscale to 1080x1920),
   rendered frame by frame with `render.js` (Playwright Chromium on the GTX 1660 Ti).

## Versions
- v1: real layout, 4 frames. v2: 55 shops, Wharf Shop stop, Long Wharf swoop.
- v3 (current): Main St 13 m curb to curb, 3.5 m sidewalks, facades 20 m apart.

## Backup
Push to this branch (or run "Back up PC scene source") and the PC runner copies
`C:\runners\sag-harbor` source into `experiments/sag-harbor/source/`.
