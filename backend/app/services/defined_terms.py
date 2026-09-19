import re
from typing import Any, Dict, List

# Patterns for inline and section defined terms
INLINE_TERM_RE = re.compile(r'[\"\“\‘]([A-Z][A-Za-z0-9\s]{1,50})[\"\”\’]\s+(?:means|shall mean|refers to|is defined as)\s+([^;\.\n]+)', re.IGNORECASE)
PAREN_TERM_RE = re.compile(r'\(\s*(?:the|a|an)?\s*[\"\“\‘]([A-Z][A-Za-z0-9\s]{1,50})[\"\”\’]\s*\)', re.IGNORECASE)


class DefinedTermsExtractor:
    @staticmethod
    def extract_defined_terms(canonical_text: str, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extracts defined terms and their definitions from clause text with character offsets.
        """
        defined_terms = []
        seen_terms = set()

        for c in clauses:
            c_text = c.get("text", "")
            c_start = c.get("char_start", 0)
            c_id = c.get("temp_id") or c.get("id")

            # 1. Check explicitly formatted inline definitions (e.g. "Services" means ...)
            for m in INLINE_TERM_RE.finditer(c_text):
                term_str = m.group(1).strip()
                def_str = m.group(2).strip()
                term_key = term_str.lower()
                if term_key not in seen_terms and len(term_str) > 1:
                    seen_terms.add(term_key)
                    t_start = c_start + m.start(1)
                    t_end = c_start + m.end(1)
                    defined_terms.append({
                        "term": term_str,
                        "definition": def_str[:500],
                        "clause_id": c_id,
                        "char_start": t_start,
                        "char_end": t_end,
                    })

            # 2. Check parenthetical defined terms (e.g. Meridian Tech ('Client'))
            for m in PAREN_TERM_RE.finditer(c_text):
                term_str = m.group(1).strip()
                term_key = term_str.lower()
                if term_key not in seen_terms and len(term_str) > 1:
                    seen_terms.add(term_key)
                    # Extract surrounding context for definition
                    context_start = max(0, m.start() - 100)
                    def_str = c_text[context_start:m.start()].strip()
                    t_start = c_start + m.start(1)
                    t_end = c_start + m.end(1)
                    defined_terms.append({
                        "term": term_str,
                        "definition": def_str or term_str,
                        "clause_id": c_id,
                        "char_start": t_start,
                        "char_end": t_end,
                    })

        return defined_terms
