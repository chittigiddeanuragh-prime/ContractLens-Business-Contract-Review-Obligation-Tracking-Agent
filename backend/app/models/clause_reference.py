from typing import Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BaseModelMixin


class ClauseReference(Base, BaseModelMixin):
    __tablename__ = "clause_references"

    version_id: Mapped[str] = mapped_column(String(36), ForeignKey("contract_versions.id"), nullable=False, index=True)
    from_clause_id: Mapped[str] = mapped_column(String(36), ForeignKey("clauses.id"), nullable=False, index=True)
    ref_text: Mapped[str] = mapped_column(String(255), nullable=False) # e.g. "Section 12.3", "Clause 4", "Schedule A"
    to_number: Mapped[str] = mapped_column(String(64), nullable=False) # e.g. "12.3", "4", "A"
    resolved_clause_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("clauses.id"), nullable=True)

    from_clause: Mapped["Clause"] = relationship("Clause", foreign_keys=[from_clause_id])
    resolved_clause: Mapped[Optional["Clause"]] = relationship("Clause", foreign_keys=[resolved_clause_id])
