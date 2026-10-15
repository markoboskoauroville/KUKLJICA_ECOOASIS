#!/usr/bin/env python3
"""The private owners' report: everything the public page leaves out (addresses, fathers' and maiden
names, the land register's full entries, burdens and pending changes), for Marko and his lawyer only.

Reads index.html (OWN), .secret/oss_detail.json and the raw answers in .secret/oss/, and writes
.secret/owners-report.html; tools/private_report_pdf.mjs prints it to PDF. Everything it writes stays in
.secret/, which is git-ignored. Run after tools/fetch_oss.py and tools/build_owners.py:

    python3 tools/private_report.py && node tools/private_report_pdf.mjs
"""
import json, re, html, pathlib, datetime, sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEC = ROOT / '.secret'
RAW = SEC / 'oss'
sys.path.insert(0, str(ROOT / 'tools'))
import project

E = lambda s: html.escape(str(s if s is not None else ''))
N = lambda n: f'{round(n):,}'.replace(',', ' ')
own = json.loads(re.search(r'^const OWN=(\{.*\});$', (ROOT / 'index.html').read_text(encoding='utf-8'), re.M).group(1))
detail = json.loads((SEC / 'oss_detail.json').read_text(encoding='utf-8'))

def raw(kind, key):
    f = RAW / f'{kind}-{key.replace("/", "_")}.json'
    if not f.exists():
        return None
    o = json.loads(f.read_text(encoding='utf-8'))
    return o[0] if isinstance(o, list) and o else o

def plain(h):
    t = re.sub(r'<br\s*/?>', ' ', str(h or ''), flags=re.I)
    t = re.sub(r'<[^>]+>', ' ', t).replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
    return re.sub(r'\s+', ' ', t).strip()

ST = {'match': 'same people', 'part': 'some names match', 'diff': 'other people'}
STATUS = {'core': 'core', 'check': 'to verify', 'doc': 'listed', 'inside': 'inside the area, not on the list'}
FAM = [('Vojvodić', ['627', '409', '416', '410', '405', '406', '417', '418', '412']), ('Bačić', ['11']), ('Martinović / Boško', ['442']),
       ('Ninčević (r. Kajica)', ['587']), ('Kaica', ['149', '150']), ('Morović', ['351']), ('Gobić', ['106', '103', '104']), ('Bosotina', ['79', '70'])]

# ---------------- the model ----------------
P = [dict(zip(['id', 'm2', 's', 'h', 'g', 'use', 'zk', 'st'], r)) for r in own['p']]
total = sum(p['m2'] for p in P)
sheet_m2, sheet_parcels = defaultdict(int), defaultdict(list)
for p in P:
    for pl, m in p['h']:
        sheet_m2[pl] += m
        sheet_parcels[pl].append((p, m))

# people per sheet, with the private detail and the full address from the raw answer
people = {}
for p in P + [{'id': m[0]} for m in own['mun']]:
    r = raw('parcel', p['id'])
    d = detail['parcels'].get(p['id']) or {}
    for sh, dsh in zip((r or {}).get('possessionSheets') or [], d.get('sheets') or []):
        pl = str(sh['possessionSheetNumber'])
        if pl in people:
            continue
        people[pl] = [dict(x, address=(w.get('address') or '').strip(), raw=w.get('name', ''))
                      for w, x in zip(sh.get('possessors') or [], dsh['people'])]

folios = {}
for u in own['zk']:
    o = raw('folio', u) or {}
    b = o.get('ownershipSheetB') or {}
    shares = []
    for sh in b.get('lrUnitShares') or []:
        shares.append({'title': plain(sh.get('description')),
                       'owners': [{'name': w.get('name', ''), 'address': (w.get('address') or '').strip()} for w in sh.get('lrOwners') or []],
                       'entries': [plain(e.get('description')) for e in (sh.get('subSharesAndEntries') or []) if isinstance(e, dict)]})
    burdens = [plain(e.get('description')) for g in ((o.get('encumbranceSheetC') or {}).get('lrEntryGroups') or []) for e in g.get('lrEntries') or []]
    a1 = [(str(x.get('parcelNumber')), plain(x.get('address')), x.get('area') or (f"{x.get('areaInHvat')} čhv" if x.get('areaInHvat') else ''))
          for x in (o.get('possessionSheetA1') or {}).get('lrParcels') or []]
    folios[u] = {'kind': o.get('lrUnitTypeName', ''), 'office': o.get('institutionName', ''), 'last': o.get('lastDiaryNumber') or '',
                 'shares': shares, 'burdens': burdens, 'plombs': [x.get('fileNumber', '') for x in o.get('activePlumbs') or []], 'a1': a1}

def who_short(pl):
    return ' · '.join(f"{x['n']} {x['share']}" for x in people.get(pl, []))

def fam_of(pl):
    return next((n for n, pls in FAM if pl in pls), 'other')

# ---------------- statistics ----------------
sheets_sorted = sorted(sheet_m2, key=lambda pl: -sheet_m2[pl])
n_people = len({x['n'] for pl in sheet_m2 for x in people.get(pl, [])})
abroad = [(pl, x) for pl in sheet_m2 for x in people.get(pl, []) if x['place'] in ('Australija', 'Tasmania', 'Sad', 'Njemačka')]
st_count = {k: sum(1 for p in P if p['st'] == k) for k in ST}
inside = [p for p in P if p['s'] == 'inside']
sizes = sorted(p['m2'] for p in P)
median = (sizes[len(sizes) // 2] + sizes[(len(sizes) - 1) // 2]) / 2
per_person = defaultdict(float)
for pl in sheet_m2:
    for x in people.get(pl, []):
        m = re.match(r'(\d+)/(\d+)', x['share'] or '')
        per_person[x['n']] += sheet_m2[pl] * (int(m[1]) / int(m[2]) if m else 0)
fam_m2 = {n: sum(sheet_m2[pl] for pl in pls) for n, pls in FAM}
fam_m2['other'] = sum(m for pl, m in sheet_m2.items() if fam_of(pl) == 'other')

parcels_k = project.karta()
listed = [p for p in parcels_k if p['s'] in project.LISTED]
in_proj = {p['id'] for p in P}
edge = sorted(((round(project.enclosed_share(p, listed), 2), p['id'], p['m2']) for p in parcels_k
               if p['s'] == 'other' and p['id'] not in in_proj), reverse=True)
edge = [e for e in edge if e[0] >= 0.4]

# ---------------- the document ----------------
today = datetime.date.today()
out = []
w = out.append
w(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Kukljica EcoOasis · Owners · private</title>
<style>
@page{{size:A4;margin:16mm 14mm 18mm}}
body{{font-family:'IBM Plex Sans',Helvetica,Arial,sans-serif;font-size:9.4pt;color:#1a1f26;line-height:1.45}}
h1{{font-family:Georgia,serif;font-weight:400;font-size:24pt;margin:0 0 4mm}}
h2{{font-family:Georgia,serif;font-weight:400;font-size:15pt;margin:9mm 0 3mm;padding-top:2mm;border-top:1px solid #c9c1ab;page-break-after:avoid}}
h3{{font-size:10.5pt;margin:5mm 0 1.5mm;page-break-after:avoid}}
.conf{{font-family:monospace;font-size:8pt;letter-spacing:.14em;text-transform:uppercase;color:#a33;border:1px solid #a33;display:inline-block;padding:1.5mm 3mm;margin-bottom:6mm}}
.kpi{{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border:1px solid #c9c1ab;margin:4mm 0}}
.kpi div{{padding:3mm;border-right:1px solid #e3ddcf;border-bottom:1px solid #e3ddcf}}
.kpi b{{display:block;font-family:Georgia,serif;font-weight:400;font-size:15pt}}
.kpi span{{font-size:7.5pt;text-transform:uppercase;letter-spacing:.06em;color:#5c6672}}
table{{width:100%;border-collapse:collapse;margin:2mm 0 3mm;font-size:8.4pt}}
th{{text-align:left;font-weight:600;font-size:7.4pt;text-transform:uppercase;letter-spacing:.05em;color:#5f6e38;border-bottom:1px solid #a9a28c;padding:1.4mm 1.6mm}}
td{{border-bottom:1px solid #e6e1d4;padding:1.4mm 1.6mm;vertical-align:top}}
tr{{page-break-inside:avoid}}
td.r,th.r{{text-align:right;white-space:nowrap}}
.m{{color:#5c6672;font-size:7.8pt}}
.box{{border:1px solid #c9c1ab;padding:3mm 4mm;margin:3mm 0;page-break-inside:avoid}}
.st-diff{{color:#b4461f}} .st-part{{color:#2a62b0}} .st-match{{color:#13805a}}
.warn{{color:#a33;font-weight:600}}
img{{width:100%;border:1px solid #c9c1ab}}
ul{{margin:1mm 0 2mm 5mm;padding:0}} li{{margin:.8mm 0}}
.pb{{page-break-before:always}}
</style></head><body>
<div class="conf">Private · personal data · not for publication</div>
<h1>Kukljica EcoOasis<br>Owners of the project land</h1>
<p>Prepared for Marko Boško and his lawyer, {today.day}. {today.month}. {today.year}. Cadastre and land register read from
oss.uredjenazemlja.hr on {E(own["pldate"])}; parcel geometry DGU, k.o. Kukljica 334723. This file holds names, fathers' and maiden
names and addresses of private people as the state's public registers show them. It is a working file for the purchase: keep it
private and do not publish or forward it beyond the lawyer.</p>
<div class="kpi">
<div><b>{len(P)}</b><span>parcels in the project</span></div><div><b>{N(total)}</b><span>m², cadastral</span></div>
<div><b>{len(sheet_m2)}</b><span>possession sheets</span></div><div><b>{n_people}</b><span>named holders</span></div>
<div><b>{len(own["zk"])}</b><span>land-register folios</span></div><div><b>{st_count["match"]}</b><span>parcels: register = holders</span></div>
<div><b>{st_count["part"]}</b><span>parcels: some names match</span></div><div><b>{st_count["diff"]}</b><span>parcels: register names others</span></div>
</div>
''')

# key findings
big3 = sum(sheet_m2[pl] for pl in sheets_sorted[:3]) / total
plomb_f = [u for u, f in folios.items() if f['plombs']]
w('<h2>Key findings</h2><ul>')
w(f'<li><b>The land register is out of date almost everywhere.</b> On {st_count["diff"] + st_count["part"]} of {len(P)} parcels it names other people than the cadastre\'s holders, mostly an older generation; only {", ".join(p["id"] for p in P if p["st"] == "match")} matches. Before a holder can sell, their ownership will normally have to be registered first (inheritance, or a court or correction procedure).</li>')
w(f'<li><b>Largest holdings.</b> By sheet: {", ".join(f"PL {pl} ({N(sheet_m2[pl])} m²)" for pl in sheets_sorted[:3])}, together {big3:.0%} of the area. By family: '
  + ', '.join(f'{n} {N(m)} m²' for n, m in sorted(fam_m2.items(), key=lambda x: -x[1])[:4]) + '.</li>')
if plomb_f:
    w('<li class="warn">Pending changes (plomba) right now: ' + '; '.join(f'folio {u}: {", ".join(folios[u]["plombs"])} (parcels {", ".join(p["id"] for p in P if u in p["zk"])})' for u in plomb_f) + '. Ask the court what is being registered before negotiating these parcels.</li>')
w(f'<li><b>Folio 55</b> is registered to the Zaklada Soppe Fortezza, Zadar, and covers {sum(1 for p in P if "55" in p["zk"])} project parcels ({N(sum(p["m2"] for p in P if "55" in p["zk"]))} m²).</li>')
w(f'<li><b>Inside the area, not on the original list:</b> {len(inside)} parcels, {N(sum(p["m2"] for p in inside))} m²: {", ".join(p["id"] for p in inside)}. 2454/1 alone is {N(next(p["m2"] for p in inside if p["id"] == "2454/1"))} m².</li>')
w(f'<li><b>Holders abroad:</b> ' + '; '.join(f'{E(x["n"])} (PL {pl}, {E(x["address"])})' for pl, x in abroad) + '.</li>')
w('<li><b>Municipal land next to the project:</b> the cadastre says Općina Kukljica; the land register says Republic of Croatia for 2450 and 2445/7 (folio 1817) and three private people for 2445/13 (folio 1520).</li>')
w('</ul>')

# maps
w('<h2 class="pb">Maps</h2>')
for f, cap in (('map-family.png', 'By family. Striped parcels are shared; dotted edge: inside the area, not on the original list.'),
               ('map-register.png', 'By land register: green, the register names the holders; blue, some names match; orange, other people.')):
    w(f'<div style="page-break-inside:avoid"><h3>{cap}</h3><img src="{f}"></div>')  # captured by private_report_pdf.mjs before printing

# contacts by sheet
w('<h2 class="pb">Holders to contact, by possession sheet</h2><p class="m">Ordered by area. Shares are the cadastre\'s; m² per person is the sheet\'s area times the share. Father\'s name and maiden name (r.) as the cadastre writes them.</p>')
cum = 0
for i, pl in enumerate(sheets_sorted, 1):
    cum += sheet_m2[pl]
    w(f'<div class="box"><h3>{i}. PL {pl} · {N(sheet_m2[pl])} m² · {sheet_m2[pl] / total:.1%} (cumulative {cum / total:.0%}) · family: {E(fam_of(pl))}</h3>')
    w('<table><tr><th>Holder</th><th>Father</th><th>Maiden name</th><th class="r">Share</th><th class="r">≈ m²</th><th>Address</th></tr>')
    for x in people.get(pl, []):
        m = re.match(r'(\d+)/(\d+)', x['share'] or '')
        w(f'<tr><td><b>{E(x["n"])}</b></td><td>{E(x["father"])}</td><td>{E(x["born"])}</td><td class="r">{E(x["share"])}</td>'
          f'<td class="r">{N(sheet_m2[pl] * int(m[1]) / int(m[2])) if m else ""}</td><td>{E(x["address"])}</td></tr>')
    w('</table><table><tr><th>Parcel</th><th class="r">m² on this sheet</th><th>Use</th><th>Status</th><th>Folio</th><th>Land register names</th></tr>')
    for p, m in sorted(sheet_parcels[pl], key=lambda t: -t[1]):
        reg = '; '.join(', '.join(o['name'].title() for o in sh['owners']) + f' ({sh["title"].rsplit(":", 1)[-1].strip()})' for u in p['zk'] for sh in folios[u]['shares'] if sh['owners'])
        w(f'<tr><td>{p["id"]}</td><td class="r">{N(m)}</td><td>{E(p["use"])}</td><td>{E(STATUS[p["s"]])}</td><td>{", ".join(p["zk"])}</td>'
          f'<td><span class="st-{p["st"]}">{ST[p["st"]]}:</span> {E(reg[:400])}</td></tr>')
    w('</table></div>')

# land register by folio
w('<h2 class="pb">Land register, folio by folio</h2><p class="m">Owners exactly as entered (with "pok." = son/daughter of the late, "ud." = widow of, "ž." = wife of). Sheet C = burdens.</p>')
for u in sorted(folios, key=lambda u: -sum(p['m2'] for p in P if u in p['zk'])):
    f = folios[u]
    ps = [p for p in P if u in p['zk']]
    mun = [m[0] for m in own['mun'] if u in m[4]]
    w(f'<div class="box"><h3>Folio (z.k. uložak) {u} · {E(f["kind"].lower())} · {E(f["office"])}</h3>')
    w(f'<p class="m">Project parcels: {", ".join(p["id"] for p in ps) + (" · municipal: " + ", ".join(mun) if mun else "")} · '
      f'{N(sum(p["m2"] for p in ps))} m² · last entry {E(f["last"])}'
      + (f' · <span class="warn">pending: {E(", ".join(f["plombs"]))}</span>' if f['plombs'] else '') + '</p>')
    w('<table><tr><th>Share</th><th>Registered owner</th><th>Address</th></tr>')
    for sh in f['shares']:
        for j, o in enumerate(sh['owners'] or [{'name': '', 'address': ''}]):
            w(f'<tr><td>{E(sh["title"]) if j == 0 else ""}</td><td>{E(o["name"].title())}</td><td>{E(o["address"])}</td></tr>')
    w('</table>')
    holders = sorted({pl for p in ps for pl, _ in p['h']}, key=lambda pl: -sheet_m2[pl])
    w('<p><b>Cadastre holders of the same parcels:</b> ' + '; '.join(f'PL {pl}: {E(who_short(pl))}' for pl in holders) + '</p>')
    if f['burdens']:
        w('<p><b>Burdens (sheet C):</b></p><ul>' + ''.join(f'<li>{E(b)}</li>' for b in f['burdens']) + '</ul>')
    else:
        w('<p class="m">No burdens entered.</p>')
    others = [a for a in f['a1'] if a[0] not in in_proj]
    if others:
        w(f'<p class="m">Other parcels in this folio ({len(others)}): ' + ', '.join(E(a[0]) for a in others[:60]) + (' …' if len(others) > 60 else '') + '</p>')
    w('</div>')

# parcel register
w('<h2 class="pb">Parcel register</h2><table><tr><th>Parcel</th><th class="r">m²</th><th>Use</th><th>Status</th><th>Possession sheets (holders, shares, m²)</th><th>Folio</th><th>Register</th></tr>')
for p in sorted(P, key=lambda p: [int(x) for x in p['id'].split('/')] + [0]):
    hs = '<br>'.join(f'PL {pl} · {N(m)} m²: {E(who_short(pl))}' for pl, m in p['h'])
    w(f'<tr><td>{p["id"]}</td><td class="r">{N(p["m2"])}</td><td>{E(p["use"])}</td><td>{E(STATUS[p["s"]])}</td><td>{hs}</td><td>{", ".join(p["zk"])}</td><td class="st-{p["st"]}">{ST[p["st"]]}</td></tr>')
w('</table>')
w('<h3>Municipal parcels next to the project</h3><table><tr><th>Parcel</th><th class="r">m²</th><th>Possession sheets</th><th>Folio</th><th>Land register</th></tr>')
for pid, m2, opc, g, zk, more in own['mun']:
    d = detail['parcels'][pid]
    hs = '<br>'.join(f'PL {sh["pl"]}: ' + E(' · '.join(f'{x["n"]} {x["share"]}' for x in sh['people'])) for sh in d['sheets'])
    reg = '; '.join(', '.join(o['name'].title() for o in sh['owners']) for u in zk for sh in folios[u]['shares'] if sh['owners'])
    w(f'<tr><td>{pid}</td><td class="r">{N(m2)}</td><td>{hs}</td><td>{", ".join(zk)}</td><td>{E(reg)}</td></tr>')
w('</table>')

# statistics
w('<h2 class="pb">Statistics</h2><div class="kpi">'
  f'<div><b>{N(sizes[0])}</b><span>m², smallest parcel</span></div><div><b>{N(median)}</b><span>m², median</span></div>'
  f'<div><b>{N(total / len(P))}</b><span>m², average</span></div><div><b>{N(sizes[-1])}</b><span>m², largest</span></div></div>')
w('<h3>Parcels by size</h3><table><tr><th>Size</th><th class="r">Parcels</th><th class="r">m²</th><th class="r">Share</th></tr>')
for lo, hi, lab in ((0, 250, '< 250 m²'), (250, 500, '250–499 m²'), (500, 1000, '500–999 m²'), (1000, 2000, '1 000–1 999 m²'), (2000, 10**9, '≥ 2 000 m²')):
    ps = [p for p in P if lo <= p['m2'] < hi]
    w(f'<tr><td>{lab}</td><td class="r">{len(ps)}</td><td class="r">{N(sum(p["m2"] for p in ps))}</td><td class="r">{sum(p["m2"] for p in ps) / total:.0%}</td></tr>')
w('</table><h3>Parcels by number of possession sheets (sellers)</h3><table><tr><th>Sheets</th><th class="r">Parcels</th><th class="r">m²</th></tr>')
for k in sorted({len(p['h']) for p in P}):
    ps = [p for p in P if len(p['h']) == k]
    w(f'<tr><td>{k}</td><td class="r">{len(ps)}</td><td class="r">{N(sum(p["m2"] for p in ps))}</td></tr>')
w('</table><h3>By family</h3><table><tr><th>Family</th><th>Sheets</th><th class="r">m²</th><th class="r">Share</th></tr>')
for n, m in sorted(fam_m2.items(), key=lambda x: -x[1]):
    pls = dict(FAM).get(n) or [pl for pl in sheet_m2 if fam_of(pl) == 'other']
    w(f'<tr><td>{E(n)}</td><td>{", ".join("PL " + pl for pl in pls if pl in sheet_m2)}</td><td class="r">{N(m)}</td><td class="r">{m / total:.1%}</td></tr>')
w('</table><h3>By person (share × sheet area), top 20</h3><table><tr><th>Person</th><th class="r">≈ m²</th><th class="r">Share</th></tr>')
for n, m in sorted(per_person.items(), key=lambda x: -x[1])[:20]:
    w(f'<tr><td>{E(n)}</td><td class="r">{N(m)}</td><td class="r">{m / total:.1%}</td></tr>')
w('</table>')

# edges and next steps
w('<h2>Parcels at the edge, not counted</h2><p>These parcels share 40–60 % of their edge with the project. They are not in the counts above; decide whether the boundary should take them in (their holders were not read).</p>'
  '<table><tr><th>Parcel</th><th class="r">m²</th><th class="r">Edge shared</th></tr>'
  + ''.join(f'<tr><td>{pid}</td><td class="r">{N(m)}</td><td class="r">{s:.0%}</td></tr>' for s, pid, m in edge if s < project.ENCLOSED) + '</table>')
w('''<h2>For the lawyer: next steps</h2><ol>
<li>Certified land-register extracts for every folio above (e-Izvadak), and the cadastral possession sheets.</li>
<li>For each folio: the route to get the holders registered (completed or new inheritance proceedings, a court procedure, a correction procedure), and who among the heirs must sign.</li>
<li>The pending changes (plomba) first: what is being registered and by whom.</li>
<li>Folio 55, Zaklada Soppe Fortezza: its position on the parcels the Vojvodić, Kaica and Ninčević families hold.</li>
<li>Powers of attorney with apostille for holders abroad.</li>
<li>Municipal and state land: who can sell or lease 2450, 2445/7 and 2445/13.</li>
<li>Spatial plan, coastal zone, protection regime and any right of first refusal before contracts are signed.</li>
</ol><p class="m">Source: Republic of Croatia, State Geodetic Administration and Ministry of Justice, oss.uredjenazemlja.hr (cadastre and land register, public registers). A possession sheet is not proof of ownership; only the land register is.</p>
</body></html>''')
(SEC / 'owners-report.html').write_text('\n'.join(out), encoding='utf-8')
print('wrote', SEC / 'owners-report.html', f'{len(P)} parcels, {len(sheet_m2)} sheets, {len(folios)} folios')
