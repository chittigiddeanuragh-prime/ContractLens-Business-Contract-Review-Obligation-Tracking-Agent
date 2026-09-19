from typing import Any, Dict, List, Optional


class QAConfidenceCalculator:
    @staticmethod
    def calculate_qa_confidence(
        llm_confidence: float = 0.90,
        answer_status: str = "answered",
        citations: List[Dict[str, Any]] = None,
        dropped_claims: int = 0,
        retrieval_score: float = 0.5,
        retrieval_coverage: float = 0.5
    ) -> Dict[str, Any]:
        
        score = min(llm_confidence, 0.90)
        breakdown = {
            "base_score": score,
            "exact_citations": 0.0,
            "fuzzy_citations": 0.0,
            "outside_clause_citations": 0.0,
            "dropped_claims_penalty": 0.0,
            "retrieval_threshold_penalty": 0.0,
            "status_penalty": 0.0,
            "final_score": 0.0
        }

        citations = citations or []
        has_fuzzy = any(c.get("verification_status") == "fuzzy" for c in citations)
        has_outside = any(c.get("verification_status") == "outside_clause" for c in citations)
        all_exact = len(citations) > 0 and all(c.get("verification_status") == "exact" for c in citations)

        if all_exact:
            breakdown["exact_citations"] = 0.10
            score += 0.10
        if has_fuzzy:
            breakdown["fuzzy_citations"] = -0.10
            score -= 0.10
        if has_outside:
            breakdown["outside_clause_citations"] = -0.25
            score -= 0.25

        if dropped_claims > 0:
            breakdown["dropped_claims_penalty"] = -0.20
            score -= 0.20

        if retrieval_score < 0.2 or retrieval_coverage < 0.3:
            breakdown["retrieval_threshold_penalty"] = -0.15
            score -= 0.15

        if answer_status == "partially_answered":
            breakdown["status_penalty"] = -0.10
            score -= 0.10

        final_score = max(0.0, min(1.0, round(score, 2)))
        breakdown["final_score"] = final_score

        if final_score >= 0.80:
            band = "high"
        elif final_score >= 0.50:
            band = "medium"
        else:
            band = "low"

        return {
            "confidence": final_score,
            "confidence_band": band,
            "confidence_breakdown": breakdown
        }
