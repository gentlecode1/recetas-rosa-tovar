#!/usr/bin/env python3
"""Extract title/excerpt/cats/thumb of recipes that have no archived page, from the archived listings."""
import re, glob, json, os, urllib.parse
from bs4 import BeautifulSoup

ours = {f[:-5] for f in os.listdir('raw')}
BOILER = re.compile(r'\s*(?:\.{2,}|…)?\s*(?:Leer\s+M\W{0,3}s|Leer\s+m\W{0,3}s|Ver\s+Receta|Read\s+More)\s*(?:[→>»\-]+)?\s*$', re.I)


def read(path):
    raw = open(path, 'rb').read()
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:3000], re.I)
    enc = (m.group(1).decode() if m else 'utf-8')
    try:
        return raw.decode(enc)
    except (UnicodeDecodeError, LookupError):
        return raw.decode('utf-8', 'replace')


def tidy(t):
    t = re.sub(r'\s+', ' ', t).strip()
    for _ in range(3):
        t = BOILER.sub('', t).strip()
    return t.rstrip('.· ').strip()


info = {}
for f in glob.glob('raw_idx/*.html'):
    soup = BeautifulSoup(read(f), 'html.parser')
    content = soup.select_one('#content') or soup
    for a in content.find_all('a', href=re.compile(r'/recipes/[^/?#]+/?$')):
        slug = urllib.parse.unquote(a['href'].rstrip('/').split('/')[-1])
        if slug in ours or slug == 'page':
            continue
        box = a.find_parent('div', class_=['thumbnail', 'content']) or a.parent
        wrap = box.parent
        cur = info.setdefault(slug, {'title': '', 'excerpt': '', 'img': None, 'cats': []})
        img = wrap.find('img')
        if img and img.get('src') and not cur['img']:
            cur['img'] = img['src']
        cont = wrap.find('div', class_='content') or wrap
        h = cont.find(re.compile('^h[1-4]$'))
        t = tidy(h.get_text(' ', strip=True)) if h else tidy(a.get_text(' ', strip=True))
        if len(t) > len(cur['title']):
            cur['title'] = t
        ent = cont.find('div', class_='entry')
        if ent:
            e = tidy(ent.get_text(' ', strip=True))
            if len(e) > len(cur['excerpt']):
                cur['excerpt'] = e
        mt = cont.find('div', class_='meta')
        if mt:
            cur['cats'] = sorted(set(cur['cats']) | {x.get_text(strip=True) for x in mt.find_all('a', rel='tag')})

json.dump(info, open('data/missing_meta.json', 'w'), ensure_ascii=False, indent=1)
bad = [k for k, v in info.items() if '\ufffd' in v['title'] + v['excerpt']]
print(f'{len(info)} recetas perdidas · {sum(1 for v in info.values() if len(v["excerpt"]) > 30)} con extracto '
      f'· {sum(1 for v in info.values() if v["img"])} con miniatura · {len(bad)} con caracteres rotos')
