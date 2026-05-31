import ast
import re
import difflib
from typing import Dict, Any, List

class TeachingEngine:
    """Enhanced teaching engine with security focus and code analysis"""
    RISKY_CALLS = [
        ("eval", "Avoid eval; it executes arbitrary code. Prefer ast.literal_eval for data."),
        ("exec", "Avoid exec; it executes arbitrary code. Refactor to functions."),
        ("pickle.load", "Untrusted pickle is RCE risk. Prefer JSON/MessagePack for untrusted data."),
        ("subprocess", "Validate inputs; avoid shell=True; use list argv; capture return codes."),
        ("os.system", "Command injection risk. Use subprocess with list arguments instead."),
        ("input(", "Always validate and sanitize user input before using it."),
    ]
    SECRET_PATTERNS = [
        (re.compile(r"(api|secret|token|key)\s*=\s*['\"][A-Za-z0-9_\-]{12,}['\"]", re.I), "Hardcoded secret detected. Use environment variables instead."),
        (re.compile(r"password\s*=\s*['\"][^'\"]+['\"]", re.I), "Hardcoded password detected. Use secure credential management."),
    ]
    def ast_summary(self, code: str) -> Dict[str, Any]:
        info = {"functions": [], "imports": [], "danger": [], "issues": []}
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            info["issues"].append(f"SyntaxError at line {e.lineno}: {e.msg}")
            return info
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                args = [a.arg for a in node.args.args]
                info["functions"].append({"name": node.name, "args": args, "lineno": node.lineno})
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [n.name for n in getattr(node, "names", [])]
                info["imports"].extend(names)
            if isinstance(node, ast.Call):
                target = self._call_name(node.func)
                for risky, reason in self.RISKY_CALLS:
                    if target and risky in target:
                        info["danger"].append({"call": target, "lineno": getattr(node, "lineno", "?"), "reason": reason})
        for pat, reason in self.SECRET_PATTERNS:
            for m in pat.finditer(code):
                line_num = code[: m.start()].count("\n") + 1
                info["danger"].append({"call": "hardcoded_secret", "lineno": line_num, "reason": reason})
        return info

    def _call_name(self, func):
        if isinstance(func, ast.Name): return func.id
        if isinstance(func, ast.Attribute):
            base = self._call_name(func.value)
            return f"{base}.{func.attr}" if base else func.attr
        return None

    def secure_findings(self, code: str) -> List[Dict[str, Any]]:
        info = self.ast_summary(code)
        findings = info["danger"]
        security_patterns = [
            (r"os\.system\s*\(", "Potential command injection; prefer subprocess without shell."),
            (r"shell=True", "Command injection risk; use shell=False and list arguments."),
            (r"f['\"].*\{.*\}.*['\"].*execute", "SQL injection risk in formatted query."),
        ]
        for pattern, reason in security_patterns:
            for match in re.finditer(pattern, code):
                line_num = code[:match.start()].count('\n') + 1
                findings.append({"call": pattern.replace(r"\s*\(", ""), "lineno": line_num, "reason": reason})
        return findings

    def suggest_improvements(self, code: str) -> Dict[str, Any]:
        """Generate specific code improvements"""
        tips = []

        try:
            ast.parse(code)
        except SyntaxError as e:
            tips.append(
                f"Fix syntax at line {e.lineno}: {e.msg}. Check missing colon, parenthesis, or quotes."
            )
            return {"tips": tips, "patch": None, "rewritten": None}

        # Security and style tips
        if "print(" in code and "if __name__" not in code:
            tips.append(
                "Wrap demo-prints under `if __name__ == '__main__':` so modules don't execute on import."
            )

        if "subprocess" in code and "shell=True" in code:
            tips.append(
                "Avoid `shell=True`—pass a list argv and validate inputs to reduce injection risk."
            )

        if "input(" in code and "strip(" not in code:
            tips.append(
                "Sanitize user input: use `.strip()` and validate type/range before use."
            )

        if "except:" in code and "Exception" not in code:
            tips.append(
                "Avoid bare `except:`—catch specific exceptions or `Exception as e` and log `e`."
            )

        if re.search(r'f["\'].*\{.*\}.*["\'].*sql', code, re.I):
            tips.append(
                "SQL injection risk: use parameterized queries instead of f-strings in SQL."
            )

        # Generate improved version for common patterns
        rewritten = None
        if "process_student_data" in code:
            rewritten = '''def process_student_data(name: str, grade: int) -> str:
    """Validate and format a student's grade (0-100)."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be non-empty string")
    if not isinstance(grade, int):
        raise TypeError("grade must be int")
    if not (0 <= grade <= 100):
        raise ValueError("grade out of range 0..100")
    return f"Student: {name.strip()}, Grade: {grade}"

if __name__ == '__main__':
    print(process_student_data('Alice', 95))
'''

        # Generate diff if rewritten exists
        patch = None
        if rewritten:
            patch = "\n".join(
                difflib.unified_diff(
                    code.splitlines(),
                    rewritten.splitlines(),
                    fromfile="original.py",
                    tofile="improved.py",
                    lineterm="",
                )
            )

        return {"tips": tips, "patch": patch, "rewritten": rewritten}

    def step_hints(self, error_output: str, code: str) -> List[str]:
        hints = []
        if "SyntaxError" in error_output: hints.extend(["Find the line number in the error message", "Check for missing colons", "Look for unmatched quotes or brackets"])
        elif "NameError" in error_output: hints.extend(["Locate the undefined variable name", "Check for spelling mistakes", "Ensure the variable is defined before use"])
        elif "IndentationError" in error_output: hints.extend(["Check indentation consistency (spaces vs tabs)", "Ensure all code blocks are properly indented"])
        elif "TypeError" in error_output: hints.extend(["Check data types being used in operations", "Verify operations are valid for the data types"])
        else: hints.extend(["Read the error message carefully for clues", "Add print statements to inspect variable values"])
        return hints

    def generate_pytests(self, code: str) -> str:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return "import pytest\n\ndef test_syntax_compiles():\n    pytest.skip('Fix syntax first.')"
        
        funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        if not funcs:
            return "import pytest\n\ndef test_no_functions_present():\n    assert True, 'Add functions to generate tests.'"
        
        f = funcs[0]
        args = [a.arg for a in f.args.args]
        valid_args = ['95' if 'grade' in arg else '"Alice"' if 'name' in arg else '"valid"' for arg in args]
        invalid_args = ['-1' if 'grade' in arg else '""' if 'name' in arg else 'None' for arg in args]
        
        return f"""import pytest
from original_module import {f.name}

def test_{f.name}_happy_path():
    result = {f.name}({", ".join(valid_args)})
    assert result is not None

def test_{f.name}_edge_cases():
    with pytest.raises((ValueError, TypeError)):
        {f.name}({", ".join(invalid_args)})"""