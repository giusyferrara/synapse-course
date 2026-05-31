with open('templates/research/research_task.html', 'r') as f:
    content = f.read()

# Fix 1: querySelector con backtick sbagliato
content = content.replace(
    'document.querySelector`[data-model="${model}"]`)',
    'document.querySelector(`[data-model="${model}"]`)'
)

# Fix 2: addMessage con backtick sbagliato
content = content.replace(
    'addMessage`Switched to ${model.toUpperCase()}`, \'ai\')',
    'addMessage(`Switched to ${model.toUpperCase()}`, \'ai\')'
)

with open('templates/research/research_task.html', 'w') as f:
    f.write(content)

print("✅ Fixed backticks!")
