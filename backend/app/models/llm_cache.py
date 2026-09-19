from typing import Optional
from sqlalchemy import String, Text, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, BaseModelMixin


class LLMCache(Base, BaseModelMixin):
    __tablename__ = "llm_cache"
    __table_args__ = (
        UniqueConstraint("file_hash", "prompt_version", "model", "task_key", name="uix_cache_key"),
    )

    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    task_key: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    response: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
