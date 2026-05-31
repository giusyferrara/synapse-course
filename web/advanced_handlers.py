# web/advanced_handlers.py
# ============================================
# 🚀 ULTIMATE VERSION v3.0 - NEURODIVERGENT-FRIENDLY AI
# Maximum Intelligence + Memory + Achievements + Progressive System
# + STEP-BY-STEP TEACHING RESPONSES
# ============================================

from mcp_coordinator import MCPCoordinator
import asyncio, re, json, traceback, random
from aiohttp import web
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64

# ============================================
# GLOBAL STATE
# ============================================
mcp_coordinator = None
student_profiles = {}
chat_history = defaultdict(list)
exercise_progress = defaultdict(lambda: {
    'completed': [], 'attempted': [], 'current_level': 'beginner',
    'achievements': [], 'streak': 0, 'last_activity': None, 
    'total_hints_used': 0, 'exercise_types_tried': []
})
learning_patterns = defaultdict(lambda: {
    'prefers_visual': 0, 'prefers_text': 0, 'needs_flowcharts': 0,
    'learns_by_doing': 0, 'needs_frequent_hints': 0, 'completes_fast': 0
})

DIFFICULTY_LEVELS = {
    'absolute_beginner': {'steps': '2-3', 'hints': 5, 'complexity': 0.5},
    'beginner': {'steps': '3-5', 'hints': 4, 'complexity': 1.0},
    'intermediate': {'steps': '5-7', 'hints': 3, 'complexity': 1.5},
    'advanced': {'steps': '7-10', 'hints': 2, 'complexity': 2.0},
    'expert': {'steps': '10+', 'hints': 1, 'complexity': 3.0}
}

# Achievement definitions
ACHIEVEMENTS = {
    'first_exercise': ('🎯 First Steps', lambda p, pr, pa: p['completed_exercises'] >= 1),
    'five_exercises': ('🚀 Getting Started', lambda p, pr, pa: p['completed_exercises'] >= 5),
    'ten_exercises': ('⚔️ Code Warrior', lambda p, pr, pa: p['completed_exercises'] >= 10),
    'twenty_exercises': ('🏆 Code Master', lambda p, pr, pa: p['completed_exercises'] >= 20),
    'streak_3': ('🔥 3-Day Streak', lambda p, pr, pa: p['streak_days'] >= 3),
    'streak_7': ('💪 Week Warrior', lambda p, pr, pa: p['streak_days'] >= 7),
    'visual_learner': ('👁️ Visual Thinker', lambda p, pr, pa: pa['prefers_visual'] >= 10),
    'help_seeker': ('🤔 Curious Mind', lambda p, pr, pa: p['total_messages'] >= 20),
    'level_up_intermediate': ('📈 Intermediate Coder', lambda p, pr, pa: p['current_level'] in ['intermediate', 'advanced']),
    'level_up_advanced': ('🎓 Advanced Programmer', lambda p, pr, pa: p['current_level'] == 'advanced'),
}

# ============================================
# 🎓 NEURODIVERGENT-FRIENDLY TEACHING SYSTEM
# ============================================

NEURODIVERGENT_SYSTEM_PROMPT = """You are an AI learning assistant for Synapse, a platform designed specifically for neurodivergent learners (ADHD, autism, dyslexia).

🎯 YOUR MISSION: TEACH step-by-step, don't just give answers.

CRITICAL RULES FOR NEURODIVERGENT LEARNERS:

1. **ALWAYS BREAK IT DOWN STEP-BY-STEP**
   - Never dump code without explanation
   - Number your steps clearly: "**Step 1:**", "**Step 2:**", etc.
   - Explain WHAT each line does AND WHY it matters

2. **USE CLEAR VISUAL STRUCTURE**
   - Use emojis for visual anchors (🎯 📊 ✨ 💡)
   - Short paragraphs (2-3 sentences max)
   - Blank lines between sections
   - Code blocks with inline comments

3. **EXPLAIN THE "WHY" NOT JUST THE "HOW"**
   - Use phrases like "This tells Python to..."
   - Connect to real-world concepts
   - Show what happens if they don't do something

4. **BE ENCOURAGING AND SUPPORTIVE**
   - Start with validation ("Great question!")
   - Use positive language
   - Celebrate progress
   - Offer to help more

5. **PROVIDE ACTIONABLE NEXT STEPS**
   - "Try it!" prompts
   - Suggestions for experimentation
   - Clear path forward

6. **RESPONSE STRUCTURE FOR CODE HELP:**
   - Opening (1 line) - Validate their question
   - Step-by-step breakdown - Each step numbered with explanation
   - Complete solution - "✨ Your complete code:"
   - Encouragement - "🎉 Try running this now!"
   - Optional enhancement - "🎨 Want to experiment?"

EXAMPLE GOOD RESPONSE:
"Great question! Let's build this bar chart together. 🎯

**Step 1: Draw the bars**
```python
plt.bar(categories, amounts)
```
This tells Python: 'Take my category names and draw bars with heights from amounts.'

**Step 2: Add labels**
```python
plt.title('My Budget')
plt.xlabel('Categories')
```
Labels help people understand what they're looking at!

✨ **Your complete code:**
```python
plt.bar(categories, amounts)
plt.title('My Budget')
plt.xlabel('Categories')
plt.show()
```

🎉 **Try running this now!**

🎨 **Want to experiment?** Try changing the color: `plt.bar(categories, amounts, color='skyblue')`"

Remember: You're not just solving their problem - you're teaching them HOW to solve problems."""

def adapt_response_to_struggle(response: str, struggle_level: int, is_visual_learner: bool = False) -> str:
    """Adapt response based on detected struggle level"""
    if struggle_level == 0:
        return response
    
    # Add supportive prefix for struggling students
    if struggle_level >= 2:
        prefix = "I can see you're working hard on this! Let's take it one small step at a time. 🤗\n\n"
        response = prefix + response
    
    # Add flowchart suggestion for high struggle
    if struggle_level >= 3:
        suffix = "\n\n💡 **Feeling stuck?** Try clicking the flowchart button - seeing the steps visually might help!"
        response += suffix
    
    # Add more visual elements for visual learners
    if is_visual_learner and struggle_level > 0:
        response = response.replace("Step 1:", "1️⃣ **Step 1:**")
        response = response.replace("Step 2:", "2️⃣ **Step 2:**")
        response = response.replace("Step 3:", "3️⃣ **Step 3:**")
        response = response.replace("Step 4:", "4️⃣ **Step 4:**")
    
    return response

async def init_mcp_for_exercises():
    global mcp_coordinator
    if mcp_coordinator is None:
        try:
            mcp_coordinator = MCPCoordinator()
            print("✅ MCP Coordinator - ULTIMATE VERSION v3.0 (Neurodivergent-Friendly)!")
            return True
        except Exception as e:
            print(f"⚠️ MCP init: {e}")
            return False
    return True

async def mcp_status(request):
    try:
        return web.json_response({
            'connected': True, 'tools_count': 7, 'status': 'active',
            'message': 'MCP ULTIMATE v3.0 - Neurodivergent-Friendly AI Teaching',
            'version': '3.0'
        })
    except Exception as e:
        return web.json_response({'connected': False, 'error': str(e)}, status=500)

# ============================================
# STUDENT PROFILE MANAGEMENT
# ============================================

def get_student_profile(student_id: str) -> dict:
    if student_id not in student_profiles:
        student_profiles[student_id] = {
            'id': student_id, 'created_at': datetime.now().isoformat(),
            'total_messages': 0, 'total_exercises': 0, 'completed_exercises': 0,
            'current_level': 'beginner', 'topics_mastered': [], 'topics_struggling': [],
            'preferred_learning_style': None, 'last_session': None,
            'achievements': [], 'streak_days': 0, 'best_streak': 0
        }
    return student_profiles[student_id]

def update_student_profile(student_id: str, updates: dict):
    profile = get_student_profile(student_id)
    profile.update(updates)
    profile['last_session'] = datetime.now().isoformat()
    
    # Auto level-up
    if profile['completed_exercises'] >= 15 and profile['current_level'] == 'beginner':
        profile['current_level'] = 'intermediate'
        check_achievement(student_id, 'level_up_intermediate')
    elif profile['completed_exercises'] >= 35 and profile['current_level'] == 'intermediate':
        profile['current_level'] = 'advanced'
        check_achievement(student_id, 'level_up_advanced')

def analyze_learning_style(student_id: str) -> str:
    patterns = learning_patterns[student_id]
    if patterns['prefers_visual'] > patterns['prefers_text'] * 1.5:
        return 'visual'
    elif patterns['prefers_text'] > patterns['prefers_visual'] * 1.5:
        return 'textual'
    return 'mixed'

# ============================================
# CHAT HISTORY
# ============================================

def add_to_chat_history(student_id: str, role: str, content: str, metadata: dict = None):
    chat_history[student_id].append({
        'role': role, 'content': content,
        'timestamp': datetime.now().isoformat(),
        'metadata': metadata or {}
    })
    if len(chat_history[student_id]) > 100:
        chat_history[student_id] = chat_history[student_id][-100:]

def get_recent_context(student_id: str, limit: int = 5) -> list:
    return chat_history[student_id][-limit:] if student_id in chat_history else []

def generate_session_summary(student_id: str) -> str:
    history = chat_history.get(student_id, [])
    if not history:
        return "Getting started"
    
    topics, exercises = set(), 0
    for msg in history[-20:]:
        if 'exercise' in msg['content'].lower():
            exercises += 1
        for topic in ['loop', 'function', 'list', 'graph', 'budget']:
            if topic in msg['content'].lower():
                topics.add(topic)
    
    parts = []
    if topics:
        parts.append(f"Topics: {', '.join(topics)}")
    if exercises:
        parts.append(f"{exercises} exercises")
    return " | ".join(parts) if parts else "Active learning"

# ============================================
# ACHIEVEMENT SYSTEM
# ============================================

def check_achievement(student_id: str, achievement_id: str) -> bool:
    profile = get_student_profile(student_id)
    if achievement_id in profile['achievements']:
        return False
    
    progress = exercise_progress[student_id]
    patterns = learning_patterns[student_id]
    achievement = ACHIEVEMENTS.get(achievement_id)
    
    if achievement and achievement[1](profile, progress, patterns):
        profile['achievements'].append(achievement_id)
        return True
    return False

def check_all_achievements(student_id: str) -> list:
    profile = get_student_profile(student_id)
    progress = exercise_progress[student_id]
    patterns = learning_patterns[student_id]
    new = []
    
    for ach_id, (ach_name, condition) in ACHIEVEMENTS.items():
        if ach_id not in profile['achievements']:
            if condition(profile, progress, patterns):
                profile['achievements'].append(ach_id)
                new.append(ach_name)
    return new

def detect_student_struggle(message: str, code: str = '') -> dict:
    """Detect if student is struggling"""
    message_lower = message.lower()
    
    struggle_keywords = [
        'help', 'stuck', 'confused', 'don\'t understand', 'not working',
        'error', 'wrong', 'difficult', 'hard', 'lost', 'what do i do',
        'how do i', 'can\'t', 'doesn\'t work', 'not sure'
    ]
    
    is_struggling = any(keyword in message_lower for keyword in struggle_keywords)
    has_minimal_code = len(code.strip()) < 20 if code else False
    has_errors_in_message = any(word in message_lower for word in ['error', 'traceback', 'exception'])
    
    struggle_level = 0
    if is_struggling:
        struggle_level += 1
    if has_minimal_code:
        struggle_level += 1
    if has_errors_in_message:
        struggle_level += 1
    
    return {
        'is_struggling': is_struggling or struggle_level >= 2,
        'struggle_level': struggle_level,
        'suggest_flowchart': is_struggling or has_errors_in_message,
        'suggest_simpler_exercise': has_minimal_code and is_struggling,
        'indicators': {
            'keywords_found': is_struggling,
            'minimal_code': has_minimal_code,
            'error_mentioned': has_errors_in_message
        }
    }


# ============================================
# 🚀 UPGRADED AI CHAT - NEURODIVERGENT-FRIENDLY
# ============================================

async def ai_chat(request):
    """UPGRADED AI Chat - Neurodivergent-Friendly Step-by-Step Teaching"""
    try:
        data = await request.json()
        message = data.get('message', '').strip()
        student_id = data.get('student_id', 'default_student')
        code = data.get('code', '')
        is_struggling = data.get('is_struggling', False)
        
        print(f"💬 [{student_id}]: {message[:80]}...")
        
        if not message:
            return web.json_response({
                'response': 'Please send a message! I\'m here to help. 💡',
                'graph_data': None, 'flowchart_code': None, 'has_visualization': False
            })
        
        # Update profile
        profile = get_student_profile(student_id)
        profile['total_messages'] += 1
        
        # Detect struggle level
        struggle_analysis = detect_student_struggle(message, code)
        struggle_level = struggle_analysis['struggle_level']
        
        if struggle_analysis['is_struggling']:
            topics_struggling = profile.get('topics_struggling', [])
            topics_struggling.append(data.get('current_topic', 'unknown'))
            profile['topics_struggling'] = topics_struggling[-10:]
        
        # Track learning preferences
        message_lower = message.lower()
        if 'graph' in message_lower or 'chart' in message_lower or 'visual' in message_lower:
            learning_patterns[student_id]['prefers_visual'] += 1
        if 'explain' in message_lower or 'what is' in message_lower:
            learning_patterns[student_id]['prefers_text'] += 1
        if 'flowchart' in message_lower:
            learning_patterns[student_id]['needs_flowcharts'] += 1
        if any(w in message_lower for w in ['help', 'stuck', 'confused']):
            learning_patterns[student_id]['needs_frequent_hints'] += 1
        
        add_to_chat_history(student_id, 'user', message, {'is_struggling': struggle_analysis['is_struggling']})
        
        # Detect intents
        wants_graph = any(w in message_lower for w in ['graph', 'chart', 'show', 'visualize', 'plot', 'display'])
        wants_flowchart = any(w in message_lower for w in ['flowchart', 'workflow', 'steps', 'how to'])
        wants_exercise = any(w in message_lower for w in ['exercise', 'practice', 'next', 'another', 'more'])
        wants_summary = any(w in message_lower for w in ['summary', 'recap', 'progress'])
        
        # Get context
        recent_context = get_recent_context(student_id, 5)
        context_str = " | ".join([f"{m['role']}: {m['content'][:40]}" for m in recent_context[-3:]])
        
        graph_data, flowchart_code, ai_response = None, None, None
        
        # SESSION SUMMARY
        if wants_summary:
            session_sum = generate_session_summary(student_id)
            achievements = check_all_achievements(student_id)
            
            ai_response = f"""📊 **Session Summary:** {session_sum}

**Progress:**
- Completed: {profile['completed_exercises']} exercises
- Level: {profile['current_level']}
- Streak: {profile['streak_days']} days

{f"🏆 New: {', '.join(achievements)}" if achievements else "Keep going! 🚀"}"""
            
            add_to_chat_history(student_id, 'assistant', ai_response, {'type': 'summary'})
            return web.json_response({
                'response': ai_response, 'achievements': achievements,
                'graph_data': None, 'flowchart_code': None, 'has_visualization': False
            })
        
        # 🎯 UPGRADED CLAUDE with NEURODIVERGENT-FRIENDLY PROMPT
        if mcp_coordinator:
            try:
                learning_style = analyze_learning_style(student_id)
                is_visual_learner = learning_style == 'visual'
                
                # BUILD NEURODIVERGENT-FRIENDLY PROMPT
                prompt = f"""{NEURODIVERGENT_SYSTEM_PROMPT}

**STUDENT CONTEXT:**
- Level: {profile['current_level']}
- Completed: {profile['completed_exercises']} exercises
- Learning style: {learning_style}
- Struggle level: {struggle_level}/3
- Recent context: {context_str if context_str else "First conversation"}

**CURRENT QUESTION:** "{message}"

{f"**STUDENT'S CODE:**\n```python\n{code}\n```\n" if code else ""}

**YOUR TASK:**
Respond using the neurodivergent-friendly format:
1. Validate their question (1 line)
2. Break down the solution step-by-step with clear explanations
3. Provide complete working code
4. Encourage them to try it
5. Suggest optional experimentation

Remember: TEACH step-by-step, don't just give answers. Use emojis, clear structure, and positive language."""

                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: mcp_coordinator.claude.client.messages.create(
                        model=mcp_coordinator.claude.model,
                        max_tokens=1200,  # Increased for detailed responses
                        messages=[{"role": "user", "content": prompt}]
                    )
                )
                
                ai_response = response.content[0].text.strip()
                
                # 🎯 ADAPT RESPONSE BASED ON STRUGGLE LEVEL
                ai_response = adapt_response_to_struggle(ai_response, struggle_level, is_visual_learner)
                
                print(f"✅ Claude (neurodivergent-friendly): {ai_response[:60]}...")
                
            except Exception as e:
                print(f"⚠️ Claude error: {e}")
                ai_response = None
        
        # INTELLIGENT FALLBACK (with better formatting)
        if not ai_response:
            print("⚠️ Smart fallback")
            
            if any(w in message_lower for w in ['hello', 'hi', 'hey']):
                if profile['total_messages'] > 10:
                    ai_response = f"Welcome back! 👋\n\nYou're at **{profile['current_level']}** level with **{profile['completed_exercises']}** exercises completed. What would you like to work on today?"
                else:
                    ai_response = "Hi! I'm your Python tutor. 👋\n\nI can help you:\n- Learn Python step-by-step\n- Build projects\n- Debug code\n\nWhat would you like to start with?"
            
            elif 'help' in message_lower or 'stuck' in message_lower:
                ai_response = """I'm here to help! 🤗

**Tell me:**
1. What are you trying to do?
2. What's confusing you?
3. Do you have any error messages?

I'll break it down step-by-step for you!"""
            
            elif wants_exercise:
                ai_response = f"Let me generate an exercise for you! 🎯\n\nWhat topic interests you?\n- Loops\n- Functions\n- Data visualization\n- Something else?"
            
            else:
                ai_response = f"I can help with that! Could you be more specific?\n\nFor example:\n- 'Help me understand loops'\n- 'Show me how to create a graph'\n- 'I'm stuck on this code'"
        
        # Generate visualizations
        if wants_graph:
            graph_data = generate_graph_for_topic(message_lower, profile)
        
        if wants_flowchart or struggle_level >= 2:
            flowchart_code = await generate_flowchart_for_concept(message, mcp_coordinator)
        
        # Proactive suggestions
        suggestions = []
        achievements = check_all_achievements(student_id)
        if achievements:
            suggestions.append({'type': 'achievement', 'message': f"🏆 {achievements[0]}!", 'icon': '🏆'})
        
        if len(recent_context) > 20:
            suggestions.append({'type': 'break', 'message': "You've been working hard! Take a 5-min break? ☕", 'icon': '☕'})
        
        if struggle_level >= 2:
            suggestions.append({'type': 'flowchart', 'message': "Try a flowchart to see the steps visually! 📊", 'icon': '📊'})
        
        add_to_chat_history(student_id, 'assistant', ai_response, {
            'has_graph': graph_data is not None,
            'has_flowchart': flowchart_code is not None,
            'struggle_adapted': struggle_level > 0
        })
        
        return web.json_response({
            'response': ai_response,
            'graph_data': graph_data,
            'flowchart_code': flowchart_code,
            'flowchart_title': extract_topic_from_message(message) if flowchart_code else None,
            'has_visualization': (graph_data is not None) or (flowchart_code is not None),
            'proactive_suggestions': suggestions[:3],
            'student_progress': {
                'level': profile['current_level'],
                'completed': profile['completed_exercises'],
                'streak': profile['streak_days']
            },
            'learning_insights': {
                'struggle_detected': struggle_analysis['is_struggling'],
                'struggle_level': struggle_level,
                'learning_style': analyze_learning_style(student_id),
                'suggest_flowchart': struggle_analysis['suggest_flowchart']
            },
            'achievements': achievements if achievements else []
        })
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        traceback.print_exc()
        return web.json_response({
            'response': 'I encountered an error, but I\'m here to help! 🔧\n\nTry asking your question again, or let me know if you need help with something specific.',
            'graph_data': None, 'flowchart_code': None, 'has_visualization': False
        }, status=500)


# ============================================
# EXERCISE CHECKING - Code Review Style
# ============================================

async def handle_check_exercise(request):
    """Check exercise with DETAILED code review feedback"""
    try:
        data = await request.json()
        code = data.get('code', '')
        exercise_id = data.get('exercise_id', '')
        student_id = data.get('student_id', 'default_student')
        
        if not code:
            return web.json_response({
                'is_correct': False,
                'feedback': 'Please write some code first!',
                'hint': 'Start by importing matplotlib: import matplotlib.pyplot as plt',
                'suggestion': 'Try the example code.',
                'output': '',
                'graph_data': None
            })
        
        profile = get_student_profile(student_id)
        progress = exercise_progress[student_id]
        
        # Track attempt
        if exercise_id not in progress['attempted']:
            progress['attempted'].append(exercise_id)
        
        # Use Claude for DETAILED feedback
        if mcp_coordinator:
            prompt = f"""You are an expert code reviewer for Python students.

STUDENT LEVEL: {profile['current_level']}
EXERCISE: {exercise_id}

STUDENT CODE:
```python
{code}
```

Analyze and respond with ONLY valid JSON (no markdown):
{{
    "is_correct": true or false,
    "feedback": "Detailed, specific feedback in 2-4 sentences. Praise what works, explain what doesn't. Be encouraging but honest.",
    "code_quality_score": 0-100,
    "strengths": ["What they did well", "Another strength"],
    "improvements": ["Specific improvement", "Another improvement"],
    "hint": "Actionable next step if incorrect (1 sentence)",
    "suggestion": "Challenge or optimization idea (1 sentence)",
    "output": "Expected output or error message",
    "best_practices": ["Best practice tip 1", "Best practice tip 2"]
}}

Keep language clear and constructive. Be positive and professional."""

            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: mcp_coordinator.claude.client.messages.create(
                        model=mcp_coordinator.claude.model,
                        max_tokens=1000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                )
                
                content = response.content[0].text.strip()
                
                # Clean JSON
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                result = json.loads(content)
                
                # Extract graph from code
                graph_data = extract_graph_from_code(code)
                result['graph_data'] = graph_data
                
                # Update progress if correct
                if result.get('is_correct') and exercise_id not in progress['completed']:
                    progress['completed'].append(exercise_id)
                    profile['completed_exercises'] += 1
                    profile['total_exercises'] += 1
                    
                    # Check achievements
                    check_all_achievements(student_id)
                
                return web.json_response(result)
                
            except Exception as e:
                print(f"⚠️ Claude check error: {e}")
        
        # Fallback: Basic check
        is_correct = 'plt.' in code and any(f in code for f in ['plt.bar', 'plt.plot', 'plt.pie'])
        
        if is_correct and exercise_id not in progress['completed']:
            progress['completed'].append(exercise_id)
            profile['completed_exercises'] += 1
        
        return web.json_response({
            'is_correct': is_correct,
            'feedback': 'Good structure! Your code looks promising.' if is_correct else 'Keep trying! Check matplotlib functions.',
            'code_quality_score': 75 if is_correct else 40,
            'strengths': ['Good start!'] if is_correct else [],
            'improvements': ['Add more details'] if not is_correct else [],
            'hint': 'Use plt.bar(), plt.plot(), or plt.pie()',
            'suggestion': 'Try adding a title with plt.title()',
            'output': 'Code submitted',
            'graph_data': extract_graph_from_code(code) if is_correct else None
        })
        
    except Exception as e:
        print(f"❌ Check error: {e}")
        return web.json_response({
            'is_correct': False,
            'feedback': 'Error checking code',
            'error': str(e),
            'graph_data': None
        }, status=500)


# ============================================
# INTELLIGENT HINTS SYSTEM
# ============================================

async def handle_get_exercise_hint(request):
    """Progressive hints that adapt to student level"""
    try:
        data = await request.json()
        exercise_id = data.get('exercise_id', '')
        hint_level = data.get('hint_level', 1)
        student_id = data.get('student_id', 'default_student')
        
        profile = get_student_profile(student_id)
        progress = exercise_progress[student_id]
        progress['total_hints_used'] += 1
        
        # Progressive hints by level
        hints = {
            'finance-ex1': [
                '💡 Hint 1: Start with importing: import matplotlib.pyplot as plt',
                '💡 Hint 2: Create your data: categories = [...] and amounts = [...]',
                '💡 Hint 3: Use plt.bar(categories, amounts) to create bars',
                '💡 Hint 4: Add labels: plt.xlabel(), plt.ylabel(), plt.title()',
                "💡 Final: Don't forget plt.show() at the end!"
            ],
            'finance-ex2': [
                '💡 Hint 1: You need TWO plt.plot() calls - one for each line',
                '💡 Hint 2: plt.plot(months, income, label="Income", color="green")',
                '💡 Hint 3: plt.plot(months, expenses, label="Expenses", color="red")',
                '💡 Hint 4: Use plt.legend() to show which line is which',
                '💡 Final: Add grid with plt.grid(True) for better readability'
            ],
            'finance-ex3': [
                '💡 Hint 1: Use plt.pie() with your values and labels',
                '💡 Hint 2: Add autopct="%1.1f%%" to show percentages',
                '💡 Hint 3: Calculate interest: total_cost - principal',
                '💡 Hint 4: Use colors parameter for custom colors',
                '💡 Final: Add explode parameter to highlight a slice'
            ],
            'finance-ex4': [
                '💡 Hint 1: Use a for loop to calculate each month',
                '💡 Hint 2: Formula: balance = balance * (1 + rate/12) + deposit',
                '💡 Hint 3: Store balances in a list: balances.append(balance)',
                '💡 Hint 4: Create months list: months = list(range(1, 13))',
                '💡 Final: Plot with plt.plot(months, balances)'
            ]
        }
        
        # Adapt to student level
        if profile['current_level'] == 'absolute_beginner':
            intro = "🌱 Beginner tip: "
        elif profile['current_level'] == 'advanced':
            intro = "🎓 Advanced tip: "
        else:
            intro = "💡 Hint: "
        
        exercise_hints = hints.get(exercise_id, ['Try breaking the problem into smaller steps'])
        hint_index = min(hint_level - 1, len(exercise_hints) - 1)
        
        # Check if using too many hints
        if progress['total_hints_used'] > profile['completed_exercises'] * 3:
            encouragement = " 💪 You're asking good questions - that's how you learn!"
        else:
            encouragement = ""
        
        return web.json_response({
            'hint': intro + exercise_hints[hint_index] + encouragement,
            'hint_level': hint_level,
            'max_hints': len(exercise_hints),
            'total_hints_used': progress['total_hints_used']
        })
        
    except Exception as e:
        print(f"❌ Hint error: {e}")
        return web.json_response({
            'hint': '💡 Try looking at the example code for guidance!',
            'error': str(e)
        }, status=500)


# ============================================
# EXERCISE GENERATION - Progressive Difficulty
# ============================================

async def generate_next_exercise(request):
    """Generate personalized progressive exercise"""
    try:
        data = await request.json()
        student_id = data.get('student_id', 'default_student')
        topic = data.get('topic', 'finance')
        
        profile = get_student_profile(student_id)
        progress = exercise_progress[student_id]
        
        if not mcp_coordinator:
            return web.json_response({'success': False, 'error': 'AI not available'}, status=503)
        
        # Determine difficulty based on progress
        level_config = DIFFICULTY_LEVELS[profile['current_level']]
        
        prompt = f"""Generate a Python programming exercise.

**STUDENT PROFILE:**
- Level: {profile['current_level']}
- Completed: {profile['completed_exercises']} exercises
- Topics mastered: {profile['topics_mastered']}

**REQUIREMENTS:**
- Topic: {topic}
- Difficulty: {profile['current_level']}
- Steps: {level_config['steps']}
- Complexity: {level_config['complexity']}x standard

**TASK:** Create a progressive exercise building on their progress.

Respond with ONLY valid JSON:
{{
    "title": "Exercise title",
    "description": "Clear task description (2-3 sentences max)",
    "difficulty": "{profile['current_level']}",
    "estimated_time": "5-15 minutes",
    "starter_code": "import matplotlib.pyplot as plt\\n\\n# Your code here\\n",
    "hints": ["Progressive hint 1", "Progressive hint 2", "Progressive hint 3"],
    "expected_output": "What code should produce",
    "learning_objectives": ["Objective 1", "Objective 2"],
    "bonus_challenge": "Optional extra challenge for fast learners"
}}

Make it practical and engaging."""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: mcp_coordinator.claude.client.messages.create(
                model=mcp_coordinator.claude.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
        )
        
        content = response.content[0].text.strip()
        
        # Clean JSON
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        exercise = json.loads(content)
        
        return web.json_response({'success': True, 'exercise': exercise})
        
    except Exception as e:
        print(f"❌ Generate error: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)


# ============================================
# HELPER FUNCTIONS
# ============================================

async def create_advanced_graph(request):
    """Create customizable graph"""
    try:
        data = await request.json()
        graph_type = data.get('type', 'bar')
        title = data.get('title', 'Graph')
        colors = data.get('colors', {})
        dimensions = data.get('dimensions', {'width': 800, 'height': 600})
        font_size = data.get('fontSize', 12)
        line_width = data.get('lineWidth', 2)
        
        if 'data' in data:
            x_data, y_data = data['data']['x'], data['data']['y']
        else:
            x_data, y_data = ['Jan', 'Feb', 'Mar', 'Apr', 'May'], [45, 67, 89, 102, 95]
        
        fig, ax = plt.subplots(figsize=(dimensions['width']/100, dimensions['height']/100))
        
        if colors.get('background'):
            fig.patch.set_facecolor(colors['background'])
            ax.set_facecolor(colors['background'])
        
        if graph_type == 'line':
            ax.plot(x_data, y_data, color=colors.get('primary', '#667eea'), linewidth=line_width, marker='o', markersize=8)
        elif graph_type == 'bar':
            ax.bar(x_data, y_data, color=colors.get('primary', '#667eea'))
        elif graph_type == 'scatter':
            ax.scatter(x_data, y_data, color=colors.get('primary', '#667eea'), s=100)
        elif graph_type == 'pie':
            colors_list = [colors.get('primary', '#667eea'), colors.get('secondary', '#764ba2'), colors.get('accent', '#10b981'), '#f59e0b', '#ef4444']
            ax.pie(y_data, labels=x_data, colors=colors_list[:len(y_data)], autopct='%1.1f%%')
        elif graph_type == 'histogram':
            ax.hist(y_data, bins=10, color=colors.get('primary', '#667eea'))
        
        ax.set_title(title, fontsize=font_size+4, fontweight='bold', color=colors.get('text', '#1f2937'))
        
        if graph_type != 'pie':
            ax.set_xlabel(data.get('xlabel', ''), fontsize=font_size, color=colors.get('text', '#1f2937'))
            ax.set_ylabel(data.get('ylabel', ''), fontsize=font_size, color=colors.get('text', '#1f2937'))
            ax.tick_params(colors=colors.get('text', '#1f2937'))
            ax.grid(True, alpha=0.3, color=colors.get('grid', '#d1d5db'))
        
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=100, facecolor=colors.get('background', 'white'))
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return web.json_response({'success': True, 'image': f'data:image/png;base64,{image_base64}', 'type': graph_type})
        
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)}, status=500)


def generate_graph_for_topic(message: str, profile: dict = None) -> dict:
    """Generate contextual graph data"""
    message_lower = message.lower()
    is_advanced = profile and profile['current_level'] in ['intermediate', 'advanced']
    
    if 'expense' in message_lower or 'budget' in message_lower:
        if is_advanced:
            return {'type': 'bar', 'labels': ['Rent', 'Food', 'Transport', 'Utilities', 'Entertainment', 'Savings', 'Misc'],
                    'values': [1200, 400, 150, 100, 200, 300, 150], 'title': 'Monthly Budget (Advanced)'}
        return {'type': 'bar', 'labels': ['Rent', 'Food', 'Transport', 'Utilities', 'Entertainment'],
                'values': [1200, 400, 150, 100, 200], 'title': 'Monthly Budget'}
    
    elif 'income' in message_lower or 'salary' in message_lower:
        return {'type': 'line', 'labels': ['Y1', 'Y3', 'Y5', 'Y7', 'Y10'],
                'values': [28000, 35000, 45000, 58000, 72000], 'title': 'Career Income'}
    
    elif 'saving' in message_lower or 'compound' in message_lower:
        if is_advanced:
            return {'type': 'line', 'labels': ['0Y', '2Y', '5Y', '10Y', '15Y', '20Y', '25Y'],
                    'values': [5000, 10500, 14000, 25000, 39000, 58000, 82000], 'title': 'Compound Interest (Advanced)'}
        return {'type': 'line', 'labels': ['0Y', '5Y', '10Y', '15Y', '20Y'],
                'values': [5000, 14000, 25000, 39000, 58000], 'title': 'Compound Interest'}
    
    elif 'mortgage' in message_lower:
        return {'type': 'pie', 'labels': ['Principal', 'Interest'], 'values': [250000, 125000], 'title': 'Mortgage Cost (£250k/25Y)'}
    
    else:
        return {'type': 'bar', 'labels': ['Q1', 'Q2', 'Q3', 'Q4'], 'values': [12000, 15000, 18000, 21000], 'title': 'Sample Data'}


async def generate_flowchart_for_concept(message: str, mcp_coord) -> str:
    """Generate Mermaid flowchart"""
    if not mcp_coord:
        return None
    
    concept = extract_topic_from_message(message)
    
    try:
        prompt = f"""Generate a Mermaid.js flowchart explaining: {concept}

Create clear, step-by-step flowchart using Mermaid syntax:

flowchart TD
    A[Start] --> B[Step 1]
    B --> C{{Decision?}}
    C -->|Yes| D[Action]
    C -->|No| E[Alternative]
    D --> F[End]
    E --> F

Keep it simple and clear (max 8 nodes).
Return ONLY Mermaid code, no explanations."""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: mcp_coord.claude.client.messages.create(
                model=mcp_coord.claude.model,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
        )
        
        flowchart = response.content[0].text.strip()
        
        if '```mermaid' in flowchart:
            flowchart = flowchart.split('```mermaid')[1].split('```')[0].strip()
        elif '```' in flowchart:
            flowchart = flowchart.split('```')[1].split('```')[0].strip()
        
        return flowchart if 'flowchart' in flowchart else None
        
    except Exception as e:
        print(f"⚠️ Flowchart error: {e}")
        return None


def extract_graph_from_code(code: str) -> dict:
    """Extract graph from student code"""
    try:
        labels_match = re.search(r'(\w+)\s*=\s*\[(.*?)\]', code)
        values_match = re.findall(r'\[([0-9,\s]+)\]', code)
        
        if not labels_match or not values_match:
            return None
        
        labels_str = labels_match.group(2)
        labels = [l.strip().strip("'\"") for l in labels_str.split(',')]
        
        for val_str in values_match:
            try:
                values = [float(v.strip()) for v in val_str.split(',')]
                if len(values) == len(labels):
                    chart_type = 'bar'
                    if 'plt.plot' in code:
                        chart_type = 'line'
                    elif 'plt.pie' in code:
                        chart_type = 'pie'
                    elif 'plt.scatter' in code:
                        chart_type = 'scatter'
                    
                    return {'type': chart_type, 'labels': labels, 'values': values, 'title': 'Your Result'}
            except:
                continue
        
        return None
    except Exception as e:
        print(f"⚠️ Graph extraction: {e}")
        return None


def extract_topic_from_message(message: str) -> str:
    """Extract main topic"""
    message_lower = message.lower()
    
    topics = {
        'loop': 'Python Loops', 'function': 'Python Functions', 'list': 'Python Lists',
        'dict': 'Python Dictionaries', 'class': 'Python Classes', 'file': 'File Handling',
        'matplotlib': 'Data Visualization', 'budget': 'Budget Management',
        'mortgage': 'Mortgage Calculations', 'compound': 'Compound Interest'
    }
    
    for keyword, topic in topics.items():
        if keyword in message_lower:
            return topic
    
    return 'Python Programming'


def get_proactive_suggestion(struggle_reason: str) -> str:
    """Get proactive suggestion"""
    suggestions = {
        'struggle_keyword': "💡 Would you like:\n• Flowchart?\n• Simpler example?\n• Step-by-step guide?",
        'multiple_questions': "🎯 I see several questions! Let me:\n• Create step-by-step guide\n• Show visual diagrams\n• What helps most?",
        'repeating_messages': "🔄 Let me try differently:\n• Workflow diagram?\n• Concrete example?\n• Which would help?"
    }
    
    return suggestions.get(struggle_reason, "💡 Need help? I can show flowcharts, graphs, or explain step-by-step!")


async def handle_run_exercise_code(request):
    """Run code safely"""
    try:
        data = await request.json()
        code = data.get('code', '')
        exercise_id = data.get('exercise_id', '')
        
        if not code:
            return web.json_response({'success': False, 'error': 'No code provided'}, status=400)
        
        tutor = request.app.get('tutor')
        if not tutor:
            return web.json_response({'success': False, 'error': 'Code execution unavailable'}, status=503)
        
        result = await tutor.tool_execute_python_debug({
            'code': code, 'user_message': f'Exercise: {exercise_id}', 'student_id': 'exercise_user'
        })
        
        return web.json_response({'success': True, 'output': result})
        
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def ai_explain_code(request):
    """AI explains code"""
    try:
        data = await request.json()
        code = data.get('code', '')
        student_id = data.get('student_id', 'default_student')
        
        if not code:
            return web.json_response({'explanation': 'Please provide code!'})
        
        profile = get_student_profile(student_id)
        
        if mcp_coordinator:
            depth = {
                'beginner': 'Explain in simple terms with analogies',
                'intermediate': 'Explain with technical details clearly',
                'advanced': 'Provide detailed technical explanation with best practices'
            }.get(profile['current_level'], 'Explain clearly')
            
            prompt = f"""Explain this Python code to a {profile['current_level']} student.

CODE:
```python
{code}
```

{depth}

Provide:
1. What the code does (1-2 sentences)
2. How it works step-by-step
3. Example output
4. One tip for improvement

Keep language clear and accessible."""
            
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: mcp_coordinator.claude.client.messages.create(
                        model=mcp_coordinator.claude.model,
                        max_tokens=800,
                        messages=[{"role": "user", "content": prompt}]
                    )
                )
                
                explanation = response.content[0].text.strip()
                return web.json_response({'success': True, 'explanation': explanation, 'student_level': profile['current_level']})
            except Exception as e:
                return web.json_response({'success': False, 'explanation': 'AI unavailable. Try running the code!'})
        
        return web.json_response({'success': False, 'explanation': 'AI service not available'})
        
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def ai_generate_exercises(request):
    """AI generates exercises"""
    try:
        data = await request.json()
        topic = data.get('topic', 'Python basics')
        level = data.get('level', 'beginner')
        count = data.get('count', 3)
        
        if mcp_coordinator:
            try:
                result = await mcp_coordinator.openai.generate_exercises(
                    topic=topic, level=level,
                    theory_content=f"Generate exercises for {topic}", count=count
                )
                
                if result.get('success'):
                    return web.json_response({'success': True, 'exercises': result.get('exercises', [])})
            except Exception as e:
                print(f"⚠️ Exercise gen error: {e}")
        
        fallback = [{'title': f'{topic} Practice', 'description': 'Try this exercise', 
                     'difficulty': 'easy', 'starter_code': '# Your code here\n',
                     'hints': ['Break into steps', 'Test as you go']}]
        
        return web.json_response({'success': True, 'exercises': fallback, 'fallback': True})
        
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def generate_flowchart_for_code(request):
    """POST /api/generate-flowchart - Generate Mermaid flowchart for code"""
    try:
        data = await request.json()
        code = data.get('code', '')
        topic = data.get('topic', 'code workflow')
        message = data.get('message', '')
        
        print(f"📊 Flowchart request: {topic}")
        
        if not code and not topic:
            return web.json_response({
                'success': False,
                'error': 'Please provide code or topic'
            }, status=400)
        
        struggle_info = detect_student_struggle(message, code)
        
        if not mcp_coordinator:
            return web.json_response({
                'success': False,
                'error': 'MCP not available',
                'struggle_detected': struggle_info['is_struggling']
            }, status=503)
        
        try:
            concept = f"Step-by-step: {code[:100]}" if code else topic
            
            flowchart_result = await mcp_coordinator.gemini.generate_flowcharts(
                topic=topic, concept=concept, count=1
            )
            
            if flowchart_result.get('success') and flowchart_result.get('flowcharts'):
                flowchart = flowchart_result['flowcharts'][0]
                
                return web.json_response({
                    'success': True,
                    'flowchart': {
                        'title': flowchart.get('title', 'Code Workflow'),
                        'description': flowchart.get('description', 'Step-by-step breakdown'),
                        'mermaid_code': flowchart.get('mermaid_code', ''),
                        'explanation': flowchart.get('explanation', '')
                    },
                    'struggle_detected': struggle_info['is_struggling'],
                    'struggle_level': struggle_info['struggle_level'],
                    'message': '📊 Flowchart to help you!'
                })
            else:
                return web.json_response({
                    'success': True,
                    'flowchart': {
                        'title': 'Code Workflow',
                        'description': 'Basic flow',
                        'mermaid_code': 'graph LR\n  A[Start]-->B[Process]\n  B-->C[Result]\n  C-->D[End]',
                        'explanation': 'Basic flow of your code'
                    },
                    'fallback': True,
                    'message': '📊 Basic flowchart!'
                })
                
        except Exception as e:
            print(f"⚠️ Flowchart error: {e}")
            return web.json_response({
                'success': False,
                'error': f'Could not generate: {str(e)}',
                'struggle_detected': struggle_info['is_struggling']
            }, status=500)
            
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def get_next_exercise_ai(request):
    """POST /api/next-exercise-ai - Personalized exercise with state adaptation"""
    try:
        data = await request.json()
        student_id = data.get('student_id', 'default_student')
        completed_topics = data.get('completed_topics', [])
        current_topic = data.get('current_topic', 'python_basics')
        difficulty = data.get('difficulty', 'beginner')
        
        print(f"🎯 AI exercise for: {student_id}")
        
        if not mcp_coordinator:
            return web.json_response({'success': False, 'error': 'MCP not available'}, status=503)
        
        # Get emotion state if tutor available
        tutor = request.app.get('tutor')
        attention_level = 0.7
        cognitive_load = 0.5
        
        if tutor and hasattr(tutor, 'emotion_analyzer'):
            try:
                emotion_state = tutor.emotion_analyzer.analyze_comprehensive_state(
                    message="New exercise",
                    user_id=student_id,
                    context={'completed_topics': completed_topics}
                )
                attention_level = emotion_state.get('attention_level', 0.7)
                cognitive_load = emotion_state.get('cognitive_load', 0.5)
            except Exception as e:
                print(f"⚠️ Emotion warning: {e}")
        
        # Adapt difficulty to cognitive state
        if cognitive_load > 0.7:
            difficulty = 'easier'
            time_estimate = '5-8 min'
        elif attention_level < 0.4:
            difficulty = 'short_focused'
            time_estimate = '3-5 min'
        else:
            time_estimate = '10-15 min'
        
        try:
            exercise_result = await mcp_coordinator.openai.generate_exercises(
                topic=current_topic,
                level=difficulty,
                theory_content=f"Completed: {', '.join(completed_topics[-3:])}",
                count=1
            )
            
            if exercise_result.get('success') and exercise_result.get('exercises'):
                exercise = exercise_result['exercises'][0]
                
                return web.json_response({
                    'success': True,
                    'exercise': exercise,
                    'adapted_to_state': True,
                    'student_state': {
                        'attention_level': attention_level,
                        'cognitive_load': cognitive_load,
                        'difficulty_adjusted': difficulty,
                        'estimated_time': time_estimate
                    },
                    'personalized': True,
                    'message': f'🎯 Personalized exercise (est. {time_estimate})'
                })
            else:
                fallback = {
                    'exercise_number': 1,
                    'title': f'{current_topic.replace("_", " ").title()} Practice',
                    'description': f'Practice {current_topic}',
                    'difficulty': difficulty,
                    'starter_code': f'# Practice {current_topic}\n# Your code here\n',
                    'expected_output': 'Complete the task',
                    'hints': ['Break into steps', 'Test as you go', 'Ask if stuck!']
                }
                
                return web.json_response({
                    'success': True,
                    'exercise': fallback,
                    'fallback': True,
                    'adapted_to_state': True,
                    'message': '🎯 Practice exercise!'
                })
                
        except Exception as e:
            print(f"⚠️ Exercise gen error: {e}")
            return web.json_response({'success': False, 'error': f'Could not generate: {str(e)}'}, status=500)
            
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)}, status=500)


# ============================================
# ROUTES SETUP
# ============================================

def setup_advanced_routes(app):
    """Setup all routes - ULTIMATE VERSION v3.0"""
    
    asyncio.create_task(init_mcp_for_exercises())
    
    # Core
    app.router.add_get('/api/mcp/status', mcp_status)
    app.router.add_post('/api/create_advanced_graph', create_advanced_graph)
    app.router.add_post('/api/ai/explain_code', ai_explain_code)
    app.router.add_post('/api/ai/generate_exercises', ai_generate_exercises)
    
    # Exercise system - UPGRADED
    app.router.add_post('/api/check-exercise', handle_check_exercise)
    app.router.add_post('/api/get-hint', handle_get_exercise_hint)
    app.router.add_post('/api/run-exercise', handle_run_exercise_code)
    
    # Chat - ULTIMATE v3.0 (NEURODIVERGENT-FRIENDLY)
    app.router.add_post('/api/chat', ai_chat)
    
    # Exercise generation
    app.router.add_post('/api/generate-next-exercise', generate_next_exercise)
    app.router.add_post('/api/next-exercise-ai', get_next_exercise_ai)
    
    # Flowchart generation
    app.router.add_post('/api/generate-flowchart', generate_flowchart_for_code)
    
    print("✅ ULTIMATE VERSION v3.0 - NEURODIVERGENT-FRIENDLY AI ACTIVATED!")
    print("   🧠 AI with Memory: ACTIVE")
    print("   💬 Neurodivergent-Friendly Chat: ACTIVE ⭐NEW⭐")
    print("   🎓 Step-by-Step Teaching: ACTIVE ⭐NEW⭐")
    print("   🏆 Achievements: ACTIVE")
    print("   📊 Visualizations: ACTIVE")
    print("   🎯 Progressive Exercises: ACTIVE")
    print("   💎 Code Review Feedback: ACTIVE")
    print("   🔄 Flowchart Generation: ACTIVE")
    print("   🎯 State-Adaptive Exercises: ACTIVE")
    print("   🤗 Struggle Detection & Adaptation: ACTIVE ⭐NEW⭐")
