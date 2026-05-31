"""
Synapse Professional Python Course - UPDATED VERSION
Added: Code Workflow Generation + Loop Prevention + JSON LOADING
"""
import asyncio
import json
import os
from datetime import datetime, timedelta

class PythonCourseContent:
    """
    Professional Python course with AI-generated content
    Features:
    - 4 AI models generating adaptive content
    - Real-world projects (London Transport API)
    - Neurodivergent learning support
    - Progress tracking and analytics
    - NEW: Code workflow explanations
    - NEW: Content caching to prevent AI loops
    - FIXED: Load from JSON files first!
    """

    def __init__(self):
        self.course_structure = self._build_course_structure()
        self.mcp_coordinator = None  # Will be injected
        self.content_cache = {}  # NEW: Cache to prevent regeneration loops
        self.cache_timeout = timedelta(hours=24)  # Cache for 24 hours

    def set_mcp_coordinator(self, coordinator):
        """Inject MCP Coordinator for AI content generation"""
        self.mcp_coordinator = coordinator

    def _build_course_structure(self):
        """Professional course structure with real projects"""
        return {
            'beginner': {
                'title': '🌱 Beginner - Python Foundations',
                'description': 'Master the fundamentals with hands-on projects',
                'color': 'from-green-500 to-emerald-600',
                'topics': [
                    {
                        'id': 'intro',
                        'name': 'Introduction to Python',
                        'icon': '🐍',
                        'duration': '45 min',
                        'description': 'Why Python? Setup and first program',
                        'learning_outcomes': [
                            'Understand why Python is popular',
                            'Set up Python environment',
                            'Write and run your first program',
                            'Use print() and basic syntax'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'variables',
                        'name': 'Variables & Data Types',
                        'icon': '📦',
                        'duration': '60 min',
                        'description': 'Store and manipulate data like a pro',
                        'learning_outcomes': [
                            'Create variables with meaningful names',
                            'Understand int, float, str, bool types',
                            'Convert between data types',
                            'Use variables in calculations'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'operators',
                        'name': 'Operators & Expressions',
                        'icon': '➕',
                        'duration': '50 min',
                        'description': 'Math, logic, and comparisons',
                        'learning_outcomes': [
                            'Use arithmetic operators',
                            'Compare values with operators',
                            'Combine conditions with logic',
                            'Understand operator precedence'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'conditionals',
                        'name': 'If Statements & Decision Making',
                        'icon': '🔀',
                        'duration': '70 min',
                        'description': 'Make your code intelligent',
                        'learning_outcomes': [
                            'Write if/elif/else statements',
                            'Use boolean conditions',
                            'Nest conditionals properly',
                            'Handle complex decision trees'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'loops_for',
                        'name': 'For Loops - Iterate Like a Pro',
                        'icon': '🔄',
                        'duration': '65 min',
                        'description': 'Automate repetitive tasks',
                        'learning_outcomes': [
                            'Loop through ranges',
                            'Iterate over lists and strings',
                            'Use enumerate() and zip()',
                            'Understand loop patterns'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'loops_while',
                        'name': 'While Loops & Loop Control',
                        'icon': '♾️',
                        'duration': '60 min',
                        'description': 'Loop until conditions are met',
                        'learning_outcomes': [
                            'Create while loops safely',
                            'Use break and continue',
                            'Avoid infinite loops',
                            'Choose for vs while correctly'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'functions',
                        'name': 'Functions - DRY Principle',
                        'icon': '⚡',
                        'duration': '80 min',
                        'description': 'Write reusable, modular code',
                        'learning_outcomes': [
                            'Define and call functions',
                            'Use parameters and return values',
                            'Understand scope',
                            'Write documentation strings'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'lists',
                        'name': 'Lists & List Operations',
                        'icon': '📋',
                        'duration': '70 min',
                        'description': 'Master Python\'s most used data structure',
                        'learning_outcomes': [
                            'Create and modify lists',
                            'Use list methods effectively',
                            'Slice and dice lists',
                            'List comprehensions'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'strings',
                        'name': 'String Manipulation',
                        'icon': '📝',
                        'duration': '65 min',
                        'description': 'Process text data professionally',
                        'learning_outcomes': [
                            'Format strings with f-strings',
                            'Use string methods',
                            'Parse and validate text',
                            'Work with multi-line strings'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'dictionaries',
                        'name': 'Dictionaries & JSON',
                        'icon': '🗂️',
                        'duration': '70 min',
                        'description': 'Key-value data structures',
                        'learning_outcomes': [
                            'Create and use dictionaries',
                            'Nested dictionaries',
                            'Work with JSON data',
                            'Dictionary comprehensions'
                        ],
                        'requires_ai_generation': True
                    }
                ]
            },
            'intermediate': {
                'title': '🚀 Intermediate - Real-World Skills',
                'description': 'Build actual applications',
                'color': 'from-blue-500 to-cyan-600',
                'topics': [
                    {
                        'id': 'oop_basics',
                        'name': 'Object-Oriented Programming Basics',
                        'icon': '🏗️',
                        'duration': '90 min',
                        'description': 'Classes, objects, and methods',
                        'learning_outcomes': [
                            'Create classes and objects',
                            'Define methods',
                            'Understand inheritance',
                            'Use OOP principles'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'file_handling',
                        'name': 'File Handling',
                        'icon': '📁',
                        'duration': '75 min',
                        'description': 'Read and write files',
                        'learning_outcomes': [
                            'Open and close files',
                            'Read file content',
                            'Write to files',
                            'Handle file errors'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'exceptions',
                        'name': 'Error Handling',
                        'icon': '🛡️',
                        'duration': '70 min',
                        'description': 'Handle errors gracefully',
                        'learning_outcomes': [
                            'Use try/except',
                            'Create custom exceptions',
                            'Handle multiple errors',
                            'Clean up resources'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'modules',
                        'name': 'Modules & Packages',
                        'icon': '📦',
                        'duration': '80 min',
                        'description': 'Organize code professionally',
                        'learning_outcomes': [
                            'Import modules',
                            'Create packages',
                            'Use pip',
                            'Manage dependencies'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'london_transport',
                        'name': '🚇 PROJECT: London Transport API',
                        'icon': '🚇',
                        'duration': '120 min',
                        'description': 'Build a real API integration',
                        'learning_outcomes': [
                            'Use TfL API',
                            'Make HTTP requests',
                            'Parse JSON responses',
                            'Build practical applications'
                        ],
                        'is_project': True,
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'apis',
                        'name': 'Working with APIs',
                        'icon': '🌐',
                        'duration': '90 min',
                        'description': 'RESTful APIs and requests',
                        'learning_outcomes': [
                            'Understand REST',
                            'Use requests library',
                            'Handle API responses',
                            'Authenticate requests'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'data_structures_advanced',
                        'name': 'Advanced Data Structures',
                        'icon': '🧮',
                        'duration': '85 min',
                        'description': 'Sets, tuples, and more',
                        'learning_outcomes': [
                            'Use sets effectively',
                            'Work with tuples',
                            'Choose right structure',
                            'Optimize performance'
                        ],
                        'requires_ai_generation': True
                    }
                ]
            },
            'advanced': {
                'title': '🔥 Advanced - Professional Development',
                'description': 'Industry-ready skills',
                'color': 'from-purple-500 to-pink-600',
                'topics': [
                    {
                        'id': 'decorators',
                        'name': 'Decorators & Metaprogramming',
                        'icon': '✨',
                        'duration': '100 min',
                        'description': 'Advanced Python features',
                        'learning_outcomes': [
                            'Create decorators',
                            'Use built-in decorators',
                            'Understand closures',
                            'Metaprogramming basics'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'testing',
                        'name': 'Testing & Quality',
                        'icon': '✅',
                        'duration': '95 min',
                        'description': 'Write professional tests',
                        'learning_outcomes': [
                            'Unit testing',
                            'Use pytest',
                            'Test coverage',
                            'TDD principles'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'async',
                        'name': 'Async Programming',
                        'icon': '⚡',
                        'duration': '110 min',
                        'description': 'Concurrent and async code',
                        'learning_outcomes': [
                            'Understand async/await',
                            'Use asyncio',
                            'Handle concurrency',
                            'Build async apps'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'databases',
                        'name': 'Databases & SQL',
                        'icon': '🗄️',
                        'duration': '105 min',
                        'description': 'Work with databases',
                        'learning_outcomes': [
                            'Use SQLite',
                            'Write SQL queries',
                            'Use ORMs',
                            'Manage data'
                        ],
                        'requires_ai_generation': True
                    }
                ]
            },
            'expert': {
                'title': '🏆 Expert - AI & Advanced Topics',
                'description': 'Cutting-edge Python',
                'color': 'from-red-500 to-orange-600',
                'topics': [
                    {
                        'id': 'machine_learning',
                        'name': 'Machine Learning Basics',
                        'icon': '🤖',
                        'duration': '150 min',
                        'description': 'Introduction to ML with Python',
                        'learning_outcomes': [
                            'Understand ML concepts',
                            'Use scikit-learn',
                            'Train simple models',
                            'Make predictions'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'ai_apis',
                        'name': 'Working with AI APIs',
                        'icon': '🤖',
                        'duration': '110 min',
                        'description': 'Claude, OpenAI, and more',
                        'learning_outcomes': [
                            'Use Claude API',
                            'Work with OpenAI',
                            'Build AI applications',
                            'Handle API costs'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'web_scraping',
                        'name': 'Web Scraping',
                        'icon': '🕷️',
                        'duration': '95 min',
                        'description': 'Extract data from websites',
                        'learning_outcomes': [
                            'Use BeautifulSoup',
                            'Parse HTML',
                            'Handle dynamic content',
                            'Respect robots.txt'
                        ],
                        'requires_ai_generation': True
                    },
                    {
                        'id': 'final_project',
                        'name': '�� CAPSTONE: Your AI Application',
                        'icon': '🎯',
                        'duration': '300 min',
                        'description': 'Build your portfolio project',
                        'learning_outcomes': [
                            'Design complete application',
                            'Integrate multiple APIs',
                            'Deploy to production',
                            'Create portfolio piece'
                        ],
                        'is_project': True,
                        'requires_ai_generation': True
                    }
                ]
            }
        }

    def get_structure(self):
        """Get complete course structure"""
        return self.course_structure

    def get_topic(self, topic_id):
        """Get specific topic"""
        for level_key, level_data in self.course_structure.items():
            for topic in level_data['topics']:
                if topic['id'] == topic_id:
                    return topic
        return None

    def _is_cache_valid(self, topic_id):
        """Check if cached content is still valid"""
        if topic_id not in self.content_cache:
            return False
        
        cache_entry = self.content_cache[topic_id]
        cache_time = cache_entry.get('timestamp')
        
        if not cache_time:
            return False
        
        # Check if cache expired
        age = datetime.now() - cache_time
        return age < self.cache_timeout

    async def get_ai_generated_content(self, topic_id, student_profile=None):
        """
        �� FIXED: Load from JSON first, then AI fallback
        Priority:
        1. Memory cache (fast)
        2. JSON file (instant)
        3. AI generation (slow)
        """
        
        # STEP 1: Check memory cache first
        if self._is_cache_valid(topic_id):
            print(f"✓ Using cached content for {topic_id}")
            return self.content_cache[topic_id]['content']
        
        # STEP 2: Try loading from JSON file! 🎯
        json_path = f"static/course_content/{topic_id}_active_ai.json"
        
        if os.path.exists(json_path):
            try:
                print(f"📂 Loading {topic_id} from JSON file: {json_path}")
                with open(json_path, 'r', encoding='utf-8') as f:
                    content_data = json.load(f)
                
                # Cache it in memory for next time
                self.content_cache[topic_id] = {
                    'content': content_data,
                    'timestamp': datetime.now()
                }
                
                print(f"✅ Successfully loaded from JSON: {json_path}")
                return content_data
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing error in {json_path}: {e}")
                print(f"   Falling back to AI generation...")
            except Exception as e:
                print(f"⚠️ Error loading JSON {json_path}: {e}")
                print(f"   Falling back to AI generation...")
        else:
            print(f"📂 No JSON file found: {json_path}")
            print(f"   Will use AI generation...")
        
        # STEP 3: AI generation fallback
        if not self.mcp_coordinator:
            print(f"⚠️ No MCP coordinator, using basic fallback")
            topic = self.get_topic(topic_id)
            return self._generate_fallback_content(topic)

        topic = self.get_topic(topic_id)
        if not topic:
            return {"error": "Topic not found"}

        level = self._get_topic_level(topic_id)
        print(f"🤖 Generating AI content for {topic_id} (no JSON available)")

        try:
            # Generate complete lesson with 4 AIs + workflow
            lesson = await self.mcp_coordinator.generate_complete_lesson(
                topic=topic['name'],
                level=level,
                student_profile=student_profile,
                include_workflow=True
            )
            
            # Cache it
            self.content_cache[topic_id] = {
                'content': lesson,
                'timestamp': datetime.now()
            }
            
            print(f"✓ AI content generated and cached for {topic_id}")
            return lesson
            
        except Exception as e:
            print(f"❌ AI generation error: {e}")
            return self._generate_fallback_content(topic)

    def _generate_fallback_content(self, topic):
        """Generate fallback content when AI fails"""
        return {
            'success': True,
            'theory': {
                'introduction': f"Learn about {topic['name']}",
                'explanation': 'Content is being prepared...',
                'key_points': topic.get('learning_outcomes', []),
                'misconceptions': [],
                'applications': []
            },
            'slides': [
                {
                    'title': f"Introduction to {topic['name']}",
                    'content': topic.get('description', ''),
                    'bullets': topic.get('learning_outcomes', [])[:3]
                }
            ],
            'flowcharts': [],
            'workflow': [
                {
                    'step_number': 1,
                    'title': 'Understanding the Concept',
                    'explanation': 'Detailed workflow coming soon...',
                    'code_snippet': '# Example code\n',
                    'variable_example': '',
                    'algorithm_visualization': ''
                }
            ],
            'images': [],
            'exercises': [
                {
                    'title': f'Practice {topic["name"]}',
                    'description': 'Exercise coming soon',
                    'difficulty': 'easy',
                    'starter_code': '# Your code here\n',
                    'hint': 'Break the problem into smaller steps'
                }
            ],
            'generation_time': 0,
            'metadata': {
                'models_used': {},
                'fallback': True
            }
        }

    def clear_cache(self, topic_id=None):
        """
        Clear content cache
        If topic_id provided, clear only that topic
        Otherwise clear all cache
        """
        if topic_id:
            if topic_id in self.content_cache:
                del self.content_cache[topic_id]
                print(f"✓ Cache cleared for {topic_id}")
        else:
            self.content_cache.clear()
            print("✓ All cache cleared")

    def _get_topic_level(self, topic_id):
        """Determine which level a topic belongs to"""
        for level_key, level_data in self.course_structure.items():
            for topic in level_data['topics']:
                if topic['id'] == topic_id:
                    return level_key
        return 'beginner'
