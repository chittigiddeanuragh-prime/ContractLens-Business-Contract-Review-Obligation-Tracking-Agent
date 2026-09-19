from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.contract import Contract
from app.models.obligation import Obligation
from app.services.obligation_extractor import ObligationExtractorService

router = APIRouter()


@router.post("/contracts/{contract_id}/obligations/extract")
def extract_obligations(contract_id: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter_by(id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    obligations = ObligationExtractorService.extract_obligations_for_version(
        db, contract.current_version_id
    )

    return {
        "contract_id": contract_id,
        "version_id": contract.current_version_id,
        "count": len(obligations),
        "obligations": [
            {
                "id": o.id,
                "party": o.party,
                "action": o.action,
                "trigger_rule": o.trigger_rule,
                "due_date": o.due_date.isoformat() if o.due_date else None,
                "days_until_due": o.days_until_due,
                "severity": o.severity,
                "hard_deadline": o.hard_deadline,
                "quote": o.quote,
                "char_start": o.char_start,
                "char_end": o.char_end,
                "page_start": o.page_start,
                "status": o.status,
                "confidence": o.confidence,
                "calculation_trace": o.calculation_trace
            }
            for o in obligations
        ]
    }


@router.get("/contracts/{contract_id}/obligations")
def get_obligations(
    contract_id: str,
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter_by(id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    query = db.query(Obligation).filter_by(version_id=contract.current_version_id)
    if status:
        query = query.filter_by(status=status)
    if severity:
        query = query.filter_by(severity=severity)

    obligations = query.all()

    return {
        "contract_id": contract_id,
        "version_id": contract.current_version_id,
        "count": len(obligations),
        "obligations": [
            {
                "id": o.id,
                "party": o.party,
                "action": o.action,
                "trigger_rule": o.trigger_rule,
                "due_date": o.due_date.isoformat() if o.due_date else None,
                "days_until_due": o.days_until_due,
                "severity": o.severity,
                "hard_deadline": o.hard_deadline,
                "quote": o.quote,
                "char_start": o.char_start,
                "char_end": o.char_end,
                "page_start": o.page_start,
                "status": o.status,
                "confidence": o.confidence,
                "calculation_trace": o.calculation_trace
            }
            for o in obligations
        ]
    }
