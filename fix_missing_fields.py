import re

with open('web/research_handlers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: neurodivergence_type - deve prendere array e convertirlo in stringa
old1 = "neurodivergence_type=data.get('neurodivergence_type'),"
new1 = """neurodivergence_type=','.join(data.get('neurodivergence', [])),"""
content = content.replace(old1, new1)

# Fix 2: neurodivergence_details - il form lo chiama 'other_details'
old2 = "neurodivergence_details=data.get('neurodivergence_details', ''),"
new2 = "neurodivergence_details=data.get('other_details', ''),"
content = content.replace(old2, new2)

# Fix 3: Aggiungi motivation dopo programming_experience
old3 = """programming_experience=data.get('programming_experience'),
                # Matplotlib Knowledge (Table 5)"""
new3 = """programming_experience=data.get('programming_experience'),
                motivation=data.get('motivation', ''),

                # Matplotlib Knowledge (Table 5)"""
content = content.replace(old3, new3)

with open('web/research_handlers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed:")
print("   - neurodivergence_type (array → string)")
print("   - neurodivergence_details → other_details")
print("   - Added motivation field")
