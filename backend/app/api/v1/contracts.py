import hashlib
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks, Query, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.models.db import get_db, SessionLocal
from app.models.contract import Contract, ContractVersion
from app.models.document_page import DocumentPage
from app.models.audit_log import AuditLog
from app.services.storage import LocalStorage
from app.models.clause import Clause
from app.models.defined_term import DefinedTerm
from app.models.clause_reference import ClauseReference
from app.services.pdf_parser import PDFParser
from app.services.clause_segmenter import ClauseSegmenter
from app.services.clause_classifier import ClauseClassifier
from app.services.defined_terms import DefinedTermsExtractor
from app.services.cross_references import CrossReferenceResolver

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/contracts", tags=["contracts"])
storage = LocalStorage()


def parse_pdf_background(version_id: str):
    """Background worker task to parse uploaded PDF and transition version status machine."""
    db: Session = SessionLocal()
    try:
        version = db.query(ContractVersion).filter(ContractVersion.id == version_id).first()
        if not version:
            return

        version.status = "parsing"
        db.commit()

        # Read PDF bytes from storage
        pdf_bytes = storage.read(version.file_path)

        # Parse PDF
        parse_result = PDFParser.parse_pdf_bytes(pdf_bytes)

        if parse_result.get("is_scanned"):
            version.status = "scanned_unsupported"
            version.error_code = parse_result.get("error_code", "scanned_unsupported")
            version.error_message = parse_result.get("error_message")
            version.page_count = parse_result.get("page_count", 0)
            db.commit()
            return

        # Store canonical text & pages
        version.canonical_text = parse_result["canonical_text"]
        version.page_count = parse_result["page_count"]

        # Delete existing pages if any
        db.query(DocumentPage).filter(DocumentPage.version_id == version_id).delete()

        for p_data in parse_result["pages_data"]:
            page_rec = DocumentPage(
                version_id=version_id,
                page_number=p_data["page_number"],
                width=p_data["width"],
                height=p_data["height"],
                char_start=p_data["char_start"],
                char_end=p_data["char_end"],
                text=p_data["text"],
                words_json=p_data["words_json"],
                org_id=version.org_id,
                created_by=version.created_by,
            )
            db.add(page_rec)

        version.status = "parsed"
        db.commit()

        # =====================================================================
        # Phase 4: Auto-start Clause Segmentation
        # =====================================================================
        version.status = "segmenting"
        db.commit()

        # Clean existing clauses, terms, references if any
        db.query(ClauseReference).filter(ClauseReference.version_id == version_id).delete()
        db.query(DefinedTerm).filter(DefinedTerm.version_id == version_id).delete()
        db.query(Clause).filter(Clause.version_id == version_id).delete()

        raw_clauses = ClauseSegmenter.segment_contract(version.canonical_text, parse_result["pages_data"])
        classified_clauses = ClauseClassifier.classify_clauses_batch(raw_clauses)

        # Map temp_id to real database UUIDs
        import uuid
        temp_to_real_id = {}
        db_clauses = []

        for c_data in classified_clauses:
            real_id = str(uuid.uuid4())
            temp_to_real_id[c_data["temp_id"]] = real_id

            c_rec = Clause(
                id=real_id,
                contract_id=version.contract_id,
                version_id=version_id,
                number=c_data["number"],
                heading=c_data["heading"],
                text=c_data["text"],
                page_start=c_data["page_start"],
                page_end=c_data["page_end"],
                page=c_data["page_start"],
                parent_id=None, # Updated in second pass
                level=c_data["level"],
                order_index=c_data["order_index"],
                clause_type=c_data["clause_type"],
                char_start=c_data["char_start"],
                char_end=c_data["char_end"],
                segmentation_method=c_data["segmentation_method"],
                confidence=c_data["confidence"],
                org_id=version.org_id,
                created_by=version.created_by,
            )
            db_clauses.append((c_rec, c_data.get("parent_id")))
            db.add(c_rec)

        # Second pass: resolve parent_id UUIDs
        for c_rec, parent_temp_id in db_clauses:
            if parent_temp_id and parent_temp_id in temp_to_real_id:
                c_rec.parent_id = temp_to_real_id[parent_temp_id]

        db.flush()

        # Extract Defined Terms
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
                created_by=version.created_by,
            )
            db.add(term_rec)

        # Extract Cross-References
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
                    created_by=version.created_by,
                )
                db.add(ref_rec)

        version.status = "segmented"
        version.error_code = None
        version.error_message = None

        contract = db.query(Contract).filter(Contract.id == version.contract_id).first()
        if contract:
            contract.status = "segmented"

        db.commit()

        # =====================================================================
        # Phase 5: Auto-start Key-Field Extraction
        # =====================================================================
        version.status = "extracting"
        if contract:
            contract.status = "extracting"
        db.commit()

        from app.agents.field_extractor import FieldExtractorAgent
        from app.services.obligation_extractor import ObligationExtractorService
        from app.services.risk_analyzer import RiskAnalyzerService

        agent = FieldExtractorAgent(db)
        fields = agent.extract_fields_for_version(version_id)
        ObligationExtractorService.extract_obligations_for_version(db, version_id)
        RiskAnalyzerService.analyze_risks_for_version(db, version_id)

        needs_review_count = sum(1 for f in fields if f.review_status in ("needs_review", "low_confidence"))
        final_status = "ready_with_warnings" if needs_review_count > 0 else "ready"
        version.status = final_status
        if contract:
            contract.status = final_status

        db.commit()


    except Exception as e:

        db.rollback()
        logger.error(f"Failed to parse PDF for version {version_id}: {str(e)}", exc_info=True)
        try:
            v_fail = db.query(ContractVersion).filter(ContractVersion.id == version_id).first()
            if v_fail:
                v_fail.status = "failed"
                v_fail.error_code = "parse_error"
                v_fail.error_message = str(e)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    counterparty: Optional[str] = Form(None),
    contract_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Validate Magic Bytes
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Invalid file format: must be a PDF document.")

    # Validate Max File Size
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB.")

    # Compute SHA-256
    file_hash = hashlib.sha256(content).hexdigest()
    org_id = settings.DEFAULT_ORG_ID

    # SHA-256 Deduplication check
    existing_version = (
        db.query(ContractVersion)
        .filter(ContractVersion.file_hash == file_hash, ContractVersion.org_id == org_id)
        .first()
    )
    if existing_version:
        return Response(
            content=json.dumps({
                "duplicate": True,
                "contract_id": existing_version.contract_id,
                "version_id": existing_version.id,
                "status": existing_version.status,
                "message": "File hash matched existing version.",
            }),
            status_code=200,
            media_type="application/json",
        )

    # Validate or create contract
    if contract_id:
        contract = db.query(Contract).filter(Contract.id == contract_id, Contract.org_id == org_id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="Specified contract_id not found.")
        version_number = len(contract.versions) + 1
    else:
        title_val = name.strip() if name and name.strip() else file.filename
        contract = Contract(
            title=title_val,
            counterparty=counterparty.strip() if counterparty else None,
            filename=file.filename,
            file_hash=file_hash,
            file_path="",
            file_size=len(content),
            mime_type="application/pdf",
            status="uploaded",
            org_id=org_id,
        )
        db.add(contract)
        db.flush()
        version_number = 1

    # Generate version storage path: {org_id}/{contract_id}/{version_id}.pdf
    import uuid
    version_id = str(uuid.uuid4())
    rel_storage_path = f"{org_id}/{contract.id}/{version_id}.pdf"
    abs_path = storage.save(rel_storage_path, content)

    # Validate PDF structure / password lock using PyMuPDF before proceeding
    import fitz
    try:
        doc = fitz.open(stream=content, filetype="pdf")
        if doc.is_encrypted:
            storage.delete(rel_storage_path)
            raise HTTPException(status_code=400, detail="Encrypted or password-protected PDFs are not supported.")
        if len(doc) > settings.MAX_PDF_PAGES:
            storage.delete(rel_storage_path)
            raise HTTPException(status_code=400, detail=f"PDF exceeds maximum page limit of {settings.MAX_PDF_PAGES} pages.")
    except HTTPException:
        raise
    except Exception as e:
        storage.delete(rel_storage_path)
        raise HTTPException(status_code=400, detail=f"Corrupt or unreadable PDF: {str(e)}")

    contract_version = ContractVersion(
        id=version_id,
        contract_id=contract.id,
        version_number=version_number,
        file_hash=file_hash,
        file_path=rel_storage_path,
        status="uploaded",
        org_id=org_id,
    )
    db.add(contract_version)

    # Create Audit Log
    audit = AuditLog(
        user_id="system",
        action="contract_upload",
        entity_type="contract",
        entity_id=contract.id,
        changes_after=json.dumps({"version_id": version_id, "file_hash": file_hash}),
        org_id=org_id,
    )
    db.add(audit)
    db.commit()

    # Trigger Background Task
    background_tasks.add_task(parse_pdf_background, version_id)

    return {
        "duplicate": False,
        "contract_id": contract.id,
        "version_id": version_id,
        "status": "uploaded",
        "version_number": version_number,
    }


@router.get("")
def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    org_id = settings.DEFAULT_ORG_ID
    contracts = (
        db.query(Contract)
        .filter(Contract.org_id == org_id)
        .order_by(Contract.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    total = db.query(func.count(Contract.id)).filter(Contract.org_id == org_id).scalar()

    result = []
    for c in contracts:
        latest_version = (
            db.query(ContractVersion)
            .filter(ContractVersion.contract_id == c.id)
            .order_by(ContractVersion.version_number.desc())
            .first()
        )
        result.append({
            "id": c.id,
            "title": c.title,
            "counterparty": c.counterparty,
            "filename": c.filename,
            "status": latest_version.status if latest_version else c.status,
            "version_count": len(c.versions),
            "latest_version_id": latest_version.id if latest_version else None,
            "page_count": latest_version.page_count if latest_version else 0,
            "created_at": c.created_at.isoformat(),
        })

    return {"total": total, "contracts": result}


@router.get("/{contract_id}")
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    org_id = settings.DEFAULT_ORG_ID
    c = db.query(Contract).filter(Contract.id == contract_id, Contract.org_id == org_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contract not found.")

    versions = (
        db.query(ContractVersion)
        .filter(ContractVersion.contract_id == c.id)
        .order_by(ContractVersion.version_number.desc())
        .all()
    )

    return {
        "id": c.id,
        "title": c.title,
        "counterparty": c.counterparty,
        "filename": c.filename,
        "created_at": c.created_at.isoformat(),
        "versions": [
            {
                "id": v.id,
                "version_number": v.version_number,
                "status": v.status,
                "error_code": v.error_code,
                "error_message": v.error_message,
                "page_count": v.page_count,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ],
    }


@router.get("/{contract_id}/versions/{version_id}")
def get_contract_version(contract_id: str, version_id: str, db: Session = Depends(get_db)):
    v = db.query(ContractVersion).filter(ContractVersion.id == version_id, ContractVersion.contract_id == contract_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Contract version not found.")

    return {
        "id": v.id,
        "contract_id": v.contract_id,
        "version_number": v.version_number,
        "status": v.status,
        "error_code": v.error_code,
        "error_message": v.error_message,
        "page_count": v.page_count,
        "canonical_text_length": len(v.canonical_text) if v.canonical_text else 0,
        "created_at": v.created_at.isoformat(),
    }


@router.get("/{contract_id}/versions/{version_id}/file")
def get_version_file(contract_id: str, version_id: str, db: Session = Depends(get_db)):
    v = db.query(ContractVersion).filter(ContractVersion.id == version_id, ContractVersion.contract_id == contract_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Contract version not found.")

    if not storage.exists(v.file_path):
        raise HTTPException(status_code=404, detail="PDF storage file not found.")

    abs_path = storage._resolve_path(v.file_path)
    return FileResponse(
        path=str(abs_path),
        media_type="application/pdf",
        filename=f"contract_{v.version_number}.pdf",
        headers={"Accept-Ranges": "bytes"},
    )


@router.get("/{contract_id}/versions/{version_id}/pages/{page_num}")
def get_version_page(contract_id: str, version_id: str, page_num: int, db: Session = Depends(get_db)):
    page = (
        db.query(DocumentPage)
        .filter(DocumentPage.version_id == version_id, DocumentPage.page_number == page_num)
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail=f"Page {page_num} not found.")

    return {
        "page_number": page.page_number,
        "width": page.width,
        "height": page.height,
        "char_start": page.char_start,
        "char_end": page.char_end,
        "text": page.text,
    }


@router.get("/{contract_id}/versions/{version_id}/highlights")
def get_version_highlights(
    contract_id: str,
    version_id: str,
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=0),
    db: Session = Depends(get_db),
):
    v = db.query(ContractVersion).filter(ContractVersion.id == version_id, ContractVersion.contract_id == contract_id).first()
    if not v or not v.canonical_text:
        raise HTTPException(status_code=404, detail="Contract version or canonical text not found.")

    max_len = len(v.canonical_text)
    if start >= max_len or end > max_len or start >= end:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid offset range [{start}, {end}]. Canonical text length is {max_len}.",
        )

    pages = (
        db.query(DocumentPage)
        .filter(DocumentPage.version_id == version_id)
        .order_by(DocumentPage.page_number.asc())
        .all()
    )

    pages_data = [
        {
            "page_number": p.page_number,
            "width": p.width,
            "height": p.height,
            "words_json": p.words_json,
        }
        for p in pages
    ]

    highlights = PDFParser.resolve_highlights(pages_data, start, end)
    return {"start": start, "end": end, "highlights": highlights}
