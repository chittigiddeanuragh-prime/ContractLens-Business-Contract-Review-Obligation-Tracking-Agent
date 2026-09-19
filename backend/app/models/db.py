from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.models.base import Base

# Imports needed to ensure all models are registered with Base.metadata
from app.models.contract import Contract, ContractVersion
from app.models.document_page import DocumentPage
from app.models.clause import Clause
from app.models.defined_term import DefinedTerm
from app.models.clause_reference import ClauseReference
from app.models.extracted_field import ExtractedField
from app.models.obligation import Obligation
from app.models.llm_cache import LLMCache
from app.models.audit_log import AuditLog

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    if "///" in settings.DATABASE_URL:
        db_path = settings.DATABASE_URL.split("///")[1]
        if db_path and db_path != ":memory:":
            from pathlib import Path
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
