// Every inline <script> of every page must at least COMPILE.
//   node tests/page_scripts_syntax_test.js
// Added 22 Nov 2026: an edit put real line breaks inside JavaScript strings on the
// Java course page; the whole script stopped and no course loaded, and the content
// tests did not notice because they never compiled the page.
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const dirs = ['templates', 'templates/mobile', 'static/lessons'];
const skip = /\.(bak|orig|backup|old|save)|~$|bak_/i;
let pages = 0, scripts = 0;
const failures = [];

for (const d of dirs) {
  const dir = path.join(root, d);
  if (!fs.existsSync(dir)) continue;
  for (const f of fs.readdirSync(dir)) {
    if (!f.endsWith('.html') || skip.test(f)) continue;
    const html = fs.readFileSync(path.join(dir, f), 'utf8');
    pages++;
    const re = /<script(?![^>]*\bsrc=)([^>]*)>([\s\S]*?)<\/script>/gi;
    let m;
    while ((m = re.exec(html))) {
      const attrs = m[1];
      if (/type\s*=\s*["'](?!text\/javascript|module)[^"']*["']/i.test(attrs)) continue; // JSON, templates
      scripts++;
      const line = html.slice(0, m.index).split('\n').length;
      try {
        new vm.Script(m[2], { filename: `${d}/${f}:${line}` });
      } catch (e) {
        if (/module/.test(attrs) && /import|export/.test(e.message)) continue;
        failures.push(`${d}/${f} (script starting at line ${line}): ${e.message}`);
      }
    }
  }
}
for (const x of failures) console.log('FAIL  ' + x);
console.log(`${pages} pages, ${scripts} inline scripts, ${failures.length} that do not compile`);
process.exit(failures.length ? 1 : 0);
