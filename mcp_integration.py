"""
MCP Tools Integration - Complete Edition
=========================================

Integrates advanced learning tools with MCP protocol
- Graph teaching tools
- DALL-E image generation
- Python documentation
- Cryptography tutorials
"""

import json
import asyncio
from typing import Dict, Any, List
from mcp_advanced_tools import (
    GraphTeachingTools,
    DALLEImageGenerator,
    PythonDocsIntegration,
    ProfessionalCryptographyTools
)


def get_available_tools() -> List[Dict[str, Any]]:
    """Get list of all available advanced tools"""
    return [
        {
            'name': 'create_graph',
            'category': 'Visualization',
            'description': 'Create educational graphs and charts',
            'parameters': ['type', 'x', 'y', 'title', 'labels']
        },
        {
            'name': 'graph_tutorial',
            'category': 'Tutorial',
            'description': 'Get interactive graph tutorials',
            'parameters': ['graph_type']
        },
        {
            'name': 'generate_visual',
            'category': 'Visual Learning',
            'description': 'Generate educational images with DALL-E',
            'parameters': ['concept', 'style']
        },
        {
            'name': 'get_python_docs',
            'category': 'Documentation',
            'description': 'Get Python function documentation',
            'parameters': ['function_name']
        },
        {
            'name': 'search_library',
            'category': 'Documentation',
            'description': 'Search Python library information',
            'parameters': ['library_name']
        },
        {
            'name': 'encryption_tutorial',
            'category': 'Cryptography',
            'description': 'Learn encryption methods',
            'parameters': ['method']
        },
        {
            'name': 'encrypt_demo',
            'category': 'Cryptography',
            'description': 'Interactive encryption demonstration',
            'parameters': ['text', 'method', 'key']
        }
    ]


def get_tool_categories() -> Dict[str, Dict[str, Any]]:
    """Get detailed information about tool categories"""
    return {
        'graph_tools': {
            'name': 'Graph Teaching Tools',
            'description': 'Create educational graphs and visualizations',
            'icon': '📊',
            'methods': [
                'create_simple_graph',
                'generate_graph_tutorial'
            ]
        },
        'dalle_tools': {
            'name': 'DALL-E Image Generator',
            'description': 'Generate educational images for visual learning',
            'icon': '🎨',
            'methods': [
                'generate_educational_image'
            ]
        },
        'python_docs': {
            'name': 'Python Documentation',
            'description': 'Quick access to Python function documentation',
            'icon': '📚',
            'methods': [
                'get_function_documentation'
            ]
        },
        'crypto_tools': {
            'name': 'Cryptography Tools',
            'description': 'Learn encryption and security concepts',
            'icon': '🔐',
            'methods': [
                'caesar_cipher',
                'fernet_encryption',
                'rsa_demonstration',
                'cryptographic_hashing',
                'digital_signature_demo',
                'caesar_cipher_tutorial',
                'create_encryption_demo'
            ]
        }
    }


class MCPToolsHandler:
    """Handler for advanced MCP tools"""
    
    def __init__(self):
        self.graph_tools = GraphTeachingTools()
        self.dalle = DALLEImageGenerator()
        self.docs = PythonDocsIntegration()
        self.crypto = ProfessionalCryptographyTools()
        
    async def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route tool calls to appropriate handlers

        Args:
            tool_name: Name of tool to call
            args: Tool arguments

        Returns:
            Tool result
        """
        handlers = {
            'create_graph': self._handle_create_graph,
            'graph_tutorial': self._handle_graph_tutorial,
            'generate_visual': self._handle_generate_visual,
            'get_python_docs': self._handle_python_docs,
            'search_library': self._handle_search_library,
            'encryption_tutorial': self._handle_encryption_tutorial,
            'encrypt_demo': self._handle_encrypt_demo
        }

        handler = handlers.get(tool_name)
        if handler:
            try:
                result = await handler(args)
                return {
                    'success': True,
                    'tool': tool_name,
                    'result': result
                }
            except Exception as e:
                return {
                    'success': False,
                    'tool': tool_name,
                    'error': str(e)
                }
        else:
            available = [t['name'] for t in get_available_tools()]
            return {
                'success': False,
                'error': f'Unknown tool: {tool_name}',
                'available_tools': available
            }

    async def _handle_create_graph(self, args: Dict) -> Dict:
        """Handle graph creation"""
        graph_data = {
            'type': args.get('type', 'line'),
            'x': args.get('x', []),
            'y': args.get('y', []),
            'title': args.get('title', 'Educational Graph'),
            'labels': args.get('labels', [])
        }

        image_data = self.graph_tools.create_simple_graph(graph_data)

        return {
            'image': image_data,
            'type': graph_data['type'],
            'explanation': f"Created {graph_data['type']} graph: {graph_data['title']}"
        }

    async def _handle_graph_tutorial(self, args: Dict) -> Dict:
        """Handle graph tutorial request"""
        graph_type = args.get('graph_type', 'line')
        tutorial = self.graph_tools.generate_graph_tutorial(graph_type)
        return tutorial

    async def _handle_generate_visual(self, args: Dict) -> Dict:
        """Handle DALL-E image generation"""
        concept = args.get('concept', 'function')
        style = args.get('style', 'cartoon')

        result = self.dalle.generate_educational_image(concept, style)
        return result

    async def _handle_python_docs(self, args: Dict) -> Dict:
        """Handle Python documentation request"""
        function_name = args.get('function_name', 'print')
        docs = self.docs.get_function_documentation(function_name)
        return docs

    async def _handle_search_library(self, args: Dict) -> Dict:
        """Handle library search"""
        library_name = args.get('library_name', 'requests')
        
        # Simple library info (since search_library might not exist in PythonDocsIntegration)
        libraries = {
            'requests': {
                'name': 'requests',
                'description': 'HTTP library for Python',
                'docs_url': 'https://requests.readthedocs.io/',
                'install': 'pip install requests',
                'common_use': 'Making HTTP requests to APIs'
            },
            'numpy': {
                'name': 'numpy',
                'description': 'Numerical computing library',
                'docs_url': 'https://numpy.org/doc/',
                'install': 'pip install numpy',
                'common_use': 'Arrays, matrices, mathematical operations'
            },
            'pandas': {
                'name': 'pandas',
                'description': 'Data analysis and manipulation',
                'docs_url': 'https://pandas.pydata.org/docs/',
                'install': 'pip install pandas',
                'common_use': 'DataFrames, CSV processing, data analysis'
            },
            'matplotlib': {
                'name': 'matplotlib',
                'description': 'Data visualization library',
                'docs_url': 'https://matplotlib.org/stable/contents.html',
                'install': 'pip install matplotlib',
                'common_use': 'Creating plots, charts, and graphs'
            }
        }
        
        return libraries.get(library_name, {
            'name': library_name,
            'description': f'Information for {library_name} not available',
            'suggestion': 'Visit https://pypi.org/ to search for this library'
        })

    async def _handle_encryption_tutorial(self, args: Dict) -> Dict:
        """Handle encryption tutorial"""
        method = args.get('method', 'caesar')

        if method == 'caesar':
            return self.crypto.caesar_cipher_tutorial()
        else:
            return {
                'title': f'Encryption: {method}',
                'description': f'Tutorial for {method} coming soon!',
                'available_tutorials': ['caesar', 'fernet', 'rsa', 'hash']
            }

    async def _handle_encrypt_demo(self, args: Dict) -> Dict:
        """Handle encryption demonstration"""
        text = args.get('text', 'HELLO')
        method = args.get('method', 'caesar')
        key = args.get('key', 3)

        return self.crypto.create_encryption_demo(text, method, key)


# Integration with existing tutor
async def extend_tutor_with_advanced_tools(tutor_instance):
    """
    Extend existing tutor with advanced MCP tools

    Usage:
        tutor = EnhancedSecurityTutor()
        await extend_tutor_with_advanced_tools(tutor)
    """
    tools_handler = MCPToolsHandler()

    # Add new methods to tutor
    async def tool_create_graph(args):
        """Create educational graph"""
        return await tools_handler.handle_tool_call('create_graph', args)

    async def tool_graph_tutorial(args):
        """Get graph tutorial"""
        return await tools_handler.handle_tool_call('graph_tutorial', args)

    async def tool_generate_visual(args):
        """Generate visual with DALL-E"""
        return await tools_handler.handle_tool_call('generate_visual', args)

    async def tool_python_docs(args):
        """Get Python documentation"""
        return await tools_handler.handle_tool_call('get_python_docs', args)

    async def tool_search_library(args):
        """Search Python library"""
        return await tools_handler.handle_tool_call('search_library', args)

    async def tool_encryption_tutorial(args):
        """Get encryption tutorial"""
        return await tools_handler.handle_tool_call('encryption_tutorial', args)

    async def tool_encrypt_demo(args):
        """Demonstrate encryption"""
        return await tools_handler.handle_tool_call('encrypt_demo', args)

    # Attach methods to tutor instance
    tutor_instance.tool_create_graph = tool_create_graph
    tutor_instance.tool_graph_tutorial = tool_graph_tutorial
    tutor_instance.tool_generate_visual = tool_generate_visual
    tutor_instance.tool_python_docs = tool_python_docs
    tutor_instance.tool_search_library = tool_search_library
    tutor_instance.tool_encryption_tutorial = tool_encryption_tutorial
    tutor_instance.tool_encrypt_demo = tool_encrypt_demo

    # Get tool categories for display
    categories = get_tool_categories()
    total_tools = len(get_available_tools())

    print("✅ Advanced MCP tools integrated with tutor!")
    print(f"📚 Added {total_tools} new tools across {len(categories)} categories")
    
    for category, info in categories.items():
        print(f"   {info['icon']} {info['name']}")

    return tutor_instance


# MCP Protocol Response Formatter
def format_mcp_response(tool_result: Dict) -> str:
    """
    Format tool result for MCP protocol

    Returns properly formatted JSON for MCP clients
    """
    return json.dumps({
        'jsonrpc': '2.0',
        'result': tool_result,
        'id': None  # Set by MCP server
    }, indent=2)


if __name__ == '__main__':
    # Test integration
    async def test_tools():
        print("=" * 70)
        print("🧪 TESTING MCP TOOLS INTEGRATION")
        print("=" * 70)
        
        handler = MCPToolsHandler()

        # Test 1: Graph creation
        print("\n📊 Test 1: Graph Creation")
        print("-" * 40)
        graph_result = await handler.handle_tool_call('create_graph', {
            'type': 'bar',
            'x': ['Math', 'Science', 'English'],
            'y': [85, 92, 78],
            'title': 'Test Scores'
        })
        print(f"✅ Success: {graph_result.get('success')}")
        if graph_result.get('success'):
            print(f"   Created: {graph_result['result']['type']} graph")

        # Test 2: Python docs
        print("\n📚 Test 2: Python Documentation")
        print("-" * 40)
        docs_result = await handler.handle_tool_call('get_python_docs', {
            'function_name': 'print'
        })
        print(f"✅ Success: {docs_result.get('success')}")
        if docs_result.get('success'):
            result = docs_result['result']
            print(f"   Function: {result['function']}")
            print(f"   Description: {result['description']}")

        # Test 3: Encryption
        print("\n🔐 Test 3: Encryption Demo")
        print("-" * 40)
        crypto_result = await handler.handle_tool_call('encrypt_demo', {
            'text': 'HELLO',
            'method': 'caesar',
            'key': 3
        })
        print(f"✅ Success: {crypto_result.get('success')}")
        if crypto_result.get('success'):
            result = crypto_result['result']
            print(f"   Original: {result['original']}")
            print(f"   Encrypted: {result['result']}")
            print(f"   Method: {result['method']}")

        # Test 4: Library search
        print("\n🔍 Test 4: Library Search")
        print("-" * 40)
        lib_result = await handler.handle_tool_call('search_library', {
            'library_name': 'requests'
        })
        print(f"✅ Success: {lib_result.get('success')}")
        if lib_result.get('success'):
            result = lib_result['result']
            print(f"   Library: {result['name']}")
            print(f"   Description: {result['description']}")

        # Summary
        print("\n" + "=" * 70)
        tools = get_available_tools()
        categories = get_tool_categories()
        print(f"✅ ALL TESTS COMPLETED!")
        print(f"📊 Total Tools Available: {len(tools)}")
        print(f"📂 Total Categories: {len(categories)}")
        print("=" * 70)

    asyncio.run(test_tools())












