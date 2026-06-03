with open('templates/research/research_task.html', 'r') as f:
    content = f.read()

# Trova e sostituisci la funzione addMessage COMPLETAMENTE
import re

# Pattern per trovare l'intera funzione addMessage
old_function = re.search(r'function addMessage\(.*?\n\s+\}', content, re.DOTALL)

new_function = '''function addMessage(text, sender) {
                const messagesDiv = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `chat-message ${sender}`;
                
                if (sender === 'ai') {
                    // Process markdown code blocks
                    let formatted = text;
                    
                    // Replace ```python ... ``` with proper HTML
                    formatted = formatted.replace(/```python([\\s\\S]*?)```/g, function(match, code) {
                        return '<pre><code>' + code.trim() + '</code></pre>';
                    });
                    
                    // Replace ``` ... ``` (generic code blocks)
                    formatted = formatted.replace(/```([\\s\\S]*?)```/g, function(match, code) {
                        return '<pre><code>' + code.trim() + '</code></pre>';
                    });
                    
                    // Replace inline `code`
                    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
                    
                    // Replace newlines with <br> EXCEPT inside <pre>
                    formatted = formatted.split('</pre>').map((part, i, arr) => {
                        if (i < arr.length - 1) {
                            const parts = part.split('<pre>');
                            parts[0] = parts[0].replace(/\\n/g, '<br>');
                            return parts.join('<pre>');
                        }
                        return part.replace(/\\n/g, '<br>');
                    }).join('</pre>');
                    
                    messageDiv.innerHTML = formatted;
                } else {
                    messageDiv.textContent = text;
                }
                
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }'''

if old_function:
    content = content.replace(old_function.group(0), new_function)
    
with open('templates/research/research_task.html', 'w') as f:
    f.write(content)

print("✅ Fixed code formatting!")
