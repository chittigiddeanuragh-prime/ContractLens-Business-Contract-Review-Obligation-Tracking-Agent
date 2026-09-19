import uuid
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.db import get_db
from app.models.contract import Contract, ContractVersion
from app.models.document_page import DocumentPage
from app.models.clause import Clause
from app.models.defined_term import DefinedTerm
from app.models.clause_reference import ClauseReference
from app.models.audit_log import AuditLog
from app.services.clause_segmenter import ClauseSegmenter
from app.services.clause_classifier import ClauseClassifier
from app.services.defined_terms import DefinedTermsExtractor
from app.services.cross_references import CrossReferenceResolver
from app.services.invariants import validate_clause_invariants

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/contracts/{contract_id}/versions/{version_id}", tags=["clauses"])


@router.get("/clauses")
def list_clauses(
    contract_id: str,
    version_id: str,
    format: str = Query("flat", pattern="^(flat|tree)$"),
    db: Session = Depends(get_db),
):
    version = db.query(ContractVersion).filter(ContractVersion.id == version_id, ContractVersion.contract_id == contract_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Contract version not found.")

    clauses = (
        db.query(Clause)
        .filter(Clause.version_id == version_id)
        .order_by(Clause.order_index.asc())
        .all()
    )

    flat_result = [
        {
            "id": c.id,
            "number": c.number,
            "heading": c.heading,
            "text": c.text,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "page": c.page,
            "parent_id": c.parent_id,
            "level": c.level,
            "order_index": c.order_index,
            "clause_type": c.clause_type,
            "char_start": c.char_start,
            "char_end": c.char_end,
            "segmentation_method": c.segmentation_method,
            "confidence": c.confidence,
        }
        for c in clauses
    ]

    if format == "flat":
        return {"clauses": flat_result, "total": len(flat_result)}

    # Build hierarchical tree
    clause_dict = {c["id"]: {**c, "children": []} for c in flat_result}
    root_clauses = []

    for c in flat_result:
        p_id = c["parent_id"]
        if p_id and p_id in clause_dict:
            clause_dict[p_id]["children"].append(clause_dict[c["id"]])
        else:
            root_clauses.append(clause_dict[c["id"]])

    return {"clauses": root_clauses, "total": len(flat_result)}


@router.get("/clauses/{clause_id}")
def get_clause_detail(contract_id: str, version_id: str, clause_id: str, db: Session = Depends(get_db)):
    clause = db.query(Clause).filter(Clause.id == clause_id, Clause.version_id == version_id).first()
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found.")

    sub_clauses = db.query(Clause).filter(Clause.parent_id == clause_id).order_by(Clause.order_index.asc()).all()
    references = db.query(ClauseReference).filter(ClauseReference.from_clause_id == clause_id).all()
    defined_terms = db.query(DefinedTerm).filter(DefinedTerm.clause_id == clause_id).all()

    return {
        "id": clause.id,
        "number": clause.number,
        "heading": clause.heading,
        "text": clause.text,
        "page_start": clause.page_start,
        "page_end": clause.page_end,
        "parent_id": clause.parent_id,
        "level": clause.level,
        "clause_type": clause.clause_type,
        "char_start": clause.char_start,
        "char_end": clause.char_end,
        "segmentation_method": clause.segmentation_method,
        "confidence": clause.confidence,
        "sub_clauses": [{"id": sc.id, "number": sc.number, "heading": sc.heading} for sc in sub_clauses],
        "references": [{"ref_text": r.ref_text, "to_number": r.to_number, "resolved_clause_id": r.resolved_clause_id} for r in references],
        "defined_terms": [{"term": dt.term, "definition": dt.definition} for dt in defined_terms],
    }


@router.get("/defined-terms")
def list_defined_terms(contract_id: str, version_id: str, db: Session = Depends(get_db)):
    terms = db.query(DefinedTerm).filter(DefinedTerm.version_id == version_id).all()
    return {
        "defined_terms": [
            {
                "id": t.id,
                "term": t.term,
                "definition": t.definition,
                "clause_id": t.clause_id,
                "char_start": t.char_start,
                "char_end": t.char_end,
            }
            for t in terms
        ]
    }


@router.post("/resegment", status_code=status.HTTP_200_OK)
def resegment_contract(contract_id: str, version_id: str, db: Session = Depends(get_db)):
    version = db.query(ContractVersion).filter(ContractVersion.id == version_id, ContractVersion.contract_id == contract_id).first()
    if not version or not version.canonical_text:
        raise HTTPException(status_code=404, detail="Contract version or canonical text not found.")

    pages = db.query(DocumentPage).filter(DocumentPage.version_id == version_id).order_by(DocumentPage.page_number.asc()).all()
    pages_data = [{"page_number": p.page_number, "width": p.width, "height": p.height, "char_start": p.char_start, "char_end": p.char_end} for p in pages]

    # Delete existing clauses, references, terms
    db.query(ClauseReference).filter(ClauseReference.version_id == version_id).delete()
    db.query(DefinedTerm).filter(DefinedTerm.version_id == version_id).delete()
    db.query(Clause).filter(Clause.version_id == version_id).delete()

    raw_clauses = ClauseSegmenter.segment_contract(version.canonical_text, pages_data)
    classified_clauses = ClauseClassifier.classify_clauses_batch(raw_clauses)

    # Validate invariants
    inv_check = validate_clause_invariants(version.canonical_text, classified_clauses)
    if not inv_check["valid"]:
        logger.warning(f"Resegment invariant warning: {inv_check['errors']}")

    temp_to_real_id = {}
    db_clauses = []

    for c_data in classified_clauses:
        real_id = str(uuid.uuid4())
        temp_to_real_id[c_data["temp_id"]] = real_id

        c_rec = Clause(
            id=real_id,
            contract_id=contract_id,
            version_id=version_id,
            number=c_data["number"],
            heading=c_data["heading"],
            text=c_data["text"],
            page_start=c_data["page_start"],
            page_end=c_data["page_end"],
            page=c_data["page_start"],
            parent_id=None,
            level=c_data["level"],
            order_index=c_data["order_index"],
            clause_type=c_data["clause_type"],
            char_start=c_data["char_start"],
            char_end=c_data["char_end"],
            segmentation_method=c_data["segmentation_method"],
            confidence=c_data["confidence"],
            org_id=version.org_id,
            created_by="admin",
        )
        db_clauses.append((c_rec, c_data.get("parent_id")))
        db.add(c_rec)

    for c_rec, parent_temp_id in db_clauses:
        if parent_temp_id and parent_temp_id in temp_to_real_id:
            c_rec.parent_id = temp_to_real_id[parent_temp_id]

    db.flush()

    # Extract Defined Terms & References
    extracted_terms = DefinedTermsExtractor.extract_defined_terms(version.canonical_text, classified_clauses)
    for t_data in extracted_terms:
        real_c_id = temp_to_real_id.get(t_data["clause_id"])
        term_rec = DefinedTerm(
            version_id=version_id,
            term=t_data["term"],
            definition=t_data["definition"],
            clause_id=real_c_id,
            char_start=t_data["char_start"],
            char_end=t_data["char_end"],
            org_id=version.org_id,
            created_by="admin",
        )
        db.add(term_rec)

    extracted_refs = CrossReferenceResolver.extract_and_resolve(classified_clauses)
    for r_data in extracted_refs:
        from_real_id = temp_to_real_id.get(r_data["from_clause_id"])
        to_real_id = temp_to_real_id.get(r_data["resolved_clause_id"]) if r_data.get("resolved_clause_id") else None

        if from_real_id:
            ref_rec = ClauseReference(
                version_id=version_id,
                from_clause_id=from_real_id,
                ref_text=r_data["ref_text"],
                to_number=r_data["to_number"],
                resolved_clause_id=to_real_id,
                org_id=version.org_id,
                created_by="admin",
            )
            db.add(ref_rec)

    # Audit log
    audit = AuditLog(
        user_id="admin",
        action="contract_resegment",
        entity_type="contract_version",
        entity_id=version_id,
        changes_after=json.dumps({"clause_count": len(classified_clauses)}),
        org_id=version.org_id,
    )
    db.add(audit)
    version.status = "segmented"
    db.commit()

    return {"status": "segmented", "resegmented_clauses_count": len(classified_clauses)}
