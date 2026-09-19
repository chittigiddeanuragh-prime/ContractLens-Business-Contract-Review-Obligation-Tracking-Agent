from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.models.db import get_db

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    configured_providers = settings.get_configured_providers()

    return {
        "status": "ok",
        "version": "1.0.0",
        "db": db_status,
        "llm_providers": configured_providers,
    }
