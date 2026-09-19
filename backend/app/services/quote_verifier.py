import re
import difflib
from typing import Any, Dict, List, Optional, Tuple


def normalize_with_map(raw_text: str) -> Tuple[str, List[int]]:
    """
    Normalizes text (collapses whitespace, normalizes quotes/dashes/ligatures)
    and returns (norm_str, index_map) where index_map[i] maps back to original raw_text position.
    """
    norm_chars = []
    index_map = []
    in_whitespace = False

    for idx, char in enumerate(raw_text):
        # Normalize quotes and dashes
        c = char
        if c in ("“", "”", "‘", "’", "`"):
            c = '"' if c in ("“", "”") else "'"
        elif c in ("—", "–"):
            c = "-"
        elif c == "ﬁ":
            norm_chars.extend(["f", "i"])
            index_map.extend([idx, idx])
            in_whitespace = False
            continue
        elif c == "ﬂ":
            norm_chars.extend(["f", "l"])
            index_map.extend([idx, idx])
            in_whitespace = False
            continue

        if c.isspace():
            if not in_whitespace:
                norm_chars.append(" ")
                index_map.append(idx)
                in_whitespace = True
        else:
            norm_chars.append(c)
            index_map.append(idx)
            in_whitespace = False

    norm_str = "".join(norm_chars).strip()
    # Adjust index_map to match stripped string
    if norm_str:
        l_trim = len("".join(norm_chars)) - len("".join(norm_chars).lstrip())
        r_trim = len("".join(norm_chars)) - len("".join(norm_chars).rstrip())
        if r_trim > 0:
            index_map = index_map[l_trim:-r_trim]
        else:
            index_map = index_map[l_trim:]

    return norm_str, index_map


class QuoteVerifier:
    @staticmethod
    def verify_quote(
        quote: Optional[str],
        canonical_text: str,
        cited_clause_id: Optional[str] = None,
        clauses: Optional[List[Dict[str, Any]]] = None,
        pages_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Verifies LLM quote exists in canonical_text and returns exact original character offsets.
        Match strategy:
          1. Exact normalized match inside cited clause.
          2. Exact normalized match anywhere in canonical_text (outside cited clause).
          3. Fuzzy match (similarity >= 0.90) inside cited clause.
          4. Fail.
        """
        if not quote or not quote.strip():
            return {
                "verification_status": "failed",
                "char_start": None,
                "char_end": None,
                "page_start": None,
                "page_end": None,
                "clause_id": cited_clause_id,
                "matched_text": None,
                "similarity": 0.0,
            }

        norm_canon, canon_map = normalize_with_map(canonical_text)
        norm_quote, _ = normalize_with_map(quote)

        if not norm_quote:
            return {
                "verification_status": "failed",
                "char_start": None,
                "char_end": None,
                "page_start": None,
                "page_end": None,
                "clause_id": cited_clause_id,
                "matched_text": None,
                "similarity": 0.0,
            }

        # Find cited clause bounds if provided
        cited_clause = None
        if cited_clause_id and clauses:
            for c in clauses:
                if c.get("id") == cited_clause_id or c.get("temp_id") == cited_clause_id:
                    cited_clause = c
                    break

        # 1. Exact normalized match inside cited clause
        if cited_clause:
            c_start = cited_clause["char_start"]
            c_end = cited_clause["char_end"]
            clause_sub = canonical_text[c_start:c_end]
            norm_sub, sub_map = normalize_with_map(clause_sub)

            sub_idx = norm_sub.lower().find(norm_quote.lower())
            if sub_idx != -1:
                start_in_sub = sub_map[sub_idx]
                end_in_sub = sub_map[min(sub_idx + len(norm_quote) - 1, len(sub_map) - 1)] + 1
                real_start = c_start + start_in_sub
                real_end = c_start + end_in_sub
                matched_text = canonical_text[real_start:real_end]

                p_start, p_end = QuoteVerifier._get_page_range(real_start, real_end, pages_data)

                return {
                    "verification_status": "exact",
                    "char_start": real_start,
                    "char_end": real_end,
                    "page_start": p_start,
                    "page_end": p_end,
                    "clause_id": cited_clause_id,
                    "matched_text": matched_text,
                    "similarity": 1.0,
                }

        # 2. Exact match anywhere in canonical_text
        doc_idx = norm_canon.lower().find(norm_quote.lower())
        if doc_idx != -1:
            real_start = canon_map[doc_idx]
            real_end = canon_map[min(doc_idx + len(norm_quote) - 1, len(canon_map) - 1)] + 1
            matched_text = canonical_text[real_start:real_end]

            p_start, p_end = QuoteVerifier._get_page_range(real_start, real_end, pages_data)

            # Find matching clause for this position if available
            found_clause_id = cited_clause_id
            if clauses:
                for c in clauses:
                    if c["char_start"] <= real_start < c["char_end"]:
                        found_clause_id = c.get("id") or c.get("temp_id")
                        break

            v_status = "exact" if found_clause_id == cited_clause_id else "outside_clause"

            return {
                "verification_status": v_status,
                "char_start": real_start,
                "char_end": real_end,
                "page_start": p_start,
                "page_end": p_end,
                "clause_id": found_clause_id,
                "matched_text": matched_text,
                "similarity": 1.0,
            }

        # 3. Fuzzy match inside cited clause or document
        search_target = canonical_text[cited_clause["char_start"]:cited_clause["char_end"]] if cited_clause else canonical_text
        base_offset = cited_clause["char_start"] if cited_clause else 0
        norm_target, target_map = normalize_with_map(search_target)

        q_len = len(norm_quote)
        best_ratio = 0.0
        best_pos = -1

        # Window sliding search
        for pos in range(0, max(1, len(norm_target) - q_len + 1), 5):
            window = norm_target[pos : pos + q_len]
            ratio = difflib.SequenceMatcher(None, window.lower(), norm_quote.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_pos = pos

        if best_ratio >= 0.88 and best_pos != -1:
            real_start = base_offset + target_map[best_pos]
            real_end = base_offset + target_map[min(best_pos + q_len - 1, len(target_map) - 1)] + 1
            matched_text = canonical_text[real_start:real_end]
            p_start, p_end = QuoteVerifier._get_page_range(real_start, real_end, pages_data)

            return {
                "verification_status": "fuzzy",
                "char_start": real_start,
                "char_end": real_end,
                "page_start": p_start,
                "page_end": p_end,
                "clause_id": cited_clause_id,
                "matched_text": matched_text,
                "similarity": round(best_ratio, 2),
            }

        # 4. Fail
        return {
            "verification_status": "failed",
            "char_start": None,
            "char_end": None,
            "page_start": None,
            "page_end": None,
            "clause_id": cited_clause_id,
            "matched_text": None,
            "similarity": 0.0,
        }

    @staticmethod
    def _get_page_range(start: int, end: int, pages_data: Optional[List[Dict[str, Any]]]) -> Tuple[int, int]:
        if not pages_data:
            return 1, 1
        p_start = 1
        p_end = 1
        for p in pages_data:
            if p["char_start"] <= start < p["char_end"]:
                p_start = p["page_number"]
            if p["char_start"] <= max(0, end - 1) < p["char_end"]:
                p_end = p["page_number"]
        return p_start, p_end
