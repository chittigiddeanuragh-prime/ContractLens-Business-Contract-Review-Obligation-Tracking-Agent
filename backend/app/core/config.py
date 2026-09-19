from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./storage/contractlens.db"
    STORAGE_DIR: str = "./storage"
    CONFIDENCE_THRESHOLD: float = 0.8
    LLM_PRIMARY: str = "gemini"
    LLM_FALLBACKS: Union[str, List[str]] = "groq,openrouter"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "meta-llama/llama-3.1-8b-instruct:free"

    LLM_MAX_CONCURRENCY: int = 2
    DEFAULT_ORG_ID: str = "org_default_001"

    # PDF Processing Settings
    MAX_UPLOAD_SIZE_MB: int = 25
    MAX_PDF_PAGES: int = 300
    SCANNED_PAGE_MIN_CHARS: int = 100
    SCANNED_MIN_PAGE_RATIO: float = 0.5
    SCANNED_LOW_CHAR_THRESHOLD: int = 50

    # Segmentation & Classification Settings
    CLASSIFY_WITH_LLM: bool = False

    # Field Extraction & Verification Settings
    EXTRACTION_MAX_CONTEXT_CHARS: int = 24000
    DATE_ORDER: str = "MDY"
    CONFIDENCE_WEIGHT_EXACT_QUOTE: float = 0.10
    CONFIDENCE_WEIGHT_BASELINE_AGREE: float = 0.10
    CONFIDENCE_WEIGHT_TARGET_CLAUSE: float = 0.05

    @field_validator("LLM_FALLBACKS", mode="before")
    @classmethod
    def parse_llm_fallbacks(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    def get_configured_providers(self) -> List[str]:
        providers = []
        if self.GEMINI_API_KEY.strip():
            providers.append("gemini")
        if self.GROQ_API_KEY.strip():
            providers.append("groq")
        if self.OPENROUTER_API_KEY.strip():
            providers.append("openrouter")
        return providers


settings = Settings()
