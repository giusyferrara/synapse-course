// SYNAPSE Idle-Aware Encouragement System v1.1
// Variations + no repeats
(function() {
    'use strict';
    
    let idleTimers = [];
    let lastTriggered = { 40: false, 90: false, 180: false };
    let lastShown = '';
    
    const VARIATIONS = {
        idle_40_seconds: [
            "Still there? Take your time, I am not going anywhere.",
            "Want a hint, or should I rephrase what we are looking at?",
            "Going at your own pace is the right pace. Want me to break it down?",
            "Just checking in! Anything making this tricky?",
            "Need a different angle? I have a few ways to explain it.",
            "Pause whenever you need. Let me know if I should slow down."
        ],
        idle_90_seconds: [
            "Sometimes a fresh approach helps. Want a simpler example?",
            "If your brain feels full, totally normal. Want me to summarise the key idea?",
            "Stuck on a specific part? Tell me what feels confusing.",
            "Even a fragment of a question is enough — I will work with it.",
            "I have got time. Want one concrete example to make it click?",
            "Take a breath. I can walk through this step by step whenever you are ready."
        ],
        idle_180_seconds: [
            "Three minutes is a fine pause. When you are ready, ask me anything.",
            "Sometimes the brain needs a real break — water, stretch, then come back.",
            "No pressure at all. I am here when something sparks your curiosity.",
            "Want a totally different example? Just say the word.",
            "Coming back fresh often beats pushing through. Take all the time you need."
        ]
    };
    
    function pickRandom(level) {
        let lessonTriggers = null;
        if (window.currentLesson?.ai_tutor_config?.intervention_triggers) lessonTriggers = window.currentLesson.ai_tutor_config.intervention_triggers;
        else if (window.lessonData?.ai_tutor_config?.intervention_triggers) lessonTriggers = window.lessonData.ai_tutor_config.intervention_triggers;
        
        const lessonMsg = lessonTriggers?.['idle_' + level + '_seconds'];
        const pool = VARIATIONS['idle_' + level + '_seconds'].slice();
        if (lessonMsg) pool.unshift(lessonMsg);
        
        let pick;
        let attempts = 0;
        do {
            pick = pool[Math.floor(Math.random() * pool.length)];
            attempts++;
        } while (pick === lastShown && attempts < 5);
        
        lastShown = pick;
        return pick;
    }
    
    function showMessage(msg) {
        if (!msg) return;
        if (typeof window.addChatMessage === 'function') {
            window.addChatMessage('ai', msg);
            return;
        }
        const chatBox = document.getElementById('chatMessages') || document.querySelector('.chat-messages');
        if (chatBox) {
            const div = document.createElement('div');
            div.className = 'chat-msg ai idle-encouragement';
            div.style.cssText = 'padding:10px 14px;margin:8px 0;background:rgba(139,92,246,0.08);border-left:3px solid #8b5cf6;border-radius:6px;font-style:italic;';
            div.textContent = msg;
            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;
            return;
        }
        const toast = document.createElement('div');
        toast.style.cssText = 'position:fixed;bottom:24px;right:24px;background:linear-gradient(135deg,#7c3aed,#5b21b6);color:white;padding:14px 18px;border-radius:10px;max-width:340px;z-index:99999;box-shadow:0 8px 24px rgba(91,33,182,0.4);font-size:14px;line-height:1.5;';
        toast.textContent = msg;
        document.body.appendChild(toast);
        setTimeout(() => { toast.style.opacity='0'; toast.style.transition='opacity 0.5s'; }, 7500);
        setTimeout(() => toast.remove(), 8000);
    }
    
    function startIdleTimers() {
        idleTimers.forEach(t => clearTimeout(t));
        idleTimers = [];
        lastTriggered = { 40: false, 90: false, 180: false };
        
        idleTimers.push(setTimeout(() => {
            if (!lastTriggered[40]) { showMessage(pickRandom(40)); lastTriggered[40] = true; }
        }, 40000));
        idleTimers.push(setTimeout(() => {
            if (!lastTriggered[90]) { showMessage(pickRandom(90)); lastTriggered[90] = true; }
        }, 90000));
        idleTimers.push(setTimeout(() => {
            if (!lastTriggered[180]) { showMessage(pickRandom(180)); lastTriggered[180] = true; }
        }, 180000));
    }
    
    let mouseDebounce;
    function debouncedReset() {
        clearTimeout(mouseDebounce);
        mouseDebounce = setTimeout(startIdleTimers, 300);
    }
    
    function bindListeners() {
        document.addEventListener('keydown', startIdleTimers, { passive: true });
        document.addEventListener('click', startIdleTimers, { passive: true });
        document.addEventListener('mousemove', debouncedReset, { passive: true });
        document.addEventListener('scroll', debouncedReset, { passive: true, capture: true });
        document.addEventListener('touchstart', startIdleTimers, { passive: true });
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => { bindListeners(); startIdleTimers(); });
    } else {
        bindListeners();
        startIdleTimers();
    }
    
    window.SYNAPSE_idleSystem = {
        restart: startIdleTimers,
        stop: () => idleTimers.forEach(t => clearTimeout(t)),
        showNow: showMessage,
        variations: VARIATIONS
    };
    
    console.log('🦋 SYNAPSE Idle-Aware v1.1 (varied) loaded');
})();