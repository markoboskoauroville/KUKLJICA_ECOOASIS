# KUKLJICA ECOOASIS — HANDOFF

**Paste this whole file into a new chat to continue. Nothing else needs explaining.**
Last updated 6.9.2026.

---

## 0. WHERE EVERYTHING IS

| | |
|---|---|
| Live site | https://kukljica-ecooasis.pages.dev |
| Preview (CMS branch) | https://cms.kukljica-ecooasis.pages.dev |
| Admin panel | https://cms.kukljica-ecooasis.pages.dev/admin |
| CV site | https://markobosko.pages.dev |
| Repo | `markoboskoauroville/KUKLJICA_ECOOASIS` — **PRIVATE** |
| CV repo | `markoboskoauroville/markoboskocv` — **PRIVATE** |
| OAuth worker | https://kukljica-cms-auth.marko-bosko-925.workers.dev |
| Manifest module | `MANTRA_MANIFEST/modules/editable-site.md` |
| OAuth card (Croatian) | `MANTRA_MANIFEST/contact/github-oauth-podsjetnik.md` |

**Read `MANTRA_MANIFEST/START_HERE.md` first.** Then `modules/editable-site.md`,
`apis/cloudflare.md`, `modules/secrets.md`.

---

## 1. THE PROJECT IN ONE PARAGRAPH

Seven hectares on the island of Ugljan, village Kukljica, in **Bačina uvala** below the Čelinjak
ridge (V. vrh, 122,8 m). Cadastral parcels **2448/6, 2448/14, 2448/13, 2449/1**, measured at
**7,02 ha** with **1,11 km** of perimeter. Restoration of old olive terraces and dry stone walls,
removal of Aleppo pine, return of indigenous species, a craft workshop, volunteers. Model is
Sadhana Forest. Co-author is the painter **Toni Franović**.

**Maževica is the neighbouring bay, NOT this land.** That error was made once and corrected
everywhere. Do not reintroduce it.

---

## 2. HOW THE SITE IS BUILT

```
index.template.html   shell only — markup, CSS, render code, no sentences
content/simple/       20 files, 179 texts, EN + HR side by side
content/extended/     19 files, 19 lists, 136 rows
tools/inject.py       merges the two at build time, fails loudly on any error
build.sh              runs inject.py, assembles dist/
admin/                Sveltia CMS, two collections: ① Simple ② Extended
.github/workflows/    push to main → build → wrangler pages deploy
```

Push to `main` is the only action needed. Cloudflare never reads the repository; the Action
runs inside it and uploads finished files. Live in about 90 seconds.

**Never edit text in `index.template.html`.** It goes in `content/`, or the admin panel cannot
see it.

Rules that are already enforced and must stay: months are written as numbers ("8. mjesec",
never "kolovoz"), Croatian is written natively rather than translated, no blur anywhere, dark
mode default with a DAY toggle, version label `v1 (a)` bottom right.

---

## 3. WHAT IS ON THE SITE NOW

Sections in order: hero, numbers strip, the land, what happened here, **four trees**,
**philosophy**, method, water, calendar (interactive 12-segment phenological ring),
food forest, **growing food**, stone and craft (incl. bunja), test ground, sound, living here,
who, phases, influences, join, footer.

Images: Boris Kačan's aerial photograph and six crops from it (**credited, permission given**),
four generated tree portraits, six generated bunja visualisations, four generated food-workflow
images, ARKOD map, topographic map, Marko's hand pruning sketch, portraits.

Generated images used so far: **18 of a 50 cap** on the Nano Banana budget.

---

## 4. OPEN ITEMS

| Item | State |
|---|---|
| **CMS merge to main** | Branch `cms` is built and deployed to preview. Marko was testing the OAuth login. When he confirms it works: merge `cms` → `main`, change `admin/config.yml` `branch: cms` → `branch: main`, redeploy. |
| **Client Secret rotation** | The GitHub OAuth client secret was pasted into the previous chat. Once login is confirmed, Marko must generate a new one, delete the old, and send it so the worker secret is replaced. |
| **Token rotation** | The GitHub PAT and Cloudflare token were both pasted in chat. Both should be revoked and reissued as fine-grained, scoped, with an expiry. |
| **CROPIX photos** | Asked €70 + VAT per photo. Marko replied asking for them free as a contribution, or one photo instead of fourteen. **Awaiting answer.** If yes: add to the craft section with "Foto: Joško Ponoš / CROPIX, Slobodna Dalmacija, 2009." If no: nothing changes, the section already works. |
| **Općina Kukljica** | Email drafted to `nacelnik@opcina-kukljica.hr` (Marin Boško, Marko's cousin — the family tie is declared in writing in the email, deliberately). Asks for ownership check, long-term use without purchase, a meeting, and help with funding applications. **Not yet sent / no reply recorded.** |
| **Toni Franović** | Email drafted. Awaiting reply. |
| **Field photography** | Still the biggest gap. Nothing on the site is a photograph of the actual parcel taken by Marko. Needed: unpruned olives, dry stone wall condition, the pine stand, a pine seedling in maquis, lichen and moss as dew evidence, the shore, the view up to Čelinjak. |

---

## 5. THE TASK FOR THIS CHAT

### Build a field map page

**The purpose is practical, not decorative.** Marko will be standing on the land, on his phone,
in sun, wanting to know one thing: *am I on parcel 2448/6 or not?*

Build a page at `/karta` (Croatian) served from the same repository, with:

**5.1 — The map**

- **OpenStreetMap** base layer via Leaflet, no API key needed
- A satellite layer as an alternative, toggled — under trees the OSM base is useless for
  orientation, satellite is what he will actually use
- **The four parcels drawn as overlays**, each a distinct outline, filled at low opacity so the
  ground underneath stays readable
- Parcel labels drawn on the polygons: `2448/6`, `2448/14`, `2448/13`, `2449/1`

**5.2 — Locate me**

- A prominent **"Gdje sam"** button using `navigator.geolocation.watchPosition`
- A marker with an accuracy circle, updating live
- **The critical feature: it must say which parcel he is standing on.** Point-in-polygon test
  against each parcel, and a persistent readout at the top of the screen, large type:
  - inside → `NA ČESTICI 2448/6` in olive
  - outside → `IZVAN ČESTICA` in ochre, with distance in metres to the nearest boundary
- Handle the phone honestly: show the GPS accuracy in metres. If accuracy is worse than the
  distance to the boundary, say so rather than claiming certainty.

**5.3 — Tap a parcel, see its document**

Marko will attach the cadastral documents in this chat. When a parcel is tapped, open a panel
showing that parcel's document: owner, area, land registry data, whatever the documents contain.
Read the attached files first and let their actual content decide the fields — do not invent a
schema before seeing them.

The documents are the source of truth for parcel areas. The 7,02 ha figure is an ARKOD
measurement of the whole block; individual parcel areas will come from the documents and may
not sum to exactly that.

**5.4 — Works offline in the field**

There is no reliable signal in Bačina uvala. Options in order of preference:
1. cache the map tiles for the parcel bounding box in the page itself
2. failing that, a clear message that tiles are unavailable while geolocation still works —
   the parcel polygons are local data and must keep working with no network at all

The parcel outlines, the point-in-polygon logic and the readout **must not depend on the
network**. Only the tiles may.

**5.5 — Fits the rest of the site**

Same palette (`#0d1117` base, olive `#7d8f4f`, Adriatic `#2aa198`, ochre `#c8892f`), same
typefaces, same bilingual dictionary pattern with `data-i18n`, same version label. Bilingual
HR/EN, Croatian written natively. **No blur.**

Add its texts to `content/simple/` as a new file so it is editable from the admin panel like
everything else, and regenerate `admin/config.yml`.

Link it from the main page — the LAND section is the right place.

### Getting the coordinates

The ARKOD image `img/arkod.jpg` shows the polygon with a scale bar and section lengths
(257,86 m · 222,72 m · 112,36 m · 31,06 m · 43,32 m · 45,1 m · 54,23 m · 100,66 m · 24,08 m ·
52,92 m · 38,63 m · 125,94 m). The topographic map `img/topo.jpg` carries a coordinate readout:
`E N: 397456,099 4878428,271 · 44°2'19,26"N 15°13'13,97"E`, which is HTRS96/TM.

**Do not guess the polygon from the images.** Ask Marko for one of these, in this order:
1. a KML, GPX, GeoJSON or shapefile export from ARKOD or the cadastre — best
2. the parcel geometry from the public cadastre (`oss.uredjenazemlja.hr`) — usually exportable
3. failing both, a walk of the perimeter with a phone GPS track

If none is available yet, build the page with a placeholder polygon clearly marked as
approximate and a note saying so, so the rest can be tested and the geometry dropped in later.

---

## 6. THINGS THAT HAVE BEEN GOT WRONG BEFORE

- **Maževica vs Bačina uvala.** The land is in Bačina uvala. Fixed once already.
- **Press photographs.** Anything from CROPIX / Slobodna Dalmacija / Joško Ponoš stays off the
  site until written permission arrives. Boris Kačan's aerials **are** permitted and credited.
- **Mobile horizontal overflow.** Fixed by giving every grid column `minmax(0, …)`. Do not add
  a fixed-width grid column without it.
- **Near-black images.** A sunset photo read as an empty rectangle on the dark background and
  was removed. Check contrast against `#0d1117` before adding an image.
- **Overclaiming.** The site's credibility rests on not exaggerating. Every claim carries a
  number, a species name or a source, and the honest limits are stated out loud (the four trees
  do not make a complete diet; the phenological calendar is provisional until observed on site).

---

## 7. WHO MARKO IS, FOR TONE

Video editor at Nova TV, 27 years in production, seven years in Auroville, percussionist,
frame drum student of Yshai Afterman, DJ Mantra, founder of the Tribal Jam Orchestra. Low
vision and dyslexia, dictates almost everything by phone, works in Croatian and English.

Write plainly. Give him the answer first. Push back when he is wrong — he wants that, and it
has already saved this project twice.

---

*Kukljica EcoOasis · handoff v1 (a) · 6.9.2026.*
