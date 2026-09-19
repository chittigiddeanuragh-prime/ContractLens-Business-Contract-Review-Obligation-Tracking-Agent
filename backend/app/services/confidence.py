from typing import Any, Dict, List, Optional
from app.services.field_registry import get_field_def


class ConfidenceCalculator:
    """
    Transparent confidence scoring engine for extracted contract fields.
    Produces numeric score (0.0 to 1.0), review_status, and full breakdown JSON.
    """

    @staticmethod
    def calculate_confidence(
        field_name: str,
        verification_res: Dict[str, Any],
        cited_clause_type: Optional[str] = None,
        normalized_success: bool = False,
        llm_prob: float = 0.95,
        baseline_match: bool = False,
        word_digit_mismatch_warning: Optional[str] = None,
        has_conflicts: bool = False,
        extraction_method: str = "llm_group"
    ) -> Dict[str, Any]:
        
        field_def = get_field_def(field_name)
        target_clause_types = field_def.get("target_clause_types", []) if field_def else []

        score = 0.0
        breakdown = {
            "quote_match": 0.0,
            "clause_type_match": 0.0,
            "normalized_success": 0.0,
            "llm_prob": 0.0,
            "regex_match": 0.0,
            "penalties": [],
            "final_score": 0.0
        }

        v_status = verification_res.get("verification_status", "failed")

        # 1. Quote match (+0.40 exact, +0.30 outside clause, +0.20 fuzzy)
        if v_status == "exact":
            breakdown["quote_match"] = 0.40
        elif v_status == "outside_clause":
            breakdown["quote_match"] = 0.30
        elif v_status == "fuzzy":
            breakdown["quote_match"] = 0.20
        else:
            breakdown["quote_match"] = 0.00

        # 2. Cited clause type matches target category (+0.25)
        if cited_clause_type and cited_clause_type in target_clause_types:
            breakdown["clause_type_match"] = 0.25
        elif cited_clause_type == "Preamble" and field_name in ("parties", "effective_date"):
            breakdown["clause_type_match"] = 0.25

        # 3. Deterministic normalizer succeeded (+0.15)
        if normalized_success:
            breakdown["normalized_success"] = 0.15

        # 4. LLM probability / confidence signal (+0.10)
        breakdown["llm_prob"] = round(min(0.10, llm_prob * 0.10), 2)

        # 5. Regex baseline match (+0.10)
        if baseline_match:
            breakdown["regex_match"] = 0.10

        subtotal = sum([
            breakdown["quote_match"],
            breakdown["clause_type_match"],
            breakdown["normalized_success"],
            breakdown["llm_prob"],
            breakdown["regex_match"]
        ])

        score = subtotal

        # Penalties & Caps
        if v_status == "failed":
            score = min(score, 0.15)
            breakdown["penalties"].append("Unverified/Hallucinated quote (capped score to 0.15)")

        if word_digit_mismatch_warning:
            score -= 0.30
            breakdown["penalties"].append(word_digit_mismatch_warning)

        if has_conflicts:
            score -= 0.20
            breakdown["penalties"].append("Conflicting value found in another clause (-0.20 penalty)")

        final_score = max(0.0, min(1.0, round(score, 2)))
        breakdown["final_score"] = final_score

        # Determine review status
        if v_status == "failed" or v_status == "not_found":
            review_status = "not_found" if v_status == "not_found" else "needs_review"
        elif final_score >= 0.85 and v_status in ("exact", "outside_clause"):
            review_status = "verified"
        elif final_score >= 0.50:
            review_status = "needs_review"
        else:
            review_status = "low_confidence"

        return {
            "confidence": final_score,
            "review_status": review_status,
            "confidence_breakdown": breakdown
        }
