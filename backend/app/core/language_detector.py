import os
from typing import Dict, List, Tuple


LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C",
    ".hpp": "C++",
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".swift": "Swift",
    ".dart": "Dart",
    ".scala": "Scala",
    ".lua": "Lua",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".r": "R",
    ".m": "Objective-C",
    ".mm": "Objective-C",
    ".pl": "Perl",
    ".pm": "Perl",
    ".hs": "Haskell",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".clj": "Clojure",
    ".cljs": "Clojure",
    ".sql": "SQL",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".xml": "XML",
    ".toml": "TOML",
    ".md": "Markdown",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".less": "LESS",
}


LANGUAGE_FILE_PATTERNS = {
    "Python": ["requirements.txt", "setup.py", "setup.cfg", "pyproject.toml", "Pipfile", "tox.ini"],
    "JavaScript": ["package.json", "package-lock.json", "webpack.config.js", "rollup.config.js"],
    "TypeScript": ["tsconfig.json", "tslint.json"],
    "Java": ["pom.xml", "build.gradle", "gradlew"],
    "Go": ["go.mod", "go.sum"],
    "Rust": ["Cargo.toml", "Cargo.lock"],
    "Ruby": ["Gemfile", "Gemfile.lock", "Rakefile"],
    "PHP": ["composer.json", "composer.lock"],
    "Swift": ["Package.swift"],
    "Dart": ["pubspec.yaml", "pubspec.lock"],
}


class LanguageDetector:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self._file_cache: Dict[str, str] = {}

    def detect_languages(self) -> Dict[str, Dict]:
        self._scan_files()
        total_lines = sum(info["lines"] for info in self._file_cache.values())

        language_stats = {}
        for path, info in self._file_cache.items():
            lang = info["language"]
            if lang and info["lines"] > 0:
                if lang not in language_stats:
                    language_stats[lang] = {"files": 0, "lines": 0}
                language_stats[lang]["files"] += 1
                language_stats[lang]["lines"] += info["lines"]

        # Calculate percentages
        result = {}
        for lang, stats in language_stats.items():
            result[lang] = {
                "language": lang,
                "percentage": round((stats["lines"] / total_lines * 100) if total_lines > 0 else 0, 2),
                "files": stats["files"],
                "lines": stats["lines"],
            }

        return result

    def detect_primary_language(self) -> str:
        stats = self.detect_languages()
        if not stats:
            return "Unknown"
        return max(stats.items(), key=lambda x: x[1]["percentage"])[0]

    def _scan_files(self):
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "venv" and d != "__pycache__"]
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.repo_path)
                try:
                    ext = os.path.splitext(file)[1].lower()
                    lines = self._count_lines(file_path)
                    language = LANGUAGE_EXTENSIONS.get(ext)

                    # Check file name patterns
                    if not language:
                        for lang, patterns in LANGUAGE_FILE_PATTERNS.items():
                            if file in patterns:
                                language = lang
                                break

                    self._file_cache[rel_path] = {
                        "language": language or "Unknown",
                        "lines": lines,
                        "path": rel_path,
                    }
                except Exception:
                    continue

    def _count_lines(self, file_path: str) -> int:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def get_all_files(self) -> Dict[str, Dict]:
        if not self._file_cache:
            self._scan_files()
        return self._file_cache
