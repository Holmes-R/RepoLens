import os
import ast
import re
from typing import Dict, Any


class ComplexityAnalyzer:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def analyze(self) -> Dict[str, Any]:
        total_files = 0
        total_lines = 0
        total_functions = 0
        total_classes = 0
        function_lengths = []
        complexities = []
        max_complexity = 0
        max_complexity_file = None

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "venv" and d != "__pycache__"]
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()

                if ext not in self._get_supported_exts():
                    continue

                total_files += 1
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue

                lines = content.split("\n")
                total_lines += len(lines)

                # Count functions and classes
                if ext == ".py":
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                total_functions += 1
                                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                                function_lengths.append(func_lines)
                                complexity = self._calculate_python_complexity(node)
                                complexities.append(complexity)
                                if complexity > max_complexity:
                                    max_complexity = complexity
                                    max_complexity_file = os.path.relpath(file_path, self.repo_path)

                            elif isinstance(node, ast.ClassDef):
                                total_classes += 1
                    except SyntaxError:
                        pass
                else:
                    # Generic counting for other languages
                    funcs = re.findall(r'(?:def|function|func|fn)\s+\w+', content)
                    classes = re.findall(r'(?:class|struct)\s+\w+', content)
                    total_functions += len(funcs)
                    total_classes += len(classes)

        avg_function_length = sum(function_lengths) / len(function_lengths) if function_lengths else 0
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0

        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "avg_function_length": round(avg_function_length, 2),
            "avg_complexity": round(avg_complexity, 2),
            "max_complexity": round(max_complexity, 2),
            "max_complexity_file": max_complexity_file,
        }

    def _calculate_python_complexity(self, node) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.Assert)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _get_supported_exts(self) -> set:
        return {
            ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp",
            ".h", ".hpp", ".go", ".rs", ".cs", ".php", ".rb", ".kt",
            ".swift", ".dart", ".scala", ".lua", ".sh", ".r",
        }
