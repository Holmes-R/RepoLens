import os
import re
import ast
from typing import Dict, List, Set, Any


class CallGraphBuilder:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.call_graph: Dict[str, List[str]] = {}
        self.function_definitions: Dict[str, str] = {}

    def build(self) -> Dict[str, List[str]]:
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "venv" and d != "__pycache__"]
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.repo_path)
                ext = os.path.splitext(file)[1].lower()
                if ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".php", ".rb"):
                    self._parse_file(file_path, rel_path, ext)

        return self.call_graph

    def _parse_file(self, file_path: str, rel_path: str, ext: str):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return

        if ext == ".py":
            self._parse_python(content, rel_path)
        else:
            self._parse_generic(content, rel_path, ext)

    def _parse_python(self, content: str, path: str):
        try:
            tree = ast.parse(content)
            current_function = None
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_name = f"{path}::{node.name}"
                    self.function_definitions[func_name] = path
                    if func_name not in self.call_graph:
                        self.call_graph[func_name] = []
                    current_function = func_name

                if isinstance(node, ast.Call) and current_function:
                    if isinstance(node.func, ast.Name):
                        called = node.func.id
                        self.call_graph[current_function].append(called)
                    elif isinstance(node.func, ast.Attribute):
                        called = f"{self._get_attribute_base(node.func)}.{node.func.attr}"
                        self.call_graph[current_function].append(called)
        except SyntaxError:
            pass

    def _parse_generic(self, content: str, path: str, ext: str):
        func_patterns = {
            ".js": r'(?:async\s+)?function\s+(\w+)|const\s+(\w+)\s*=',
            ".ts": r'(?:async\s+)?function\s+(\w+)|const\s+(\w+)\s*=',
            ".go": r'func\s+(?:\([^)]+\)\s+)?(\w+)',
            ".rs": r'fn\s+(\w+)',
            ".java": r'(?:public|private|protected)\s+\w+\s+(\w+)\s*\(',
            ".php": r'function\s+(\w+)',
            ".rb": r'def\s+(\w+)',
        }

        pattern = func_patterns.get(ext)
        if not pattern:
            return

        current_function = None
        lines = content.split("\n")

        for i, line in enumerate(lines):
            matches = re.findall(pattern, line)
            for match in matches:
                func_name = match if isinstance(match, str) else (match[0] or match[1])
                if func_name:
                    qualified = f"{path}::{func_name}"
                    self.function_definitions[qualified] = path
                    self.call_graph[qualified] = []
                    current_function = qualified

            call_pattern = r'(\w+)\s*\('
            for match in re.finditer(call_pattern, line):
                called = match.group(1)
                if called not in ("if", "while", "for", "switch", "catch", "return", "throw", "typeof", "instanceof", "new", "delete", "function"):
                    if current_function:
                        self.call_graph[current_function].append(called)

    def _get_attribute_base(self, node) -> str:
        if isinstance(node, ast.Attribute):
            return f"{self._get_attribute_base(node.value)}.{node.attr}"
        elif isinstance(node, ast.Name):
            return node.id
        return ""
