with open('templates/dashboard.html', 'r') as f:
    lines = f.readlines()

# Trova tutte le righe con "label: 'ADHD'" e cambia il backgroundColor nella riga successiva
i = 0
while i < len(lines):
    if "'ADHD'" in lines[i] or '"ADHD"' in lines[i]:
        # Cerca backgroundColor nelle prossime 10 righe
        for j in range(i, min(i+10, len(lines))):
            if 'backgroundColor' in lines[j] and '#667eea' in lines[j]:
                lines[j] = lines[j].replace('#667eea', '#FF6B6B')
                print(f"Changed line {j+1}: ADHD color to red")
    i += 1

with open('templates/dashboard.html', 'w') as f:
    f.writelines(lines)

print("✅ Fixed ADHD chart colors to red!")
