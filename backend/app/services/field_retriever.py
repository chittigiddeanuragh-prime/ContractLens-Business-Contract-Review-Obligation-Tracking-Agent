from typing import Any, Dict, List, Optional
from rank_bm25 import BM25Okapi
from app.core.config import settings
from app.services.field_registry import FIELD_REGISTRY, GROUPS, EXTRACTION_GROUPS


class FieldRetriever:
    @staticmethod
    def build_group_context(
        group_id: str,
        clauses: List[Dict[str, Any]],
        canonical_text: Optional[str] = None,
        defined_terms: Optional[List[Dict[str, Any]]] = None,
        max_chars: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Builds targeted context for an extraction group formatted as:
        [CLAUSE id=<uuid> number=7.2 page=8 type=payment]
        <text>
        [/CLAUSE]
        """
        if max_chars is None:
            max_chars = settings.EXTRACTION_MAX_CONTEXT_CHARS

        # Handle group name alias mapping (e.g. "dates_and_term" -> "A")
        real_group_id = group_id
        if group_id in EXTRACTION_GROUPS:
            if group_id == "dates_and_term":
                real_group_id = "A"
            elif group_id == "renewal_and_termination":
                real_group_id = "B"
            elif group_id == "fees_and_liability":
                real_group_id = "C"
            elif group_id == "governing_law_and_disputes":
                real_group_id = "D"

        group_fields = GROUPS.get(real_group_id, [])
        target_types = set()
        keywords = []

        for f_name in group_fields:
            spec = FIELD_REGISTRY.get(f_name)
            if spec:
                target_types.update(spec.target_clause_types)
                keywords.extend(spec.keyword_hints)

        # 1. Filter clauses matching target clause types, preamble, or signature block
        selected_clauses = []
        selected_ids = set()

        for c in clauses:
            c_type = c.get("category") or c.get("clause_type")
            c_num = str(c.get("number") or c.get("clause_number", "")).upper()
            c_id = c.get("id") or c.get("temp_id")

            if c_type in target_types or "PREAMBLE" in c_num or "SIGNATURE" in c_num or c.get("level") == 1:
                selected_clauses.append(c)
                selected_ids.add(c_id)

        # 2. BM25 keyword search over remaining clauses
        remaining_clauses = [c for c in clauses if (c.get("id") or c.get("temp_id")) not in selected_ids]
        if remaining_clauses and keywords:
            corpus = [c.get("text", "").lower().split() for c in remaining_clauses]
            bm25 = BM25Okapi(corpus)
            query = " ".join(keywords).lower().split()
            scores = bm25.get_scores(query)

            # Top 5 BM25 matches
            scored_clauses = sorted(zip(scores, remaining_clauses), key=lambda x: x[0], reverse=True)
            for score, c in scored_clauses[:5]:
                if score > 0:
                    selected_clauses.append(c)
                    selected_ids.add(c.get("id") or c.get("temp_id"))

        # Sort selected clauses by canonical character start
        selected_clauses.sort(key=lambda x: x.get("char_start", 0))

        # Format context string
        context_pieces = []
        curr_chars = 0

        for c in selected_clauses:
            c_id = c.get("id") or c.get("temp_id")
            c_num = c.get("number") or c.get("clause_number", "")
            c_page = c.get("page_start", 1)
            c_type = c.get("category") or c.get("clause_type", "other")
            c_text = c.get("text", "")

            clause_block = f"[CLAUSE id={c_id} number={c_num} page={c_page} type={c_type}]\n{c_text}\n[/CLAUSE]\n\n"
            if curr_chars + len(clause_block) > max_chars:
                break

            context_pieces.append(clause_block)
            curr_chars += len(clause_block)

        # Append defined terms definitions if present
        if defined_terms:
            terms_text = []
            for dt in defined_terms:
                t_str = f"Defined Term: \"{dt['term']}\" = {dt['definition']}"
                if curr_chars + len(t_str) < max_chars:
                    terms_text.append(t_str)
                    curr_chars += len(t_str) + 1

            if terms_text:
                context_pieces.append("[DEFINED_TERMS]\n" + "\n".join(terms_text) + "\n[/DEFINED_TERMS]\n\n")

        # Fallback to preamble/first 2000 chars if no clauses matched
        if not context_pieces and canonical_text:
            return canonical_text[:max_chars]

        return "".join(context_pieces)
