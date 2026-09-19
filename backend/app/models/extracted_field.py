from typing import Optional
from sqlalchemy import String, Text, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BaseModelMixin


class ExtractedField(Base, BaseModelMixin):
    __tablename__ = "extracted_fields"

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), nullable=False, index=True)
    version_id: Mapped[str] = mapped_column(String(36), ForeignKey("contract_versions.id"), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    display_label: Mapped[str] = mapped_column(String(128), nullable=False)
    value_type: Mapped[str] = mapped_column(String(32), nullable=False, default="text")
    value: Mapped[str] = mapped_column(Text, nullable=False) # Human-readable display value
    value_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_normalized: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON object
    normalized_kind: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Verified canonical text slice
    llm_quote_debug: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clause_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("clauses.id"), nullable=True)
    clause_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    char_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    char_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="failed") # exact, fuzzy, outside_clause, failed, not_found
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    confidence_breakdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON object
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, default="auto_approved") # auto_approved, needs_review, approved, edited, rejected, not_found
    conflict: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    alternates: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON array
    extraction_method: Mapped[str] = mapped_column(String(32), nullable=False, default="llm") # llm, baseline, both
    provider: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    contract: Mapped["Contract"] = relationship("Contract", back_populates="extracted_fields")
    clause: Mapped[Optional["Clause"]] = relationship("Clause")
