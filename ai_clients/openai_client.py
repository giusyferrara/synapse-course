"""
OpenAI Client - Exercise Generation & Code Evaluation
Uses OpenAI GPT for creating interactive exercises (v1.0+ API)
"""

from openai import AsyncOpenAI
import asyncio
from typing import Dict, Any, List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import json

class OpenAIClient:
    """OpenAI client for generating exercises and evaluating code"""
    
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        print(f"✅ OpenAI client initialized ({self.model})")
    
    async def generate_exercises(
        self,
        topic: str,
        level: str = "beginner",
        theory_content: str = "",
        count: int = 5
    ) -> Dict[str, Any]:
        """Generate progressive exercises"""
        
        prompt = f"""Create {count} Python programming exercises for teaching "{topic}" to {level} students.

Theory context:
{theory_content[:500]}

Generate exercises with progressive difficulty: easy, easy, medium, medium, hard

For each exercise, provide:
1. Title (clear, engaging)
2. Description (what student should do)
3. Difficulty level (easy/medium/hard)
4. Starter code (template to help them start)
5. Expected output
6. Hints (3 progressive hints)

Format as JSON array:
[
  {{
    "exercise_number": 1,
    "title": "Create Your First Variable",
    "description": "Create a variable called 'age' and set it to 25, then print it",
    "difficulty": "easy",
    "starter_code": "# Create a variable here\\n",
    "expected_output": "25",
    "hints": [
      "Remember: variable_name = value",
      "Use the format: age = some_number",
      "Don't forget to print the variable!"
    ]
  }},
  ...
]

Make exercises practical and build on each other.
Return ONLY the JSON array.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Python educator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0].strip()
            
            exercises = json.loads(content)
            
            return {
                "success": True,
                "exercises": exercises,
                "count": len(exercises),
                "model": self.model,
                "tokens": response.usage.total_tokens
            }
            
        except json.JSONDecodeError as e:
            print(f"⚠️ OpenAI JSON parse error: {e}")
            return {
                "success": True,
                "exercises": self._create_fallback_exercises(topic, count),
                "count": count,
                "fallback": True
            }
        except Exception as e:
            print(f"❌ OpenAI exercises error: {e}")
            return {
                "success": False,
                "error": str(e),
                "exercises": []
            }
    
    async def evaluate_code(
        self,
        student_code: str,
        exercise: Dict[str, Any],
        topic: str
    ) -> Dict[str, Any]:
        """Evaluate student's code submission"""
        
        prompt = f"""Evaluate this student's Python code for an exercise on {topic}.

Exercise: {exercise.get('title', '')}
Description: {exercise.get('description', '')}

Student's Code:
```python
{student_code}
```

Provide evaluation as JSON:
{{
  "passes_tests": true/false,
  "score": 0-100,
  "feedback": {{
    "positive": "what they did well",
    "issues": ["problems"],
    "suggestions": ["improvements"]
  }},
  "encouragement": "positive message"
}}

Be constructive and encouraging!
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a supportive code reviewer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            
            evaluation = json.loads(content)
            
            return {
                "success": True,
                "evaluation": evaluation,
                "model": self.model
            }
            
        except Exception as e:
            print(f"❌ OpenAI evaluation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_fallback_exercises(self, topic: str, count: int) -> List[Dict]:
        """Create basic exercises if AI generation fails"""
        return [
            {
                "exercise_number": i + 1,
                "title": f"{topic.capitalize()} Exercise {i + 1}",
                "description": f"Practice {topic} concepts",
                "difficulty": "easy" if i < 2 else "medium" if i < 4 else "hard",
                "starter_code": f"# Write your {topic} code here\n",
                "expected_output": "Result",
                "hints": [
                    "Break the problem into steps",
                    "Test your code as you go",
                    "Ask for help if stuck!"
                ]
            }
            for i in range(count)
        ]
