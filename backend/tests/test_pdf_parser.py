import os
import fitz
import pytest
from app.services.pdf_parser import PDFParser


def create_sample_pdf_bytes():
    doc = fitz.open()
    
    # Page 1
    p1 = doc.new_page(width=600, height=800)
    p1.insert_text((50, 30), "HEADER - CONFIDENTIAL", fontsize=10) # Header
    p1.insert_text((50, 100), "SECTION 1. DEFINITIONS AND AGREEMENT TERMS", fontsize=14)
    p1.insert_text((50, 130), "This Master Agreement defines all relevant terms, operational responsibilities, and conditions governing the relationship between the parties.", fontsize=10)
    p1.insert_text((50, 160), "Vendor agrees to perform services according to professional industry standards and timely deliverables.", fontsize=10)
    p1.insert_text((50, 770), "FOOTER - PAGE 1", fontsize=10) # Footer

    # Page 2
    p2 = doc.new_page(width=600, height=800)
    p2.insert_text((50, 30), "HEADER - CONFIDENTIAL", fontsize=10) # Header
    p2.insert_text((50, 100), "SECTION 2. TERM AND AUTOMATIC RENEWAL", fontsize=14)
    p2.insert_text((50, 130), "The term shall be 12 months from the effective date and shall automatically renew for additional terms.", fontsize=10)
    p2.insert_text((50, 160), "Either party may terminate by providing written notice ninety days prior to the expiration date.", fontsize=10)
    p2.insert_text((50, 770), "FOOTER - PAGE 2", fontsize=10) # Footer

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_scanned_pdf_bytes():
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    pix = fitz.Pixmap(fitz.csRGB, fitz.Rect(0, 0, 600, 800), False)
    pix.clear_with(240)
    page.insert_image(page.rect, pixmap=pix)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_pdf_parser_canonical_offsets_and_words():
    pdf_bytes = create_sample_pdf_bytes()
    res = PDFParser.parse_pdf_bytes(pdf_bytes)

    assert res["is_scanned"] is False
    assert res["page_count"] == 2
    canonical_text = res["canonical_text"]
    assert "SECTION 1. DEFINITIONS AND AGREEMENT TERMS" in canonical_text
    assert "SECTION 2. TERM AND AUTOMATIC RENEWAL" in canonical_text

    for page_data in res["pages_data"]:
        c_start = page_data["char_start"]
        c_end = page_data["char_end"]
        page_slice = canonical_text[c_start:c_end]
        assert page_slice == page_data["text"]

        # Verify word offsets slice back to word text
        for w in page_data["words_list"]:
            if not w["is_header_footer"]:
                w_start = w["char_start"]
                w_end = w["char_end"]
                assert canonical_text[w_start:w_end] == w["text"]


def test_header_footer_exclusion():
    pdf_bytes = create_sample_pdf_bytes()
    res = PDFParser.parse_pdf_bytes(pdf_bytes)
    canonical_text = res["canonical_text"]

    # "HEADER - CONFIDENTIAL" repeats in top 8% of pages 1 and 2
    assert "HEADER - CONFIDENTIAL" not in canonical_text


def test_scanned_pdf_detection():
    scanned_bytes = create_scanned_pdf_bytes()
    res = PDFParser.parse_pdf_bytes(scanned_bytes)
    assert res["is_scanned"] is True
    assert res["error_code"] == "scanned_unsupported"


def test_highlight_resolution():
    pdf_bytes = create_sample_pdf_bytes()
    res = PDFParser.parse_pdf_bytes(pdf_bytes)
    canonical_text = res["canonical_text"]

    target_phrase = "SECTION 1. DEFINITIONS"
    start_idx = canonical_text.find(target_phrase)
    end_idx = start_idx + len(target_phrase)

    highlights = PDFParser.resolve_highlights(res["pages_data"], start_idx, end_idx)
    assert len(highlights) == 1
    assert highlights[0]["page"] == 1
    assert len(highlights[0]["rects"]) >= 1
