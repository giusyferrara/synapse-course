import time
import json
import subprocess
import sys
import tempfile
import os
from datetime import datetime

# Add parent directory to path to import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_advanced_tools import (
    GraphTeachingTools,
    DALLEImageGenerator,
    PythonDocsIntegration,
    ProfessionalCryptographyTools
)

from core.engine import TeachingEngine
from ai.router import AIRouter
from database.config import SessionLocal
from database.models import Student, LearningSession, AIResponse, ChatConversation, ChatMessage

class EnhancedSecurityTutor:
    """
    Comprehensive AI tutor for neurodivergent learners
    Supports multiple learning levels and adaptive content delivery
    """
    
    def __init__(self):
        self.ai_router = AIRouter()
        self.teacher = TeachingEngine()
        self.graph_tools = GraphTeachingTools()
        self.dalle_tools = DALLEImageGenerator()
        self.python_docs = PythonDocsIntegration()
        self.crypto_tools = ProfessionalCryptographyTools()

    def get_db_session(self):
        return SessionLocal()
    
    def _get_student_id(self, args):
        """Get student/participant ID - REJECT anonymous/temp IDs"""
        student_id = args.get("student_id") or args.get("participant_id")
        
        # ❌ REJECT anonymous/temporary IDs
        if not student_id or student_id in ["anonymous", "web_user", "anonymous_user", "", "null", "undefined"]:
            return None
        
        # ❌ REJECT temporary IDs
        if student_id.startswith("TEMP_"):
            return None
        
        return student_id

    def _ensure_utf8(self, text: str) -> str:
        """Ensure proper UTF-8 encoding for all text output"""
        if isinstance(text, str):
            return text.encode('utf-8', errors='ignore').decode('utf-8')
        return str(text)

    def _create_response_json(self, response_text: str, **kwargs) -> str:
        """Create standardized JSON response"""
        return json.dumps({
            "response": self._ensure_utf8(response_text),
            **kwargs
        }, ensure_ascii=False)

    async def tool_execute_python_debug(self, args):
        """Enhanced execute with comprehensive analysis and database logging."""
        start_time = time.time()
        code = args.get("code", "")
        user_message = args.get("user_message", "")
        student_id_str = self._get_student_id(args)

        db = self.get_db_session()
        try:
            # Get or create student record
            student = db.query(Student).filter(Student.student_id == student_id_str).first()
            if not student:
                student = Student(student_id=student_id_str, neurodivergent_type="unknown")
                db.add(student)
                db.commit()
                db.refresh(student)

            # Create learning session
            session = LearningSession(
                student_record_id=student.id,
                code_submitted=code,
                mood_input=user_message
            )
            db.add(session)
            db.flush()

            # Execute code
            if not code.strip():
                return self._create_response_json("No code provided. Write some Python code and try again!")

            # Run security analysis first
            security_findings = self.teacher.secure_findings(code)
            # === SANDBOX: Block dangerous code ===
            import re
            code_lower = code.lower()
            code_normalized = re.sub(r'\s+', ' ', code).lower()
            BLOCKED = ['import os', 'import subprocess', 'import sys', 'import shutil',
                       'import socket', 'import pathlib', 'import crypt', 'import getpass',
                       'import resource', 'import platform', 'import ctypes', 'import signal',
                       'import http', 'import urllib', 'import requests', 'import pickle',
                       'import shelve', 'import marshal', 'import sqlite3', 'import pty',
                       'import glob', 'import tempfile', 'import io', 'import fcntl',
                       'from os', 'from subprocess', 'from pathlib', 'from shutil',
                       'from socket', 'from ctypes', 'from http', 'from urllib',
                       'os.system', 'os.popen', 'os.environ', 'os.listdir', 'os.remove',
                       'os.getcwd', 'os.chdir', 'os.mkdir', 'os.rmdir', 'os.unlink',
                       '__import__', '__builtins__', '__subclasses__', '__globals__',
                       'subprocess.run', 'subprocess.call', 'subprocess.Popen',
                       'open(', 'exec(', 'eval(', 'compile(',
                       'globals(', 'locals(', 'vars(', 'getattr(', 'setattr(',
                       '/opt/', '/root/', '/etc/', '/home/', '/tmp/', '/var/',
                       '/usr/', '/bin/', '/sbin/', '/proc/', '/dev/',
                       'useradd', 'usermod', 'userdel', 'passwd', 'chmod', 'chown',
                       'sudoers', 'authorized_keys', 'crontab', 'rm -rf', 'rm -r',
                       '.env', 'environ']
            for b in BLOCKED:
                if b in code_lower or b in code_normalized:
                    return self._create_response_json(f'\U0001f512 Security: "{b}" is not allowed in this learning environment.')
            execution_output = ""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='/tmp') as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
                os.chmod(temp_file_path, 0o644)

            try:
                result = subprocess.run(
                    [
                        'docker', 'run', '--rm',
                        '--network', 'none',
                        '--memory', '64m',
                        '--cpus', '0.5',
                        '--pids-limit', '50',
                        '--read-only',
                        '--tmpfs', '/tmp:size=10m',
                        '--security-opt', 'no-new-privileges',
                        '-v', f'{temp_file_path}:/code/run.py:ro',
                        'synapse-sandbox',
                        'python3', '/code/run.py'
                    ],
                    capture_output=True,
                    text=True,
                    timeout=12
                )
                execution_output = result.stdout + result.stderr
                has_errors = bool(result.returncode != 0)
            except subprocess.TimeoutExpired:
                execution_output = "Code execution timed out after 10 seconds."
                has_errors = True
                subprocess.run(['docker', 'kill', '--signal=KILL'], capture_output=True, timeout=5)
            except Exception as e:
                execution_output = f"Execution error: {str(e)}"
                has_errors = True
            finally:
                os.unlink(temp_file_path)

            # Analyze results
            code_info = self.teacher.ast_summary(code)

            # Get AI assistance if needed
            ai_response = ""
            if has_errors:
                ai_response = await self.ai_router.get_tutor_response(
                    f"Help debug this code with clear explanations: {code}\nError: {execution_output}"
                )

            # Save AI response
            if ai_response:
                ai_record = AIResponse(
                    session_id=session.id,
                    tool_used="analyze",
                    ai_response=ai_response,
                    response_time=time.time() - start_time
                )
                db.add(ai_record)

            db.commit()

            # Format response
            response_parts = [
                "=" * 50,
                "PYTHON EXECUTION RESULTS",
                "=" * 50,
                "",
                "OUTPUT:",
                execution_output or "(No output produced)",
                "",
                f"Functions detected: {len(code_info['functions'])}",
                f"Security issues: {len(security_findings)}",
                ""
            ]

            if security_findings:
                response_parts.extend([
                    "SECURITY WARNINGS:",
                    *[f"• Line {f['lineno']}: {f['reason']}" for f in security_findings],
                    ""
                ])

            if ai_response:
                response_parts.extend([
                    "AI TUTOR FEEDBACK:",
                    ai_response,
                    ""
                ])

            execution_time = time.time() - start_time
            response_parts.append(f"Analysis completed in {execution_time:.2f}s")
            return self._create_response_json("\n".join(response_parts))
            
        except Exception as e:
            db.rollback()
            return self._create_response_json(f"Error during analysis: {str(e)}")
        finally:
            db.close()

    async def tool_visual_guide(self, args):
        """Generate comprehensive visual programming guide"""
        code = args.get("code", "")
        user_message = args.get("user_message", "")
        student_id = self._get_student_id(args)
        
        if not code.strip():
            return self._create_response_json(self._generate_programming_basics_visual())

        # Analyze code structure
        info = self.teacher.ast_summary(code)
        security_findings = self.teacher.secure_findings(code)

        parts = [
            "🎨 VISUAL PROGRAMMING EXPLANATION",
            "=" * 50,
            ""
        ]

        # 1. CODE STRUCTURE VISUALIZATION
        parts.extend(self._generate_code_structure_visual(code, info))

        # 2. STEP-BY-STEP EXECUTION FLOW
        parts.extend(self._generate_execution_flow_visual(code, info))

        # 3. DATA TRANSFORMATION DIAGRAM
        parts.extend(self._generate_data_flow_visual(code, info))

        # 4. SECURITY VULNERABILITY MAPPING (if any)
        if security_findings:
            parts.extend(self._generate_security_visual(code, security_findings))

        # 5. INTERACTIVE LEARNING COMPONENTS
        parts.extend(self._generate_interactive_learning(code, info))

        # 6. MERMAID DIAGRAM FOR COMPLEX FLOWS
        mermaid_diagram = self._generate_mermaid_diagram(code, info)
        if mermaid_diagram:
            return json.dumps({
                "analogy": "\n".join(parts),
                "mermaid_code": mermaid_diagram
            })

        return self._create_response_json("\n".join(parts))

    def _generate_code_structure_visual(self, code: str, info: dict) -> list:
        """Generate visual breakdown of code structure"""
        parts = [
            "🏗️ CODE STRUCTURE BREAKDOWN",
            "-" * 30,
            ""
        ]

        # Visual hierarchy
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip():
                indent_level = (len(line) - len(line.lstrip())) // 4
                indent_visual = "  " * indent_level + "├─ " if indent_level > 0 else "🔸 "
                # Color-code different elements
                if line.strip().startswith('def '):
                    parts.append(f"Line {i:2d}: {indent_visual}🔧 FUNCTION: {line.strip()}")
                elif '=' in line and not line.strip().startswith('#'):
                    parts.append(f"Line {i:2d}: {indent_visual}📦 VARIABLE: {line.strip()}")
                elif line.strip().startswith('if ') or line.strip().startswith('elif ') or line.strip().startswith('else'):
                    parts.append(f"Line {i:2d}: {indent_visual}🚦 DECISION: {line.strip()}")
                elif line.strip().startswith('for ') or line.strip().startswith('while '):
                    parts.append(f"Line {i:2d}: {indent_visual}🔄 LOOP: {line.strip()}")
                elif line.strip().startswith('return'):
                    parts.append(f"Line {i:2d}: {indent_visual}📤 OUTPUT: {line.strip()}")
                else:
                    parts.append(f"Line {i:2d}: {indent_visual}⚙️ ACTION: {line.strip()}")

        parts.extend(["", ""])
        return parts

    def _generate_execution_flow_visual(self, code: str, info: dict) -> list:
        """Generate step-by-step execution visualization"""
        parts = [
            "🏃 STEP-BY-STEP EXECUTION FLOW",
            "-" * 30,
            ""
        ]

        if info["functions"]:
            func = info["functions"][0]
            parts.extend([
                f"📊 EXECUTION PATH for {func['name']}():",
                "",
                "```",
                "🚀 START EXECUTION",
                "    ↓",
                f"📥 RECEIVE INPUT: {', '.join(func['args'])}",
                "    ↓"
            ])

            # Analyze the function body
            lines = code.split('\n')
            for line in lines[1:]:  # Skip function definition
                if line.strip() and not line.strip().startswith('#'):
                    if 'query' in line.lower():
                        parts.append("📝 BUILD DATABASE QUERY")
                        parts.append("    ↓")
                    elif 'return' in line:
                        parts.append("📤 RETURN RESULT")
                        parts.append("    ↓")
                    else:
                        parts.append(f"⚙️ PROCESS: {line.strip()[:40]}...")
                        parts.append("    ↓")

            parts.extend([
                "🏁 END EXECUTION",
                "```",
                ""
            ])

        return parts

    def _generate_data_flow_visual(self, code: str, info: dict) -> list:
        """Generate data transformation visualization"""
        parts = [
            "📊 DATA FLOW VISUALIZATION",
            "-" * 30,
            ""
        ]

        # Analyze variables and data flow
        if 'user_id' in code:
            parts.extend([
                "🔄 DATA TRANSFORMATION CHAIN:",
                "",
                "```",
                "Input Data    →    Processing    →    Output",
                "┌─────────┐       ┌─────────┐        ┌─────────┐",
                "│user_id  │   →   │ f-string │    →   │SQL query│",
                "│'123'    │       │formatting│        │result   │",
                "└─────────┘       └─────────┘        └─────────┘",
                "```",
                ""
            ])

            if 'f"' in code or "f'" in code:
                parts.extend([
                    "⚠️ STRING INTERPOLATION VISUAL:",
                    "",
                    "BEFORE: user_id = '123'",
                    "DURING: f\"SELECT * FROM users WHERE id = '{user_id}'\"",
                    "AFTER:  \"SELECT * FROM users WHERE id = '123'\"",
                    "",
                    "🚨 DANGER ZONE: User input becomes part of SQL command!",
                    ""
                ])

        return parts

    def _generate_security_visual(self, code: str, security_findings: list) -> list:
        """Generate security vulnerability visualization"""
        parts = [
            "🔒 SECURITY VULNERABILITY MAP",
            "-" * 30,
            ""
        ]

        parts.extend([
            "🚨 ATTACK VISUALIZATION:",
            "",
            "```",
            "Normal Input:     '123'",
            "↓",
            "Safe Query:       SELECT * FROM users WHERE id = '123'",
            "↓",
            "Result:          ✅ User data returned",
            "",
            "Malicious Input:  \"1'; DROP TABLE users; --\"",
            "↓",
            "Dangerous Query:  SELECT * FROM users WHERE id = '1'; DROP TABLE users; --'",
            "↓",
            "Result:          💥 DATABASE DESTROYED!",
            "```",
            ""
        ])

        for finding in security_findings:
            parts.extend([
                f"📍 Line {finding['lineno']}: {finding['call']}",
                f"   💀 Risk: {finding['reason']}",
                f"   🛡️ Fix: Use parameterized queries",
                ""
            ])

        parts.extend([
            "✅ SECURE VERSION:",
            "```python",
            "def get_user_safe(user_id):",
            "    query = \"SELECT * FROM users WHERE id = ?\"",
            "    return execute_query(query, [user_id])  # Safe!",
            "```",
            ""
        ])

        return parts

    def _generate_interactive_learning(self, code: str, info: dict) -> list:
        """Generate truly interactive learning components with validation"""
        parts = [
            "🎯 INTERACTIVE LEARNING CHALLENGES",
            "-" * 30,
            ""
        ]

        if info["functions"]:
            func_name = info["functions"][0]["name"]
            # Generate interactive HTML form instead of static text
            interactive_html = self._create_interactive_security_challenge(func_name)
            parts.extend([
                "🔐 INTERACTIVE CODING PUZZLE:",
                "CHALLENGE: Complete the secure version of the function",
                "Fill in the blanks below and click 'Check Answer' for immediate feedback",
                "",
                interactive_html,
                "",
                "🎯 Learning Objectives:",
                "1. Understand input validation techniques",
                "2. Learn parameterized query syntax",
                "3. Practice secure coding patterns",
                "4. Get immediate feedback on your understanding",
                ""
            ])

        # Add debugging exercise
        parts.extend([
            "🐛 INTERACTIVE DEBUGGING EXERCISE:",
            "",
            self._create_interactive_debugging_challenge(code),
            ""
        ])

        return parts

    def _create_interactive_security_challenge(self, func_name: str) -> str:
        """Create an interactive HTML form for security learning"""
        challenge_id = "security_challenge"
        html = f'''
    <div id="{challenge_id}" style="background: #f8fafc; padding: 20px; border-radius: 10px; margin: 10px 0;">
        <h4>🛡️ Secure Coding Challenge</h4>
        <p>Complete the secure version of <code>{func_name}</code>:</p>
        <div style="background: #1e293b; color: #e2e8f0; padding: 15px; border-radius: 8px; font-family: monospace; margin: 10px 0;">
            <div>def secure_get_user(user_id):</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;# Step 1: Validate input</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;if not user_id or not <input type="text" id="answer1" placeholder="type validation" style="background: #374151; color: white; border: 1px solid #6b7280; padding: 2px;">:</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;return None</div>
            <div><br></div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;# Step 2: Use safe query</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;query = "SELECT * FROM users WHERE id = <input type="text" id="answer2" placeholder="placeholder" style="background: #374151; color: white; border: 1px solid #6b7280; padding: 2px;">"</div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;return execute_query(query, [<input type="text" id="answer3" placeholder="parameter" style="background: #374151; color: white; border: 1px solid #6b7280; padding: 2px;">])</div>
        </div>
        <button onclick="checkSecurityAnswers()" style="background: #10b981; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-right: 10px;">Check Answer</button>
        <button onclick="getHint()" style="background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-right: 10px;">Get Hint</button>
        <button onclick="showSolution()" style="background: #8b5cf6; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">Show Solution</button>
        <div id="feedback" style="margin-top: 15px; padding: 10px; border-radius: 6px; display: none;"></div>
        <div id="hint" style="margin-top: 15px; padding: 10px; background: #fef3c7; border-radius: 6px; display: none;"></div>
    </div>
    <script>
    const securityAnswers = {{
        answer1: ["isinstance(user_id, (str, int))", "isinstance(user_id, str) or isinstance(user_id, int)", "type(user_id) in (str, int)"],
        answer2: ["?", "?"],
        answer3: ["user_id", "user_id"]
    }};
    let currentHints = {{
        answer1: [
            "Think about Python's type checking function...",
            "Use isinstance() to check if user_id is a string or integer",
            "isinstance(user_id, (str, int))"
        ],
        answer2: [
            "What character represents a parameter placeholder in SQL?",
            "Single character that starts with 'q'...",
            "?"
        ],
        answer3: [
            "What variable should be passed as the parameter?",
            "The same variable name from the function parameter",
            "user_id"
        ]
    }};
    let hintLevel = 0;
    function normalizeAnswer(answer) {{
        return answer.toLowerCase().trim().replace(/\\s+/g, ' ');
    }}
    function checkSecurityAnswers() {{
        const answer1 = document.getElementById('answer1').value;
        const answer2 = document.getElementById('answer2').value;
        const answer3 = document.getElementById('answer3').value;
        let results = [];
        let allCorrect = true;
        const isAnswer1Correct = securityAnswers.answer1.some(correct =>
            normalizeAnswer(answer1) === normalizeAnswer(correct) ||
            normalizeAnswer(answer1).includes(normalizeAnswer(correct))
        );
        results.push({{
            field: 'Input Validation',
            correct: isAnswer1Correct,
            answer: answer1
        }});
        const isAnswer2Correct = securityAnswers.answer2.some(correct =>
            normalizeAnswer(answer2) === normalizeAnswer(correct)
        );
        results.push({{
            field: 'SQL Placeholder',
            correct: isAnswer2Correct,
            answer: answer2
        }});
        const isAnswer3Correct = securityAnswers.answer3.some(correct =>
            normalizeAnswer(answer3) === normalizeAnswer(correct)
        );
        results.push({{
            field: 'Parameter Value',
            correct: isAnswer3Correct,
            answer: answer3
        }});
        allCorrect = results.every(r => r.correct);
        displayFeedback(results, allCorrect);
    }}
    function displayFeedback(results, allCorrect) {{
        const feedbackDiv = document.getElementById('feedback');
        let feedbackHTML = '<h5>' + (allCorrect ? '🎉 Excellent Work!' : '📝 Keep Learning!') + '</h5>';
        results.forEach(result => {{
            const icon = result.correct ? '✅' : '❌';
            const status = result.correct ? 'Correct' : 'Needs work';
            feedbackHTML += `<div style="margin: 5px 0;"><strong>${{icon}} ${{result.field}}:</strong> ${{status}}</div>`;
        }});
        if (allCorrect) {{
            feedbackHTML += '<div style="background: #d1fae5; padding: 10px; border-radius: 6px; margin-top: 10px;"><strong>🎓 Security Concepts Mastered!</strong><br>You understand input validation and parameterized queries!</div>';
        }} else {{
            feedbackHTML += '<div style="background: #fef2f2; padding: 10px; border-radius: 6px; margin-top: 10px;"><strong>🤔 Keep Trying!</strong><br>Review the hints and try again.</div>';
        }}
        feedbackDiv.innerHTML = feedbackHTML;
        feedbackDiv.style.display = 'block';
    }}
    function getHint() {{
        const hintDiv = document.getElementById('hint');
        if (hintLevel < 3) {{
            let hintHTML = '<h5>💡 Hint Level ' + (hintLevel + 1) + '</h5>';
            hintHTML += '<div><strong>Input Validation:</strong> ' + currentHints.answer1[hintLevel] + '</div>';
            hintHTML += '<div><strong>SQL Placeholder:</strong> ' + currentHints.answer2[hintLevel] + '</div>';
            hintHTML += '<div><strong>Parameter:</strong> ' + currentHints.answer3[hintLevel] + '</div>';
            hintDiv.innerHTML = hintHTML;
            hintDiv.style.display = 'block';
            hintLevel++;
        }} else {{
            hintDiv.innerHTML = '<div>You\\'ve seen all hints! Try the "Show Solution" button if you\\'re still stuck.</div>';
        }}
    }}
    function showSolution() {{
        document.getElementById('answer1').value = 'isinstance(user_id, (str, int))';
        document.getElementById('answer2').value = '?';
        document.getElementById('answer3').value = 'user_id';
        const feedbackDiv = document.getElementById('feedback');
        feedbackDiv.innerHTML = '<h5>📚 Complete Solution</h5><div style="background: #e0f2fe; padding: 15px; border-radius: 6px;"><strong>Explanation:</strong><br>• isinstance() checks if user_id is string or integer<br>• ? placeholder prevents SQL injection<br>• user_id parameter passes safely to query</div>';
        feedbackDiv.style.display = 'block';
    }}
    </script>
    '''
        return html

    def _create_interactive_debugging_challenge(self, code: str) -> str:
        """Create an interactive debugging exercise"""
        html = '''
    <div style="background: #fef3c7; padding: 20px; border-radius: 10px; margin: 10px 0;">
        <h4>🐛 Interactive Debugging Challenge</h4>
        <p>Click on the vulnerable line in the original code:</p>
        <div id="debug_code" style="background: #1e293b; color: #e2e8f0; padding: 15px; border-radius: 8px; font-family: monospace; margin: 10px 0;">
    ''' + self._make_code_clickable(code) + '''
        </div>
        <div id="debug_feedback" style="margin-top: 15px; display: none;"></div>
    </div>
    <script>
    function highlightVulnerability(lineElement, lineNumber) {
        document.querySelectorAll('.highlighted-line').forEach(el => {
            el.style.background = 'transparent';
            el.classList.remove('highlighted-line');
        });
        lineElement.style.background = '#7c3aed';
        lineElement.classList.add('highlighted-line');
        const feedbackDiv = document.getElementById('debug_feedback');
        const lineText = lineElement.textContent;
        if (lineText.includes('f"') || lineText.includes("f'")) {
            feedbackDiv.innerHTML = '<div style="background: #d1fae5; padding: 10px; border-radius: 6px;"><strong>🎯 Correct!</strong><br>You identified the SQL injection vulnerability in the f-string formatting!</div>';
        } else {
            feedbackDiv.innerHTML = '<div style="background: #fef2f2; padding: 10px; border-radius: 6px;"><strong>🤔 Try Again!</strong><br>Look for the line that directly includes user input in a SQL query.</div>';
        }
        feedbackDiv.style.display = 'block';
    }
    </script>
    '''
        return html

    def _make_code_clickable(self, code: str) -> str:
        """Convert code into clickable lines for debugging exercise"""
        lines = code.split('\n')
        clickable_html = ""
        for i, line in enumerate(lines, 1):
            if line.strip():
                clickable_html += f'<div onclick="highlightVulnerability(this, {i})" style="cursor: pointer; padding: 2px 5px; margin: 1px 0; border-radius: 3px; transition: background 0.2s;">{line}</div>'
            else:
                clickable_html += '<div><br></div>'
        return clickable_html

    def _generate_mermaid_diagram(self, code: str, info: dict) -> str:
        """Generate Mermaid diagram for complex flows"""
        if not info["functions"]:
            return None

        func = info["functions"][0]
        if any("f-string" in str(finding) or "string concatenation" in str(finding) for finding in self.teacher.secure_findings(code)):
            return f"""graph TD
    A[🚀 Function Called: {func['name']}] --> B[📥 Receive user_id]
    B --> C{{🔍 Input Validation?}}
    C -->|❌ No Validation| D[⚠️ Dangerous Path]
    C -->|✅ Validated| E[🛡️ Safe Path]
    D --> F[📝 String Concatenation]
    F --> G[💥 SQL Injection Risk]
    G --> H[🚨 Database Compromised]
    E --> I[📝 Parameterized Query]
    I --> J[✅ Safe Execution]
    J --> K[📊 Return Data]
    style D fill:#ffcccc
    style F fill:#ffcccc
    style G fill:#ff6666
    style H fill:#ff0000,color:#fff
    style E fill:#ccffcc
    style I fill:#ccffcc
    style J fill:#66ff66
    style K fill:#00ff00,color:#000"""

        return f"""graph TD
    A[🚀 Start: {func['name']}] --> B[📥 Input: {', '.join(func['args'])}]
    B --> C[⚙️ Process Data]
    C --> D[📤 Return Result]
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0"""

    def _generate_programming_basics_visual(self) -> str:
        """Generate basic programming concepts when no code provided"""
        return """🎨 VISUAL PROGRAMMING CONCEPTS
==================================

🧱 VARIABLES - Storage Containers
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ name = "Jo" │    │ age = 25    │    │ grade = 95  │
│             │    │             │    │             │
│  📝 Text    │    │  🔢 Number  │    │  📊 Score   │
└─────────────┘    └─────────────┘    └─────────────┘
```

🔧 FUNCTIONS - Code Machines
```
Input → [🤖 FUNCTION] → Output
"Bob" → [    greet   ] → "Hello Bob!"
  25  → [  double   ] → 50
 data → [  process  ] → result
```

�� DECISIONS - Traffic Light Logic
```
      🤔 Question: Is age >= 18?
         ↙               ↘
    ✅ YES (True)    🔴 NO (False)
         ↓               ↓
   "You can vote"   "Too young"
```

🔄 LOOPS - Carousel Repetition
```
🎠 for each item in list:
   📝 Do something with item
   🔄 Repeat until done
   🛑 Stop when list empty
```

💡 Try writing some code and click 'Visual Guide' for custom diagrams!"""

    async def tool_run_tests(self, args):
        """Generate interactive educational exercises instead of broken pytest"""
        code = args.get("code", "")
        user_message = args.get("user_message", "")
        student_id = self._get_student_id(args)
        
        if not code.strip():
            return self._create_response_json(self._generate_starter_exercises())
        
        # Analyze what the student wrote
        info = self.teacher.ast_summary(code)
        security_findings = self.teacher.secure_findings(code)

        # Create contextual exercises based on their code
        exercises = []

        # Security-focused exercise if vulnerabilities found
        if security_findings:
            exercises.append(self._create_security_exercise(code, security_findings[0]))

        # Function improvement exercise if they wrote functions
        if info["functions"]:
            exercises.append(self._create_function_exercise(info["functions"][0]))

        # Input validation exercise
        exercises.append(self._create_validation_exercise())

        # Error handling exercise
        exercises.append(self._create_error_handling_exercise())

        return self._create_response_json(self._format_interactive_exercises(exercises))

    def _generate_starter_exercises(self):
        """Basic exercises for students with no code"""
        return """🎯 INTERACTIVE CODING EXERCISES
======================================

📝 EXERCISE 1: Complete the Function
```python
def greet_user(name):
    # Fill in the missing code
    if not name or len(name) < 2:
        return "Invalid name"
    return f"Hello, ___!"  # Fix this line
```

✅ Expected Output: greet_user("Alice") should return "Hello, Alice!"

📝 EXERCISE 2: Fix the Security Issue
```python
def search_user(user_input):
    # This has a security problem - fix it
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return query
```

🛡️ Challenge: Make this safe from SQL injection

📝 EXERCISE 3: Add Input Validation
```python
def calculate_age(birth_year):
    # Add validation here
    current_year = 2024
    return current_year - birth_year
```

🎯 Requirements:
- Check if birth_year is a number
- Check if birth_year is reasonable (1900-2024)
- Return error message for invalid input

Copy and paste these into the code area, fill in the blanks, and click 'Run Code' to test!"""

    def _create_security_exercise(self, original_code, finding):
        """Create an exercise to fix a specific security issue"""
        return {
            "type": "security_fix",
            "title": "🛡️ Security Challenge: Fix the Vulnerability",
            "description": f"Your code has a security issue on line {finding['lineno']}",
            "original_code": original_code,
            "vulnerability": finding['reason'],
            "challenge": f"Rewrite the code to eliminate the {finding['call']} vulnerability",
            "hints": [
                "Use parameterized queries instead of string formatting",
                "Separate data from SQL commands",
                "Consider using prepared statements"
            ]
        }

    def _create_function_exercise(self, func_info):
        """Create an exercise to improve a function"""
        return {
            "type": "function_improvement",
            "title": f"🔧 Improve the {func_info['name']} Function",
            "description": "Add missing features to make this function production-ready",
            "tasks": [
                "Add input validation",
                "Add error handling (try/except)",
                "Add type hints",
                "Add a docstring",
                "Handle edge cases"
            ],
            "example": f"""
def {func_info['name']}_improved({', '.join(func_info['args'])}):
    '''
    TODO: Add docstring explaining what this function does
    '''
    # TODO: Add input validation
    if not {func_info['args'][0] if func_info['args'] else 'input'}:
        raise ValueError("Input cannot be empty")

    try:
        # TODO: Add your improved logic here
        pass
    except Exception as e:
        # TODO: Add error handling
        return f"Error: {{e}}"
"""
        }

    def _create_validation_exercise(self):
        """Create input validation exercise"""
        return {
            "type": "validation",
            "title": "✅ Input Validation Challenge",
            "description": "Create a function that safely validates user input",
            "template": """
def validate_email(email):
    '''Validate if an email address is properly formatted'''
    # TODO: Check if email is not None or empty
    # TODO: Check if email contains @ symbol
    # TODO: Check if email has valid format
    # TODO: Return True for valid, False for invalid
    pass

# Test cases to try:
# validate_email("user@example.com") → True
# validate_email("invalid-email") → False
# validate_email("") → False
# validate_email(None) → False
""",
            "hints": [
                "Use 'if not email:' to check for None/empty",
                "Use 'email.count('@')' to check for exactly one @",
                "Use 'email.endswith()' and 'email.startswith()' for basic format",
                "Consider using regular expressions for advanced validation"
            ]
        }

    def _create_error_handling_exercise(self):
        """Create error handling exercise"""
        return {
            "type": "error_handling",
            "title": "🚨 Error Handling Challenge",
            "description": "Add proper error handling to this risky function",
            "template": """
def divide_numbers(a, b):
    '''Safely divide two numbers with proper error handling'''
    # TODO: Add try/except block
    # TODO: Handle division by zero
    # TODO: Handle non-numeric inputs
    # TODO: Return meaningful error messages

    result = a / b  # This line needs protection!
    return result

# Test these cases:
# divide_numbers(10, 2) → 5.0
# divide_numbers(10, 0) → "Error: Cannot divide by zero"
# divide_numbers("a", 2) → "Error: Inputs must be numbers"
""",
            "hints": [
                "Use try/except blocks around risky operations",
                "Check for b == 0 before dividing",
                "Use isinstance() to check if inputs are numbers",
                "Return descriptive error messages"
            ]
        }

    def _format_interactive_exercises(self, exercises):
        """Format exercises into interactive learning format"""
        output = ["🎯 PERSONALIZED CODING EXERCISES", "=" * 50, ""]
        output.append("Based on your code, here are targeted practice exercises:")
        output.append("")

        for i, exercise in enumerate(exercises, 1):
            output.extend([
                f"📝 EXERCISE {i}: {exercise['title']}",
                "-" * 40,
                exercise['description'],
                ""
            ])

            if exercise['type'] == 'security_fix':
                output.extend([
                    f"🚨 Vulnerability Found: {exercise['vulnerability']}",
                    "",
                    "Your current code:",
                    "```python",
                    exercise['original_code'],
                    "```",
                    "",
                    f"Challenge: {exercise['challenge']}",
                    "",
                    "💡 Hints:",
                    *[f"• {hint}" for hint in exercise['hints']],
                    ""
                ])
            elif 'template' in exercise:
                output.extend([
                    "Code template to complete:",
                    "```python",
                    exercise['template'],
                    "```",
                    ""
                ])
                if 'hints' in exercise:
                    output.extend([
                        "💡 Hints:",
                        *[f"• {hint}" for hint in exercise['hints']],
                        ""
                    ])

        output.extend([
            "🎯 HOW TO PRACTICE:",
            "1. Copy an exercise template into the code area",
            "2. Fill in the TODO sections",
            "3. Click 'Run Code' to test your solution",
            "4. Use 'AI Explain' if you get stuck",
            "5. Try the next exercise when ready!",
            "",
            "📈 These exercises build real programming skills used in professional development!"
        ])

        return "\n".join(output)

    async def tool_explain_code(self, args):
        """Explain code with AI enhancement"""
        code = args.get("code", "")
        user_message = args.get("user_message", "")
        student_id = self._get_student_id(args)

        info = self.teacher.ast_summary(code)

        parts = [
            "=" * 50,
            "CODE EXPLANATION",
            "=" * 50,
            f"Functions: {', '.join(f['name'] for f in info['functions']) or 'None'}",
            f"Imports: {', '.join(info['imports']) or 'None'}",
            "",
        ]

        # Try to get AI explanation
        if code.strip():
            prompt = (
                "Explain this code to a student learning programming. "
                "First identify the programming language, then explain what each part does. "
                "Be concrete, use examples, and mention any potential issues or improvements. "
                "Include 2-3 practice exercises at the end.\n\n" + code
            )

            # Invoke Gemini planner: detect language and recommend learning path
            orchestrator_prompt = (
                "You are a pedagogical AI planner for a programming tutor. "
                "Analyse the code below, detect the programming language, and return a JSON plan.\n\n"
                f"Code snippet:\n{code[:400]}\n"
                f"Learner query: {user_message[:200] if user_message else '(no question)'}\n\n"
                "Return ONLY valid JSON in this exact format, no markdown, no prose:\n"
                '{"language": "python|java|other", "suggest_tools": ["tool1", "tool2"]}\n\n'
                "For suggest_tools pick 1-2 from: suggest_fixes, review_code_security, "
                "run_tests, visual_guide. Pick tools relevant to what the learner needs next."
            )
            detected_language = ""
            suggested_tools = []
            try:
                plan_result = await self.ai_router.get_ai_plan(orchestrator_prompt)
                if isinstance(plan_result, dict):
                    detected_language = plan_result.get("language", "").lower()
                    suggested_tools = plan_result.get("suggest_tools", [])
                print(f"AI Planner: Gemini language='{detected_language}', tools={suggested_tools}", flush=True)
            except Exception as plan_err:
                print(f"AI Planner: skipped ({plan_err})", flush=True)

            ai_explanation = await self.ai_router.get_tutor_response(prompt)

            if ai_explanation:
                parts.extend(["AI TEACHER EXPLANATION:", ai_explanation, ""])
                course_map = {
                    "python": "Python Course",
                    "java":   "Java Security",
                }
                tool_labels = {
                    "suggest_fixes": "Suggest Fixes",
                    "review_code_security": "Security Check",
                    "run_tests": "Run Tests",
                    "visual_guide": "Visual Guide",
                }
                course_hint = course_map.get(detected_language)
                tool_hint = [tool_labels.get(t) for t in suggested_tools if t in tool_labels]
                tool_hint = [t for t in tool_hint if t]
                if course_hint or tool_hint:
                    parts.append("")
                    parts.append("Suggested next steps:")
                    if course_hint:
                        parts.append(f"- For structured learning, continue in the {course_hint}.")
                    if tool_hint:
                        if len(tool_hint) == 1:
                            parts.append(f"- To explore this code further, click {tool_hint[0]} above.")
                        else:
                            parts.append(f"- To explore this code further, try: {', '.join(tool_hint)}.")
                    parts.append("")
            else:
                parts.extend([
                    "BASIC ANALYSIS:",
                    "• This code defines functions and may import modules",
                    "• Review each function's purpose and parameters",
                    "• Consider adding type hints and documentation",
                    "",
                ])

        return self._create_response_json("\n".join(parts))

    async def tool_suggest_fixes(self, args):
        """Suggest code improvements with AI enhancement"""
        code = args.get("code", "")
        user_message = args.get("user_message", "")
        student_id = self._get_student_id(args)

        suggestions = self.teacher.suggest_improvements(code)

        parts = ["=" * 50, "SUGGESTED IMPROVEMENTS", "=" * 50]

        if suggestions["tips"]:
            parts.append("IMMEDIATE IMPROVEMENTS:")
            for tip in suggestions["tips"]:
                parts.append(f"• {tip}")
            parts.append("")

        if suggestions["rewritten"]:
            parts.extend([
                "IMPROVED VERSION:", "```python", suggestions["rewritten"], "```", ""
            ])

        # Get AI suggestions
        if code.strip():
            prompt = (
                "Review this Python code and suggest 3-5 specific improvements "
                "for security, readability, and best practices. "
                "Provide brief code examples for each suggestion.\n\n" + code
            )

            ai_suggestions = await self.ai_router.get_tutor_response(prompt)
            if ai_suggestions:
                parts.extend(["AI ENHANCEMENT SUGGESTIONS:", ai_suggestions])

        return self._create_response_json("\n".join(parts))

    async def tool_generate_tests(self, args):
        """Generate educational exercises and practice problems"""
        code = args.get("code", "")
        user_message = args.get("user_message", "")
        student_id = self._get_student_id(args)

        if not code.strip():
            return self._create_response_json(self._generate_basic_exercises())

        # Analyze the code to create relevant exercises
        info = self.teacher.ast_summary(code)

        parts = [
            "=" * 50,
            "PRACTICE EXERCISES",
            "=" * 50,
            "Based on your code, here are some exercises to practice:",
            "",
        ]

        # Generate exercises based on what they wrote
        if any("user" in f["name"].lower() for f in info["functions"]):
            parts.extend([
                "EXERCISE 1: Input Validation",
                "Modify your function to:",
                "• Check if user_id is not None",
                "• Check if user_id is a positive integer",
                "• Return an error message for invalid inputs",
                "",
                "EXERCISE 2: Security Improvement",
                "Rewrite the SQL query to avoid injection:",
                "• Use parameterized queries instead of f-strings",
                "• Research the difference between safe and unsafe queries",
                "",
                "EXERCISE 3: Error Handling",
                "Add try/except blocks to handle:",
                "• Database connection errors",
                "• User not found scenarios",
                "• Network timeout issues",
                "",
            ])

        # General programming exercises
        parts.extend([
            "BONUS CHALLENGES:",
            "1. Add logging to track function calls",
            "2. Create a simple test case manually",
            "3. Add type hints to your function parameters",
            "4. Write docstrings explaining what your function does",
            "",
            "TIP: Try implementing one exercise at a time, then use 'Analyze & Learn' to check your work!",
        ])

        return self._create_response_json("\n".join(parts))

    async def tool_secure_review(self, args):
        """Comprehensive security review"""
        code = args.get("code", "")
        user_message = args.get("user_message", "")
        student_id = self._get_student_id(args)

        findings = self.teacher.secure_findings(code)

        parts = ["=" * 50, "SECURITY REVIEW", "=" * 50]

        if not findings:
            parts.extend([
                "✅ No obvious security issues detected",
                "",
                "GENERAL SECURITY CHECKLIST:",
                "• Validate all user inputs",
                "• Use parameterized queries for databases",
                "• Avoid shell=True in subprocess calls",
                "• Store secrets in environment variables",
                "• Implement proper error handling",
                "",
            ])
        else:
            parts.extend(["�� SECURITY ISSUES FOUND:", ""])
            for finding in findings:
                parts.extend([
                    f"❌ Line {finding['lineno']}: {finding['call']}",
                    f"   Issue: {finding['reason']}",
                    "",
                ])

        return self._create_response_json("\n".join(parts))

    async def tool_test_ai(self, args):
        """Test if AI services are working"""
        user_message = args.get("user_message", "")
        student_id = self._get_student_id(args)

        parts = ["=" * 50, "AI DIAGNOSTIC TEST", "=" * 50]

        # Check API keys
        anthropic_key_set = bool(self.ai_router.anthropic_key)
        openai_key_set = bool(self.ai_router.openai_key)
        google_key_set = bool(self.ai_router.google_key)

        parts.extend([
            f"Anthropic API Key: {'SET' if anthropic_key_set else 'NOT SET'}",
            f"OpenAI API Key: {'SET' if openai_key_set else 'NOT SET'}",
            f"Google API Key: {'SET' if google_key_set else 'NOT SET'}",
            "",
        ])

        # Test AI initialization
        self.ai_router._init_clients()

        parts.extend([
            f"Anthropic Client: {'INITIALIZED' if self.ai_router._anthropic else 'FAILED'}",
            f"OpenAI Client: {'INITIALIZED' if self.ai_router._openai else 'FAILED'}",
            f"Google Gemini Client: {'INITIALIZED' if self.ai_router._gemini else 'FAILED'}",
            "",
        ])

        # Test text AI call
        test_prompt = "Say 'AI is working' in exactly those words."

        if anthropic_key_set or openai_key_set:
            parts.append("Testing Text AI Response:")
            try:
                ai_response = await self.ai_router.get_tutor_response(test_prompt)
                if ai_response:
                    parts.extend([
                        "TEXT AI RESPONSE RECEIVED:",
                        f"'{ai_response.strip()}'",
                        "",
                    ])
                else:
                    parts.extend([
                        "TEXT AI RESPONSE FAILED: No response received",
                        "",
                    ])
            except Exception as e:
                parts.extend([
                    f"TEXT AI RESPONSE ERROR: {str(e)}",
                    "",
                ])

        return self._create_response_json("\n".join(parts))

    def _generate_basic_exercises(self):
        """Generate basic programming exercises when no code is provided"""
        return """======================
BEGINNER PROGRAMMING EXERCISES
======================

EXERCISE 1: Safe User Input
Write a function that:
- Takes a username and password as parameters
- Validates that username is at least 3 characters
- Validates that password is at least 8 characters
- Returns True if valid, False otherwise

EXERCISE 2: Secure Data Processing
Create a function that:
- Takes a list of user data
- Removes any entries with missing information
- Validates email format using regular expressions
- Returns cleaned data

EXERCISE 3: Basic Security Check
Write a function that:
- Checks if a file path is safe (no ../ patterns)
- Validates file extensions against allowed types
- Returns True for safe files, False for dangerous ones

Start with Exercise 1, then paste your code and use 'Analyze & Learn' for feedback!"""

    def _get_adaptation(self, pattern):
        """Get learning adaptations for ADHD patterns"""
        adaptations = {
            "adhd_attention_loss": "Using shorter examples and frequent check-ins",
            "adhd_hyperfocus": "Providing deep-dive resources for extended learning",
            "autism_overwhelm": "Reducing complexity and using structured examples",
            "high_cognitive_load": "Breaking concepts into smaller, manageable pieces",
            "anxiety_indicators": "Providing extra encouragement and clear next steps",
        }
        return adaptations.get(pattern, "Adapting pace to your learning style")

    def _simplify_error_for_adhd(self, error_text):
        """Simplify error messages for ADHD learners"""
        if "SyntaxError" in error_text:
            return "Syntax issue: Check for typos, missing colons, or unmatched brackets"
        if "NameError" in error_text:
            return "Variable not found: Check spelling or if you defined it first"
        if "IndentationError" in error_text:
            return "Indentation problem: Make sure your code blocks line up properly"
        if "TypeError" in error_text:
            return "Type mismatch: Check if you're using the right data types"
        return "Something unexpected happened - let's debug it step by step"

    async def tool_chat_followup(self, args):
        """Handle interactive chat with conversation history"""
        user_message = args.get("message", "")
        student_id_str = self._get_student_id(args)
        conversation_id = args.get("conversation_id")
        code_context = args.get("code", "")

        db = self.get_db_session()
        try:
            # Get or create student
            student = db.query(Student).filter(Student.student_id == student_id_str).first()
            if not student:
                student = Student(student_id=student_id_str, neurodivergent_type="unknown")
                db.add(student)
                db.commit()
                db.refresh(student)

            # Get or create conversation
            if conversation_id:
                conversation = db.query(ChatConversation).filter(
                    ChatConversation.id == conversation_id
                ).first()
            else:
                # Create new conversation
                session = LearningSession(
                    student_record_id=student.id,
                    code_submitted=code_context,
                    mood_input=user_message
                )
                db.add(session)
                db.flush()

                conversation = ChatConversation(
                    student_record_id=student.id,
                    session_id=session.id,
                    topic="Programming Help"
                )
                db.add(conversation)
                db.flush()

            # Get conversation history (last 10 messages for context)
            history = db.query(ChatMessage).filter(
                ChatMessage.conversation_id == conversation.id
            ).order_by(ChatMessage.timestamp.desc()).limit(10).all()
            history.reverse()  # Put in chronological order

            # Save user message
            user_msg = ChatMessage(
                conversation_id=conversation.id,
                role="user",
                message=user_message
            )
            db.add(user_msg)
            db.flush()

            # Build context for AI
            context_messages = []
            for msg in history:
                context_messages.append({
                    "role": msg.role,
                    "content": msg.message
                })
            context_messages.append({"role": "user", "content": user_message})

            # Generate AI response with context
            system_prompt = f"""You are a helpful, clear, structured and patient programming tutor.

Guidelines:
- Use simple, clear language
- Break complex concepts into steps
- Provide encouragement
- Always be supportive and patient

FORMATTING RULES (CRITICAL):

1. Always use clear SECTIONS with emoji headers
2. Add BLANK LINES between sections
3. Use BULLET POINTS for lists
4. Keep each sentence on its own line
5. Use visual separators

RESPONSE STRUCTURE:

🔍 WHAT IT DOES
[Brief 1-line summary]

📝 HOW IT WORKS
- Point 1
- Point 2
- Point 3

⚠️ WARNING (if applicable)
[Security/issue warning]

✅ BETTER APPROACH (if applicable)
[Improved version]

EXAMPLE GOOD RESPONSE:

🔍 WHAT THIS FUNCTION DOES

This retrieves user data from the database.

📝 HOW IT WORKS

- Line 1: Defines function with user_id parameter
- Line 2: Builds SQL query using f-string
- Line 3: Executes query and returns result

⚠️ SECURITY ISSUE

SQL injection vulnerability - user input goes directly into query.

✅ SAFE VERSION

query = "SELECT * FROM users WHERE id = ?"
execute_query(query, [user_id])

{f'Code being discussed: {code_context}' if code_context else ''}

REMEMBER: Always use sections, bullets, and spacing!"""


            # Get AI response
            ai_response = await self.ai_router.get_chat_response(
                system_prompt=system_prompt,
                messages=context_messages
            )

            # Ensure UTF-8 encoding
            if isinstance(ai_response, str):
                ai_response = ai_response.encode('utf-8', errors='ignore').decode('utf-8')

            # Save assistant response
            assistant_msg = ChatMessage(
                conversation_id=conversation.id,
                role="assistant",
                message=ai_response
            )
            db.add(assistant_msg)

            # Update conversation timestamp
            conversation.last_message = datetime.utcnow()
            db.commit()

            # Return response with conversation ID for continuity
            return json.dumps({
                "response": ai_response,
                "conversation_id": conversation.id,
                "message_count": len(history) + 2
            })

        except Exception as e:
            db.rollback()
            return json.dumps({
                "response": f"I encountered an error: {str(e)}. Let's try again!",
                "error": True
            })
        finally:
            db.close()

    async def tool_create_graph(self, args):
        """Create educational graphs"""
        try:
            result = self.graph_tools.create_simple_graph(args)
            return {"result": {"image": result}}
        except Exception as e:
            return {"error": str(e)}
    
    async def tool_graph_tutorial(self, args):
        """Get graph tutorial"""
        try:
            graph_type = args.get('graph_type', 'line')
            result = self.graph_tools.generate_graph_tutorial(graph_type)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def tool_python_docs(self, args):
        """Get Python documentation"""
        try:
            function_name = args.get('function_name', 'print')
            result = self.python_docs.get_function_documentation(function_name)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def tool_encryption_tutorial(self, args):
        """Get encryption tutorial"""
        try:
            method = args.get('method', 'caesar')
            if method == 'caesar':
                result = self.crypto_tools.caesar_cipher_tutorial()
            else:
                result = {"title": f"Encryption: {method}", "explanation": "Tutorial coming soon"}
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def tool_encrypt_demo(self, args):
        """Demonstrate encryption"""
        try:
            text = args.get('text', 'HELLO')
            method = args.get('method', 'caesar')
            key = args.get('key', 3)
            result = self.crypto_tools.create_encryption_demo(text, method, key)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def ask_claude(self, message: str, participant_code: str = None) -> str:
        """Direct chat with Claude"""
        if not self.ai_router._anthropic:
            return "Claude is not available. Please check API key."
        try:
            response = self.ai_router._anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system="You are a helpful Python programming tutor.",
                messages=[{"role": "user", "content": message}]
            )
            return response.content[0].text if response.content else "No response"
        except Exception as e:
            return f"Claude error: {str(e)}"

    async def ask_gpt4(self, message: str, participant_code: str = None) -> str:
        """Direct chat with GPT-4"""
        if not self.ai_router._openai:
            return "GPT-4 is not available. Please check API key."
        try:
            response = self.ai_router._openai.chat.completions.create(
                model="gpt-4",
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": "You are a helpful Python programming tutor."},
                    {"role": "user", "content": message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"GPT-4 error: {str(e)}"

    async def ask_gemini(self, message: str, participant_code: str = None) -> str:
        """Direct chat with Gemini"""
        if not self.ai_router._gemini:
            return "Gemini is not available. Please check API key."
        try:
            response = self.ai_router._gemini.generate_content(message)
            return response.text
        except Exception as e:
            return f"Gemini error: {str(e)}"
