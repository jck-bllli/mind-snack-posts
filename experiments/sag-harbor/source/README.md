# Sag Harbor real-town render

Stylized low-poly 3D Sag Harbor built from real map data, rendered on the home PC (GTX 1660 Ti) with three.js + Playwright.
Reusable as the template for any real-place render: swap the bbox, re-run the data steps, keep the scene engine.

## Pipeline
1. **Map data** - `q.txt` is the Overpass query (buildings, highways, coastline, piers, POIs) for the bbox.
   Fetch with Python (Git Bash curl fails TLS to overpass-api.de) -> `osm.json`.
   `python -I tools/prep.py osm.json sh_data.json` converts to local meters (x east, z south, origin = Main St / Bay St).
2. **Aerial** - USGS NAIP ImageServer `exportImage` (public domain) -> `aerial.jpg`, bounds in `aerial_naip.json`.
   NYS orthos (orthos.its.ny.gov wms/2023) in `aerial/` for checking only. Never Google/Bing.
3. **Reference photos** - `python -I tools/commons.py photos` pulls Wikimedia Commons with license + author -> `photos/credits.csv`. Reference only.
4. **Shops** - Chamber of Commerce directory pages in `web/`, `tools/chamber.py` parses them, `tools/shops.py` -> `shops.json` / `shops.csv` (name, address, side, type, source).
5. **Scene** - `scene_sh.html`: OSM buildings extruded (merged per material, breathing vertex hook), land from the coastline, aerial ground,
   roads, Long Wharf, piers, instanced boats, trees placed from aerial green pixels, one facade per real shop on a 13 m Main St street wall,
   cars, lamps, benches, planters, pedestrians, cinema marquee, windmill, tie-dye whale, color rain, post (trails, tie-dye grade, dither).
   `window.renderAt(t)` returns a 540x960 PNG. `?overhead&noaerial&ov=x0,z0,x1,z1` gives a top-down map for checking against the aerial.
6. **Render** - `NT_SCENE=scene_sh.html node render.js <outDir> <fps> <secs> [frameList]` then ffmpeg nearest-upscale to 1080x1920.
   Reel spec: libx264 veryfast crf 20 yuv420p, AAC 128k 48 kHz, +faststart. Outputs to `C:\runners\outbox` for sync.

## Music
`tools/score.py` writes an original 30 s jam-band style score (Karplus-Strong guitar, organ, walking bass, shuffle drums, wobble/phaser that follow the trip).
Run with the local venv: `.venv/Scripts/python.exe -I tools/score.py score.wav` (create with `python -m venv .venv` + `pip install numpy`).
Full video: render 900 frames to `full30/`, then ffmpeg upscale + `volume=1.85dB,alimiter=limit=0.8:level=false,loudnorm=I=-14:TP=-1.5:LRA=11`.

## Versions
- `scene_sh_v1.html` first pass (window-grid facades, steeple shot)
- `scene_sh_v2.html` 55 real shops, Wharf Shop stop, Long Wharf swoop
- `scene_sh.html` current (v3): narrowed Main St, continuous street wall
- Stills: `stills/`, `stills_v2/`, `stills_v3/`

## Rules
Original art only (no logos, no Grateful Dead imagery). Shop names in plain fonts. Do not post anything without Jack's go.
