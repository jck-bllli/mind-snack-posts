import json, re, csv
rows = json.load(open('web/chamber.json'))
CH = 'Sag Harbor Chamber of Commerce directory (sagharborchamber.com)'
shops = []
skip = re.compile(r'Southampton|riverhead|East Hampton|Bridgehampton|Hampton Bays', re.I)
OFFICE = {'GNFerraris LLC', 'Paul Alter Architecture PLLC', 'Hamptons Massage & Lymphatics', 'Chris Tice / Corcoran', 'Malloy Enterprises, Inc.', 'Fighting Chance', 'John Jermain Memorial Library'}
def typ(name, cat, summ):
    s = (name + ' ' + summ).lower()
    for k, ws in [('toys', 'toy|kite'), ('books', 'book'), ('food', 'bagel|coffee|caf|restaurant|bistro|sushi|taqueria|kitchen|market|deli|italian|cuisine|foods|hotel|dining|bilboquet'),
                  ('liquor', 'liquor|wine'), ('pharmacy', 'pharmacy|apothecary|hemp'), ('bank', 'bank|savings'), ('gallery', 'gallery|art'),
                  ('hardware', 'hardware'), ('florist', 'florist|flower'), ('pets', 'pet'), ('home', 'home|furnish|upholster'), ('variety', 'variety|5 & 10')]:
        if re.search(ws, s): return k
    return 'clothing' if cat in ('shop', 'services') else 'food'
for r in rows:
    a = r['addr']
    if skip.search(a) or r['name'] in OFFICE: continue
    m = re.match(r'\s*(\d+)\s*([A-Z]?)\s+(Main|Bay)\s', a, re.I)
    if m:
        num, street = int(m.group(1)), m.group(3).title() + ' St'
        if street == 'Main St' and num > 160: continue
        if street == 'Bay St' and num > 12: continue
        shops.append(dict(name=r['name'].replace('�', "'"), num=num, unit=m.group(2), street=street, type=typ(r['name'], r['cat'], r['summary']), source=CH, addr=a))
    elif re.search(r'Long Wharf', a, re.I):
        shops.append(dict(name=r['name'].replace('�', "'"), num=1, unit='', street='Long Wharf', type=typ(r['name'], r['cat'], r['summary']), source=CH, addr=a))
# from web listings / OSM (not in the chamber directory)
extra = [('Sag Harbor Cinema', 90, 'Main St', 'cinema', 'OpenStreetMap node + sagharborcinema.org'),
         ('Henry Lehr', 103, 'Main St', 'clothing', 'Modern Luxury, Aug 2025 (moved to 103 Main St)'),
         ('LoveShackFancy', 117, 'Main St', 'clothing', 'theshopkeepers.com Hamptons guide'),
         ('Matta', 82, 'Main St', 'clothing', 'theshopkeepers.com Hamptons guide'),
         ('TWP', 155, 'Main St', 'clothing', 'twpclothing.com store page'),
         ('Lifestyle', 127, 'Main St', 'clothing', 'OpenStreetMap node'),
         ('Grindstone Coffee & Donuts', 10, 'Main St', 'food', 'OpenStreetMap node (10A Main St)'),
         ('Sag Harbor Village Hall', 55, 'Main St', 'civic', 'OpenStreetMap')]
have = {s['name'] for s in shops}
for n, num, st, ty, src in extra:
    if n not in have: shops.append(dict(name=n, num=num, unit='', street=st, type=ty, source=src, addr=f'{num} {st}'))
FIX = {'Harbor Pets': 'pets', 'Sag Harbor Variety': 'variety', 'Southern Tide': 'clothing', 'Stella & Ruby': 'clothing', 'La Maisonette + Cannon Art': 'gallery', 'Land Shark Unlimited': 'clothing', 'Illusions': 'jewelry', 'Dragon Hemp/Menard': 'pharmacy', 'Sag Harbor Liquor Store': 'liquor'}
for s in shops:
    s['name'] = re.sub(r'[^ -~]', "'", s['name'])
    s['type'] = FIX.get(s['name'], s['type'])
for s in shops:
    s['side'] = ('east' if s['num'] % 2 else 'west') if s['street'] == 'Main St' else ('north' if s['street'] == 'Bay St' and s['num'] % 2 else 'south' if s['street'] == 'Bay St' else 'wharf')
shops.sort(key=lambda s: (s['street'], s['num'], s['name']))
json.dump(shops, open('shops.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
with open('shops.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['name', 'addr', 'street', 'num', 'unit', 'side', 'type', 'source']); w.writeheader()
    for s in shops: w.writerow({k: s[k] for k in w.fieldnames})
print(len(shops))
for s in shops: print(s['street'], s['num'], s['unit'], s['side'], s['type'], '|', s['name'])
