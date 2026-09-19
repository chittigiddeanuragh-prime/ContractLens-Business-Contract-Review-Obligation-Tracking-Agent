import re
from typing import Any, Dict, List, Optional
from app.services.field_registry import TARGET_FIELDS, FIELD_REGISTRY


class QARouter:
    @staticmethod
    def route_question(question: str) -> Dict[str, Any]:
        q_lower = question.strip().lower()

        # 1. Compare Unsupported Route
        if any(w in q_lower for w in ["what changed", "compare v1", "compare version", "difference between versions", "versus v1"]):
            return {
                "route": "compare_unsupported",
                "matched_fields": [],
                "confidence": 1.0,
                "reason": "Version comparison is unsupported in current phase"
            }

        # 2. Confidentiality & IP Clause Override
        if any(w in q_lower for w in ["confidential", "confidentiality", "intellectual property", "ip rights", "data breach", "indemnify"]):
            return {
                "route": "clauses",
                "matched_fields": [],
                "confidence": 0.95,
                "reason": "Semantic clause topic"
            }

        # 3. Check Obligations Route keywords
        if any(w in q_lower for w in ["upcoming", "due date", "what do i need to do", "when do i have to", "action required"]):
            return {
                "route": "obligations",
                "matched_fields": [],
                "confidence": 0.90,
                "reason": "Matched obligation deadline keywords"
            }

        # 4. Check Fields Route keywords
        FIELD_KEYWORDS = {
            "parties": ["party", "parties", "client", "vendor", "entered into"],
            "effective_date": ["effective date", "effective as of", "commencing"],
            "expiration_date": ["expire", "expiration", "end date", "terminate on"],
            "term_length": ["initial term", "term length", "period of"],
            "renewal_type": ["renew", "renewal", "auto-renew", "automatic"],
            "renewal_term": ["renewal period", "successive term", "renewal duration"],
            "notice_period_nonrenewal": ["non-renewal", "notice of non-renewal", "nonrenewal"],
            "payment_terms": ["payment term", "net 30", "net 45", "invoicing", "payable"],
            "contract_value_or_fees": ["annual fee", "contract value", "total fee", "fees", "cost"],
            "liability_cap": ["liability cap", "limitation of liability", "aggregate liability"],
            "termination_for_convenience": ["termination for convenience", "without cause", "convenience"],
            "termination_notice_period": ["termination notice", "notice to terminate"],
            "governing_law": ["governing law", "jurisdiction", "laws of", "state of"]
        }

        matched_fields = []
        for f_name, keywords in FIELD_KEYWORDS.items():
            if any(kw in q_lower for kw in keywords):
                matched_fields.append(f_name)

        is_semantic_clause = any(w in q_lower for w in ["why", "what happens", "how", "explain", "describe", "consequence", "reason"])

        if matched_fields and is_semantic_clause:
            return {
                "route": "hybrid",
                "matched_fields": matched_fields,
                "confidence": 0.90,
                "reason": "Matched key field and semantic question"
            }

        if matched_fields:
            return {
                "route": "fields",
                "matched_fields": matched_fields,
                "confidence": 0.95,
                "reason": f"Matched field keywords for {matched_fields}"
            }

        # 5. Default Semantic Clauses Route
        return {
            "route": "clauses",
            "matched_fields": [],
            "confidence": 0.85,
            "reason": "Semantic contract clause query"
        }
