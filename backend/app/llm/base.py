from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ProviderError(Exception):
    def __init__(
        self,
        message: str,
        retryable: bool = False,
        status_code: int = 500,
        provider_name: str = "",
    ):
        super().__init__(message)
        self.message = message
        self.retryable = retryable
        self.status_code = status_code
        self.provider_name = provider_name

    def __str__(self) -> str:
        return f"[{self.provider_name or 'Provider'}] (status {self.status_code}, retryable={self.retryable}): {self.message}"


class LLMUnavailableError(Exception):
    def __init__(self, summary: Dict[str, Any]):
        message = f"All LLM providers failed: {summary}"
        super().__init__(message)
        self.summary = summary


class Provider(ABC):
    name: str
    model: str

    @abstractmethod
    async def complete_json(
        self,
        system: str,
        user: str,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Executes a JSON completion request to the LLM provider.
        Returns parsed JSON dict.
        Raises ProviderError on failure.
        """
        pass
