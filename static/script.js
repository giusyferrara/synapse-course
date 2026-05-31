// Markdown renderer helper (uses marked.js from CDN in index.html)
function renderMarkdown(text) {
    if (typeof marked === 'undefined' || !text) return text || '';
    try {
        const html = marked.parse(text);
        if (typeof hljs !== 'undefined') {
            setTimeout(() => {
                document.querySelectorAll('.ai-rendered pre code').forEach(block => {
                    try { hljs.highlightElement(block); } catch (e) {}
                });
            }, 0);
        }
        return html;
    } catch (e) {
        return text;
    }
}

// Main API calling function - CLEAN VERSION
function callAPI(endpoint) {
    console.log(`🚀 Calling API: ${endpoint}`);
    
    const codeInput = document.getElementById('codeInput');
    const resultsDiv = document.getElementById('results');
    
    if (!codeInput || !codeInput.value.trim()) {
        alert('⚠️ Please enter some code first!');
        return;
    }
    
    const code = codeInput.value;
    
    // Show loading
    if (resultsDiv) {
        resultsDiv.innerHTML = '<div style="text-align: center; padding: 30px;"><div class="loading"></div><div style="margin-top: 15px;">Processing...</div></div>';
    }
    
    // Disable buttons
    const buttons = document.querySelectorAll('.clean-btn');
    buttons.forEach(b => b.disabled = true);
    
    // API call
    fetch(`/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            code: code,
            student_id: 'web_user'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (resultsDiv) {
            // ✅ CLEAN JSON EXTRACTION
            let content = '';
            
            // Try to extract clean text
            if (data.response) {
                content = data.response;
                
                // Check if response is nested JSON
                if (typeof content === 'string' && content.includes('"response"')) {
                    try {
                        const nested = JSON.parse(content);
                        content = nested.response || content;
                    } catch(e) {
                        // Not nested JSON, continue
                    }
                }
            } else {
                // Fallback
                content = data.analysis || data.explanation || data.visualization || 
                          data.fixes || data.review || data.results || 
                          JSON.stringify(data, null, 2);
            }
            
            // ✅ CLEAN DISPLAY with proper formatting
            resultsDiv.innerHTML = `
                <div class="ai-rendered">
                    ${renderMarkdown(content)}
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('API Error:', error);
        if (resultsDiv) {
            resultsDiv.innerHTML = `<div style="color: red; padding: 20px;">Error: ${error.message}</div>`;
        }
    })
    .finally(() => {
        buttons.forEach(b => b.disabled = false);
    });
}

// Button functions matching HTML onclick attributes
function analyzeBtn() {
    callAPI('analyze');
}

function explainBtn() {
    callAPI('explain');
}

function visualBtn() {
    callAPI('visual_explanation');
}

function suggestFixesBtn() {
    callAPI('suggest_fixes');
}

function securityReviewBtn() {
    callAPI('secure_review');
}

function runTestsBtn() {
    callAPI('run_tests');
}

function testAIBtn() {
    callAPI('test_ai');
}

console.log('✅ Global button functions loaded!');

// ========== END OF GLOBAL FUNCTIONS ==========

// CRITICAL FIX: Wait for complete page load
window.addEventListener('load', function() {
    console.log('🚀 Synapse AI Tutor - Enhanced Version Loading...');

    // DEBUG: Check if critical elements exist
    console.log('🔍 Checking critical elements...');
    console.log('- codeInput:', !!document.getElementById('codeInput'));
    console.log('- moodInput:', !!document.getElementById('moodInput'));
    console.log('- results:', !!document.getElementById('results'));
    console.log('- analyzeBtn:', !!document.getElementById('analyzeBtn'));

    // ========== MERMAID INITIALIZATION ==========
    if (typeof mermaid !== 'undefined') {
        try {
            mermaid.initialize({
                startOnLoad: false,
                theme: 'default',
                securityLevel: 'loose'
            });
            console.log('✅ Mermaid initialized');
        } catch (e) {
            console.warn('⚠️ Mermaid init failed:', e);
        }
    }

    // ========== STATE VARIABLES (DECLARED ONCE!) ==========
    const elements = {
        codeInput: document.getElementById('codeInput'),
        moodInput: document.getElementById('moodInput'),
        resultsDiv: document.getElementById('results')
    };

    const state = {
        currentFontSize: 16,
        readingPointerActive: false,
        calmingAudioActive: false,
        highContrastActive: false,
        focusAssistActive: false,
        currentAudioIndex: 0,
        accessibilityExpanded: false,
        learningStateMinimized: false
    };

    let conversationId = null;
    let lastEmotionState = null;

    
    // ========== HELPER FUNCTIONS ==========
    function processResponseText(text) {
        if (!text) return "";
        text = text.replace(/\\n/g, '\n');
        text = text.replace(/\\t/g, '\t');
        text = text.replace(/\\"/g, '"');
        text = text.replace(/\\\\/g, '\\');
        text = text.replace(/\\u([0-9a-fA-F]{4})/g, (match, grp) =>
            String.fromCharCode(parseInt(grp, 16))
        );
        return text;
    }

    function processImageUrls(text) {
        if (!text) return "";
        text = text.replace(
            /(https:\/\/oaidalleapiprodscus\.blob\.core\.windows\.net\/[^\s)]+)/gi,        
            (url) => {
                const cleanUrl = url.replace(/[)]*$/, '');
                return `<a href="${cleanUrl}" target="_blank" style="display: inline-block; margin: 5px; padding: 8px 12px; background: #4facfe; color: white; text-decoration: none; border-radius: 6px;">View AI Image</a>`;
            }
        );
        return text;
    }

    // ========== MAIN API FUNCTION ==========
    async function callAPIEnhanced(endpoint) {
        console.log(`🚀 Calling API endpoint: ${endpoint}`);

        const code = elements.codeInput.value;
        const mood = elements.moodInput ? elements.moodInput.value : '';
        const buttons = document.querySelectorAll('.clean-btn');

        buttons.forEach(b => b.disabled = true);
        elements.resultsDiv.innerHTML = '<div class="loading"></div> Analyzing... Please wait.';

        try {
            const response = await fetch('/' + endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code: code,
                    user_message: mood,
                    student_id: 'web_user'
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('📦 Raw API Response:', data);

            let text = data.response || "";
            let emotionState = data.emotion_state;

            // CRITICAL FIX: Clean nested JSON from response
            if (typeof text === 'string' && text.includes('"response"')) {
                try {
                    const parsed = JSON.parse(text);
                    text = parsed.response || text;
                    if (parsed.emotion_state && !emotionState) {
                        emotionState = parsed.emotion_state;
                    }
                } catch (e) {
                    const match = text.match(/"response":\s*"((?:[^"\\]|\\.)*)"/);
                    if (match) {
                        text = match[1];
                    }
                }
            }

            console.log('�� Cleaned text:', text.substring(0, 100));

            
            // Check for visual data (Mermaid diagrams)
            try {
                const visualData = JSON.parse(text);
                if (visualData.analogy && visualData.mermaid_code) {
                    const processedAnalogy = processResponseText(visualData.analogy);      
                    elements.resultsDiv.innerHTML = `
                        <div style="padding: 20px; background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%); border-radius: 12px; margin-bottom: 20px; border-left: 4px solid #4facfe;">
                            <h4 style="margin: 0 0 10px 0; color: #2d3748;">📊 Visual Explanation</h4>
                            <pre style="white-space: pre-wrap; font-family: 'Segoe UI', sans-serif; font-size: ${state.currentFontSize}px; line-height: 1.6; margin: 0;">${processedAnalogy}</pre>
                        </div>
                        <div class="mermaid" style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0;">${visualData.mermaid_code}</div>
                    `;
                    if (typeof mermaid !== 'undefined' && mermaid.run) {
                        await mermaid.run();
                    }
                    return;
                }
            } catch (_) {
                // Not visual data, continue
            }

            // Process and display text
            text = processResponseText(text);
            text = processImageUrls(text);

            elements.resultsDiv.innerHTML = `
                <div class="ai-rendered" style="font-size: ${state.currentFontSize}px;">
                    ${renderMarkdown(text)}
                </div>
            `;

        } catch (error) {
            console.error('❌ API Error:', error);
            elements.resultsDiv.innerHTML = `
                <div style="color: #ef4444; padding: 15px; background: #fef2f2; border-radius: 8px; border: 1px solid #fecaca;">
                    <strong>⚠️ Error:</strong> ${error.message}<br><br>
                    Please check if the server is running properly.
                </div>
            `;
        } finally {
            buttons.forEach(b => b.disabled = false);
            enableChat();
        }
    }

    // ========== INTERACTIVE LEARNING ==========
    window.checkSecurityAnswers = function() {
        const answer1 = document.getElementById('answer1');
        const answer2 = document.getElementById('answer2');
        const answer3 = document.getElementById('answer3');

        if (!answer1 || !answer2 || !answer3) {
            alert('Please fill in all answers first');
            return;
        }

        const feedbackDiv = document.getElementById('feedback');
        if (!feedbackDiv) return;

        let correct = 0;
        let feedback = '<h5>📊 Results:</h5>';

        if (answer1.value.toLowerCase().includes('isinstance') ||
            answer1.value.toLowerCase().includes('type')) {
            feedback += '<div style="color: green; margin: 5px 0;">✅ Input validation: Correct!</div>';
            correct++;
        } else {
            feedback += '<div style="color: red; margin: 5px 0;">❌ Input validation: Try isinstance()</div>';
        }

        if (answer2.value.trim() === '?') {
            feedback += '<div style="color: green; margin: 5px 0;">✅ SQL placeholder: Correct!</div>';
            correct++;
        } else {
            feedback += '<div style="color: red; margin: 5px 0;">❌ SQL placeholder: Use ?</div>';
        }

        if (answer3.value.trim() === 'user_id') {
            feedback += '<div style="color: green; margin: 5px 0;">✅ Parameter: Correct!</div>';
            correct++;
        } else {
            feedback += '<div style="color: red; margin: 5px 0;">❌ Parameter: Should be user_id</div>';
        }

        if (correct === 3) {
            feedback += '<div style="background: #d1fae5; padding: 10px; margin-top: 10px; border-radius: 6px;"><strong>🎉 Perfect!</strong></div>';
        } else {
            feedback += '<div style="background: #fef3c7; padding: 10px; margin-top: 10px; border-radius: 6px;"><strong>💪 Keep trying! ' + correct + '/3 correct</strong></div>';    
        }

        feedbackDiv.innerHTML = feedback;
        feedbackDiv.style.display = 'block';
    }

    window.getHint = function() {
        let hintDiv = document.getElementById('hint');
        if (!hintDiv) {
            const container = document.getElementById('results');
            if (container) {
                hintDiv = document.createElement('div');
                hintDiv.id = 'hint';
                hintDiv.style.cssText = 'margin-top: 15px; padding: 10px; background: #fef3c7; border-radius: 6px;';
                container.appendChild(hintDiv);
            }
        }

        const hints = [
            '💡 Hint 1: Use isinstance(user_id, (str, int))',
            '💡 Hint 2: Use ? for SQL placeholder',
            '💡 Hint 3: Pass user_id as parameter'
        ];

        if (!window.currentHintIndex) window.currentHintIndex = 0;

        if (hintDiv) {
            hintDiv.innerHTML = '<strong>' + hints[window.currentHintIndex] + '</strong>'; 
            hintDiv.style.display = 'block';
            window.currentHintIndex = (window.currentHintIndex + 1) % hints.length;        
        }
    }

    window.showSolution = function() {
        const answer1 = document.getElementById('answer1');
        const answer2 = document.getElementById('answer2');
        const answer3 = document.getElementById('answer3');

        if (answer1) answer1.value = 'isinstance(user_id, (str, int))';
        if (answer2) answer2.value = '?';
        if (answer3) answer3.value = 'user_id';

        const feedbackDiv = document.getElementById('feedback');
        if (feedbackDiv) {
            feedbackDiv.innerHTML = `
                <h5>📚 Solution:</h5>
                <div style="background: #e0f2fe; padding: 15px; border-radius: 6px;">      
                    • isinstance() validates type<br>
                    • ? prevents SQL injection<br>
                    • user_id passes safely
                </div>
            `;
            feedbackDiv.style.display = 'block';
        }
    }

    window.highlightVulnerability = function(lineElement, lineNumber) {
        document.querySelectorAll('.highlighted-line').forEach(el => {
            el.style.background = 'transparent';
            el.classList.remove('highlighted-line');
        });

        lineElement.style.background = 'rgba(124, 58, 237, 0.3)';
        lineElement.classList.add('highlighted-line');

        const feedbackDiv = document.getElementById('debug_feedback');
        if (!feedbackDiv) return;

        const lineText = lineElement.textContent;
        if (lineText.includes('f"') || lineText.includes("f'")) {
            feedbackDiv.innerHTML = '<div style="background: #d1fae5; padding: 10px; border-radius: 6px;"><strong>🎯 Correct!</strong></div>';
        } else {
            feedbackDiv.innerHTML = '<div style="background: #fef2f2; padding: 10px; border-radius: 6px;"><strong>🤔 Try again!</strong></div>';
        }
        feedbackDiv.style.display = 'block';
    }

		// ========== CHAT FUNCTIONS ==========
		function enableChat() {
			const chatCard = document.getElementById('chatCard');
			if (chatCard) {
				chatCard.style.display = 'block';
				console.log('💬 Chat enabled');
			}
		}

		// ========== CHAT FUNCTIONS - CLEAN VERSION ==========

	window.sendChatMessage = function() {
		const input = document.getElementById('chatInput');
		const message = input.value.trim();
		if (!message || input.disabled) return;

		input.disabled = true;
		addChatMessage('user', message);
		input.value = '';
		addChatMessage('assistant', '...', true);

		fetch('/chat_followup', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				message: message,
				conversation_id: conversationId,
				student_id: 'web_user',
				code: elements.codeInput.value
			})
		})
		.then(response => response.json())
		.then(data => {
			removeChatTyping();

			// ✅ CLEAN JSON EXTRACTION - Remove nested JSON wrapper
			let responseText = 'Processing...';
			
			if (data.response) {
				responseText = data.response;
				
				// Check if response contains nested JSON string
				if (typeof responseText === 'string' && responseText.includes('"response"')) {
					try {
						const nested = JSON.parse(responseText);
						responseText = nested.response || responseText;
					} catch(e) {
						// Not valid JSON, use as-is
						console.log('Response is not nested JSON');
					}
				}
				
				// Remove escaped newlines and format properly
				responseText = responseText
					.replace(/\\n/g, '\n')
					.replace(/\\t/g, '\t')
					.replace(/\\"/g, '"');
			}
			
			addChatMessage('assistant', responseText);

			if (data.conversation_id) {
				conversationId = data.conversation_id;
			}
		})
		.catch(error => {
			removeChatTyping();
			addChatMessage('assistant', 'Error occurred. Please try again.');
			console.error('💬 Chat error:', error);
		})
		.finally(() => {
			input.disabled = false;
			input.focus();
		});
	}

	function addChatMessage(role, message, isTyping = false) {
		const chatDiv = document.getElementById('chatHistory');
		if (!chatDiv) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${role} ${isTyping ? 'typing' : ''}`;
    
    // ✅ CLEAN MESSAGE FORMATTING
    let formattedMessage = message;
    
    if (!isTyping) {
        // Convert newlines to <br>
        formattedMessage = formattedMessage.replace(/\n/g, '<br>');
        
        // Convert markdown-style bold **text** to <strong>
        formattedMessage = formattedMessage.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Convert markdown-style code `text` to <code>
        formattedMessage = formattedMessage.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Convert bullet points • to proper list items
        if (formattedMessage.includes('•')) {
            const lines = formattedMessage.split('<br>');
            formattedMessage = lines.map(line => {
                if (line.trim().startsWith('•')) {
                    return `<div style="padding-left: 20px; margin: 5px 0;">${line}</div>`;
                }
                return line;
            }).join('<br>');
        }
        
        // Add spacing around emoji headers (🎯, 📝, ⚠️, etc.)
        formattedMessage = formattedMessage.replace(/([🎯📝⚠️✅❌🔍💡🚀])\s*([^<br>]+)/g, 
            '<div style="margin-top: 15px; margin-bottom: 8px; font-weight: 600; color: #667eea;">$1 $2</div>');
        
        // Add spacing around horizontal rules
        formattedMessage = formattedMessage.replace(/---/g, 
            '<hr style="margin: 20px 0; border: none; border-top: 2px solid #e2e8f0;">');
    }
    
    msgDiv.innerHTML = `
        <div class="message-header">${role === 'user' ? '👤 You' : '🤖 Tutor'}</div>
        <div class="message-content" style="line-height: 1.8;">${formattedMessage}</div>
        ${!isTyping ? `<div class="message-time">${new Date().toLocaleTimeString()}</div>` : ''}
    `;
    
    chatDiv.appendChild(msgDiv);
    chatDiv.scrollTop = chatDiv.scrollHeight;
}

function removeChatTyping() {
    const typingMsgs = document.querySelectorAll('.chat-message.typing');
    typingMsgs.forEach(msg => msg.remove());
}

    window.clearChat = function() {
        if (confirm('Clear chat?')) {
            const chatDiv = document.getElementById('chatHistory');
            if (chatDiv) chatDiv.innerHTML = '';
            conversationId = null;
        }
    }

    // ========== CODE TEMPLATES ==========
    function loadCodeTemplate(templateName) {
        const templates = {
            'sql-injection': `def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = '{user_id}'" # Vulnerable
    return execute_query(query)`,
            'xss': `def render_comment(user_input):
    return f"<div>{user_input}</div>"  # XSS vulnerable`,
            'secure-example': `def get_user_secure(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    return execute_query(query, [user_id])  # Safe!`,
            'clear': ''
        };
        if (templates[templateName] !== undefined) {
            elements.codeInput.value = templates[templateName];
            console.log(`📝 Template: ${templateName}`);
        }
    }

    // ========== EVENT LISTENERS ==========
    // NOTE: HTML has inline onclick handlers, so we only add listeners for elements without them
    console.log('🔌 Connecting event listeners...');

    const buttonMappings = {
        'analyzeBtn': () => callAPIEnhanced('analyze'),
        'explainBtn': () => callAPIEnhanced('explain'),
        'visualBtn': () => callAPIEnhanced('visual_explanation'),
        'suggestFixesBtn': () => callAPIEnhanced('suggest_fixes'),
        'securityReviewBtn': () => callAPIEnhanced('secure_review'),
        'runTestsBtn': () => callAPIEnhanced('run_tests'),
        'testAIBtn': () => callAPIEnhanced('test_ai')
    };

    let connectedButtons = 0;
    Object.entries(buttonMappings).forEach(([id, handler]) => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', function(e) {
                console.log(`🖱️ Clicked: ${id}`);
                handler();
            });
            connectedButtons++;
            console.log(`✅ ${id}`);
        } else {
            console.error(`❌ NOT FOUND: ${id}`);
        }
    });

    console.log(`📊 Main buttons: ${connectedButtons}/${Object.keys(buttonMappings).length}`);

    // Template buttons
    document.querySelectorAll('.template-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const template = e.target.dataset.template;
            if (template) {
                loadCodeTemplate(template);
            }
        });
    });

    // Chat Enter key
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    // Utility buttons
    const clearBtn = document.getElementById('clearResultsBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            elements.resultsDiv.innerHTML = '<p>✨ Results cleared!</p>';
        });
    }

    const copyBtn = document.getElementById('copyResultBtn');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const text = elements.resultsDiv.textContent;
            navigator.clipboard.writeText(text).then(() => {
                alert('✅ Copied!');
            }).catch(() => {
                alert('❌ Copy failed');
            });
        });
    }

    // ========== STYLES ==========
    const style = document.createElement('style');
    style.textContent = `
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #4facfe;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .buttons-grid {
            display: grid;
            gap: 12px !important;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        }
        a.clean-btn, .buttons-grid a.clean-btn {
            text-decoration: none !important;
        }
        .clean-btn, .nav-btn, .template-btn {
            margin: 4px !important;
        }
        .template-btn {
            padding: 8px 14px;
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.3s ease;
            color: #2d3748;
        }
        .template-btn:hover {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transform: translateY(-2px);
        }
        .chat-history {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
            padding: 15px;
            margin-bottom: 15px;
            background: #f8fafc;
            border-radius: 8px;
        }
        .chat-message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 8px;
            animation: fadeIn 0.3s ease;
        }
        .chat-message.user {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-left: 20%;
        }
        .chat-message.assistant {
            background: white;
            border: 1px solid #e2e8f0;
            margin-right: 20%;
        }
        .message-header {
            font-weight: 600;
            margin-bottom: 5px;
            font-size: 14px;
        }
        .message-content {
            line-height: 1.6;
        }
        .message-time {
            font-size: 11px;
            opacity: 0.7;
            margin-top: 5px;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .highlighted-line {
            background: rgba(124, 58, 237, 0.3) !important;
            transition: background 0.3s ease;
            cursor: pointer;
        }
        #feedback, #hint, #debug_feedback {
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        input[type="text"]#answer1,
        input[type="text"]#answer2,
        input[type="text"]#answer3 {
            background: #374151;
            color: white;
            border: 1px solid #6b7280;
            padding: 4px 8px;
            border-radius: 4px;
            font-family: monospace;
            min-width: 120px;
        }
        .dark-mode .chat-message.assistant {
            background: #2d3748;
            color: #e2e8f0;
            border-color: #4a5568;
        }
        .dark-mode #emotionDisplay {
            background: #2d3748;
            color: #e2e8f0;
            border-color: #667eea;
        }
        .nav-btn.active {
            background: #4facfe !important;
            color: white !important;
            border-color: #4facfe !important;
        }
        .hidden {
            display: none !important;
        }

    `;
    document.head.appendChild(style);

    // Initialize
   // createEmotionDisplay();

    console.log('✅ Script fully loaded!');
    console.log('🔍 If buttons don\'t work, check errors above');
});

// ========== ADVANCED TOOLS FUNCTIONS ==========
function openAdvancedTools() {
    console.log('🛠️ Navigating to Advanced Tools...');
    window.location.href = '/tools';
}

console.log('✅ Advanced Tools functions loaded');

// ========== EXERCISES FUNCTIONS ==========
async function runExercise(exerciseNum) {
    console.log(`🎯 Running exercise ${exerciseNum}`);

    const code = document.getElementById(`code-ex${exerciseNum}`).value;
    const resultDiv = document.getElementById(`result-ex${exerciseNum}`);
    const feedbackDiv = document.getElementById(`feedback-ex${exerciseNum}`);
    const outputDiv = document.getElementById(`output-ex${exerciseNum}`);

    if (!code.trim()) {
        alert('⚠️ Please write some code first!');
        return;
    }

    // Show result section
    resultDiv.style.display = 'block';

    // Show loading
    feedbackDiv.innerHTML = '<p>🔄 AI is analyzing your code...</p>';
    outputDiv.textContent = '';

    try {
        const response = await fetch('/api/check-exercise', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                exercise_id: `finance-ex${exerciseNum}`,
                language: 'python'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();

        // Display AI feedback
        if (result.is_correct) {
            feedbackDiv.innerHTML = `
                <p style="font-size: 17px; font-weight: bold; color: #2e7d32;">
                    🎉 EXCELLENT WORK!
                </p>
                <p>${result.feedback}</p>
                ${result.suggestion ? `<p><strong>�� Next:</strong> ${result.suggestion}</p>` : ''}
            `;
        } else {
            feedbackDiv.innerHTML = `
                <p style="font-size: 17px; font-weight: bold; color: #f57c00;">
                    💪 You're almost there!
                </p>
                <p>${result.feedback}</p>
                ${result.hint ? `<p><strong>🔧 Try:</strong> ${result.hint}</p>` : ''}     
            `;
        }

        // Display output
        if (result.output) {
            outputDiv.textContent = result.output;
        }

        console.log('✅ Exercise feedback received');

    } catch (error) {
        console.error('❌ Exercise error:', error);
        feedbackDiv.innerHTML = `
            <p style="color: #d32f2f; font-weight: bold;">⚠️ Connection Error</p>
            <p>Could not reach AI. Try again!</p>
            <p style="font-size: 12px; color: #666;">Error: ${error.message}</p>
        `;
    }
}

console.log('✅ Exercise functions loaded');

console.log('✅ All JavaScript functions loaded successfully!');

