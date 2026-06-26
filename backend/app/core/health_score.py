from typing import Dict, Any


class HealthScoreCalculator:
    def __init__(self, analysis_data: Dict[str, Any]):
        self.data = analysis_data

    def calculate(self) -> Dict[str, Any]:
        scores = {}

        # Security score
        scores["security"] = self._calculate_security()

        # Maintainability score
        scores["maintainability"] = self._calculate_maintainability()

        # Documentation score
        scores["documentation"] = self._calculate_documentation()

        # Testing score
        scores["testing"] = self._calculate_testing()

        # Architecture score
        scores["architecture"] = self._calculate_architecture()

        # Performance score
        scores["performance"] = self._calculate_performance()

        # Code quality score
        scores["quality"] = self._calculate_quality()

        # Complexity score
        scores["complexity"] = self._calculate_complexity()

        # Dependency freshness score
        scores["dependency"] = self._calculate_dependency_freshness()

        # Activity score
        scores["activity"] = self._calculate_activity()

        # Overall score (weighted average)
        weights = {
            "security": 20,
            "maintainability": 15,
            "documentation": 10,
            "testing": 15,
            "architecture": 10,
            "performance": 5,
            "quality": 10,
            "complexity": 5,
            "dependency": 5,
            "activity": 5,
        }

        overall = sum(scores[k] * weights[k] for k in weights) / sum(weights.values())
        scores["overall"] = round(overall, 1)
        scores["details"] = self._generate_details(scores)

        return scores

    def _calculate_security(self) -> float:
        score = 70
        deps = self.data.get("dependencies", [])
        if len(deps) < 10:
            score += 10
        if self.data.get("readme_content") and "security" in self.data["readme_content"].lower():
            score += 10
        # Check for common security files
        files = self.data.get("analyzed_files", [])
        security_files = [f for f in files if any(kw in f.lower() for kw in
            [".env", "security", "auth", "jwt", "oauth", "cors", "helmet", "csrf", "xss", "sanitize", "validator"])]
        if security_files:
            score += 10
        return min(score, 100)

    def _calculate_maintainability(self) -> float:
        score = 70
        complexity = self.data.get("complexity", {})
        avg_func_len = complexity.get("avg_function_length", 0)
        if avg_func_len < 10:
            score += 15
        elif avg_func_len < 20:
            score += 10
        elif avg_func_len < 50:
            score += 5
        else:
            score -= 10
        total_files = complexity.get("total_files", 0)
        if 10 <= total_files <= 100:
            score += 10
        return min(score, 100)

    def _calculate_documentation(self) -> float:
        score = 50
        if self.data.get("readme_content"):
            score += 20
            if len(self.data["readme_content"]) > 500:
                score += 10
        files = self.data.get("analyzed_files", [])
        doc_files = [f for f in files if "doc" in f.lower() or "readme" in f.lower() or "wiki" in f.lower() or "guide" in f.lower()]
        if doc_files:
            score += 10 * min(len(doc_files), 3)
        return min(score, 100)

    def _calculate_testing(self) -> float:
        score = 50
        files = self.data.get("analyzed_files", [])
        test_files = [f for f in files if "test" in f.lower() or "spec" in f.lower() or "mock" in f.lower()]
        if test_files:
            score += 20
        frameworks = self.data.get("frameworks", [])
        test_frameworks = [f for f in frameworks if f.get("category") == "testing"]
        if test_frameworks:
            score += 20
        return min(score, 100)

    def _calculate_architecture(self) -> float:
        score = 60
        arch = self.data.get("architecture")
        if arch and arch.get("confidence", 0) > 50:
            score += 20
        if self.data.get("modules"):
            score += 10
        layers = self.data.get("architecture", {}).get("layers", [])
        if len(layers) >= 3:
            score += 10
        return min(score, 100)

    def _calculate_performance(self) -> float:
        score = 75
        files = self.data.get("analyzed_files", [])
        # Check for performance-related files/patterns
        perf_indicators = ["cache", "redis", "memcached", "index", "optimize", "lazy", "throttle", "debounce", "batch"]
        for f in files:
            if any(kw in f.lower() for kw in perf_indicators):
                score += 5
                break
        frameworks = self.data.get("frameworks", [])
        if any(f.get("category") in ("database", "cache") for f in frameworks):
            score += 5
        # Penalize very large files
        complexity = self.data.get("complexity", {})
        if complexity.get("max_complexity", 0) > 30:
            score -= 10
        return min(max(score, 0), 100)

    def _calculate_quality(self) -> float:
        score = 70
        complexity = self.data.get("complexity", {})
        if complexity.get("total_files", 0) > 0:
            funcs_per_file = complexity.get("total_functions", 0) / max(complexity.get("total_files", 1), 1)
            if 2 < funcs_per_file < 10:
                score += 10
            elif funcs_per_file > 20:
                score -= 10
        if complexity.get("avg_complexity", 0) < 3:
            score += 10
        elif complexity.get("avg_complexity", 10) > 10:
            score -= 10
        return min(max(score, 0), 100)

    def _calculate_complexity(self) -> float:
        score = 80
        complexity = self.data.get("complexity", {})
        total_lines = complexity.get("total_lines", 0)
        total_files = complexity.get("total_files", 1)
        avg_file_size = total_lines / total_files
        if avg_file_size < 100:
            score += 10
        elif avg_file_size > 500:
            score -= 15
        elif avg_file_size > 300:
            score -= 5
        if complexity.get("max_complexity", 0) > 50:
            score -= 10
        return min(max(score, 0), 100)

    def _calculate_dependency_freshness(self) -> float:
        score = 70
        deps = self.data.get("dependencies", [])
        if not deps:
            return 100
        # Check for outdated patterns
        outdated_keywords = ["legacy", "deprecated", "v0", "alpha", "beta", "dev"]
        outdated_count = sum(1 for d in deps if any(kw in d.get("name", "").lower() for kw in outdated_keywords))
        score -= outdated_count * 5
        return min(max(score, 0), 100)

    def _calculate_activity(self) -> float:
        score = 60
        contributors = self.data.get("contributors", [])
        if len(contributors) > 5:
            score += 15
        elif len(contributors) > 1:
            score += 10
        if len(contributors) > 10:
            score += 10
        return min(score, 100)

    def _generate_details(self, scores: Dict[str, float]) -> Dict[str, Any]:
        return {
            "breakdown": {
                "security": {"score": scores["security"], "max": 100, "weight": 20},
                "maintainability": {"score": scores["maintainability"], "max": 100, "weight": 15},
                "documentation": {"score": scores["documentation"], "max": 100, "weight": 10},
                "testing": {"score": scores["testing"], "max": 100, "weight": 15},
                "architecture": {"score": scores["architecture"], "max": 100, "weight": 10},
                "performance": {"score": scores["performance"], "max": 100, "weight": 5},
                "quality": {"score": scores["quality"], "max": 100, "weight": 10},
                "complexity": {"score": scores["complexity"], "max": 100, "weight": 5},
                "dependency": {"score": scores["dependency"], "max": 100, "weight": 5},
                "activity": {"score": scores["activity"], "max": 100, "weight": 5},
            },
            "recommendations": self._generate_recommendations(scores),
        }

    def _generate_recommendations(self, scores: Dict[str, float]) -> list:
        recs = []
        if scores["security"] < 70:
            recs.append("Improve security by adding authentication, input validation, and security headers")
        if scores["documentation"] < 60:
            recs.append("Add comprehensive documentation including README, API docs, and code comments")
        if scores["testing"] < 60:
            recs.append("Increase test coverage by adding unit and integration tests")
        if scores["maintainability"] < 60:
            recs.append("Refactor large functions and improve code organization")
        if scores["quality"] < 60:
            recs.append("Address code quality issues and follow consistent coding standards")
        if scores["complexity"] < 60:
            recs.append("Reduce complexity by breaking down complex functions and modules")
        if scores["dependency"] < 70:
            recs.append("Update outdated dependencies and remove unused packages")
        return recs
