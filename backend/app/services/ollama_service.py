import requests
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AIService:
    def __init__(
        self,
        provider: str = "ollama",
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5:7b",
        groq_api_key: str = "",
        groq_model: str = "llama3-70b-8192",
        gemini_api_key: str = "",
        gemini_model: str = "gemini-1.5-flash",
    ):
        self.provider = provider.lower()
        self.ollama_url = ollama_url.rstrip("/")
        self.ollama_model = ollama_model
        self.groq_api_key = groq_api_key
        self.groq_model = groq_model
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model

    def chat(self, messages: List[Dict[str, str]]) -> Optional[str]:
        if self.provider == "gemini":
            return self._chat_gemini(messages)
        if self.provider == "groq":
            return self._chat_groq(messages)
        return self._chat_ollama(messages)

    def is_available(self) -> bool:
        if self.provider == "gemini":
            return bool(self.gemini_api_key)
        if self.provider == "groq":
            return bool(self.groq_api_key)
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def test_chat(self) -> str:
        msgs = [
            {"role": "system", "content": "You are a helpful assistant. Reply with exactly one short sentence."},
            {"role": "user", "content": "Say hello in exactly 3 words."},
        ]
        result = self.chat(msgs)
        if result is None:
            return f"ERROR: provider={self.provider} returned None (check logs)"
        if result.startswith("Groq ") or result.startswith("Gemini ") or result.startswith("Cannot "):
            return result
        return result

    def _chat_ollama(self, messages: List[Dict[str, str]]) -> Optional[str]:
        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7, "top_p": 0.9},
        }
        log_msgs = [{k: v[:100] if k == "content" else v for k, v in m.items()} for m in messages[-3:]]
        logger.info("Ollama request: model=%s, messages=%d, last_msgs=%s",
                    self.ollama_model, len(messages), log_msgs)
        try:
            resp = requests.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=180,
            )
        except requests.ConnectionError:
            logger.error("Cannot connect to Ollama at %s", self.ollama_url)
            return None
        except requests.Timeout:
            logger.error("Ollama request timed out after 180s")
            return None
        except Exception as e:
            logger.error("Ollama request failed: %s", e)
            return None
        if resp.status_code != 200:
            logger.error("Ollama HTTP %d: %s", resp.status_code, resp.text[:1000])
            return None
        try:
            data = resp.json()
        except json.JSONDecodeError:
            logger.error("Ollama bad JSON: %s", resp.text[:1000])
            return None
        content = data.get("message", {}).get("content", "")
        if not content:
            logger.warning("Ollama empty response: %s", json.dumps(data)[:500])
        else:
            logger.info("Ollama response: %d chars, starts with: %s",
                        len(content), content[:150])
        return content

    def _chat_groq(self, messages: List[Dict[str, str]]) -> Optional[str]:
        log_msgs = [{k: v[:100] if k == "content" else v for k, v in m.items()} for m in messages[-3:]]
        logger.info("Groq request: model=%s, messages=%d, last_msgs=%s",
                    self.groq_model, len(messages), log_msgs)
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.groq_model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 8192,
                },
                timeout=60,
            )
        except requests.ConnectionError:
            logger.error("Cannot connect to Groq API")
            return "Cannot connect to Groq API"
        except requests.Timeout:
            logger.error("Groq request timed out after 60s")
            return "Groq request timed out"
        except Exception as e:
            logger.error("Groq request failed: %s", e)
            return f"Groq request failed: {e}"
        if resp.status_code != 200:
            logger.error("Groq HTTP %d: %s", resp.status_code, resp.text[:1000])
            return f"Groq API error ({resp.status_code}): {resp.text[:500]}"
        try:
            data = resp.json()
        except json.JSONDecodeError:
            logger.error("Groq bad JSON: %s", resp.text[:1000])
            return f"Groq bad response: {resp.text[:500]}"
        choices = data.get("choices", [])
        if not choices:
            logger.warning("Groq empty choices: %s", json.dumps(data)[:500])
            return f"Groq returned no choices: {json.dumps(data)[:300]}"
        content = choices[0].get("message", {}).get("content", "")
        if not content:
            logger.warning("Groq empty content: %s", json.dumps(data)[:500])
            return "Groq returned empty content"
        logger.info("Groq response: %d chars, starts with: %s",
                    len(content), content[:150])
        return content

    def _chat_gemini(self, messages: List[Dict[str, str]]) -> Optional[str]:
        log_msgs = [{k: v[:100] if k == "content" else v for k, v in m.items()} for m in messages[-3:]]
        logger.info("Gemini request: model=%s, messages=%d, last_msgs=%s",
                    self.gemini_model, len(messages), log_msgs)

        system_prompt = ""
        contents = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            elif m["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": m["content"]}]})
            elif m["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": m["content"]}]})

        body = {"contents": contents}
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}",
                json=body,
                timeout=60,
            )
        except requests.ConnectionError:
            logger.error("Cannot connect to Gemini API")
            return "Cannot connect to Gemini API"
        except requests.Timeout:
            logger.error("Gemini request timed out after 60s")
            return "Gemini request timed out"
        except Exception as e:
            logger.error("Gemini request failed: %s", e)
            return f"Gemini request failed: {e}"
        if resp.status_code != 200:
            logger.error("Gemini HTTP %d: %s", resp.status_code, resp.text[:1000])
            return f"Gemini API error ({resp.status_code}): {resp.text[:500]}"
        try:
            data = resp.json()
        except json.JSONDecodeError:
            logger.error("Gemini bad JSON: %s", resp.text[:1000])
            return f"Gemini bad response: {resp.text[:500]}"
        candidates = data.get("candidates", [])
        if not candidates:
            logger.warning("Gemini empty candidates: %s", json.dumps(data)[:500])
            return f"Gemini returned no candidates: {json.dumps(data)[:300]}"
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            logger.warning("Gemini empty parts: %s", json.dumps(data)[:500])
            return "Gemini returned empty content"
        content = parts[0].get("text", "")
        if not content:
            logger.warning("Gemini empty text: %s", json.dumps(data)[:500])
            return "Gemini returned empty text"
        logger.info("Gemini response: %d chars, starts with: %s",
                    len(content), content[:150])
        return content
