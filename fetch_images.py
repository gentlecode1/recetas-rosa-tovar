#!/usr/bin/env python3
"""Fetch archived uploads. Falls back to any archived size-variant of the same base image."""
import json, re, os, time, collections, urllib.parse, urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (archive-recovery)'}
ROOT = 'downloads/images'
cdx = {}
for u, t, s in json.load(open('data/cdx_img.json'))[1:]:
    k = urllib.parse.unquote(re.search(r'/wp-content/uploads/(.+)$', u).group(1))
    cdx[k] = (u, t)

size = lambda k: (lambda m: int(m.group(1)) * int(m.group(2)) if m else 10 ** 7)(re.search(r'-(\d+)x(\d+)\.\w+$', k))
base = lambda k: re.sub(r'-\d+x\d+(\.\w+)$', r'\1', k).lower()
bybase = collections.defaultdict(list)
for k in cdx:
    bybase[base(k)].append(k)

want = [urllib.parse.unquote(re.search(r'/wp-content/uploads/(.+)$', l.strip()).group(1))
        for l in open('data/images.txt') if l.strip()]
resolved, missing = {}, []
for w in want:
    cands = bybase.get(base(w), [])
    if not cands:
        missing.append(w); continue
    resolved[w] = max(cands, key=size)   # best available quality

print(f'{len(resolved)} resolvable, {len(missing)} missing')
json.dump({'resolved': resolved, 'missing': sorted(set(missing))},
          open('data/img_map.json', 'w'), ensure_ascii=False, indent=1)

todo = sorted(set(resolved.values()))
for i, k in enumerate(todo, 1):
    out = os.path.join(ROOT, k)
    if os.path.exists(out) and os.path.getsize(out) > 500:
        continue
    os.makedirs(os.path.dirname(out), exist_ok=True)
    u, ts = cdx[k]
    wb = f'https://web.archive.org/web/{ts}id_/' + urllib.parse.quote(urllib.parse.unquote(u), safe=':/?&=')
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(wb, headers=UA), timeout=90) as r:
                open(out, 'wb').write(r.read())
            print(f'[{i}/{len(todo)}] {k}', flush=True); break
        except Exception as e:
            print('  retry', a, k, e, flush=True); time.sleep(4 * (a + 1))
    else:
        print('FAIL', k, flush=True)
    time.sleep(0.5)
