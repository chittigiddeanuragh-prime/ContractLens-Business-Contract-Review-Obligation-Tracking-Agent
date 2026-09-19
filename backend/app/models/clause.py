from typing import Optional
from sqlalchemy import String, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BaseModelMixin


class Clause(Base, BaseModelMixin):
    __tablename__ = "clauses"

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), nullable=False, index=True)
    version_id: Mapped[str] = mapped_column(String(36), ForeignKey("contract_versions.id"), nullable=False, index=True)
    number: Mapped[str] = mapped_column(String(64), nullable=False)
    heading: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    page: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("clauses.id"), nullable=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clause_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True) # definitions, term, renewal, termination, etc.
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    segmentation_method: Mapped[str] = mapped_column(String(32), nullable=False, default="rules") # rules, llm_assisted, paragraph_fallback
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    contract: Mapped["Contract"] = relationship("Contract", back_populates="clauses")
    sub_clauses: Mapped[list["Clause"]] = relationship("Clause", backref="parent", remote_side="Clause.id")
