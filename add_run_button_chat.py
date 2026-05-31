with open('templates/research/research_task.html', 'r') as f:
    content = f.read()

# Trova la parte dove formatta i code blocks
old_replace = """formatted = formatted.replace(/```python([\\s\\S]*?)```/g, function(match, code) {
                        return '<pre><code>' + code.trim() + '</code></pre>';
                    });"""

new_replace = """formatted = formatted.replace(/```python([\\s\\S]*?)```/g, function(match, code) {
                        const codeId = 'code_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                        return '<div class="code-block-wrapper">' +
                               '<button class="run-code-btn" onclick="runChatCode(\'' + codeId + '\')">▶ Run Code</button>' +
                               '<pre><code id="' + codeId + '">' + code.trim() + '</code></pre>' +
                               '<div id="output_' + codeId + '" class="code-output"></div>' +
                               '</div>';
                    });"""

content = content.replace(old_replace, new_replace)

# Aggiungi CSS per il bottone Run
css_insert = """.code-block-wrapper {
    position: relative;
    margin: 15px 0;
}
.run-code-btn {
    position: absolute;
    top: 5px;
    right: 5px;
    background: #4CAF50;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 13px;
    font-weight: bold;
    z-index: 10;
}
.run-code-btn:hover {
    background: #45a049;
}
.code-output {
    margin-top: 10px;
    padding: 10px;
    background: #f5f5f5;
    border-radius: 8px;
    max-height: 400px;
    overflow: auto;
}
.code-output img {
    max-width: 100%;
    border-radius: 8px;
}
"""

# Inserisci dopo .chat-message code
content = content.replace('.chat-toggle-btn {', css_insert + '\n.chat-toggle-btn {')

# Aggiungi funzione JavaScript per eseguire il codice
js_function = """
        async function runChatCode(codeId) {
            const codeElement = document.getElementById(codeId);
            const outputElement = document.getElementById('output_' + codeId);
            const code = codeElement.textContent;
            
            outputElement.innerHTML = '<p style="color: #666;">⏳ Running...</p>';
            
            try {
                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({code: code})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    let html = '';
                    if (data.output) {
                        html += '<div style="white-space: pre-wrap; font-family: monospace; margin-bottom: 10px;">' + data.output + '</div>';
                    }
                    if (data.image) {
                        html += '<img src="data:image/png;base64,' + data.image + '" alt="Plot">';
                    }
                    outputElement.innerHTML = html || '<p style="color: green;">✅ Code executed successfully!</p>';
                } else {
                    outputElement.innerHTML = '<p style="color: red;">❌ Error: ' + (data.error || 'Unknown error') + '</p>';
                }
            } catch (error) {
                outputElement.innerHTML = '<p style="color: red;">❌ Error: ' + error.message + '</p>';
            }
        }
"""

# Inserisci prima della funzione sendMessage
content = content.replace('async function sendMessage() {', js_function + '\n        async function sendMessage() {')

with open('templates/research/research_task.html', 'w') as f:
    f.write(content)

print("✅ Added Run Code button to chat code blocks!")
