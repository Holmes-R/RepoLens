import os
import json
import re
from typing import List, Dict, Any


class DependencyAnalyzer:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def analyze(self) -> List[Dict[str, Any]]:
        dependencies = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "venv" and d != "__pycache__"]
            for file in files:
                file_path = os.path.join(root, file)
                if file == "package.json":
                    deps = self._parse_package_json(file_path)
                    for d in deps:
                        d["source_file"] = os.path.relpath(file_path, self.repo_path)
                    dependencies.extend(deps)
                elif file == "requirements.txt":
                    deps = self._parse_requirements_txt(file_path)
                    for d in deps:
                        d["source_file"] = os.path.relpath(file_path, self.repo_path)
                    dependencies.extend(deps)
                elif file == "Cargo.toml":
                    deps = self._parse_cargo_toml(file_path)
                    for d in deps:
                        d["source_file"] = os.path.relpath(file_path, self.repo_path)
                    dependencies.extend(deps)
                elif file == "go.mod":
                    deps = self._parse_go_mod(file_path)
                    for d in deps:
                        d["source_file"] = os.path.relpath(file_path, self.repo_path)
                    dependencies.extend(deps)
                elif file == "Gemfile":
                    deps = self._parse_gemfile(file_path)
                    for d in deps:
                        d["source_file"] = os.path.relpath(file_path, self.repo_path)
                    dependencies.extend(deps)
                elif file == "pubspec.yaml":
                    deps = self._parse_pubspec(file_path)
                    for d in deps:
                        d["source_file"] = os.path.relpath(file_path, self.repo_path)
                    dependencies.extend(deps)
                elif file == "pom.xml":
                    deps = self._parse_pom_xml(file_path)
                    for d in deps:
                        d["source_file"] = os.path.relpath(file_path, self.repo_path)
                    dependencies.extend(deps)

        return dependencies

    def _parse_package_json(self, file_path: str) -> List[Dict[str, str]]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
                if dep_type in data:
                    for name, version in data[dep_type].items():
                        deps.append({
                            "name": name,
                            "version": version.lstrip("^~>=<"),
                            "type": "external",
                            "source": "npm",
                            "category": dep_type.replace("Dependencies", ""),
                        })
        except Exception:
            pass
        return deps

    def _parse_requirements_txt(self, file_path: str) -> List[Dict[str, str]]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-"):
                        parts = re.split(r'===|==|~=|!=|<=|>=|<|>', line, maxsplit=1)
                        name = parts[0].strip()
                        version = parts[1].strip() if len(parts) > 1 else "*"
                        deps.append({
                            "name": name,
                            "version": version,
                            "type": "external",
                            "source": "pypi",
                        })
        except Exception:
            pass
        return deps

    def _parse_cargo_toml(self, file_path: str) -> List[Dict[str, str]]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            in_deps = False
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("[dependencies"):
                    in_deps = True
                elif line.startswith("[") and in_deps:
                    in_deps = False
                elif in_deps and "=" in line:
                    parts = line.split("=", 1)
                    name = parts[0].strip()
                    version = parts[1].strip().strip('"').strip("'")
                    deps.append({
                        "name": name,
                        "version": version,
                        "type": "external",
                        "source": "cargo",
                    })
        except Exception:
            pass
        return deps

    def _parse_go_mod(self, file_path: str) -> List[Dict[str, str]]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                in_require_block = False
                for line in f:
                    line = line.split("//", 1)[0].strip()
                    if line == "require (":
                        in_require_block = True
                        continue
                    if line == ")":
                        in_require_block = False
                        continue
                    if line.startswith("require ") or in_require_block:
                        parts = line.removeprefix("require ").split()
                        if len(parts) >= 2:
                            deps.append({
                                "name": parts[0],
                                "version": parts[1],
                                "type": "external",
                                "source": "go",
                            })
        except Exception:
            pass
        return deps

    def _parse_gemfile(self, file_path: str) -> List[Dict[str, str]]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    match = re.match(r"gem\s+['\"]([\w-]+)['\"]", line)
                    if match:
                        deps.append({
                            "name": match.group(1),
                            "version": "*",
                            "type": "external",
                            "source": "rubygems",
                        })
        except Exception:
            pass
        return deps

    def _parse_pubspec(self, file_path: str) -> List[Dict[str, str]]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                in_deps = False
                dependency_indent = None
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    indent = len(line) - len(line.lstrip())
                    if indent == 0:
                        in_deps = stripped in ("dependencies:", "dev_dependencies:")
                        dependency_indent = None
                        continue
                    if in_deps and ":" in stripped:
                        if dependency_indent is None:
                            dependency_indent = indent
                        if indent != dependency_indent:
                            continue
                        parts = stripped.split(":", 1)
                        name = parts[0].strip()
                        version = parts[1].split(" #", 1)[0].strip().strip("\"'") or "*"
                        deps.append({
                            "name": name,
                            "version": version,
                            "type": "external",
                            "source": "pub",
                        })
        except Exception:
            pass
        return deps

    def _parse_pom_xml(self, file_path: str) -> List[Dict[str, str]]:
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            artifacts = re.findall(r'<dependency>.*?<groupId>(.*?)</groupId>.*?<artifactId>(.*?)</artifactId>.*?<version>(.*?)</version>.*?</dependency>', content, re.DOTALL)
            for group, artifact, version in artifacts:
                deps.append({
                    "name": f"{group}.{artifact}",
                    "version": version,
                    "type": "external",
                    "source": "maven",
                })
        except Exception:
            pass
        return deps
