import os
import asyncio
import threading
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ["PYTHON_DOTENV_DISABLED"] = "1"

from fastapi.testclient import TestClient
from git import Repo
from httpx import ASGITransport, AsyncClient

from backend.app.core.analyzer import RepositoryAnalyzer
from backend.app.core.dependency_analyzer import DependencyAnalyzer
from backend.app.core.language_detector import LanguageDetector
from backend.app.models.analysis import AnalyzeRequest
from backend.app.models.repository import AnalysisResult, Repository
from backend.app.services.git_service import GitService


class DependencyRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def analyze_file(self, name, content):
        (self.root / name).write_text(content, encoding="utf-8")
        return DependencyAnalyzer(str(self.root)).analyze()

    def test_python_pinned_versions_do_not_include_equals(self):
        deps = self.analyze_file("requirements.txt", "fastapi==0.115.0\nrequests>=2.32.0\nuvicorn[standard]~=0.30.0\n")
        self.assertEqual([d["version"] for d in deps], ["0.115.0", "2.32.0", "0.30.0"])

    def test_go_require_blocks_and_single_require(self):
        deps = self.analyze_file("go.mod", "module example.com/app\nrequire (\n example.com/one v1.2.3\n example.com/two v2.0.0 // indirect\n)\nrequire example.com/three v3.0.0\n")
        self.assertEqual([(d["name"], d["version"]) for d in deps], [
            ("example.com/one", "v1.2.3"), ("example.com/two", "v2.0.0"), ("example.com/three", "v3.0.0")])

    def test_pubspec_excludes_nested_options_and_unrelated_sections(self):
        deps = self.analyze_file("pubspec.yaml", "name: app\ndependencies:\n  flutter:\n    sdk: flutter\n  http: ^1.2.0\n  local_package:\n    path: ../local\ndev_dependencies:\n  flutter_test:\n    sdk: flutter\nflutter:\n  uses-material-design: true\n")
        self.assertEqual([d["name"] for d in deps], ["flutter", "http", "local_package", "flutter_test"])
        self.assertEqual(deps[0]["version"], "*")

    def test_language_percentages_exclude_unknown_files(self):
        (self.root / "main.py").write_text("print('hello')\n", encoding="utf-8")
        (self.root / "unknown.xyz").write_text("unknown\n" * 9, encoding="utf-8")
        stats = LanguageDetector(str(self.root)).detect_languages()
        self.assertEqual(stats["Python"]["percentage"], 100)


class RepositoryRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.service = GitService(str(self.root / "clones"))

    def test_repository_names_keep_trailing_git_characters(self):
        for name in ["git", "digit", "widget", "project.git"]:
            expected = name.removesuffix(".git")
            with self.subTest(name=name):
                self.assertEqual(self.service._extract_owner_repo(f"https://github.com/owner/{name}/"), ("owner", expected))

    def make_repository(self):
        source = self.root / "source"
        repo = Repo.init(source, initial_branch="develop")
        self.addCleanup(repo.close)
        (source / "main.py").write_text("def hello():\n    return 'hello'\n", encoding="utf-8")
        (source / "requirements.txt").write_text("fastapi==0.115.0\n", encoding="utf-8")
        (source / "SECURITY.md").write_text("Security policy\n", encoding="utf-8")
        (source / "test_main.py").write_text("def test_hello():\n    assert True\n", encoding="utf-8")
        repo.index.add(["main.py", "requirements.txt", "SECURITY.md", "test_main.py"])
        repo.index.commit("Initial commit")
        return source

    def test_unspecified_branch_uses_repository_default(self):
        self.assertIsNone(AnalyzeRequest(repo_url="https://github.com/owner/project").branch)
        clone = self.service.clone_repository(str(self.make_repository()))
        with Repo(clone) as repo:
            self.assertEqual(repo.active_branch.name, "develop")

    def test_explicit_missing_branch_does_not_fall_back(self):
        source = self.make_repository()
        repo = Repo(source)
        self.addCleanup(repo.close)
        repo.create_head("master")
        with self.assertRaises(Exception):
            self.service.clone_repository(str(source), "main")

    def test_clone_errors_do_not_expose_github_token(self):
        self.service.github_token = "test-secret-token"
        from git import GitCommandError
        def fail_clone(url, *args, **kwargs):
            raise GitCommandError(["git", "clone", url], 128, stderr=f"failed: {url}")
        with patch("backend.app.services.git_service.Repo.clone_from", side_effect=fail_clone):
            with self.assertRaises(Exception) as raised:
                self.service.clone_repository("https://github.com/owner/project")
        self.assertNotIn("test-secret-token", str(raised.exception))

    def test_analysis_preserves_dependency_sources_files_and_actual_branch(self):
        source = self.make_repository()
        config = SimpleNamespace(REPO_STORAGE_PATH=str(self.root / "clones"), GITHUB_TOKEN="")
        analyzer = RepositoryAnalyzer(config)
        with patch.object(analyzer.git_service, "get_github_repo_info", return_value={}), patch.object(analyzer.git_service, "get_recent_commits", return_value=[]):
            result = analyzer.analyze(str(source))
        self.assertEqual(result.repository.status, "completed", result.repository.error_message)
        self.assertEqual(result.repository.default_branch, "develop")
        self.assertEqual(result.dependencies[0].source_file, "requirements.txt")
        self.assertIn("test_main.py", result.analyzed_files)
        from backend.app.api.routes.analyze import analysis_cache
        from backend.app.main import app
        analysis_cache[result.repository.id] = result
        self.addCleanup(analysis_cache.pop, result.repository.id, None)
        response = TestClient(app).get(f"/api/health/{result.repository.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scores"]["overall"], result.health_score)


class APIRegressionTests(unittest.TestCase):
    def test_analysis_accepts_post_at_the_api_prefix(self):
        from backend.app.main import app
        from backend.app.api.routes.analyze import analysis_cache
        result = AnalysisResult(repository=Repository(url="https://github.com/owner/project", name="project", full_name="owner/project", status="completed"))
        self.addCleanup(analysis_cache.pop, result.repository.id, None)
        with patch("backend.app.api.routes.analyze.analyzer.analyze", return_value=result):
            response = TestClient(app).post("/api/analyze/", json={"repo_url": result.repository.url})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["analysis_id"], result.repository.id)

    def test_failed_analysis_returns_an_error(self):
        from backend.app.main import app
        result = AnalysisResult(repository=Repository(url="https://github.com/owner/project", name="project", full_name="owner/project", status="failed", error_message="Analysis failed"))
        with patch("backend.app.api.routes.analyze.analyzer.analyze", return_value=result):
            response = TestClient(app).post("/api/analyze/", json={"repo_url": result.repository.url})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Analysis failed")

    def test_advertised_diagram_types_match_generated_types(self):
        from backend.app.main import app
        response = TestClient(app).get("/api/diagrams/types")
        self.assertEqual({item["id"] for item in response.json()["types"]}, {"architecture", "dependency", "sequence", "directory", "layer"})


class ServerResponsivenessTests(unittest.IsolatedAsyncioTestCase):
    async def test_health_remains_responsive_during_analysis(self):
        from backend.app.main import app
        from backend.app.api.routes.analyze import analysis_cache
        started = threading.Event()
        release = threading.Event()
        result = AnalysisResult(repository=Repository(url="https://github.com/owner/project", name="project", full_name="owner/project", status="completed"))

        def slow_analysis(*args):
            started.set()
            release.wait(timeout=3)
            return result

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with patch("backend.app.api.routes.analyze.analyzer.analyze", side_effect=slow_analysis):
                task = asyncio.create_task(client.post("/api/analyze/", json={"repo_url": result.repository.url}))
                try:
                    self.assertTrue(await asyncio.to_thread(started.wait, 1))
                    health = await asyncio.wait_for(client.get("/api/health"), timeout=1)
                    self.assertEqual(health.status_code, 200)
                    self.assertFalse(task.done(), "Analysis must still be running when health responds")
                finally:
                    release.set()
                    await task
                    analysis_cache.pop(result.repository.id, None)


if __name__ == "__main__":
    unittest.main()
