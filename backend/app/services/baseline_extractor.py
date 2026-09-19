import re
from typing import Any, Dict, List, Optional
from app.services.field_registry import TARGET_FIELDS
from app.services.quote_verifier import QuoteVerifier


class BaselineExtractor:
    """
    Fallback deterministic regex extractor.
    Enforces Invariant E5 & E6 (never gets stuck when LLM fails).
    """

    @staticmethod
    def extract_all_fields(
        canonical_text: str,
        clauses: List[Dict[str, Any]],
        pages_data: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        results = []

        for field_def in TARGET_FIELDS:
            field_name = field_def["field_name"]
            extracted = BaselineExtractor.extract_single_field(
                field_name=field_name,
                canonical_text=canonical_text,
                clauses=clauses,
                pages_data=pages_data
            )
            results.append(extracted)

        return results

    @staticmethod
    def extract_single_field(
        field_name: str,
        canonical_text: str,
        clauses: List[Dict[str, Any]],
        pages_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        match_info = None

        if field_name == "effective_date":
            match_info = BaselineExtractor._regex_search(
                r'(?:effective\s+as\s+of|dated\s+as\s+of|effective\s+date\s*[:\s]*)\s*([A-Z][a-z]+\s+\d{1,2},\s*\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
                canonical_text, clauses
            )
        elif field_name == "expiration_date":
            match_info = BaselineExtractor._regex_search(
                r'(?:expiration\s+date|shall\s+expire\s+on|terminate\s+on)\s*[:\s]*([A-Z][a-z]+\s+\d{1,2},\s*\d{4}|\d{4}-\d{2}-\d{2})',
                canonical_text, clauses
            )
        elif field_name == "term_length":
            match_info = BaselineExtractor._regex_search(
                r'initial\s+term\s+of\s+([A-Za-z0-9\s\(\)]+?(?:years?|months?))',
                canonical_text, clauses
            )
        elif field_name == "renewal_type":
            match_info = BaselineExtractor._regex_search(
                r'(automatically\s+renew|auto-renew|successive\s+periods?)',
                canonical_text, clauses
            )
        elif field_name == "renewal_term":
            match_info = BaselineExtractor._regex_search(
                r'successive\s+([A-Za-z0-9\s\(\)]+?(?:years?|months?|periods?))',
                canonical_text, clauses
            )
        elif field_name == "notice_period_nonrenewal":
            match_info = BaselineExtractor._regex_search(
                r'([A-Za-z0-9\s\(\)]+?days?)\s+prior\s+to\s+the\s+expiration',
                canonical_text, clauses
            ) or BaselineExtractor._regex_search(
                r'notice\s+of\s+non-renewal\s+at\s+least\s+([A-Za-z0-9\s\(\)]+?days?)',
                canonical_text, clauses
            )
        elif field_name == "payment_terms":
            match_info = BaselineExtractor._regex_search(
                r'(net\s+\d+|due\s+within\s+\d+\s+days|due\s+upon\s+receipt)',
                canonical_text, clauses
            )
        elif field_name == "contract_value_or_fees":
            match_info = BaselineExtractor._regex_search(
                r'(?:service\s+fees\s+of|total\s+fees\s+of|fees\s+of)\s*(\$[0-9,]+|[0-9,]+\s+USD)',
                canonical_text, clauses
            ) or BaselineExtractor._regex_search(
                r'(\$[0-9,]{4,})',
                canonical_text, clauses
            )
        elif field_name == "liability_cap":
            match_info = BaselineExtractor._regex_search(
                r'(?:aggregate\s+liability[\s\S]*?exceed|capped\s+at)\s*(\$[0-9,]+|[0-9,]+\s+USD)',
                canonical_text, clauses
            )
        elif field_name == "termination_for_convenience":
            match_info = BaselineExtractor._regex_search(
                r'(terminate\s+(?:this\s+agreement\s+)?without\s+cause|for\s+convenience)',
                canonical_text, clauses
            )
        elif field_name == "termination_notice_period":
            match_info = BaselineExtractor._regex_search(
                r'([A-Za-z0-9\s\(\)]+?days?)\s+(?:prior\s+)?written\s+notice',
                canonical_text, clauses
            )
        elif field_name == "governing_law":
            match_info = BaselineExtractor._regex_search(
                r'(?:governed\s+by\s+and\s+construed\s+in\s+accordance\s+with\s+the\s+laws\s+of\s+the\s+State\s+of|laws\s+of\s+the\s+State\s+of)\s+([A-Z][a-z]+)',
                canonical_text, clauses
            )
        elif field_name == "parties":
            match_info = BaselineExtractor._regex_search(
                r'by\s+and\s+between\s+([A-Z][A-Za-z0-9\s,\.\'\(\)]+?)\s+and\s+([A-Z][A-Za-z0-9\s,\.\'\(\)]+?)(?:,\s*effective|\s+dated|\.)',
                canonical_text, clauses
            )

        if match_info:
            raw_val = match_info["extracted_value"]
            quote = match_info["quote"]
            cited_clause_id = match_info["clause_id"]

            v_res = QuoteVerifier.verify_quote(
                quote=quote,
                canonical_text=canonical_text,
                cited_clause_id=cited_clause_id,
                clauses=clauses,
                pages_data=pages_data
            )

            return {
                "field_name": field_name,
                "value_raw": raw_val,
                "quote": quote,
                "clause_id": v_res.get("clause_id"),
                "verification_status": v_res["verification_status"],
                "char_start": v_res["char_start"],
                "char_end": v_res["char_end"],
                "page_start": v_res["page_start"],
                "page_end": v_res["page_end"],
                "extraction_method": "regex_baseline",
                "similarity": v_res["similarity"]
            }

        # Not found fallback (Invariant E2)
        return {
            "field_name": field_name,
            "value_raw": None,
            "quote": None,
            "clause_id": None,
            "verification_status": "not_found",
            "char_start": None,
            "char_end": None,
            "page_start": None,
            "page_end": None,
            "extraction_method": "regex_baseline",
            "similarity": 0.0
        }

    @staticmethod
    def _regex_search(
        pattern: str,
        canonical_text: str,
        clauses: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        match = re.search(pattern, canonical_text, re.IGNORECASE)
        if not match:
            return None

        # Full match snippet as quote
        quote = match.group(0).strip()
        val = match.group(1).strip() if match.groups() else quote
        match_start = match.start()

        clause_id = None
        for c in clauses:
            if c["char_start"] <= match_start < c["char_end"]:
                clause_id = c.get("id") or c.get("temp_id")
                break

        return {
            "extracted_value": val,
            "quote": quote,
            "clause_id": clause_id
        }
