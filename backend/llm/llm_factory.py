"""
LLM factory — returns a ready-to-use LLM wrapper based on the configured provider.

Supported providers:
- ``gemini``  — Google Gemini via google-generativeai SDK
- ``groq``    — Groq inference API via httpx

Both implement the same ``BaseLLM`` interface with a ``generate(prompt) -> str`` method.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Base interface
# ---------------------------------------------------------------------------


class BaseLLM(ABC):
    """Abstract interface that all LLM backends must implement."""

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        """Generate text for the given prompt."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the backend is properly configured."""


# ---------------------------------------------------------------------------
# Gemini backend
# ---------------------------------------------------------------------------


class GeminiLLM(BaseLLM):
    """Google Gemini backend using the ``google-generativeai`` SDK."""

    MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._model = None

    def _get_model(self):
        if self._model is None:
            import google.generativeai as genai  # noqa

            genai.configure(api_key=self._api_key)
            self._model = genai.GenerativeModel(self.MODEL)
            logger.info("Gemini model '%s' initialised", self.MODEL)
        return self._model

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        try:
            model = self._get_model()
            response = model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": 0.3,
                },
            )
            return response.text
        except Exception as exc:
            logger.error("Gemini generate failed: %s", exc)
            raise

    def is_available(self) -> bool:
        return bool(self._api_key)


# ---------------------------------------------------------------------------
# Groq backend
# ---------------------------------------------------------------------------


class GroqLLM(BaseLLM):
    """Groq inference backend via REST API."""

    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL = "llama3-8b-8192"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        import httpx  # noqa

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        with httpx.Client(timeout=60) as client:
            response = client.post(self.API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def is_available(self) -> bool:
        return bool(self._api_key)


# ---------------------------------------------------------------------------
# Mock backend (testing / no API key)
# ---------------------------------------------------------------------------


class MockLLM(BaseLLM):
    """Deterministic mock used when no API key is configured."""

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        logger.warning("MockLLM is active — no real LLM configured")
        return (
            "This is a mock response. "
            "Please configure GEMINI_API_KEY or GROQ_API_KEY in your .env file."
        )

    def is_available(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class LLMFactory:
    """Creates and caches the appropriate LLM backend."""

    _instance: Optional[BaseLLM] = None

    @classmethod
    def get_llm(cls) -> BaseLLM:
        """Return the singleton LLM instance."""
        if cls._instance is None:
            cls._instance = cls._create()
        return cls._instance

    @classmethod
    def _create(cls) -> BaseLLM:
        from config import settings  # deferred to avoid import-time failures

        provider = settings.llm_provider.lower()

        if provider == "gemini" and settings.gemini_api_key:
            logger.info("Using Gemini LLM backend")
            return GeminiLLM(settings.gemini_api_key)

        if provider == "groq" and settings.groq_api_key:
            logger.info("Using Groq LLM backend")
            return GroqLLM(settings.groq_api_key)

        # Fallback: try Gemini even if provider is not explicitly set
        if settings.gemini_api_key:
            logger.info("Falling back to Gemini LLM")
            return GeminiLLM(settings.gemini_api_key)

        if settings.groq_api_key:
            logger.info("Falling back to Groq LLM")
            return GroqLLM(settings.groq_api_key)

        logger.warning("No LLM API key found — using MockLLM")
        return MockLLM()
