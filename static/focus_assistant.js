// ============================================
// FOCUS ASSISTANT - Universal Spotlight Mode
// ============================================
// Works on: index.html, advanced_learning.html, course.html
// Author: Synapse AI
// Version: 1.0
// ============================================

(function() {
    'use strict';
    
    console.log('🎯 Focus Assistant Module Loading...');
    
    // Global state
    window.focusAssistantState = {
        active: false,
        focusedElement: null
    };
    
    // ========== MAIN TOGGLE FUNCTION ==========
    window.toggleFocusAssistant = function() {
        window.focusAssistantState.active = !window.focusAssistantState.active;
        const btn = document.getElementById('focusAssistBtn');
        
        if (window.focusAssistantState.active) {
            activateFocusMode();
            if (btn) {
                btn.classList.add('active');
                btn.setAttribute('aria-pressed', 'true');
            }
            console.log('✅ Focus mode ACTIVATED');
        } else {
            deactivateFocusMode();
            if (btn) {
                btn.classList.remove('active');
                btn.setAttribute('aria-pressed', 'false');
            }
            console.log('❌ Focus mode DEACTIVATED');
        }
    };
    
    // ========== ACTIVATE FOCUS MODE ==========
    function activateFocusMode() {
        // Create dark overlay
        const overlay = document.createElement('div');
        overlay.id = 'focusOverlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.78);
            z-index: 10040;
            pointer-events: none;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(overlay);
        
        // Add event listeners
        document.addEventListener('click', handleFocusClick, true);
        document.addEventListener('mouseover', highlightFocusableArea);
        document.addEventListener('mouseout', removePreviewHighlight);
        
        // Show instruction message
        showFocusMessage('🎯 Click on any area to spotlight it. Click 🎯 again to exit.');
    }
    
    // ========== DEACTIVATE FOCUS MODE ==========
    function deactivateFocusMode() {
        // Remove overlay
        const overlay = document.getElementById('focusOverlay');
        if (overlay) overlay.remove();
        
        // Remove focus from element
        if (window.focusAssistantState.focusedElement) {
            window.focusAssistantState.focusedElement.style.position = '';
            window.focusAssistantState.focusedElement.style.zIndex = '';
            window.focusAssistantState.focusedElement.style.boxShadow = '';
            window.focusAssistantState.focusedElement = null;
        }
        
        // Remove event listeners
        document.removeEventListener('click', handleFocusClick, true);
        document.removeEventListener('mouseover', highlightFocusableArea);
        document.removeEventListener('mouseout', removePreviewHighlight);
        
        // Remove any preview highlights
        document.querySelectorAll('.focus-preview').forEach(el => {
            el.classList.remove('focus-preview');
            el.style.outline = '';
        });
        
        // Remove message
        const message = document.getElementById('focusMessage');
        if (message) message.remove();
    }
    
    // ========== HANDLE FOCUS CLICK ==========
    function handleFocusClick(e) {
        if (!window.focusAssistantState.active) return;
        
        // Don't do anything if clicking the button itself
        if (e.target.closest('.nav-btn') || e.target.closest('#focusAssistBtn')) {
            return;
        }
        
        e.preventDefault();
        e.stopPropagation();
        
        // Find the closest clickable element
        let targetElement = e.target;
        
        // Universal selectors that work across all pages
        const containerSelectors = [
            // Common across all pages
            '.card',
            '.column-card',
            '.panel',
            
            // Advanced Learning specific
            '.tool-content',
            '.exercise-box',
            '.output-box',
            
            // Course specific
            '.lesson-content',
            '.lesson-section',
            '.content-block',
            
            // Tutor specific
            '.tutor-section',
            '.code-editor',
            '.results-panel',
            
            // Generic
            '.chat-container',
            '.chat-messages',
            'section',
            'article',
            'main',
            'div[class*="container"]',
            'div[class*="section"]',
            'div[class*="content"]'
        ];
        
        // Find the appropriate container
        for (const selector of containerSelectors) {
            const container = targetElement.closest(selector);
            if (container) {
                targetElement = container;
                break;
            }
        }
        
        focusOnElement(targetElement);
    }
    
    // ========== HIGHLIGHT FOCUSABLE AREA (PREVIEW) ==========
    function highlightFocusableArea(e) {
        if (!window.focusAssistantState.active || window.focusAssistantState.focusedElement) {
            return;
        }
        
        // Remove previous preview
        document.querySelectorAll('.focus-preview').forEach(el => {
            el.classList.remove('focus-preview');
            el.style.outline = '';
        });
        
        let targetElement = e.target;
        
        // Look for container
        const containerSelectors = [
            '.card',
            '.column-card',
            '.tool-content',
            '.panel',
            '.exercise-box',
            '.lesson-content',
            'section'
        ];
        
        for (const selector of containerSelectors) {
            const container = targetElement.closest(selector);
            if (container) {
                targetElement = container;
                break;
            }
        }
        
        // Add preview border (green outline)
        targetElement.style.outline = '3px solid rgba(16, 185, 129, 0.6)';
        targetElement.classList.add('focus-preview');
    }
    
    // ========== REMOVE PREVIEW HIGHLIGHT ==========
    function removePreviewHighlight(e) {
        if (!window.focusAssistantState.active || window.focusAssistantState.focusedElement) {
            return;
        }
        
        const target = e.target.closest('.focus-preview');
        if (target) {
            target.style.outline = '';
            target.classList.remove('focus-preview');
        }
    }
    
    // ========== FOCUS ON ELEMENT ==========
    function focusOnElement(element) {
        // Remove previous focus
        if (window.focusAssistantState.focusedElement) {
            window.focusAssistantState.focusedElement.style.position = '';
            window.focusAssistantState.focusedElement.style.zIndex = '';
            window.focusAssistantState.focusedElement.style.boxShadow = '';
        }
        
        // Apply focus with a crisp green ring + glow (matches the shared toolbar module)
        element.style.position = 'relative';
        element.style.zIndex = '10042';
        element.style.boxShadow = '0 0 0 4px rgba(16, 185, 129, .95), 0 0 50px rgba(16, 185, 129, .5)';
        
        // Smooth scroll to element
        element.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center',
            inline: 'center'
        });
        
        // Store focused element
        window.focusAssistantState.focusedElement = element;
        
        // Update message
        showFocusMessage('✅ Area spotlighted! Click elsewhere to change, or click 🎯 to exit.');
    }
    
    // ========== SHOW FOCUS MESSAGE ==========
    function showFocusMessage(text) {
        // Remove existing message
        const existing = document.getElementById('focusMessage');
        if (existing) existing.remove();
        
        // Create new message
        const message = document.createElement('div');
        message.id = 'focusMessage';
        message.textContent = text;
        message.style.cssText = `
            position: fixed;
            top: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            z-index: 10000;
            box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4);
            animation: focusMessageSlideDown 0.4s ease;
            max-width: 90%;
            text-align: center;
        `;
        document.body.appendChild(message);
        
        // Auto-hide after 4 seconds
        setTimeout(() => {
            if (message && message.parentNode) {
                message.style.animation = 'focusMessageSlideUp 0.4s ease';
                setTimeout(() => message.remove(), 400);
            }
        }, 4000);
    }
    
    // ========== KEYBOARD SUPPORT ==========
    document.addEventListener('keydown', function(e) {
        // ESC key to exit focus mode
        if (e.key === 'Escape' && window.focusAssistantState.active) {
            window.toggleFocusAssistant();
        }
    });
    
    console.log('✅ Focus Assistant Module Loaded!');
    
})();

// ========== AUTO-INITIALIZE ON DOM READY ==========
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🎯 Focus Assistant ready for use');
    });
} else {
    console.log('🎯 Focus Assistant ready for use');
}
