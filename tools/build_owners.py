#!/usr/bin/env python3
"""Build the data block for the Owner's Manual section of index.html.

Source: the PARCELS block of .build/karta.html (official DGU geometry of
k.o. Kukljica 334723, data date 7. 9. 2026, with holders from the posjedovni
listovi dated 11. 6. 2014). Writes one line, `const OWN=...;`, between the
OWNERS-DATA markers in index.html. Run from the repo root:

    python3 tools/build_owners.py
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
KARTA = ROOT / '.build' / 'karta.html'
INDEX = ROOT / 'index.html'

src = KARTA.read_text(encoding='utf-8')
m = re.search(r'^const PARCELS = (\[.*\]);\s*$', src, re.M)
parcels = json.loads(m.group(1))

PROJECT = ('core', 'check', 'doc')
proj = [p for p in parcels if p['s'] in PROJECT]
muni = [p for p in parcels if p['s'] == 'opcina']

# Holders of the core parcels are known only from the parcel list (no sheet
# attached, no shares). Keep them as one sheet each, shares unknown.
CORE_SHEETS = {
    'PL 442': ('442', [('Martinović Šimica', None, None, ''), ('Boško Ivana', None, None, '')]),
    'PL 70 / 79': ('70/79', [('Bosotina Ante', None, None, 'PL 70'), ('Bosotina Šime', None, None, 'PL 79')]),
}
SPELL = {'Gobic': 'Gobić'}  # same family, spelled without the diacritic on one sheet

sheets = {}

def parse_who(who):
    out = []
    for part in who.split(' · '):
        mm = re.match(r'^(.*?) \((\d+)/(\d+)(?:, (.*))?\)$', part.strip())
        name, num, den, note = mm.group(1), int(mm.group(2)), int(mm.group(3)), mm.group(4) or ''
        if ', ' in name:  # "Vojvodić Božo, SAD"
            name, abroad = name.split(', ', 1)
            note = (abroad + (', ' + note if note else '')).strip()
        out.append((name, num, den, note))
    return out

rows = []
for p in proj:
    hs = []
    if 'h' in p:
        for h in p['h']:
            sheets.setdefault(h['pl'], parse_who(h['who']))
            hs.append([h['pl'], h['m2']])
    else:
        pl, persons = CORE_SHEETS[p['n']]
        sheets.setdefault(pl, persons)
        hs.append([pl, p['m2']])
    rows.append([p['id'], p['m2'], p['s'], hs, [[round(x, 6), round(y, 6)] for x, y in p['g'][0]]])

def fam(name):
    s = name.split(' ')[0]
    return SPELL.get(s, s)

out_sheets = {pl: [[n, a, b, note, fam(n)] for n, a, b, note in ps] for pl, ps in sheets.items()}

# municipal parcels: listed, and drawn on the map
mrows = [[p['id'], p['m2'], sum(h['m2'] for h in p.get('h', [])), [[round(x, 6), round(y, 6)] for x, y in p['g'][0]]] for p in muni]

# context: other parcels of the cadastral municipality inside the map frame, no holder data
xs = [pt[0] for r in rows for pt in r[4]]; ys = [pt[1] for r in rows for pt in r[4]]
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
ctx = []
for p in parcels:
    if p['s'] != 'other':
        continue
    ring = p['g'][0]
    if any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in ring):
        ctx.append([p['id'], p['m2'], [[round(x, 6), round(y, 6)] for x, y in ring]])

data = {'date': '7. 9. 2026.', 'pldate': '11. 6. 2014.', 'p': rows, 'pl': out_sheets, 'mun': mrows, 'ctx': ctx,
        'box': [x0, x1, y0, y1]}
line = 'const OWN=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';'

html = INDEX.read_text(encoding='utf-8')
new = re.sub(r'(/\* OWNERS-DATA:start[^\n]*\*/\n).*?\n(/\* OWNERS-DATA:end \*/)',
             lambda mm: mm.group(1) + line + '\n' + mm.group(2), html, flags=re.S)
if new == html and line not in html:
    raise SystemExit('OWNERS-DATA markers not found in index.html')
INDEX.write_text(new, encoding='utf-8')
print(f'{len(rows)} parcels, {len(out_sheets)} sheets, {len(mrows)} municipal, {len(ctx)} context, {len(line)//1024} KB')
