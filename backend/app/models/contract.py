from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BaseModelMixin


class Contract(Base, BaseModelMixin):
    __tablename__ = "contracts"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    counterparty: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False, default="application/pdf")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")

    versions: Mapped[list["ContractVersion"]] = relationship("ContractVersion", back_populates="contract", cascade="all, delete-orphan")
    clauses: Mapped[list["Clause"]] = relationship("Clause", back_populates="contract", cascade="all, delete-orphan")
    extracted_fields: Mapped[list["ExtractedField"]] = relationship("ExtractedField", back_populates="contract", cascade="all, delete-orphan")
    obligations: Mapped[list["Obligation"]] = relationship("Obligation", back_populates="contract", cascade="all, delete-orphan")
    risk_items: Mapped[list["RiskItem"]] = relationship("RiskItem", back_populates="contract", cascade="all, delete-orphan")


class ContractVersion(Base, BaseModelMixin):
    __tablename__ = "contract_versions"

    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded") # uploaded, parsing, parsed, failed, scanned_unsupported
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    canonical_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    contract: Mapped["Contract"] = relationship("Contract", back_populates="versions")
    pages: Mapped[list["DocumentPage"]] = relationship("DocumentPage", back_populates="version", cascade="all, delete-orphan")
