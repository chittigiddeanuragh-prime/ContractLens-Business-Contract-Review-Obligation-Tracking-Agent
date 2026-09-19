from typing import Any, Dict, List


def validate_clause_invariants(canonical_text: str, clauses_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validates non-negotiable clause invariants across a set of extracted clauses:
      I1. clause.text == canonical_text[clause.char_start:clause.char_end], always, exactly.
      I3. No overlaps between sibling clauses.
      I4. Parent spans contain their children's spans.
    Returns {"valid": bool, "errors": list[str]}.
    """
    errors = []

    # Map clauses by ID or temporary index for parent checking
    clause_map = {c.get("id", idx): c for idx, c in enumerate(clauses_data)}

    for idx, c in enumerate(clauses_data):
        c_id = c.get("id", f"clause_{idx}")
        start = c.get("char_start")
        end = c.get("char_end")
        text = c.get("text")

        # Check I1
        if start is None or end is None or start < 0 or end > len(canonical_text) or start >= end:
            errors.append(f"Clause {c_id} ({c.get('number')}) has out-of-bound offsets [{start}, {end}]. Canonical length is {len(canonical_text)}.")
            continue

        actual_slice = canonical_text[start:end]
        if actual_slice != text:
            errors.append(
                f"Invariant I1 Violation on Clause {c_id} ({c.get('number')}): "
                f"clause.text does not match canonical_text[{start}:{end}]. "
                f"Expected slice repr: {repr(actual_slice[:50])}, Got text repr: {repr(text[:50])}."
            )

        # Check I4 (Parent containment)
        parent_id = c.get("parent_id")
        if parent_id and parent_id in clause_map:
            parent = clause_map[parent_id]
            p_start = parent.get("char_start")
            p_end = parent.get("char_end")
            if p_start is not None and p_end is not None:
                if start < p_start or end > p_end:
                    errors.append(
                        f"Invariant I4 Violation: Child clause {c_id} ({c.get('number')}) [{start}, {end}] "
                        f"is not fully contained in parent {parent_id} [{p_start}, {p_end}]."
                    )

    # Check I3 (No sibling overlaps)
    # Group clauses by parent_id
    siblings_by_parent: Dict[Any, List[Dict[str, Any]]] = {}
    for c in clauses_data:
        siblings_by_parent.setdefault(c.get("parent_id"), []).append(c)

    for p_id, siblings in siblings_by_parent.items():
        sorted_s = sorted(siblings, key=lambda x: x.get("char_start", 0))
        for i in range(len(sorted_s) - 1):
            curr_c = sorted_s[i]
            next_c = sorted_s[i + 1]
            if curr_c.get("char_end", 0) > next_c.get("char_start", 0):
                errors.append(
                    f"Invariant I3 Violation (Sibling Overlap): Sibling clause {curr_c.get('number')} [{curr_c.get('char_start')}, {curr_c.get('char_end')}] "
                    f"overlaps with {next_c.get('number')} [{next_c.get('char_start')}, {next_c.get('char_end')}]."
                )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }
