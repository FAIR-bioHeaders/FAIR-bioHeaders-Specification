// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. https://mozilla.org/MPL/2.0/.
// Optional local browser-DOM check, not an FHT toolkit/website implementation.
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.FHT_PLAYWRIGHT_MODULE || 'playwright');
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const pairs = readdirSync(path.join(root, 'examples')).filter(name => name.endsWith('.fht.json')).map(name => [
  path.join(root, 'examples', 'html', name.replace(/\.json$/, '.html')),
  path.join(root, 'examples', name)
]);
if (process.argv.length === 4) pairs.push(process.argv.slice(2));
else assert.equal(process.argv.length, 2, 'optional arguments are HTML JSON');
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  const requests = [];
  page.on('request', request => requests.push(request.url()));
  for (const [html, json] of pairs) {
    await page.setContent(readFileSync(html, 'utf8'));
    const actual = await page.evaluate(() => {
      const value = element => {
        const type = element.getAttribute('data-fhr-type');
        if (type === 'array') return Array.from(element.children, child => {
          if (child.getAttribute('itemprop') !== 'item') throw Error('unlabelled array child');
          return value(child);
        });
        if (type === 'object') return table(element.firstElementChild);
        if (type === 'integer' || type === 'number') return JSON.parse(element.textContent);
        if (type === 'boolean') return JSON.parse(element.textContent);
        if (type !== 'string') throw Error('unexpected scalar type');
        if (getComputedStyle(element).whiteSpace !== 'pre-wrap') throw Error('readable string whitespace collapses');
        if (element.innerText !== element.textContent) throw Error('readable string differs from metadata');
        return element.textContent;
      };
      const table = element => {
        const result = {};
        for (const row of element.tBodies[0].rows) {
          const name = row.cells[0].textContent;
          const property = row.cells[1].firstElementChild;
          if (property.getAttribute('itemprop') !== name) throw Error('readable/embedded label mismatch');
          if (Object.hasOwn(result, name)) throw Error('duplicate readable field');
          result[name] = value(property);
        }
        return result;
      };
      const scopes = document.querySelectorAll('table[itemtype]');
      if (scopes.length !== 1) throw Error('ambiguous record table');
      if (document.querySelector('script, iframe, object, embed, link, a, [hidden]')) throw Error('active/hidden content');
      for (const element of document.querySelectorAll('*')) {
        if (Array.from(element.attributes).some(attribute => attribute.name.startsWith('on'))) throw Error('event handler');
      }
      return table(scopes[0]);
    });
    const source = JSON.parse(readFileSync(json, 'utf8'));
    const expected = Object.fromEntries(Object.entries(source).filter(([name]) => !name.startsWith('x-')));
    assert.equal(JSON.stringify(actual), JSON.stringify(expected), html);
  }
  assert.deepEqual(requests, [], 'standalone metadata must not fetch anything');
  console.log(`${pairs.length} standalone records match Chromium DOM extraction; no active content or network requests.`);
} finally {
  await browser.close();
}
