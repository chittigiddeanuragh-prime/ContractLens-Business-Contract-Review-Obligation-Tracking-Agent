from datetime import date
from typing import Optional
from sqlalchemy import String, Text, Boolean, Date, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BaseModelMixin


class Obligation(Base, BaseModelMixin):
    __tablename__ = "obligations"

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), nullable=False, index=True)
    version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("contract_versions.id"), nullable=True, index=True)
    party: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_rule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    days_until_due: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="medium") # high, medium, low
    hard_deadline: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clause_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("clauses.id"), nullable=True)
    char_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    char_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending") # pending, fulfilled, overdue, needs_anchor
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    confidence_breakdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON
    calculation_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON calculation trace

    contract: Mapped["Contract"] = relationship("Contract", back_populates="obligations")
    clause: Mapped[Optional["Clause"]] = relationship("Clause")
