// Runs the REAL checkSolution() from templates/course.html against a fake page.
//   node tests/check_solution_page_test.js
// Prints one line per case and exits 1 if any fails.
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'templates', 'course.html'), 'utf8');

function extract(name) {
  const start = html.indexOf('    async function ' + name + '(') >= 0
    ? html.indexOf('    async function ' + name + '(') : html.indexOf('    function ' + name + '(');
  if (start < 0) throw new Error('not found: ' + name);
  const end = html.indexOf('\n    }\n', start);
  return html.slice(start, end + 6);
}

function page(editorCode) {
  const els = {
    codeEditor: { value: editorCode },
    outputConsole: { textContent: '' },
    chatInput: { value: '' },
  };
  const env = { chat: [], fetches: [], sent: [], events: [], els };
  env.document = { getElementById: (id) => els[id] || null };
  env.addChatMessage = (who, text) => env.chat.push([who, text]);
  env.logLearningEvent = (t, d) => env.events.push([t, d]);
  env.sendMessage = () => env.sent.push(els.chatInput.value);
  env.fetch = async (url, opts) => {
    env.fetches.push([url, JSON.parse(opts.body)]);
    return { json: async () => env.reply };
  };
  return env;
}

async function run(env, currentGraded) {
  const fn = new Function('document', 'addChatMessage', 'logLearningEvent', 'sendMessage', 'fetch', 'currentGraded', 'console',
    extract('checkSolution') + '\nreturn checkSolution();');
  await fn(env.document, env.addChatMessage, env.logLearningEvent, env.sendMessage, env.fetch, currentGraded, { error() {} });
}

const results = [];
function check(name, ok) { results.push(ok); console.log((ok ? 'PASS  ' : 'FAIL  ') + name); }

(async () => {
  // 1. own code: the tutor answers, the grader is never called, nothing is graded
  let e = page('print("Hello, Python Forensics!")');
  await run(e, null);
  check('own code: no call to the grader', e.fetches.length === 0);
  check('own code: the tutor is asked once', e.sent.length === 1 && /look at the code in my editor/.test(e.sent[0]));
  check('own code: says plainly it is not a grade, under the editor and in the chat',
    /not a grade/.test(e.els.outputConsole.textContent) && e.chat.some(([w, t]) => /not a grade/.test(t)));

  // 2. a course exercise: only ids and code go to the server; the verdict shows under the editor
  e = page('print("x")');
  e.reply = { status: 'failed', feedback: 'Line 1 is different.' };
  await run(e, { course_id: 'py_syntax_output', exercise_id: 'ex_01' });
  check('exercise: one call to evaluate_code', e.fetches.length === 1 && e.fetches[0][0] === '/api/course/evaluate_code');
  check('exercise: body is exactly course_id, exercise_id, code',
    JSON.stringify(Object.keys(e.fetches[0][1]).sort()) === JSON.stringify(['code', 'course_id', 'exercise_id']));
  check('exercise: verdict shown under the editor', /Line 1 is different/.test(e.els.outputConsole.textContent));
  check('exercise: the tutor is not asked', e.sent.length === 0);

  e = page('print("Hello, Python Forensics!")');
  e.reply = { status: 'passed', feedback: 'Correct!' };
  await run(e, { course_id: 'py_syntax_output', exercise_id: 'ex_01' });
  check('exercise passed: celebrated under the editor', /🎉 Correct!/.test(e.els.outputConsole.textContent));

  // 3. empty editor: nothing is sent anywhere
  e = page('   ');
  await run(e, { course_id: 'py_syntax_output', exercise_id: 'ex_01' });
  check('empty editor: nothing sent', e.fetches.length === 0 && e.sent.length === 0);

  // 4. loading an example forgets the exercise
  for (const f of ['tryExample', 'runExampleDirectly', 'generateAIExercise']) {
    check(f + ' clears the graded exercise', /currentGraded = null;/.test(extract(f)));
  }
  check('Start Exercise sets the graded exercise', /currentGraded = \{ course_id: courseId, exercise_id: exercise\.exercise_id/.test(extract('loadExerciseCode')));

  process.exit(results.every(Boolean) ? 0 : 1);
})();
