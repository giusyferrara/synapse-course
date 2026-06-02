/* synapse_focus.js — Focus Mode + Focus Assistant, ported VERBATIM from index.html (/app)
   so the mission page and ShopSecure behave EXACTLY like the main app. Presentational only.
   Defines window.toggleFocusMode / window.toggleFocusAssistant / window.synapseFocusReset.
   The container selectors in updateFocusSpotlight are broadened to also match the mission
   and ShopSecure content blocks; everything else mirrors index.html 1:1. */
(function () {
  "use strict";
  if (window.__synapseFocusLoaded) return;
  window.__synapseFocusLoaded = true;

  // --- styles: identical to index.html's focus CSS ---
  var css =
    '.focus-mode-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);backdrop-filter:blur(4px);z-index:9998;display:none;pointer-events:none;transition:opacity .3s ease;}' +
    '.focus-mode-overlay.active{display:block;}' +
    'body.focus-mode main,body.focus-mode .container,body.focus-mode main.container,body.focus-mode .main-content,body.focus-mode .task-panel{position:relative;z-index:9999;}' +
    // toolbar/nav (which holds the focus-off + Reset controls) must stay ABOVE the dim overlay so the off-switch is always visible/reachable. Covers BOTH Focus Mode and Focus Assistant; position:relative makes the z-index actually apply to ShopSecure's static .nav (mirrors index.html's nav at z-index 10001).
    'body.focus-mode nav,body.focus-mode .nav,body.focus-assistant-active nav,body.focus-assistant-active .nav{position:relative;z-index:10002;}' +
    '#focusModeBtn.active,[title="Focus Mode"].active{background:#6366f1!important;color:#fff!important;box-shadow:0 0 15px rgba(99,102,241,.6)!important;}' +
    '[title="Focus Assistant"].active,#focusAssistBtn.active,#focusAssistBtnVisible.active{background:#f59e0b!important;color:#fff!important;box-shadow:0 0 15px rgba(245,158,11,.6)!important;}';
  var st = document.createElement('style');
  st.id = 'synapseFocusCss';
  st.textContent = css;
  (document.head || document.documentElement).appendChild(st);

  function ensureModeOverlay() {
    var ov = document.getElementById('focusModeOverlay');
    if (!ov) {
      ov = document.createElement('div');
      ov.className = 'focus-mode-overlay';
      ov.id = 'focusModeOverlay';
      document.body.appendChild(ov);
    }
    return ov;
  }
  function syncBtn(title, on) {
    document.querySelectorAll('[title="' + title + '"]').forEach(function (b) { b.classList.toggle('active', on); });
  }

  // ===== FOCUS MODE (index.html toggleFocusMode) =====
  var focusModeActive = false;
  window.toggleFocusMode = function () {
    focusModeActive = !focusModeActive;
    var overlay = ensureModeOverlay();
    if (focusModeActive) { overlay.classList.add('active'); document.body.classList.add('focus-mode'); }
    else { overlay.classList.remove('active'); document.body.classList.remove('focus-mode'); }
    syncBtn('Focus Mode', focusModeActive);
  };

  // ===== FOCUS ASSISTANT (index.html toggleFocusAssistant + updateFocusSpotlight) =====
  var focusAssistantActive = false, currentSpotlight = null, focusOverlay = null;
  window.toggleFocusAssistant = function () {
    focusAssistantActive = !focusAssistantActive;
    document.body.classList.toggle('focus-assistant-active', focusAssistantActive);
    if (focusAssistantActive) {
      focusOverlay = document.createElement('div');
      focusOverlay.id = 'focus-assistant-overlay';
      focusOverlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.85);z-index:9998;pointer-events:none;transition:opacity .3s ease;';
      document.body.appendChild(focusOverlay);
      document.addEventListener('click', updateFocusSpotlight, true);
      document.addEventListener('focusin', updateFocusSpotlight, true);
    } else {
      if (focusOverlay) focusOverlay.remove();
      if (currentSpotlight) currentSpotlight.remove();
      currentSpotlight = null; focusOverlay = null;
      document.removeEventListener('click', updateFocusSpotlight, true);
      document.removeEventListener('focusin', updateFocusSpotlight, true);
    }
    syncBtn('Focus Assistant', focusAssistantActive);
  };

  function updateFocusSpotlight(e) {
    if (!focusAssistantActive) return;
    var target = e.target;
    while (target && target !== document.body) {
      if ((target.classList && (target.classList.contains('card') || target.classList.contains('column-card') ||
            target.classList.contains('lesson-panel') || target.classList.contains('cred-box') ||
            target.classList.contains('tab-pane') || target.classList.contains('product-card') ||
            target.classList.contains('finding-card') || target.classList.contains('cred-table') ||
            target.classList.contains('tips-list'))) ||
          target.tagName === 'SECTION' || target.tagName === 'TEXTAREA' || target.tagName === 'INPUT' ||
          target.id === 'main-content') {
        break;
      }
      target = target.parentElement;
    }
    if (!target || target === document.body) return;
    if (currentSpotlight) currentSpotlight.remove();
    var rect = target.getBoundingClientRect();
    currentSpotlight = document.createElement('div');
    currentSpotlight.id = 'focus-spotlight';
    currentSpotlight.style.cssText =
      'position:fixed;top:' + (rect.top - 15) + 'px;left:' + (rect.left - 15) + 'px;' +
      'width:' + (rect.width + 30) + 'px;height:' + (rect.height + 30) + 'px;' +
      'z-index:10000;pointer-events:none;border:3px solid rgba(102,126,234,0.8);border-radius:15px;transition:all .3s ease;background:transparent;';
    document.body.appendChild(currentSpotlight);
    target.style.position = 'relative';
    target.style.zIndex = '9999';
    target.style.background = target.style.background || 'white';
  }

  // Reset hook (mission/ShopSecure call this from their Reset button)
  window.synapseFocusReset = function () {
    if (focusModeActive) window.toggleFocusMode();
    if (focusAssistantActive) window.toggleFocusAssistant();
  };
})();
