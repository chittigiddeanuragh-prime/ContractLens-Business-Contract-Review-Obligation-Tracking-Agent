import re
from typing import Any, Dict, List, Optional

CROSS_REF_RE = re.compile(
    r'\b((?:Section|Clause|Article|Schedule|Exhibit|Annex)\s+([A-Za-z0-9\.\-]+))\b',
    re.IGNORECASE
)


class CrossReferenceResolver:
    @staticmethod
    def extract_and_resolve(clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extracts cross-references in clause text and resolves target clause IDs by number.
        """
        # Build lookup table of clause numbers -> clause ID / temp_id
        number_map: Dict[str, str] = {}
        for c in clauses:
            c_id = c.get("temp_id") or c.get("id")
            c_num = c.get("number", "").strip().upper()
            if c_num:
                number_map[c_num] = c_id
                # Strip prefix for matching ("SECTION 1" -> "1")
                num_only = re.sub(r'^(?:SECTION|ARTICLE|CLAUSE|SCHEDULE|EXHIBIT|ANNEX)\s+', '', c_num)
                if num_only:
                    number_map[num_only] = c_id

        cross_refs = []
        seen = set()

        for c in clauses:
            from_id = c.get("temp_id") or c.get("id")
            c_text = c.get("text", "")

            for m in CROSS_REF_RE.finditer(c_text):
                full_ref_text = m.group(1).strip()
                to_num_raw = m.group(2).strip().rstrip(".")
                
                dedup_key = (from_id, full_ref_text.upper())
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                # Attempt resolution
                resolved_id = number_map.get(full_ref_text.upper()) or number_map.get(to_num_raw.upper())

                cross_refs.append({
                    "from_clause_id": from_id,
                    "ref_text": full_ref_text,
                    "to_number": to_num_raw,
                    "resolved_clause_id": resolved_id,
                })

        return cross_refs
