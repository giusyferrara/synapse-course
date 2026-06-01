"""
MCP Coordinator - Orchestrates Multiple AI Models
Coordinates Claude, Gemini, OpenAI, and DALL-E to create complete adaptive lessons
UPDATED: Added workflow generation for code explanations
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from ai_clients.claude_client import ClaudeClient
from ai_clients.gemini_client import GeminiClient
from ai_clients.openai_client import OpenAIClient
from ai_clients.dalle_client import DALLEClient
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPCoordinator:
    """
    Model Context Protocol Coordinator
    Orchestrates multiple AI models to generate adaptive, multimodal learning content
    """
    
    def __init__(self):
        """Initialize all AI clients"""
        try:
            self.claude = ClaudeClient()
            self.gemini = GeminiClient()
            self.openai = OpenAIClient()
            self.dalle = DALLEClient()
            
            self.cache = {}
            logger.info("✅ MCP Coordinator initialized with 4 AI clients")
            
        except Exception as e:
            logger.error(f"❌ MCP Coordinator initialization failed: {e}")
            raise
    
    def get_quiz_ai(self):
        """Lazily build a singleton QuizAIService that reuses the Claude client.

        On-demand quiz 'explain'/'hint' only. The service owns the per-question
        cache + per-user rate limit, so state persists across requests. The
        generation call is synchronous (Anthropic SDK); the aiohttp handler runs
        explain()/hint() in an executor to avoid blocking the event loop.
        """
        if getattr(self, "_quiz_ai", None) is None:
            from quiz.quiz_ai import QuizAIService, MAX_TOKENS

            def _gen(prompt):
                resp = self.claude.client.messages.create(
                    model=self.claude.model,
                    max_tokens=MAX_TOKENS,
                    messages=[{"role": "user", "content": prompt}],
                )
                return resp.content[0].text

            self._quiz_ai = QuizAIService(_gen)
        return self._quiz_ai

    async def generate_complete_lesson(
        self,
        topic: str,
        level: str = "beginner",
        student_profile: Optional[Dict[str, Any]] = None,
        include_workflow: bool = True  # NEW PARAMETER!
    ) -> Dict[str, Any]:
        """
        Generate a complete adaptive lesson using all 4 AIs
        
        This is the MAIN function that coordinates everything!
        
        Args:
            topic: Topic name (e.g., "variables", "functions")
            level: Difficulty level (beginner, intermediate, advanced)
            student_profile: Optional neurodivergent profile
            include_workflow: NEW! Generate code explanation workflow
            
        Returns:
            Complete lesson with theory, slides, flowcharts, workflow, images, exercises
        """
        
        logger.info(f"🎯 Generating complete lesson: {topic} ({level})")
        start_time = datetime.now()
        
        try:
            # STEP 1: Generate theory with Claude (foundation)
            logger.info("📚 Step 1/6: Generating theory with Claude...")
            theory_result = await self.claude.generate_theory(
                topic=topic,
                level=level,
                student_profile=student_profile
            )
            
            if not theory_result["success"]:
                raise Exception(f"Theory generation failed: {theory_result.get('error')}")
            
            theory_content = theory_result["content"]
            theory_text = json.dumps(theory_content) if isinstance(theory_content, dict) else str(theory_content)
            
            # STEP 2-5: Run Gemini, OpenAI, DALL-E, Workflow in parallel (faster!)
            logger.info("⚡ Steps 2-5: Running multiple AIs in parallel...")
            
            if config.MCP_PARALLEL_EXECUTION:
                # Parallel execution - MUCH faster!
                tasks = []
                
                # Slides
                tasks.append(self.gemini.generate_slides(
                    topic=topic,
                    theory_content=theory_text,
                    level=level,
                    count=config.LESSON_STRUCTURE["slides"]["count"]
                ))
                
                # Flowcharts
                tasks.append(self.gemini.generate_flowcharts(
                    topic=topic,
                    concept=f"{topic} process and workflow",
                    count=config.LESSON_STRUCTURE["flowcharts"]["count"]
                ))
                
                # Exercises
                tasks.append(self.openai.generate_exercises(
                    topic=topic,
                    level=level,
                    theory_content=theory_text,
                    count=config.LESSON_STRUCTURE["exercises"]["count"]
                ))
                
                # NEW: Code Workflow (using Claude)
                if include_workflow:
                    tasks.append(self.generate_code_workflow(
                        topic=topic,
                        level=level,
                        theory_content=theory_content
                    ))
                else:
                    tasks.append(asyncio.sleep(0))  # Placeholder
                
                # Run all in parallel
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                slides_result = results[0] if not isinstance(results[0], Exception) else {"slides": []}
                flowcharts_result = results[1] if not isinstance(results[1], Exception) else {"flowcharts": []}
                exercises_result = results[2] if not isinstance(results[2], Exception) else {"exercises": []}
                workflow_result = results[3] if include_workflow and not isinstance(results[3], Exception) else {"workflow": []}
                
            else:
                # Sequential execution (safer but slower)
                logger.info("🎨 Step 2/6: Generating slides with Gemini...")
                slides_result = await self.gemini.generate_slides(
                    topic=topic,
                    theory_content=theory_text,
                    level=level,
                    count=config.LESSON_STRUCTURE["slides"]["count"]
                )
                
                logger.info("📊 Step 3/6: Generating flowcharts with Gemini...")
                flowcharts_result = await self.gemini.generate_flowcharts(
                    topic=topic,
                    concept=f"{topic} process and workflow",
                    count=config.LESSON_STRUCTURE["flowcharts"]["count"]
                )
                
                logger.info("�� Step 4/6: Generating exercises with OpenAI...")
                exercises_result = await self.openai.generate_exercises(
                    topic=topic,
                    level=level,
                    theory_content=theory_text,
                    count=config.LESSON_STRUCTURE["exercises"]["count"]
                )
                
                # NEW: Generate workflow
                logger.info("🛠️ Step 5/6: Generating code workflow with Claude...")
                if include_workflow:
                    workflow_result = await self.generate_code_workflow(
                        topic=topic,
                        level=level,
                        theory_content=theory_content
                    )
                else:
                    workflow_result = {"workflow": []}
            
            # STEP 6: Generate images with DALL-E (uses exercises context)
            logger.info("🖼️ Step 6/6: Generating images with DALL-E...")
            
            # Extract concepts from theory for visualization
            concepts_to_visualize = self._extract_visual_concepts(topic, theory_content)
            
            images_result = await self.dalle.generate_educational_images(
                topic=topic,
                concepts=concepts_to_visualize,
                style="educational_diagram"
            )
            
            # STEP 7: Apply neurodivergent adaptations
            if student_profile:
                logger.info("♿ Applying neurodivergent adaptations...")
                adaptations = self._apply_adaptations(student_profile)
            else:
                adaptations = {}
            
            # STEP 8: Combine everything into complete lesson
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Lesson generated in {elapsed:.1f}s")
            
            complete_lesson = {
                "success": True,
                "topic": topic,
                "level": level,
                "generated_at": datetime.now().isoformat(),
                "generation_time": elapsed,
                
                "theory": theory_content,
                "slides": slides_result.get("slides", []),
                "flowcharts": flowcharts_result.get("flowcharts", []),
                "workflow": workflow_result.get("workflow", []),  # NEW!
                "images": images_result.get("images", []),
                "exercises": exercises_result.get("exercises", []),
                "adaptations": adaptations,
                
                "metadata": {
                    "models_used": {
                        "theory": theory_result.get("model", "claude"),
                        "slides": slides_result.get("model", "gemini"),
                        "flowcharts": flowcharts_result.get("model", "gemini"),
                        "workflow": "claude",  # NEW!
                        "images": images_result.get("model", "dalle-3"),
                        "exercises": exercises_result.get("model", "gpt-4")
                    },
                    "tokens_used": {
                        "theory": theory_result.get("tokens", 0),
                        "exercises": exercises_result.get("tokens", 0),
                        "workflow": workflow_result.get("tokens", 0)  # NEW!
                    },
                    "student_profile": student_profile
                }
            }
            
            # Cache if enabled
            if config.ENABLE_CONTENT_CACHING:
                cache_key = f"{topic}_{level}"
                self.cache[cache_key] = complete_lesson
                logger.info(f"💾 Lesson cached: {cache_key}")
            
            return complete_lesson
            
        except Exception as e:
            logger.error(f"❌ Lesson generation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "topic": topic,
                "level": level
            }
    
    async def generate_code_workflow(
        self,
        topic: str,
        level: str,
        theory_content: Any
    ) -> Dict[str, Any]:
        """
        NEW FUNCTION: Generate step-by-step code workflow explanation
        
        Shows how code works with:
        - Code snippets for each step
        - Variable examples
        - Algorithm visualization
        - Explanations in simple language
        
        Args:
            topic: The programming topic
            level: Difficulty level
            theory_content: The theory to base workflow on
            
        Returns:
            Dict with workflow steps
        """
        
        try:
            # Use Claude's generate_workflow method
            response = await self.claude.generate_workflow(
                topic=topic,
                level=level
            )
            
            if not response.get("success"):
                raise Exception(f"Claude workflow generation failed: {response.get('error')}")
            
            workflow_steps = response.get("workflow", [])
            
            if not workflow_steps:
                # Fallback workflow
                workflow_steps = self._generate_fallback_workflow(topic)
            
            return {
                "success": True,
                "workflow": workflow_steps,
                "tokens": response.get("tokens", 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Workflow generation error: {e}")
            return {
                "success": False,
                "workflow": self._generate_fallback_workflow(topic),
                "error": str(e)
            }
    
    def _parse_workflow_json(self, content: str) -> List[Dict[str, Any]]:
        """Parse workflow JSON from Claude's response"""
        try:
            # Look for JSON array in the response
            if '[' in content and ']' in content:
                start = content.find('[')
                end = content.rfind(']') + 1
                json_str = content[start:end]
                
                workflow = json.loads(json_str)
                
                # Validate structure
                if isinstance(workflow, list) and len(workflow) > 0:
                    return workflow
            
            return []
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse workflow JSON: {e}")
            return []
    
    def _generate_fallback_workflow(self, topic: str) -> List[Dict[str, Any]]:
        """Generate fallback workflow when AI generation fails"""
        return [
            {
                "step_number": 1,
                "title": f"Understanding {topic}",
                "explanation": f"Learn the basics of {topic} and how it works in Python.",
                "code_snippet": f"# {topic} example\nprint('Hello, World!')",
                "variable_example": "",
                "algorithm_visualization": "Processing the concept step by step"
            },
            {
                "step_number": 2,
                "title": "Practice Exercise",
                "explanation": "Try writing your own code based on what you learned.",
                "code_snippet": "# Your code here\n",
                "variable_example": "",
                "algorithm_visualization": "Apply your knowledge"
            }
        ]
    
    def _extract_visual_concepts(self, topic: str, theory: Any) -> List[str]:
        """Extract key concepts that need visual representation"""
        
        # Default concepts based on topic
        concept_map = {
            "variables": [
                "variable as a labeled container",
                "variable assignment process",
                "variable types comparison"
            ],
            "functions": [
                "function definition and call",
                "function parameters flow",
                "return value visualization"
            ],
            "loops": [
                "while loop process",
                "for loop iteration",
                "loop break and continue"
            ],
            "conditionals": [
                "if-else decision tree",
                "boolean logic flow",
                "nested conditions"
            ],
            "lists": [
                "list as ordered container",
                "list indexing visualization",
                "list methods overview"
            ],
            "london_transport": [
                "TfL API connection flow",
                "JSON data structure",
                "real-time data visualization"
            ]
        }
        
        # Try to extract from theory if it's structured
        if isinstance(theory, dict) and "key_points" in theory:
            concepts = theory["key_points"][:3]
        else:
            concepts = concept_map.get(topic, [f"{topic} concept {i+1}" for i in range(3)])
        
        return concepts
    
    def _apply_adaptations(self, student_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Apply neurodivergent-specific adaptations"""
        
        profile_type = student_profile.get("type", "neurotypical")
        profile_config = config.NEURODIVERGENT_PROFILES.get(profile_type, {})
        
        return {
            "profile_type": profile_type,
            "visual_style": profile_config.get("visual_style", "standard"),
            "font": profile_config.get("font", "standard"),
            "colors": profile_config.get("colors", []),
            "structure": profile_config.get("structure", "standard"),
            "features_enabled": {
                "text_to_speech": profile_config.get("text_to_speech", False),
                "high_contrast": profile_type == "autism",
                "short_chunks": profile_type == "adhd",
                "visual_emphasis": profile_type == "dyslexia"
            }
        }
    
    async def get_cached_lesson(self, topic: str, level: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached lesson if available"""
        cache_key = f"{topic}_{level}"
        return self.cache.get(cache_key)
    
    async def regenerate_section(
        self,
        topic: str,
        section: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Regenerate a specific section of a lesson
        
        Args:
            topic: Topic name
            section: Which section (theory, slides, exercises, images, workflow)
            context: Existing lesson context
            
        Returns:
            Regenerated section
        """
        
        logger.info(f"🔄 Regenerating {section} for {topic}")
        
        try:
            if section == "theory":
                return await self.claude.generate_theory(topic, context.get("level", "beginner"))
            
            elif section == "slides":
                return await self.gemini.generate_slides(
                    topic,
                    str(context.get("theory", "")),
                    context.get("level", "beginner")
                )
            
            elif section == "exercises":
                return await self.openai.generate_exercises(
                    topic,
                    context.get("level", "beginner"),
                    str(context.get("theory", ""))
                )
            
            elif section == "images":
                concepts = self._extract_visual_concepts(topic, context.get("theory"))
                return await self.dalle.generate_educational_images(topic, concepts)
            
            elif section == "workflow":  # NEW!
                return await self.generate_code_workflow(
                    topic=topic,
                    level=context.get("level", "beginner"),
                    theory_content=context.get("theory")
                )
            
            else:
                return {"success": False, "error": f"Unknown section: {section}"}
                
        except Exception as e:
            logger.error(f"❌ Section regeneration failed: {e}")
            return {"success": False, "error": str(e)}


# Test function
async def test_mcp():
    """Test MCP Coordinator with full lesson generation"""
    coordinator = MCPCoordinator()
    
    print("\n" + "="*60)
    print("🧪 TESTING MCP COORDINATOR - FULL LESSON GENERATION")
    print("="*60)
    
    # Test with a simple topic
    result = await coordinator.generate_complete_lesson(
        topic="variables",
        level="beginner",
        student_profile={"type": "autism"},
        include_workflow=True  # NEW!
    )
    
    if result["success"]:
        print(f"\n✅ LESSON GENERATED SUCCESSFULLY!")
        print(f"⏱️  Time: {result['generation_time']:.1f}s")
        print(f"\n📚 Theory: {str(result['theory'])[:100]}...")
        print(f"🎨 Slides: {len(result.get('slides', []))} slides")
        print(f"📊 Flowcharts: {len(result.get('flowcharts', []))} flowcharts")
        print(f"🛠️ Workflow: {len(result.get('workflow', []))} steps")  # NEW!
        print(f"🖼️  Images: {len(result.get('images', []))} images")
        print(f"💪 Exercises: {len(result.get('exercises', []))} exercises")
        print(f"\n🎯 Models used:")
        for key, model in result["metadata"]["models_used"].items():
            print(f"   - {key}: {model}")
    else:
        print(f"\n❌ LESSON GENERATION FAILED: {result['error']}")


if __name__ == "__main__":
    asyncio.run(test_mcp())
