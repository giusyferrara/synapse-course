with open('templates/research/research_task.html', 'r') as f:
    content = f.read()

# Fix 1: Aggiungi CSS per code blocks
css_code = '''.chat-message pre {
    background: #2d2d2d;
    color: #f8f8f2;
    padding: 15px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 10px 0;
    font-family: 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.6;
}
.chat-message code {
    font-family: 'Courier New', monospace;
    background: #2d2d2d;
    color: #66d9ef;
    padding: 2px 6px;
    border-radius: 3px;
}
'''

# Inserisci dopo .chat-toggle-btn
content = content.replace('.chat-toggle-btn {', css_code + '.chat-toggle-btn {')

# Fix 2: Modifica addMessage
old = '''        function addMessage(text, sender) {
                const messagesDiv = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `chat-message ${sender}`;
                messageDiv.textContent = text;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }'''

new = '''        function addMessage(text, sender) {
                const messagesDiv = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `chat-message ${sender}`;
                
                // Format code blocks for AI responses
                if (sender === 'ai') {
                    let formatted = text;
                    // Python code blocks
                    formatted = formatted.replace(/```python\\n([\\s\\S]*?)```/g, '<pre><code>$1</code></pre>');
                    // Generic code blocks
                    formatted = formatted.replace(/```([\\s\\S]*?)```/g, '<pre><code>$1</code></pre>');
                    // Inline code
                    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
                    // Preserve line breaks
                    formatted = formatted.replace(/\\n/g, '<br>');
                    messageDiv.innerHTML = formatted;
                } else {
                    messageDiv.textContent = text;
                }
                
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }'''

content = content.replace(old, new)

with open('templates/research/research_task.html', 'w') as f:
    f.write(content)

print("✅ Fixed!")
print("   - CSS per code blocks")
print("   - JavaScript formatta Python code")
