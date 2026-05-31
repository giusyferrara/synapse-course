#!/usr/bin/env python3
"""
Fix per i nomi dei campi AI in web/research_handlers.py
"""

# Leggi il file
with open('web/research_handlers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# REPLACEMENTS
replacements = [
    ("data.get('ai_awareness_1'", "data.get('ai_aware_1'"),
    ("data.get('ai_awareness_2'", "data.get('ai_aware_2'"),
    ("data.get('ai_awareness_3'", "data.get('ai_aware_3'"),
    ("data.get('ai_evaluation_1'", "data.get('ai_eval_1'"),
    ("data.get('ai_evaluation_2'", "data.get('ai_eval_2'"),
    ("data.get('ai_evaluation_3'", "data.get('ai_eval_3'"),
    ("data.get('chatgpt_cognitive_1'", "data.get('chatgpt_cog_1'"),
    ("data.get('chatgpt_cognitive_2'", "data.get('chatgpt_cog_2'"),
    ("data.get('chatgpt_cognitive_3'", "data.get('chatgpt_cog_3'"),
    ("data.get('usage_intention_1'", "data.get('usage_intent_1'"),
    ("data.get('usage_intention_2'", "data.get('usage_intent_2'"),
    ("data.get('usage_intention_3'", "data.get('usage_intent_3'"),
]

# Apply
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f"✅ {old} → {new}")

# Write back
with open('web/research_handlers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ File updated!")
