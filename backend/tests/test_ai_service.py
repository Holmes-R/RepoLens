import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from fastapi.testclient import TestClient

from backend.app.models.repository import AnalysisResult, Repository
from backend.app.services.ollama_service import AIService, AIServiceError


class ConfigurationTests(unittest.TestCase):
    def test_backend_env_loads_even_when_launched_from_another_directory(self):
        source = Path(__file__).resolve().parents[1] / "app" / "config.py"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_path = root / "backend" / "app" / "config.py"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            (root / "backend" / ".env").write_text("OLLAMA_MODEL=configured-model:latest\n", encoding="utf-8")
            env = dict(os.environ)
            env.pop("OLLAMA_MODEL", None)
            env.pop("PYTHON_DOTENV_DISABLED", None)
            code = f"import runpy; loaded = runpy.run_path({str(config_path)!r}); print(loaded['config'].OLLAMA_MODEL)"
            result = subprocess.run([sys.executable, "-c", code], cwd=root, env=env, capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.strip(), "configured-model:latest")


class OllamaServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = AIService(ollama_model="test-model:latest")
        self.messages = [{"role": "user", "content": "Hello"}]

    def response(self, status=200, payload=None):
        response = Mock(status_code=status, text="provider error")
        response.json.return_value = payload
        return response

    def test_missing_model_reports_how_to_fix_configuration(self):
        response = self.response(404, {"error": "model 'test-model:latest' not found"})
        with patch("backend.app.services.ollama_service.requests.post", return_value=response):
            with self.assertRaises(AIServiceError) as raised:
                self.service.chat(self.messages)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("test-model:latest", str(raised.exception))
        self.assertIn("OLLAMA_MODEL", str(raised.exception))
        self.assertIn("ollama list", str(raised.exception))

    def test_timeout_and_connection_failure_have_distinct_errors(self):
        for error, status in [(requests.Timeout(), 504), (requests.ConnectionError(), 503)]:
            with self.subTest(error=type(error).__name__):
                with patch("backend.app.services.ollama_service.requests.post", side_effect=error):
                    with self.assertRaises(AIServiceError) as raised:
                        self.service.chat(self.messages)
                self.assertEqual(raised.exception.status_code, status)

    def test_model_runtime_error_is_preserved(self):
        response = self.response(500, {"error": "model requires more system memory"})
        with patch("backend.app.services.ollama_service.requests.post", return_value=response):
            with self.assertRaisesRegex(AIServiceError, "requires more system memory"):
                self.service.chat(self.messages)

    def test_invalid_json_is_reported(self):
        response = self.response()
        response.json.side_effect = ValueError("invalid json")
        with patch("backend.app.services.ollama_service.requests.post", return_value=response):
            with self.assertRaisesRegex(AIServiceError, "invalid JSON"):
                self.service.chat(self.messages)

    def test_empty_and_malformed_success_responses_are_errors(self):
        for payload in [{"message": {"content": ""}}, {"message": None}, {"message": {"content": "   "}}, [], {"error": "generation failed"}]:
            with self.subTest(payload=payload):
                with patch("backend.app.services.ollama_service.requests.post", return_value=self.response(payload=payload)):
                    with self.assertRaises(AIServiceError):
                        self.service.chat(self.messages)

    def test_successful_chat_returns_content(self):
        response = self.response(payload={"message": {"content": "Hello there!"}})
        with patch("backend.app.services.ollama_service.requests.post", return_value=response) as post:
            self.assertEqual(self.service.chat(self.messages), "Hello there!")
        self.assertEqual(post.call_args.kwargs["json"]["model"], "test-model:latest")
        self.assertFalse(post.call_args.kwargs["json"]["stream"])

    def test_thinking_can_be_disabled_or_left_to_the_model_default(self):
        for setting in [False, True, None]:
            with self.subTest(setting=setting):
                service = AIService(ollama_think=setting)
                response = self.response(payload={"message": {"content": "Hello!"}})
                with patch("backend.app.services.ollama_service.requests.post", return_value=response) as post:
                    service.chat(self.messages)
                payload = post.call_args.kwargs["json"]
                if setting is None:
                    self.assertNotIn("think", payload)
                else:
                    self.assertIs(payload["think"], setting)


class ChatErrorTests(unittest.TestCase):
    def setUp(self):
        from backend.app.main import app
        from backend.app.api.routes.analyze import analysis_cache
        self.client = TestClient(app)
        self.result = AnalysisResult(repository=Repository(url="https://github.com/owner/project", name="project", full_name="owner/project", status="completed"))
        analysis_cache[self.result.repository.id] = self.result
        self.addCleanup(analysis_cache.pop, self.result.repository.id, None)

    def test_chat_returns_provider_error_to_the_user(self):
        with patch("backend.app.api.routes.chat.ai_service.is_available", return_value=True), patch("backend.app.api.routes.chat.ai_service.chat", side_effect=AIServiceError("Model is not installed", 503)):
            response = self.client.post("/api/chat/", json={"analysis_id": self.result.repository.id, "message": "Hello"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Model is not installed")

    def test_diagnostic_endpoint_does_not_claim_a_failed_request_succeeded(self):
        with patch("backend.app.api.routes.chat.ai_service.is_available", return_value=True), patch("backend.app.api.routes.chat.ai_service.test_chat", side_effect=AIServiceError("Model is not installed", 503)):
            response = self.client.get("/api/chat/test")
        self.assertEqual(response.json()["status"], "error")
        self.assertEqual(response.json()["message"], "Model is not installed")

    def test_diagnostic_endpoint_marks_cloud_errors_as_errors(self):
        with patch("backend.app.api.routes.chat.ai_service.is_available", return_value=True), patch("backend.app.api.routes.chat.ai_service.test_chat", return_value="Groq API error (429): rate limited"):
            response = self.client.get("/api/chat/test")
        self.assertEqual(response.json()["status"], "error")

    def test_diagnostic_endpoint_reports_the_selected_gemini_model(self):
        service = AIService(provider="gemini", gemini_model="configured-gemini-model")
        with patch("backend.app.api.routes.chat.ai_service", service), patch.object(service, "is_available", return_value=True), patch.object(service, "test_chat", return_value="Hello there!"):
            response = self.client.get("/api/chat/test")
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["model"], "configured-gemini-model")


if __name__ == "__main__":
    unittest.main()
