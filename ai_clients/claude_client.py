import anthropic
import asyncio
from typing import Dict, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import json
import re

class ClaudeClient:
    """Claude AI client for generating educational theory content"""
    
    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.CLAUDE_MODEL
        print(f"✅ Claude client initialized ({self.model})")
    
    def _clean_json_response(self, text: str) -> str:
        """Remove markdown JSON formatting"""
        # Remove ```json and ``` wrappers
        text = re.sub(r'^```json\s*', '', text.strip())
        text = re.sub(r'\s*```$', '', text.strip())
        text = re.sub(r'^```\s*', '', text.strip())
        return text.strip()
    
    async def generate_theory(
        self,
        topic: str,
        level: str = "beginner",
        student_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate educational theory content"""
        
        profile_instructions = ""
        if student_profile:
            profile_type = student_profile.get("type", "neurotypical")
            
            if profile_type == "autism":
                profile_instructions = """
Use concrete, literal language. Avoid metaphors unless explained explicitly.
Structure content sequentially with clear steps.
Use high-contrast examples with distinct categories.
"""
            elif profile_type == "dyslexia":
                profile_instructions = """
Use short sentences and paragraphs.
Emphasize visual representations over long text.
Include phonetic breakdown of technical terms.
"""
            elif profile_type == "adhd":
                profile_instructions = """
Keep explanations brief and focused.
Use frequent examples to maintain engagement.
Break content into small, digestible chunks.
"""
        
        prompt = f"""You are an expert Python educator creating content for {level} level students.

Topic: {topic.upper()}

{profile_instructions}

Create educational theory content with:

1. INTRODUCTION (2-3 sentences)
   - What is this concept?
   - Why is it important?

2. CORE EXPLANATION (3-4 paragraphs)
   - Clear, simple explanation
   - Real-world analogy
   - How it works step-by-step

3. KEY POINTS (5 bullet points)
   - Most important facts to remember

4. COMMON MISCONCEPTIONS (2-3 points)
   - What students often misunderstand
   - Correct understanding

5. PRACTICAL APPLICATIONS (2-3 examples)
   - Where is this used in real code?

CRITICAL: Return ONLY valid JSON, no markdown formatting, no code blocks.

Format:
{{
  "introduction": "Clear 2-3 sentence introduction here",
  "explanation": "Detailed explanation in 3-4 paragraphs here",
  "key_points": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"],
  "misconceptions": ["Misconception 1", "Misconception 2"],
  "applications": ["Application 1", "Application 2", "Application 3"]
}}

Return the JSON directly with no ```json wrapper."""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            
            content = response.content[0].text
            
            # Clean markdown formatting
            content = self._clean_json_response(content)
            
            try:
                theory_data = json.loads(content)
                
                # Validate structure
                if not isinstance(theory_data, dict):
                    raise ValueError("Response is not a dict")
                
                # Ensure all required fields exist with defaults
                theory_data.setdefault("introduction", "")
                theory_data.setdefault("explanation", "")
                theory_data.setdefault("key_points", [])
                theory_data.setdefault("misconceptions", [])
                theory_data.setdefault("applications", [])
                
                return {
                    "success": True,
                    "content": theory_data,
                    "model": self.model,
                    "tokens": response.usage.input_tokens + response.usage.output_tokens
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ Claude JSON parse error: {e}")
                print(f"Raw content: {content[:200]}...")
                
                # Fallback: use raw text
                return {
                    "success": True,
                    "content": {
                        "introduction": f"Learn about {topic}",
                        "explanation": content,
                        "key_points": [f"Understanding {topic} is important"],
                        "misconceptions": [],
                        "applications": []
                    },
                    "model": self.model,
                    "tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "fallback": True
                }
            
        except Exception as e:
            print(f"❌ Claude generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    async def generate_workflow(
        self,
        topic: str,
        level: str = "beginner"
    ) -> Dict[str, Any]:
        """
        NEW: Generate step-by-step code workflow explanation
        """
        
        prompt = f"""You are a Python educator creating a step-by-step code workflow for {level} students.

Topic: {topic}

Create 4-6 progressive steps that explain how the code works. Each step should include:

1. **step_number**: The step number (1, 2, 3, etc.)
2. **title**: Short descriptive title (e.g., "Initialize Variables")
3. **explanation**: Clear explanation of what happens in this step (2-3 sentences)
4. **code_snippet**: Python code example for this step
5. **variable_example**: Show variable values (e.g., "x = 5, y = 10")
6. **algorithm_visualization**: Describe what's happening algorithmically

CRITICAL: Return ONLY valid JSON array, no markdown formatting, no code blocks.

Format:
[
  {{
    "step_number": 1,
    "title": "Step title here",
    "explanation": "What this step does...",
    "code_snippet": "x = 5\\ny = 10",
    "variable_example": "x is 5, y is 10",
    "algorithm_visualization": "Store values in memory"
  }},
  {{
    "step_number": 2,
    "title": "Next step title",
    "explanation": "What happens next...",
    "code_snippet": "result = x + y",
    "variable_example": "result is 15",
    "algorithm_visualization": "Add two numbers together"
  }}
]

Return the JSON array directly with no ```json wrapper."""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            
            content = response.content[0].text
            content = self._clean_json_response(content)
            
            try:
                workflow_data = json.loads(content)
                
                # Validate it's an array
                if not isinstance(workflow_data, list):
                    raise ValueError("Response is not an array")
                
                return {
                    "success": True,
                    "workflow": workflow_data,
                    "model": self.model,
                    "tokens": response.usage.input_tokens + response.usage.output_tokens
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ Claude workflow JSON parse error: {e}")
                print(f"Raw content: {content[:200]}...")
                
                # Fallback workflow
                return {
                    "success": True,
                    "workflow": [
                        {
                            "step_number": 1,
                            "title": f"Understanding {topic}",
                            "explanation": "Learn the fundamentals of this concept.",
                            "code_snippet": f"# {topic} example\nprint('Hello')",
                            "variable_example": "",
                            "algorithm_visualization": "Step-by-step process"
                        }
                    ],
                    "model": self.model,
                    "tokens": response.usage.input_tokens + response.usage.output_tokens,
                    "fallback": True
                }
            
        except Exception as e:
            print(f"❌ Claude workflow generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "workflow": []
            }
    
    async def generate_hint(
        self,
        exercise_description: str,
        student_code: str,
        hint_level: int = 1
    ) -> str:
        """Generate progressive hints for exercises"""
        
        hint_prompts = {
            1: "Give a gentle nudge in the right direction. Point to which ??? to fill first and what kind of value goes there. Do NOT show the full answer yet.",
            2: "Give a concrete example for ONE of the ??? placeholders. Show the actual Java code they should type for that one field. Explain why that value is correct.",
            3: "Show the complete working code with all ??? replaced with realistic values. The student has asked multiple times and needs to see a full example to learn from."
        }
        
        prompt = f"""You are the Synapse AI Security Tutor for a Java and cybersecurity course for neurodivergent learners. This is JAVA not Python. For knowledge exercises guide concepts step by step. Be encouraging. NEVER mention university or lectures.

Exercise: {exercise_description}

Student's current code:
```java
{student_code}
```

{hint_prompts.get(hint_level, hint_prompts[1])}

Give a helpful, encouraging hint (2-3 sentences max)."""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"❌ Claude hint error: {e}")
            return "Try breaking the problem into smaller steps. You're on the right track!"
    
    async def analyze_student_code(
        self,
        code: str,
        topic: str,
        student_level: str = "beginner"
    ) -> Dict[str, Any]:
        """Analyze student's code and provide educational feedback"""
        
        prompt = f"""You are the Synapse AI Security Tutor analyzing a {student_level} student's code.

Topic: {topic}
Student's Code:
```java
{code}
```

Provide feedback as JSON:
{{
  "positive": "what they did well",
  "improvements": "what could be better",
  "tip": "one specific improvement tip",
  "next_step": "what to learn next"
}}

Return only JSON, no markdown."""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=800,
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            
            content = response.content[0].text
            content = self._clean_json_response(content)
            
            try:
                feedback = json.loads(content)
            except json.JSONDecodeError:
                feedback = {
                    "positive": "Good effort!",
                    "improvements": content,
                    "tip": "Keep practicing!",
                    "next_step": "Try the next exercise"
                }
            
            return {
                "success": True,
                "feedback": feedback,
                "model": self.model
            }
            
        except Exception as e:
            print(f"❌ Claude analysis error: {e}")
            return {
                "success": False,
                "error": str(e),
                "feedback": None
            }
