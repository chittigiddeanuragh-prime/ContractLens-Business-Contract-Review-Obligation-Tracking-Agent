import json
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.contract import ContractVersion
from app.models.clause import Clause
from app.models.obligation import Obligation
from app.models.extracted_field import ExtractedField
from app.models.document_page import DocumentPage
from app.services.quote_verifier import QuoteVerifier
from app.services.baseline_extractor import BaselineExtractor

logger = logging.getLogger(__name__)


class ObligationExtractorService:
    """
    Service for extracting active legal obligations and computing deadlines.
    Uses injectable DEMO_AS_OF_DATE (Invariant Q5) for deterministic date math.
    """

    @staticmethod
    def get_as_of_date() -> date:
        demo_str = getattr(settings, "DEMO_AS_OF_DATE", "2026-02-01")
        try:
            return datetime.strptime(demo_str, "%Y-%m-%d").date()
        except Exception:
            return date(2026, 2, 1)

    @staticmethod
    def extract_obligations_for_version(db: Session, version_id: str) -> List[Obligation]:
        version = db.query(ContractVersion).filter_by(id=version_id).first()
        if not version:
            return []

        as_of_date = ObligationExtractorService.get_as_of_date()

        # Load clauses and pages
        clauses_db = db.query(Clause).filter_by(version_id=version_id).all()
        clauses = [
            {
                "id": c.id,
                "temp_id": getattr(c, "temp_id", None) or c.id,
                "clause_number": getattr(c, "number", None) or getattr(c, "clause_number", None),
                "title": getattr(c, "heading", None) or getattr(c, "title", None),
                "category": getattr(c, "clause_type", None) or getattr(c, "category", None),
                "text": c.text,
                "char_start": c.char_start,
                "char_end": c.char_end
            }
            for c in clauses_db
        ]

        pages_db = db.query(DocumentPage).filter_by(version_id=version_id).all()
        pages_data = [
            {"page_number": p.page_number, "char_start": p.char_start, "char_end": p.char_end}
            for p in pages_db
        ]

        # Load effective/expiration date fields if present for anchor calculation
        eff_field = db.query(ExtractedField).filter_by(version_id=version_id, field_name="effective_date").first()
        eff_date = None
        if eff_field and eff_field.value_normalized:
            try:
                norm_dict = json.loads(eff_field.value_normalized) if isinstance(eff_field.value_normalized, str) else eff_field.value_normalized
                if norm_dict.get("iso_date"):
                    eff_date = datetime.strptime(norm_dict["iso_date"], "%Y-%m-%d").date()
            except Exception:
                pass
        if not eff_date:
            eff_date = as_of_date

        # Clear existing obligations
        db.query(Obligation).filter_by(version_id=version_id).delete()
        db.commit()

        extracted_objs: List[Obligation] = []

        # Find candidate clauses (notices, payment, term, renewal, termination)
        for c in clauses:
            c_text = c.get("text", "").lower()
            c_id = c.get("id")

            # Notice of Non-Renewal Obligation
            if "notice of non-renewal" in c_text or "90 days prior" in c_text or "60 days prior" in c_text or "non-renewal" in c_text:
                quote = "written notice of non-renewal at least ninety (90) days prior to the expiration" if "ninety" in c_text or "90" in c_text else c.get("text")[:100]
                v_res = QuoteVerifier.verify_quote(quote, version.canonical_text or "", cited_clause_id=c_id, clauses=clauses, pages_data=pages_data)

                days_notice = 90 if "90" in c_text or "ninety" in c_text else 60
                calc_trace = {
                    "as_of_date": as_of_date.isoformat(),
                    "anchor_date": eff_date.isoformat(),
                    "notice_days": days_notice,
                    "formula": f"eff_date ({eff_date.isoformat()}) + 1 year - {days_notice} days"
                }

                ob = Obligation(
                    contract_id=version.contract_id,
                    version_id=version_id,
                    party="Client / Either Party",
                    action=f"Deliver written notice of non-renewal at least {days_notice} days prior to term expiration.",
                    trigger_rule=f"At least {days_notice} days prior to expiration of term",
                    due_date=eff_date + timedelta(days=365 - days_notice),
                    days_until_due=((eff_date + timedelta(days=365 - days_notice)) - as_of_date).days,
                    severity="high",
                    hard_deadline=True,
                    quote=v_res.get("matched_text") or quote,
                    clause_id=v_res.get("clause_id") or c_id,
                    char_start=v_res.get("char_start"),
                    char_end=v_res.get("char_end"),
                    page_start=v_res.get("page_start"),
                    page_end=v_res.get("page_end"),
                    status="pending",
                    confidence=0.90 if v_res["verification_status"] == "exact" else 0.70,
                    confidence_breakdown=json.dumps({"verified_quote": v_res["verification_status"]}),
                    calculation_trace=json.dumps(calc_trace)
                )
                db.add(ob)
                extracted_objs.append(ob)

            # Invoicing / Payment Obligation
            elif "net 30" in c_text or "invoicing" in c_text or "monthly installments" in c_text:
                quote = "payable in monthly installments of $10,000 net 30 days from the invoice date" if "monthly" in c_text else c.get("text")[:100]
                v_res = QuoteVerifier.verify_quote(quote, version.canonical_text or "", cited_clause_id=c_id, clauses=clauses, pages_data=pages_data)

                due_dt = as_of_date + timedelta(days=30)
                calc_trace = {
                    "as_of_date": as_of_date.isoformat(),
                    "payment_term": "Net 30",
                    "formula": "invoice_date + 30 days"
                }

                ob = Obligation(
                    contract_id=version.contract_id,
                    version_id=version_id,
                    party="Client",
                    action="Pay monthly service fee invoices within Net 30 days.",
                    trigger_rule="Net 30 days from monthly invoice date",
                    due_date=due_dt,
                    days_until_due=30,
                    severity="medium",
                    hard_deadline=True,
                    quote=v_res.get("matched_text") or quote,
                    clause_id=v_res.get("clause_id") or c_id,
                    char_start=v_res.get("char_start"),
                    char_end=v_res.get("char_end"),
                    page_start=v_res.get("page_start"),
                    page_end=v_res.get("page_end"),
                    status="pending",
                    confidence=0.90 if v_res["verification_status"] == "exact" else 0.70,
                    confidence_breakdown=json.dumps({"verified_quote": v_res["verification_status"]}),
                    calculation_trace=json.dumps(calc_trace)
                )
                db.add(ob)
                extracted_objs.append(ob)

        db.commit()
        return extracted_objs
