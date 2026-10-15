// /api/oss/<path>?... → the state's cadastre and land register (oss.uredjenazemlja.hr), for the
// Owner's manual refresh button. OSS refuses a browser's Origin, so the site asks for it, the way the
// ARKOD Layer app does (markoboskoauroville/arkod_web, functions/_proxy.js).
//
// Narrow on purpose: three calls, k.o. Kukljica (334723) and its land book (21261) only, GET only.
// Every answer is cut down before it leaves: names and shares, never an address, a father's name or a
// maiden name, the same rule as data/oss.json. The state refuses some of Cloudflare's addresses (about
// two calls in three, measured by arkod_web); that comes back as 503 and the page asks again.

const BASE = 'https://oss.uredjenazemlja.hr/oss/public/';
const KO = '334723';
const BOOK = '21261';
const UA = 'kukljica-ecooasis/1 (+https://github.com/markoboskoauroville/KUKLJICA_ECOOASIS)';
const CORS = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, OPTIONS' };
const ABROAD = { AUSTRALIJA: 'Australija', TASMANIA: 'Australija', SAD: 'SAD', USA: 'SAD', 'NJEMAČKA': 'Njemačka' };

const title = (s) => String(s ?? '').toLowerCase().replace(/(^|[\s\-"(])(\p{L})/gu, (m, a, b) => a + b.toUpperCase());

/** A holder on a possession sheet: 'BOŠKO IVANA, DRAGUTIN, R. GOBIĆ' → 'Boško Ivana'. */
export function holderName(raw) {
  const first = String(raw ?? '').split(',')[0];
  return title(first.toUpperCase().split(/\s+(?:POK|UD|Ž|ROĐ)\.?\s/)[0].trim());
}

/** An owner in the land register: surname and first name; a foundation or the state as written. */
export function ownerName(raw) {
  const t = String(raw ?? '').replace(/\./g, '. ').replace(/\s+/g, ' ').trim();
  const q = t.match(/"\s*(.*?)\s*"\s*(.*)$/);
  if (q) return title(q[1] + (q[2] ? ', ' + q[2] : ''));
  if (/^(REPUBLIKA|OPĆINA|GRAD )/i.test(t)) return title(t);
  return title(t.split(' ').slice(0, 2).join(' '));
}

/** Only the country of a holder abroad, from the last part of the address. */
export function abroadOf(address) {
  const parts = String(address ?? '').split(',').map((s) => s.trim()).filter(Boolean);
  const tail = (parts[parts.length - 1] ?? '').replace(/\d/g, '').trim().toUpperCase();
  return ABROAD[tail] ?? '';
}

export function cutParcel(o) {
  if (!o || String(o.cadMunicipalityRegNum) !== KO) return null;
  return {
    number: String(o.parcelNumber ?? ''),
    m2: Number(o.area) || 0,
    parts: (o.parcelParts ?? []).map((p) => ({ use: String(p.name ?? '').toLowerCase(), m2: Number(p.area) || 0, pl: String(p.possessionSheetNumber ?? '') })),
    sheets: (o.possessionSheets ?? []).map((sh) => ({
      pl: String(sh.possessionSheetNumber ?? ''),
      people: (sh.possessors ?? []).map((w) => {
        const a = abroadOf(w.address);
        return a ? { n: holderName(w.name), share: String(w.ownership ?? ''), abroad: a } : { n: holderName(w.name), share: String(w.ownership ?? '') };
      }),
    })),
    folios: (o.lrUnitsFromParcelLinks ?? []).filter((u) => String(u.mainBookId) === BOOK)
      .map((u) => ({ unit: String(u.lrUnitNumber), kind: String(u.lrUnitTypeName ?? '').toLowerCase() })),
  };
}

const plain = (h) => String(h ?? '').replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();

export function cutFolio(raw) {
  const o = Array.isArray(raw) ? raw[0] : raw;
  if (!o || String(o.mainBookId) !== BOOK) return null;
  const groups = o.encumbranceSheetC?.lrEntryGroups ?? [];
  return {
    unit: String(o.lrUnitNumber ?? ''),
    kind: String(o.lrUnitTypeName ?? '').toLowerCase(),
    burdens: groups.reduce((a, g) => a + (g.lrEntries ?? []).length, 0),
    pending: (o.activePlumbs ?? []).length,
    shares: (o.ownershipSheetB?.lrUnitShares ?? []).map((sh) => {
      const t = plain(sh.description);
      return { share: t.includes(':') ? t.slice(t.lastIndexOf(':') + 1).trim() : t, owners: (sh.lrOwners ?? []).map((w) => ownerName(w.name)) };
    }).filter((sh) => sh.owners.length),
  };
}

/** Which of the three calls, and its address at the state; null for anything else. */
export function route(path, query) {
  const q = new URLSearchParams(query);
  if (path === 'search-cad-parcels/parcel-numbers' && q.get('municipalityRegNum') === KO && /^\d{1,6}(\/\d{1,4})?$/.test(q.get('search') ?? '')) {
    return { kind: 'search', url: `${BASE}${path}?search=${encodeURIComponent(q.get('search'))}&municipalityRegNum=${KO}` };
  }
  if (path === 'cad/parcel-info' && /^\d{1,12}$/.test(q.get('parcelId') ?? '')) {
    return { kind: 'parcel', url: `${BASE}${path}?parcelId=${q.get('parcelId')}` };
  }
  if (path === 'lr/lr-unit' && q.get('mainBookId') === BOOK && /^\d{1,7}$/.test(q.get('lrUnitNumber') ?? '')) {
    return { kind: 'folio', url: `${BASE}${path}?lrUnitNumber=${q.get('lrUnitNumber')}&mainBookId=${BOOK}&historicalOverview=false` };
  }
  return null;
}

const reply = (status, body, keep = 0) => new Response(typeof body === 'string' ? body : JSON.stringify(body), {
  status, headers: { ...CORS, 'Content-Type': typeof body === 'string' ? 'text/plain; charset=utf-8' : 'application/json; charset=utf-8',
    'Cache-Control': keep ? `public, max-age=${keep}` : 'no-store' },
});

export async function onRequest({ request, params }, fetcher = fetch) {
  if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
  if (request.method !== 'GET') return reply(405, 'method not allowed');
  const path = [].concat(params?.path ?? []).join('/');
  const r = route(path, new URL(request.url).search);
  if (!r) return reply(400, 'not an Owner\'s manual call');
  let answer;
  try {
    answer = await fetcher(r.url, { headers: { 'User-Agent': UA, Accept: 'application/json' } });
  } catch (e) {
    return reply(502, 'the state could not be reached');
  }
  if (answer.status === 403) return reply(503, 'refused by the state, ask again');
  if (!answer.ok) return reply(answer.status, 'the state answered ' + answer.status);
  let json;
  try { json = await answer.json(); } catch { return reply(502, 'the state sent no JSON'); }
  if (r.kind === 'search') return reply(200, (Array.isArray(json) ? json : []).map((h) => ({ key1: String(h.key1 ?? ''), value1: String(h.value1 ?? '') })), 3600);
  const out = r.kind === 'parcel' ? cutParcel(json) : cutFolio(json);
  return out ? reply(200, out, 3600) : reply(404, 'not in k.o. Kukljica');
}
