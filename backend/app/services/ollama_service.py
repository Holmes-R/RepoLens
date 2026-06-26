import requests
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, messages: List[Dict[str, str]]) -> Optional[str]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7, "top_p": 0.9},
        }
        log_msgs = [{k: v[:100] if k == "content" else v for k, v in m.items()} for m in messages[-3:]]
        logger.info("Ollama request: model=%s, messages=%d, last_msgs=%s",
                    self.model, len(messages), log_msgs)

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=180,
            )
        except requests.ConnectionError:
            logger.error("Cannot connect to Ollama at %s", self.base_url)
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

    def is_available(self) -> bool:
        """Check if Ollama server is reachable (does NOT check model existence)."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def test_chat(self) -> str:
        """Send a simple test prompt and return the raw response for debugging."""
        msgs = [
            {"role": "system", "content": "You are a helpful assistant. Reply with exactly one short sentence."},
            {"role": "user", "content": "Say hello in exactly 3 words."},
        ]
        result = self.chat(msgs)
        if result is None:
            return f"ERROR: Ollama returned None (check logs)"
        return result
