from typing import Optional
from sqlalchemy import String, Text, Boolean, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BaseModelMixin


class RiskItem(Base, BaseModelMixin):
    __tablename__ = "risk_items"

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), nullable=False, index=True)
    version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("contract_versions.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="general") # liability, termination, indemnification, data_privacy, payment_terms, compliance, ip_rights
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="medium") # critical, high, medium, low
    score: Mapped[float] = mapped_column(Float, nullable=False, default=5.0) # 0.0 - 10.0 risk severity score
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Grounded citation attributes
    quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clause_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("clauses.id"), nullable=True)
    char_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    char_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="verified") # verified, unverified, reviewed
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    confidence_breakdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON string

    contract: Mapped["Contract"] = relationship("Contract", back_populates="risk_items")
    clause: Mapped[Optional["Clause"]] = relationship("Clause")
