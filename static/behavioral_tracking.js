// ============================================
// OBJECTIVE BEHAVIORAL TRACKING
// ============================================
// Tracks ONLY measurable, tangible events.
// NO fake calculations. NO automatic scores.
// NO ADHD/dyslexia scoring.
//
// Collects:
// - Time on page, idle time
// - Click/scroll/keypress events
// - Tab switches
// - Code execution (attempts, errors, success)
// - Help requests
// - Exercise completions
//
// Behavioral data (attention, emotion, stress) comes ONLY from
// self-report widget if user chooses to submit it.
// ============================================

console.log('📊 Objective Behavioral Tracking Initialized');

// ============================================
// SESSION DATA STRUCTURE
// ============================================

// Reuse existing session or create new one
let sessionData = {
  session_id: sessionStorage.getItem('current_session_id') || generateSessionId(),
  user_id: localStorage.getItem('synapse_participant_code') || null,
  course_id: localStorage.getItem('current_course_id') || null,
  start_time: sessionStorage.getItem('session_start_time') || new Date().toISOString(),
  end_time: null,

  // ✅ OBJECTIVE METRICS (always tracked)
  objective_events: {
    clicks: [],
    keypresses: [],
    scrolls: [],
    tab_switches: [],
    code_executions: [],
    help_requests: [],
    exercise_loads: []
  },

  // ✅ SUMMARY STATS (calculated from events)
  summary: {
    total_clicks: 0,
    total_keypresses: 0,
    total_scrolls: 0,
    total_tab_switches: 0,
    code_attempts: 0,
    code_errors: 0,
    code_success: 0,
    hints_requested: 0,
    exercises_completed: 0,
    session_duration_seconds: 0,
    total_idle_seconds: 0
  },

  // ✅ SUBJECTIVE DATA (null until user reports)
  self_reports: []
};

function generateSessionId() {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Store session ID so it persists across page reloads
if (!sessionStorage.getItem('current_session_id')) {
  sessionStorage.setItem('current_session_id', sessionData.session_id);
  sessionStorage.setItem('session_start_time', sessionData.start_time);
  console.log('🆕 New session created:', sessionData.session_id);
} else {
  console.log('♻️ Resuming session:', sessionData.session_id);
}

// Update session when user/course info becomes available
function updateSessionInfo() {
  const newUserId = localStorage.getItem('synapse_participant_code');
  const newCourseId = localStorage.getItem('current_course_id');
  
  if (newUserId && !sessionData.user_id) {
    sessionData.user_id = newUserId;
    console.log('👤 User ID set:', newUserId);
  }
  
  if (newCourseId && !sessionData.course_id) {
    sessionData.course_id = newCourseId;
    console.log('📚 Course ID set:', newCourseId);
  }
}

// Check for updates every few seconds
setInterval(updateSessionInfo, 3000);

// ============================================
// ACTIVITY TRACKING
// ============================================

let lastActivityTime = Date.now();

function updateActivity() {
  lastActivityTime = Date.now();
}

function getIdleTime() {
  return (Date.now() - lastActivityTime) / 1000;
}

// ============================================
// CLICK TRACKING
// ============================================

document.addEventListener('click', (e) => {
  updateActivity();

  const event = {
    timestamp: new Date().toISOString(),
    x: e.clientX,
    y: e.clientY,
    target: e.target.tagName,
    element_id: e.target.id || null,
    element_class: e.target.className || null
  };

  sessionData.objective_events.clicks.push(event);
  sessionData.summary.total_clicks++;

  console.log(`🖱️ Click #${sessionData.summary.total_clicks}:`, e.target.tagName);
});

// ============================================
// KEYPRESS TRACKING
// ============================================

let lastKeypressTime = Date.now();

document.addEventListener('keypress', (e) => {
  updateActivity();

  const now = Date.now();
  const interval = now - lastKeypressTime;

  const event = {
    timestamp: new Date().toISOString(),
    key: e.key === ' ' ? 'SPACE' : (e.key.length === 1 ? 'CHAR' : e.key),
    interval_ms: interval
  };

  sessionData.objective_events.keypresses.push(event);
  sessionData.summary.total_keypresses++;

  lastKeypressTime = now;
});

// ============================================
// SCROLL TRACKING
// ============================================

let lastScrollPosition = window.scrollY;

document.addEventListener('scroll', () => {
  updateActivity();

  const position = window.scrollY;
  const delta = position - lastScrollPosition;

  const event = {
    timestamp: new Date().toISOString(),
    position: position,
    delta: delta,
    direction: delta > 0 ? 'down' : 'up'
  };

  sessionData.objective_events.scrolls.push(event);
  sessionData.summary.total_scrolls++;

  lastScrollPosition = position;
});

// ============================================
// TAB SWITCH TRACKING
// ============================================

let currentTab = null;

function trackTabSwitch(fromTab, toTab) {
  updateActivity();

  const event = {
    timestamp: new Date().toISOString(),
    from_tab: fromTab,
    to_tab: toTab
  };

  sessionData.objective_events.tab_switches.push(event);
  sessionData.summary.total_tab_switches++;

  currentTab = toTab;

  console.log(`📑 Tab switch: ${fromTab} → ${toTab} (Total: ${sessionData.summary.total_tab_switches})`);
}

// Hook into existing switchTab function
const originalSwitchTab = window.switchTab;
if (typeof originalSwitchTab === 'function') {
  window.switchTab = function(tabName) {
    const oldTab = currentTab;
    trackTabSwitch(oldTab, tabName);
    return originalSwitchTab.call(this, tabName);
  };
}

// ============================================
// CODE EXECUTION TRACKING
// ============================================

function trackCodeExecution(code, success, error, executionTimeMs) {
  updateActivity();

  const event = {
    timestamp: new Date().toISOString(),
    code_length: code.length,
    success: success,
    has_error: !!error,
    error_type: error ? (error.includes('Syntax') ? 'syntax' : 'runtime') : null,
    execution_time_ms: executionTimeMs
  };

  sessionData.objective_events.code_executions.push(event);
  sessionData.summary.code_attempts++;

  if (success) {
    sessionData.summary.code_success++;
  } else {
    sessionData.summary.code_errors++;
  }

  console.log(`💻 Code execution #${sessionData.summary.code_attempts}: ${success ? 'SUCCESS' : 'ERROR'}`);
  
  // Save session after code execution (if valid session)
  saveSessionIfValid();
}

// Hook into existing runCode function
const originalRunCode = window.runCode;
if (typeof originalRunCode === 'function') {
  window.runCode = async function() {
    const code = document.getElementById('codeEditor')?.value || '';
    const startTime = Date.now();

    try {
      const result = await originalRunCode.call(this);
      const execTime = Date.now() - startTime;

      // Determine success
      const outputConsole = document.getElementById('outputConsole');
      const output = outputConsole?.textContent || '';
      const success = !output.includes('Error') && !output.includes('Traceback');

      trackCodeExecution(code, success, success ? null : output, execTime);

      return result;
    } catch (error) {
      const execTime = Date.now() - startTime;
      trackCodeExecution(code, false, error.message, execTime);
      throw error;
    }
  };
}

// ============================================
// HELP REQUEST TRACKING
// ============================================

function trackHelpRequest(type, context) {
  updateActivity();

  const event = {
    timestamp: new Date().toISOString(),
    type: type,
    context: context || null
  };

  sessionData.objective_events.help_requests.push(event);
  sessionData.summary.hints_requested++;

  console.log(`🆘 Help request: ${type} (Total: ${sessionData.summary.hints_requested})`);
  
  // Save session after help request (if valid session)
  saveSessionIfValid();
}

// Hook into existing help functions
const originalGetAIHint = window.getAIHint;
if (typeof originalGetAIHint === 'function') {
  window.getAIHint = function() {
    trackHelpRequest('ai_hint', currentCourse);
    return originalGetAIHint.call(this);
  };
}

// ============================================
// EXERCISE TRACKING
// ============================================

function trackExerciseLoad(exerciseId, exerciseTitle) {
  updateActivity();

  const event = {
    timestamp: new Date().toISOString(),
    exercise_id: exerciseId,
    exercise_title: exerciseTitle
  };

  sessionData.objective_events.exercise_loads.push(event);

  console.log(`📝 Exercise loaded: ${exerciseTitle}`);
}

function trackExerciseComplete(exerciseId) {
  sessionData.summary.exercises_completed++;
  console.log(`✅ Exercise completed: ${exerciseId} (Total: ${sessionData.summary.exercises_completed})`);
  
  // Save session after exercise completion (if valid session)
  saveSessionIfValid();
}

// ============================================
// SELF-REPORT INTEGRATION
// ============================================

async function submitSelfReport() {
  console.log('📊 Self-report submission...');

  const feeling = document.getElementById('feelingDropdown')?.value;
  const attention = parseInt(document.getElementById('attentionSlider')?.value);
  const difficulty = parseInt(document.getElementById('difficultySlider')?.value);
  const emotion = parseInt(document.getElementById('emotionSlider')?.value);
  const stress = parseInt(document.getElementById('stressSlider')?.value);

  if (!feeling) {
    alert('Please select how you are feeling');
    return;
  }

  const selfReport = {
    timestamp: new Date().toISOString(),
    feeling: feeling,
    attention: attention,
    difficulty: difficulty,
    emotion: emotion,
    stress: stress,
    current_idle_time: Math.round(getIdleTime())
  };

  sessionData.self_reports.push(selfReport);

  console.log('✅ Self-report added:', selfReport);

  // Send to server
  try {
    await fetch('/api/research/self_report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionData.session_id,
        user_id: sessionData.user_id,
        self_report: selfReport
      })
    });

    // Success feedback
    const panel = document.getElementById('selfReportPanel');
    if (panel) {
      panel.innerHTML = `
        <div style="text-align: center; padding: 40px;">
          <div style="font-size: 48px;">✅</div>
          <h3 style="color: #10b981;">Thank You!</h3>
          <p>Reports: ${sessionData.self_reports.length}</p>
        </div>
      `;
      setTimeout(() => {
        panel.style.display = 'none';
      }, 2000);
    }
    
    // Save session after self-report
    saveSessionIfValid();
    
  } catch (error) {
    console.error('❌ Self-report error:', error);
    alert('Could not submit feedback.');
  }
}

// Make function available globally
window.submitSelfReport = submitSelfReport;

// ============================================
// SESSION SAVE (SMART SAVING)
// ============================================

let lastSaveTime = 0;
const SAVE_COOLDOWN = 30000; // Don't save more than once per 30 seconds

async function saveSession() {
  // Calculate session duration
  const now = new Date();
  sessionData.end_time = now.toISOString();
  const startTime = new Date(sessionData.start_time);
  sessionData.summary.session_duration_seconds = Math.round((now - startTime) / 1000);
  sessionData.summary.total_idle_seconds = Math.round(getIdleTime());

  console.log('💾 Saving session data...', {
    session_id: sessionData.session_id,
    user_id: sessionData.user_id,
    course_id: sessionData.course_id,
    duration: sessionData.summary.session_duration_seconds + 's',
    clicks: sessionData.summary.total_clicks,
    code_attempts: sessionData.summary.code_attempts,
    self_reports: sessionData.self_reports.length
  });

  try {
    const response = await fetch('/api/research/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sessionData)
    });
    
    if (response.ok) {
      console.log('✅ Session saved successfully');
      lastSaveTime = Date.now();
    } else {
      console.error('❌ Session save failed:', response.status);
    }
  } catch (error) {
    console.error('❌ Session save error:', error);
  }
}

function saveSessionIfValid() {
  // 🚫 DON'T SAVE if no user or no course
  if (!sessionData.user_id || !sessionData.course_id) {
    console.log('⏸️ Skipping save - no user or course set');
    return;
  }

  // 🚫 DON'T SAVE if no meaningful activity
  const hasActivity = 
    sessionData.summary.total_clicks > 5 ||
    sessionData.summary.code_attempts > 0 ||
    sessionData.self_reports.length > 0 ||
    sessionData.summary.exercises_completed > 0;

  if (!hasActivity) {
    console.log('⏸️ Skipping save - no meaningful activity yet');
    return;
  }

  // 🚫 DON'T SAVE if saved recently (cooldown)
  const timeSinceLastSave = Date.now() - lastSaveTime;
  if (timeSinceLastSave < SAVE_COOLDOWN) {
    console.log(`⏸️ Skipping save - cooldown (${Math.round(timeSinceLastSave/1000)}s ago)`);
    return;
  }

  // ✅ All checks passed - save!
  saveSession();
}

// ✅ Save on page unload (only if valid session)
window.addEventListener('beforeunload', () => {
  if (sessionData.user_id && sessionData.course_id) {
    // Use sendBeacon for reliable save on page unload
    const blob = new Blob([JSON.stringify(sessionData)], { type: 'application/json' });
    navigator.sendBeacon('/api/research/session', blob);
  }
});

// ============================================
// PERIODIC LOG (for debugging)
// ============================================

setInterval(() => {
  console.log('📊 SESSION STATS:', {
    session_id: sessionData.session_id.substring(0, 20) + '...',
    user_id: sessionData.user_id || 'NOT SET',
    course_id: sessionData.course_id || 'NOT SET',
    duration: Math.round((Date.now() - new Date(sessionData.start_time)) / 1000) + 's',
    clicks: sessionData.summary.total_clicks,
    keypresses: sessionData.summary.total_keypresses,
    scrolls: sessionData.summary.total_scrolls,
    tab_switches: sessionData.summary.total_tab_switches,
    code_attempts: sessionData.summary.code_attempts,
    errors: sessionData.summary.code_errors,
    success_rate: sessionData.summary.code_attempts > 0
      ? Math.round((sessionData.summary.code_success / sessionData.summary.code_attempts) * 100) + '%'
      : 'N/A',
    self_reports: sessionData.self_reports.length,
    idle_time: Math.round(getIdleTime()) + 's'
  });
}, 30000); // Every 30 seconds

console.log('✅ Objective Behavioral Tracking Active');
console.log('📊 Tracking: clicks, keypresses, scrolls, tabs, code execution, help requests');
console.log('🧠 Behavioral data: ONLY from self-report widget (optional)');
console.log('❌ NO fake calculations, NO automatic scoring');
console.log('💾 Smart saving: Only when user_id + course_id set + meaningful activity');
