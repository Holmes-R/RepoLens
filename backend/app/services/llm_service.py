import os
import json
from typing import List, Dict, Any, Optional


class LLMService:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    def generate_documentation(self, context: Dict[str, Any]) -> str:
        """Generate documentation using available context (LLM or template-based)."""
        repo_name = context.get("repository", {}).get("name", "Unknown")
        language_stats = context.get("language_stats", [])
        frameworks = context.get("frameworks", [])
        architecture = context.get("architecture", {})
        deps = context.get("dependencies", [])

        primary_lang = max(language_stats, key=lambda x: x["percentage"])["language"] if language_stats else "Unknown"
        framework_names = [f["name"] for f in frameworks]
        arch_pattern = architecture.get("pattern", "Not detected")

        docs = f"""# {repo_name} - Repository Analysis

## Overview
This repository is primarily written in **{primary_lang}**.
Detected frameworks: {', '.join(framework_names) if framework_names else 'None detected'}.
Architecture pattern: **{arch_pattern}**.

## Language Breakdown
"""
        for lang in sorted(language_stats, key=lambda x: x["percentage"], reverse=True):
            docs += f"- {lang['language']}: {lang['percentage']}% ({lang['files']} files, {lang['lines']} lines)\n"

        if architecture:
            docs += f"\n## Architecture\n"
            docs += f"**Pattern**: {arch_pattern}\n"
            docs += f"**Description**: {architecture.get('description', '')}\n"
            if architecture.get("layers"):
                docs += "\n### Layers\n"
                for layer in architecture["layers"]:
                    docs += f"- {layer}\n"

        docs += f"\n## Dependencies ({len(deps)} total)\n"
        source_groups = {}
        for d in deps:
            source = d.get("source", "unknown")
            if source not in source_groups:
                source_groups[source] = []
            source_groups[source].append(d)
        for source, sdeps in source_groups.items():
            docs += f"\n### {source.upper()}\n"
            for d in sdeps[:10]:
                docs += f"- {d['name']} ({d['version']})\n"
            if len(sdeps) > 10:
                docs += f"- ... and {len(sdeps) - 10} more\n"

        complexity = context.get("complexity", {})
        if complexity:
            docs += f"\n## Complexity Metrics\n"
            docs += f"- Total Files: {complexity.get('total_files', 0)}\n"
            docs += f"- Total Lines: {complexity.get('total_lines', 0)}\n"
            docs += f"- Total Functions: {complexity.get('total_functions', 0)}\n"
            docs += f"- Total Classes: {complexity.get('total_classes', 0)}\n"
            docs += f"- Average Function Length: {complexity.get('avg_function_length', 0)} lines\n"
            docs += f"- Cyclomatic Complexity: {complexity.get('avg_complexity', 0)}\n"

        return docs

    def answer_question(self, question: str, context: List[Dict[str, Any]], repo_info: Dict[str, Any]) -> str:
        """Generate answer using retrieved context."""
        files_context = "\n\n".join([
            f"File: {r['file']}\n```\n{r['text'][:500]}```"
            for r in context[:3]
        ])

        repo_name = repo_info.get("name", "Unknown")
        repo_desc = repo_info.get("description", "A software repository")

        answer = f"""Based on analysis of **{repo_name}** ({repo_desc}):

**Relevant files found:**
"""
        for r in context[:5]:
            answer += f"- `{r['file']}` (relevance: {r.get('score', 0)})\n"

        answer += f"""

**Analysis:**
The repository `{repo_name}` contains code primarily using the patterns found in the above files. Based on the codebase structure, here is relevant information regarding your question about "{question}":

"""
        # Generate specific response based on question type
        q_lower = question.lower()
        if any(kw in q_lower for kw in ["architecture", "structure", "pattern", "design"]):
            arch = repo_info.get("architecture", {})
            answer += f"The repository follows a **{arch.get('pattern', 'custom')}** architecture pattern. "
            answer += arch.get("description", "")
        elif any(kw in q_lower for kw in ["dependency", "package", "library", "module"]):
            deps = repo_info.get("dependencies", [])
            answer += f"The project uses **{len(deps)}** external dependencies. "
            answer += f"The primary package manager is determined by the project's language and framework."
        elif any(kw in q_lower for kw in ["function", "class", "method", "code"]):
            complexity = repo_info.get("complexity", {})
            answer += f"The codebase contains **{complexity.get('total_functions', 0)}** functions and **{complexity.get('total_classes', 0)}** classes across **{complexity.get('total_files', 0)}** files. "
        elif any(kw in q_lower for kw in ["test", "testing", "coverage"]):
            frameworks = repo_info.get("frameworks", [])
            test_fws = [f["name"] for f in frameworks if f.get("category") == "testing"]
            if test_fws:
                answer += f"Testing frameworks detected: {', '.join(test_fws)}. "
            else:
                answer += "No testing frameworks detected in the project. "
        elif any(kw in q_lower for kw in ["database", "db", "sql", "orm"]):
            frameworks = repo_info.get("frameworks", [])
            db_fws = [f["name"] for f in frameworks if f.get("category") == "database"]
            if db_fws:
                answer += f"Database technologies detected: {', '.join(db_fws)}. "
            else:
                answer += "The codebase structure was analyzed for database patterns. "
        elif any(kw in q_lower for kw in ["security", "vulnerability", "auth", "jwt", "attack"]):
            answer += "Security analysis performed includes dependency checking, code pattern analysis, and configuration review. "
        elif any(kw in q_lower for kw in ["deploy", "docker", "ci/cd", "pipeline", "devops"]):
            frameworks = repo_info.get("frameworks", [])
            devops_fws = [f["name"] for f in frameworks if f.get("category") == "devops"]
            if devops_fws:
                answer += f"DevOps tools detected: {', '.join(devops_fws)}. "
            else:
                answer += "No specific CI/CD or deployment configuration detected. "
        else:
            answer += f"The repository is a **{repo_desc}** project. For more specific information, please ask about architecture, dependencies, testing, security, or deployment."

        answer += f"\n\nThe relevant files listed above contain the specific code related to your query."
        return answer

    def generate_readme(self, repo_path: str, analysis: Dict[str, Any]) -> str:
        """Generate a comprehensive README based on analysis."""
        repo_name = analysis.get("repository", {}).get("name", "Project")
        primary_lang = ""
        if analysis.get("language_stats"):
            primary_lang = max(analysis["language_stats"], key=lambda x: x["percentage"])["language"]

        readme = f"""# {repo_name}

## 📋 Overview
{analysis.get('repository', {}).get('description', 'A software project analyzed by RepoLens AI.')}

## 🛠 Tech Stack
- **Primary Language**: {primary_lang or 'Not detected'}
"""
        if analysis.get("frameworks"):
            readme += "- **Frameworks**: " + ", ".join([f["name"] for f in analysis["frameworks"]]) + "\n"

        if analysis.get("architecture"):
            readme += f"\n## 🏗 Architecture\n"
            readme += f"**Pattern**: {analysis['architecture']['pattern']}\n"
            readme += f"**Description**: {analysis['architecture']['description']}\n"

        if analysis.get("complexity"):
            c = analysis["complexity"]
            readme += f"""
## 📊 Code Statistics
| Metric | Value |
|--------|-------|
| Total Files | {c['total_files']} |
| Total Lines | {c['total_lines']} |
| Total Functions | {c['total_functions']} |
| Total Classes | {c['total_classes']} |
| Avg Function Length | {c['avg_function_length']} lines |
| Avg Complexity | {c['avg_complexity']} |
"""

        if analysis.get("dependencies"):
            readme += f"\n## 📦 Dependencies ({len(analysis['dependencies'])} total)\n"
            for d in analysis["dependencies"][:15]:
                readme += f"- {d['name']} ({d['version']})\n"

        if analysis.get("health_score") is not None:
            readme += f"\n## 💚 Health Score: {analysis['health_score']}/100\n"

        readme += f"""
---
*Generated by [RepoLens AI](https://github.com/yourusername/repo-lens) on automatic analysis*
"""
        return readme
