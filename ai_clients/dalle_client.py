"""
DALL-E Client - Simple Educational Images
Creates FOCUSED, SIMPLE diagrams for learning
"""

from openai import AsyncOpenAI
import asyncio
from typing import Dict, Any, List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class DALLEClient:
    """DALL-E client for simple educational images"""
    
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.DALLE_MODEL
        print(f"✅ DALL-E client initialized ({self.model})")
    
    async def generate_educational_images(
        self,
        topic: str,
        concepts: List[str],
        style: str = "educational_diagram"
    ) -> Dict[str, Any]:
        """Generate SIMPLE educational images"""
        
        images = []
        
        for i, concept in enumerate(concepts[:3]):
            prompt = self._build_simple_prompt(topic, concept)
            
            try:
                print(f"🎨 Generating image {i+1}/3: {concept[:40]}...")
                
                response = await self.client.images.generate(
                    model=self.model,
                    prompt=prompt,
                    n=1,
                    size="1024x1024",
                    quality="standard"
                )
                
                image_url = response.data[0].url
                
                images.append({
                    "concept": concept,
                    "url": image_url,
                    "prompt": prompt,
                    "description": f"Simple diagram: {concept}",
                    "alt_text": f"{concept} in {topic}"
                })
                
                print(f"✅ Image {i+1} generated!")
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"⚠️ DALL-E image {i+1} error: {e}")
                images.append({
                    "concept": concept,
                    "url": None,
                    "error": str(e),
                    "description": f"Could not generate: {concept}",
                    "alt_text": concept
                })
        
        return {
            "success": len([img for img in images if img.get("url")]) > 0,
            "images": images,
            "count": len(images),
            "model": self.model
        }
    
    def _build_simple_prompt(self, topic: str, concept: str) -> str:
        """Build SIMPLE, FOCUSED prompts"""
        
        # Concept-specific simple prompts
        simple_prompts = {
            "variable": "A single labeled box or container with the word 'age' on it and the number '25' inside. Minimalist flat design, one object only, white background, bright colors.",
            
            "function": "A simple machine or box labeled 'function' with an input arrow on left, output arrow on right. Minimalist diagram, flat design, one concept only.",
            
            "loop": "A circular arrow showing repetition, with simple numbers 1, 2, 3 along the path. Clean minimal design, one concept, white background.",
            
            "conditional": "A simple Y-shaped path showing 'if' decision, with Yes/No arrows. Minimal flat design, bright colors, one decision point only.",
            
            "list": "A vertical stack of 3 numbered boxes showing a list: [0] apple, [1] banana, [2] orange. Simple flat design, one concept.",
            
            "string": "The word 'Hello' in quotation marks with a simple explanation. Minimal design, one concept, bright colors.",
            
            "default": f"A single simple diagram showing {concept}. ONE object or concept only. Flat design, bright colors, white background, minimalist, no text except labels."
        }
        
        # Find matching template
        for key, template in simple_prompts.items():
            if key in concept.lower() or key in topic.lower():
                return template
        
        # Default simple prompt
        return f"""A minimalist educational diagram for {concept}.

CRITICAL REQUIREMENTS:
- Show ONLY ONE main concept
- Simple geometric shapes
- Flat design, no 3D
- White or light background
- Maximum 3 colors
- Clear and uncluttered
- Suitable for beginners age 14+
- No complex scenes
- Focus on ONE idea only"""
        
        return base_prompt
