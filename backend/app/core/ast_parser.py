import os
import ast
import re
from typing import Dict, List, Any, Optional


class ASTParser:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        ext = os.path.splitext(file_path)[1].lower()
        rel_path = os.path.relpath(file_path, self.repo_path)

        result = {
            "path": rel_path,
            "imports": [],
            "exports": [],
            "classes": [],
            "functions": [],
            "type": "file",
        }

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return result

        if ext in (".py",):
            return self._parse_python(content, rel_path)
        elif ext in (".js", ".jsx", ".ts", ".tsx"):
            return self._parse_jsts(content, rel_path)
        elif ext in (".java",):
            return self._parse_java(content, rel_path)
        elif ext in (".go",):
            return self._parse_go(content, rel_path)
        elif ext in (".rs",):
            return self._parse_rust(content, rel_path)
        elif ext in (".cs",):
            return self._parse_csharp(content, rel_path)
        elif ext in (".php",):
            return self._parse_php(content, rel_path)

        return result

    def _parse_python(self, content: str, path: str) -> Dict[str, Any]:
        result = {"path": path, "imports": [], "exports": [], "classes": [], "functions": [], "type": "file"}
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        result["imports"].append(f"{module}.{alias.name}" if module else alias.name)
                elif isinstance(node, ast.ClassDef):
                    bases = [self._get_name(b) for b in node.bases]
                    result["classes"].append({
                        "name": node.name,
                        "bases": bases,
                        "methods": [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))],
                        "line": node.lineno,
                    })
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if isinstance(node.parent, ast.Module) if hasattr(node, 'parent') else True:
                        decorators = [self._get_name(d) for d in node.decorator_list]
                        result["functions"].append({
                            "name": node.name,
                            "decorators": decorators,
                            "line": node.lineno,
                        })
        except SyntaxError:
            pass
        return result

    def _parse_jsts(self, content: str, path: str) -> Dict[str, Any]:
        result = {"path": path, "imports": [], "exports": [], "classes": [], "functions": [], "type": "file"}

        # Import patterns
        import_patterns = [
            r'import\s+(?:\{[^}]*\}\s+from\s+)?["\']([^"\']+)["\']',
            r'import\s+\w+\s+from\s+["\']([^"\']+)["\']',
            r'require\(["\']([^"\']+)["\']\)',
            r'import\s+["\']([^"\']+)["\']',
        ]
        for pattern in import_patterns:
            result["imports"].extend(re.findall(pattern, content))

        # Export patterns
        export_patterns = [
            r'export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)',
            r'export\s+\{[^}]+\}',
            r'module\.exports\s*=\s*(\w+)',
        ]
        for pattern in export_patterns:
            exports = re.findall(pattern, content)
            result["exports"].extend(exports)

        # Class patterns
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?'
        for match in re.finditer(class_pattern, content):
            result["classes"].append({
                "name": match.group(1),
                "bases": [match.group(2)] if match.group(2) else [],
                "line": content[:match.start()].count("\n") + 1,
            })

        # Function patterns
        func_pattern = r'(?:async\s+)?function\s+(\w+)|(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>|(\w+)\s*\([^)]*\)\s*\{'
        for match in re.finditer(func_pattern, content):
            name = match.group(1) or match.group(2) or match.group(3)
            if name and name not in ["if", "while", "for", "switch", "catch"]:
                result["functions"].append({
                    "name": name,
                    "line": content[:match.start()].count("\n") + 1,
                })

        return result

    def _parse_java(self, content: str, path: str) -> Dict[str, Any]:
        result = {"path": path, "imports": [], "exports": [], "classes": [], "functions": [], "type": "file"}
        result["imports"] = re.findall(r'import\s+([\w.]+);', content)

        class_pattern = r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?'
        for match in re.finditer(class_pattern, content):
            result["classes"].append({
                "name": match.group(1),
                "bases": [match.group(2)] if match.group(2) else [],
                "interfaces": [i.strip() for i in match.group(3).split(",")] if match.group(3) else [],
                "line": content[:match.start()].count("\n") + 1,
            })

        return result

    def _parse_go(self, content: str, path: str) -> Dict[str, Any]:
        result = {"path": path, "imports": [], "exports": [], "classes": [], "functions": [], "type": "file"}
        import_blocks = re.findall(r'import\s+\((.*?)\)', content, re.DOTALL)
        for block in import_blocks:
            result["imports"].extend(re.findall(r'"([^"]+)"', block))
        result["imports"].extend(re.findall(r'import\s+"([^"]+)"', content))

        result["functions"] = [{"name": f} for f in re.findall(r'func\s+(\w+)', content)]
        result["classes"] = [{"name": s} for s in re.findall(r'type\s+(\w+)\s+struct', content)]

        return result

    def _parse_rust(self, content: str, path: str) -> Dict[str, Any]:
        result = {"path": path, "imports": [], "exports": [], "classes": [], "functions": [], "type": "file"}
        result["imports"] = re.findall(r'(?:use|extern crate)\s+([\w:]+)', content)
        result["functions"] = [{"name": f} for f in re.findall(r'fn\s+(\w+)', content)]
        result["classes"] = [{"name": s} for s in re.findall(r'struct\s+(\w+)|impl\s+(\w+)', content)]

        return result

    def _parse_csharp(self, content: str, path: str) -> Dict[str, Any]:
        result = {"path": path, "imports": [], "exports": [], "classes": [], "functions": [], "type": "file"}
        result["imports"] = re.findall(r'using\s+([\w.]+);', content)
        result["classes"] = [{"name": c} for c in re.findall(r'class\s+(\w+)', content)]
        return result

    def _parse_php(self, content: str, path: str) -> Dict[str, Any]:
        result = {"path": path, "imports": [], "exports": [], "classes": [], "functions": [], "type": "file"}
        result["imports"] = re.findall(r'(?:use|require|include)\s+([\w\\/]+)', content)
        result["classes"] = [{"name": c} for c in re.findall(r'class\s+(\w+)', content)]
        result["functions"] = [{"name": f} for f in re.findall(r'function\s+(\w+)', content)]
        return result

    def _get_name(self, node) -> str:
        if hasattr(node, 'id'):
            return node.id
        elif hasattr(node, 'attr'):
            return node.attr
        elif hasattr(node, 's'):
            return node.s
        return str(node)
