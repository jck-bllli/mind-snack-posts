import json, urllib.request, urllib.parse, csv, os, re, sys, time, html
OUT = sys.argv[1]; MAX = 90
UA = {'User-Agent': 'SagHarborArtRef/1.0 (personal reference collection; jackbelloli0 contact via github jck-bllli)'}
API = 'https://commons.wikimedia.org/w/api.php'
def get(params):
    params.update(format='json')
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(API + '?' + urllib.parse.urlencode(params), headers=UA), timeout=60))
        except Exception as e:
            print('retry', e); time.sleep(2 ** i)
    return {}
def members(cat, kind):
    out, cont = [], {}
    while True:
        d = get(dict(action='query', list='categorymembers', cmtitle=cat, cmtype=kind, cmlimit=500, **cont))
        out += [m['title'] for m in d.get('query', {}).get('categorymembers', [])]
        if 'continue' not in d: return out
        cont = {'cmcontinue': d['continue']['cmcontinue']}
# crawl categories, prioritising the downtown subjects
root = 'Category:Sag Harbor, New York'
want = re.compile(r'Main Street|Cinema|Whalers|Presbyterian|Windmill|Long Wharf|Bay Street|harbor|Harbor|Sag Harbor|boat|Custom House|American Hotel|Whaling Museum|Library|Firem', re.I)
skip = re.compile(r'maps|people|births|deaths|logos|audio|documents|newspapers|postcards|stamps', re.I)
seen, queue, cats = set(), [(root, 0)], []
while queue:
    c, dep = queue.pop(0)
    if c in seen: continue
    seen.add(c); cats.append(c)
    if dep < 3:
        for s in members(c, 'subcat'):
            if not skip.search(s) and (dep == 0 or want.search(s)): queue.append((s, dep + 1))
print('categories', len(cats)); [print(' ', c) for c in cats]
files = []
for c in cats:
    for f in members(c, 'file'):
        if f not in files and re.search(r'\.(jpe?g|png)$', f, re.I): files.append(f)
print('files', len(files))
pri = lambda f: (0 if re.search(r'Main|Cinema|Whaler|Presbyter|Windmill|Wharf|Bay St|harbor|boat|marina|Custom|American Hotel|street', f, re.I) else 1)
files.sort(key=pri)
rows, n = [], 0
for i in range(0, len(files), 40):
    if n >= MAX: break
    d = get(dict(action='query', titles='|'.join(files[i:i+40]), prop='imageinfo', iiprop='url|extmetadata|size', iiurlwidth=1280))
    for p in d.get('query', {}).get('pages', {}).values():
        if n >= MAX: break
        ii = (p.get('imageinfo') or [{}])[0]; md = ii.get('extmetadata', {})
        lic = md.get('LicenseShortName', {}).get('value', '?')
        if not re.search(r'CC0|Public domain|PD|CC BY', lic, re.I): print('skip license', lic, p['title']); continue
        artist = re.sub('<[^>]+>', '', html.unescape(md.get('Artist', {}).get('value', '?'))).strip()
        url = ii.get('thumburl') or ii.get('url')
        name = re.sub(r'[^\w.\-]+', '_', p['title'][5:])[:90]
        dst = os.path.join(OUT, name)
        if not os.path.exists(dst):
            try:
                open(dst, 'wb').write(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read())
            except Exception as e: print('dl fail', e); continue
            time.sleep(0.4)
        n += 1
        rows.append(dict(file=name, title=p['title'], license=lic, author=artist, source='https://commons.wikimedia.org/wiki/' + urllib.parse.quote(p['title'].replace(' ', '_')), license_url=md.get('LicenseUrl', {}).get('value', '')))
with open(os.path.join(OUT, 'credits.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print('downloaded', n)
