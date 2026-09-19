import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.llm.base import Provider, ProviderError, LLMUnavailableError
from app.llm.providers import GeminiProvider, OpenAICompatProvider
from app.llm.prompts import get_prompt
from app.models.llm_cache import LLMCache

logger = logging.getLogger(__name__)

# Global concurrency semaphore
_llm_semaphore = asyncio.Semaphore(settings.LLM_MAX_CONCURRENCY)


class LLMClient:
    @staticmethod
    def get_provider_by_name(name: str) -> Optional[Provider]:
        name_clean = name.strip().lower()
        if name_clean == "gemini":
            return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
        elif name_clean == "groq":
            return OpenAICompatProvider(
                name="groq",
                base_url="https://api.groq.com/openai/v1",
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL,
            )
        elif name_clean == "openrouter":
            return OpenAICompatProvider(
                name="openrouter",
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY,
                model=settings.OPENROUTER_MODEL,
            )
        return None

    @classmethod
    def get_configured_chain(cls) -> List[Provider]:
        chain_names = [settings.LLM_PRIMARY] + list(settings.LLM_FALLBACKS)
        providers = []
        seen = set()
        for name in chain_names:
            if name and name not in seen:
                seen.add(name)
                provider = cls.get_provider_by_name(name)
                if provider:
                    providers.append(provider)
        return providers

    @classmethod
    async def run(
        cls,
        task: str,
        schema: Optional[Type[BaseModel]] = None,
        system: Optional[str] = None,
        user: str = "",
        file_hash: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Executes an LLM request using the configured provider fallback chain, DB caching,
        concurrency limits, and Pydantic schema validation.
        """
        # Resolve prompt and version
        default_system, prompt_version = get_prompt(task)
        system_prompt = system or default_system
        schema_dict = schema.model_json_schema() if schema else None

        # 1. Check DB LLMCache
        if file_hash and db:
            cached = (
                db.query(LLMCache)
                .filter(
                    LLMCache.file_hash == file_hash,
                    LLMCache.prompt_version == prompt_version,
                    LLMCache.task_key == task,
                )
                .first()
            )
            if cached:
                logger.info(
                    "LLM Call",
                    extra={
                        "extra_fields": {
                            "provider": cached.provider,
                            "model": cached.model,
                            "latency_ms": 0,
                            "cache_hit": True,
                            "attempt": 0,
                            "outcome": "cache_hit",
                            "task": task,
                        }
                    },
                )
                cached_data = json.loads(cached.response)
                if schema:
                    # Validate cached content against schema
                    schema.model_validate(cached_data)
                return cached_data

        providers = cls.get_configured_chain()
        failure_summary: Dict[str, str] = {}

        async with _llm_semaphore:
            for provider in providers:
                validation_retry_done = False
                current_system = system_prompt

                for attempt in range(1, 3):
                    if attempt > 1:
                        await asyncio.sleep(0.5 * (2 ** (attempt - 2)))

                    start_time = time.time()
                    try:
                        res_json = await provider.complete_json(
                            system=current_system,
                            user=user,
                            schema=schema_dict,
                            temperature=0.0,
                        )
                        latency_ms = int((time.time() - start_time) * 1000)

                        # Pydantic Schema Validation
                        if schema:
                            try:
                                validated_obj = schema.model_validate(res_json)
                                res_json = validated_obj.model_dump()
                            except ValidationError as ve:
                                if not validation_retry_done:
                                    validation_retry_done = True
                                    current_system = (
                                        f"{system_prompt}\n\nNote: Your last output failed schema validation: {str(ve)}. "
                                        "Ensure you return strictly valid JSON matching the schema."
                                    )
                                    logger.warning(
                                        f"LLM output validation failed for {provider.name}, retrying once with schema warning."
                                    )
                                    continue
                                else:
                                    raise ProviderError(
                                        f"Pydantic validation failed twice: {str(ve)}",
                                        retryable=False,
                                        status_code=422,
                                        provider_name=provider.name,
                                    )

                        # Token estimation
                        prompt_tokens = (len(current_system) + len(user)) // 4
                        completion_tokens = len(json.dumps(res_json)) // 4

                        logger.info(
                            "LLM Call",
                            extra={
                                "extra_fields": {
                                    "provider": provider.name,
                                    "model": provider.model,
                                    "latency_ms": latency_ms,
                                    "cache_hit": False,
                                    "attempt": attempt,
                                    "outcome": "success",
                                    "task": task,
                                }
                            },
                        )

                        # Save to DB cache if db and file_hash provided
                        if file_hash and db:
                            try:
                                cache_entry = LLMCache(
                                    file_hash=file_hash,
                                    prompt_version=prompt_version,
                                    model=provider.model,
                                    task_key=task,
                                    response=json.dumps(res_json),
                                    prompt_tokens=prompt_tokens,
                                    completion_tokens=completion_tokens,
                                    latency_ms=latency_ms,
                                    provider=provider.name,
                                )
                                db.add(cache_entry)
                                db.commit()
                            except Exception as db_err:
                                db.rollback()
                                logger.warning(f"Failed to save LLM response to cache: {str(db_err)}")

                        return res_json

                    except ProviderError as pe:
                        latency_ms = int((time.time() - start_time) * 1000)
                        failure_summary[provider.name] = str(pe)
                        logger.warning(
                            "LLM Call Failed",
                            extra={
                                "extra_fields": {
                                    "provider": provider.name,
                                    "model": provider.model,
                                    "latency_ms": latency_ms,
                                    "cache_hit": False,
                                    "attempt": attempt,
                                    "outcome": "error",
                                    "error": str(pe),
                                }
                            },
                        )
                        if not pe.retryable:
                            break

        raise LLMUnavailableError(summary=failure_summary)
