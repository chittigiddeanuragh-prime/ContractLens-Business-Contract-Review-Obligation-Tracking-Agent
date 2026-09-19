import re
import json
import logging
from typing import Any, Dict, List, Tuple, Optional
from app.services.invariants import validate_clause_invariants

logger = logging.getLogger(__name__)

FALSE_POSITIVE_DATE_RE = re.compile(
    r"^\d+\.\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b",
    re.IGNORECASE,
)
FALSE_POSITIVE_CURRENCY_RE = re.compile(r"^\$\d+")


class ClauseSegmenter:
    @staticmethod
    def _extract_lines(canonical_text: str) -> List[Tuple[int, int, str]]:
        """Splits canonical text into lines with (start_offset, end_offset, line_str)."""
        lines = []
        pos = 0
        for line in canonical_text.split("\n"):
            line_len = len(line)
            lines.append((pos, pos + line_len, line))
            pos += line_len + 1 # +1 for \n
        return lines

    @staticmethod
    def _is_heading(line: str) -> Optional[Tuple[str, str, int]]:
        """
        Returns (number, heading, level) if line matches a clause heading pattern, else None.
        """
        l_str = line.strip()
        if not l_str:
            return None

        # Check false positives
        if FALSE_POSITIVE_DATE_RE.match(l_str) or FALSE_POSITIVE_CURRENCY_RE.match(l_str):
            return None

        # Preamble / Recitals
        if re.match(r"^(?:RECITALS|PREAMBLE|WHEREAS)\b", l_str, re.IGNORECASE):
            return ("PREAMBLE", "RECITALS", 1)

        # Signature Block
        if re.match(r"^(?:IN WITNESS WHEREOF|IN WITNESS|SIGNED|EXECUTION)\b", l_str, re.IGNORECASE):
            return ("SIGNATURES", "SIGNATURE BLOCK", 1)

        # Schedule / Exhibit / Annex
        m_sch = re.match(r"^(?:SCHEDULE|EXHIBIT|ANNEX)\s+([A-Za-z0-9]+)\b", l_str, re.IGNORECASE)
        if m_sch:
            num = f"SCHEDULE {m_sch.group(1).upper()}"
            rest = l_str[m_sch.end():].lstrip(" .:-")
            heading = rest if len(rest.split()) <= 10 else ""
            return (num, heading, 1)

        # Section / Article prefix (e.g. "SECTION 1. DEFINITIONS" or "ARTICLE I")
        m_sec = re.match(r"^(?:SECTION|Section|ARTICLE|Article|CLAUSE|Clause)\s+([A-Za-z0-9\.\-]+)[\.\:]?\s*(.*)", l_str)
        if m_sec:
            raw_num = m_sec.group(1).rstrip(".")
            prefix_type = l_str.split()[0].upper()
            num = f"{prefix_type} {raw_num}"
            rest = m_sec.group(2).strip()
            heading = rest.split(".")[0].strip() if rest else ""
            if len(heading.split()) > 12:
                heading = ""
            level = raw_num.count(".") + 1
            return (num, heading, level)

        # Numeric prefix (e.g. "1. DEFINITIONS", "1.1 Scope", "7.2.1 Fees")
        m_num = re.match(r"^(\d+(?:\.\d+)*)[\.\:]?\s+([A-Z0-9].*)", l_str)
        if m_num:
            num = m_num.group(1)
            rest = m_num.group(2).strip()
            heading = rest.split(".")[0].strip()
            if len(heading.split()) > 12:
                heading = ""
            level = num.count(".") + 1
            return (num, heading, level)

        # Subsection prefix (e.g. "(a) Client Data", "(i) Subclause")
        m_sub = re.match(r"^\(([a-z1-9]|[ivx]+)\)\s+([A-Z0-9].*)", l_str)
        if m_sub:
            sub_num = f"({m_sub.group(1)})"
            rest = m_sub.group(2).strip()
            heading = rest.split(".")[0].strip()
            if len(heading.split()) > 10:
                heading = ""
            return (sub_num, heading, 2)

        # ALL-CAPS Standalone Heading (e.g. "CONFIDENTIALITY")
        if l_str.isupper() and 4 <= len(l_str) <= 60 and not l_str.endswith("."):
            return (l_str, l_str, 1)

        return None

    @classmethod
    def segment_rules(cls, canonical_text: str, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rule-based segmentation producing exact canonical text slices."""
        lines = cls._extract_lines(canonical_text)
        detected_starts = []

        for line_idx, (start_off, end_off, line_str) in enumerate(lines):
            res = cls._is_heading(line_str)
            if res:
                num, heading, level = res
                detected_starts.append({
                    "line_idx": line_idx,
                    "start_off": start_off,
                    "number": num,
                    "heading": heading,
                    "level": level,
                })

        if not detected_starts:
            return []

        doc_len = len(canonical_text)
        clauses = []
        parent_stack: List[Dict[str, Any]] = []

        for i in range(len(detected_starts)):
            curr = detected_starts[i]
            next_start = detected_starts[i + 1]["start_off"] if i + 1 < len(detected_starts) else doc_len

            c_start = curr["start_off"]
            c_end = next_start

            # Calculate page start and end
            p_start = 1
            p_end = 1
            for p in pages_data:
                if p["char_start"] <= c_start < p["char_end"]:
                    p_start = p["page_number"]
                if p["char_start"] <= max(0, c_end - 1) < p["char_end"]:
                    p_end = p["page_number"]

            c_text = canonical_text[c_start:c_end]

            # Resolve parent_id from stack
            while parent_stack and parent_stack[-1]["level"] >= curr["level"]:
                parent_stack.pop()

            parent_id = parent_stack[-1]["temp_id"] if parent_stack else None
            temp_id = f"clause_rule_{i+1}"

            clause_obj = {
                "temp_id": temp_id,
                "number": curr["number"],
                "heading": curr["heading"],
                "text": c_text,
                "page_start": p_start,
                "page_end": p_end,
                "page": p_start,
                "parent_id": parent_id,
                "level": curr["level"],
                "order_index": i + 1,
                "char_start": c_start,
                "char_end": c_end,
                "segmentation_method": "rules",
                "confidence": 0.95,
            }

            clauses.append(clause_obj)
            parent_stack.append({"level": curr["level"], "temp_id": temp_id})

        return clauses

    @classmethod
    def segment_paragraph_fallback(cls, canonical_text: str, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback segmentation splitting text into paragraph-level clauses."""
        doc_len = len(canonical_text)
        paragraphs = canonical_text.split("\n\n")
        clauses = []
        curr_pos = 0

        for idx, p_text in enumerate(paragraphs):
            if not p_text.strip():
                curr_pos += len(p_text) + 2
                continue

            c_start = curr_pos
            c_end = curr_pos + len(p_text)
            curr_pos = c_end + 2

            p_start = 1
            p_end = 1
            for p in pages_data:
                if p["char_start"] <= c_start < p["char_end"]:
                    p_start = p["page_number"]
                if p["char_start"] <= max(0, c_end - 1) < p["char_end"]:
                    p_end = p["page_number"]

            c_slice = canonical_text[c_start:c_end]

            clauses.append({
                "temp_id": f"clause_para_{idx+1}",
                "number": f"P{idx+1}",
                "heading": p_text.strip().split("\n")[0][:40],
                "text": c_slice,
                "page_start": p_start,
                "page_end": p_end,
                "page": p_start,
                "parent_id": None,
                "level": 1,
                "order_index": idx + 1,
                "char_start": c_start,
                "char_end": c_end,
                "segmentation_method": "paragraph_fallback",
                "confidence": 0.50,
            })

        return clauses

    @classmethod
    def segment_contract(cls, canonical_text: str, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Primary segmentation entry point. Executes rule-based segmentation, verifies invariants,
        and falls back to paragraph splitting if rules extract < 5 clauses.
        """
        clauses = cls.segment_rules(canonical_text, pages_data)

        # Check coverage
        covered_chars = sum(len(c["text"]) for c in clauses)
        total_chars = len(canonical_text)
        coverage_ratio = covered_chars / total_chars if total_chars > 0 else 0

        if len(clauses) < 5 or coverage_ratio < 0.6:
            logger.warning(f"Rule segmenter found only {len(clauses)} clauses (coverage: {coverage_ratio:.2f}). Falling back to paragraph segmenter.")
            clauses = cls.segment_paragraph_fallback(canonical_text, pages_data)

        # Validate Invariants I1, I3, I4
        inv_check = validate_clause_invariants(canonical_text, clauses)
        if not inv_check["valid"]:
            logger.error(f"Clause invariants failed: {inv_check['errors']}")

        return clauses
