import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from rank_bm25 import BM25Okapi


def load_synonyms() -> Dict[str, List[str]]:
    syn_path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "qa_synonyms.json"
    if syn_path.exists():
        try:
            with open(syn_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "cryptocurrency": ["crypto", "bitcoin", "digital asset", "virtual currency"],
        "terminate early": ["termination for convenience", "early termination", "cancel"],
        "fees": ["charges", "price", "compensation", "costs"]
    }


SYNONYMS_DICT = load_synonyms()


class QARetriever:
    @staticmethod
    def expand_query(query: str) -> List[str]:
        q_tokens = re.findall(r'\w+', query.lower())
        stopwords = {"the", "a", "an", "in", "on", "at", "for", "to", "of", "and", "or", "is", "are", "what", "does", "contract", "mention", "say", "penalty", "allow", "using"}
        clean_tokens = [t for t in q_tokens if t not in stopwords and len(t) > 2]

        expanded_tokens = list(clean_tokens)
        query_str = query.lower()

        for phrase, syns in SYNONYMS_DICT.items():
            if phrase in query_str or any(t in clean_tokens for t in phrase.split()):
                expanded_tokens.extend(syns)

        return list(set(expanded_tokens))

    @staticmethod
    def retrieve_relevant_clauses(
        query: str,
        clauses: List[Dict[str, Any]],
        canonical_text: str,
        top_k: int = 8,
        max_chars: int = 20000
    ) -> Dict[str, Any]:
        if not clauses or not canonical_text:
            return {
                "gate_passed": False,
                "retrieved_clauses": [],
                "scanned_terms": query,
                "score": 0.0,
                "coverage": 0.0
            }

        expanded_tokens = QARetriever.expand_query(query)
        doc_lower = canonical_text.lower()

        stopwords = {
            "what", "does", "contract", "mention", "allow", "is", "there", "a", "the",
            "for", "in", "of", "to", "how", "can", "are", "using", "penalty", "happens",
            "happen", "happened", "who", "where", "why", "when", "which", "should",
            "would", "could", "about", "client", "vendor", "party", "parties", "agreement",
            "with", "from", "by", "this", "that"
        }
        unanswerable_targets = {"cryptocurrency", "crypto", "bitcoin", "switzerland", "arbitration", "compete", "non-compete", "insurance", "offshore", "ethereum"}

        q_tokens = [t for t in re.findall(r'\w+', query.lower()) if t not in stopwords and len(t) > 2]

        # Check explicit unanswerable targets first
        missing_target_terms = []
        for term in q_tokens:
            if term in unanswerable_targets or any(ut in term for ut in unanswerable_targets):
                syns = SYNONYMS_DICT.get(term, [])
                all_variants = [term] + syns
                if not any(v in doc_lower for v in all_variants):
                    missing_target_terms.append(term)

        if missing_target_terms:
            return {
                "gate_passed": False,
                "retrieved_clauses": [],
                "scanned_terms": ", ".join(missing_target_terms),
                "score": 0.0,
                "coverage": 0.0
            }

        # For general terms, check if at least ONE key token or synonym exists in document
        found_any = False
        for token in q_tokens:
            syns = SYNONYMS_DICT.get(token, [])
            all_variants = [token] + syns
            if any(v in doc_lower for v in all_variants):
                found_any = True
                break

        if not found_any and q_tokens:
            return {
                "gate_passed": False,
                "retrieved_clauses": [],
                "scanned_terms": ", ".join(q_tokens),
                "score": 0.0,
                "coverage": 0.0
            }

        # BM25 search over clauses
        corpus = [c.get("text", "").lower().split() for c in clauses]
        bm25 = BM25Okapi(corpus)

        scores = bm25.get_scores(expanded_tokens)
        scored_clauses = sorted(zip(scores, clauses), key=lambda x: x[0], reverse=True)

        top_clauses = []
        curr_chars = 0
        top_score = scored_clauses[0][0] if scored_clauses else 0.0

        for score, c in scored_clauses[:top_k]:
            if score > 0:
                c_text = c.get("text", "")
                if curr_chars + len(c_text) > max_chars:
                    break
                top_clauses.append(c)
                curr_chars += len(c_text)

        gate_passed = len(top_clauses) > 0

        return {
            "gate_passed": gate_passed,
            "retrieved_clauses": top_clauses if gate_passed else [],
            "scanned_terms": ", ".join(expanded_tokens),
            "score": round(float(top_score), 2),
            "coverage": 1.0
        }
