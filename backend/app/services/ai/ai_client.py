"""
app/services/ai/ai_client.py

Abstraction around external LLM providers (e.g. Gemini, OpenAI-compatible services).
Isolates API calls, rate-limiting, and timeout handling.
Never logs API keys or customer PII.
Raises AIAvailabilityError whenever the AI service is unconfigured or unreachable.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIAvailabilityError(Exception):
    """Raised when the AI provider cannot be contacted or is disabled."""
    pass


class AIClient:
    """
    HTTP client abstraction for invoking external generative AI models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        service_url: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        model_name: Optional[str] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.AI_API_KEY
        self.service_url = service_url if service_url is not None else settings.AI_SERVICE_URL
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else getattr(settings, "AI_TIMEOUT_SECONDS", 30)
        )
        self.model_name = (
            model_name if model_name is not None else getattr(settings, "AI_MODEL_NAME", "gemini-1.5-flash")
        )

    @property
    def is_configured(self) -> bool:
        """Returns True only if an API key or dedicated service URL is supplied."""
        return bool(self.api_key and self.api_key.strip()) or bool(self.service_url and self.service_url.strip())

    async def generate_analysis(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Sends the prompt to the configured AI provider.
        Returns the raw string response.

        Raises:
            AIAvailabilityError: If no key is set, timeout occurs, or network fails.
        """
        if not self.is_configured:
            logger.info("AI provider call bypassed: AI_API_KEY is not configured.")
            raise AIAvailabilityError("AI provider is not configured (missing AI_API_KEY).")

        logger.info(
            "Calling AI provider using model=%s with timeout=%ss",
            self.model_name,
            self.timeout_seconds,
        )

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout_seconds)) as client:
                # Custom proxy / gateway URL if provided
                if self.service_url:
                    payload = {
                        "prompt": prompt,
                        "system_prompt": system_prompt,
                        "model": self.model_name,
                    }
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                    }
                    resp = await client.post(self.service_url, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    # Return content field or raw text
                    if isinstance(data, dict):
                        return data.get("text") or data.get("content") or str(data)
                    return str(data)

                # Default: Google Gemini generateContent endpoint
                gemini_url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{self.model_name}:generateContent?key={self.api_key}"
                )
                contents = []
                if system_prompt:
                    contents.append({"role": "user", "parts": [{"text": f"System context:\n{system_prompt}"}]})
                contents.append({"role": "user", "parts": [{"text": prompt}]})

                req_body = {
                    "contents": contents,
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json",
                    },
                }

                resp = await client.post(gemini_url, json=req_body)
                resp.raise_for_status()
                res_json = resp.json()

                candidates = res_json.get("candidates") or []
                if not candidates:
                    raise AIAvailabilityError("Empty candidate list returned by Gemini API.")

                parts = candidates[0].get("content", {}).get("parts") or []
                if not parts:
                    raise AIAvailabilityError("No content parts returned in Gemini response.")

                return parts[0].get("text", "")

        except httpx.TimeoutException as exc:
            logger.warning("AI provider timed out after %s seconds: %s", self.timeout_seconds, exc)
            raise AIAvailabilityError(f"AI provider request timed out after {self.timeout_seconds}s") from exc
        except httpx.HTTPStatusError as exc:
            logger.warning("AI provider returned HTTP error %s: %s", exc.response.status_code, exc.response.text[:200])
            raise AIAvailabilityError(f"AI provider HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.warning("AI provider network failure: %s", exc)
            raise AIAvailabilityError(f"Network error connecting to AI provider: {exc}") from exc
        except Exception as exc:
            logger.exception("Unexpected error communicating with AI provider: %s", exc)
            raise AIAvailabilityError(f"Unexpected AI provider error: {exc}") from exc


# Default global instance
default_ai_client = AIClient()
