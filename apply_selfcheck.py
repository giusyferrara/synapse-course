#!/usr/bin/env python3
"""Transform Submit Findings into Self-Check with local validation"""
from pathlib import Path

p = Path('templates/research/research_task.html')
content = p.read_text(encoding='utf-8')

# 1) Change button text
old_btn = '<button class="submit-btn" id="submitTaskBtn" onclick="submitTask()">&#128228; Submit Findings</button>'
new_btn = '<button class="submit-btn" id="submitTaskBtn" onclick="submitTask()">&#9989; Check My Answers</button>'
if old_btn not in content:
    print("ERROR: button not found")
    exit(1)
content = content.replace(old_btn, new_btn)

# 2) Replace submitTask function (with blank lines exactly as in file)
old_func = """async function submitTask() {
    const filledFindings = findings.filter(f => f.cwe_code);

    if (filledFindings.length === 0) {
        if (!confirm('You have not documented any findings yet. Are you sure you want to submit?')) return;
    } else {
        if (!confirm('Submit ' + filledFindings.length + ' findings? You cannot change them after submitting.')) return;
    }

    const btn = document.getElementById('submitTaskBtn');
    btn.disabled = true;
    btn.textContent = 'Submitting...';

    const elapsed = taskStartTime ? Math.floor((Date.now() - taskStartTime.getTime()) / 1000) : 0;

    const payload = {
        participant_code: participantCode,
        vulnerability_findings: filledFindings,
        elapsed_time: elapsed,
        time_remaining: totalSeconds,
        // interaction_logs collected via log_interaction API \u2014 don't overwrite
        ai_messages_count: document.querySelectorAll('.chat-msg.assistant').length,
        ai_hints_requested: 0,
        ai_encouragements_sent: encouragementCount
    };

    try {
        const resp = await fetch('/api/research/submit_task', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await resp.json();

        if (result.success) {
            clearInterval(timerInterval);
            clearInterval(autoSaveInterval);
            clearInterval(idleCheckInterval);
            // Go to post-test
            window.location.href = '/research/post_test?participant=' + participantCode;
        } else {
            alert('Error submitting: ' + (result.error || 'Unknown error'));
            btn.disabled = false;
            btn.textContent = '\\uD83D\\uDCE8 Submit Findings';
        }
    } catch (err) {
        alert('Connection error. Your findings are auto-saved. Please try again.');
        btn.disabled = false;
        btn.textContent = '\\uD83D\\uDCE8 Submit Findings';
    }
}"""

new_func = '''async function submitTask() {
    const filledFindings = findings.filter(f => f.cwe_code);
    if (filledFindings.length === 0) {
        alert('Please document at least one finding before checking your answers.');
        return;
    }
    const ciaPreferred = {
        'CWE-502': ['Confidentiality + Integrity + Availability', 'Integrity + Availability'],
        'CWE-22': ['Confidentiality', 'Confidentiality + Integrity'],
        'CWE-352': ['Integrity', 'Confidentiality + Integrity', 'Integrity + Availability']
    };
    let totalPoints = 0;
    const maxPoints = filledFindings.length * 3;
    let perFindingHtml = '';
    filledFindings.forEach(function(f) {
        perFindingHtml += '<div style="background:#f8fafc;border-left:4px solid #6366f1;padding:16px;margin-bottom:16px;border-radius:8px">';
        perFindingHtml += '<h3 style="color:#4f46e5;margin-bottom:12px">' + f.cwe_code + '</h3>';
        const mit = f.mitigation || '';
        if (mit.indexOf('_correct') !== -1) {
            totalPoints++;
            perFindingHtml += '<p style="color:#16a34a;margin-bottom:8px">\\u2713 <strong>Mitigation correct</strong> \\u2014 you identified an effective defence.</p>';
        } else if (mit) {
            perFindingHtml += '<p style="color:#dc2626;margin-bottom:8px">\\u2717 <strong>Mitigation needs review</strong> \\u2014 the option you chose does not fully prevent this vulnerability. Re-read the AI tutor explanation.</p>';
        } else {
            perFindingHtml += '<p style="color:#f59e0b;margin-bottom:8px">\\u26a0 <strong>Mitigation not selected</strong></p>';
        }
        const cia = f.impact_cia || '';
        const ciaIdeal = ciaPreferred[f.cwe_code] || [];
        if (ciaIdeal.indexOf(cia) !== -1) {
            totalPoints++;
            perFindingHtml += '<p style="color:#16a34a;margin-bottom:8px">\\u2713 <strong>CIA impact appropriate</strong> \\u2014 your assessment matches the threat model.</p>';
        } else if (cia) {
            perFindingHtml += '<p style="color:#f59e0b;margin-bottom:8px">\\u26a0 <strong>CIA impact partial</strong> \\u2014 consider: ' + (ciaIdeal[0] || 'Confidentiality') + '.</p>';
        } else {
            perFindingHtml += '<p style="color:#f59e0b;margin-bottom:8px">\\u26a0 <strong>CIA impact not selected</strong></p>';
        }
        const attacks = f.attacks || [];
        if (Array.isArray(attacks) && attacks.length > 0) {
            totalPoints++;
            perFindingHtml += '<p style="color:#16a34a">\\u2713 <strong>Attack documented</strong> \\u2014 ' + attacks.length + ' technique' + (attacks.length>1?'s':'') + ' identified.</p>';
        } else {
            perFindingHtml += '<p style="color:#f59e0b">\\u26a0 <strong>No attack technique documented</strong></p>';
        }
        perFindingHtml += '</div>';
    });
    const percent = Math.round((totalPoints / maxPoints) * 100);
    let scoreColor = '#dc2626';
    let scoreLabel = 'Needs more practice';
    if (percent >= 80) { scoreColor = '#16a34a'; scoreLabel = 'Excellent \\u2014 strong mastery'; }
    else if (percent >= 60) { scoreColor = '#0891b2'; scoreLabel = 'Good \\u2014 solid understanding'; }
    else if (percent >= 40) { scoreColor = '#f59e0b'; scoreLabel = 'Partial \\u2014 review the weakest areas'; }
    const scoreBlock = '<div style="background:linear-gradient(135deg,' + scoreColor + '15,' + scoreColor + '05);border:2px solid ' + scoreColor + ';padding:20px;border-radius:12px;text-align:center;margin-bottom:24px"><div style="font-size:48px;font-weight:800;color:' + scoreColor + '">' + totalPoints + '/' + maxPoints + '</div><div style="color:' + scoreColor + ';font-weight:600;margin-top:4px">' + scoreLabel + '</div></div>';
    const closeBtn = '<div style="text-align:center;margin-top:24px"><button onclick="closeSelfCheck()" style="padding:12px 32px;background:linear-gradient(135deg,#6366f1,#4f46e5);color:white;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer">Close</button></div>';
    let modal = document.getElementById('selfCheckModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'selfCheckModal';
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:10000;display:flex;align-items:center;justify-content:center;padding:20px';
        document.body.appendChild(modal);
    }
    modal.innerHTML = '<div style="background:white;border-radius:16px;padding:32px;max-width:600px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.3)"><h2 style="color:#1e293b;margin-bottom:20px">\\ud83d\\udcca Self-Check Results</h2>' + scoreBlock + perFindingHtml + closeBtn + '</div>';
    modal.style.display = 'flex';
}
function closeSelfCheck() {
    const modal = document.getElementById('selfCheckModal');
    if (modal) modal.style.display = 'none';
}'''

if old_func not in content:
    print("ERROR: submitTask function not found")
    exit(1)
content = content.replace(old_func, new_func)

p.write_text(content, encoding='utf-8')
print("OK Submit Findings -> Self-Check with local validation")
