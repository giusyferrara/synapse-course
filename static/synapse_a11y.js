/* ================================================================
   SYNAPSE ACCESSIBILITY SUITE v2.0
   External JS — loaded by ALL templates
   
   SAFE: Does NOT replace existing toggle functions.
   Only ADDS: persistence, glow, and new features.
   ================================================================ */
(function() {
  // ================================================================
  // TOAST NOTIFICATIONS — feedback on every button click
  // ================================================================
  window.synapseToast = function(message, duration) {
    duration = duration || 2000;
    var existing = document.getElementById('synapse-toast');
    if (existing) existing.remove();
    var toast = document.createElement('div');
    toast.id = 'synapse-toast';
    toast.textContent = message;
    toast.style.cssText = 'position:fixed;top:60px;left:50%;transform:translateX(-50%);background:#1e293b;color:#e2e8f0;padding:10px 20px;border-radius:10px;font-size:14px;font-weight:600;z-index:999999;box-shadow:0 4px 20px rgba(0,0,0,0.4);border:1px solid #475569;transition:opacity 0.3s;';
    document.body.appendChild(toast);
    setTimeout(function(){ toast.style.opacity = '0'; }, duration - 300);
    setTimeout(function(){ toast.remove(); }, duration);
  };


  'use strict';

  var PREFS_KEY = 'synapse_a11y_prefs';
  var readingMaskActive = false;
  var maskWindowSize = 120;
  var colorOverlayState = 0; // 0=off, 1=warm, 2=cool, 3=rose
  var cursorHighlightActive = false;
  var lineSpacingState = 0; // 0=normal, 1=1.5, 2=2.0
  var calmModeActive = false;
  var dictActive = false;
  var progressActive = false;

  // ================================================================
  // 1. LOCALSTORAGE PERSISTENCE
  // ================================================================
  function saveAllPrefs() {
    try {
      var prefs = {
        darkMode: document.body.classList.contains('dark-mode'),
        dyslexia: document.body.classList.contains('dyslexia-font'),
        highContrast: document.body.classList.contains('high-contrast'),
        reduceMotion: document.body.classList.contains('reduce-motion'),
        lineSpacing: lineSpacingState,
        colorOverlay: colorOverlayState,
        cursorHighlight: cursorHighlightActive,
        calmMode: calmModeActive,
        readingMask: readingMaskActive,
        dictActive: dictActive,
        progressBar: progressActive
      };
      localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
    } catch(e) { /* localStorage might be full or blocked */ }
  }

  function restoreAllPrefs() {
    try {
      var raw = localStorage.getItem(PREFS_KEY);
      if (!raw) return;
      var prefs = JSON.parse(raw);

      // Dark mode
      if (prefs.darkMode && !document.body.classList.contains('dark-mode')) {
        document.body.classList.add('dark-mode');
        localStorage.setItem('darkMode', 'true');
      }
      // Dyslexia
      if (prefs.dyslexia && !document.body.classList.contains('dyslexia-font')) {
        document.body.classList.add('dyslexia-font');
      }
      // High contrast
      if (prefs.highContrast && !document.body.classList.contains('high-contrast')) {
        document.body.classList.add('high-contrast');
      }
      // Reduce motion
      if (prefs.reduceMotion && !document.body.classList.contains('reduce-motion')) {
        document.body.classList.add('reduce-motion');
      }
      // Line spacing
      if (prefs.lineSpacing) {
        lineSpacingState = prefs.lineSpacing;
        applyLineSpacing();
      }
      // Color overlay
      if (prefs.colorOverlay) {
        colorOverlayState = prefs.colorOverlay;
        applyColorOverlay();
      }
      // Cursor highlight
      if (prefs.cursorHighlight) {
        cursorHighlightActive = true;
        var ch = document.getElementById('synapse-cursor-highlight');
        if (ch) ch.classList.add('active');
      }
      // Calm mode
      if (prefs.calmMode) {
        calmModeActive = true;
        document.body.classList.add('synapse-calm-mode');
      }
      // Reading mask
      if (prefs.readingMask) {
        readingMaskActive = true;
        var rm = document.getElementById('synapse-reading-mask');
        if (rm) rm.classList.add('active');
      }
      // Dictionary
      if (prefs.dictActive) {
        dictActive = true;
      }
      // Progress bar
      if (prefs.progressBar) {
        progressActive = true;
        var pb = document.getElementById('synapse-progress-bar');
        if (pb) pb.classList.add('active');
        updateProgressBar();
      }

      // Restore glows
      setTimeout(restoreGlows, 200);

    } catch(e) { /* parse error, ignore */ }
  }

  // ================================================================
  // 2. BUTTON GLOW SYSTEM
  // ================================================================
  var BODY_CLASS_MAP = {
    'Dark Mode': 'dark-mode',
    'Dyslexia Font': 'dyslexia-font-active',
    'High Contrast': 'high-contrast',
    'Focus Mode': 'focus-mode',
    'Reduce Motion': 'reduce-motion',
    'Calm Mode': 'synapse-calm-mode'
  };

  var STATE_FEATURES = [
    'Reading Mask', 'Reading Guide', 'Read Aloud', 'Focus Assistant',
    'Calming Audio', 'Voice Input', 'Line Spacing', 'Color Overlay',
    'Cursor Highlight', 'Dictionary', 'Progress Bar'
  ];

  function getButtonTooltip(btn) {
    return btn.getAttribute('data-tooltip') || btn.getAttribute('title') || '';
  }

  function isFeatureActive(tooltip) {
    // Check body class
    if (BODY_CLASS_MAP[tooltip]) {
      return document.body.classList.contains(BODY_CLASS_MAP[tooltip]);
    }
    // Check JS state for new features
    switch(tooltip) {
      case 'Reading Mask': return readingMaskActive;
      case 'Line Spacing': return lineSpacingState > 0;
      case 'Color Overlay': return colorOverlayState > 0;
      case 'Cursor Highlight': return cursorHighlightActive;
      case 'Calm Mode': return calmModeActive;
      case 'Dictionary': return dictActive;
      case 'Progress Bar': return progressActive;
      default: return null; // unknown - use toggle approach
    }
  }

  function updateGlows() {
    var btns = document.querySelectorAll(
      '.access-menu-inline button, #accessBtns button, #accessMenuInline button, .nav-buttons .access-btn'
    );
    btns.forEach(function(btn) {
      var tooltip = getButtonTooltip(btn);
      if (!tooltip || tooltip === 'Reset All') return;
      var text = (btn.textContent || '').trim();
      if (text === 'A+' || text === 'A-') return;

      var active = isFeatureActive(tooltip);
      if (active === true) {
        btn.classList.add('synapse-on');
      } else if (active === false) {
        btn.classList.remove('synapse-on');
      }
      // If null (unknown), leave as-is (toggle handled by click)
    });
  }

  function restoreGlows() {
    updateGlows();
  }

  function setupGlowListeners() {
    var btns = document.querySelectorAll(
      '.access-menu-inline button, #accessBtns button, #accessMenuInline button, .nav-buttons .access-btn'
    );
    btns.forEach(function(btn) {
      var tooltip = getButtonTooltip(btn);
      if (!tooltip) return;
      var text = (btn.textContent || '').trim();
      // Skip non-toggle buttons
      if (text === 'A+' || text === 'A-' || tooltip === 'Reset All' ||
          tooltip === 'Larger Text' || tooltip === 'Smaller Text') return;

      btn.addEventListener('click', function() {
        // Small delay to let the existing toggle function run first
        setTimeout(function() {
          updateGlows();
          saveAllPrefs();
        }, 100);
      });
    });

    // Reset buttons clear ALL glows
    var resetBtns = document.querySelectorAll('.nav-btn-reset, [data-tooltip="Reset All"], button[onclick*="resetAccessibility"], button[onclick*="resetAllAccessibility"]');
    resetBtns.forEach(function(rb) {
      rb.addEventListener('click', function() {
        setTimeout(function() {
          document.querySelectorAll('.synapse-on').forEach(function(b) {
            b.classList.remove('synapse-on');
          });
          // Reset new feature states
          readingMaskActive = false;
          lineSpacingState = 0;
          colorOverlayState = 0;
          cursorHighlightActive = false;
          calmModeActive = false;
          dictActive = false;
          progressActive = false;
          // Reset DOM
          document.body.classList.remove('synapse-line-spacing-1', 'synapse-line-spacing-2', 'synapse-calm-mode');
          var rm = document.getElementById('synapse-reading-mask');
          if (rm) rm.classList.remove('active');
          var co = document.getElementById('synapse-color-overlay');
          if (co) { co.className = ''; }
          var ch = document.getElementById('synapse-cursor-highlight');
          if (ch) ch.classList.remove('active');
          var pb = document.getElementById('synapse-progress-bar');
          if (pb) pb.classList.remove('active');
          // Close dictionary tooltip
          var dt = document.getElementById('synapse-dict-tooltip');
          if (dt) dt.classList.remove('visible');
          saveAllPrefs();
        }, 100);
      });
    });
  }

  // ================================================================
  // 3. READING MASK (Screen mask following mouse)
  // ================================================================
  function createReadingMask() {
    if (document.getElementById('synapse-reading-mask')) return;
    var container = document.createElement('div');
    container.id = 'synapse-reading-mask';
    container.innerHTML =
      '<div id="synapse-mask-top"></div>' +
      '<div id="synapse-mask-window"></div>' +
      '<div id="synapse-mask-bottom"></div>';
    document.body.appendChild(container);

    document.addEventListener('mousemove', function(e) {
      if (!readingMaskActive) return;
      var half = maskWindowSize / 2;
      var top = Math.max(0, e.clientY - half);
      var bottom = e.clientY + half;
      var vh = window.innerHeight;

      var maskTop = document.getElementById('synapse-mask-top');
      var maskBottom = document.getElementById('synapse-mask-bottom');
      var maskWindow = document.getElementById('synapse-mask-window');

      if (maskTop) {
        maskTop.style.top = '0';
        maskTop.style.height = top + 'px';
      }
      if (maskBottom) {
        maskBottom.style.top = bottom + 'px';
        maskBottom.style.height = (vh - bottom) + 'px';
      }
      if (maskWindow) {
        maskWindow.style.top = top + 'px';
        maskWindow.style.height = maskWindowSize + 'px';
      }
    });
  }

  // Global function for onclick
  window.synapseToggleReadingMask = function() {
    readingMaskActive = !readingMaskActive;
    synapseToast(readingMaskActive ? '\u{1F532} Reading Mask: ON' : '\u{1F532} Reading Mask: OFF');
    var rm = document.getElementById('synapse-reading-mask');
    if (rm) {
      rm.classList.toggle('active', readingMaskActive);
    }
    saveAllPrefs();
  };

  // ================================================================
  // 4. LINE SPACING CONTROL
  // ================================================================
  function applyLineSpacing() {
    document.body.classList.remove('synapse-line-spacing-1', 'synapse-line-spacing-2');
    if (lineSpacingState === 1) {
      document.body.classList.add('synapse-line-spacing-1');
    } else if (lineSpacingState === 2) {
      document.body.classList.add('synapse-line-spacing-2');
    }
  }

  window.synapseToggleLineSpacing = function() {
    lineSpacingState = (lineSpacingState + 1) % 3;
    applyLineSpacing();
    saveAllPrefs();
  };

  // ================================================================
  // 5. COLOR OVERLAY / TINT
  // ================================================================
  function applyColorOverlay() {
    var co = document.getElementById('synapse-color-overlay');
    if (!co) return;
    co.className = '';
    switch(colorOverlayState) {
      case 1: co.className = 'warm'; break;
      case 2: co.className = 'cool'; break;
      case 3: co.className = 'rose'; break;
    }
  }

  function createColorOverlay() {
    if (document.getElementById('synapse-color-overlay')) return;
    var overlay = document.createElement('div');
    overlay.id = 'synapse-color-overlay';
    document.body.appendChild(overlay);
  }

  window.synapseToggleColorOverlay = function() {
    colorOverlayState = (colorOverlayState + 1) % 4;
    applyColorOverlay();
    saveAllPrefs();
  };

  // ================================================================
  // 6. CURSOR HIGHLIGHT
  // ================================================================
  function createCursorHighlight() {
    if (document.getElementById('synapse-cursor-highlight')) return;
    var ch = document.createElement('div');
    ch.id = 'synapse-cursor-highlight';
    document.body.appendChild(ch);

    document.addEventListener('mousemove', function(e) {
      if (!cursorHighlightActive) return;
      ch.style.left = e.clientX + 'px';
      ch.style.top = e.clientY + 'px';
    });
  }

  window.synapseToggleCursorHighlight = function() {
    cursorHighlightActive = !cursorHighlightActive;
    synapseToast(cursorHighlightActive ? '\u{1F7E1} Cursor Highlight: ON — move your mouse!' : '\u{1F7E1} Cursor Highlight: OFF');
    var ch = document.getElementById('synapse-cursor-highlight');
    if (ch) ch.classList.toggle('active', cursorHighlightActive);
    saveAllPrefs();
  };

  // ================================================================
  // 7. BUILT-IN DICTIONARY (double-click word → definition)
  // ================================================================
  var DICTIONARY = {
    // Java fundamentals
    'variable': 'A named container that stores a value in memory. Like a labelled box where you put data.',
    'string': 'A sequence of characters (text) enclosed in double quotes. Example: "Hello World"',
    'int': 'A data type that stores whole numbers (no decimals). Range: -2.1 billion to 2.1 billion.',
    'boolean': 'A data type with only two values: true or false. Used for yes/no decisions.',
    'array': 'A fixed-size container that holds multiple values of the same type, accessed by index (starting at 0).',
    'method': 'A reusable block of code that performs a specific task. Like a recipe you can call by name.',
    'class': 'A blueprint for creating objects. Defines what data an object holds and what it can do.',
    'object': 'An instance of a class. If the class is a cookie cutter, the object is the cookie.',
    'constructor': 'A special method that runs automatically when you create a new object. Sets up initial values.',
    'parameter': 'A variable in a method definition that receives a value when the method is called.',
    'argument': 'The actual value you pass to a method when you call it.',
    'return': 'Sends a value back from a method to whoever called it.',
    'void': 'Means a method does not return any value.',
    'static': 'Belongs to the class itself, not to any specific object. Shared by all instances.',
    'public': 'An access modifier that allows code from anywhere to use this class/method/variable.',
    'private': 'An access modifier that only allows access from within the same class.',
    'inheritance': 'When a child class gets all the methods and variables from a parent class. Like inheriting traits from parents.',
    'polymorphism': 'The ability to use the same method name but have it behave differently depending on the object.',
    'encapsulation': 'Wrapping data and methods together and restricting direct access. Like a capsule protecting its contents.',
    'interface': 'A contract that defines what methods a class must implement, without saying how.',
    'exception': 'An error event that disrupts normal program flow. Can be caught and handled gracefully.',
    'try': 'A block of code where you attempt something that might throw an exception.',
    'catch': 'A block that handles a specific type of exception if one occurs in the try block.',
    'finally': 'A block that always runs after try/catch, whether an exception occurred or not.',
    'loop': 'Code that repeats a block of instructions until a condition is met. Types: for, while, do-while.',
    'iteration': 'One single pass through a loop body.',
    'recursion': 'When a method calls itself. Must have a base case to stop, or it runs forever.',
    'null': 'A special value meaning "no object" or "nothing". Causes NullPointerException if you try to use it.',
    'compile': 'Converting human-readable code into bytecode that the Java Virtual Machine can execute.',
    'debug': 'The process of finding and fixing errors (bugs) in your code.',
    'syntax': 'The grammar rules of a programming language. Like spelling and punctuation in English.',
    'algorithm': 'A step-by-step set of instructions to solve a specific problem.',

    // Security terms
    'vulnerability': 'A weakness in software that an attacker can exploit to gain unauthorized access or cause damage.',
    'exploit': 'A technique or piece of code that takes advantage of a vulnerability to cause unintended behavior.',
    'payload': 'The malicious code or data delivered by an exploit. The actual "attack" part.',
    'injection': 'An attack where malicious data is inserted into a program to trick it into executing unintended commands.',
    'sql': 'Structured Query Language — used to communicate with databases. SQL injection manipulates these queries.',
    'xss': 'Cross-Site Scripting — injecting malicious JavaScript into a webpage that other users will see and execute.',
    'csrf': 'Cross-Site Request Forgery — tricking a logged-in user into performing actions they did not intend.',
    'authentication': 'Verifying WHO you are (proving your identity). Like showing your passport.',
    'authorization': 'Verifying WHAT you can do (permissions). Like checking if your ticket allows VIP access.',
    'session': 'A temporary connection between a user and a server, tracked by a session ID (usually in a cookie).',
    'cookie': 'A small piece of data stored in the browser, sent with every request to the same site.',
    'encryption': 'Scrambling data so only authorized parties can read it. Like writing in a secret code.',
    'hashing': 'Converting data into a fixed-length fingerprint. One-way: you cannot reverse it back to the original.',
    'sanitization': 'Cleaning user input to remove or neutralize dangerous characters before processing.',
    'validation': 'Checking that user input meets expected format and rules before accepting it.',
    'owasp': 'Open Web Application Security Project — a community that publishes the Top 10 web security risks.',
    'cwe': 'Common Weakness Enumeration — a catalogue of known software weakness types (e.g., CWE-79 = XSS).',
    'firewall': 'A network security system that monitors and filters incoming/outgoing traffic based on rules.',
    'patch': 'A software update that fixes a vulnerability or bug.',
    'penetration': 'Penetration testing (pen test) — authorized simulated attack to find vulnerabilities before real attackers do.',
    'brute': 'Brute force — trying every possible combination until the correct one is found (passwords, keys).',
    'phishing': 'A social engineering attack that tricks people into revealing sensitive information via fake messages.',
    'malware': 'Malicious software designed to damage, disrupt, or gain unauthorized access to systems.',
    'ransomware': 'Malware that encrypts your files and demands payment for the decryption key.',
    'pickle': 'Python serialization format. WARNING: pickle.loads() on untrusted data = Remote Code Execution (CWE-502).',
    'deserialization': 'Converting stored/transmitted data back into an object. Insecure deserialization can lead to RCE.',
    'traversal': 'Path traversal — manipulating file paths (../) to access files outside the intended directory.',
    'privilege': 'Privilege escalation — gaining higher access rights than originally authorized.'
  };

  function createDictTooltip() {
    if (document.getElementById('synapse-dict-tooltip')) return;
    var tooltip = document.createElement('div');
    tooltip.id = 'synapse-dict-tooltip';
    tooltip.innerHTML = '<span class="dict-close" onclick="document.getElementById(\'synapse-dict-tooltip\').classList.remove(\'visible\')">&times;</span><span class="dict-term"></span><span class="dict-def"></span>';
    document.body.appendChild(tooltip);
  }

  document.addEventListener('dblclick', function(e) {
    if (!dictActive) return;
    var sel = window.getSelection();
    var word = (sel.toString() || '').trim().toLowerCase().replace(/[^a-z]/g, '');
    if (!word || word.length < 2) return;
    // If word not in dictionary, send to AI chat
    if (!DICTIONARY[word]) {
      var chatInput = document.getElementById('chatInput');
      if (chatInput && typeof sendChat === 'function') {
        chatInput.value = 'What does "' + word + '" mean? Explain simply.';
        sendChat();
        synapseToast('\u{1F4DA} Asked AI about: ' + word);
      } else if (typeof sendMessage === 'function') {
        var ci = document.getElementById('chatInput');
        if (ci) { ci.value = 'What does "' + word + '" mean? Explain simply.'; sendMessage(); }
        synapseToast('\u{1F4DA} Asked AI about: ' + word);
      } else {
        synapseToast('\u{1F4DA} "' + word + '" — not in dictionary. Try asking the AI tutor!');
      }
      return;
    }

    var def = DICTIONARY[word];
    if (!def) return;

    var tooltip = document.getElementById('synapse-dict-tooltip');
    if (!tooltip) return;

    tooltip.querySelector('.dict-term').textContent = word.charAt(0).toUpperCase() + word.slice(1);
    tooltip.querySelector('.dict-def').textContent = def;

    // Position near mouse
    var x = Math.min(e.clientX + 10, window.innerWidth - 340);
    var y = Math.min(e.clientY + 10, window.innerHeight - 200);
    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
    tooltip.classList.add('visible');

    // Auto-hide after 8 seconds
    setTimeout(function() { tooltip.classList.remove('visible'); }, 8000);
  });

  // Close tooltip on click elsewhere
  document.addEventListener('click', function(e) {
    var tooltip = document.getElementById('synapse-dict-tooltip');
    if (tooltip && !tooltip.contains(e.target)) {
      tooltip.classList.remove('visible');
    }
  });

  window.synapseToggleDictionary = function() {
    dictActive = !dictActive;
    synapseToast(dictActive ? '\u{1F4DA} Dictionary: ON — double-click any word!' : '\u{1F4DA} Dictionary: OFF');
    if (!dictActive) {
      var tooltip = document.getElementById('synapse-dict-tooltip');
      if (tooltip) tooltip.classList.remove('visible');
    }
    saveAllPrefs();
  };

  // ================================================================
  // 8. CALM MODE
  // ================================================================
  window.synapseToggleCalmMode = function() {
    calmModeActive = !calmModeActive;
    synapseToast(calmModeActive ? '\u{1F9D8} Calm Mode: ON' : '\u{1F9D8} Calm Mode: OFF');
    document.body.classList.toggle('synapse-calm-mode', calmModeActive);
    saveAllPrefs();
  };

  // ================================================================
  // 9. PROGRESS BAR (scroll-based)
  // ================================================================
  function createProgressBar() {
    if (document.getElementById('synapse-progress-bar')) return;
    var bar = document.createElement('div');
    bar.id = 'synapse-progress-bar';
    bar.innerHTML = '<div id="synapse-progress-fill"></div>';
    document.body.appendChild(bar);

    window.addEventListener('scroll', function() {
      if (!progressActive) return;
      updateProgressBar();
    });
  }

  function updateProgressBar() {
    var fill = document.getElementById('synapse-progress-fill');
    if (!fill) return;
    var scrollTop = window.scrollY || document.documentElement.scrollTop;
    var scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
    var pct = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
    fill.style.width = Math.min(100, pct) + '%';
  }

  window.synapseToggleProgressBar = function() {
    progressActive = !progressActive;
    synapseToast(progressActive ? '\u{1F4CA} Progress Bar: ON — scroll to see it!' : '\u{1F4CA} Progress Bar: OFF');
    var pb = document.getElementById('synapse-progress-bar');
    if (pb) pb.classList.toggle('active', progressActive);
    if (progressActive) updateProgressBar();
    saveAllPrefs();
  };

  // ================================================================
  // 10. FONT SIZE PERSISTENCE
  // ================================================================
  // Hook into existing A+/A- buttons to save font size
  function setupFontSizePersistence() {
    var btns = document.querySelectorAll('[data-tooltip="Larger Text"], [data-tooltip="Smaller Text"], [title="A+"], [title="A-"], [title="Increase Font Size"], [title="Decrease Font Size"], [title="Larger Text"], [title="Smaller Text"]');
    btns.forEach(function(btn) {
      btn.addEventListener('click', function() {
        setTimeout(function() {
          try {
            localStorage.setItem('synapse_fontsize', document.body.style.fontSize || '');
          } catch(e) {}
        }, 100);
      });
    });

    // Restore font size
    try {
      var saved = localStorage.getItem('synapse_fontsize');
      if (saved) document.body.style.fontSize = saved;
    } catch(e) {}
  }

  
  // ================================================================
  // 11. BOOKMARK READING POINTER (click to place, stays there)
  // ================================================================
  var bookmarkActive = false;

  function createBookmark() {
    if (document.getElementById('synapse-bookmark')) return;
    var bm = document.createElement('div');
    bm.id = 'synapse-bookmark';
    document.body.appendChild(bm);

    document.addEventListener('click', function(e) {
      if (!bookmarkActive) return;
      // Ignore clicks on nav, buttons, inputs
      if (e.target.closest('nav') || e.target.closest('button') || 
          e.target.closest('input') || e.target.closest('textarea') ||
          e.target.closest('.chat-panel') || e.target.closest('.access-menu-inline') ||
          e.target.closest('#accessBtns')) return;

      var bm = document.getElementById('synapse-bookmark');
      if (!bm) return;

      // Place bookmark at click position (page coordinates, not viewport)
      var scrollY = window.pageYOffset || document.documentElement.scrollTop;
      var yPos = e.clientY + scrollY;
      bm.style.top = yPos + 'px';
      bm.classList.add('active');
    });
  }

  window.synapseToggleBookmark = function() {
    bookmarkActive = !bookmarkActive;
    document.body.classList.toggle('synapse-bookmark-mode', bookmarkActive);
    if (!bookmarkActive) {
      var bm = document.getElementById('synapse-bookmark');
      if (bm) bm.classList.remove('active');
    }
  };

  // ================================================================
  // INIT
  // ================================================================
  function init() {
    // Create DOM elements for new features
    createReadingMask();
    createColorOverlay();
    createCursorHighlight();
    createDictTooltip();
    createProgressBar();

    // Restore saved preferences
    restoreAllPrefs();

    // Setup glow listeners
    setupGlowListeners();

    // Setup font size persistence
    setupFontSizePersistence();

    // Also save prefs when body classes change (catches existing toggle functions)
    var observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(m) {
        if (m.attributeName === 'class') {
          setTimeout(function() {
            updateGlows();
            saveAllPrefs();
          }, 50);
        }
      });
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });

    console.log('✨ Synapse Accessibility Suite v2.0 loaded');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
