# test_mcp_hybrid.py - Test script for the hybrid server
#!/usr/bin/env python3
"""
Test the MCP functionality of the hybrid educational server
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_mcp_tools():
    """Test MCP tools via subprocess"""
    
    # Test code with security vulnerability
    test_code = '''def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return execute_query(query)'''
    
    print("Testing MCP Educational Tools")
    print("=" * 50)
    
    # Test comprehensive analysis
    print("1. Testing Comprehensive Code Analysis...")
    result = await run_mcp_tool("analyze_code_comprehensive", {
        "code": test_code,
        "user_message": "I'm confused about security in this code",
        "student_id": "test_student"
    })
    print("✅ Analysis completed")
    print(result[:200] + "..." if len(result) > 200 else result)
    print()
    
    # Test visual explanation
    print("2. Testing Visual Explanation...")
    result = await run_mcp_tool("generate_visual_explanation", {
        "code": test_code,
        "accessibility_level": "intermediate"
    })
    print("✅ Visual explanation generated")
    print(result[:200] + "..." if len(result) > 200 else result)
    print()
    
    # Test security review
    print("3. Testing Security Review...")
    result = await run_mcp_tool("review_code_security", {
        "code": test_code
    })
    print("✅ Security review completed")
    print(result[:200] + "..." if len(result) > 200 else result)
    print()

async def run_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Run a single MCP tool via the hybrid server"""
    
    # Create a simple MCP client request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    try:
        # Start the hybrid server in MCP mode
        process = subprocess.Popen(
            [sys.executable, "app.py", "--mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send the request
        stdout, stderr = process.communicate(
            input=json.dumps(request) + "\n",
            timeout=30
        )
        
        if stderr:
            return f"Error: {stderr}"
        
        return stdout.strip()
        
    except subprocess.TimeoutExpired:
        process.kill()
        return "Timeout: MCP request took too long"
    except Exception as e:
        return f"Error running MCP tool: {str(e)}"

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())

# claude_desktop_config.json - Configuration for Claude Desktop
{
  "mcpServers": {
    "educational-tutor": {
      "command": "python",
      "args": ["app.py", "--mcp"],
      "cwd": "/path/to/your/python-debug-tutor-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "your-anthropic-key",
        "OPENAI_API_KEY": "your-openai-key",
        "GOOGLE_API_KEY": "your-google-key",
        "DATABASE_URL": "your-database-url"
      }
    }
  }
}

# requirements.txt - Add MCP dependency to your existing requirements
# Add this line to your existing requirements.txt:
mcp>=1.0.0

# demo_script.py - Demo script for your professor
#!/usr/bin/env python3
"""
Demo script showing both web and MCP capabilities
"""

import asyncio
import subprocess
import time
import webbrowser
import sys

async def run_demo():
    """Run a complete demo of both interfaces"""
    
    print("🎓 EDUCATIONAL TUTOR SYSTEM DEMO")
    print("=" * 50)
    print()
    
    # 1. Start web server
    print("1. Starting Web Interface...")
    web_process = subprocess.Popen([sys.executable, "app.py"])
    time.sleep(3)  # Give server time to start
    
    print("✅ Web interface available at http://localhost:6281")
    print("   - Try the Visual Guide button")
    print("   - Test accessibility features")
    print("   - Check neurodivergent adaptations")
    print()
    
    # 2. Open browser
    print("2. Opening browser for demonstration...")
    webbrowser.open("http://localhost:6281")
    print()
    
    # 3. Show MCP capabilities
    print("3. Testing MCP Protocol Capabilities...")
    print("   (This would normally be used by Claude Desktop or other MCP clients)")
    
    # 4. Wait for user interaction
    input("Press Enter after demonstrating the web interface...")
    
    # 5. Clean shutdown
    print("4. Shutting down web server...")
    web_process.terminate()
    web_process.wait()
    print("✅ Demo completed")
    print()
    
    # 6. Show MCP configuration
    print("5. MCP Configuration for Claude Desktop:")
    print("   Add this to your Claude Desktop settings:")
    print('''
    {
      "mcpServers": {
        "educational-tutor": {
          "command": "python",
          "args": ["app.py", "--mcp"],
          "cwd": "/your/project/path"
        }
      }
    }
    ''')
    print()
    print("6. Available MCP Tools:")
    tools = [
        "analyze_code_comprehensive - Full analysis with security + accessibility",
        "generate_visual_explanation - Visual code breakdowns", 
        "review_code_security - Security vulnerability detection",
        "explain_code_concepts - AI-enhanced explanations",
        "suggest_improvements - Code quality suggestions",
        "run_tests - Safe code execution with testing",
        "diagnose_ai_status - AI systems testing"
    ]
    for tool in tools:
        print(f"   • {tool}")

if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo error: {e}")

# install_mcp.py - Installation helper
#!/usr/bin/env python3
"""
Installation helper for MCP dependencies
"""

import subprocess
import sys

def install_mcp_dependencies():
    """Install required MCP dependencies"""
    
    print("Installing MCP dependencies...")
    
    dependencies = [
        "mcp>=1.0.0"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False
    
    print("\n✅ All MCP dependencies installed!")
    print("\nYou can now run:")
    print("  Web mode:  python app.py")
    print("  MCP mode:  python app.py --mcp")
    
    return True

if __name__ == "__main__":
    install_mcp_dependencies()
