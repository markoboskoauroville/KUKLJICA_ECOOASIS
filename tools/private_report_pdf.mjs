// Print the private owners' report to PDF, with the two maps captured from the page itself.
// Needs a local server on the repo root (python3 -m http.server 8765) and Playwright.
// Writes only to .secret/ (git-ignored):  node tools/private_report_pdf.mjs
import { createRequire } from 'module';
import path from 'path';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
let pw;
try { pw = require('playwright'); } catch { pw = require(path.join(process.env.NODE_PATH || '', 'playwright')); }
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SEC = path.join(ROOT, '.secret');

const b = await pw.chromium.launch();
const page = await b.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 2 });
await page.addInitScript(() => { try { localStorage.setItem('kem', 'day'); localStorage.removeItem('ke-own-live'); } catch (e) {} });
await page.goto('http://localhost:8765/index.html?lang=en');
await page.addStyleTag({ content: 'nav{position:static!important}' });
for (const [mode, file] of [['fam', 'map-family.png'], ['zk', 'map-register.png']]) {
  await page.click(`#owmaptabs button[data-m="${mode}"]`);
  await page.waitForTimeout(250);
  await (await page.$('.owmapwrap > div')).screenshot({ path: path.join(SEC, file) });
}
const doc = await b.newPage();
await doc.goto('file://' + path.join(SEC, 'owners-report.html'));
const out = path.join(SEC, 'Kukljica-EcoOasis-owners-PRIVATE.pdf');
await doc.pdf({
  path: out, format: 'A4', printBackground: true, displayHeaderFooter: true,
  headerTemplate: '<div></div>',
  footerTemplate: '<div style="font:7pt monospace;color:#a33;width:100%;padding:0 14mm;display:flex;justify-content:space-between"><span>KUKLJICA ECOOASIS · OWNERS · PRIVATE, NOT FOR PUBLICATION</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
  margin: { top: '16mm', bottom: '18mm', left: '14mm', right: '14mm' },
});
await b.close();
console.log('wrote', out);
