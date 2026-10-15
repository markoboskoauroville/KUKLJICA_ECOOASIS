#!/usr/bin/env python3
"""Build the data block for the Owner's Manual section of index.html.

Sources:
  .build/karta.html  the PARCELS block: official DGU geometry of k.o. Kukljica 334723 (7. 9. 2026),
                     which parcels are in the project, and the other parcels drawn for context.
  data/oss.json      the current possession sheets (posjedovni listovi, with shares and the area of
                     each sheet on each parcel) and the land-registry folios (z.k. ulošci), written
                     by tools/fetch_oss.py from oss.uredjenazemlja.hr.
  .secret/oss_detail.json (optional, never published) only to recognise a holder in the land
                     registry under a maiden name; the page gets the match, not the name.

Writes one line, `const OWN=...;`, between the OWNERS-DATA markers in index.html. Run from the
repo root after tools/fetch_oss.py:

    python3 tools/build_owners.py
"""
import json, re, pathlib, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
KARTA = ROOT / '.build' / 'karta.html'
OSS = ROOT / 'data' / 'oss.json'
DETAIL = ROOT / '.secret' / 'oss_detail.json'
INDEX = ROOT / 'index.html'

parcels = json.loads(re.search(r'^const PARCELS = (\[.*\]);\s*$', KARTA.read_text(encoding='utf-8'), re.M).group(1))
oss = json.loads(OSS.read_text(encoding='utf-8'))
detail = json.loads(DETAIL.read_text(encoding='utf-8')) if DETAIL.exists() else None

PROJECT = ('core', 'check', 'doc')
proj = [p for p in parcels if p['s'] in PROJECT]
muni = [p for p in parcels if p['s'] == 'opcina']
SPELL = {'Gobic': 'Gobić'}  # same family, spelled without the diacritic on one sheet
FIRST_NAME_FIRST = {'Antica Joja': 'Joja', 'Senija Ivanov': 'Ivanov'}  # written first name first on the sheet

def ring(p):
    return [[round(x, 6), round(y, 6)] for x, y in p['g'][0]]

def fam(name):
    if name in FIRST_NAME_FIRST:
        return FIRST_NAME_FIRST[name]
    s = name.split(' ')[0]
    return SPELL.get(s, s)

def key(name):
    """'Kajica Marija Pok. Mate' → 'kajica marija': surname and first name, no diacritics."""
    t = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    t = re.sub(r'[^a-z ]', ' ', t).split()
    t = ['kajica' if w in ('kaica', 'kajca') else w for w in t]
    return ' '.join(t[:2])

def frac(s):
    m = re.match(r'^\s*(\d+)\s*/\s*(\d+)\s*$', s or '')
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)

sheets, rows, zst = {}, [], {}
for p in proj:
    rec = oss['parcels'][p['id']]
    per = {}
    for part in rec['parts']:
        per[part['pl']] = per.get(part['pl'], 0) + part['m2']
    for sh in rec['sheets']:
        if sh['pl'] not in sheets:
            sheets[sh['pl']] = [[x['n'], *frac(x['share']), x.get('abroad', ''), fam(x['n'])] for x in sh['people']]
    use = max(rec['parts'], key=lambda x: x['m2'])['use'].lower() if rec['parts'] else ''
    # does the land registry name the same people as the cadastre?
    holders = set()
    for sh in rec['sheets']:
        for x in sh['people']:
            holders.add(key(x['n']))
    aliases = {}
    if detail:
        for sh in detail['parcels'][p['id']]['sheets']:
            for x in sh['people']:
                if x.get('born'):
                    aliases[key(x['n'])] = key(x['born'] + ' ' + x['n'].split(' ', 1)[-1])
    reg = {key(o['n']) for f in rec['folios'] for sh in oss['folios'][f]['shares'] for o in sh['owners']}
    hit = {h for h in holders if h in reg or aliases.get(h) in reg}
    st = 'match' if hit and hit == holders else ('part' if hit else 'diff')
    rows.append([p['id'], p['m2'], p['s'], [[pl, m] for pl, m in per.items()], ring(p), use, rec['folios'], st])

zk = {}
for u, f in oss['folios'].items():
    zk[u] = {'k': f['kind'].lower(), 'b': f['burdens'], 'pend': f['pending'],
             'o': [[o['n'] for o in sh['owners']] + [sh['share']] for sh in f['shares'] if sh['owners']]}

# municipal parcels: listed and drawn; area held by Općina Kukljica's sheet, other sheets, folio
mrows = []
for p in muni:
    rec = oss['parcels'][p['id']]
    opc = sum(x['m2'] for x in rec['parts'] if x['pl'] == '657')
    mrows.append([p['id'], p['m2'], opc, ring(p), rec['folios'], len({x['pl'] for x in rec['parts']}) - (1 if opc else 0)])

# context: other parcels of the cadastral municipality inside the map frame, no holder data
xs = [pt[0] for r in rows for pt in r[4]]; ys = [pt[1] for r in rows for pt in r[4]]
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
ctx = [[p['id'], p['m2'], ring(p)] for p in parcels
       if p['s'] == 'other' and any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in p['g'][0])]

y, m, d = oss['fetched'].split('-')
data = {'date': '7. 9. 2026.', 'pldate': f'{int(d)}. {int(m)}. {y}.', 'p': rows, 'pl': sheets, 'zk': zk, 'mun': mrows,
        'ctx': ctx, 'box': [x0, x1, y0, y1]}
line = 'const OWN=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';'

html = INDEX.read_text(encoding='utf-8')
new = re.sub(r'(/\* OWNERS-DATA:start[^\n]*\*/\n).*?\n(/\* OWNERS-DATA:end \*/)',
             lambda mm: mm.group(1) + line + '\n' + mm.group(2), html, flags=re.S)
if new == html and line not in html:
    raise SystemExit('OWNERS-DATA markers not found in index.html')
INDEX.write_text(new, encoding='utf-8')
from collections import Counter
print(f'{len(rows)} parcels, {len(sheets)} sheets, {len(zk)} folios, {len(mrows)} municipal, {len(ctx)} context, {len(line)//1024} KB')
print('registry status', Counter(r[7] for r in rows))
