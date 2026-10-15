"""Which parcels the Owner's manual covers. Shared by fetch_oss.py and build_owners.py.

The project is every parcel of the field map (.build/karta.html) marked core, check or doc, plus the
parcels inside the area that were never on the list: a parcel whose edge runs along project parcels
for at least ENCLOSED of its length. 2454/1 (3 377 m², 15.10.2026) is the one that showed the gap.
"""
import json, math, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LISTED = ('core', 'check', 'doc')
ENCLOSED = 0.6   # share of the edge that touches project parcels
NEAR_M = 1.5     # metres: closer than this counts as touching
KX = math.cos(math.radians(44.036))

def karta():
    src = (ROOT / '.build' / 'karta.html').read_text(encoding='utf-8')
    return json.loads(re.search(r'^const PARCELS = (\[.*\]);\s*$', src, re.M).group(1))

def _edges(r):
    return list(zip(r, r[1:] + r[:1]))

def _dist(px, py, a, b):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy or 1e-18
    u = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot((px - ax - u * dx) * KX * 111320, (py - ay - u * dy) * 111320)

def _points(r, step=2.0):
    out = []
    for (ax, ay), (bx, by) in _edges(r):
        n = max(1, int(math.hypot((bx - ax) * KX * 111320, (by - ay) * 111320) / step))
        out += [(ax + (bx - ax) * i / n, ay + (by - ay) * i / n) for i in range(n)]
    return out

def enclosed_share(p, listed):
    edges = [e for q in listed for e in _edges(q['g'][0])]
    pts = _points(p['g'][0])
    return sum(1 for x, y in pts if min(_dist(x, y, a, b) for a, b in edges) < NEAR_M) / len(pts)

def project(parcels=None):
    """[(parcel, status)] in field-map order; status is the field map's, or 'inside'."""
    parcels = parcels or karta()
    listed = [p for p in parcels if p['s'] in LISTED]
    out = []
    for p in parcels:
        if p['s'] in LISTED:
            out.append((p, p['s']))
        elif p['s'] == 'other' and enclosed_share(p, listed) >= ENCLOSED:
            out.append((p, 'inside'))
    return out
