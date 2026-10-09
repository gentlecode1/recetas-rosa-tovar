#!/usr/bin/env python3
"""Generate the static site into site/ from data/recipes.json."""
import json, os, re, shutil, html, unicodedata, collections, urllib.parse
from bs4 import BeautifulSoup

OUT = 'site'
PUB = 'downloads'
SITE_NAME = 'La cocina de Rosa Tovar'
TAGLINE = 'Recetas, cursos y libros de cocina — archivo restaurado'

MESES = {'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04', 'May': '05', 'Jun': '06',
         'Jul': '07', 'Ago': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dic': '12'}


def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-')


def iso(d):
    m = re.match(r'(\d{1,2}),\s*(\w+),\s*(\d{4})', d or '')
    return f'{m.group(3)}-{MESES.get(m.group(2)[:3].title(), "01")}-{int(m.group(1)):02d}' if m else ''


def nice_title(t):
    t = t.strip(' *')
    # quita numeraciones de serie ("2.- ", "1. ", "3) ") pero respeta ordinales ("7ª PARTE")
    t = re.sub(r'^\d+\s*[.)\-–]+\s*(?![ªº])', '', t)
    t = t.lstrip(' .–-—·*')
    return t.strip() or 'Receta'


def clean_body(body):
    soup = BeautifulSoup(body, 'html.parser')
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src.startswith('/images/') and not os.path.exists(PUB + src):
            a = img.find_parent('a')
            (a or img).decompose()
    for a in soup.find_all('a'):
        if a.get('href', '').startswith('/images/') and not os.path.exists(PUB + a['href']):
            a.unwrap()
    for t in soup.find_all(['script', 'style', 'iframe']):
        t.decompose()
    out = str(soup)
    return re.sub(r'(\s*<p>(?:&nbsp;|\s)*</p>\s*)+', '\n', out).strip()


def first_image(body):
    m = re.search(r'<img[^>]+src="((?:\.\./)?/?images/[^"]+)"', body)
    if not m:
        return None
    return '/' + m.group(1).lstrip('./').lstrip('/').replace('images/', 'images/', 1) if not m.group(1).startswith('/') else m.group(1)


CSS = """
:root{--ink:#2b2320;--muted:#7a6a60;--bg:#fbf7f1;--card:#fff;--accent:#9c3b26;--line:#e7ded2}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.65 Georgia,'Iowan Old Style',serif}
a{color:var(--accent)}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px}
header.top{background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}
header.top .wrap{display:flex;align-items:center;gap:24px;padding-top:14px;padding-bottom:14px;flex-wrap:wrap}
.brand{font-size:21px;font-weight:700;text-decoration:none;color:var(--ink);letter-spacing:.3px}
.brand small{display:block;font-size:11px;font-weight:400;color:var(--muted);letter-spacing:.14em;text-transform:uppercase}
nav a{margin-right:18px;text-decoration:none;color:var(--muted);font-size:14px;letter-spacing:.06em;text-transform:uppercase}
nav a:hover,nav a.on{color:var(--accent)}
.hero{padding:54px 0 30px;text-align:center}
.hero h1{font-size:40px;margin:0 0 8px}
.hero p{color:var(--muted);margin:0 auto;max-width:620px}
input[type=search]{width:100%;max-width:520px;padding:13px 16px;border:1px solid var(--line);border-radius:30px;background:var(--card);font:16px Georgia,serif;margin-top:22px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:22px;margin:30px 0 60px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;text-decoration:none;color:inherit;display:flex;flex-direction:column;transition:.15s}
.card:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.08)}
.card .ph{aspect-ratio:4/3;background:#f0e9df center/cover no-repeat;display:flex;align-items:center;justify-content:center;color:#c9bbab;font-size:34px}
.card .ph{flex:0 0 auto}
.card h3{margin:0;padding:14px 16px 6px;font-size:17px;line-height:1.3;flex:0 0 auto}
.card p{margin:0;padding:0 16px 14px;color:var(--muted);font-size:13px;flex:1 1 auto}
.tags{padding:0 16px 14px;display:flex;gap:6px;flex-wrap:wrap;align-items:flex-start;align-content:flex-start;flex:0 0 auto;margin-top:auto}
.tag{display:inline-block;align-self:flex-start;font-size:11px;line-height:1.5;background:#f3ece2;color:var(--muted);padding:3px 9px;border-radius:20px;text-decoration:none;white-space:nowrap}
article.recipe{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:38px 44px;margin:30px 0 60px}
article.recipe h1{font-size:34px;margin:0 0 6px;line-height:1.2}
.meta{color:var(--muted);font-size:14px;margin-bottom:26px}
.meta a{color:var(--muted)}
.ingredients{background:#faf5ed;border:1px solid var(--line);border-radius:10px;padding:20px 26px;margin:0 0 28px}
.ingredients h2{font-size:15px;text-transform:uppercase;letter-spacing:.12em;color:var(--accent);margin:0 0 12px}
.ingredients ul{margin:0;padding-left:20px}
.ingredients li{margin:5px 0}
.body img{max-width:100%;height:auto;border-radius:8px;display:block;margin:20px auto}
.body p{margin:0 0 16px}
.src{font-size:13px;color:var(--muted);border-top:1px solid var(--line);padding-top:16px;margin-top:30px}
footer{border-top:1px solid var(--line);padding:30px 0 50px;color:var(--muted);font-size:13px;text-align:center}
.catlist{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0 40px;justify-content:center;align-items:flex-start;align-content:flex-start}
.catlist a{display:inline-block;align-self:flex-start;background:var(--card);border:1px solid var(--line);padding:8px 16px;border-radius:30px;text-decoration:none;font-size:14px;line-height:1.5;white-space:nowrap}
.count{color:var(--muted);font-size:13px}
.card .ph span{font:600 40px Georgia,serif;color:#cdbfae}
.card.partial .ph{background:repeating-linear-gradient(45deg,#f5efe6,#f5efe6 10px,#f1e9dd 10px,#f1e9dd 20px)}
.tag.warn{background:#f6e3d8;color:#a4552f}
.notice{background:#fdf3e7;border:1px solid #e8d3bd;border-left:4px solid #c08552;border-radius:8px;padding:16px 20px;margin:0 0 26px;font-size:15px;color:#6b513a}
.notice b{color:#a4552f}
.excerpt-partial{font-size:19px;line-height:1.7}
.excerpt-partial .cut{color:var(--muted);font-style:italic}
.filters{display:flex;gap:14px;justify-content:center;margin-top:14px;font-size:14px;color:var(--muted)}
.filters label{cursor:pointer}
.pend{list-style:none;margin:0 0 60px;padding:0}
.pend li{background:var(--card);border:1px solid var(--line);border-left:4px solid #d9b08c;border-radius:8px;margin-bottom:10px;padding:14px 18px}
.pend a{font-weight:700;text-decoration:none;font-size:17px}
.pend .c{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;margin-left:8px}
.pend .x{display:block;color:var(--muted);font-size:14px;margin-top:5px}
.letter{font-size:13px;letter-spacing:.2em;color:var(--accent);margin:26px 0 10px;text-transform:uppercase}
@media(max-width:600px){article.recipe{padding:24px 20px}.hero h1{font-size:30px}}
"""


def rewrite_links(body, known, depth=1):
    """Pasa rutas absolutas a relativas y reapunta los enlaces internos a las páginas nuevas."""
    up = '../' * depth
    soup = BeautifulSoup(body, 'html.parser')
    for img in soup.find_all('img'):
        if img.get('src', '').startswith('/images/'):
            img['src'] = up + img['src'][1:]
    for a in soup.find_all('a', href=True):
        h = a['href']
        if h.startswith('/images/'):
            a['href'] = up + h[1:]
            continue
        m = re.match(r'^/recipes/([^/?#]+)/?$', h)
        if m:
            slug = urllib.parse.unquote(m.group(1))
            if slug in known:
                a['href'] = f'{up}recetas/{slug}.html'
            else:                      # receta que no sobrevivió: deja el texto sin enlace
                a.unwrap()
        elif h.startswith('/'):
            a.unwrap()
    return str(soup)


def page(title, body, active='', depth=0):
    r = '../' * depth or './'
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{r}style.css">
</head><body>
<header class="top"><div class="wrap">
<a class="brand" href="{r}index.html">{SITE_NAME}<small>recetas · cursos · libros</small></a>
<nav>
<a href="{r}index.html" class="{'on' if active=='home' else ''}">Inicio</a>
<a href="{r}recetas/index.html" class="{'on' if active=='recetas' else ''}">Recetas</a>
<a href="{r}categorias/index.html" class="{'on' if active=='cat' else ''}">Categorías</a>
<a href="{r}pendientes.html" class="{'on' if active=='pend' else ''}">Pendientes</a>
</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap">Archivo restaurado de recetasrosatovar.com · contenido © Rosa Tovar</div></footer>
</body></html>"""


def card(r, depth):
    root = '../' * depth
    img = r['img']
    if img:
        ph = f'<div class="ph" style="background-image:url({root.rstrip("/") or "."}{img})"></div>'
    else:
        ph = f'<div class="ph"><span>{html.escape(r["title"][:1].upper() or "R")}</span></div>'
    tags = ''.join(f'<span class="tag">{html.escape(c)}</span>' for c in r['categories'][:3])
    flag = '<span class="tag warn">incompleta</span>' if r.get('incomplete') else ''
    return (f'<a class="card{" partial" if r.get("incomplete") else ""}" href="{root}recetas/{r["slug"]}.html">{ph}'
            f'<h3>{html.escape(r["title"])}</h3><p>{html.escape(r["excerpt"][:110])}…</p>'
            f'<div class="tags">{tags}{flag}</div></a>')


def main():
    raw = json.load(open('data/recipes.json'))
    recipes = []
    for x in raw:
        body = clean_body(x['body_html'])
        if len(re.sub(r'<[^>]+>', '', body).strip()) < 40 and not x['ingredients']:
            continue
        recipes.append({**x, 'title': nice_title(x['title']), 'body': body,
                        'iso': iso(x['date']), 'img': first_image(body)})
    recipes.sort(key=lambda r: (r['iso'] or '0000'), reverse=True)

    # --- recetas perdidas: ficha incompleta a partir de los índices archivados ---
    stubs = []
    try:
        meta = json.load(open('data/missing_meta.json'))
    except FileNotFoundError:
        meta = {}
    try:
        stub_imgs = json.load(open('data/missing_imgs.json'))
    except FileNotFoundError:
        stub_imgs = {}
    for slug, v in meta.items():
        exc = re.sub(r'\s*\.\.\.\s*Leer más.*$', '', v['excerpt']).strip()
        stubs.append({'slug': slug, 'title': nice_title(v['title']), 'categories': v['cats'],
                      'date': None, 'iso': '', 'ingredients': [], 'body': '', 'excerpt': exc,
                      'img': stub_imgs.get(slug), 'incomplete': True,
                      'source': f'http://www.recetasrosatovar.com/recipes/{slug}/'})
    stubs.sort(key=lambda r: r['title'])
    allr = recipes + stubs
    known = {r['slug'] for r in allr}
    for r in recipes:
        r['body'] = rewrite_links(r['body'], known, 1)
        r['img'] = first_image(r['body'])

    os.makedirs(f'{OUT}/recetas', exist_ok=True)
    os.makedirs(f'{OUT}/categorias', exist_ok=True)
    open(f'{OUT}/style.css', 'w').write(CSS)
    if os.path.isdir(f'{PUB}/images'):
        if os.path.islink(f'{OUT}/images') or os.path.exists(f'{OUT}/images'):
            shutil.rmtree(f'{OUT}/images', ignore_errors=True)
        shutil.copytree(f'{PUB}/images', f'{OUT}/images')

    cats = collections.defaultdict(list)
    for r in allr:
        for c in r['categories']:
            cats[c].append(r)

    # fichas incompletas
    for r in stubs:
        tags = ' · '.join(f'<a href="../categorias/{slugify(c)}.html">{html.escape(c)}</a>'
                          for c in r['categories'])
        body = (f'<article class="recipe"><h1>{html.escape(r["title"])}</h1>'
                f'<div class="meta">{tags}</div>'
                '<div class="notice"><b>Receta pendiente de recuperar.</b> El sitio original dejó de '
                'funcionar y esta página nunca llegó a guardarse en Internet Archive. Esto es todo lo que '
                'se conserva de ella, rescatado de los listados archivados.</div>'
                f'<div class="body excerpt-partial"><p>{html.escape(r["excerpt"])}'
                f'<span class="cut"> […el texto se corta aquí]</span></p></div>'
                f'<div class="src">URL original: <a href="{r["source"]}">{r["source"]}</a></div></article>')
        open(f'{OUT}/recetas/{r["slug"]}.html', 'w').write(
            page(f'{r["title"]} (incompleta) · {SITE_NAME}', body, 'recetas', 1))

    # recipe pages
    for r in recipes:
        ing = ''
        if r['ingredients']:
            ing = ('<div class="ingredients"><h2>Ingredientes</h2><ul>' +
                   ''.join(f'<li>{html.escape(i)}</li>' for i in r['ingredients']) + '</ul></div>')
        tags = ' · '.join(f'<a href="../categorias/{slugify(c)}.html">{html.escape(c)}</a>'
                          for c in r['categories'])
        body = (f'<article class="recipe"><h1>{html.escape(r["title"])}</h1>'
                f'<div class="meta">{tags}{" — " + r["date"] if r["date"] else ""}</div>'
                f'{ing}<div class="body">{r["body"]}</div>'
                f'<div class="src">Recuperado del archivo de <a href="{r["source"]}">{r["source"]}</a></div></article>')
        open(f'{OUT}/recetas/{r["slug"]}.html', 'w').write(page(f'{r["title"]} · {SITE_NAME}', body, 'recetas', 1))

    # recipe index (client-side search)
    index = [{'t': r['title'], 'u': r['slug'], 'c': r['categories'],
              'i': r['img'] or '', 'e': r['excerpt'][:110], 'p': bool(r.get('incomplete'))} for r in allr]
    json.dump(index, open(f'{OUT}/recetas/index.json', 'w'), ensure_ascii=False)
    listing = ''.join(card(r, 1) for r in allr)
    body = (f'<div class="hero"><h1>Todas las recetas</h1>'
            f'<p class="count">{len(recipes)} recetas completas · '
            f'{len(stubs)} pendientes de recuperar</p>'
            f'<input type="search" id="q" placeholder="Buscar receta o ingrediente…" autofocus>'
            f'<div class="filters"><label><input type="checkbox" id="onlyfull"> Ver solo las completas</label>'
            f'<a href="../pendientes.html">Ver las {len(stubs)} pendientes →</a></div></div>'
            f'<div class="grid" id="grid">{listing}</div>'
            """<script>
const q=document.getElementById('q'),g=document.getElementById('grid'),f=document.getElementById('onlyfull');
const cards=[...g.children];
const norm=s=>s.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');
const keys=cards.map(c=>norm(c.textContent));
function run(){const s=norm(q.value).trim(),only=f.checked;
cards.forEach((c,i)=>{const ok=(!s||keys[i].includes(s))&&(!only||!c.classList.contains('partial'));
c.style.display=ok?'':'none';});}
q.addEventListener('input',run);f.addEventListener('change',run);
</script>""")
    open(f'{OUT}/recetas/index.html', 'w').write(page(f'Recetas · {SITE_NAME}', body, 'recetas', 1))

    # category pages
    for c, rs in cats.items():
        n_full = sum(1 for r in rs if not r.get('incomplete'))
        extra = f' · {len(rs) - n_full} pendientes' if len(rs) > n_full else ''
        body = (f'<div class="hero"><h1>{html.escape(c)}</h1>'
                f'<p class="count">{n_full} recetas{extra}</p></div>'
                f'<div class="grid">{"".join(card(r, 1) for r in rs)}</div>')
        open(f'{OUT}/categorias/{slugify(c)}.html', 'w').write(page(f'{c} · {SITE_NAME}', body, 'cat', 1))
    links = ''.join(f'<a href="{slugify(c)}.html">{html.escape(c)} <span class="count">({len(rs)})</span></a>'
                    for c, rs in sorted(cats.items(), key=lambda kv: -len(kv[1])))
    open(f'{OUT}/categorias/index.html', 'w').write(page(
        f'Categorías · {SITE_NAME}',
        f'<div class="hero"><h1>Categorías</h1></div><div class="catlist">{links}</div>', 'cat', 1))

    # página de pendientes
    items, letter = [], None
    for r in stubs:
        L = r['title'][:1].upper()
        L = L if L.isalpha() else '#'
        if L != letter:
            letter = L
            items.append(f'</ul><div class="letter">{html.escape(L)}</div><ul class="pend">')
        catspan = ('<span class="c">' + html.escape(' · '.join(r['categories'])) + '</span>') if r['categories'] else ''
        items.append(f'<li><a href="recetas/{r["slug"]}.html">{html.escape(r["title"])}</a>{catspan}'
                     f'<span class="x">{html.escape(r["excerpt"][:150])}…</span></li>')
    body = (f'<div class="hero"><h1>Recetas pendientes</h1>'
            f'<p>{len(stubs)} recetas que existieron en el sitio original pero cuya página nunca llegó '
            f'a guardarse en Internet Archive. De cada una se conserva el título, las categorías y un '
            f'fragmento del texto.</p>'
            f'<p class="count">{len(recipes)} completas · {len(stubs)} pendientes</p></div>'
            f'<ul class="pend">{"".join(items)}</ul>')
    open(f'{OUT}/pendientes.html', 'w').write(page(f'Recetas pendientes · {SITE_NAME}', body, 'pend', 0))

    # home
    feat = [r for r in recipes if r['img']][:12]
    top = sorted(cats.items(), key=lambda kv: -len(kv[1]))[:12]
    toplinks = ''.join(f'<a href="categorias/{slugify(c)}.html">{html.escape(c)}</a>' for c, _ in top)
    body = (f'<div class="hero"><h1>{SITE_NAME}</h1><p>{TAGLINE}</p>'
            f'<p class="count">{len(recipes)} recetas · {len(cats)} categorías · '
            f'<a href="pendientes.html">{len(stubs)} pendientes de recuperar</a></p></div>'
            f'<div class="catlist">{toplinks}</div>'
            f'<div class="grid">{"".join(card(r, 0) for r in feat)}</div>')
    open(f'{OUT}/index.html', 'w').write(page(SITE_NAME, body, 'home', 0))
    print(f'generated {len(recipes)} recipes + {len(stubs)} stubs, {len(cats)} categories -> {OUT}/')


if __name__ == '__main__':
    main()
