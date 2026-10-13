import unittest
from unittest.mock import Mock, patch

import requests
from fastapi.testclient import TestClient

from backend.app.models.repository import AnalysisResult, Repository
from backend.app.services.ollama_service import AIService, AIServiceError


class GeminiServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = AIService(provider="gemini", gemini_api_key="unit-test-secret")
        self.messages = [
            {"role": "system", "content": "Explain this repository."},
            {"role": "user", "content": "What does it do?"},
            {"role": "assistant", "content": "It analyzes repositories."},
            {"role": "user", "content": "Explain more."},
        ]

    def response(self, status=200, payload=None):
        response = Mock(status_code=status, text="provider response")
        response.json.return_value = payload
        return response

    def answer(self, text):
        return {"candidates": [{"content": {"parts": [{"text": text}]}}]}

    def test_supported_default_and_header_auth_preserve_chat_context(self):
        with patch("backend.app.services.ollama_service.requests.post", return_value=self.response(payload=self.answer("Answer"))) as post:
            self.assertEqual(self.service.chat(self.messages), "Answer")
        self.assertEqual(post.call_args.args[0], "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent")
        self.assertNotIn("unit-test-secret", post.call_args.args[0])
        self.assertEqual(post.call_args.kwargs["headers"]["x-goog-api-key"], "unit-test-secret")
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["systemInstruction"]["parts"][0]["text"], "Explain this repository.")
        self.assertEqual([message["role"] for message in body["contents"]], ["user", "model", "user"])

    def test_full_model_resource_name_does_not_duplicate_models_prefix(self):
        self.service.gemini_model = AIService(gemini_model="models/gemini-3.8-flash").gemini_model
        with patch("backend.app.services.ollama_service.requests.post", return_value=self.response(payload=self.answer("Answer"))) as post:
            self.service.chat(self.messages)
        self.assertIn("/models/gemini-3.8-flash:generateContent", post.call_args.args[0])
        self.assertNotIn("/models/models/", post.call_args.args[0])

    def test_retired_model_error_is_actionable_and_redacts_credentials(self):
        response = self.response(404, {"error": {"message": "Model retired; key=unit-test-secret"}})
        with patch("backend.app.services.ollama_service.requests.post", return_value=response):
            with self.assertRaises(AIServiceError) as raised:
                self.service.chat(self.messages)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("GEMINI_MODEL", str(raised.exception))
        self.assertIn("restart", str(raised.exception))
        self.assertNotIn("unit-test-secret", str(raised.exception))

    def test_missing_key_fails_without_sending_a_request(self):
        self.service.gemini_api_key = ""
        with patch("backend.app.services.ollama_service.requests.post") as post:
            with self.assertRaisesRegex(AIServiceError, "GEMINI_API_KEY"):
                self.service.chat(self.messages)
        post.assert_not_called()

    def test_multiple_text_parts_are_combined_without_thought_parts(self):
        payload = {"candidates": [{"content": {"parts": [
            {"text": "internal reasoning", "thought": True},
            {"text": "First sentence. "}, {"text": "Second sentence."},
        ]}}]}
        with patch("backend.app.services.ollama_service.requests.post", return_value=self.response(payload=payload)):
            self.assertEqual(self.service.chat(self.messages), "First sentence. Second sentence.")

    def test_malformed_and_empty_answers_are_errors(self):
        for payload in [[], {}, {"candidates": []}, {"candidates": [None]}, {"candidates": [{"content": None}]}, self.answer(" ")]:
            with self.subTest(payload=payload):
                with patch("backend.app.services.ollama_service.requests.post", return_value=self.response(payload=payload)):
                    with self.assertRaises(AIServiceError):
                        self.service.chat(self.messages)

    def test_invalid_json_is_reported(self):
        response = self.response()
        response.json.side_effect = ValueError("invalid JSON")
        with patch("backend.app.services.ollama_service.requests.post", return_value=response):
            with self.assertRaisesRegex(AIServiceError, "invalid JSON"):
                self.service.chat(self.messages)

    def test_network_timeout_and_rate_limit_use_distinct_statuses(self):
        for error, status in [(requests.ConnectionError(), 503), (requests.Timeout(), 504)]:
            with self.subTest(error=type(error).__name__):
                with patch("backend.app.services.ollama_service.requests.post", side_effect=error):
                    with self.assertRaises(AIServiceError) as raised:
                        self.service.chat(self.messages)
                self.assertEqual(raised.exception.status_code, status)
        with patch("backend.app.services.ollama_service.requests.post", return_value=self.response(429, {"error": {"message": "Quota exceeded"}})):
            with self.assertRaises(AIServiceError) as raised:
                self.service.chat(self.messages)
        self.assertEqual(raised.exception.status_code, 429)


class GeminiChatRouteTests(unittest.TestCase):
    def setUp(self):
        from backend.app.main import app
        from backend.app.api.routes.analyze import analysis_cache
        self.client = TestClient(app)
        self.result = AnalysisResult(repository=Repository(url="https://github.com/owner/project", name="project", full_name="owner/project", status="completed"))
        analysis_cache[self.result.repository.id] = self.result
        self.addCleanup(analysis_cache.pop, self.result.repository.id, None)
        self.service = AIService(provider="gemini", gemini_api_key="unit-test-secret")

    def test_answer_beginning_with_provider_name_is_not_an_error(self):
        text = "Gemini can explain this repository."
        with patch("backend.app.api.routes.chat.ai_service", self.service), patch.object(self.service, "chat", return_value=text):
            response = self.client.post("/api/chat/", json={"analysis_id": self.result.repository.id, "message": "What can you do?"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], text)

    def test_diagnostic_accepts_answer_beginning_with_provider_name(self):
        with patch("backend.app.api.routes.chat.ai_service", self.service), patch.object(self.service, "chat", return_value="Gemini is ready."):
            response = self.client.get("/api/chat/test")
        self.assertEqual(response.json()["status"], "ok")

    def test_retired_model_error_reaches_the_chat_client(self):
        response = Mock(status_code=404, text="model retired")
        response.json.return_value = {"error": {"message": "Model is no longer available"}}
        with patch("backend.app.api.routes.chat.ai_service", self.service), patch("backend.app.services.ollama_service.requests.post", return_value=response):
            result = self.client.post("/api/chat/", json={"analysis_id": self.result.repository.id, "message": "Hello"})
        self.assertEqual(result.status_code, 503)
        self.assertIn("GEMINI_MODEL", result.json()["detail"])


if __name__ == "__main__":
    unittest.main()
