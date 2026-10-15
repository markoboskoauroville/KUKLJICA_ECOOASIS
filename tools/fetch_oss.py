#!/usr/bin/env python3
"""Fetch the current cadastre and land-registry records of the project parcels from OSS
(oss.uredjenazemlja.hr, the state's public One Stop Shop), the same calls the ARKOD Layer app
makes (markoboskoauroville/arkod_web, public/js/core/parcels.js).

For each parcel of the Owner's manual:
  search-cad-parcels/parcel-numbers  → the OSS parcel id
  cad/parcel-info                    → possession sheets (posjedovni list) with shares, z.k. folios
  lr/lr-unit                         → the owner sheet (vlasnički list, sheet B) and burdens (sheet C)

Raw answers are kept in .secret/oss/ and the lawyer's detail (father's name, maiden name, place)
in .secret/oss_detail.json; .secret/ is git-ignored and never published. The published summary,
data/oss.json, keeps only names, shares, folio numbers and counts of burdens and pending changes. Run from the repo root, then tools/build_owners.py:

    python3 tools/fetch_oss.py
"""
import json, re, time, pathlib, urllib.parse, urllib.request, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / '.secret' / 'oss'
OUT = ROOT / 'data' / 'oss.json'
DETAIL = ROOT / '.secret' / 'oss_detail.json'
BASE = 'https://oss.uredjenazemlja.hr/oss/public'
KO = '334723'  # k.o. Kukljica
# a holder abroad is published by country only, as the 2014 sheets were
ABROAD = {'Australija': 'Australija', 'Tasmania': 'Australija', 'Sad': 'SAD', 'Njemačka': 'Njemačka'}

def get(url, name):
    f = RAW / name
    if f.exists():
        return json.loads(f.read_text(encoding='utf-8'))
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'kukljica-ecooasis/1'})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.loads(r.read().decode('utf-8'))
            f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
            time.sleep(0.6)
            return data
        except Exception as e:
            print('  retry', name, e); time.sleep(2 ** attempt * 2)
    raise SystemExit('failed: ' + url)

def plain(html):
    t = re.sub(r'<br\s*/?>', ' · ', str(html or ''), flags=re.I)
    t = re.sub(r'<[^>]+>', '', t).replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
    return re.sub(r'\s+', ' ', re.sub(r'(\s*·\s*)+', ' · ', t)).strip(' ·')

def place(addr):
    """Only the place, never the street: the last comma part, or the whole when it has no digit."""
    a = (addr or '').strip()
    if not a:
        return ''
    parts = [p.strip() for p in a.split(',') if p.strip()]
    tail = parts[-1] if parts else a
    tail = re.sub(r'\d', '', tail).strip(' .-')
    return tail.title()

def person(raw_name):
    """'MARTINOVIĆ ŠIMICA, DRAGUTIN, R. GOBIĆ' → name 'Martinović Šimica', father 'Dragutin', born 'Gobić'."""
    parts = [p.strip() for p in raw_name.split(',')]
    name = re.split(r'\s+(?:POK|UD|Ž|ROĐ)\.?\s', (parts[0] if parts else raw_name).upper() + ' ', maxsplit=1)[0].strip().title()
    born = next((p[2:].strip().title() for p in parts[1:] if p.upper().startswith('R.')), '')
    father = next((p.title() for p in parts[1:] if p and not p.upper().startswith('R.') and not re.search(r'\d|OIB', p.upper())), '')
    return name, father, born

MARK = re.compile(r'^(pok|ud|ž|žena|rođ|r|fu|gm|di|kći|sin|dr)\.?$', re.I)

def reg_name(raw):
    """A land-registry owner: 'Gobić Božo pok. Ante' → ('Gobić Božo', 'pok. Ante'); the rest stays private."""
    raw = re.sub(r'\s+', ' ', raw.replace('.', '. ')).strip()
    m = re.search(r'"\s*(.*?)\s*"\s*(.*)$', raw)
    if m:  # a foundation: 'Javna Dobrotvornost " Zaklada Soppe Fortezza" Zadar'
        return (m.group(1) + (', ' + m.group(2) if m.group(2) else '')).title(), ''
    if raw.upper().startswith(('REPUBLIKA', 'OPĆINA', 'GRAD ')):
        return raw.title(), ''
    w = raw.split(' ')  # surname and first name; whatever follows (patronymic, husband) stays private
    return ' '.join(w[:2]).title(), ' '.join(w[2:])

def parcel_numbers():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    own = json.loads(re.search(r'^const OWN=(\{.*\});$', html, re.M).group(1))
    return [p[0] for p in own['p']] + [m[0] for m in own['mun']]

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out = {'fetched': datetime.date.today().isoformat(), 'source': 'oss.uredjenazemlja.hr', 'parcels': {}, 'folios': {}}
    for num in parcel_numbers():
        safe = num.replace('/', '_')
        hits = get(f'{BASE}/search-cad-parcels/parcel-numbers?search={urllib.parse.quote(num)}&municipalityRegNum={KO}', f'search-{safe}.json')
        hit = next((h for h in hits if str(h.get('value1')) == num), None)
        if not hit:
            print('not found', num); out['parcels'][num] = None; continue
        rec = get(f'{BASE}/cad/parcel-info?parcelId={hit["key1"]}', f'parcel-{safe}.json')
        sheets = []
        for sh in rec.get('possessionSheets') or []:
            people = []
            for w in sh.get('possessors') or []:
                n, father, born = person(w.get('name', ''))
                people.append({'n': n, 'father': father, 'born': born, 'share': w.get('ownership') or '', 'place': place(w.get('address'))})
            sheets.append({'pl': sh.get('possessionSheetNumber'), 'people': people})
        parts = [{'use': p.get('name'), 'm2': int(p.get('area') or 0), 'pl': p.get('possessionSheetNumber')} for p in rec.get('parcelParts') or []]
        units = [{'unit': u.get('lrUnitNumber'), 'book': u.get('mainBookId'), 'kind': u.get('lrUnitTypeName')} for u in rec.get('lrUnitsFromParcelLinks') or []]
        out['parcels'][num] = {'m2': int(rec.get('area') or 0), 'place': (rec.get('address') or '').title(), 'parts': parts, 'sheets': sheets,
                               'folios': [u['unit'] for u in units]}
        for u in units:
            key = u['unit']
            if key in out['folios']:
                continue
            raw = get(f'{BASE}/lr/lr-unit?lrUnitNumber={urllib.parse.quote(key)}&mainBookId={u["book"]}&historicalOverview=false', f'folio-{key}.json')
            o = raw[0] if isinstance(raw, list) and raw else raw
            b = (o or {}).get('ownershipSheetB') or {}
            shares = []
            for sh in b.get('lrUnitShares') or []:
                owners = []
                for w in sh.get('lrOwners') or []:
                    n, rest = reg_name(w.get('name', '').strip())
                    owners.append({'n': n, 'rest': rest, 'place': place(w.get('address'))})
                title = plain(sh.get('description'))
                shares.append({'share': title.rsplit(':', 1)[-1].strip() if ':' in title else title, 'owners': owners})
            groups = ((o or {}).get('encumbranceSheetC') or {}).get('lrEntryGroups') or []
            a1 = ((o or {}).get('possessionSheetA1') or {}).get('lrParcels') or []
            out['folios'][key] = {'kind': u['kind'], 'office': (o or {}).get('institutionName', ''), 'shares': shares,
                                  'burdens': sum(len(g.get('lrEntries') or []) for g in groups),
                                  'pending': len((o or {}).get('activePlumbs') or []),
                                  'parcels': [str(p.get('parcelNumber')) for p in a1]}
        print(num, [s['pl'] for s in sheets], 'z.k.', [u['unit'] for u in units])
    DETAIL.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    pub = json.loads(json.dumps(out))
    for p in pub['parcels'].values():
        for sh in (p or {}).get('sheets', []):
            sh['people'] = [dict({'n': x['n'], 'share': x['share']}, **({'abroad': ABROAD[x['place']]} if x['place'] in ABROAD else {}))
                            for x in sh['people']]
    for fo in pub['folios'].values():
        for sh in fo['shares']:
            sh['owners'] = [{'n': x['n']} for x in sh['owners']]
    OUT.write_text(json.dumps(pub, ensure_ascii=False, indent=1), encoding='utf-8')
    print('wrote', OUT, 'and', DETAIL)

if __name__ == '__main__':
    main()
