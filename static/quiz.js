/* Adaptive Security Quiz — front-end flow (Milestone 4).
   Fetches an adaptive set, shows one question at a time with gentle feedback,
   and calls AI explain/hint ONLY on explicit button clicks. */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var state = { questions: [], i: 0, correctCount: 0, selected: null, answered: false, startedAt: 0 };

  function api(path, opts) {
    return fetch(path, Object.assign({ headers: { "Content-Type": "application/json" } }, opts || {}))
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, status: r.status, body: j }; }); });
  }

  function start() {
    api("/api/quiz/next?n=10").then(function (res) {
      if (!res.ok) {
        $("loading").textContent = (res.body && res.body.error) || "Could not load the quiz.";
        return;
      }
      state.questions = res.body.questions || [];
      if (!state.questions.length) { $("loading").textContent = "No questions available."; return; }
      $("loading").classList.add("hidden");
      $("quiz").classList.remove("hidden");
      render();
    }).catch(function () { $("loading").textContent = "Network error — please refresh."; });
  }

  function render() {
    var q = state.questions[state.i];
    state.selected = null; state.answered = false; state.startedAt = Date.now();

    var total = state.questions.length;
    $("progressLabel").textContent = "Question " + (state.i + 1) + "/" + total;
    $("progressBar").style.width = ((state.i) / total * 100) + "%";

    var chips = [];
    chips.push('<span class="chip">' + q.category + "</span>");
    chips.push('<span class="chip">' + q.skill_tag + "</span>");
    if (q.owasp) chips.push('<span class="chip">OWASP ' + q.owasp + "</span>");
    chips.push('<span class="chip diff">' + q.difficulty + "</span>");
    $("chips").innerHTML = chips.join("");

    $("prompt").textContent = q.prompt;

    var code = $("code");
    if (q.code_snippet) { code.textContent = q.code_snippet; code.classList.remove("hidden"); }
    else { code.classList.add("hidden"); }

    var opts = $("options");
    opts.innerHTML = "";
    q.options.forEach(function (o) {
      var b = document.createElement("button");
      b.className = "opt"; b.type = "button"; b.dataset.id = o.id;
      b.setAttribute("aria-pressed", "false");
      b.innerHTML = '<span class="k">' + o.id + '</span><span>' + escapeHtml(o.text) + "</span>";
      b.addEventListener("click", function () { selectOption(o.id, b); });
      opts.appendChild(b);
    });

    // reset transient UI
    $("preActions").classList.remove("hidden");
    $("postActions").classList.add("hidden");
    $("feedback").classList.add("hidden");
    $("explainBox").classList.add("hidden");
    $("hintBox").classList.add("hidden");
    $("checkBtn").disabled = true;
    $("hintBtn").disabled = false;
    $("explainBtn").disabled = false;
  }

  function selectOption(id, btn) {
    if (state.answered) return;
    state.selected = id;
    Array.prototype.forEach.call(document.querySelectorAll(".opt"), function (b) {
      b.classList.toggle("selected", b === btn);
      b.setAttribute("aria-pressed", b === btn ? "true" : "false");
    });
    $("checkBtn").disabled = false;
  }

  function check() {
    if (state.selected == null || state.answered) return;
    var q = state.questions[state.i];
    var elapsed = Date.now() - state.startedAt;
    $("checkBtn").disabled = true;
    api("/api/quiz/answer", {
      method: "POST",
      body: JSON.stringify({ question_id: q.id, chosen_option: state.selected, time_ms: elapsed })
    }).then(function (res) {
      if (!res.ok) { showFeedback(false, "Could not record that answer — " + ((res.body && res.body.error) || ""), null, null); return; }
      state.answered = true;
      if (res.body.is_correct) state.correctCount++;
      markOptions(res.body.correct_option_id);
      showFeedback(res.body.is_correct, res.body.explanation, res.body.source_reference, q);
      $("preActions").classList.add("hidden");
      $("postActions").classList.remove("hidden");
    });
  }

  function markOptions(correctId) {
    Array.prototype.forEach.call(document.querySelectorAll(".opt"), function (b) {
      b.disabled = true;
      if (b.dataset.id === correctId) b.classList.add("correct");
      else if (b.dataset.id === state.selected) b.classList.add("incorrect");
    });
  }

  function showFeedback(ok, explanation, source, q) {
    var fb = $("feedback");
    fb.className = "feedback " + (ok ? "ok" : "no");
    var head = ok ? "✅ Nice — that's right." : "🌱 Not quite — and that's okay. Here's why:";
    var html = "<h3>" + head + "</h3><div>" + escapeHtml(explanation || "") + "</div>";
    if (source) html += '<div class="src">Reference: ' + escapeHtml(source) + "</div>";
    fb.innerHTML = html;
    fb.classList.remove("hidden");
    fb.focus();
  }

  function next() {
    state.i++;
    if (state.i >= state.questions.length) { finish(); return; }
    render();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function finish() {
    $("progressBar").style.width = "100%";
    $("quiz").classList.add("hidden");
    var total = state.questions.length;
    var pct = Math.round(state.correctCount / total * 100);
    var msg = pct >= 80 ? "Brilliant work!" : pct >= 50 ? "Solid effort — you're building real skill." : "Every attempt teaches you something. Keep going!";
    var s = $("summary");
    s.innerHTML =
      '<div class="big">' + state.correctCount + "/" + total + "</div>" +
      "<p>" + msg + "</p>" +
      '<p class="muted">Questions you missed will gently come back later for review.</p>' +
      '<div id="progressView" class="progress-view muted">Loading your progress…</div>' +
      '<div class="actions" style="justify-content:center"><button class="btn" type="button" id="againBtn">Start another set</button></div>';
    s.classList.remove("hidden");
    loadProgress();
    $("againBtn").addEventListener("click", function () {
      state = { questions: [], i: 0, correctCount: 0, selected: null, answered: false, startedAt: 0 };
      s.classList.add("hidden");
      $("loading").classList.remove("hidden");
      $("loading").textContent = "Loading your quiz…";
      start();
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function loadProgress() {
    var pv = $("progressView");
    if (!pv) return;
    api("/api/quiz/progress").then(function (res) {
      if (!res.ok) { pv.innerHTML = ""; return; }
      var d = res.body;
      var attempted = (d.skills || []).filter(function (s) { return s.attempted; });
      attempted.sort(function (a, b) { return (a.accuracy || 0) - (b.accuracy || 0); });
      var rows = attempted.map(function (s) {
        var pct = Math.round((s.accuracy || 0) * 100);
        return '<div class="prog-row"><span class="prog-skill">' + escapeHtml(s.skill_tag) +
          '</span><span class="prog-bar"><i style="width:' + pct + '%"></i></span>' +
          '<span class="prog-pct">' + pct + "%</span></div>";
      }).join("");
      var recent = d.recent_accuracy == null ? "—" : Math.round(d.recent_accuracy * 100) + "%";
      pv.innerHTML =
        '<h3>Your progress</h3>' +
        '<p class="muted">Seen ' + d.questions_seen + ' questions · recent accuracy ' + recent +
        ' · current level: ' + (d.allowed_difficulties || []).join(", ") + "</p>" +
        (rows || '<p class="muted">Answer a few questions to see per-skill progress.</p>');
    });
  }

  function hint() {
    var q = state.questions[state.i];
    $("hintBtn").disabled = true;
    api("/api/quiz/hint", { method: "POST", body: JSON.stringify({ question_id: q.id }) })
      .then(function (res) {
        var box = $("hintBox"); box.classList.remove("hidden");
        if (res.status === 429) { $("hintText").textContent = res.body.error; return; }
        if (!res.ok) { $("hintText").textContent = "Hint unavailable right now — trust your reasoning!"; return; }
        $("hintText").textContent = res.body.ai_text;
      });
  }

  function explain() {
    var q = state.questions[state.i];
    $("explainBtn").disabled = true;
    var box = $("explainBox"); box.classList.remove("hidden");
    $("explainText").textContent = "Thinking…";
    api("/api/quiz/explain", { method: "POST", body: JSON.stringify({ question_id: q.id, chosen_option: state.selected }) })
      .then(function (res) {
        if (res.status === 429) { $("explainText").textContent = res.body.error; return; }
        if (!res.ok) { $("explainText").textContent = "AI explanation unavailable — the explanation above always stands."; return; }
        $("explainText").textContent = res.body.ai_text;
      });
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    $("checkBtn").addEventListener("click", check);
    $("nextBtn").addEventListener("click", next);
    $("hintBtn").addEventListener("click", hint);
    $("explainBtn").addEventListener("click", explain);
    start();
  });
})();
