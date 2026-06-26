import os
from typing import Dict, Any, Optional
from datetime import datetime

from backend.app.core.language_detector import LanguageDetector
from backend.app.core.framework_detector import FrameworkDetector
from backend.app.core.dependency_analyzer import DependencyAnalyzer
from backend.app.core.ast_parser import ASTParser
from backend.app.core.call_graph import CallGraphBuilder
from backend.app.core.architecture_detector import ArchitectureDetector
from backend.app.core.complexity_analyzer import ComplexityAnalyzer
from backend.app.core.health_score import HealthScoreCalculator
from backend.app.services.git_service import GitService
from backend.app.services.diagram_service import DiagramService
from backend.app.services.llm_service import LLMService
from backend.app.services.vector_service import VectorService
from backend.app.models.repository import (
    Repository, LanguageStats, Framework, Dependency, ModuleInfo,
    ArchitectureInfo, ComplexityMetrics, AnalysisResult
)


class RepositoryAnalyzer:
    def __init__(self, config):
        self.config = config
        self.git_service = GitService(config.REPO_STORAGE_PATH, config.GITHUB_TOKEN)
        self.diagram_service = DiagramService()
        self.llm_service = LLMService(config.OPENAI_API_KEY, config.OPENAI_MODEL)
        self.vector_service = VectorService(config.VECTOR_DB_PATH)

    def analyze(self, repo_url: str, branch: str = "main", deep: bool = False) -> AnalysisResult:
        # Clone repository
        local_path = self.git_service.clone_repository(repo_url, branch)
        repo_name = self.git_service._extract_repo_name(repo_url)

        repo = Repository(
            url=repo_url,
            name=repo_name,
            full_name=repo_name,
            default_branch=branch,
            local_path=local_path,
            status="analyzing",
        )

        try:
            # Run all analyzers
            language_detector = LanguageDetector(local_path)
            framework_detector = FrameworkDetector(local_path)
            dependency_analyzer = DependencyAnalyzer(local_path)
            ast_parser = ASTParser(local_path)
            call_graph_builder = CallGraphBuilder(local_path)
            architecture_detector = ArchitectureDetector(local_path)
            complexity_analyzer = ComplexityAnalyzer(local_path)

            # Gather language stats
            raw_lang_stats = language_detector.detect_languages()
            lang_stats = [LanguageStats(**raw_lang_stats[k]) for k in raw_lang_stats]

            # Gather frameworks
            raw_frameworks = framework_detector.detect()
            frameworks = [Framework(**fw) for fw in raw_frameworks]

            # Gather dependencies
            raw_deps = dependency_analyzer.analyze()
            dependencies = [Dependency(**d) for d in raw_deps]

            # Parse modules
            all_files = language_detector.get_all_files()
            modules = []
            for rel_path, info in all_files.items():
                ext = os.path.splitext(rel_path)[1].lower()
                if ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".cs", ".php", ".rb"):
                    full_path = os.path.join(local_path, rel_path)
                    parsed = ast_parser.parse_file(full_path)
                    modules.append(ModuleInfo(
                        name=os.path.basename(rel_path),
                        path=rel_path,
                        type="file",
                        language=info["language"],
                        imports=parsed["imports"],
                        exports=parsed["exports"],
                        classes=[c["name"] for c in parsed["classes"]],
                        functions=[f["name"] for f in parsed["functions"]],
                    ))

            # Build call graph
            call_graph = call_graph_builder.build()

            # Detect architecture
            arch_data = architecture_detector.detect()
            architecture = None
            if arch_data:
                architecture = ArchitectureInfo(
                    pattern=arch_data["pattern"],
                    confidence=arch_data["confidence"],
                    description=arch_data["description"],
                    layers=arch_data.get("layers", []),
                    scores=arch_data.get("scores", {}),
                    evidence=arch_data.get("evidence", []),
                )

            # Complexity metrics
            complexity_data = complexity_analyzer.analyze()
            complexity = ComplexityMetrics(**complexity_data)

            # Contributor info
            contributors = self.git_service.get_contributors(local_path)

            # Read README
            readme_content = None
            for readme_name in ["README.md", "README.rst", "README.txt", "README"]:
                readme_path = os.path.join(local_path, readme_name)
                if os.path.exists(readme_path):
                    try:
                        with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                            readme_content = f.read(5000)
                    except Exception:
                        pass
                    break

            # Build analysis data for health score
            all_files_list = list(all_files.keys())
            analysis_data = {
                "dependencies": [d.model_dump() for d in dependencies],
                "frameworks": [f.model_dump() for f in frameworks],
                "architecture": arch_data or {},
                "complexity": complexity_data,
                "modules": [m.model_dump() for m in modules],
                "contributors": contributors,
                "readme_content": readme_content,
                "analyzed_files": all_files_list,
            }

            # Calculate health score
            health_calc = HealthScoreCalculator(analysis_data)
            health_scores = health_calc.calculate()

            # Generate diagrams
            diagram_data = {
                "architecture": arch_data or {},
                "language_stats": [ls.model_dump() for ls in lang_stats],
                "dependencies": [d.model_dump() for d in dependencies],
                "modules": [m.model_dump() for m in modules],
            }

            diagrams = {
                "architecture": self.diagram_service.generate_mermaid_diagram("architecture", diagram_data),
                "dependency": self.diagram_service.generate_mermaid_diagram("dependency", diagram_data),
                "sequence": self.diagram_service.generate_mermaid_diagram("sequence", diagram_data),
                "class": self.diagram_service.generate_mermaid_diagram("class", diagram_data),
                "layer": self.diagram_service.generate_mermaid_diagram("layer", diagram_data),
            }

            # Build result
            result = AnalysisResult(
                repository=repo,
                language_stats=lang_stats,
                frameworks=frameworks,
                dependencies=dependencies,
                modules=modules,
                architecture=architecture,
                call_graph=call_graph,
                complexity=complexity,
                health_score=health_scores.get("overall"),
                contributors=contributors,
                readme_content=readme_content,
                diagrams=diagrams,
            )

            repo.status = "completed"
            repo.updated_at = datetime.now()

            # Index repository into vector store before cleanup
            try:
                self.vector_service.index_repository(local_path, repo.id)
            except Exception:
                pass

            return result

        except Exception as e:
            repo.status = "failed"
            repo.error_message = str(e)
            return AnalysisResult(repository=repo)

        finally:
            if not deep:
                self.git_service.cleanup(local_path)
