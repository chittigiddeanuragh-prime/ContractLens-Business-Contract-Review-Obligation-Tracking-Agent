import json
import re
import fitz  # PyMuPDF
from typing import Any, Dict, List, Tuple, Optional
from app.core.config import settings


def normalize_text(text: str) -> str:
    """Normalizes ligatures, unicode quotes, and dashes."""
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    text = text.replace("—", "-").replace("–", "-")
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    return text


def detect_headers_footers(doc: fitz.Document) -> set:
    """
    Identifies (page_num, line_text_normalized) tuples that appear on >= 60% of pages
    within the top 8% or bottom 8% of page height.
    """
    page_count = len(doc)
    if page_count < 2:
        return set()

    line_counts: Dict[str, int] = {}
    page_lines: List[List[Tuple[str, int, int]]] = []

    for page_idx in range(page_count):
        page = doc[page_idx]
        p_height = page.rect.height
        top_threshold = p_height * 0.08
        bottom_threshold = p_height * 0.92
        words = page.get_text("words") # (x0, y0, x1, y1, word, block, line, word_no)
        
        # Group words by line
        lines_dict: Dict[Tuple[int, int], List[Tuple[float, float, float, float, str]]] = {}
        for w in words:
            key = (w[5], w[6])
            lines_dict.setdefault(key, []).append(w[:5])

        page_hf_lines = set()
        for (b, l), w_list in lines_dict.items():
            min_y = min(w[1] for w in w_list)
            max_y = max(w[3] for w in w_list)
            if min_y <= top_threshold or max_y >= bottom_threshold:
                line_str = " ".join(w[4] for w in w_list)
                line_norm = re.sub(r"\d+", "", line_str).strip()
                if len(line_norm) > 2:
                    page_hf_lines.add(line_norm)

        for line_norm in page_hf_lines:
            line_counts[line_norm] = line_counts.get(line_norm, 0) + 1

    header_footer_norms = {
        norm for norm, count in line_counts.items() if (count / page_count) >= 0.6
    }
    return header_footer_norms


class PDFParser:
    @staticmethod
    def parse_pdf_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Parses PDF bytes, checks encryption & scanned status, constructs canonical text,
        filters headers/footers, and maps word bounding boxes to canonical text character offsets.
        """
        if not pdf_bytes.startswith(b"%PDF"):
            raise ValueError("Invalid PDF file format: missing %PDF magic bytes.")

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Corrupt or invalid PDF file: {str(e)}")

        if doc.is_encrypted:
            raise ValueError("Encrypted or password-protected PDFs are not supported.")

        page_count = len(doc)
        if page_count == 0:
            raise ValueError("PDF document contains 0 pages.")

        if page_count > settings.MAX_PDF_PAGES:
            raise ValueError(f"PDF exceeds maximum page limit of {settings.MAX_PDF_PAGES} pages.")

        # Check for scanned PDF
        total_chars = 0
        low_char_pages = 0
        for page in doc:
            t = page.get_text("text").strip()
            char_len = len(t)
            total_chars += char_len
            if char_len < settings.SCANNED_LOW_CHAR_THRESHOLD:
                low_char_pages += 1

        avg_chars = total_chars / page_count
        low_char_ratio = low_char_pages / page_count

        if avg_chars < settings.SCANNED_PAGE_MIN_CHARS or low_char_ratio > settings.SCANNED_MIN_PAGE_RATIO:
            return {
                "is_scanned": True,
                "error_code": "scanned_unsupported",
                "error_message": "This PDF looks scanned or image-only. OCR support is on the roadmap.",
                "page_count": page_count,
            }

        # Header/Footer detection
        hf_norms = detect_headers_footers(doc)

        canonical_pieces = []
        pages_data = []
        current_offset = 0

        for page_idx in range(page_count):
            page = doc[page_idx]
            page_num = page_idx + 1
            p_width = page.rect.width
            p_height = page.rect.height

            if page_idx > 0:
                canonical_pieces.append("\n\f\n")
                current_offset += 3

            page_start_offset = current_offset
            words_raw = page.get_text("words") # x0, y0, x1, y1, text, block, line, word_no

            # Group words into blocks and lines
            blocks: Dict[int, Dict[int, List[Any]]] = {}
            for w in words_raw:
                b_idx, l_idx = w[5], w[6]
                blocks.setdefault(b_idx, {}).setdefault(l_idx, []).append(w)

            page_words_processed = []
            page_text_pieces = []

            first_line = True
            for b_idx in sorted(blocks.keys()):
                lines = blocks[b_idx]
                for l_idx in sorted(lines.keys()):
                    w_list = sorted(lines[l_idx], key=lambda x: (x[7], x[0]))
                    line_str = " ".join(w[4] for w in w_list)
                    line_norm = re.sub(r"\d+", "", line_str).strip()

                    is_hf = line_norm in hf_norms

                    if is_hf:
                        for w in w_list:
                            page_words_processed.append({
                                "text": w[4],
                                "bbox": [round(w[0], 2), round(w[1], 2), round(w[2], 2), round(w[3], 2)],
                                "char_start": None,
                                "char_end": None,
                                "line": l_idx,
                                "block": b_idx,
                                "is_header_footer": True,
                            })
                        continue

                    if not first_line:
                        canonical_pieces.append("\n")
                        page_text_pieces.append("\n")
                        current_offset += 1
                    first_line = False

                    # Append words on line
                    for i, w in enumerate(w_list):
                        if i > 0:
                            canonical_pieces.append(" ")
                            page_text_pieces.append(" ")
                            current_offset += 1

                        raw_w_text = normalize_text(w[4])
                        w_len = len(raw_w_text)
                        w_start = current_offset
                        w_end = current_offset + w_len

                        canonical_pieces.append(raw_w_text)
                        page_text_pieces.append(raw_w_text)
                        current_offset += w_len

                        page_words_processed.append({
                            "text": raw_w_text,
                            "bbox": [round(w[0], 2), round(w[1], 2), round(w[2], 2), round(w[3], 2)],
                            "char_start": w_start,
                            "char_end": w_end,
                            "line": l_idx,
                            "block": b_idx,
                            "is_header_footer": False,
                        })

            page_end_offset = current_offset
            page_full_text = "".join(page_text_pieces)

            pages_data.append({
                "page_number": page_num,
                "width": round(p_width, 2),
                "height": round(p_height, 2),
                "char_start": page_start_offset,
                "char_end": page_end_offset,
                "text": page_full_text,
                "words_json": json.dumps(page_words_processed),
                "words_list": page_words_processed,
            })

        canonical_text = "".join(canonical_pieces)

        return {
            "is_scanned": False,
            "page_count": page_count,
            "canonical_text": canonical_text,
            "pages_data": pages_data,
        }

    @staticmethod
    def resolve_highlights(pages_data: List[Dict[str, Any]], start: int, end: int) -> List[Dict[str, Any]]:
        """
        Given canonical text character range [start, end], returns bounding rectangles per page:
        [{page: page_number, width: page_width, height: page_height, rects: [{x0,y0,x1,y1}]}]
        Merges adjacent word boxes on the same line into unified rectangles.
        """
        page_highlights = []

        for p in pages_data:
            p_num = p["page_number"]
            p_w = p["width"]
            p_h = p["height"]
            
            words_list = p.get("words_list")
            if not words_list:
                words_list = json.loads(p["words_json"])

            # Find matching words on this page
            matching_words = []
            for w in words_list:
                if w.get("is_header_footer") or w.get("char_start") is None or w.get("char_end") is None:
                    continue
                # Overlap check
                if w["char_start"] < end and w["char_end"] > start:
                    matching_words.append(w)

            if not matching_words:
                continue

            # Group matching words by line
            line_groups: Dict[Tuple[int, int], List[Any]] = {}
            for w in matching_words:
                key = (w["block"], w["line"])
                line_groups.setdefault(key, []).append(w)

            rects = []
            for (b, l), w_group in line_groups.items():
                min_x0 = min(w["bbox"][0] for w in w_group)
                min_y0 = min(w["bbox"][1] for w in w_group)
                max_x1 = max(w["bbox"][2] for w in w_group)
                max_y1 = max(w["bbox"][3] for w in w_group)
                rects.append({
                    "x0": round(min_x0, 2),
                    "y0": round(min_y0, 2),
                    "x1": round(max_x1, 2),
                    "y1": round(max_y1, 2),
                })

            if rects:
                page_highlights.append({
                    "page": p_num,
                    "width": p_w,
                    "height": p_h,
                    "rects": rects,
                })

        return page_highlights
