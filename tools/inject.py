#!/usr/bin/env python3
"""inject.py — turns content/*.json into the JS data block and writes .build/index.html

Reads the template, replaces the /*__CONTENT__*/ marker with generated JavaScript,
and fails loudly if anything is missing rather than shipping a half-empty page.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIMPLE = ROOT / "content" / "simple"
EXTENDED = ROOT / "content" / "extended"
TEMPLATE = ROOT / "index.template.html"
KARTA_TEMPLATE = ROOT / "karta.template.html"
PARCELS = ROOT / "data" / "parcele.json"
OUT_DIR = ROOT / ".build"

# array name -> ordered columns, must match the render code in the template
SCHEMA = {
    "SPECIES": ["en", "hr", "status"],
    "TREES":   ["element_en", "element_hr", "name_en", "name_hr", "latin", "image", "text_en", "text_hr"],
    "WORK":    ["name_en", "name_hr", "text_en", "text_hr", "output_en", "output_hr"],
    "CAL":     ["month", "flower_en", "flower_hr", "bees_en", "bees_hr", "work_en", "work_hr"],
    "AREA":    ["name_en", "name_hr", "m2", "colour"],
    "VEG":     ["text_en", "text_hr", "time"],
    "GRAIN":   ["text_en", "text_hr", "time"],
    "OIL":     ["text_en", "text_hr", "time"],
    "SUGAR":   ["text_en", "text_hr", "time"],
    "PESTS":   ["name_en", "name_hr", "text_en", "text_hr"],
    "WATERL":  ["name_en", "name_hr", "text_en", "text_hr"],
    "FOODL":   ["name_en", "name_hr", "text_en", "text_hr"],
    "CRAFTL":  ["name_en", "name_hr", "text_en", "text_hr"],
    "TESTL":   ["name_en", "name_hr", "text_en", "text_hr"],
    "LIVEL":   ["name_en", "name_hr", "text_en", "text_hr"],
    "JOINL":   ["name_en", "name_hr", "text_en", "text_hr"],
    "CVFACTS": ["name_en", "name_hr", "text_en", "text_hr"],
    "PHASES":  ["name_en", "name_hr", "text_en", "text_hr", "current"],
    "INF":     ["name_en", "name_hr", "text_en", "text_hr", "url"],
}


def die(msg):
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        die(f"missing content file {path.relative_to(ROOT)}")
    except json.JSONDecodeError as e:
        die(f"{path.relative_to(ROOT)} is not valid JSON, line {e.lineno}: {e.msg}")


def build_dictionary():
    """Merge every content/simple/*.json into the en and hr dictionaries."""
    en, hr, seen = {}, {}, {}
    files = sorted(SIMPLE.glob("*.json"))
    if not files:
        die("content/simple holds no files")
    for f in files:
        data = load(f)
        for row in data.get("fields", []):
            k = (row.get("key") or "").strip()
            if not k:
                die(f"{f.name} has a field with no key")
            if k in seen:
                die(f"key {k} appears in both {seen[k]} and {f.name}")
            seen[k] = f.name
            en[k] = row.get("en", "")
            hr[k] = row.get("hr", "") or row.get("en", "")
    return en, hr, len(files)


def build_arrays():
    """Turn every content/extended/*.json into the positional arrays the page renders from."""
    out = {}
    for name, cols in SCHEMA.items():
        f = EXTENDED / f"{name.lower()}.json"
        data = load(f)
        items = data.get("items", [])
        if not items:
            die(f"{f.name} holds no items")
        rows = []
        for i, it in enumerate(items, 1):
            row = []
            for c in cols:
                v = it.get(c, "")
                if c == "current":
                    v = 1 if v else 0
                elif c in ("m2", "month"):
                    try:
                        v = int(v)
                    except (TypeError, ValueError):
                        die(f"{f.name} item {i}: {c} must be a number, got {v!r}")
                row.append(v)
            rows.append(row)
        out[name] = rows
    return out


def build_karta(en, hr):
    """The field map page: karta.* texts plus the parcel geometry, no other dependencies."""
    if not KARTA_TEMPLATE.exists():
        die("karta.template.html not found")
    html = KARTA_TEMPLATE.read_text(encoding="utf-8")
    import re
    used = set(re.findall(r'data-i18n="([^"]+)"', html))
    bad = sorted(k for k in used if not k.startswith("karta."))
    if bad:
        die(f"karta.template.html uses keys outside karta.*: {bad}")
    missing = sorted(used - set(en))
    if missing:
        die(f"keys used in karta markup but absent from content: {missing}")
    t = {"en": {k: v for k, v in en.items() if k.startswith("karta.")},
         "hr": {k: v for k, v in hr.items() if k.startswith("karta.")}}
    if len(t["en"]) < 30:
        die("content/simple/karta.json looks empty")
    parcels = load(PARCELS)
    core = [x for x in parcels if x.get("s") == "core"]
    if len(core) != 4:
        die(f"data/parcele.json must hold exactly four core parcels, found {len(core)}")
    for x in parcels:
        if not x.get("g") or not x.get("id"):
            die(f"data/parcele.json: parcel without geometry or id: {x.get('id')!r}")
    block = ("/* generated by tools/inject.py — edit content/simple/karta.json and data/parcele.json, never this */\n"
             "const T = " + json.dumps(t, ensure_ascii=False) + ";\n"
             "const PARCELS = " + json.dumps(parcels, ensure_ascii=False, separators=(",", ":")) + ";\n")
    if "/*__KARTA__*/" not in html:
        die("karta template has no /*__KARTA__*/ marker")
    html = html.replace("/*__KARTA__*/", block, 1)
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "karta.html").write_text(html, encoding="utf-8")
    print(f"karta: {len(t['en'])} texts, {len(parcels)} parcels ({len(core)} core)")


def main():
    if not TEMPLATE.exists():
        die("index.template.html not found")

    en, hr, n_files = build_dictionary()
    arrays = build_arrays()

    # every key used in the markup must exist in both languages
    html = TEMPLATE.read_text(encoding="utf-8")
    import re
    used = set(re.findall(r'data-i18n="([^"]+)"', html))
    missing_en = sorted(used - set(en))
    missing_hr = sorted(used - set(hr))
    if missing_en or missing_hr:
        die(f"keys used in markup but absent from content — EN {missing_en} HR {missing_hr}")

    parts = ["/* generated by tools/inject.py — edit content/, never this */",
             "const T = " + json.dumps({"en": en, "hr": hr}, ensure_ascii=False) + ";"]
    for name, rows in arrays.items():
        parts.append(f"const {name} = " + json.dumps(rows, ensure_ascii=False) + ";")
    block = "\n".join(parts) + "\n"

    if "/*__CONTENT__*/" not in html:
        die("template has no /*__CONTENT__*/ marker")
    html = html.replace("/*__CONTENT__*/", block, 1)

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")

    build_karta(en, hr)

    unused = sorted(set(en) - used - {k for k in en if k.startswith("karta.")})
    print(f"injected {len(en)} texts from {n_files} files, "
          f"{len(arrays)} lists, {sum(len(r) for r in arrays.values())} rows")
    if unused:
        print(f"note: {len(unused)} texts are defined but not used in the markup")


if __name__ == "__main__":
    main()
