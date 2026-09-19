from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.contract import Contract, ContractVersion
from app.models.extracted_field import ExtractedField
from app.agents.field_extractor import FieldExtractorAgent

router = APIRouter()


@router.post("/contracts/{contract_id}/extract")
def extract_contract_fields(
    contract_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter_by(id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    version = db.query(ContractVersion).filter_by(id=contract.current_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Contract version not found")

    version.status = "extracting"
    db.commit()

    # Synchronous extraction for fast API response or background task
    agent = FieldExtractorAgent(db)
    fields = agent.extract_fields_for_version(version.id)

    # Check review statuses to determine version status
    needs_review_count = sum(1 for f in fields if f.review_status in ("needs_review", "low_confidence"))
    if needs_review_count > 0:
        version.status = "ready_with_warnings"
    else:
        version.status = "ready"
    db.commit()

    return {
        "status": version.status,
        "contract_id": contract_id,
        "version_id": version.id,
        "fields_extracted": len(fields),
        "needs_review_count": needs_review_count
    }


@router.get("/contracts/{contract_id}/fields")
def get_contract_fields(
    contract_id: str,
    group: Optional[str] = Query(None, description="Filter by group name"),
    review_status: Optional[str] = Query(None, description="Filter by review status"),
    db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter_by(id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    query = db.query(ExtractedField).filter_by(version_id=contract.current_version_id)

    if group:
        query = query.filter_by(group_name=group)
    if review_status:
        query = query.filter_by(review_status=review_status)

    fields = query.all()

    return {
        "contract_id": contract_id,
        "version_id": contract.current_version_id,
        "total_fields": len(fields),
        "fields": [
            {
                "id": f.id,
                "field_name": f.field_name,
                "display_label": f.display_label,
                "group_name": f.group_name,
                "value_type": f.value_type,
                "value_raw": f.value_raw,
                "value_normalized": f.value_normalized,
                "quote": f.quote,
                "char_start": f.char_start,
                "char_end": f.char_end,
                "page_start": f.page_start,
                "page_end": f.page_end,
                "clause_id": f.clause_id,
                "verification_status": f.verification_status,
                "review_status": f.review_status,
                "confidence": f.confidence,
                "confidence_breakdown": f.confidence_breakdown,
                "conflict": f.conflict,
                "alternates": f.alternates,
                "extraction_method": f.extraction_method
            }
            for f in fields
        ]
    }


@router.get("/contracts/{contract_id}/fields/{field_name}")
def get_single_field(
    contract_id: str,
    field_name: str,
    db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter_by(id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    field = db.query(ExtractedField).filter_by(
        version_id=contract.current_version_id,
        field_name=field_name
    ).first()

    if not field:
        raise HTTPException(status_code=404, detail=f"Field '{field_name}' not found")

    return {
        "id": field.id,
        "field_name": field.field_name,
        "display_label": field.display_label,
        "group_name": field.group_name,
        "value_type": field.value_type,
        "value_raw": field.value_raw,
        "value_normalized": field.value_normalized,
        "quote": field.quote,
        "char_start": field.char_start,
        "char_end": field.char_end,
        "page_start": field.page_start,
        "page_end": field.page_end,
        "clause_id": field.clause_id,
        "verification_status": field.verification_status,
        "review_status": field.review_status,
        "confidence": field.confidence,
        "confidence_breakdown": field.confidence_breakdown,
        "conflict": field.conflict,
        "alternates": field.alternates,
        "extraction_method": field.extraction_method
    }


@router.get("/contracts/{contract_id}/summary")
def get_contract_summary(
    contract_id: str,
    db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter_by(id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    fields = db.query(ExtractedField).filter_by(version_id=contract.current_version_id).all()
    field_map = {f.field_name: f for f in fields}

    return {
        "contract_id": contract.id,
        "name": contract.name,
        "counterparty": contract.counterparty or (field_map.get("parties").value_raw if field_map.get("parties") else None),
        "status": contract.current_version.status if contract.current_version else "unknown",
        "key_fields": {
            "parties": field_map.get("parties").value_raw if field_map.get("parties") else None,
            "effective_date": field_map.get("effective_date").value_normalized.get("iso_date") if field_map.get("effective_date") and field_map.get("effective_date").value_normalized else None,
            "expiration_date": field_map.get("expiration_date").value_normalized.get("iso_date") if field_map.get("expiration_date") and field_map.get("expiration_date").value_normalized else None,
            "term_length": field_map.get("term_length").value_raw if field_map.get("term_length") else None,
            "contract_value": field_map.get("contract_value_or_fees").value_raw if field_map.get("contract_value_or_fees") else None,
            "liability_cap": field_map.get("liability_cap").value_raw if field_map.get("liability_cap") else None,
            "governing_law": field_map.get("governing_law").value_raw if field_map.get("governing_law") else None,
        }
    }
