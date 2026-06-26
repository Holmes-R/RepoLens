import os
import json
from typing import List, Dict, Any


FRAMEWORK_PATTERNS = {
    "react": {
        "files": [".babelrc", "tsconfig.json"],
        "deps": ["react", "react-dom", "next", "gatsby", "react-scripts"],
        "category": "frontend",
    },
    "vue": {
        "files": ["vue.config.js"],
        "deps": ["vue", "vue-router", "vuex", "nuxt"],
        "category": "frontend",
    },
    "angular": {
        "files": ["angular.json", "tsconfig.app.json"],
        "deps": ["@angular/core", "@angular/common"],
        "category": "frontend",
    },
    "django": {
        "files": ["manage.py", "urls.py", "wsgi.py"],
        "deps": ["django"],
        "category": "backend",
    },
    "flask": {
        "deps": ["flask"],
        "category": "backend",
    },
    "fastapi": {
        "deps": ["fastapi"],
        "category": "backend",
    },
    "express": {
        "deps": ["express"],
        "category": "backend",
    },
    "spring": {
        "files": ["pom.xml", "build.gradle"],
        "deps": ["spring-boot", "spring-core", "spring-web"],
        "category": "backend",
    },
    "rails": {
        "files": ["Gemfile", "Rakefile", "config/routes.rb"],
        "deps": ["rails", "activerecord"],
        "category": "backend",
    },
    "tensorflow": {
        "deps": ["tensorflow", "tf-nightly"],
        "category": "ai",
    },
    "pytorch": {
        "deps": ["torch", "pytorch"],
        "category": "ai",
    },
    "jest": {
        "deps": ["jest", "ts-jest"],
        "category": "testing",
    },
    "junit": {
        "deps": ["junit", "jupiter"],
        "category": "testing",
    },
    "pytest": {
        "deps": ["pytest"],
        "category": "testing",
    },
    "docker": {
        "files": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        "category": "devops",
    },
    "kubernetes": {
        "files": ["deployment.yaml", "service.yaml", "kustomization.yaml"],
        "category": "devops",
    },
}


class FrameworkDetector:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def detect(self) -> List[Dict[str, Any]]:
        frameworks = []
        found_categories = set()

        # Check for dependency files
        package_files = self._find_package_files()

        for name, info in FRAMEWORK_PATTERNS.items():
            detected = False

            # Check file existence
            if "files" in info:
                for f in info["files"]:
                    if os.path.exists(os.path.join(self.repo_path, f)):
                        detected = True
                        break

            # Check dependencies
            if not detected and "deps" in info:
                for dep in info["deps"]:
                    if self._check_dependency_in_files(dep, package_files):
                        detected = True
                        break

            if detected and info.get("category") not in found_categories:
                found_categories.add(info.get("category"))

            if detected:
                version = self._extract_version(name, package_files)
                frameworks.append({
                    "name": name,
                    "version": version,
                    "category": info.get("category", "other"),
                })

        return frameworks

    def _find_package_files(self) -> List[tuple]:
        files = []
        for root, dirs, filenames in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "venv"]
            for f in filenames:
                if f in ["package.json", "requirements.txt", "Cargo.toml", "go.mod", "Gemfile", "Pipfile"]:
                    files.append((os.path.join(root, f), f))
        return files

    def _check_dependency_in_files(self, dep: str, package_files: List[tuple]) -> bool:
        for file_path, fname in package_files:
            try:
                if fname == "package.json":
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                        all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                        if dep in all_deps or any(dep in k for k in all_deps):
                            return True
                elif fname == "requirements.txt":
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().lower()
                        if dep.lower() in content:
                            return True
            except Exception:
                continue
        return False

    def _extract_version(self, name: str, package_files: List[tuple]) -> str:
        patterns = FRAMEWORK_PATTERNS.get(name, {})
        deps = patterns.get("deps", [])
        for file_path, fname in package_files:
            try:
                if fname == "package.json" and deps:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                        all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                        for dep in deps:
                            if dep in all_deps:
                                return all_deps[dep].lstrip("^~>=<")
                elif fname == "requirements.txt" and deps:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            for dep in deps:
                                if dep in line.lower() and "==" in line:
                                    return line.split("==")[1].strip()
            except Exception:
                continue
        return None
