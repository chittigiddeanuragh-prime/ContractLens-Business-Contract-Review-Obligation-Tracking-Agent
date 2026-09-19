from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.contract import Contract, ContractVersion
from app.services.risk_analyzer import RiskAnalyzerService

router = APIRouter()


def _get_target_version_id(db: Session, contract_id: str) -> str:
    contract = db.query(Contract).filter_by(id=contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    version_id = getattr(contract, "current_version_id", None)
    if not version_id and contract.versions:
        version_id = contract.versions[-1].id
    
    if not version_id:
        version = db.query(ContractVersion).filter_by(contract_id=contract_id).order_by(ContractVersion.version_number.desc()).first()
        if version:
            version_id = version.id

    if not version_id:
        raise HTTPException(status_code=400, detail="Contract has no parsed versions")
    return version_id


@router.post("/contracts/{contract_id}/risk/analyze")
def analyze_risk(contract_id: str, db: Session = Depends(get_db)):
    version_id = _get_target_version_id(db, contract_id)
    res = RiskAnalyzerService.analyze_risks_for_version(db, version_id)
    return {
        "contract_id": contract_id,
        "version_id": version_id,
        **res
    }


@router.get("/contracts/{contract_id}/risk")
def get_risk(
    contract_id: str,
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_anomaly: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    version_id = _get_target_version_id(db, contract_id)
    res = RiskAnalyzerService.get_risks_for_version(db, version_id)
    
    risk_items = res["risk_items"]
    if severity:
        risk_items = [r for r in risk_items if r["severity"].lower() == severity.lower()]
    if category:
        risk_items = [r for r in risk_items if r["category"].lower() == category.lower()]
    if is_anomaly is not None:
        risk_items = [r for r in risk_items if r["is_anomaly"] == is_anomaly]
        
    return {
        "contract_id": contract_id,
        "version_id": version_id,
        "overall_risk_score": res["overall_risk_score"],
        "critical_count": res["critical_count"],
        "high_count": res["high_count"],
        "medium_count": res["medium_count"],
        "low_count": res["low_count"],
        "anomaly_count": res["anomaly_count"],
        "risk_items": risk_items
    }
