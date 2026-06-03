/*
 * synapse_a11y_toolbar.js — shared, page-INDEPENDENT accessibility toolbar.
 *
 * A faithful extraction of index.html's inline toolbar into one reusable module:
 *   - injects the SAME top navbar (logo + Home/Java/Graphs + accessibility cluster),
 *     same icons, the butterfly accessibility icon (NO wheelchair), horizontal inline row;
 *   - keeps ALL state in this closure (no index-only globals);
 *   - creates its OWN DOM hooks (reading-pointer panel/line, focus overlay, audio panel);
 *   - delegates shared features to synapse_a11y.js (window.synapseToggle*) and the
 *     focus assistant to focus_assistant.js (window.toggleFocusAssistant);
 *   - ships its own styling in synapse_a11y_toolbar.css.
 *
 * Usage on a page:
 *   <link rel="stylesheet" href="/static/synapse_a11y_toolbar.css">
 *   <script src="/static/focus_assistant.js"></script>      (optional, for the 💡 button)
 *   <script src="/static/synapse_a11y_toolbar.js"></script> (before synapse_a11y.js)
 *   <script src="/static/synapse_a11y.js"></script>
 */
(function () {
  "use strict";
  if (window.__synapseToolbarLoaded) return;
  window.__synapseToolbarLoaded = true;

  // ---------- private state ----------
  var fontPct = 100, ttsEnabled = false, pointerActive = false,
      voiceRecognition = null, isRecording = false,
      focusModeActive = false, focusAssistActive = false, spotEl = null, spotPrev = null;

  function toast(msg) { if (window.synapseToast) window.synapseToast(msg); else console.log(msg); }
  function setActive(id, on) { var b = document.getElementById(id); if (b) b.classList.toggle("active", on); }

  // ---------- the navbar markup (identical to index.html) ----------
  var NAV_HTML =
    '<nav id="synapseA11yNav" style="position:fixed;top:0;left:0;right:0;height:56px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);display:flex;align-items:center;justify-content:space-between;padding:0 20px;box-shadow:0 2px 10px rgba(0,0,0,0.1);z-index:10001;">' +
      '<a href="/app" style="display:flex;align-items:center;gap:12px;text-decoration:none;">' +
        '<img src="/icons/butterfly_logo_bright.svg" alt="Synapse" style="width:40px;height:40px;" onerror="this.outerHTML=\'<span style=font-size:40px>🧠</span>\';">' +
        '<div style="display:flex;flex-direction:column;">' +
          '<span style="color:white;font-size:18px;font-weight:700;">Synapse</span>' +
          '<span style="color:rgba(255,255,255,0.8);font-size:12px;">Learning designed for focused, creative minds</span>' +
        '</div>' +
      '</a>' +
      '<div style="display:flex;align-items:center;gap:6px;">' +
        '<button onclick="window.location.href=\'/app\'" title="Home" style="width:38px;height:38px;border:none;border-radius:50%;background:rgba(255,255,255,0.15);cursor:pointer;font-size:20px;color:white;">🏠</button>' +
        '<button onclick="window.location.href=\'/course/java-security\'" title="Java Security" style="width:38px;height:38px;border:none;border-radius:50%;background:rgba(255,255,255,0.15);cursor:pointer;font-size:20px;color:white;">🔒</button>' +
        '<button onclick="window.location.href=\'/tools\'" title="Graphs" style="width:38px;height:38px;border:none;border-radius:50%;background:rgba(255,255,255,0.15);cursor:pointer;font-size:20px;color:white;">📊</button>' +
        '<button onclick="document.getElementById(\'accessBtns\').style.display=document.getElementById(\'accessBtns\').style.display===\'flex\'?\'none\':\'flex\'" title="Accessibility" style="width:40px;height:40px;border:none;border-radius:50%;background:transparent;cursor:pointer;padding:0;">' +
          '<img src="/icons/access.png" alt="Accessibility" style="width:40px;height:40px;" onerror="this.outerHTML=\'🦋\'">' +
        '</button>' +
        '<div id="accessBtns" style="display:none;gap:4px;align-items:center;">' +
          btn("darkModeBtn", "synapseToolbar.toggleDark()", "Dark Mode", "🌙", 16) +
          btn("dyslexiaBtn", "synapseToolbar.toggleDyslexiaFont()", "Dyslexia Font", "📖", 16) +
          btn("", "synapseToolbar.increaseFontSize()", "A+", "A+", 14, true) +
          btn("", "synapseToolbar.decreaseFontSize()", "A-", "A-", 14, true) +
          btn("readingPointerBtn", "synapseToolbar.toggleReadingPointer()", "Reading Pointer", "📍", 16) +
          btn("textToSpeechBtn", "synapseToolbar.toggleTextToSpeech()", "Text to Speech", "🔊", 16) +
          btn("highContrastBtn", "synapseToolbar.toggleHighContrast()", "High Contrast", "⚫⚪", 10) +
          btn("focusModeBtn", "synapseToolbar.toggleFocusMode()", "Focus Mode", "🎯", 16) +
          btn("focusAssistantBtn", "synapseToolbar.toggleFocusAssistant()", "Focus Assistant", "💡", 16) +
          btn("", "synapseToolbar.toggleCalmingAudio()", "Calming Audio", "🎵", 16) +
          btn("voiceBtn", "synapseToolbar.toggleVoiceInput()", "Voice Input", "🎤", 16) +
          btn("reduceMotionBtn", "synapseToolbar.toggleReduceMotion()", "Reduce Motion", "⚡", 16) +
          btn("", "window.synapseToggleLineSpacing&&synapseToggleLineSpacing();this.classList.toggle('active')", "Line Spacing", "↕", 16) +
          btn("", "window.synapseToggleReadingMask&&synapseToggleReadingMask();this.classList.toggle('active')", "Reading Mask", "🔲", 16) +
          btn("", "window.synapseToggleColorOverlay&&synapseToggleColorOverlay();this.classList.toggle('active')", "Color Overlay", "🎨", 16) +
          btn("", "window.synapseToggleCursorHighlight&&synapseToggleCursorHighlight();this.classList.toggle('active')", "Cursor Highlight", "🟡", 16) +
          btn("", "window.synapseToggleDictionary&&synapseToggleDictionary();this.classList.toggle('active')", "Dictionary", "📚", 16) +
          btn("", "window.synapseToggleCalmMode&&synapseToggleCalmMode();this.classList.toggle('active')", "Calm Mode", "🧘", 16) +
          btn("", "synapseToolbar.reset()", "Reset All", "🔄", 18, false, "rgba(255,107,107,0.6)") +
        '</div>' +
      '</div>' +
    '</nav>';

  function btn(id, onclick, title, label, fontSize, bold, bg) {
    return '<button' + (id ? ' id="' + id + '"' : "") +
      ' onclick="' + onclick + '" title="' + title + '" data-tooltip="' + title + '"' +
      ' style="width:34px;height:34px;border:none;border-radius:50%;background:' + (bg || "rgba(255,255,255,0.2)") +
      ';cursor:pointer;font-size:' + fontSize + 'px;' + (bold ? "font-weight:700;" : "") +
      'color:white;transition:all 0.2s;">' + label + "</button>";
  }

  var POINTER_HTML =
    '<div id="synapseReadingPointerSettings">' +
      '<h3>📍 Reading Pointer Settings</h3>' +
      '<div class="setting-group"><label>Pointer Color</label>' +
        '<input type="color" id="synapsePointerColor" value="#667eea" onchange="synapseToolbar.updatePointerSettings()"></div>' +
      '<div class="setting-group"><label>Line Thickness <span class="thickness-value" id="synapseThicknessValue">3px</span></label>' +
        '<input type="range" id="synapsePointerThickness" min="1" max="10" value="3" step="1" oninput="synapseToolbar.updatePointerSettings()"></div>' +
      '<div class="pointer-preview"><div class="pointer-preview-line" id="synapsePointerPreviewLine"></div></div>' +
      '<button class="pointer-toggle-btn" id="synapsePointerToggleBtn" onclick="synapseToolbar.togglePointerActive()">📍 Activate Pointer</button>' +
    '</div>' +
    '<div id="synapseReadingPointerLine"></div>' +
    '<div id="synapseFocusOverlay"></div>';

  // ---------- injection ----------
  function inject() {
    if (document.getElementById("synapseA11yNav")) return;
    var holder = document.createElement("div");
    holder.innerHTML = NAV_HTML + POINTER_HTML;
    // prepend nav + appended hooks
    var nodes = Array.prototype.slice.call(holder.childNodes);
    nodes.forEach(function (n) { document.body.appendChild(n); });
    document.body.classList.add("synapse-has-toolbar");
    // Reserve EXACTLY the toolbar's real height so it never covers page content,
    // on any screen size or however many rows it wraps to.
    var navEl = document.getElementById("synapseA11yNav");
    function reserveToolbarSpace() {
      if (navEl) document.body.style.paddingTop = (navEl.offsetHeight + 20) + "px"; // +20px breathing room
    }
    reserveToolbarSpace();
    setTimeout(reserveToolbarSpace, 300); // after the logo image / fonts settle
    window.addEventListener("resize", reserveToolbarSpace);
    restore();
  }

  // ---------- handlers (faithful to index.html, self-contained) ----------
  var api = {
    toggleDark: function () {
      var on = document.body.classList.toggle("dark-mode");
      setActive("darkModeBtn", on);
      try { localStorage.setItem("darkMode", on); } catch (e) {}
    },
    toggleHighContrast: function () {
      var on = document.body.classList.toggle("high-contrast");
      setActive("highContrastBtn", on);
      try { localStorage.setItem("highContrast", on); } catch (e) {}
    },
    toggleDyslexiaFont: function () {
      var on = document.body.classList.toggle("dyslexia-font-active");
      setActive("dyslexiaBtn", on);
      try { localStorage.setItem("dyslexiaFont", on); } catch (e) {}
    },
    increaseFontSize: function () {
      if (fontPct < 160) { fontPct += 10; applyFont(); }
    },
    decreaseFontSize: function () {
      if (fontPct > 80) { fontPct -= 10; applyFont(); }
    },
    toggleReadingPointer: function () {
      var p = document.getElementById("synapseReadingPointerSettings");
      var on = p.classList.toggle("visible");
      setActive("readingPointerBtn", on);
      if (on) loadPointer();
    },
    updatePointerSettings: function () {
      var color = val("synapsePointerColor", "#667eea"), th = val("synapsePointerThickness", "3");
      style("synapsePointerPreviewLine", color, th);
      style("synapseReadingPointerLine", color, th);
      var v = document.getElementById("synapseThicknessValue"); if (v) v.textContent = th + "px";
      try { localStorage.setItem("synapsePointer", JSON.stringify({ color: color, thickness: th })); } catch (e) {}
    },
    togglePointerActive: function () {
      var b = document.getElementById("synapsePointerToggleBtn"), line = document.getElementById("synapseReadingPointerLine");
      pointerActive = !pointerActive;
      if (pointerActive) { b.classList.add("active"); b.textContent = "✅ Pointer Active"; line.classList.add("active"); document.addEventListener("mousemove", movePointer); }
      else { b.classList.remove("active"); b.textContent = "📍 Activate Pointer"; line.classList.remove("active"); document.removeEventListener("mousemove", movePointer); }
    },
    toggleTextToSpeech: function () {
      ttsEnabled = !ttsEnabled; setActive("textToSpeechBtn", ttsEnabled);
      if (ttsEnabled) {
        if (window.speechSynthesis) window.speechSynthesis.speak(new SpeechSynthesisUtterance("Text to speech on"));
        document.addEventListener("click", speak);
      } else { if (window.speechSynthesis) window.speechSynthesis.cancel(); document.removeEventListener("click", speak); }
    },
    toggleReduceMotion: function () {
      var on = document.body.classList.toggle("reduce-motion"); setActive("reduceMotionBtn", on);
    },
    toggleVoiceInput: function () {
      var btn = document.getElementById("voiceBtn");
      if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) { toast("Voice input isn't supported in this browser."); return; }
      var target = document.activeElement;
      var isField = target && (target.tagName === "TEXTAREA" || (target.tagName === "INPUT" && /text|search/i.test(target.type || "text")));
      if (isRecording) { if (voiceRecognition) voiceRecognition.stop(); return; }
      if (!isField) { toast("Click into a text box first, then use voice input."); return; }
      var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      voiceRecognition = new SR(); voiceRecognition.continuous = false; voiceRecognition.interimResults = false; voiceRecognition.lang = "en-US";
      voiceRecognition.onstart = function () { isRecording = true; if (btn) btn.classList.add("active"); };
      voiceRecognition.onresult = function (e) { var t = e.results[0][0].transcript; if (target && "value" in target) target.value += t + " "; };
      voiceRecognition.onerror = function (e) { isRecording = false; if (btn) btn.classList.remove("active"); toast("Voice error: " + e.error); };
      voiceRecognition.onend = function () { isRecording = false; if (btn) btn.classList.remove("active"); };
      voiceRecognition.start();
    },
    // 🎯 Focus Mode = spotlight follows the pointer (hover); only the hovered area is lit.
    toggleFocusMode: function () {
      focusModeActive = !focusModeActive;
      setActive("focusModeBtn", focusModeActive);
      if (focusModeActive) {
        if (focusAssistActive) api.toggleFocusAssistant();   // mutually exclusive
        showOverlay(true);
        document.addEventListener("mousemove", hoverSpot);
        showHint("🔦 Spotlight follows your pointer. Click 🎯 again to exit.");
      } else {
        document.removeEventListener("mousemove", hoverSpot);
        deactivateSpotlight();
      }
    },
    // 💡 Focus Assistant = click an area to pin the spotlight; click again elsewhere to move it.
    toggleFocusAssistant: function () {
      focusAssistActive = !focusAssistActive;
      setActive("focusAssistantBtn", focusAssistActive);
      if (focusAssistActive) {
        if (focusModeActive) api.toggleFocusMode();          // mutually exclusive
        showOverlay(true);
        document.addEventListener("click", clickSpot, true);
        showHint("💡 Click any area to spotlight it. Click 💡 again to exit.");
      } else {
        document.removeEventListener("click", clickSpot, true);
        deactivateSpotlight();
      }
    },
    toggleCalmingAudio: function () {
      var audio = document.getElementById("synapseCalmAudio");
      if (!audio) {
        audio = document.createElement("audio"); audio.id = "synapseCalmAudio"; audio.loop = true; audio.volume = 0.3;
        audio.innerHTML = '<source src="/static/audio/adhd_calm.mp3" type="audio/mpeg">' +
                          '<source src="/static/audio/relax_sleep.mp3" type="audio/mpeg">' +
                          '<source src="/static/audio/sensory_rain.mp3" type="audio/mpeg">';
        document.body.appendChild(audio);
      }
      if (audio.paused) { audio.play().then(function () { toast("Calming audio playing"); }).catch(function () { toast("Audio unavailable."); }); }
      else { audio.pause(); toast("Calming audio paused"); }
    },
    reset: function () {
      document.body.classList.remove("dark-mode", "high-contrast", "dyslexia-font-active", "reduce-motion", "focus-mode", "synapse-calm-mode");
      fontPct = 100; applyFont();
      ["darkModeBtn", "highContrastBtn", "dyslexiaBtn", "readingPointerBtn", "textToSpeechBtn", "reduceMotionBtn", "focusModeBtn", "focusAssistantBtn", "voiceBtn"].forEach(function (id) { setActive(id, false); });
      focusModeActive = false; focusAssistActive = false;
      document.removeEventListener("mousemove", hoverSpot);
      document.removeEventListener("click", clickSpot, true);
      deactivateSpotlight();
      var line = document.getElementById("synapseReadingPointerLine"); if (line) line.classList.remove("active");
      pointerActive = false; document.removeEventListener("mousemove", movePointer);
      ttsEnabled = false; if (window.speechSynthesis) window.speechSynthesis.cancel(); document.removeEventListener("click", speak);
      var a = document.getElementById("synapseCalmAudio"); if (a) a.pause();
      var menu = document.getElementById("accessBtns"); if (menu) menu.style.display = "none";
      toast("Accessibility reset");
    }
  };

  // ---------- helpers ----------
  function applyFont() {
    var s = document.getElementById("synapse-fs-style") || document.createElement("style");
    s.id = "synapse-fs-style"; s.textContent = "html{font-size:" + fontPct + "%}";
    if (!s.parentNode) document.head.appendChild(s);
  }
  function val(id, d) { var el = document.getElementById(id); return el ? el.value : d; }
  function style(id, color, th) { var el = document.getElementById(id); if (el) { el.style.background = color; el.style.height = th + "px"; el.style.boxShadow = "0 0 " + (th * 3) + "px " + color; } }
  function movePointer(e) { var l = document.getElementById("synapseReadingPointerLine"); if (l && pointerActive) l.style.top = e.clientY + "px"; }
  function speak(e) {
    if (!ttsEnabled) return;
    var t = e.target.textContent || e.target.value;
    if (t && t.trim() && t.length < 500) { window.speechSynthesis.cancel(); var u = new SpeechSynthesisUtterance(t.trim()); u.rate = 0.9; window.speechSynthesis.speak(u); }
  }
  function loadPointer() {
    try { var s = JSON.parse(localStorage.getItem("synapsePointer") || "null"); if (s) { setVal("synapsePointerColor", s.color); setVal("synapsePointerThickness", s.thickness); } } catch (e) {}
    api.updatePointerSettings();
  }
  function setVal(id, v) { var el = document.getElementById(id); if (el && v != null) el.value = v; }
  function restore() {
    try {
      if (localStorage.getItem("darkMode") === "true") api.toggleDark();
      if (localStorage.getItem("highContrast") === "true") api.toggleHighContrast();
      if (localStorage.getItem("dyslexiaFont") === "true") api.toggleDyslexiaFont();
    } catch (e) {}
  }

  // ---------- focus spotlight (self-contained; no focus_assistant.js dependency) ----------
  function showOverlay(on) {
    var ov = document.getElementById("synapseFocusOverlay");
    if (ov) ov.classList.toggle("active", !!on);
  }
  function nearestContainer(el) {
    if (!el || !el.closest) return el;
    return el.closest('.card,.opt,section,article,[class*="container"],[class*="content"],[class*="panel"]') || el;
  }
  function spotlightTarget(el) {
    if (!el || el === spotEl || (el.closest && el.closest("#synapseA11yNav"))) return;
    clearSpotlight();
    spotPrev = { position: el.style.position, zIndex: el.style.zIndex, boxShadow: el.style.boxShadow };
    if (getComputedStyle(el).position === "static") el.style.position = "relative";
    el.style.zIndex = "9999";  // above the .6 overlay (9998), below the navbar (10001)
    el.style.boxShadow = "0 0 0 4px rgba(16,185,129,.9), 0 0 40px rgba(16,185,129,.55)";
    spotEl = el;
  }
  function clearSpotlight() {
    if (!spotEl) return;
    spotEl.style.position = (spotPrev && spotPrev.position) || "";
    spotEl.style.zIndex = (spotPrev && spotPrev.zIndex) || "";
    spotEl.style.boxShadow = (spotPrev && spotPrev.boxShadow) || "";
    spotEl = null; spotPrev = null;
  }
  function deactivateSpotlight() { clearSpotlight(); showOverlay(false); hideHint(); }
  function hoverSpot(e) {
    if (!focusModeActive) return;
    if (e.target.closest && e.target.closest("#synapseA11yNav")) return;  // keep toolbar usable
    spotlightTarget(nearestContainer(e.target));
  }
  function clickSpot(e) {
    if (!focusAssistActive) return;
    if (e.target.closest && e.target.closest("#synapseA11yNav")) return;  // never swallow toolbar clicks
    e.preventDefault(); e.stopPropagation();                              // a click only re-aims the spotlight
    spotlightTarget(nearestContainer(e.target));
  }
  var hintTimer = null;
  function showHint(text) {
    hideHint();
    var h = document.createElement("div");
    h.id = "synapseFocusHint"; h.textContent = text;
    document.body.appendChild(h);
    hintTimer = setTimeout(function () { var el = document.getElementById("synapseFocusHint"); if (el) el.remove(); }, 4000);
  }
  function hideHint() {
    if (hintTimer) { clearTimeout(hintTimer); hintTimer = null; }
    var el = document.getElementById("synapseFocusHint"); if (el) el.remove();
  }

  window.synapseToolbar = api;

  if (document.body) inject();
  else document.addEventListener("DOMContentLoaded", inject);
})();
