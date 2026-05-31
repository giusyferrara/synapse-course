#!/usr/bin/env python3
"""
Educational Programming Tutor MCP Server
Provides accessibility-focused programming education tools via MCP protocol
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource
)

# Import your existing classes
from core.tutor import EnhancedSecurityTutor
from core.emotion import AdvancedEmotionAnalyzer
from core.engine import TeachingEngine
from ai.router import AIRouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EducationalTutorMCPServer:
    def __init__(self):
        self.server = Server("educational-tutor")
        self.tutor = EnhancedSecurityTutor()
        
        # Register MCP tools
        self._register_tools()
        
    def _register_tools(self):
        """Register all educational tools with the MCP server"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available educational tools"""
            return [
                Tool(
                    name="analyze_code_comprehensive",
                    description="Comprehensive code analysis with security review, emotional state awareness, and neurodivergent adaptations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to analyze"
                            },
                            "user_message": {
                                "type": "string", 
                                "description": "Student's current mood or feelings",
                                "default": ""
                            },
                            "student_id": {
                                "type": "string",
                                "description": "Unique student identifier for personalization",
                                "default": "anonymous"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="generate_visual_explanation",
                    description="Create accessibility-focused visual explanations of programming concepts with interactive diagrams",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to visualize"
                            },
                            "user_message": {
                                "type": "string",
                                "description": "Context about student's learning needs",
                                "default": ""
                            },
                            "accessibility_level": {
                                "type": "string",
                                "enum": ["basic", "intermediate", "advanced"],
                                "description": "Complexity level for visual explanations",
                                "default": "intermediate"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="review_code_security",
                    description="Analyze code for security vulnerabilities with educational explanations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to review for security issues"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="explain_code_concepts",
                    description="Explain programming concepts with AI-enhanced educational content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to explain"
                            },
                            "learning_style": {
                                "type": "string",
                                "enum": ["visual", "auditory", "kinesthetic", "reading"],
                                "description": "Preferred learning style",
                                "default": "visual"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="suggest_code_improvements",
                    description="Suggest improvements for code quality, security, and best practices",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to improve"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="generate_practice_exercises",
                    description="Generate personalized coding exercises based on current code",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Base code to generate exercises from"
                            },
                            "difficulty": {
                                "type": "string",
                                "enum": ["beginner", "intermediate", "advanced"],
                                "description": "Exercise difficulty level",
                                "default": "intermediate"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="run_code_tests",
                    description="Execute code with safety checks and generate automated tests",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to test"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="diagnose_ai_systems",
                    description="Test AI services connectivity and capabilities for educational features",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="analyze_emotional_state",
                    description="Analyze student's emotional and cognitive state for personalized learning adaptations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Student's message or input to analyze"
                            },
                            "context": {
                                "type": "object",
                                "description": "Additional context about the learning session",
                                "default": {}
                            }
                        },
                        "required": ["message"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Execute educational tools based on MCP requests"""
            
            try:
                if name == "analyze_code_comprehensive":
                    result = await self.tutor.tool_execute_python_debug(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "generate_visual_explanation":
                    result = await self.tutor.tool_visual_explanation(arguments)
                    
                    # Check if result is JSON (Mermaid diagram)
                    try:
                        json_result = json.loads(result)
                        if "mermaid_code" in json_result:
                            return CallToolResult(
                                content=[
                                    TextContent(
                                        type="text", 
                                        text=json_result["analogy"]
                                    ),
                                    EmbeddedResource(
                                        type="resource",
                                        resource={
                                            "uri": "data:text/plain;base64," + 
                                                   json_result["mermaid_code"].encode('base64').decode(),
                                            "mimeType": "text/plain"
                                        }
                                    )
                                ]
                            )
                    except (json.JSONDecodeError, KeyError):
                        pass
                    
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "review_code_security":
                    result = await self.tutor.tool_secure_review(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "explain_code_concepts":
                    result = await self.tutor.tool_explain_code(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "suggest_code_improvements":
                    result = await self.tutor.tool_suggest_fixes(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "generate_practice_exercises":
                    result = await self.tutor.tool_generate_tests(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "run_code_tests":
                    result = await self.tutor.tool_run_tests(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "diagnose_ai_systems":
                    result = await self.tutor.tool_test_ai(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "analyze_emotional_state":
                    # Direct emotional analysis
                    emotion_state = self.tutor.emotion_analyzer.analyze_comprehensive_state(
                        message=arguments["message"],
                        user_id="mcp_user",
                        context=arguments.get("context", {})
                    )
                    
                    result = json.dumps(emotion_state, indent=2)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text", 
                            text=f"Unknown tool: {name}"
                        )],
                        isError=True
                    )
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {str(e)}")
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=f"Error executing {name}: {str(e)}"
                    )],
                    isError=True
                )

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="educational-tutor",
                    server_version="1.0.0",
                    capabilities={
                        "tools": {},
                        "prompts": {},
                        "resources": {}
                    }
                )
            )

async def main():
    """Main entry point"""
    logger.info("Starting Educational Tutor MCP Server...")
    
    server = EducationalTutorMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())#!/usr/bin/env python3
"""
Educational Programming Tutor MCP Server
Provides accessibility-focused programming education tools via MCP protocol
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource
)

# Import your existing classes
from core.tutor import EnhancedSecurityTutor
from core.emotion import AdvancedEmotionAnalyzer
from core.engine import TeachingEngine
from ai.router import AIRouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EducationalTutorMCPServer:
    def __init__(self):
        self.server = Server("educational-tutor")
        self.tutor = EnhancedSecurityTutor()
        
        # Register MCP tools
        self._register_tools()
        
    def _register_tools(self):
        """Register all educational tools with the MCP server"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available educational tools"""
            return [
                Tool(
                    name="analyze_code_comprehensive",
                    description="Comprehensive code analysis with security review, emotional state awareness, and neurodivergent adaptations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to analyze"
                            },
                            "user_message": {
                                "type": "string", 
                                "description": "Student's current mood or feelings",
                                "default": ""
                            },
                            "student_id": {
                                "type": "string",
                                "description": "Unique student identifier for personalization",
                                "default": "anonymous"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="generate_visual_explanation",
                    description="Create accessibility-focused visual explanations of programming concepts with interactive diagrams",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to visualize"
                            },
                            "user_message": {
                                "type": "string",
                                "description": "Context about student's learning needs",
                                "default": ""
                            },
                            "accessibility_level": {
                                "type": "string",
                                "enum": ["basic", "intermediate", "advanced"],
                                "description": "Complexity level for visual explanations",
                                "default": "intermediate"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="review_code_security",
                    description="Analyze code for security vulnerabilities with educational explanations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to review for security issues"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="explain_code_concepts",
                    description="Explain programming concepts with AI-enhanced educational content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to explain"
                            },
                            "learning_style": {
                                "type": "string",
                                "enum": ["visual", "auditory", "kinesthetic", "reading"],
                                "description": "Preferred learning style",
                                "default": "visual"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="suggest_code_improvements",
                    description="Suggest improvements for code quality, security, and best practices",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to improve"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="generate_practice_exercises",
                    description="Generate personalized coding exercises based on current code",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Base code to generate exercises from"
                            },
                            "difficulty": {
                                "type": "string",
                                "enum": ["beginner", "intermediate", "advanced"],
                                "description": "Exercise difficulty level",
                                "default": "intermediate"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="run_code_tests",
                    description="Execute code with safety checks and generate automated tests",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to test"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="diagnose_ai_systems",
                    description="Test AI services connectivity and capabilities for educational features",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="analyze_emotional_state",
                    description="Analyze student's emotional and cognitive state for personalized learning adaptations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Student's message or input to analyze"
                            },
                            "context": {
                                "type": "object",
                                "description": "Additional context about the learning session",
                                "default": {}
                            }
                        },
                        "required": ["message"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Execute educational tools based on MCP requests"""
            
            try:
                if name == "analyze_code_comprehensive":
                    result = await self.tutor.tool_execute_python_debug(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "generate_visual_explanation":
                    result = await self.tutor.tool_visual_explanation(arguments)
                    
                    # Check if result is JSON (Mermaid diagram)
                    try:
                        json_result = json.loads(result)
                        if "mermaid_code" in json_result:
                            return CallToolResult(
                                content=[
                                    TextContent(
                                        type="text", 
                                        text=json_result["analogy"]
                                    ),
                                    EmbeddedResource(
                                        type="resource",
                                        resource={
                                            "uri": "data:text/plain;base64," + 
                                                   json_result["mermaid_code"].encode('base64').decode(),
                                            "mimeType": "text/plain"
                                        }
                                    )
                                ]
                            )
                    except (json.JSONDecodeError, KeyError):
                        pass
                    
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "review_code_security":
                    result = await self.tutor.tool_secure_review(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "explain_code_concepts":
                    result = await self.tutor.tool_explain_code(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "suggest_code_improvements":
                    result = await self.tutor.tool_suggest_fixes(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "generate_practice_exercises":
                    result = await self.tutor.tool_generate_tests(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "run_code_tests":
                    result = await self.tutor.tool_run_tests(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "diagnose_ai_systems":
                    result = await self.tutor.tool_test_ai(arguments)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                elif name == "analyze_emotional_state":
                    # Direct emotional analysis
                    emotion_state = self.tutor.emotion_analyzer.analyze_comprehensive_state(
                        message=arguments["message"],
                        user_id="mcp_user",
                        context=arguments.get("context", {})
                    )
                    
                    result = json.dumps(emotion_state, indent=2)
                    return CallToolResult(
                        content=[TextContent(type="text", text=result)]
                    )
                
                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text", 
                            text=f"Unknown tool: {name}"
                        )],
                        isError=True
                    )
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {str(e)}")
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=f"Error executing {name}: {str(e)}"
                    )],
                    isError=True
                )

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="educational-tutor",
                    server_version="1.0.0",
                    capabilities={
                        "tools": {},
                        "prompts": {},
                        "resources": {}
                    }
                )
            )

async def main():
    """Main entry point"""
    logger.info("Starting Educational Tutor MCP Server...")
    
    server = EducationalTutorMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
