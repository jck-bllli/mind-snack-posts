import re,html,glob,json,os
rows={}
for f in sorted(glob.glob('web/*.html')):
  cat=os.path.basename(f).rsplit('_',1)[0]
  s=open(f,encoding='utf-8',errors='replace').read()
  for a in re.findall(r'<article class="vendor">(.*?)</article>',s,re.S):
    n=re.search(r'callout-title"><a[^>]*>(.*?)</a>',a); ad=re.search(r'<address>(.*?)</address>',a,re.S); sm=re.search(r'class="summary">\s*<a[^>]*>(.*?)</a>',a,re.S)
    if not n: continue
    name=html.unescape(n.group(1)).strip(); addr=html.unescape(ad.group(1)).strip() if ad else ''
    rows.setdefault(name,dict(name=name,addr=addr,cat=cat,summary=html.unescape(re.sub(r'\s+',' ',sm.group(1))).strip()[:120] if sm else ''))
main=[r for r in rows.values() if re.search(r'\bMain\s*St|Long Wharf|Bay St',r['addr'],re.I)]
print(len(rows),'total;',len(main),'main/wharf/bay')
for r in sorted(main,key=lambda r:r['addr']): print(r['addr'],'|',r['name'],'|',r['cat'],'|',r['summary'][:60])
json.dump(list(rows.values()),open('web/chamber.json','w'),indent=0)
