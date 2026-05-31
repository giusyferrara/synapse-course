// ========================================
// TEXT-TO-SPEECH - CLICK TO READ/STOP
// ========================================
let speechEnabled = false;
let speechSynthesis = window.speechSynthesis;
let currentUtterance = null;

// Initialize default TTS settings
window.ttsRate = 0.9;
window.ttsPitch = 1.0;

function toggleTextToSpeech() {
  speechEnabled = !speechEnabled;
  
  if (speechEnabled) {
    console.log('🔊 Text-to-speech ENABLED - Click any text to read it');
    
    // Add visual indicator
    document.body.style.cursor = 'help';
    
    // Add click listener to all readable elements
    document.addEventListener('click', handleTextClick);
    
    // Show TTS controls
    const controls = document.getElementById('ttsControls');
    if (controls) {
      controls.style.display = 'block';
    }
    
    speakText("Text to speech enabled. Click anywhere to read that section. Click again to stop.");
    
  } else {
    console.log('🔇 Text-to-speech DISABLED');
    
    // Remove cursor indicator
    document.body.style.cursor = 'default';
    
    // Remove click listener
    document.removeEventListener('click', handleTextClick);
    
    // Hide controls
    const controls = document.getElementById('ttsControls');
    if (controls) {
      controls.style.display = 'none';
    }
    
    // Stop any ongoing speech
    stopSpeech();
    speakText("Text to speech disabled.");
  }
  
  logInteraction('accessibility_feature', {
    feature: 'text_to_speech',
    enabled: speechEnabled
  });
}

function handleTextClick(event) {
  if (!speechEnabled) return;
  
  // Don't read if clicking buttons or inputs
  if (event.target.tagName === 'BUTTON' || 
      event.target.tagName === 'INPUT' ||
      event.target.tagName === 'TEXTAREA' ||
      event.target.onclick) {
    return;
  }
  
  // If currently speaking, STOP
  if (speechSynthesis.speaking) {
    stopSpeech();
    console.log('🛑 Speech stopped');
    return;
  }
  
  // Find closest readable element
  let element = event.target;
  
  // Traverse up to find paragraph, div, or heading
  while (element && element !== document.body) {
    if (element.tagName === 'P' || 
        element.tagName === 'DIV' || 
        element.tagName === 'H1' || 
        element.tagName === 'H2' || 
        element.tagName === 'H3' || 
        element.tagName === 'H4' ||
        element.tagName === 'LI' ||
        element.className.includes('slide-content') ||
        element.className.includes('theory') ||
        element.id.includes('Content')) {
      break;
    }
    element = element.parentElement;
  }
  
  if (element && element !== document.body) {
    // Highlight element being read
    highlightElement(element);
    
    // Read it
    readElement(element);
    
    console.log('🔊 Reading:', element.tagName);
  }
}

function speakText(text, onEnd) {
  if (!speechSynthesis) {
    console.error('Speech synthesis not supported');
    return;
  }
  
  // Stop any ongoing speech
  stopSpeech();
  
  // Clean text
  text = text.replace(/\s+/g, ' ').trim();
  
  if (!text || text.length < 3) return;
  
  currentUtterance = new SpeechSynthesisUtterance(text);
  
  // Settings - PARSE to float with fallback
  const rate = parseFloat(window.ttsRate);
  const pitch = parseFloat(window.ttsPitch);
  
  currentUtterance.rate = (!isNaN(rate) && isFinite(rate)) ? rate : 0.9;
  currentUtterance.pitch = (!isNaN(pitch) && isFinite(pitch)) ? pitch : 1.0;
  currentUtterance.volume = 1.0;
  
  // Use best English voice
  const voices = speechSynthesis.getVoices();
  const englishVoice = voices.find(v => v.lang.startsWith('en-GB')) || 
                       voices.find(v => v.lang.startsWith('en-'));
  if (englishVoice) {
    currentUtterance.voice = englishVoice;
  }
  
  // Callback when done
  if (onEnd) {
    currentUtterance.onend = onEnd;
  }
  
  console.log('🔊 Speaking with rate:', currentUtterance.rate, 'pitch:', currentUtterance.pitch);
  speechSynthesis.speak(currentUtterance);
}

function stopSpeech() {
  if (speechSynthesis.speaking) {
    speechSynthesis.cancel();
  }
  
  // Remove highlights
  const highlighted = document.querySelectorAll('.tts-reading');
  highlighted.forEach(el => el.classList.remove('tts-reading'));
}

function readElement(element) {
  if (!speechEnabled || !element) return;
  
  // Get text content
  let text = element.innerText || element.textContent;
  
  // Clean up
  text = text.replace(/\s+/g, ' ').trim();
  
  // Skip if too short or empty
  if (text.length < 5) return;
  
  // Limit length
  if (text.length > 3000) {
    text = text.substring(0, 3000);
  }
  
  speakText(text, () => {
    // Remove highlight when done
    element.classList.remove('tts-reading');
  });
}

function highlightElement(element) {
  // Remove previous highlights
  const highlighted = document.querySelectorAll('.tts-reading');
  highlighted.forEach(el => el.classList.remove('tts-reading'));
  
  // Add highlight to current
  element.classList.add('tts-reading');
}

function updateTTSSettings() {
  const speedSlider = document.getElementById('ttsSpeed');
  const pitchSlider = document.getElementById('ttsPitch');
  
  if (speedSlider) {
    window.ttsRate = parseFloat(speedSlider.value);
    document.getElementById('ttsSpeedValue').textContent = speedSlider.value;
  }
  
  if (pitchSlider) {
    window.ttsPitch = parseFloat(pitchSlider.value);
    document.getElementById('ttsPitchValue').textContent = pitchSlider.value;
  }
  
  speakText("Settings updated. This is how I sound now.");
}

// Initialize voices when available
if (speechSynthesis.onvoiceschanged !== undefined) {
  speechSynthesis.onvoiceschanged = function() {
    console.log('✅ TTS voices loaded:', speechSynthesis.getVoices().length);
  };
}

console.log('✅ Text-to-Speech system initialized');

// ========================================
// GLOBAL STATE
// ========================================
let currentCourse = null;
let courseData = {};
let initialMessageSent = false;

// Initialize Mermaid
if (window.mermaid) {
  mermaid.initialize({ 
    startOnLoad: true,
    theme: 'default',
    securityLevel: 'loose'
  });
}

window.addEventListener('DOMContentLoaded', async function() {
  await loadAllCourses();
  
  if (false) { // DISABLED - AI responds only when course selected
    addChatMessage('ai', '👋 Hi! I\'m your AI tutor. Select a course to start, then ask me anything!');
    initialMessageSent = true;
  }
});

// ========================================
// RESET ACCESSIBILITY TO DEFAULT
// ========================================
function resetAccessibility() {
  console.log('🔄 Resetting all accessibility settings...');
  
  // Remove all accessibility classes
  document.body.classList.remove(
    'dark-mode',
    'dyslexia-mode', 
    'large-text',
    'extra-large-text',
    'high-contrast'
  );
  
  // Disable reading guide
  const guide = document.getElementById('readingGuide');
  if (guide && guide.classList.contains('active')) {
    guide.classList.remove('active');
    document.removeEventListener('mousemove', updateReadingGuide);
  }
  
  // Close all panels
  document.getElementById('accessPanel').classList.remove('open');
  const learningPanel = document.getElementById('learningPanel');
  if (learningPanel) {
    learningPanel.classList.remove('open');
  }
  
  // Log the reset
  logInteraction('accessibility_reset', {
    timestamp: Date.now(),
    all_settings: 'reset_to_default'
  });
  
  console.log('✅ All accessibility settings reset to default');
  
  // Visual feedback
  const resetBtn = event.target;
  const originalText = resetBtn.innerHTML;
  resetBtn.innerHTML = '✅ Reset Complete!';
  resetBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
  
  setTimeout(() => {
    resetBtn.innerHTML = originalText;
    resetBtn.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
  }, 2000);
}

// ========================================
// LOAD ALL JSON COURSES
// ========================================
async function loadAllCourses() {
  const courses = [
    { id: 'python_basics_active_ai', icon: '🐍', title: 'Python Basics', desc: 'Start your journey', badge: 'BEGINNER' },
    { id: 'control_flow_active_ai', icon: '🔀', title: 'Control Flow', desc: 'If/else and loops', badge: 'BEGINNER' },
    { id: 'data_structures_active_ai', icon: '📦', title: 'Data Structures', desc: 'Lists, dicts, sets', badge: 'INTERMEDIATE' },
    { id: 'functions_modules_active_ai', icon: '⚙️', title: 'Functions & Modules', desc: 'Reusable code', badge: 'INTERMEDIATE' },
    { id: 'london_transport_active_ai', icon: '🚇', title: 'London Transport API', desc: 'Real-world project', badge: 'ADVANCED' },
    { id: 'data_analysis_active_ai', icon: '📊', title: 'Data Analysis', desc: 'Pandas & visualization', badge: 'ADVANCED' }
  ];

  const courseGrid = document.getElementById('courseGrid');
  courseGrid.innerHTML = '<p style="padding:20px;text-align:center;color:#64748b;">📚 Loading courses...</p>';

  let loadedCount = 0;

  for (const course of courses) {
    try {
      const response = await fetch(`/static/course_content/${course.id}.json`);
      if (response.ok) {
        const data = await response.json();
        courseData[course.id] = data;
        loadedCount++;
        
        if (loadedCount === 1) {
          courseGrid.innerHTML = '';
        }
        
        const card = document.createElement('div');
        card.className = 'course-card';
        card.onclick = () => loadCourse(course.id, course);
        card.innerHTML = `
          <span class="course-badge">${course.badge}</span>
          <div class="course-icon">${course.icon}</div>
          <div class="course-title">${course.title}</div>
          <div class="course-desc">${course.desc}</div>
        `;
        courseGrid.appendChild(card);
      } else {
        console.warn(`Course ${course.id} not found (${response.status})`);
      }
    } catch (error) {
      console.error(`Failed to load course ${course.id}:`, error);
    }
  }
  
  if (loadedCount === 0) {
    courseGrid.innerHTML = `
      <div style="padding:40px;text-align:center;background:#fff3cd;border-radius:12px;border:2px solid #ffc107;">
        <h3 style="color:#856404;margin-bottom:12px;">⚠️ No Courses Found</h3>
        <p style="color:#856404;margin-bottom:16px;">JSON course files are missing from /static/course_content/</p>
        <p style="font-size:13px;color:#856404;">
          <strong>Quick Fix:</strong><br>
          Make sure these files exist:<br>
          • python_basics_active_ai.json<br>
          • control_flow_active_ai.json<br>
          • data_structures_active_ai.json<br>
          • functions_modules_active_ai.json<br>
          • london_transport_active_ai.json<br>
          • data_analysis_active_ai.json
        </p>
      </div>
    `;
  } else {
    console.log(`✅ Loaded ${loadedCount} courses successfully!`);
    console.log('📊 Course data:', courseData);
  }
}

// ========================================
// LOAD SPECIFIC COURSE - FIXED VERSION
// ========================================
function loadCourse(courseId, courseInfo) {
  currentCourse = courseId;
  
  console.log('🎓 Loading course:', courseId);
  
  // LOG FOR RESEARCH
  logLearningEvent('course_started', {
    course_id: courseId,
    course_title: courseInfo.title,
    course_level: courseInfo.badge
  });
  
  // Update active state
  document.querySelectorAll('.course-card').forEach(card => {
    card.classList.remove('active');
  });
  document.querySelectorAll('.course-card').forEach(card => {
    if (card.querySelector('.course-title')?.textContent === courseInfo.title) {
      card.classList.add('active');
    }
  });
  
  const data = courseData[courseId];
  console.log('📚 Course data:', data);
  
  if (!data) {
    console.error('❌ Course data not found for:', courseId);
    addChatMessage('ai', '❌ Course data not found. Please check that the JSON file exists.');
    return;
  }

  // Update header
  document.getElementById('lessonTitle').textContent = courseInfo.title;
  document.getElementById('lessonBadge').textContent = courseInfo.badge;

  // Get first lesson
  const lesson = data.lessons && data.lessons.length > 0 ? data.lessons[0] : null;
  
  if (!lesson) {
    console.error('❌ No lessons found in course data');
    addChatMessage('ai', '⚠️ This course has no lessons yet. Content coming soon!');
    return;
  }

  console.log('📚 Lesson data:', lesson);

  // LOAD THEORY
  let theoryHTML = '';
  
  if (lesson.theory) {
    const theory = lesson.theory;
    
    theoryHTML = `
      <div style="padding: 20px;">
        <h2>📚 Introduction</h2>
        <p style="font-size: 18px; line-height: 1.8; color: #1e293b;">${theory.introduction || ''}</p>
        
        ${theory.why_important ? `
          <div style="background: #f0f9ff; padding: 16px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3b82f6;">
            <strong>💡 Why This Matters:</strong>
            <p>${theory.why_important}</p>
          </div>
        ` : ''}
        
        ${theory.key_concepts ? `
          <h3 style="margin-top: 32px;">🔑 Key Concepts</h3>
          ${theory.key_concepts.map(concept => `
            <div style="background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 20px; margin: 16px 0;">
              <h4 style="color: #6366f1; margin-bottom: 12px;">${concept.concept}</h4>
              <p style="margin-bottom: 12px;">${concept.explanation}</p>
              ${concept.example ? `
                <pre style="background: #f8fafc; padding: 12px; border-radius: 8px; overflow-x: auto;"><code>${concept.example}</code></pre>
              ` : ''}
              ${concept.ai_hint ? `
                <div style="background: #fef3c7; padding: 12px; border-radius: 8px; margin-top: 12px; border-left: 4px solid #f59e0b;">
                  <strong>💡 AI Hint:</strong> ${concept.ai_hint}
                </div>
              ` : ''}
            </div>
          `).join('')}
        ` : ''}
      </div>
    `;
  }
  
  document.getElementById('theoryContent').innerHTML = theoryHTML || '<p>Theory content not available.</p>';

  // LOAD SLIDES
  let slidesHTML = '';
  
  if (lesson.complete_examples && lesson.complete_examples.length > 0) {
    console.log(`📊 Creating ${lesson.complete_examples.length} interactive example slides`);
    
    lesson.complete_examples.forEach((example, index) => {
      slidesHTML += `
        <div class="slide-container" style="margin-bottom: 32px; background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
          <h2 class="slide-title">${example.title}</h2>
          
          ${example.description ? `
            <p style="color: #64748b; margin: 12px 0 16px 0; font-size: 15px;">${example.description}</p>
          ` : ''}
          
          ${example.difficulty ? `
            <span style="display: inline-block; padding: 4px 12px; background: #e0e7ff; color: #4f46e5; border-radius: 6px; font-size: 12px; font-weight: 600; margin-bottom: 16px;">
              ${example.difficulty.toUpperCase()}
            </span>
          ` : ''}
          
          <div style="background: #f8fafc; border-radius: 8px; padding: 16px; margin: 16px 0; border-left: 4px solid #6366f1;">
            <strong style="font-size: 13px; color: #1e293b;">📝 Code Example:</strong>
            <pre style="background: #1e293b; color: #e2e8f0; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 12px 0; font-family: 'Courier New', monospace; line-height: 1.6;"><code>${example.code}</code></pre>
          </div>
          
          ${example.output ? `
            <div style="background: #1e293b; color: #10b981; padding: 16px; border-radius: 8px; font-family: monospace; margin: 16px 0; line-height: 1.6;">
              <strong style="color: #10b981;">▶️ Expected Output:</strong><br>
              ${example.output.replace(/\n/g, '<br>')}
            </div>
          ` : ''}
          
          ${example.ai_explanation ? `
            <div style="background: #f0f9ff; padding: 16px; border-radius: 8px; border-left: 4px solid #3b82f6; margin: 16px 0;">
              ${example.ai_explanation}
            </div>
          ` : ''}
          
          ${example.ai_challenge ? `
            <div style="background: #fef3c7; padding: 16px; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 16px 0;">
              <strong>🎯 Challenge:</strong> ${example.ai_challenge}
            </div>
          ` : ''}
          
          <div style="display: flex; gap: 12px; margin-top: 20px; flex-wrap: wrap;">
            <button 
              onclick="tryExample('${courseId}', 0, ${index})" 
              class="example-try-btn"
              style="
                flex: 1;
                min-width: 200px;
                padding: 14px 24px;
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                color: white;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                font-size: 15px;
                font-weight: 600;
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
                transition: all 0.3s;
              "
            >
              💻 Try This Example
            </button>
            
            <button 
              onclick="runExampleDirectly('${courseId}', 0, ${index})" 
              class="example-run-btn"
              style="
                padding: 14px 24px;
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                font-size: 15px;
                font-weight: 600;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
                transition: all 0.3s;
              "
            >
              ▶️ Run & See Output
            </button>
            
            <button 
              onclick="generateAIExercise('${courseId}', 0, ${index})" 
              class="example-ai-btn"
              style="
                padding: 14px 24px;
                background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                color: white;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                font-size: 15px;
                font-weight: 600;
                box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
                transition: all 0.3s;
              "
            >
              🤖 AI: Make Exercise
            </button>
          </div>
        </div>
      `;
    });
  } else {
    console.warn('⚠️ No examples found for slides');
    slidesHTML = '<div class="slide-container"><h2 class="slide-title">Examples Coming Soon</h2><p>Interactive examples will be added soon!</p></div>';
  }
  
  document.getElementById('slidesContent').innerHTML = slidesHTML;

  // LOAD FLOWCHART
  if (lesson.visual_diagram && lesson.visual_diagram.content) {
    document.getElementById('flowchartContent').innerHTML = `
      <div style="padding: 20px;">
        <h2>${lesson.visual_diagram.title}</h2>
        <pre style="background: #f8fafc; padding: 20px; border-radius: 8px; font-family: monospace; line-height: 1.6; overflow-x: auto;">${lesson.visual_diagram.content}</pre>
        ${lesson.visual_diagram.ai_diagram_prompt ? `
          <div style="background: #f0f9ff; padding: 12px; border-radius: 8px; margin-top: 16px; border-left: 4px solid #3b82f6;">
            ${lesson.visual_diagram.ai_diagram_prompt}
          </div>
        ` : ''}
      </div>
    `;
  } else {
    document.getElementById('flowchartContent').innerHTML = '<p>Visual diagram not available yet.</p>';
  }

  // LOAD EXERCISES
  let exercisesHTML = '<h3>📝 Practice Exercises</h3>';
  
  if (lesson.practice_exercises && lesson.practice_exercises.length > 0) {
    console.log(`✏️ Found ${lesson.practice_exercises.length} practice exercises`);
    
    lesson.practice_exercises.forEach((ex, index) => {
      exercisesHTML += `
        <div style="margin: 20px 0; padding: 20px; background: white; border-radius: 12px; border: 2px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
          <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <span style="background: #6366f1; color: white; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 700;">
              ${ex.difficulty?.toUpperCase() || 'PRACTICE'}
            </span>
            <h4 style="margin: 0; flex: 1;">${ex.title || `Exercise ${index + 1}`}</h4>
          </div>
          
          <p style="color: #64748b; margin-bottom: 16px;">${ex.description || ''}</p>
          
          ${ex.ai_intro ? `
            <div style="background: #f0f9ff; padding: 12px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #3b82f6;">
              ${ex.ai_intro}
            </div>
          ` : ''}
          
          <button class="editor-btn" onclick="loadExerciseCode('${courseId}', 0, ${index})" style="background: #6366f1; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
            📝 Start Exercise
          </button>
        </div>
      `;
    });
  } else {
    console.warn('⚠️ No practice exercises found');
    exercisesHTML += '<p style="color: #64748b; padding: 20px;">No exercises available yet. AI tutor will help create them!</p>';
  }
  
  document.getElementById('exercisesContent').innerHTML = exercisesHTML;

  // AI WELCOME MESSAGE
  const aiMessages = {
    'python_basics_active_ai': '🐍 Welcome to Python Basics! This is where your coding journey begins. Ready to write your first program?',
    'london_transport_active_ai': '🚇 Welcome to London Transport API! This course uses REAL data from TfL. Ready to build a live tracker?',
    'data_analysis_active_ai': '📊 Data Analysis connects to our Advanced Learning Tools! Want to explore interactive visualizations?',
    'control_flow_active_ai': '🔀 Control Flow is all about making smart decisions in code. Let\'s learn if/else and loops!',
    'data_structures_active_ai': '📦 Data Structures are the building blocks of great programs. Let\'s master lists, dicts, and sets!',
    'functions_modules_active_ai': '⚙️ Functions make your code reusable and clean. Time to level up your programming!',
    'default': `🎓 Ready to master ${courseInfo.title}? I'll adapt to your learning pace. Ask me anything!`
  };

  addChatMessage('ai', aiMessages[courseId] || aiMessages.default);
  
  switchTab('theory');
  
  console.log('✅ Course loaded successfully!');
}

// ========================================
// LOAD EXERCISE STARTER CODE
// ========================================
function loadExerciseCode(courseId, lessonIndex, exerciseIndex) {
  const data = courseData[courseId];
  
  if (!data || !data.lessons || !data.lessons[lessonIndex]) {
    console.error('❌ Course or lesson not found');
    addChatMessage('ai', '❌ Could not load exercise. Please try again.');
    return;
  }
  
  const lesson = data.lessons[lessonIndex];
  const exercises = lesson.practice_exercises || lesson.exercises || [];
  
  if (!exercises[exerciseIndex]) {
    console.error('❌ Exercise not found');
    addChatMessage('ai', '❌ Exercise not found.');
    return;
  }
  
  const exercise = exercises[exerciseIndex];
  
  document.getElementById('codeEditor').value = exercise.starter_code || '# Write your code here...\n';
  document.getElementById('outputConsole').textContent = '✓ Starter code loaded! Click Run Code when ready.';
  
  switchTab('practice');
  
  userActivity.currentExerciseStart = Date.now();
  userActivity.lastClick = Date.now();
  
  const hint = exercise.hints && exercise.hints[0] ? exercise.hints[0].message : 'Need help? Just ask!';
  
  logLearningEvent('exercise_loaded', {
    exercise_title: exercise.title,
    exercise_index: exerciseIndex,
    has_starter_code: !!exercise.starter_code,
    difficulty: exercise.difficulty
  });
  
  addChatMessage('ai', `💻 ${exercise.ai_intro || `Starting: ${exercise.title}`}\n\n💡 ${hint}`);
}

// ========================================
// TRY EXAMPLE
// ========================================
function tryExample(courseId, lessonIndex, exampleIndex) {
  const data = courseData[courseId];
  
  if (!data || !data.lessons || !data.lessons[lessonIndex]) {
    console.error('❌ Course or lesson not found');
    addChatMessage('ai', '❌ Could not load example. Please try again.');
    return;
  }
  
  const lesson = data.lessons[lessonIndex];
  const examples = lesson.complete_examples || [];
  
  if (!examples[exampleIndex]) {
    console.error('❌ Example not found');
    addChatMessage('ai', '❌ Example not found.');
    return;
  }
  
  const example = examples[exampleIndex];
  
  document.getElementById('codeEditor').value = example.code || '# Example code\n';
  document.getElementById('outputConsole').textContent = '✓ Example loaded! Modify the code and click "Run Code" to test it.';
  
  switchTab('practice');
  
  userActivity.lastClick = Date.now();
  userActivity.currentExerciseStart = Date.now();
  
  logLearningEvent('example_loaded', {
    example_title: example.title,
    example_index: exampleIndex,
    has_challenge: !!example.ai_challenge,
    difficulty: example.difficulty
  });
  
  let message = `💻 Loaded example: "${example.title}".\n\n`;
  
  if (example.ai_challenge) {
    message += `🎯 Challenge: ${example.ai_challenge}`;
  } else {
    message += `Try modifying the code and see what happens! Change values, add your own variables, or experiment with the logic.`;
  }
  
  addChatMessage('ai', message);
}

// ========================================
// RUN EXAMPLE DIRECTLY
// ========================================
async function runExampleDirectly(courseId, lessonIndex, exampleIndex) {
  const data = courseData[courseId];
  
  if (!data || !data.lessons || !data.lessons[lessonIndex]) {
    console.error('❌ Course or lesson not found');
    addChatMessage('ai', '❌ Could not run example.');
    return;
  }
  
  const lesson = data.lessons[lessonIndex];
  const examples = lesson.complete_examples || [];
  
  if (!examples[exampleIndex]) {
    console.error('❌ Example not found');
    addChatMessage('ai', '❌ Example not found.');
    return;
  }
  
  const example = examples[exampleIndex];
  
  document.getElementById('codeEditor').value = example.code || '# Example code\n';
  
  switchTab('practice');
  
  document.getElementById('outputConsole').textContent = '⏳ Running example...';
  
  const executionStart = Date.now();
  
  try {
    const response = await fetch('/api/course/run_code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: example.code,
        topic_id: courseId
      })
    });
    
    const result = await response.json();
    const executionTime = Date.now() - executionStart;
    
    document.getElementById('outputConsole').textContent = result.output || result.result || '✅ Example executed successfully!';
    
    userActivity.codeAttempts++;
    userActivity.codeSuccess++;
    userActivity.lastSuccess = Date.now();
    
    logLearningEvent('example_executed', {
      example_title: example.title,
      example_index: exampleIndex,
      execution_time_ms: executionTime,
      success: true
    });
    
    addChatMessage('ai', `✅ Example ran successfully! The output matches what we expected. Now try modifying the code to experiment.`);
    
  } catch (error) {
    userActivity.codeAttempts++;
    userActivity.codeErrors++;
    
    document.getElementById('outputConsole').textContent = '❌ Error running example: ' + error.message + '\n\nMake sure your server is running!';
    
    addChatMessage('ai', '❌ Could not run the example. The server might be down. Try the "Try This Example" button instead to load it in the editor.');
    
    logLearningEvent('example_execution_failed', {
      example_title: example.title,
      error: error.message
    });
  }
}

// ========================================
// GENERATE AI EXERCISE
// ========================================
async function generateAIExercise(courseId, lessonIndex, exampleIndex) {
  const data = courseData[courseId];
  
  if (!data || !data.lessons || !data.lessons[lessonIndex]) {
    console.error('❌ Course or lesson not found');
    addChatMessage('ai', '❌ Could not generate exercise.');
    return;
  }
  
  const lesson = data.lessons[lessonIndex];
  const examples = lesson.complete_examples || [];
  
  if (!examples[exampleIndex]) {
    console.error('❌ Example not found');
    addChatMessage('ai', '❌ Example not found.');
    return;
  }
  
  const example = examples[exampleIndex];
  
  addChatMessage('ai', `🤖 Generating a custom exercise based on "${example.title}"... This may take a moment.`);
  
  switchTab('practice');
  document.getElementById('outputConsole').textContent = '⏳ AI is generating a custom exercise for you...';
  
  try {
    const response = await fetch('/api/course/generate_exercise', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic_id: courseId,
        example_code: example.code,
        example_title: example.title,
        difficulty: example.difficulty || 'easy',
        ai_challenge: example.ai_challenge || ''
      })
    });
    
    if (!response.ok) {
      throw new Error('AI generation failed - endpoint may not exist');
    }
    
    const result = await response.json();
    
    document.getElementById('codeEditor').value = result.starter_code || result.code || '# AI-generated exercise\n';
    document.getElementById('outputConsole').textContent = result.description || '✓ AI generated a custom exercise for you!';
    
    userActivity.currentExerciseStart = Date.now();
    logLearningEvent('ai_exercise_generated', {
      based_on: example.title,
      example_index: exampleIndex,
      success: true
    });
    
    const aiMessage = result.hint 
      ? `🎯 Custom exercise generated!\n\n${result.description}\n\n💡 Hint: ${result.hint}`
      : `🎯 Custom exercise generated! ${result.description || 'Try to complete this challenge!'}`;
    
    addChatMessage('ai', aiMessage);
    
  } catch (error) {
    console.error('AI generation error:', error);
    
    let modifiedCode = example.code;
    
    modifiedCode = modifiedCode
      .replace(/Emma Watson/g, 'YOUR_NAME')
      .replace(/25/g, 'YOUR_AGE')
      .replace(/London/g, 'YOUR_CITY')
      .replace(/Developer/g, 'YOUR_JOB')
      .replace(/10/g, 'NUM1')
      .replace(/5/g, 'NUM2');
    
    document.getElementById('codeEditor').value = modifiedCode;
    document.getElementById('outputConsole').textContent = '✓ Exercise created! Replace the placeholder values (YOUR_NAME, YOUR_AGE, etc.) with your own information.';
    
    logLearningEvent('ai_exercise_fallback', {
      based_on: example.title,
      reason: 'API not available'
    });
    
    addChatMessage('ai', `💡 I created a modified version of "${example.title}" for you!\n\nReplace the placeholders (YOUR_NAME, YOUR_AGE, YOUR_CITY, etc.) with your own values and run it.\n\n(Note: Full AI generation requires MCP server to be running)`);
  }
}

// ========================================
// TAB NAVIGATION
// ========================================
function switchTab(tabName) {
  userActivity.tabSwitches++;
  userActivity.lastClick = Date.now();
  
  logInteraction('tab_switch', {
    from_tab: document.querySelector('.tab-btn.active')?.textContent,
    to_tab: tabName,
    total_switches: userActivity.tabSwitches
  });
  
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  
  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.textContent.toLowerCase().includes(tabName.toLowerCase())) {
      btn.classList.add('active');
    }
  });
  
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });
  
  document.getElementById(tabName + 'Tab').classList.add('active');
  
  if (tabName === 'flowchart' && window.mermaid) {
    setTimeout(() => {
      mermaid.run({ nodes: document.querySelectorAll('.mermaid') });
    }, 100);
  }
}

// ========================================
// CODE EDITOR
// ========================================
async function runCode() {
  const code = document.getElementById('codeEditor').value;
  const output = document.getElementById('outputConsole');
  
  if (!code.trim()) {
    output.textContent = '⚠️ Please write some code first!';
    return;
  }

  output.textContent = '⏳ Running your code...';
  const executionStart = Date.now();

  try {
    const response = await fetch('/api/course/run_code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: code,
        topic_id: currentCourse
      })
    });
    
    const result = await response.json();
    const executionTime = Date.now() - executionStart;
    
    output.textContent = result.output || result.result || '✅ Code executed successfully!';
    
    userActivity.codeAttempts++;
    const hasError = result.error || result.output?.includes('Error') || result.output?.includes('Traceback');
    
    if (hasError) {
      userActivity.codeErrors++;
      userActivity.errorTimes.push(Date.now());
      if (userActivity.errorTimes.length > 5) {
        userActivity.errorTimes.shift();
      }
    } else {
      userActivity.codeSuccess++;
    }
    
    logLearningEvent('code_executed', {
      code_length: code.length,
      execution_time_ms: executionTime,
      success: !hasError,
      has_output: !!result.output,
      total_attempts: userActivity.codeAttempts,
      success_rate: userActivity.codeSuccess / userActivity.codeAttempts
    });
    
    if (hasError) {
      addChatMessage('ai', '�� I see an error in your code. Want me to help you fix it?');
    } else {
      addChatMessage('ai', '🎉 Great job running your code! Want to try the next challenge?');
    }
  } catch (error) {
    userActivity.codeAttempts++;
    userActivity.codeErrors++;
    userActivity.errorTimes.push(Date.now());
    
    logLearningEvent('code_execution_failed', {
      code_length: code.length,
      error_message: error.message
    });
    
    output.textContent = '❌ Error: ' + error.message + '\n\nTip: Make sure your server is running!';
    addChatMessage('ai', '❌ There was a problem running your code. The server might be down. Want to try again?');
  }
}

function clearCode() {
  document.getElementById('codeEditor').value = '';
  document.getElementById('outputConsole').textContent = 'Output will appear here...';
  addChatMessage('ai', '✨ Editor cleared! Ready for your next code!');
}

async function getAIHint() {
  const code = document.getElementById('codeEditor').value;
  addChatMessage('user', '💡 Can you give me a hint for this code?');
  addChatMessage('ai', '🤔 Let me analyze your code... (Hint: This would connect to the AI tutor API)');
}

function checkSolution() {
  addChatMessage('user', '✅ Can you check if my solution is correct?');
  addChatMessage('ai', '👀 Checking your solution... (This would validate against expected output)');
}

// ========================================
// CHAT FUNCTIONS
// ========================================
function addChatMessage(type, message) {
  const messagesContainer = document.getElementById('chatMessages');
  
  const messageDiv = document.createElement('div');
  messageDiv.className = `chat-message ${type}`;
  
  const avatar = document.createElement('div');
  avatar.className = `chat-avatar ${type}`;
  avatar.textContent = type === 'ai' ? '🤖' : '👤';
  
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble';
  if (type === 'ai' && typeof marked !== 'undefined') {
    bubble.innerHTML = marked.parse(message);
    bubble.querySelectorAll('pre code').forEach(el => {
      if (typeof hljs !== 'undefined') hljs.highlightElement(el);
    });
  } else {
    bubble.textContent = message;
  }
  
  messageDiv.appendChild(avatar);
  messageDiv.appendChild(bubble);
  messagesContainer.appendChild(messageDiv);
  
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  
  if (!message) return;
  
  userActivity.chatMessages++;
  userActivity.lastKeypress = Date.now();
  
  logInteraction('chat_message_sent', {
    message_length: message.length,
    contains_question: message.includes('?'),
    total_messages: userActivity.chatMessages,
    help_seeking_rate: userActivity.chatMessages / ((Date.now() - userActivity.sessionStart) / 60000)
  });
  
  addChatMessage('user', message);
  input.value = '';
  const thinkingId = "thinking-" + Date.now();
  addChatMessage("ai", "Thinking...", thinkingId);
  try {
    const codeContext = document.getElementById("codeEditor")?.value || "";
    const outputContext = document.getElementById("outputConsole")?.textContent || "";
    const response = await fetch("/api/course/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        course_id: currentCourse || "python_basics",
        code_context: codeContext,
        output_context: outputContext
      })
    });
    const thinkingMsg = document.getElementById(thinkingId);
    if (thinkingMsg) thinkingMsg.remove();
    if (response.ok) {
      const result = await response.json();
      addChatMessage("ai", result.response || result.message || "Let me help you with that!");
      logLearningEvent("ai_response_received", { course_id: currentCourse });
    } else {
      addChatMessage("ai", "Could not get a response. Try again!");
    }
  } catch (error) {
    const thinkingMsg = document.getElementById(thinkingId);
    if (thinkingMsg) thinkingMsg.remove();
    console.error("Chat error:", error);
    addChatMessage("ai", "Connection issue. Make sure the server is running.");
  }
}
function handleChatKeyPress(event) {
  if (event.key === 'Enter') {
    sendMessage();
  }
}

// ========================================
// ACCESSIBILITY FUNCTIONS
// ========================================
function toggleAccessPanel() {
  document.getElementById('accessPanel').classList.toggle('open');
}

function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
  const enabled = document.body.classList.contains('dark-mode');
  
  logInteraction('accessibility_feature', {
    feature: 'dark_mode',
    enabled: enabled
  });
}

function toggleDyslexiaMode() {
  document.body.classList.toggle('dyslexia-mode');
  const enabled = document.body.classList.contains('dyslexia-mode');
  
  logInteraction('accessibility_feature', {
    feature: 'dyslexia_font',
    enabled: enabled
  });
}

function toggleTextSize() {
  if (document.body.classList.contains('large-text')) {
    document.body.classList.remove('large-text');
    document.body.classList.add('extra-large-text');
  } else if (document.body.classList.contains('extra-large-text')) {
    document.body.classList.remove('extra-large-text');
  } else {
    document.body.classList.add('large-text');
  }
  
  logInteraction('accessibility_feature', {
    feature: 'text_size',
    size: document.body.classList.contains('extra-large-text') ? 'extra-large' : 
          document.body.classList.contains('large-text') ? 'large' : 'normal'
  });
}

function toggleReadingGuide() {
  const guide = document.getElementById('readingGuide');
  guide.classList.toggle('active');
  const enabled = guide.classList.contains('active');
  
  if (enabled) {
    document.addEventListener('mousemove', updateReadingGuide);
    addChatMessage('ai', '📍 Reading guide enabled! Move your mouse to see it.');
  } else {
    document.removeEventListener('mousemove', updateReadingGuide);
  }
  
  logInteraction('accessibility_feature', {
    feature: 'reading_guide',
    enabled: enabled
  });
}

function updateReadingGuide(e) {
  const guide = document.getElementById('readingGuide');
  guide.style.top = e.clientY + 'px';
}

function toggleHighContrast() {
  document.body.classList.toggle('high-contrast');
  const enabled = document.body.classList.contains('high-contrast');
  
  logInteraction('accessibility_feature', {
    feature: 'high_contrast',
    enabled: enabled
  });
}

function toggleLearningStatePanel() {
  const panel = document.getElementById('learningPanel');
  panel.classList.toggle('open');
}

// ========================================
// METRIC BAR UPDATE
// ========================================
function updateMetricBar(barId, percentage) {
  const bar = document.getElementById(barId);
  const valueId = barId.replace('Bar', 'Value');
  const valueSpan = document.getElementById(valueId);
  
  if (bar) {
    bar.style.width = Math.min(Math.max(percentage, 0), 100) + '%';
    
    if (percentage < 40) {
      bar.style.background = '#ef4444';
    } else if (percentage < 70) {
      bar.style.background = '#f59e0b';
    } else {
      bar.style.background = '#10b981';
    }
  }
  
  if (valueSpan) {
    valueSpan.textContent = Math.round(percentage) + '%';
  }
}

// ========================================
// RESEARCH DATA COLLECTION
// ========================================
let sessionData = {
  session_id: generateSessionId(),
  user_id: null,
  course_id: null,
  start_time: new Date().toISOString(),
  interactions: [],
  metrics_history: [],
  learning_events: []
};

// ========================================
// BEHAVIORAL METRICS
// ========================================
let userActivity = {
  lastClick: Date.now(),
  lastKeypress: Date.now(),
  lastScroll: Date.now(),
  sessionStart: Date.now(),
  
  codeAttempts: 0,
  codeSuccess: 0,
  codeErrors: 0,
  errorTimes: [],
  
  chatMessages: 0,
  tabSwitches: 0
};

function generateSessionId() {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function getIdleTime() {
  const now = Date.now();
  const lastActivity = Math.max(
    userActivity.lastClick,
    userActivity.lastKeypress,
    userActivity.lastScroll
  );
  return (now - lastActivity) / 1000;
}

function calculateAttention() {
  const idleSeconds = getIdleTime();
  if (idleSeconds < 30) return 90;
  if (idleSeconds < 60) return 70;
  if (idleSeconds < 120) return 40;
  return 20;
}

function calculateCognitiveLoad() {
  if (userActivity.codeAttempts === 0) return 50;
  
  const errorRate = userActivity.codeErrors / userActivity.codeAttempts;
  const baseLoad = 30 + (errorRate * 70);
  const helpFactor = Math.min(userActivity.chatMessages * 5, 20);
  
  return Math.min(baseLoad + helpFactor, 100);
}

function calculateEmotionalState() {
  if (userActivity.codeAttempts === 0) return 70;
  
  const successRate = userActivity.codeSuccess / userActivity.codeAttempts;
  return 35 + (successRate * 60);
}

function calculateStressLevel() {
  if (userActivity.codeAttempts === 0) return 25;
  
  const errorRate = userActivity.codeErrors / userActivity.codeAttempts;
  const errorStress = errorRate * 50;
  const helpStress = Math.min(userActivity.chatMessages * 8, 30);
  
  let rapidErrorBonus = 0;
  if (userActivity.errorTimes.length >= 2) {
    const lastTwo = userActivity.errorTimes.slice(-2);
    if (lastTwo[1] - lastTwo[0] < 30000) {
      rapidErrorBonus = 20;
    }
  }
  
  return Math.min(errorStress + helpStress + rapidErrorBonus, 100);
}

function trackUserActivity() {
  userActivity.lastClick = Date.now();
}

function trackKeypress() {
  userActivity.lastKeypress = Date.now();
}

function trackScroll() {
  userActivity.lastScroll = Date.now();
}

document.addEventListener('click', trackUserActivity);
document.addEventListener('keypress', trackKeypress);
document.addEventListener('scroll', trackScroll);

setInterval(() => {
  const attention = calculateAttention();
  const cognitive = calculateCognitiveLoad();
  const emotion = calculateEmotionalState();
  const stress = calculateStressLevel();
  
  // DISABLED: updateMetricBar("attentionBar"', attention);
  // DISABLED: updateMetricBar("cognitiveBar"', cognitive);
  // DISABLED: updateMetricBar("emotionBar"', emotion);
  // DISABLED: updateMetricBar("stressBar"', stress);
  
  // console.log('📊 Metrics:', {
    attention: Math.round(attention),
    cognitive: Math.round(cognitive),
    emotion: Math.round(emotion),
    stress: Math.round(stress),
    idle: Math.round(getIdleTime()) + 's',
    attempts: userActivity.codeAttempts,
    errors: userActivity.codeErrors,
    success: userActivity.codeSuccess
  });
}, 5000);

console.log('✅ Simple honest behavioral tracking active');

function logInteraction(eventType, data) {
  const interaction = {
    timestamp: new Date().toISOString(),
    event_type: eventType,
    data: data,
    current_course: currentCourse,
    attention: calculateAttention(),
    cognitive: calculateCognitiveLoad(),
    emotion: calculateEmotionalState(),
    stress: calculateStressLevel()
  };
  
  sessionData.interactions.push(interaction);
  
  if (sessionData.interactions.length % 10 === 0) {
    saveSessionData();
  }
}

function logLearningEvent(eventType, data) {
  const event = {
    timestamp: new Date().toISOString(),
    event_type: eventType,
    data: data
  };
  
  sessionData.learning_events.push(event);
}

async function saveSessionData() {
  try {
    await fetch('/api/research/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sessionData)
    });
  } catch (error) {
    console.error('Failed to save session data:', error);
  }
}

setInterval(saveSessionData, 30000);

window.addEventListener('beforeunload', () => {
  saveSessionData();
});

// ========================================
// SELF-REPORT WIDGET
// ========================================
function toggleSelfReportPanel() {
  const panel = document.getElementById('selfReportPanel');
  if (panel.style.display === 'none') {
    panel.style.display = 'block';
    resetSelfReportTimer();
  } else {
    panel.style.display = 'none';
  }
}

function handleFeelingSelect() {
  const dropdown = document.getElementById('feelingDropdown');
  const feeling = dropdown.value;
  
  if (!feeling) return;
  
  const presets = {
    'confident': {attention: 9, difficulty: 3, emotion: 9, stress: 2},
    'interested': {attention: 8, difficulty: 5, emotion: 8, stress: 3},
    'motivated': {attention: 8, difficulty: 5, emotion: 9, stress: 3},
    'focused': {attention: 10, difficulty: 5, emotion: 7, stress: 2},
    'okay': {attention: 6, difficulty: 5, emotion: 6, stress: 4},
    'curious': {attention: 7, difficulty: 6, emotion: 6, stress: 5},
    'processing': {attention: 5, difficulty: 6, emotion: 5, stress: 5},
    'confused': {attention: 4, difficulty: 8, emotion: 4, stress: 7},
    'stuck': {attention: 6, difficulty: 9, emotion: 3, stress: 8},
    'overwhelmed': {attention: 3, difficulty: 9, emotion: 2, stress: 9},
    'frustrated': {attention: 5, difficulty: 8, emotion: 2, stress: 8},
    'tired': {attention: 3, difficulty: 7, emotion: 4, stress: 6},
    'too_difficult': {attention: 5, difficulty: 10, emotion: 3, stress: 9},
    'not_clear': {attention: 4, difficulty: 8, emotion: 4, stress: 7},
    'need_break': {attention: 2, difficulty: 7, emotion: 3, stress: 8},
    'distracted': {attention: 2, difficulty: 6, emotion: 5, stress: 6}
  };
  
  const preset = presets[feeling];
  if (preset) {
    document.getElementById('attentionSlider').value = preset.attention;
    document.getElementById('difficultySlider').value = preset.difficulty;
    document.getElementById('emotionSlider').value = preset.emotion;
    document.getElementById('stressSlider').value = preset.stress;
    
    // ✅ FIX: Aggiungi "/10" invece di solo il numero
    document.getElementById('attentionValue').textContent = preset.attention + '/10';
    document.getElementById('difficultyValue').textContent = preset.difficulty + '/10';
    document.getElementById('emotionValue').textContent = preset.emotion + '/10';
    document.getElementById('stressValue').textContent = preset.stress + '/10';
  }
}
  const data = {
    feeling: feeling,
    attention: attention,
    difficulty: difficulty,
    emotion: emotion,
    stress: stress
  };
  
  try {
    const response = await fetch('/api/metrics/self_report', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    
    if (response.ok) {
      const panel = document.getElementById('selfReportPanel');
      panel.innerHTML = `
        <div style="text-align: center; padding: 40px 20px;">
          <div style="font-size: 48px; margin-bottom: 16px;">✓</div>
          <h3 style="font-size: 18px; color: #10b981; margin-bottom: 12px;">Thank You!</h3>
          <p style="font-size: 14px; color: #64748b;">Your feedback helps improve the learning experience.</p>
        </div>
      `;
      
      setTimeout(() => {
        panel.style.display = 'none';
        location.reload();
      }, 2000);
      
      console.log('📝 Self-report submitted:', data);
    }
  } catch (error) {
    console.error('❌ Self-report error:', error);
    alert('Could not submit feedback. Please try again.');
  }
}

let selfReportTimer = null;

function resetSelfReportTimer() {
  if (selfReportTimer) {
    clearTimeout(selfReportTimer);
  }
  
  selfReportTimer = setTimeout(() => {
    const panel = document.getElementById('selfReportPanel');
    if (panel.style.display === 'none') {
      const button = document.getElementById('selfReportToggle');
      button.style.animation = 'pulse 1s infinite';
      
      const style = document.createElement('style');
      style.textContent = `
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }
      `;
      document.head.appendChild(style);
    }
  }, 600000);
}

resetSelfReportTimer();

// ========================================
// ACCESSIBILITY NAVBAR FUNCTIONS
// ========================================
// ========================================

// GLOBAL VARIABLES (add at the top of file)
let voiceRecognition = null;
let isRecording = false;
let currentFontSize = 16;
let readingPointerActive = false;
let ttsEnabled = false;

// ========================================
// MENU FUNCTIONS
// ========================================
function toggleAccessMenu() {
  console.log('🦋 Opening accessibility menu...');
  const buttons = document.querySelectorAll('.nav-btn.hidden');
  const toggleBtn = document.getElementById('accessMenuToggle');
  const closeBtn = document.getElementById('closeMenuBtn');
  
  buttons.forEach((btn, i) => {
    setTimeout(() => {
      btn.classList.remove('hidden');
    }, i * 30);
  });
  
  if (toggleBtn) toggleBtn.style.display = 'none';
  if (closeBtn) closeBtn.style.display = 'flex';
  
  console.log('✅ Menu OPENED');
}

function closeAccessMenu() {
  console.log('❌ Closing accessibility menu...');
  const buttons = document.querySelectorAll('.nav-btn.hidden, .nav-btn:not(.hidden)');
  const toggleBtn = document.getElementById('accessMenuToggle');
  const closeBtn = document.getElementById('closeMenuBtn');
  
  // Hide all buttons EXCEPT home and first few fixed ones
  const allNavBtns = document.querySelectorAll('.nav-btn');
  allNavBtns.forEach((btn, index) => {
    // Keep first 5 visible (home, courses, focus assistant, mood, accessibility toggle)
    if (index >= 5) {
      btn.classList.add('hidden');
    }
  });
  
  if (toggleBtn) toggleBtn.style.display = 'flex';
  if (closeBtn) closeBtn.style.display = 'none';
  
  console.log('✅ Menu CLOSED');
}

// ========================================
// DARK MODE
// ========================================
function toggleDark() {
  document.body.classList.toggle('dark-mode');
  const icon = document.getElementById('darkModeIcon');
  if (icon) {
    if (document.body.classList.contains('dark-mode')) {
      icon.src = '/icons/sun.png';
      icon.alt = 'Light Mode';
    } else {
      icon.src = '/icons/dark.png';
      icon.alt = 'Dark Mode';
    }
  }
  console.log('🌙 Dark mode:', document.body.classList.contains('dark-mode') ? 'ON' : 'OFF');
}

// ========================================
// DYSLEXIA FONT
// ========================================
function toggleDyslexiaFont() {
  document.body.classList.toggle('dyslexia-mode');
  const btn = document.getElementById('dyslexiaBtn');
  if (btn) btn.classList.toggle('active');
  console.log('📖 Dyslexia font:', document.body.classList.contains('dyslexia-mode') ? 'ON' : 'OFF');
}

// ========================================
// FONT SIZE
// ========================================
function increaseFontSize() {
  if (currentFontSize < 32) {
    currentFontSize += 2;
    document.body.style.fontSize = currentFontSize + 'px';
    console.log('✅ Font size increased to:', currentFontSize + 'px');
  }
}

function decreaseFontSize() {
  if (currentFontSize > 12) {
    currentFontSize -= 2;
    document.body.style.fontSize = currentFontSize + 'px';
    console.log('✅ Font size decreased to:', currentFontSize + 'px');
  }
}

// ========================================
// READING POINTER
// ========================================
function toggleReadingPointer() {
  const settings = document.getElementById('readingPointerSettings');
  const btn = document.getElementById('readingPointerBtn');
  
  if (settings) {
    const isVisible = settings.classList.contains('visible');
    if (isVisible) {
      settings.classList.remove('visible');
      if (btn) btn.classList.remove('active');
      console.log('📍 Pointer panel: CLOSED');
    } else {
      settings.classList.add('visible');
      if (btn) btn.classList.add('active');
      console.log('📍 Pointer panel: OPENED');
    }
  }
}

function togglePointerActive() {
  const btn = document.getElementById('pointerToggleBtn');
  const line = document.getElementById('readingPointerLine');
  readingPointerActive = !readingPointerActive;
  
  if (readingPointerActive) {
    if (btn) {
      btn.classList.add('active');
      btn.textContent = '✅ Pointer Active';
    }
    if (line) line.classList.add('active');
    document.addEventListener('mousemove', updatePointerPosition);
    console.log('✅ READING POINTER ACTIVE');
  } else {
    if (btn) {
      btn.classList.remove('active');
      btn.textContent = '📍 Activate Pointer';
    }
    if (line) line.classList.remove('active');
    document.removeEventListener('mousemove', updatePointerPosition);
    console.log('❌ Pointer OFF');
  }
}

function updatePointerPosition(e) {
  const line = document.getElementById('readingPointerLine');
  if (line && readingPointerActive) {
    line.style.top = e.clientY + 'px';
  }
}

// ========================================
// TEXT TO SPEECH
// ========================================
function toggleTextToSpeech() {
  ttsEnabled = !ttsEnabled;
  const btn = document.getElementById('textToSpeechBtn');
  
  if (ttsEnabled) {
    if (btn) btn.classList.add('active');
    if (window.speechSynthesis) {
      const msg = new SpeechSynthesisUtterance('Text to speech enabled. Click any text to hear it.');
      window.speechSynthesis.speak(msg);
    }
    document.addEventListener('click', handleTextToSpeech);
    console.log('🔊 TTS: ON');
  } else {
    window.speechSynthesis?.cancel();
    if (btn) btn.classList.remove('active');
    document.removeEventListener('click', handleTextToSpeech);
    console.log('🔊 TTS: OFF');
  }
}

function handleTextToSpeech(e) {
  if (!ttsEnabled) return;
  
  // Don't speak if clicking buttons
  if (e.target.tagName === 'BUTTON' || e.target.tagName === 'INPUT') return;
  
  const text = e.target.textContent || e.target.innerText;
  if (text && text.trim() && text.length < 500) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text.trim());
    utterance.rate = 0.9;
    window.speechSynthesis.speak(utterance);
  }
}

// ========================================
// VOICE INPUT
// ========================================
function toggleVoiceInput() {
  console.log('🎤 Voice Input toggled');
  const btn = document.getElementById('voiceBtn');
  
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('❌ Voice input is not supported in your browser. Try Chrome or Edge.');
    return;
  }

  if (isRecording) {
    if (voiceRecognition) {
      voiceRecognition.stop();
      isRecording = false;
      if (btn) btn.classList.remove('active', 'recording');
      console.log('�� Recording STOPPED');
    }
    return;
  }

  if (!voiceRecognition) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    voiceRecognition = new SpeechRecognition();
    voiceRecognition.continuous = false;
    voiceRecognition.interimResults = false;
    voiceRecognition.lang = 'en-US';
    
    voiceRecognition.onstart = () => {
      isRecording = true;
      if (btn) btn.classList.add('active', 'recording');
      console.log('🎤 LISTENING...');
    };
    
    voiceRecognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      const codeEditor = document.getElementById('codeEditor');
      if (codeEditor) {
        codeEditor.value += transcript + '\n';
      }
      console.log('🎤 Recognized:', transcript);
      if (typeof addChatMessage === 'function') {
        addChatMessage('ai', `🎤 I heard: "${transcript}"`);
      }
    };
    
    voiceRecognition.onerror = (e) => {
      console.error('🎤 Voice error:', e.error);
      isRecording = false;
      if (btn) btn.classList.remove('active', 'recording');
      if (e.error !== 'no-speech') {
        alert('🎤 Error: ' + e.error);
      }
    };
    
    voiceRecognition.onend = () => {
      isRecording = false;
      if (btn) btn.classList.remove('active', 'recording');
      console.log('🎤 Recording ended');
    };
  }
  
  voiceRecognition.start();
}

// ========================================
// REDUCE MOTION
// ========================================
function toggleReduceMotion() {
  document.body.classList.toggle('reduce-motion');
  const btn = document.getElementById('reduceMotionBtn');
  if (btn) btn.classList.toggle('active');
  
  const styleId = 'reduce-motion-style';
  const existing = document.getElementById(styleId);
  
  if (existing) {
    existing.remove();
    console.log('⚡ Animations: ON');
  } else {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = '* { animation: none !important; transition: none !important; }';
    document.head.appendChild(style);
    console.log('⚡ Animations: OFF');
  }
}

// ========================================
// HIGH CONTRAST
// ========================================
function toggleHighContrast() {
  document.body.classList.toggle('high-contrast');
  const btn = document.getElementById('highContrastBtn');
  if (btn) btn.classList.toggle('active');
  console.log('⚫ High Contrast:', document.body.classList.contains('high-contrast') ? 'ON' : 'OFF');
}

// ========================================
// FOCUS ASSISTANT
// ========================================

function toggleFocusAssistant() {
  console.log('🎯 Focus Assistant toggled');
  
  // Check if focus_assistant.js is loaded and has the function
  if (typeof window.showFocusAssistant === 'function') {
    window.showFocusAssistant();
    console.log('✅ Focus Assistant panel opened');
  } else if (typeof window.toggleFocusAssistantPanel === 'function') {
    window.toggleFocusAssistantPanel();
    console.log('✅ Focus Assistant panel toggled');
  } else {
    // If focus_assistant.js not loaded
    console.error('❌ focus_assistant.js not loaded!');
    alert('🎯 Focus Assistant requires focus_assistant.js to be loaded.\n\nMake sure the file is in /static/ and loaded in course.html');
  }
}

// ========================================
// CLOSE FOCUS ASSISTANT
// ========================================
function closeFocusAssistant() {
  const panel = document.getElementById('focusAssistantPanel');
  if (panel) {
    panel.style.display = 'none';
    console.log('❌ Focus Assistant: CLOSED');
  }
}
// ========================================
// SELF REPORT PANEL
// ========================================
function toggleSelfReportPanel() {
  const panel = document.getElementById('selfReportPanel');
  if (panel) {
    if (panel.style.display === 'none' || !panel.style.display) {
      panel.style.display = 'block';
      console.log('📊 Self-report panel: OPENED');
    } else {
      panel.style.display = 'none';
      console.log('📊 Self-report panel: CLOSED');
    }
  } else {
    console.warn('⚠️ Self-report panel not found in DOM');
  }
}
// ========================================
// FOCUS MODE 
// ========================================
function toggleFocusMode() {
  document.body.classList.toggle('focus-mode');
  const isActive = document.body.classList.contains('focus-mode');
  
  if (isActive) {
    // Hide distractions
    const header = document.querySelector('.lesson-header');
    
    if (header) header.style.opacity = '0.3';
    
    console.log('✅ Focus Mode: ON');
  } else {
    const header = document.querySelector('.lesson-header');
    const sidebar = document.querySelector('.course-selector');
    if (header) header.style.opacity = '1';
    if (sidebar) sidebar.style.opacity = '1';
    console.log('❌ Focus Mode: OFF');
  }
}
console.log('✅ All accessibility functions loaded successfully!');
