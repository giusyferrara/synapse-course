// Algorithm Player regressions (Nov 2026): truthful prediction texts, keyboard on buttons, aria-live.
//   node tests/algorithm_player_test.js
// Runs the REAL helper functions taken from static/lessons/algorithm-player.html.
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'static', 'lessons', 'algorithm-player.html'), 'utf8');

function extract(name) {
  const start = html.indexOf('  function ' + name + '(');
  if (start < 0) throw new Error('not found: ' + name);
  const end = html.indexOf('\n  }\n', start);
  return html.slice(start, end + 4);
}
const api = new Function(extract('predictOptions') + extract('predictCopy') + extract('keyAction') +
  '\nreturn { predictCopy, predictOptions, keyAction };')();

const results = [];
function check(name, ok) { results.push(ok); console.log((ok ? 'PASS  ' : 'FAIL  ') + name); }
const FALSE_CLAIMS = /won the comparison|isn't added to it|simply overwritten/;

// accumulating: the new value comes FROM the old one
let c = api.predictCopy('total', 4, 12, '    total = total + list[i];');
check('total = total + list[i]: says it is worked out from the old value', /worked out from the old one/.test(c.right + c.wrong));
check('total = total + list[i]: no false claim', !FALSE_CLAIMS.test(c.now + c.right + c.wrong));
check('the line about to run is shown', /total = total \+ list\[i\]/.test(c.now));
c = api.predictCopy('total', 4, 12, 'total += list[i];');
check('total += ...: worked out from the old value', /worked out from the old one/.test(c.right));

// replacing
c = api.predictCopy('best', 3, 8, '        best = list[i];');
check('best = list[i]: says the old value is replaced', /replaced by the new value/.test(c.right));
c = api.predictCopy('lo', 0, 5, '        lo = mid + 1;');
check('lo = mid + 1: replaced, nothing about comparisons', /replaced/.test(c.right) && !FALSE_CLAIMS.test(c.right + c.wrong + c.now));
c = api.predictCopy('total', 0, 0, 'int total = 0;');
check('a Java declaration is read correctly', /replaced/.test(c.right));

// no claim when the line does not show an assignment to that name
c = api.predictCopy('i', 2, 3, 'i++');
check('i++: no claim about how', !/worked out|replaced/.test(c.right));
c = api.predictCopy('total', 1, 2, 'subtotal = subtotal + 1;');
check('subtotal is not total', !/worked out|replaced/.test(c.right));
c = api.predictCopy('x', 1, 2, 'if (x == 2) {');
check('a comparison is not an assignment', !/worked out|replaced/.test(c.right));

// options
const o = api.predictOptions(0, 4);
check('options: three, all different, the right one included', o.length === 3 && new Set(o).size === 3 && o.includes(4));
check('options: never a duplicate for any small pair', [...Array(8).keys()].every((w) =>
  [...Array(8).keys()].every((n) => { const p = api.predictOptions(w, n); return new Set(p).size === p.length && p.includes(n); })));

// keyboard
check('arrows work while a button has focus', api.keyAction('BUTTON', 'ArrowRight') === 'next' && api.keyAction('BUTTON', 'ArrowLeft') === 'back');
check('Space on a button stays the button\'s own', api.keyAction('BUTTON', ' ') === null);
check('Space elsewhere plays', api.keyAction('DIV', ' ') === 'play' && api.keyAction('BODY', ' ') === 'play');
check('typing and the step slider keep their keys', api.keyAction('INPUT', 'ArrowRight') === null && api.keyAction('SELECT', 'ArrowLeft') === null);

// page-wide
check('the false texts are gone from the whole player', !FALSE_CLAIMS.test(html));
check('a polite live region exists', /id="live"[^>]*aria-live="polite"/.test(html));
const stepFn = extract('step');
check('Play does not announce every step (no announce inside step())', !/announce\(/.test(stepFn));
check('pausing announces once', /announce\("Paused\. "/.test(extract('stop')));

process.exit(results.every(Boolean) ? 0 : 1);
