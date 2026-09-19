import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.llm.client import LLMClient
from app.llm.safety import wrap_untrusted
from app.models.contract import ContractVersion
from app.models.clause import Clause
from app.models.defined_term import DefinedTerm
from app.models.document_page import DocumentPage
from app.models.extracted_field import ExtractedField
from app.services.field_registry import EXTRACTION_GROUPS, TARGET_FIELDS, get_field_def
from app.services.field_retriever import FieldRetriever
from app.services.quote_verifier import QuoteVerifier
from app.services.baseline_extractor import BaselineExtractor
from app.services.confidence import ConfidenceCalculator
from app.services.normalizers import (
    normalize_date,
    normalize_duration,
    normalize_money,
    normalize_payment_terms,
    normalize_renewal_type,
    check_word_digit_mismatch
)

logger = logging.getLogger(__name__)


class FieldExtractorAgent:
    """
    LLM Field Extraction Agent.
    Strictly enforces Non-Negotiable Invariants:
      E1: Quotes verified by CODE in canonical text (never trust LLM offsets/pages).
      E2: Store 'not_found' when missing (never fabricate values).
      E3: All LLM context wrapped with wrap_untrusted().
      E4: Dates, durations, money normalized by Python code.
      E5/E6: Regex baseline fallback if LLM fails or is unavailable.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.llm_client = LLMClient()

    def extract_fields_for_version(self, version_id: str) -> List[ExtractedField]:
        version = self.db.query(ContractVersion).filter_by(id=version_id).first()
        if not version:
            raise ValueError(f"ContractVersion {version_id} not found")

        # Load clauses, defined terms, pages
        clauses_db = self.db.query(Clause).filter_by(version_id=version_id).order_by(Clause.char_start).all()
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

        pages_db = self.db.query(DocumentPage).filter_by(version_id=version_id).order_by(DocumentPage.page_number).all()
        pages_data = [
            {
                "page_number": p.page_number,
                "char_start": p.char_start,
                "char_end": p.char_end
            }
            for p in pages_db
        ]

        defined_terms_db = self.db.query(DefinedTerm).filter_by(version_id=version_id).all()
        defined_terms = [
            {"term": t.term, "definition": t.definition}
            for t in defined_terms_db
        ]

        canonical_text = version.canonical_text or ""

        # Remove previous extracted fields for clean update
        self.db.query(ExtractedField).filter_by(version_id=version_id).delete()
        self.db.commit()

        extracted_records: List[ExtractedField] = []

        # Process each group
        for group_key, group_def in EXTRACTION_GROUPS.items():
            fields_in_group = group_def["fields"]
            group_results = self._extract_group(
                group_key=group_key,
                group_def=group_def,
                canonical_text=canonical_text,
                clauses=clauses,
                defined_terms=defined_terms,
                pages_data=pages_data,
                file_hash=version.file_hash
            )

            for field_name in fields_in_group:
                field_data = group_results.get(field_name) if isinstance(group_results, dict) else None
                field_rec = self._build_extracted_field_record(
                    contract_id=version.contract_id,
                    version_id=version_id,
                    field_name=field_name,
                    field_data=field_data,
                    canonical_text=canonical_text,
                    clauses=clauses,
                    pages_data=pages_data
                )
                self.db.add(field_rec)
                extracted_records.append(field_rec)

        self.db.commit()
        return extracted_records

    def _extract_group(
        self,
        group_key: str,
        group_def: Dict[str, Any],
        canonical_text: str,
        clauses: List[Dict[str, Any]],
        defined_terms: List[Dict[str, Any]],
        pages_data: List[Dict[str, Any]],
        file_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs LLM extraction for one field group.
        Falls back to regex baseline if LLM fails (Invariant E5 & E6).
        """
        retrieved_context = FieldRetriever.build_group_context(
            group_id=group_key,
            clauses=clauses,
            canonical_text=canonical_text,
            defined_terms=defined_terms
        )

        wrapped_context = wrap_untrusted(retrieved_context)

        field_descriptions = "\n".join([
            f"- {f_name}: {get_field_def(f_name)['description']}"
            for f_name in group_def["fields"]
        ])

        system_prompt = (
            "You are a legal contract field extraction assistant. Extract specified key fields from contract text.\n"
            "CRITICAL RULES:\n"
            "1. Only return quotes that EXACTLY exist in the provided text.\n"
            "2. If a field is not present in the text, set value to null and quote to null.\n"
            "3. DO NOT fabricate or assume values.\n"
            "4. For each field, return a JSON object with keys: 'value_raw', 'quote', 'cited_clause_id'.\n"
            "5. Format your output strictly as a JSON object with field names as top-level keys."
        )

        user_prompt = (
            f"Target Fields to Extract:\n{field_descriptions}\n\n"
            f"Contract Context:\n{wrapped_context}\n\n"
            "Respond ONLY with a valid JSON object."
        )

        try:
            # Run async LLMClient inside sync context safely
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                # In active loop (e.g. FastAPI async endpoint thread)
                coro = LLMClient.run(
                    task=f"extract_{group_key}",
                    system=system_prompt,
                    user=user_prompt,
                    file_hash=file_hash,
                    db=self.db
                )
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, coro)
                    parsed_data = future.result(timeout=15)
            else:
                parsed_data = loop.run_until_complete(
                    LLMClient.run(
                        task=f"extract_{group_key}",
                        system=system_prompt,
                        user=user_prompt,
                        file_hash=file_hash,
                        db=self.db
                    )
                )

            return parsed_data
        except Exception as e:
            logger.warning(f"LLM extraction failed for group {group_key}: {e}. Falling back to baseline regex.")
            # Fallback for group fields using baseline regex (Invariant E5 & E6)
            fallback_res = {}
            for f_name in group_def["fields"]:
                baseline_item = BaselineExtractor.extract_single_field(
                    field_name=f_name,
                    canonical_text=canonical_text,
                    clauses=clauses,
                    pages_data=pages_data
                )
                fallback_res[f_name] = {
                    "value_raw": baseline_item["value_raw"],
                    "quote": baseline_item["quote"],
                    "cited_clause_id": baseline_item["clause_id"],
                    "extraction_method": "regex_baseline"
                }
            return fallback_res

    def _build_extracted_field_record(
        self,
        contract_id: str,
        version_id: str,
        field_name: str,
        field_data: Optional[Dict[str, Any]],
        canonical_text: str,
        clauses: List[Dict[str, Any]],
        pages_data: List[Dict[str, Any]]
    ) -> ExtractedField:
        field_def = get_field_def(field_name) or {}

        if not field_data or not field_data.get("value_raw") and not field_data.get("quote"):
            # Try baseline fallback before marking not_found
            baseline_item = BaselineExtractor.extract_single_field(
                field_name=field_name,
                canonical_text=canonical_text,
                clauses=clauses,
                pages_data=pages_data
            )
            if baseline_item["value_raw"]:
                field_data = {
                    "value_raw": baseline_item["value_raw"],
                    "quote": baseline_item["quote"],
                    "cited_clause_id": baseline_item["clause_id"],
                    "extraction_method": "regex_baseline"
                }
            else:
                return ExtractedField(
                    contract_id=contract_id,
                    version_id=version_id,
                    field_name=field_name,
                    display_label=field_def.get("display_label", field_name),
                    value_type=field_def.get("value_type", "string"),
                    value="Not Found",
                    value_raw=None,
                    value_normalized=None,
                    quote=None,
                    verification_status="not_found",
                    review_status="not_found",
                    confidence=0.0,
                    confidence_breakdown=json.dumps({"status": "not_found"}),
                    extraction_method="none"
                )

        value_raw = field_data.get("value_raw")
        if isinstance(value_raw, list):
            value_raw = ", ".join([str(v) for v in value_raw])
        elif value_raw is not None:
            value_raw = str(value_raw)

        quote = field_data.get("quote")
        cited_clause_id = field_data.get("cited_clause_id")
        extraction_method = field_data.get("extraction_method", "llm_group")

        # 1. CODE Verification of Quote in Canonical Text (Invariant E1)
        v_res = QuoteVerifier.verify_quote(
            quote=quote,
            canonical_text=canonical_text,
            cited_clause_id=cited_clause_id,
            clauses=clauses,
            pages_data=pages_data
        )

        # 2. Deterministic Normalization (Invariant E4)
        val_norm = None
        norm_success = False
        value_type = field_def.get("value_type", "string")

        if value_type == "date":
            val_norm_str, _ = normalize_date(value_raw)
            if val_norm_str:
                val_norm = {"iso_date": val_norm_str}
                norm_success = True
        elif value_type == "duration":
            val_norm = normalize_duration(value_raw)
            norm_success = bool(val_norm.get("normalized_text"))
        elif value_type == "money":
            val_norm = normalize_money(value_raw)
            norm_success = bool(val_norm.get("amount"))
        elif value_type == "payment_terms":
            val_norm = normalize_payment_terms(value_raw)
            norm_success = bool(val_norm.get("normalized"))
        elif value_type == "enum":
            norm_str = normalize_renewal_type(value_raw)
            val_norm = {"enum_value": norm_str}
            norm_success = norm_str != "not_specified"
        else:
            val_norm = {"text": value_raw}
            norm_success = True

        # Check word/digit agreement
        word_digit_warning = check_word_digit_mismatch(quote or "") or check_word_digit_mismatch(value_raw or "")

        # 3. Check regex baseline match for cross-checking
        baseline_item = BaselineExtractor.extract_single_field(
            field_name=field_name,
            canonical_text=canonical_text,
            clauses=clauses,
            pages_data=pages_data
        )
        baseline_match = bool(baseline_item["value_raw"] and v_res["verification_status"] in ("exact", "outside_clause"))

        # Find cited clause type
        cited_clause_type = None
        if v_res.get("clause_id"):
            for c in clauses:
                if c.get("id") == v_res["clause_id"] or c.get("temp_id") == v_res["clause_id"]:
                    cited_clause_type = c.get("category")
                    break

        # 4. Confidence Score Calculation
        conf_data = ConfidenceCalculator.calculate_confidence(
            field_name=field_name,
            verification_res=v_res,
            cited_clause_type=cited_clause_type,
            normalized_success=norm_success,
            llm_prob=0.95,
            baseline_match=baseline_match,
            word_digit_mismatch_warning=word_digit_warning,
            has_conflicts=False,
            extraction_method=extraction_method
        )

        display_val = value_raw or "Not Found"
        if val_norm and isinstance(val_norm, dict):
            if val_norm.get("iso_date"):
                display_val = val_norm["iso_date"]
            elif val_norm.get("normalized_text"):
                display_val = val_norm["normalized_text"]
            elif val_norm.get("normalized"):
                display_val = val_norm["normalized"]

        return ExtractedField(
            contract_id=contract_id,
            version_id=version_id,
            field_name=field_name,
            display_label=field_def.get("display_label", field_name),
            value_type=value_type,
            value=display_val,
            value_raw=value_raw,
            value_normalized=json.dumps(val_norm) if val_norm else None,
            quote=v_res.get("matched_text") or quote,
            char_start=v_res.get("char_start"),
            char_end=v_res.get("char_end"),
            page_start=v_res.get("page_start"),
            page_end=v_res.get("page_end"),
            clause_id=v_res.get("clause_id"),
            verification_status=v_res["verification_status"],
            review_status=conf_data["review_status"],
            confidence=conf_data["confidence"],
            confidence_breakdown=json.dumps(conf_data["confidence_breakdown"]),
            extraction_method=extraction_method
        )
