"""
Synapse AI Tutor - Configuration
Complete settings for MCP + 4 AI integration
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ========================================
# API KEYS - Read from .env file
# ========================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ========================================
# AI MODEL SETTINGS
# ========================================
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Best for educational content
GEMINI_MODEL = "gemini-2.5-flash"      # Best for slides/flowcharts
OPENAI_MODEL = "gpt-4o"                    # Best for exercises
DALLE_MODEL = "dall-e-3"                   # For educational images

# ========================================
# CONTENT GENERATION SETTINGS
# ========================================
ENABLE_CONTENT_CACHING = True  # Cache AI-generated lessons
CACHE_DURATION_DAYS = 30       # How long to cache lessons

# ========================================
# NEURODIVERGENT ADAPTATIONS
# ========================================
NEURODIVERGENT_PROFILES = {
    "autism": {
        "visual_style": "high_contrast",
        "structure": "linear_sequential",
        "examples": "concrete_literal",
        "colors": ["#0066cc", "#00cc66", "#ffcc00"],
        "font_size": "large",
        "animations": "minimal"
    },
    "dyslexia": {
        "font": "OpenDyslexic",
        "font_size": "extra_large",
        "line_spacing": 2.0,
        "text_to_speech": True,
        "color_overlay": "#fdf6e3",
        "visual_emphasis": "high"
    },
    "adhd": {
        "lesson_length": "short",  # 5-10 min chunks
        "interactivity": "high",
        "gamification": True,
        "breaks_frequency": "every_10_min",
        "focus_mode": True,
        "progress_visible": True
    },
    "neurotypical": {
        "balanced": True,
        "adaptive": True
    }
}

# ========================================
# LESSON GENERATION PARAMETERS
# ========================================
LESSON_STRUCTURE = {
    "theory": {
        "max_paragraphs": 5,
        "use_analogies": True,
        "include_visuals": True
    },
    "slides": {
        "count": 5,
        "style": "modern_minimal",
        "one_concept_per_slide": True
    },
    "flowcharts": {
        "count": 2,
        "tool": "mermaid",
        "complexity": "adaptive"
    },
    "images": {
        "count": 3,
        "style": "educational_diagram",
        "color_scheme": "friendly"
    },
    "exercises": {
        "count": 5,
        "difficulty_levels": ["easy", "easy", "medium", "medium", "hard"],
        "auto_grading": True,
        "hints": True
    }
}

# ========================================
# MCP COORDINATOR SETTINGS
# ========================================
MCP_PARALLEL_EXECUTION = True  # Run AIs in parallel
MCP_TIMEOUT_SECONDS = 90       # Max time for generation
MCP_RETRY_ATTEMPTS = 3         # Retry on failure

# ========================================
# ACCESSIBILITY FEATURES
# ========================================
ACCESSIBILITY_FEATURES = {
    "text_to_speech": True,
    "speech_to_text": True,
    "dark_mode": True,
    "dyslexia_font": True,
    "reading_guide": True,
    "zen_mode": True,
    "focus_assist": True,
    "motion_reduction": True,
    "high_contrast": True
}

# ========================================
# SERVER SETTINGS
# ========================================
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 6281,
    "debug": True,
    "cors_enabled": True
}

# ========================================
# TRANSPORT FOR LONDON (TfL) API SETTINGS
# ========================================
TFL_APP_KEY = os.getenv("TFL_APP_KEY", "")
USE_TFL_MOCK = os.getenv("USE_TFL_MOCK", "false").lower() == "true"

def get_tfl_config():
    return {
        "app_key": TFL_APP_KEY,
        "use_mock": USE_TFL_MOCK
    }


# ========================================
# VALIDATION
# ========================================
def validate_config():
    """Check if essential API keys are present"""
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not GOOGLE_API_KEY:
        missing.append("GOOGLE_API_KEY")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    
    if missing:
        print(f"⚠️  Missing API keys: {', '.join(missing)}")
        print("   Add them to your .env file")
        return False
    
    print("✅ All API keys configured!")
    return True

if __name__ == "__main__":
    validate_config()
