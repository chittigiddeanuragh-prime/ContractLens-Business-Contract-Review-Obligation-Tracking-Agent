from typing import Any, Dict, List, Optional
from app.services.quote_verifier import QuoteVerifier

NOT_FOUND_TEXT = "Not found in the contract."


class QACitationVerifier:
    @staticmethod
    def verify_and_assemble_answer(
        claims: List[Dict[str, Any]],
        canonical_text: str,
        clauses: List[Dict[str, Any]],
        pages_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Enforces Invariant Q1: Every factual statement in an answer must be backed by at least one
        citation whose quote was verified by CODE. Statements with unverified citations are removed.
        If no claims survive -> exact NOT_FOUND_TEXT.
        """
        verified_claims = []
        all_verified_citations = []
        citation_index_counter = 1

        for claim in claims:
            claim_text = claim.get("text", "").strip()
            raw_citations = claim.get("citations", [])
            verified_claim_citations = []

            for cit in raw_citations:
                raw_quote = cit.get("quote")
                cited_clause_id = cit.get("clause_id")

                v_res = QuoteVerifier.verify_quote(
                    quote=raw_quote,
                    canonical_text=canonical_text,
                    cited_clause_id=cited_clause_id,
                    clauses=clauses,
                    pages_data=pages_data
                )

                if v_res["verification_status"] in ("exact", "outside_clause", "fuzzy"):
                    assembled_cit = {
                        "citation_index": citation_index_counter,
                        "clause_id": v_res.get("clause_id") or cited_clause_id,
                        "quote": v_res.get("matched_text") or raw_quote,
                        "char_start": v_res.get("char_start"),
                        "char_end": v_res.get("char_end"),
                        "page_start": v_res.get("page_start", 1),
                        "page_end": v_res.get("page_end", 1),
                        "verification_status": v_res["verification_status"]
                    }
                    verified_claim_citations.append(assembled_cit)
                    all_verified_citations.append(assembled_cit)
                    citation_index_counter += 1

            # Invariant Q1: Claim MUST have at least 1 verified citation to survive
            if verified_claim_citations:
                verified_claims.append({
                    "text": claim_text,
                    "citations": verified_claim_citations
                })

        # If zero claims survived verification -> refusal
        if not verified_claims:
            return {
                "answer_status": "not_found",
                "answer_text": NOT_FOUND_TEXT,
                "claims": [],
                "citations": [],
                "diagnostic": "All claims failed code citation verification"
            }

        # Build clean answer text with inline citation markers
        answer_parts = []
        for claim in verified_claims:
            cit_markers = " ".join([f"[{c['citation_index']}]" for c in claim["citations"]])
            answer_parts.append(f"{claim['text']} {cit_markers}".strip())

        final_answer_text = "\n\n".join(answer_parts)

        return {
            "answer_status": "answered" if len(verified_claims) == len(claims) else "partially_answered",
            "answer_text": final_answer_text,
            "claims": verified_claims,
            "citations": all_verified_citations,
            "dropped_claim_count": len(claims) - len(verified_claims)
        }
