#!/usr/bin/env python3
"""Parse raw/*.html (Wayback snapshots) -> data/recipes.json + image list."""
import json, os, re, glob, urllib.parse, collections
from bs4 import BeautifulSoup

try:
    IMG_MAP = {('/images/' + k): ('/images/' + v)
               for k, v in json.load(open('data/img_map.json'))['resolved'].items()}
except FileNotFoundError:
    IMG_MAP = {}

DOMAIN_RE = re.compile(r'https?://(?:www\.)?recetasrosatovar\.com(?::80)?')

def clean_url(u):
    u = re.sub(r'^https?://web\.archive\.org/web/\d+(?:id_|im_)?/', '', u or '')
    return u

def local_img(u):
    u = clean_url(u)
    m = re.search(r'/wp-content/uploads/(.+)$', u)
    if not m:
        return u
    p = '/images/' + urllib.parse.unquote(m.group(1))
    return IMG_MAP.get(p, p)

recipes, images = [], set()

for path in sorted(glob.glob('raw/*.html')):
    slug = os.path.basename(path)[:-5]
    soup = BeautifulSoup(open(path, encoding='utf-8', errors='replace').read(), 'html.parser')
    bc = soup.select_one('#breadcrumb')
    if bc: bc.decompose()
    post = soup.select_one('#content div.post')
    if not post:
        print('skip (no .post):', slug); continue
    h1 = post.find('h1')
    title = h1.get_text(' ', strip=True) if h1 else slug

    meta = post.select_one('.meta')
    cats, date = [], None
    if meta:
        cats = [a.get_text(strip=True) for a in meta.find_all('a', rel='tag')]
        mt = re.search(r'el\s+(\d{1,2},\s*\w+,\s*\d{4})', meta.get_text(' ', strip=True))
        date = mt.group(1) if mt else None

    ing_box = post.select_one('.ingredients')
    ingredients = [t for li in (ing_box.select('li') if ing_box else []) if (t := li.get_text(' ', strip=True))]
    if ing_box:
        ing_box.decompose()
    for junk in post.select('.bookmarks_ingredients_wrapper, .meta, script, style, .wp-pagenavi, .sharedaddy'):
        junk.decompose()
    if h1: h1.decompose()

    entry = post.select_one('.entry') or post
    for img in entry.find_all('img'):
        src = clean_url(img.get('src'))
        if 'wp-content/uploads' in src:
            images.add(src)
            img['src'] = local_img(src)
        del img['srcset'], img['sizes']
    for a in entry.find_all('a'):
        href = clean_url(a.get('href'))
        if 'wp-content/uploads' in href:
            images.add(href); a['href'] = local_img(href)
        elif DOMAIN_RE.match(href):
            a['href'] = DOMAIN_RE.sub('', href) or '/'
        a.attrs.pop('rel', None)

    body = entry.decode_contents().strip()
    body = re.sub(r'(\s*<p>(&nbsp;|\s)*</p>\s*)+', '\n', body)
    text = entry.get_text(' ', strip=True)

    recipes.append({
        'slug': slug, 'title': title, 'categories': cats, 'date': date,
        'ingredients': ingredients, 'body_html': body,
        'excerpt': re.sub(r'\s+', ' ', text)[:220],
        'images': sorted({local_img(i) for i in images if local_img(i) in body}),
        'source': f'http://www.recetasrosatovar.com/recipes/{slug}/',
    })

os.makedirs('data', exist_ok=True)
json.dump(recipes, open('data/recipes.json', 'w'), ensure_ascii=False, indent=1)
open('data/images.txt', 'w').write('\n'.join(sorted(images)))
print(f'{len(recipes)} recipes, {len(images)} images')
print('no ingredients:', sum(1 for r in recipes if not r['ingredients']))
