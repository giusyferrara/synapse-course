# Fix JavaScript to send individual AI values
import re

file_path = 'templates/research/research_signup.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the formData section and replace it
old_pattern = r"const formData = \{.*?// Calculate total AI literacy"
new_formdata = """const formData = {
                // Demographics
                age: document.getElementById('age').value,
                email: document.getElementById('email').value,
                nickname: nickname,
                gender: document.getElementById('gender').value,
                study_program: document.getElementById('study_program').value,
                study_year: document.getElementById('study_year').value,

                // Neurodivergence
                neurodivergence: Array.from(document.querySelectorAll('input[name="neurodivergence"]:checked'))
                    .map(cb => cb.value),
                other_details: document.getElementById('other_details').value,

                // Programming experience
                python_experience: document.getElementById('python_experience').value,
                programming_experience: document.getElementById('programming_experience').value,
                motivation: document.getElementById('motivation').value,

                // Matplotlib (individual values)
                matplotlib_q1: document.getElementById('matplotlib_q1').value,
                matplotlib_q2: document.getElementById('matplotlib_q2').value,
                matplotlib_q3: document.getElementById('matplotlib_q3').value,
                matplotlib_q4: document.getElementById('matplotlib_q4').value,
                matplotlib_q5: document.querySelector('input[name="matplotlib_q5"]:checked')?.value,

                // AI Awareness (individual values)
                ai_aware_1: document.querySelector('input[name="ai_aware_1"]:checked')?.value,
                ai_aware_2: document.querySelector('input[name="ai_aware_2"]:checked')?.value,
                ai_aware_3: document.querySelector('input[name="ai_aware_3"]:checked')?.value,

                // AI Usage
                ai_usage_1: document.querySelector('input[name="ai_usage_1"]:checked')?.value,
                ai_usage_2: document.querySelector('input[name="ai_usage_2"]:checked')?.value,
                ai_usage_3: document.querySelector('input[name="ai_usage_3"]:checked')?.value,

                // AI Evaluation
                ai_eval_1: document.querySelector('input[name="ai_eval_1"]:checked')?.value,
                ai_eval_2: document.querySelector('input[name="ai_eval_2"]:checked')?.value,
                ai_eval_3: document.querySelector('input[name="ai_eval_3"]:checked')?.value,

                // AI Ethics
                ai_ethics_1: document.querySelector('input[name="ai_ethics_1"]:checked')?.value,
                ai_ethics_2: document.querySelector('input[name="ai_ethics_2"]:checked')?.value,
                ai_ethics_3: document.querySelector('input[name="ai_ethics_3"]:checked')?.value,

                // ChatGPT Cognitive
                chatgpt_cog_1: document.querySelector('input[name="chatgpt_cog_1"]:checked')?.value,
                chatgpt_cog_2: document.querySelector('input[name="chatgpt_cog_2"]:checked')?.value,
                chatgpt_cog_3: document.querySelector('input[name="chatgpt_cog_3"]:checked')?.value,

                // Usage Intention
                usage_intent_1: document.querySelector('input[name="usage_intent_1"]:checked')?.value,
                usage_intent_2: document.querySelector('input[name="usage_intent_2"]:checked')?.value,
                usage_intent_3: document.querySelector('input[name="usage_intent_3"]:checked')?.value,

                // Metadata
                consent: true,
                timestamp: new Date().toISOString()
            };

            // Calculate total AI literacy"""

content = re.sub(old_pattern, new_formdata, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ JavaScript fixed - now sends all individual AI values!")
