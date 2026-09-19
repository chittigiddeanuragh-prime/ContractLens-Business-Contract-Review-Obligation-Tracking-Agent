import json
import logging
from typing import Any, Dict, Optional
import httpx
from app.llm.base import Provider, ProviderError

logger = logging.getLogger(__name__)


def parse_json_response(raw_text: str) -> Dict[str, Any]:
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)


class GeminiProvider(Provider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.name = "gemini"

    async def complete_json(
        self,
        system: str,
        user: str,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ProviderError("Gemini API key is missing", retryable=False, status_code=401, provider_name=self.name)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        prompt_text = f"{system}\n\n{user}"
        if schema:
            prompt_text += f"\n\nReturn JSON matching schema: {json.dumps(schema)}"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt_text}],
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": temperature,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                res = await client.post(url, json=payload)
            except httpx.RequestError as e:
                raise ProviderError(f"Network error: {str(e)}", retryable=True, status_code=503, provider_name=self.name)

            if res.status_code != 200:
                is_retryable = res.status_code in (429, 500, 502, 503, 504)
                raise ProviderError(
                    f"Gemini API returned status {res.status_code}: {res.text[:200]}",
                    retryable=is_retryable,
                    status_code=res.status_code,
                    provider_name=self.name,
                )

            try:
                data = res.json()
                raw_content = data["candidates"][0]["content"]["parts"][0]["text"]
                return parse_json_response(raw_content)
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                raise ProviderError(
                    f"Failed to parse JSON response from Gemini: {str(e)}",
                    retryable=True,
                    status_code=502,
                    provider_name=self.name,
                )


class OpenAICompatProvider(Provider):
    def __init__(self, name: str, base_url: str, api_key: str, model: str):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def complete_json(
        self,
        system: str,
        user: str,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ProviderError(f"{self.name} API key is missing", retryable=False, status_code=401, provider_name=self.name)

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.name == "openrouter":
            headers["HTTP-Referer"] = "https://contractlens.ai"
            headers["X-Title"] = "ContractLens"

        system_msg = system
        if schema:
            system_msg += f"\n\nReturn JSON matching schema: {json.dumps(schema)}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                res = await client.post(url, headers=headers, json=payload)
            except httpx.RequestError as e:
                raise ProviderError(f"Network error: {str(e)}", retryable=True, status_code=503, provider_name=self.name)

            if res.status_code != 200:
                is_retryable = res.status_code in (429, 500, 502, 503, 504)
                raise ProviderError(
                    f"{self.name} API returned status {res.status_code}: {res.text[:200]}",
                    retryable=is_retryable,
                    status_code=res.status_code,
                    provider_name=self.name,
                )

            try:
                data = res.json()
                raw_content = data["choices"][0]["message"]["content"]
                return parse_json_response(raw_content)
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                raise ProviderError(
                    f"Failed to parse JSON response from {self.name}: {str(e)}",
                    retryable=True,
                    status_code=502,
                    provider_name=self.name,
                )
