import json, math, sys
src, dst = sys.argv[1], sys.argv[2]
E = json.load(open(src, encoding='utf-8'))['elements']
ways = [e for e in E if e['type'] == 'way']
def nodes_of(name): 
    s = set()
    for w in ways:
        if w.get('tags', {}).get('name') == name and 'highway' in w['tags']: s |= set(w['nodes'])
    return s
pos = {}
for w in ways:
    for nid, g in zip(w['nodes'], w['geometry']): pos[nid] = (g['lat'], g['lon'])
shared = nodes_of('Main Street') & nodes_of('Bay Street')
print('Main/Bay shared nodes', [(n, pos[n]) for n in shared])
LAT0, LON0 = pos[sorted(shared)[0]] if shared else (41.0010, -72.2955)
KX = 111320 * math.cos(math.radians(LAT0)); KY = 110950
xy = lambda g: [round((g['lon'] - LON0) * KX, 2), round(-(g['lat'] - LAT0) * KY, 2)]  # x east, z south
out = dict(origin=[LAT0, LON0], kx=KX, ky=KY, bbox=[40.9940, -72.2990, 41.0040, -72.2880], buildings=[], roads=[], coast=[], piers=[], areas=[], pois=[])
for e in E:
    t = e.get('tags', {})
    if e['type'] == 'way' and 'building' in t:
        out['buildings'].append(dict(id=e['id'], p=[xy(g) for g in e['geometry']], k=t['building'], lv=t.get('building:levels'), h=t.get('height'), roof=t.get('roof:shape'), n=t.get('name'), am=t.get('amenity'), st=t.get('addr:street')))
    elif e['type'] == 'relation' and 'building' in t:
        for m in e.get('members', []):
            if m.get('role') == 'outer' and 'geometry' in m:
                out['buildings'].append(dict(id=e['id'], p=[xy(g) for g in m['geometry']], k=t['building'], lv=t.get('building:levels'), n=t.get('name')))
    elif e['type'] == 'way' and 'highway' in t:
        out['roads'].append(dict(id=e['id'], p=[xy(g) for g in e['geometry']], k=t['highway'], n=t.get('name'), br=t.get('bridge')))
    elif e['type'] == 'way' and t.get('natural') == 'coastline':
        out['coast'].append([xy(g) for g in e['geometry']])
    elif e['type'] == 'way' and t.get('man_made') in ('pier', 'breakwater', 'groyne', 'bridge'):
        out['piers'].append(dict(p=[xy(g) for g in e['geometry']], k=t['man_made'], n=t.get('name'), area=t.get('area')))
    elif e['type'] == 'way' and ('leisure' in t or 'natural' in t or 'landuse' in t or 'amenity' in t):
        out['areas'].append(dict(p=[xy(g) for g in e['geometry']], k=t.get('leisure') or t.get('natural') or t.get('landuse') or t.get('amenity'), n=t.get('name')))
    elif e['type'] == 'node' and 'name' in t:
        out['pois'].append(dict(p=xy(e), n=t['name'], k=t.get('amenity') or t.get('shop') or t.get('tourism') or ''))
json.dump(out, open(dst, 'w', encoding='utf-8'), separators=(',', ':'))
print({k: len(v) for k, v in out.items() if isinstance(v, list)})
print('piers', [(p['k'], p['n'], len(p['p'])) for p in out['piers']])
print('cinema', [p for p in out['pois'] if 'Cinema' in p['n']])
for b in out['buildings']:
    if b['n']: print(b['n'], b['p'][0])
