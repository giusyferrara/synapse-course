/* Adaptive Security Quiz — front-end flow (Milestone 4).
   Fetches an adaptive set, shows one question at a time with gentle feedback,
   and calls AI explain/hint ONLY on explicit button clicks. */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var state = { questions: [], i: 0, correctCount: 0, selected: null, answered: false, startedAt: 0, hintLevel: 0, chatHistory: [] };

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

    var CATS = {
      detect: { icon: "🐞", label: "Spot it" },
      understand: { icon: "💡", label: "Understand" },
      remediate: { icon: "🛠️", label: "Fix it" },
      tooling: { icon: "🔧", label: "Tooling" },
      severity: { icon: "⚖️", label: "Severity" }
    };
    var meta = CATS[q.category] || { icon: "•", label: q.category };
    $("card").className = "card cat-" + q.category;
    var chips = [];
    chips.push('<span class="chip cat-chip">' + meta.icon + " " + meta.label + "</span>");
    chips.push('<span class="chip">' + q.skill_tag + "</span>");
    if (q.owasp) chips.push('<span class="chip">OWASP ' + q.owasp + "</span>");
    chips.push('<span class="chip diff">' + q.difficulty + "</span>");
    $("chips").innerHTML = chips.join("");

    $("prompt").textContent = q.prompt;

    var code = $("code");
    var opts = $("options");
    opts.innerHTML = "";

    if (q.format === "fill_blank") {
      // Code with a drop slot + tappable tokens ("tap to place" — robust on touch)
      var marker = "▢"; // ▢
      var snippet = q.code_snippet || "";
      var idx = snippet.indexOf(marker);
      if (idx === -1) { code.textContent = snippet; }
      else {
        code.innerHTML = escapeHtml(snippet.slice(0, idx)) +
          '<span class="fb-slot" id="fbSlot">______</span>' +
          escapeHtml(snippet.slice(idx + marker.length));
      }
      code.classList.remove("hidden");
      opts.className = "options tokens";
      q.options.forEach(function (o) {
        var b = document.createElement("button");
        b.className = "token"; b.type = "button"; b.dataset.id = o.id;
        b.textContent = o.text;
        b.addEventListener("click", function () { placeToken(o.id, o.text, b); });
        opts.appendChild(b);
      });
    } else {
      opts.className = "options";
      if (q.code_snippet) { code.textContent = q.code_snippet; code.classList.remove("hidden"); }
      else { code.classList.add("hidden"); }
      q.options.forEach(function (o) {
        var b = document.createElement("button");
        b.className = "opt"; b.type = "button"; b.dataset.id = o.id;
        b.setAttribute("aria-pressed", "false");
        b.innerHTML = '<span class="k">' + o.id + '</span><span>' + escapeHtml(o.text) + "</span>";
        b.addEventListener("click", function () { selectOption(o.id, b); });
        opts.appendChild(b);
      });
    }

    // reset transient UI
    $("preActions").classList.remove("hidden");
    $("postActions").classList.add("hidden");
    $("feedback").classList.add("hidden");
    $("explainBox").classList.add("hidden");
    $("hintBox").classList.add("hidden");
    $("checkBtn").disabled = true;
    $("hintBtn").disabled = false;
    $("explainBtn").disabled = false;

    // staged hint + context chat reset for the new question
    state.hintLevel = 0;
    state.chatHistory = [];
    $("hintBtn").textContent = "💡 Hint";
    $("chatBox").classList.add("hidden");
    $("chatLog").innerHTML = "";
    $("chatInput").value = "";
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

  function placeToken(id, text, btn) {
    if (state.answered) return;
    state.selected = id;
    var slot = $("fbSlot");
    if (slot) { slot.textContent = text; slot.classList.add("filled"); }
    Array.prototype.forEach.call(document.querySelectorAll(".token"), function (b) {
      b.classList.toggle("chosen", b === btn);
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
    var tokens = document.querySelectorAll(".token");
    if (tokens.length) {
      var correctText = null, q = state.questions[state.i];
      q.options.forEach(function (o) { if (o.id === correctId) correctText = o.text; });
      Array.prototype.forEach.call(tokens, function (b) {
        b.disabled = true;
        if (b.dataset.id === correctId) b.classList.add("correct");
        else if (b.dataset.id === state.selected) b.classList.add("incorrect");
      });
      var slot = $("fbSlot");
      if (slot) {
        var ok = state.selected === correctId;
        slot.classList.add(ok ? "slot-ok" : "slot-no");
        if (!ok && correctText != null) slot.textContent = correctText;
      }
    }
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
      state = { questions: [], i: 0, correctCount: 0, selected: null, answered: false, startedAt: 0, hintLevel: 0, chatHistory: [] };
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

      // Learning gain: baseline -> current per skill (shows once there is enough practice)
      var gains = d.gains || [];
      var growth = "";
      if (gains.length) {
        growth = '<h3 style="margin-top:16px">Your growth 📈</h3>' +
          '<p class="muted">How much you\'ve improved as you practise.</p>' +
          gains.map(function (g) {
            var b = Math.round(g.baseline * 100), c = Math.round(g.current * 100);
            var arrow = g.delta > 0 ? "↑" : (g.delta < 0 ? "↓" : "→");
            var col = g.delta > 0 ? "var(--ok)" : (g.delta < 0 ? "var(--warn)" : "var(--ink-soft)");
            return '<div class="prog-row"><span class="prog-skill">' + escapeHtml(g.skill_tag) +
              '</span><span class="muted" style="flex:1">' + b + "% → <strong>" + c + "%</strong></span>" +
              '<span class="gain-badge" style="color:' + col + '">' + arrow + " " +
              Math.abs(Math.round(g.delta * 100)) + "</span></div>";
          }).join("");
      }

      pv.innerHTML =
        '<h3>Your progress</h3>' +
        '<p class="muted">Seen ' + d.questions_seen + ' questions · recent accuracy ' + recent +
        ' · current level: ' + (d.allowed_difficulties || []).join(", ") + "</p>" +
        (rows || '<p class="muted">Answer a few questions to see per-skill progress.</p>') +
        growth;
    });
  }

  function hint() {
    if (state.hintLevel >= 3) return;
    var q = state.questions[state.i];
    var next = state.hintLevel + 1;
    $("hintBtn").disabled = true;
    api("/api/quiz/hint", { method: "POST", body: JSON.stringify({ question_id: q.id, level: next }) })
      .then(function (res) {
        var box = $("hintBox"); box.classList.remove("hidden");
        if (!res.ok) {
          $("hintText").textContent = res.status === 429 ? res.body.error
            : "Hint unavailable right now — trust your reasoning!";
          if (state.hintLevel < 3) $("hintBtn").disabled = false;
          return;
        }
        state.hintLevel = next;
        $("hintText").textContent = "Hint " + next + "/3 — " + res.body.ai_text;
        if (next < 3) { $("hintBtn").disabled = false; $("hintBtn").textContent = "💡 More hint (" + next + "/3)"; }
        else { $("hintBtn").textContent = "💡 Hint (3/3)"; }
      });
  }

  function toggleChat() {
    var box = $("chatBox");
    box.classList.toggle("hidden");
    if (!box.classList.contains("hidden")) $("chatInput").focus();
  }

  function appendChat(role, text) {
    var log = $("chatLog");
    var d = document.createElement("div");
    d.className = "chat-msg " + role;
    d.textContent = text;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
    return d;
  }

  function sendChat() {
    var input = $("chatInput");
    var msg = (input.value || "").trim();
    if (!msg) return;
    var q = state.questions[state.i];
    appendChat("user", msg);
    var priorHistory = state.chatHistory.slice();
    state.chatHistory.push({ role: "user", text: msg });
    input.value = ""; input.disabled = true; $("chatSend").disabled = true;
    var bubble = appendChat("ai", "…");
    api("/api/quiz/chat", {
      method: "POST",
      body: JSON.stringify({ question_id: q.id, message: msg, answered: state.answered, history: priorHistory })
    }).then(function (res) {
      input.disabled = false; $("chatSend").disabled = false; input.focus();
      var text = res.ok ? res.body.ai_text
        : (res.status === 429 ? res.body.error : "Tutor unavailable right now — try again in a moment.");
      bubble.textContent = text;
      if (res.ok) state.chatHistory.push({ role: "ai", text: text });
    }).catch(function () {
      input.disabled = false; $("chatSend").disabled = false;
      bubble.textContent = "Network error — please try again.";
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
    $("askBtn").addEventListener("click", toggleChat);
    $("chatSend").addEventListener("click", sendChat);
    $("chatInput").addEventListener("keypress", function (e) { if (e.key === "Enter") sendChat(); });
    start();
  });
})();
