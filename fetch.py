#!/usr/bin/env python3
"""Download best Wayback snapshot of each recipe page into raw/."""
import json, os, time, urllib.request, urllib.error, sys

BEST = json.load(open('data/targets.json'))
os.makedirs('raw', exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (archive-recovery; personal site restore)'}

items = sorted(BEST.items())
for i, (slug, (url, ts)) in enumerate(items, 1):
    out = f'raw/{slug}.html'
    if os.path.exists(out) and os.path.getsize(out) > 2000:
        continue
    wb = f'https://web.archive.org/web/{ts}id_/{url}'
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(wb, headers=UA), timeout=90) as r:
                data = r.read()
            open(out, 'wb').write(data)
            print(f'[{i}/{len(items)}] {slug} {len(data)}B', flush=True)
            break
        except Exception as e:
            print(f'  retry {attempt} {slug}: {e}', flush=True)
            time.sleep(5 * (attempt + 1))
    else:
        print(f'FAIL {slug}', flush=True)
    time.sleep(1.0)
