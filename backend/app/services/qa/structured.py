import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.extracted_field import ExtractedField
from app.models.obligation import Obligation
from app.services.obligation_extractor import ObligationExtractorService

NOT_FOUND_TEXT = "Not found in the contract."


class StructuredAnswerer:
    @staticmethod
    def answer_fields_route(
        db: Session,
        version_id: str,
        matched_fields: List[str]
    ) -> Dict[str, Any]:
        if not matched_fields:
            return {
                "answer_status": "not_found",
                "answer_text": NOT_FOUND_TEXT,
                "claims": [],
                "citations": []
            }

        target_field_name = matched_fields[0]
        field_rec = db.query(ExtractedField).filter_by(
            version_id=version_id,
            field_name=target_field_name
        ).first()

        if not field_rec or field_rec.verification_status == "not_found" or not field_rec.value_raw:
            return {
                "answer_status": "not_found",
                "answer_text": NOT_FOUND_TEXT,
                "scope_line": f"Searched contract metadata for: {target_field_name.replace('_', ' ')}.",
                "claims": [],
                "citations": []
            }

        if field_rec.verification_status == "failed":
            return {
                "answer_status": "needs_clarification",
                "answer_text": f"A value was found for {field_rec.display_label} ({field_rec.value_raw}), but its source quote could not be verified by code in the canonical contract text.",
                "claims": [],
                "citations": []
            }

        # Formulate plain English answer template
        label = field_rec.display_label
        val = field_rec.value_raw
        norm_dict = {}
        if field_rec.value_normalized:
            try:
                norm_dict = json.loads(field_rec.value_normalized) if isinstance(field_rec.value_normalized, str) else field_rec.value_normalized
            except Exception:
                pass

        if target_field_name == "effective_date" and norm_dict.get("iso_date"):
            dt_obj = datetime.strptime(norm_dict["iso_date"], "%Y-%m-%d")
            ans_text = f"The contract effective date is {dt_obj.strftime('%d %B %Y')}."
        elif target_field_name == "expiration_date" and norm_dict.get("iso_date"):
            dt_obj = datetime.strptime(norm_dict["iso_date"], "%Y-%m-%d")
            ans_text = f"The contract expires on {dt_obj.strftime('%d %B %Y')}."
        elif target_field_name == "governing_law":
            ans_text = f"This contract is governed by the laws of {val}."
        elif target_field_name == "liability_cap":
            ans_text = f"The total limitation of liability cap is {val}."
        elif target_field_name == "payment_terms":
            ans_text = f"The payment terms specified in the contract are {val}."
        else:
            ans_text = f"The {label.lower()} is {val}."

        citation = {
            "clause_id": field_rec.clause_id,
            "quote": field_rec.quote,
            "page_start": field_rec.page_start or 1,
            "char_start": field_rec.char_start,
            "char_end": field_rec.char_end
        }

        return {
            "answer_status": "answered",
            "answer_text": ans_text,
            "claims": [{"text": ans_text, "citation_indices": [1]}],
            "citations": [citation],
            "confidence": field_rec.confidence
        }

    @staticmethod
    def answer_obligations_route(
        db: Session,
        version_id: str,
    ) -> Dict[str, Any]:
        as_of_date = ObligationExtractorService.get_as_of_date()
        obligations = db.query(Obligation).filter_by(version_id=version_id).all()

        if not obligations:
            return {
                "answer_status": "not_found",
                "answer_text": NOT_FOUND_TEXT,
                "scope_line": f"Searched active obligations as of {as_of_date.strftime('%d %B %Y')}.",
                "claims": [],
                "citations": []
            }

        items_text = []
        citations = []
        for idx, ob in enumerate(obligations, 1):
            due_str = ob.due_date.strftime('%d %B %Y') if ob.due_date else 'Not specified'
            days_str = f"({ob.days_until_due} days remaining)" if ob.days_until_due is not None else ""
            items_text.append(f"{idx}. {ob.party}: {ob.action} [Due: {due_str} {days_str}]")
            if ob.quote:
                citations.append({
                    "clause_id": ob.clause_id,
                    "quote": ob.quote,
                    "page_start": ob.page_start or 1,
                    "char_start": ob.char_start,
                    "char_end": ob.char_end
                })

        ans_text = f"As of {as_of_date.strftime('%d %B %Y')}, the following active contract obligations were identified:\n" + "\n".join(items_text)

        return {
            "answer_status": "answered",
            "answer_text": ans_text,
            "claims": [{"text": ans_text, "citation_indices": list(range(1, len(citations) + 1))}],
            "citations": citations,
            "confidence": 0.90
        }
