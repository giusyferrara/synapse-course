# ai_response_template.py
# ============================================
# NEURODIVERGENT-FRIENDLY AI RESPONSE SYSTEM
# ============================================

"""
This module defines the system prompt and response structure for the AI assistant
to ensure all responses are clear, educational, and neurodivergent-friendly.
"""

# ============================================
# CORE SYSTEM PROMPT
# ============================================

NEURODIVERGENT_SYSTEM_PROMPT = """
You are an AI learning assistant for Synapse, a platform designed specifically for neurodivergent learners (ADHD, autism, dyslexia).

🎯 YOUR MISSION: TEACH, don't just give answers.

CRITICAL RULES FOR NEURODIVERGENT LEARNERS:

1. **ALWAYS BREAK IT DOWN STEP-BY-STEP**
   - Never dump code without explanation
   - Number your steps clearly: Step 1, Step 2, etc.
   - Explain WHAT each line does AND WHY it matters

2. **USE CLEAR VISUAL STRUCTURE**
   - Use emojis for visual anchors (🎯 📊 ✨ 💡)
   - Short paragraphs (2-3 sentences max)
   - Blank lines between sections
   - Code blocks with comments inside

3. **EXPLAIN THE "WHY" NOT JUST THE "HOW"**
   - "This tells Python to..." explanations
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

6. **NEVER:**
   - Give code dumps without explanation
   - Use jargon without explaining it
   - Write long paragraphs
   - Be cold or robotic

RESPONSE STRUCTURE FOR CODE HELP:

1. Opening (1 line) - Validate their question
2. Step-by-step breakdown - Each step clearly numbered with explanation
3. Complete solution - "Here's your full code:"
4. Encouragement - "Try it!" or "Great work!"
5. Optional enhancement - "Want to make it better? Try..."

EXAMPLE GOOD RESPONSE:
"Great question! Let's build this bar chart together. 🎯

**Step 1: Draw the bars**
```python
plt.bar(categories, amounts)
```
This tells Python: 'Take my category names and draw bars with the heights from amounts.'

**Step 2: Add labels**
```python
plt.title('My Budget')
plt.xlabel('Categories')
```
Labels help people understand what they're looking at!

✨ **Your complete code:**
[full code block]

🎨 **Want to experiment?** Try changing the color: `color='skyblue'`"

EXAMPLE BAD RESPONSE:
"Add these lines:
```python
plt.bar(categories, amounts)
plt.title('Monthly Budget')
plt.xlabel('Categories')
plt.ylabel('Amount ($)')
plt.show()
```
This creates the bar chart and displays it!"

Remember: You're not just solving their problem - you're teaching them HOW to solve problems.
"""

# ============================================
# RESPONSE FORMATTERS
# ============================================

def format_code_explanation_response(
    user_question: str,
    solution_steps: list,
    complete_code: str,
    enhancement_suggestion: str = None,
    difficulty_level: str = "beginner"
) -> str:
    """
    Format a code explanation response following neurodivergent-friendly principles.
    
    Args:
        user_question: What the student asked
        solution_steps: List of dicts with {'step_num': int, 'code': str, 'explanation': str}
        complete_code: The full working solution
        enhancement_suggestion: Optional extra challenge
        difficulty_level: Student's current level
    
    Returns:
        Formatted response string
    """
    
    # Opening validation
    openings = [
        "Great question! Let's tackle this together. 🎯",
        "I can help with that! Let's break it down step by step. 💡",
        "Perfect timing to learn this! Here's how it works. ✨",
        "Excellent question! Let me show you how to build this. 🚀"
    ]
    
    import random
    response = random.choice(openings) + "\n\n"
    
    # Step-by-step breakdown
    for step in solution_steps:
        response += f"**Step {step['step_num']}: {step.get('title', 'Next step')}**\n"
        response += f"```python\n{step['code']}\n```\n"
        response += f"{step['explanation']}\n\n"
    
    # Complete solution
    response += "✨ **Your complete code:**\n"
    response += f"```python\n{complete_code}\n```\n\n"
    
    # Encouragement
    encouragements = [
        "🎉 Try running this now!",
        "✅ Give it a try and see what happens!",
        "🚀 Run this code and watch it work!",
        "💪 You've got this - run the code!"
    ]
    response += random.choice(encouragements) + "\n\n"
    
    # Optional enhancement
    if enhancement_suggestion:
        response += f"🎨 **Want to level up?** {enhancement_suggestion}\n"
    
    return response


def format_concept_explanation_response(
    concept: str,
    explanation: str,
    example_code: str = None,
    analogy: str = None
) -> str:
    """
    Format a concept explanation following neurodivergent-friendly principles.
    """
    
    response = f"Let me explain **{concept}** in a clear way! 💡\n\n"
    
    # Main explanation in short paragraphs
    paragraphs = explanation.split('\n\n')
    for para in paragraphs:
        if len(para) > 200:  # Break long paragraphs
            sentences = para.split('. ')
            for i in range(0, len(sentences), 2):
                response += '. '.join(sentences[i:i+2]) + '.\n\n'
        else:
            response += para + '\n\n'
    
    # Analogy if provided
    if analogy:
        response += f"🎯 **Think of it like this:** {analogy}\n\n"
    
    # Example code
    if example_code:
        response += "📝 **Here's an example:**\n"
        response += f"```python\n{example_code}\n```\n\n"
    
    response += "✨ Does this make sense? Feel free to ask follow-up questions!"
    
    return response


def format_error_help_response(
    error_message: str,
    explanation: str,
    fix_steps: list,
    corrected_code: str
) -> str:
    """
    Format an error help response.
    """
    
    response = "I see what's happening! Let's fix this error. 🔧\n\n"
    
    response += f"**The Error:**\n`{error_message}`\n\n"
    response += f"**What it means:** {explanation}\n\n"
    
    response += "**How to fix it:**\n"
    for i, step in enumerate(fix_steps, 1):
        response += f"{i}. {step}\n"
    response += "\n"
    
    response += "✨ **Your corrected code:**\n"
    response += f"```python\n{corrected_code}\n```\n\n"
    
    response += "🎉 This should work now! Give it a try.\n"
    
    return response


# ============================================
# STRUGGLE DETECTION -> RESPONSE ADAPTATION
# ============================================

def adapt_response_to_struggle_level(
    base_response: str,
    struggle_level: int,
    is_visual_learner: bool = False
) -> str:
    """
    Adapt response based on detected struggle level.
    
    Args:
        base_response: The initial formatted response
        struggle_level: 0-3 (0=no struggle, 3=high struggle)
        is_visual_learner: Whether to add more visual elements
    
    Returns:
        Adapted response
    """
    
    if struggle_level == 0:
        return base_response
    
    # Add supportive prefix for struggling students
    if struggle_level >= 2:
        prefix = "I can see you're working hard on this! Let's take it one small step at a time. 🤗\n\n"
        base_response = prefix + base_response
    
    # Add flowchart suggestion for high struggle
    if struggle_level >= 3:
        suffix = "\n\n💡 **Feeling stuck?** Try clicking the flowchart button - seeing the steps visually might help!"
        base_response += suffix
    
    # Add more visual elements for visual learners
    if is_visual_learner:
        base_response = base_response.replace("Step 1:", "1️⃣ Step 1:")
        base_response = base_response.replace("Step 2:", "2️⃣ Step 2:")
        base_response = base_response.replace("Step 3:", "3️⃣ Step 3:")
        base_response = base_response.replace("Step 4:", "4️⃣ Step 4:")
    
    return base_response


# ============================================
# INTEGRATION EXAMPLE
# ============================================

def generate_ai_response(
    user_message: str,
    context: dict,
    student_profile: dict,
    struggle_detected: bool = False
) -> str:
    """
    Main function to generate AI response with all formatting rules applied.
    
    This would be called from your ai_chat handler in advanced_handlers.py
    """
    
    # Parse user intent
    is_code_help = any(word in user_message.lower() for word in ['help', 'how do i', 'can you', 'stuck'])
    is_error = any(word in user_message.lower() for word in ['error', 'not working', "doesn't work"])
    
    # Get student learning preferences
    is_visual = student_profile.get('preferred_learning_style') == 'visual'
    struggle_level = 2 if struggle_detected else 0
    
    # Generate appropriate response type
    if is_code_help:
        # This would call your MCP coordinator to get solution
        # Then format it properly
        response = format_code_explanation_response(
            user_question=user_message,
            solution_steps=[
                {
                    'step_num': 1,
                    'title': 'Draw the bars',
                    'code': 'plt.bar(categories, amounts)',
                    'explanation': "This tells Python: 'Look at my categories and draw bars with heights from amounts.'"
                },
                # ... more steps
            ],
            complete_code="# Full solution here",
            enhancement_suggestion="Try adding colors: plt.bar(categories, amounts, color='skyblue')"
        )
    elif is_error:
        response = format_error_help_response(
            error_message="Error message here",
            explanation="What the error means",
            fix_steps=["Step 1", "Step 2"],
            corrected_code="# Fixed code"
        )
    else:
        response = format_concept_explanation_response(
            concept="Topic",
            explanation="Explanation",
            example_code="# Example"
        )
    
    # Adapt to struggle level
    response = adapt_response_to_struggle_level(
        response, 
        struggle_level=struggle_level,
        is_visual_learner=is_visual
    )
    
    return response


# ============================================
# PROMPT TEMPLATES FOR MCP COORDINATOR
# ============================================

MCP_CLAUDE_PROMPT_TEMPLATE = """
{system_prompt}

CONTEXT:
- Student level: {level}
- Topics completed: {completed_topics}
- Current struggle indicators: {struggle_indicators}
- Learning style: {learning_style}

STUDENT QUESTION:
{user_message}

RESPOND FOLLOWING THE NEURODIVERGENT-FRIENDLY FORMAT:
1. Validate question
2. Break down step-by-step with explanations
3. Provide complete solution
4. Encourage and suggest next steps

Remember: TEACH, don't just give answers!
"""

def build_mcp_prompt(user_message: str, student_profile: dict, context: dict) -> str:
    """Build the complete prompt to send to MCP Claude."""
    
    return MCP_CLAUDE_PROMPT_TEMPLATE.format(
        system_prompt=NEURODIVERGENT_SYSTEM_PROMPT,
        level=student_profile.get('current_level', 'beginner'),
        completed_topics=', '.join(context.get('completed_topics', [])),
        struggle_indicators=context.get('struggle_indicators', 'None detected'),
        learning_style=student_profile.get('preferred_learning_style', 'mixed'),
        user_message=user_message
    )# ai_response_template.py
# ============================================
# NEURODIVERGENT-FRIENDLY AI RESPONSE SYSTEM
# ============================================

"""
This module defines the system prompt and response structure for the AI assistant
to ensure all responses are clear, educational, and neurodivergent-friendly.
"""

# ============================================
# CORE SYSTEM PROMPT
# ============================================

NEURODIVERGENT_SYSTEM_PROMPT = """
You are an AI learning assistant for Synapse, a platform designed specifically for neurodivergent learners (ADHD, autism, dyslexia).

🎯 YOUR MISSION: TEACH, don't just give answers.

CRITICAL RULES FOR NEURODIVERGENT LEARNERS:

1. **ALWAYS BREAK IT DOWN STEP-BY-STEP**
   - Never dump code without explanation
   - Number your steps clearly: Step 1, Step 2, etc.
   - Explain WHAT each line does AND WHY it matters

2. **USE CLEAR VISUAL STRUCTURE**
   - Use emojis for visual anchors (🎯 📊 ✨ 💡)
   - Short paragraphs (2-3 sentences max)
   - Blank lines between sections
   - Code blocks with comments inside

3. **EXPLAIN THE "WHY" NOT JUST THE "HOW"**
   - "This tells Python to..." explanations
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

6. **NEVER:**
   - Give code dumps without explanation
   - Use jargon without explaining it
   - Write long paragraphs
   - Be cold or robotic

RESPONSE STRUCTURE FOR CODE HELP:

1. Opening (1 line) - Validate their question
2. Step-by-step breakdown - Each step clearly numbered with explanation
3. Complete solution - "Here's your full code:"
4. Encouragement - "Try it!" or "Great work!"
5. Optional enhancement - "Want to make it better? Try..."

EXAMPLE GOOD RESPONSE:
"Great question! Let's build this bar chart together. 🎯

**Step 1: Draw the bars**
```python
plt.bar(categories, amounts)
```
This tells Python: 'Take my category names and draw bars with the heights from amounts.'

**Step 2: Add labels**
```python
plt.title('My Budget')
plt.xlabel('Categories')
```
Labels help people understand what they're looking at!

✨ **Your complete code:**
[full code block]

🎨 **Want to experiment?** Try changing the color: `color='skyblue'`"

EXAMPLE BAD RESPONSE:
"Add these lines:
```python
plt.bar(categories, amounts)
plt.title('Monthly Budget')
plt.xlabel('Categories')
plt.ylabel('Amount ($)')
plt.show()
```
This creates the bar chart and displays it!"

Remember: You're not just solving their problem - you're teaching them HOW to solve problems.
"""

# ============================================
# RESPONSE FORMATTERS
# ============================================

def format_code_explanation_response(
    user_question: str,
    solution_steps: list,
    complete_code: str,
    enhancement_suggestion: str = None,
    difficulty_level: str = "beginner"
) -> str:
    """
    Format a code explanation response following neurodivergent-friendly principles.
    
    Args:
        user_question: What the student asked
        solution_steps: List of dicts with {'step_num': int, 'code': str, 'explanation': str}
        complete_code: The full working solution
        enhancement_suggestion: Optional extra challenge
        difficulty_level: Student's current level
    
    Returns:
        Formatted response string
    """
    
    # Opening validation
    openings = [
        "Great question! Let's tackle this together. 🎯",
        "I can help with that! Let's break it down step by step. 💡",
        "Perfect timing to learn this! Here's how it works. ✨",
        "Excellent question! Let me show you how to build this. 🚀"
    ]
    
    import random
    response = random.choice(openings) + "\n\n"
    
    # Step-by-step breakdown
    for step in solution_steps:
        response += f"**Step {step['step_num']}: {step.get('title', 'Next step')}**\n"
        response += f"```python\n{step['code']}\n```\n"
        response += f"{step['explanation']}\n\n"
    
    # Complete solution
    response += "✨ **Your complete code:**\n"
    response += f"```python\n{complete_code}\n```\n\n"
    
    # Encouragement
    encouragements = [
        "🎉 Try running this now!",
        "✅ Give it a try and see what happens!",
        "🚀 Run this code and watch it work!",
        "💪 You've got this - run the code!"
    ]
    response += random.choice(encouragements) + "\n\n"
    
    # Optional enhancement
    if enhancement_suggestion:
        response += f"🎨 **Want to level up?** {enhancement_suggestion}\n"
    
    return response


def format_concept_explanation_response(
    concept: str,
    explanation: str,
    example_code: str = None,
    analogy: str = None
) -> str:
    """
    Format a concept explanation following neurodivergent-friendly principles.
    """
    
    response = f"Let me explain **{concept}** in a clear way! 💡\n\n"
    
    # Main explanation in short paragraphs
    paragraphs = explanation.split('\n\n')
    for para in paragraphs:
        if len(para) > 200:  # Break long paragraphs
            sentences = para.split('. ')
            for i in range(0, len(sentences), 2):
                response += '. '.join(sentences[i:i+2]) + '.\n\n'
        else:
            response += para + '\n\n'
    
    # Analogy if provided
    if analogy:
        response += f"🎯 **Think of it like this:** {analogy}\n\n"
    
    # Example code
    if example_code:
        response += "📝 **Here's an example:**\n"
        response += f"```python\n{example_code}\n```\n\n"
    
    response += "✨ Does this make sense? Feel free to ask follow-up questions!"
    
    return response


def format_error_help_response(
    error_message: str,
    explanation: str,
    fix_steps: list,
    corrected_code: str
) -> str:
    """
    Format an error help response.
    """
    
    response = "I see what's happening! Let's fix this error. 🔧\n\n"
    
    response += f"**The Error:**\n`{error_message}`\n\n"
    response += f"**What it means:** {explanation}\n\n"
    
    response += "**How to fix it:**\n"
    for i, step in enumerate(fix_steps, 1):
        response += f"{i}. {step}\n"
    response += "\n"
    
    response += "✨ **Your corrected code:**\n"
    response += f"```python\n{corrected_code}\n```\n\n"
    
    response += "🎉 This should work now! Give it a try.\n"
    
    return response


# ============================================
# STRUGGLE DETECTION -> RESPONSE ADAPTATION
# ============================================

def adapt_response_to_struggle_level(
    base_response: str,
    struggle_level: int,
    is_visual_learner: bool = False
) -> str:
    """
    Adapt response based on detected struggle level.
    
    Args:
        base_response: The initial formatted response
        struggle_level: 0-3 (0=no struggle, 3=high struggle)
        is_visual_learner: Whether to add more visual elements
    
    Returns:
        Adapted response
    """
    
    if struggle_level == 0:
        return base_response
    
    # Add supportive prefix for struggling students
    if struggle_level >= 2:
        prefix = "I can see you're working hard on this! Let's take it one small step at a time. 🤗\n\n"
        base_response = prefix + base_response
    
    # Add flowchart suggestion for high struggle
    if struggle_level >= 3:
        suffix = "\n\n💡 **Feeling stuck?** Try clicking the flowchart button - seeing the steps visually might help!"
        base_response += suffix
    
    # Add more visual elements for visual learners
    if is_visual_learner:
        base_response = base_response.replace("Step 1:", "1️⃣ Step 1:")
        base_response = base_response.replace("Step 2:", "2️⃣ Step 2:")
        base_response = base_response.replace("Step 3:", "3️⃣ Step 3:")
        base_response = base_response.replace("Step 4:", "4️⃣ Step 4:")
    
    return base_response


# ============================================
# INTEGRATION EXAMPLE
# ============================================

def generate_ai_response(
    user_message: str,
    context: dict,
    student_profile: dict,
    struggle_detected: bool = False
) -> str:
    """
    Main function to generate AI response with all formatting rules applied.
    
    This would be called from your ai_chat handler in advanced_handlers.py
    """
    
    # Parse user intent
    is_code_help = any(word in user_message.lower() for word in ['help', 'how do i', 'can you', 'stuck'])
    is_error = any(word in user_message.lower() for word in ['error', 'not working', "doesn't work"])
    
    # Get student learning preferences
    is_visual = student_profile.get('preferred_learning_style') == 'visual'
    struggle_level = 2 if struggle_detected else 0
    
    # Generate appropriate response type
    if is_code_help:
        # This would call your MCP coordinator to get solution
        # Then format it properly
        response = format_code_explanation_response(
            user_question=user_message,
            solution_steps=[
                {
                    'step_num': 1,
                    'title': 'Draw the bars',
                    'code': 'plt.bar(categories, amounts)',
                    'explanation': "This tells Python: 'Look at my categories and draw bars with heights from amounts.'"
                },
                # ... more steps
            ],
            complete_code="# Full solution here",
            enhancement_suggestion="Try adding colors: plt.bar(categories, amounts, color='skyblue')"
        )
    elif is_error:
        response = format_error_help_response(
            error_message="Error message here",
            explanation="What the error means",
            fix_steps=["Step 1", "Step 2"],
            corrected_code="# Fixed code"
        )
    else:
        response = format_concept_explanation_response(
            concept="Topic",
            explanation="Explanation",
            example_code="# Example"
        )
    
    # Adapt to struggle level
    response = adapt_response_to_struggle_level(
        response, 
        struggle_level=struggle_level,
        is_visual_learner=is_visual
    )
    
    return response


# ============================================
# PROMPT TEMPLATES FOR MCP COORDINATOR
# ============================================

MCP_CLAUDE_PROMPT_TEMPLATE = """
{system_prompt}

CONTEXT:
- Student level: {level}
- Topics completed: {completed_topics}
- Current struggle indicators: {struggle_indicators}
- Learning style: {learning_style}

STUDENT QUESTION:
{user_message}

RESPOND FOLLOWING THE NEURODIVERGENT-FRIENDLY FORMAT:
1. Validate question
2. Break down step-by-step with explanations
3. Provide complete solution
4. Encourage and suggest next steps

Remember: TEACH, don't just give answers!
"""

def build_mcp_prompt(user_message: str, student_profile: dict, context: dict) -> str:
    """Build the complete prompt to send to MCP Claude."""
    
    return MCP_CLAUDE_PROMPT_TEMPLATE.format(
        system_prompt=NEURODIVERGENT_SYSTEM_PROMPT,
        level=student_profile.get('current_level', 'beginner'),
        completed_topics=', '.join(context.get('completed_topics', [])),
        struggle_indicators=context.get('struggle_indicators', 'None detected'),
        learning_style=student_profile.get('preferred_learning_style', 'mixed'),
        user_message=user_message
    )
