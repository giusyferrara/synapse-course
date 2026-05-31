with open('templates/dashboard.html', 'r') as f:
    content = f.read()

# Nuova funzione che usa participants invece di sessions
new_function = '''        function populateSessions() {
            const participants = researchData.participants || [];
            const sessionsTable = document.getElementById('sessionsTable');
            
            if (participants.length === 0) {
                sessionsTable.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #64748b;">No research sessions yet</td></tr>';
                return;
            }
            
            sessionsTable.innerHTML = participants
                .filter(p => p.task_completed)  // Solo chi ha fatto il task
                .slice(0, 20)
                .map((p, index) => {
                    const duration = p.task_elapsed_time ? `${Math.floor(p.task_elapsed_time / 60)}m ${p.task_elapsed_time % 60}s` : 'N/A';
                    const date = p.signup_date ? new Date(p.signup_date).toLocaleDateString() : 'N/A';
                    const group = p.group || 'Unknown';
                    const score = p.score_total || 'N/A';
                    
                    return `
                        <tr>
                            <td style="font-family: monospace; font-size: 12px;">${index + 1}</td>
                            <td><strong>${p.code || 'Anonymous'}</strong></td>
                            <td><span class="participant-badge">${group}</span></td>
                            <td>${date}</td>
                            <td>${duration}</td>
                            <td><strong>${score}</strong></td>
                        </tr>
                    `;
                }).join('');
        }'''

# Sostituisci la vecchia funzione
old_function = '''        function populateSessions() {
            const sessions = researchData.sessions || [];
            const participants = researchData.participants || [];
            const sessionsTable = document.getElementById('sessionsTable');
            sessionsTable.innerHTML = sessions.slice(0, 20).map(s => {
                const participant = participants.find(p => p.code === s.participant_code);
                const group = participant?.group || 'Unknown';
                const duration = s.duration ? `${Math.floor(s.duration / 60)}m` : 'N/A';
                const date = s.start_time ? new Date(s.start_time).toLocaleDateString() : 'N/A';
                return `
                    <tr>
                        <td style="font-family: monospace; font-size: 11px;">${s.session_id.substring(0, 20)}...</td>
                        <td><strong>${s.participant_code || 'Anonymous'}</strong></td>
                        <td><span class="participant-badge">${group}</span></td>
                        <td>${date}</td>
                        <td>${duration}</td>
                        <td>${s.interactions || 0}</td>
                    </tr>
                `;
            }).join('');
        }'''

content = content.replace(old_function, new_function)

# Aggiorna anche l'header della tabella per riflettere i nuovi dati
old_header = '''<thead>
                            <tr>
                                <th>Session ID</th>
                                <th>Participant</th>
                                <th>Group</th>
                                <th>Date</th>
                                <th>Duration</th>
                                <th>Interactions</th>
                            </tr>
                        </thead>'''

new_header = '''<thead>
                            <tr>
                                <th>#</th>
                                <th>Participant</th>
                                <th>Group</th>
                                <th>Date</th>
                                <th>Duration</th>
                                <th>Score</th>
                            </tr>
                        </thead>'''

content = content.replace(old_header, new_header)

with open('templates/dashboard.html', 'w') as f:
    f.write(content)

print("✅ Fixed sessions table!")
print("   - Now shows research participants")
print("   - Displays: #, Participant, Group, Date, Duration, Score")
