// ============================================
// SELF-REPORT WIDGET - NAVBAR VERSION
// For Synapse AI navbar integration
// NO floating button - uses navbar button
// ============================================

(function() {
  if (window.selfReportWidgetLoaded) return;
  window.selfReportWidgetLoaded = true;

  // CSS Injection
  const style = document.createElement('style');
  style.textContent = `
    .self-report-panel {
      position: fixed;
      top: 70px;
      left: 20px;
      background: white;
      border-radius: 16px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
      width: 360px;
      max-height: calc(100vh - 100px);
      overflow-y: auto;
      padding: 24px;
      z-index: 10000;
      display: none;
    }
    .self-report-panel h3 {
      font-size: 20px;
      font-weight: 600;
      margin-bottom: 16px;
      color: #1e293b;
    }
    .feeling-dropdown {
      width: 100%;
      padding: 12px 16px;
      border: 2px solid #e2e8f0;
      border-radius: 8px;
      font-size: 15px;
      margin-bottom: 20px;
      cursor: pointer;
      background: white;
      transition: all 0.2s;
    }
    .feeling-dropdown:hover { border-color: #94a3b8; }
    .feeling-dropdown:focus {
      outline: none;
      border-color: #8b5cf6;
      box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
    }
    .slider-container { margin-bottom: 24px; }
    .slider-label {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }
    .slider-label-left {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      font-weight: 500;
      color: #475569;
    }
    .slider-label-icon { font-size: 20px; }
    .slider-value-display {
      font-size: 24px;
      font-weight: 700;
      padding: 4px 12px;
      border-radius: 8px;
      min-width: 50px;
      text-align: center;
      transition: all 0.3s;
    }
    .value-low { background: #fef2f2; color: #dc2626; }
    .value-medium { background: #fef3c7; color: #f59e0b; }
    .value-high { background: #dcfce7; color: #16a34a; }
    .slider-input {
      width: 100%;
      height: 8px;
      border-radius: 4px;
      outline: none;
      -webkit-appearance: none;
      cursor: pointer;
    }
    .slider-attention {
      background: linear-gradient(to right, #fca5a5 0%, #fbbf24 50%, #a78bfa 100%);
    }
    .slider-attention::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: #8b5cf6;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(139, 92, 246, 0.4);
    }
    .slider-difficulty {
      background: linear-gradient(to right, #86efac 0%, #fbbf24 50%, #ef4444 100%);
    }
    .slider-difficulty::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: #f59e0b;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(245, 158, 11, 0.4);
    }
    .slider-emotion {
      background: linear-gradient(to right, #ef4444 0%, #fbbf24 50%, #10b981 100%);
    }
    .slider-emotion::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: #10b981;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
    }
    .slider-stress {
      background: linear-gradient(to right, #86efac 0%, #fbbf24 50%, #ef4444 100%);
    }
    .slider-stress::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: #ef4444;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
    }
    .slider-range-labels {
      display: flex;
      justify-content: space-between;
      margin-top: 4px;
      font-size: 12px;
      color: #94a3b8;
    }
    .slider-description {
      text-align: center;
      margin-top: 8px;
      font-size: 13px;
      font-weight: 500;
      color: #64748b;
      min-height: 20px;
    }
    .submit-button {
      width: 100%;
      padding: 14px;
      background: linear-gradient(135deg, #8b5cf6, #6366f1);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s;
      margin-top: 8px;
    }
    .submit-button:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(139, 92, 246, 0.4);
    }
    .submit-button:disabled {
      background: #94a3b8;
      cursor: not-allowed;
    }
    .close-button {
      position: absolute;
      top: 16px;
      right: 16px;
      background: none;
      border: none;
      font-size: 24px;
      color: #94a3b8;
      cursor: pointer;
      padding: 4px;
      line-height: 1;
      transition: all 0.2s;
    }
    .close-button:hover {
      color: #475569;
      transform: rotate(90deg);
    }
  `;
  document.head.appendChild(style);

  // HTML Injection (NO BUTTON - uses navbar button)
  const html = `
    <div id="selfReportPanel" class="self-report-panel">
      <button class="close-button" onclick="toggleSelfReportPanel()">×</button>
      <h3>😊 How are you?</h3>
      <select id="feelingDropdown" class="feeling-dropdown" onchange="handleFeelingSelect()">
        <option value="">How are you feeling right now?</option>
        <optgroup label="✅ Feeling Good">
          <option value="confident">💪 Confident - I've got this!</option>
          <option value="interested">🤔 Interested - This is engaging</option>
          <option value="motivated">🚀 Motivated - Ready to learn</option>
          <option value="focused">🎯 Focused - In the zone</option>
        </optgroup>
        <optgroup label="😐 Neutral">
          <option value="okay">👌 Okay - Doing fine</option>
          <option value="curious">🧐 Curious - Want to learn more</option>
          <option value="processing">💭 Processing - Need time to think</option>
        </optgroup>
        <optgroup label="😟 Struggling">
          <option value="confused">😕 Confused - Not clear</option>
          <option value="stuck">🚧 Stuck - Can't move forward</option>
          <option value="overwhelmed">😰 Overwhelmed - Too much</option>
          <option value="frustrated">😤 Frustrated - This is hard</option>
          <option value="tired">😴 Tired - Low energy</option>
        </optgroup>
        <optgroup label="🆘 Need Help">
          <option value="too_difficult">⚠️ Too difficult - Over my head</option>
          <option value="not_clear">❓ Not clear - Don't understand</option>
          <option value="need_break">☕ Need break - Pause needed</option>
          <option value="distracted">🌀 Distracted - Can't focus</option>
        </optgroup>
      </select>
      <p style="font-size: 13px; color: #64748b; margin-bottom: 16px; text-align: center;">
        Optional: Fine-tune the sliders below (1-10 scale)
      </p>
      <div class="slider-container">
        <div class="slider-label">
          <div class="slider-label-left">
            <span class="slider-label-icon">🧠</span>
            <span>Attention</span>
          </div>
          <div id="attentionValue" class="slider-value-display value-medium">5</div>
        </div>
        <input type="range" min="1" max="10" value="5" class="slider-input slider-attention" id="attentionSlider">
        <div class="slider-range-labels"><span>Distracted</span><span>Focused</span></div>
        <div id="attentionDesc" class="slider-description">Moderate focus</div>
      </div>
      <div class="slider-container">
        <div class="slider-label">
          <div class="slider-label-left">
            <span class="slider-label-icon">💎</span>
            <span>Difficulty</span>
          </div>
          <div id="difficultyValue" class="slider-value-display value-medium">5</div>
        </div>
        <input type="range" min="1" max="10" value="5" class="slider-input slider-difficulty" id="difficultySlider">
        <div class="slider-range-labels"><span>Too Easy</span><span>Too Hard</span></div>
        <div id="difficultyDesc" class="slider-description">Just right</div>
      </div>
      <div class="slider-container">
        <div class="slider-label">
          <div class="slider-label-left">
            <span class="slider-label-icon">😊</span>
            <span>Emotion</span>
          </div>
          <div id="emotionValue" class="slider-value-display value-medium">5</div>
        </div>
        <input type="range" min="1" max="10" value="5" class="slider-input slider-emotion" id="emotionSlider">
        <div class="slider-range-labels"><span>Frustrated</span><span>Happy</span></div>
        <div id="emotionDesc" class="slider-description">Neutral feeling</div>
      </div>
      <div class="slider-container">
        <div class="slider-label">
          <div class="slider-label-left">
            <span class="slider-label-icon">😰</span>
            <span>Stress</span>
          </div>
          <div id="stressValue" class="slider-value-display value-medium">5</div>
        </div>
        <input type="range" min="1" max="10" value="5" class="slider-input slider-stress" id="stressSlider">
        <div class="slider-range-labels"><span>Relaxed</span><span>Stressed</span></div>
        <div id="stressDesc" class="slider-description">Moderate stress</div>
      </div>
      <button class="submit-button" onclick="submitSelfReport()">Submit Feedback</button>
    </div>
  `;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {
    document.body.insertAdjacentHTML('beforeend', html);

    const descriptions = {
      attention: ["Extremely distracted", "Very distracted", "Somewhat distracted", "Slightly distracted", "Moderate focus", "Fairly focused", "Quite focused", "Very focused", "Highly focused", "Completely focused"],
      difficulty: ["Way too easy", "Too easy", "A bit too easy", "Slightly easy", "Just right", "Slightly challenging", "Challenging", "Quite difficult", "Very difficult", "Extremely difficult"],
      emotion: ["Very frustrated", "Frustrated", "Somewhat frustrated", "Slightly unhappy", "Neutral", "Fairly content", "Content", "Happy", "Very happy", "Extremely happy"],
      stress: ["Completely relaxed", "Very relaxed", "Relaxed", "Calm", "Moderate stress", "Somewhat stressed", "Stressed", "Quite stressed", "Very stressed", "Extremely stressed"]
    };

    function updateSlider(type, value) {
      const val = parseInt(value);
      const display = document.getElementById(`${type}Value`);
      const desc = document.getElementById(`${type}Desc`);
      if (!display || !desc) return;
      display.textContent = val;
      display.className = 'slider-value-display';
      if (type === 'attention' || type === 'emotion') {
        if (val <= 3) display.classList.add('value-low');
        else if (val <= 7) display.classList.add('value-medium');
        else display.classList.add('value-high');
      } else {
        if (val <= 3) display.classList.add('value-high');
        else if (val <= 7) display.classList.add('value-medium');
        else display.classList.add('value-low');
      }
      desc.textContent = descriptions[type][val - 1];
    }

    ['attention', 'difficulty', 'emotion', 'stress'].forEach(type => {
      const slider = document.getElementById(`${type}Slider`);
      if (slider) {
        slider.addEventListener('input', e => updateSlider(type, e.target.value));
        updateSlider(type, 5);
      }
    });

    window.toggleSelfReportPanel = function() {
      const panel = document.getElementById('selfReportPanel');
      if (panel) {
        panel.style.display = panel.style.display === 'none' || !panel.style.display ? 'block' : 'none';
      }
    };

    window.handleFeelingSelect = function() {
      const dropdown = document.getElementById('feelingDropdown');
      if (!dropdown) return;
      const presets = {
        confident: {attention: 9, difficulty: 3, emotion: 9, stress: 2},
        interested: {attention: 8, difficulty: 5, emotion: 8, stress: 3},
        motivated: {attention: 8, difficulty: 5, emotion: 9, stress: 3},
        focused: {attention: 10, difficulty: 5, emotion: 7, stress: 2},
        okay: {attention: 6, difficulty: 5, emotion: 6, stress: 4},
        curious: {attention: 7, difficulty: 6, emotion: 6, stress: 5},
        processing: {attention: 5, difficulty: 6, emotion: 5, stress: 5},
        confused: {attention: 4, difficulty: 8, emotion: 4, stress: 7},
        stuck: {attention: 6, difficulty: 9, emotion: 3, stress: 8},
        overwhelmed: {attention: 3, difficulty: 9, emotion: 2, stress: 9},
        frustrated: {attention: 5, difficulty: 8, emotion: 2, stress: 8},
        tired: {attention: 3, difficulty: 7, emotion: 4, stress: 6},
        too_difficult: {attention: 5, difficulty: 10, emotion: 3, stress: 9},
        not_clear: {attention: 4, difficulty: 8, emotion: 4, stress: 7},
        need_break: {attention: 2, difficulty: 7, emotion: 3, stress: 8},
        distracted: {attention: 2, difficulty: 6, emotion: 5, stress: 6}
      };
      const preset = presets[dropdown.value];
      if (preset) {
        ['attention', 'difficulty', 'emotion', 'stress'].forEach(type => {
          const slider = document.getElementById(`${type}Slider`);
          if (slider) {
            slider.value = preset[type];
            updateSlider(type, preset[type]);
          }
        });
      }
    };

    window.submitSelfReport = async function() {
      const feeling = document.getElementById('feelingDropdown')?.value;
      const attention = parseInt(document.getElementById('attentionSlider')?.value || 5);
      const difficulty = parseInt(document.getElementById('difficultySlider')?.value || 5);
      const emotion = parseInt(document.getElementById('emotionSlider')?.value || 5);
      const stress = parseInt(document.getElementById('stressSlider')?.value || 5);
      
      if (!feeling) {
        alert('Please select how you\'re feeling from the dropdown');
        return;
      }
      
      const data = {
        type: 'self_report',
        feeling_category: feeling,
        self_reported_attention: attention,
        self_reported_cognitive_load: difficulty,
        self_reported_emotion: emotion,
        self_reported_stress: stress,
        timestamp: new Date().toISOString()
      };
      
      try {
        const btn = document.querySelector('.submit-button');
        if (btn) {
          btn.disabled = true;
          btn.textContent = 'Submitting...';
        }
        
        const response = await fetch('/api/metrics/update', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(data)
        });
        
        if (response.ok) {
          const panel = document.getElementById('selfReportPanel');
          if (panel) {
            panel.innerHTML = `
              <div style="text-align: center; padding: 40px 20px;">
                <div style="font-size: 64px; margin-bottom: 16px;">✓</div>
                <h3 style="font-size: 22px; color: #10b981; margin-bottom: 8px;">Thank You!</h3>
                <p style="font-size: 14px; color: #64748b;">Your feedback helps improve the learning experience.</p>
              </div>
            `;
          }
          console.log('Self-report submitted:', data);
          setTimeout(() => {
            toggleSelfReportPanel();
            setTimeout(() => location.reload(), 300);
          }, 2000);
        }
      } catch (error) {
        console.error('Self-report error:', error);
        alert('Could not submit feedback. Please try again.');
        const btn = document.querySelector('.submit-button');
        if (btn) {
          btn.disabled = false;
          btn.textContent = 'Submit Feedback';
        }
      }
    };
  }
})();
