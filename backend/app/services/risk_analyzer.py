import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.contract import ContractVersion
from app.models.clause import Clause
from app.models.extracted_field import ExtractedField
from app.models.document_page import DocumentPage
from app.models.risk import RiskItem
from app.models.audit_log import AuditLog
from app.services.quote_verifier import QuoteVerifier
from app.llm.client import LLMClient

logger = logging.getLogger(__name__)


class RiskAnalyzerService:
    """
    Service for analyzing contract risks, anomalies, and deviations from standard market terms.
    All citations are verified by CODE against the canonical text (Invariant E1).
    """

    @staticmethod
    def analyze_risks_for_version(db: Session, version_id: str) -> Dict[str, Any]:
        version = db.query(ContractVersion).filter_by(id=version_id).first()
        if not version:
            return {
                "overall_risk_score": 0.0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "anomaly_count": 0,
                "risk_items": []
            }

        # Clear existing risk items for this version
        db.query(RiskItem).filter_by(version_id=version_id).delete()
        db.commit()

        canonical_text = version.canonical_text or ""
        doc_lower = canonical_text.lower()

        # Load clauses and pages for quote verification
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

        # Load extracted fields for additional context
        fields_db = db.query(ExtractedField).filter_by(version_id=version_id).all()
        fields_map = {f.field_name: f for f in fields_db}

        detected_risks: List[Dict[str, Any]] = []

        # 1. Rule-Based Risk & Anomaly Scanning
        # ----------------------------------------------------
        # Rule 1: Unlimited Liability or Missing Limitation Cap
        liab_field = fields_map.get("limitation_of_liability")
        if not liab_field or liab_field.verification_status == "not_found" or "unlimited" in (liab_field.value or "").lower():
            # Find relevant liability clause text for citation
            liab_clause = next((c for c in clauses if "liability" in (c.get("title") or "").lower() or "limitation of liability" in (c.get("category") or "").lower()), None)
            quote_text = liab_clause["text"][:200] if liab_clause else canonical_text[:200]
            detected_risks.append({
                "title": "Uncapped or Unlimited Liability Risk",
                "category": "liability",
                "severity": "critical",
                "score": 9.5,
                "description": "The contract does not specify a standard financial cap on liability or contains unlimited liability provisions.",
                "recommendation": "Negotiate a standard cap on liability (e.g. 1x - 2x annual contract fees).",
                "is_anomaly": True,
                "quote": quote_text
            })

        # Rule 2: Automatic Renewal with Short Opt-Out Notice Window
        auto_renew_field = fields_map.get("auto_renewal")
        notice_field = fields_map.get("notice_period_for_non_renewal")
        if auto_renew_field and (auto_renew_field.value or "").lower() == "true":
            renew_clause = next((c for c in clauses if "renew" in (c.get("title") or "").lower() or "term" in (c.get("title") or "").lower()), None)
            quote_text = renew_clause["text"][:200] if renew_clause else "contract renews automatically"
            
            notice_val = notice_field.value if notice_field else ""
            is_short = any(s in notice_val.lower() for s in ["10", "15", "short", "immediate"])
            detected_risks.append({
                "title": "Automatic Renewal & Renewal Lock-In",
                "category": "termination",
                "severity": "high" if is_short else "medium",
                "score": 7.5 if is_short else 5.5,
                "description": f"Contract automatically renews. Non-renewal notice required: {notice_val or 'See renewal terms'}.",
                "recommendation": "Calendar non-renewal notice deadline immediately or require explicit mutual renewal.",
                "is_anomaly": True if is_short else False,
                "quote": quote_text
            })

        # Rule 3: Broad Unilateral Indemnification
        indem_clause = next((c for c in clauses if "indemnif" in c.get("text", "").lower()), None)
        if indem_clause:
            quote_text = indem_clause["text"][:250]
            is_broad = "hold harmless" in quote_text.lower() or "all claims" in quote_text.lower()
            detected_risks.append({
                "title": "Broad Indemnification Obligations",
                "category": "indemnification",
                "severity": "high" if is_broad else "medium",
                "score": 7.0 if is_broad else 5.0,
                "description": "Indemnification clause imposes broad defense and hold-harmless obligations.",
                "recommendation": "Ensure indemnification is strictly limited to third-party IP infringement or gross negligence.",
                "is_anomaly": is_broad,
                "quote": quote_text
            })

        # Rule 4: Short Payment Terms or Late Payment Penalties
        pay_field = fields_map.get("payment_terms")
        if pay_field and pay_field.verification_status != "not_found":
            pay_val = pay_field.value.lower()
            if any(s in pay_val for s in ["10 days", "15 days", "immediate", "upon receipt"]):
                detected_risks.append({
                    "title": "Aggressive Payment Window",
                    "category": "payment_terms",
                    "severity": "medium",
                    "score": 4.5,
                    "description": f"Payment terms are unusually short ({pay_field.value}). Standard baseline is Net 30/60.",
                    "recommendation": "Request Net 30 payment terms.",
                    "is_anomaly": True,
                    "quote": pay_field.quote or pay_field.value
                })

        # Rule 5: Termination for Convenience Asymmetry
        term_conv_field = fields_map.get("termination_for_convenience")
        if term_conv_field and (term_conv_field.value or "").lower() == "false":
            detected_risks.append({
                "title": "No Termination for Convenience",
                "category": "termination",
                "severity": "medium",
                "score": 5.0,
                "description": "Neither party can terminate the contract early without cause/material breach.",
                "recommendation": "Add mutual 30-day notice termination for convenience clause.",
                "is_anomaly": False,
                "quote": term_conv_field.quote or "termination for convenience not permitted"
            })

        # Rule 6: Governing Law / Non-Standard Venue
        law_field = fields_map.get("governing_law")
        if law_field and law_field.verification_status != "not_found":
            law_val = law_field.value
            detected_risks.append({
                "title": f"Governing Law: {law_val}",
                "category": "compliance",
                "severity": "low",
                "score": 2.5,
                "description": f"Contract is governed by the laws of {law_val}.",
                "recommendation": "Verify local counsel representation for this jurisdiction if disputes arise.",
                "is_anomaly": False,
                "quote": law_field.quote or law_val
            })

        # 2. LLM Risk Analysis Enrichment (if available)
        # ----------------------------------------------------
        try:
            llm_prompt = (
                f"You are a legal risk assessment expert analyzing a contract.\n"
                f"Contract Text Excerpt:\n{canonical_text[:4000]}\n\n"
                f"Identify 1-3 additional specific high-risk terms or anomalies. Return ONLY JSON:\n"
                f"[\n"
                f"  {{\n"
                f"    \"title\": \"Short Title\",\n"
                f"    \"category\": \"liability|termination|indemnification|data_privacy|payment_terms|compliance|ip_rights\",\n"
                f"    \"severity\": \"critical|high|medium|low\",\n"
                f"    \"score\": 6.5,\n"
                f"    \"description\": \"Why it is risky\",\n"
                f"    \"recommendation\": \"How to fix\",\n"
                f"    \"is_anomaly\": false,\n"
                f"    \"quote\": \"exact verbatim quote from text\"\n"
                f"  }}\n"
                f"]"
            )
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                import concurrent.futures
                coro = LLMClient.run(
                    task="risk_analysis",
                    system="You are a legal risk assessment expert.",
                    user=llm_prompt,
                    file_hash=version.file_hash,
                    db=db
                )
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, coro)
                    raw_llm_res = future.result(timeout=10)
            else:
                raw_llm_res = loop.run_until_complete(
                    LLMClient.run(
                        task="risk_analysis",
                        system="You are a legal risk assessment expert.",
                        user=llm_prompt,
                        file_hash=version.file_hash,
                        db=db
                    )
                )

            if isinstance(raw_llm_res, str):
                json_match = re.search(r'\[.*\]', raw_llm_res, re.DOTALL)
                if json_match:
                    llm_items = json.loads(json_match.group(0))
                    for item in llm_items:
                        if isinstance(item, dict) and item.get("quote"):
                            detected_risks.append(item)
            elif isinstance(raw_llm_res, list):
                for item in raw_llm_res:
                    if isinstance(item, dict) and item.get("quote"):
                        detected_risks.append(item)
        except Exception as e:
            logger.warning(f"LLM risk analysis unavailable or failed: {e}")

        # 3. Grounded Citation Verification (Invariant E1)
        # ----------------------------------------------------
        risk_models: List[RiskItem] = []
        crit_c = 0
        high_c = 0
        med_c = 0
        low_c = 0
        anomaly_c = 0

        for r in detected_risks:
            raw_quote = r.get("quote", "")
            ver_res = QuoteVerifier.verify_quote(
                quote=raw_quote,
                canonical_text=canonical_text,
                clauses=clauses,
                pages_data=pages_data
            )

            sev = (r.get("severity") or "medium").lower()
            if sev not in ("critical", "high", "medium", "low"):
                sev = "medium"

            if sev == "critical":
                crit_c += 1
            elif sev == "high":
                high_c += 1
            elif sev == "medium":
                med_c += 1
            else:
                low_c += 1

            if r.get("is_anomaly"):
                anomaly_c += 1

            is_verified = ver_res["verification_status"] != "failed"
            status = "verified" if is_verified else "unverified"

            risk_item = RiskItem(
                contract_id=version.contract_id,
                version_id=version_id,
                title=r.get("title", "Contract Risk"),
                category=r.get("category", "general"),
                severity=sev,
                score=float(r.get("score", 5.0)),
                description=r.get("description", ""),
                recommendation=r.get("recommendation", ""),
                is_anomaly=bool(r.get("is_anomaly", False)),
                quote=ver_res["matched_text"] if is_verified else raw_quote,
                clause_id=ver_res["clause_id"],
                char_start=ver_res["char_start"],
                char_end=ver_res["char_end"],
                page_start=ver_res["page_start"],
                page_end=ver_res["page_end"],
                status=status,
                confidence=1.0 if is_verified else 0.6,
                confidence_breakdown=json.dumps({"verification_status": ver_res["verification_status"], "similarity": ver_res.get("similarity", 0.0)})
            )
            db.add(risk_item)
            risk_models.append(risk_item)

        db.commit()

        # 4. Compute Overall Risk Score (0-100)
        # ----------------------------------------------------
        raw_score = (crit_c * 30.0) + (high_c * 15.0) + (med_c * 5.0) + (low_c * 1.0) + (anomaly_c * 5.0)
        overall_risk_score = round(min(100.0, raw_score), 1)

        # Audit Log
        audit_rec = AuditLog(
            user_id="system",
            action="risk_assessment",
            entity_type="contract_version",
            entity_id=version_id,
            changes_after=json.dumps({
                "overall_risk_score": overall_risk_score,
                "risk_count": len(risk_models),
                "critical_count": crit_c,
                "anomaly_count": anomaly_c
            })
        )
        db.add(audit_rec)
        db.commit()

        return {
            "overall_risk_score": overall_risk_score,
            "critical_count": crit_c,
            "high_count": high_c,
            "medium_count": med_c,
            "low_count": low_c,
            "anomaly_count": anomaly_c,
            "risk_items": [
                {
                    "id": r.id,
                    "title": r.title,
                    "category": r.category,
                    "severity": r.severity,
                    "score": r.score,
                    "description": r.description,
                    "recommendation": r.recommendation,
                    "is_anomaly": r.is_anomaly,
                    "quote": r.quote,
                    "clause_id": r.clause_id,
                    "char_start": r.char_start,
                    "char_end": r.char_end,
                    "page_start": r.page_start,
                    "page_end": r.page_end,
                    "status": r.status,
                    "confidence": r.confidence
                }
                for r in risk_models
            ]
        }

    @staticmethod
    def get_risks_for_version(db: Session, version_id: str) -> Dict[str, Any]:
        risk_models = db.query(RiskItem).filter_by(version_id=version_id).all()

        crit_c = sum(1 for r in risk_models if r.severity == "critical")
        high_c = sum(1 for r in risk_models if r.severity == "high")
        med_c = sum(1 for r in risk_models if r.severity == "medium")
        low_c = sum(1 for r in risk_models if r.severity == "low")
        anomaly_c = sum(1 for r in risk_models if r.is_anomaly)

        raw_score = (crit_c * 30.0) + (high_c * 15.0) + (med_c * 5.0) + (low_c * 1.0) + (anomaly_c * 5.0)
        overall_risk_score = round(min(100.0, raw_score), 1)

        return {
            "overall_risk_score": overall_risk_score,
            "critical_count": crit_c,
            "high_count": high_c,
            "medium_count": med_c,
            "low_count": low_c,
            "anomaly_count": anomaly_c,
            "risk_items": [
                {
                    "id": r.id,
                    "title": r.title,
                    "category": r.category,
                    "severity": r.severity,
                    "score": r.score,
                    "description": r.description,
                    "recommendation": r.recommendation,
                    "is_anomaly": r.is_anomaly,
                    "quote": r.quote,
                    "clause_id": r.clause_id,
                    "char_start": r.char_start,
                    "char_end": r.char_end,
                    "page_start": r.page_start,
                    "page_end": r.page_end,
                    "status": r.status,
                    "confidence": r.confidence
                }
                for r in risk_models
            ]
        }
