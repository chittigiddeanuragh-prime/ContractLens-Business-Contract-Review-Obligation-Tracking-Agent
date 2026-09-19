import fitz
import pytest
from app.services.pdf_parser import PDFParser
from app.services.clause_segmenter import ClauseSegmenter
from app.services.clause_classifier import ClauseClassifier
from app.services.defined_terms import DefinedTermsExtractor
from app.services.cross_references import CrossReferenceResolver
from app.services.invariants import validate_clause_invariants


def create_numbered_contract_pdf():
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_text((50, 40), "HEADER - CONFIDENTIAL AGREEMENT", fontsize=10)
    
    text_content = (
        "MASTER SERVICES AGREEMENT\n"
        "RECITALS\n"
        "WHEREAS, Client desires to obtain services.\n"
        "SECTION 1. DEFINITIONS AND TERMS\n"
        "1.1 Services means cloud data services.\n"
        "1.2 Confidential Information means proprietary data.\n"
        "SECTION 2. TERM AND RENEWAL\n"
        "2.1 Initial Term shall be 2 years.\n"
        "2.2 Automatic Renewal shall occur unless 90 days notice is given.\n"
        "SECTION 12. MISCELLANEOUS\n"
        "12.1 Notices shall be sent pursuant to Section 2.2 above.\n"
        "IN WITNESS WHEREOF, the parties execute this agreement."
    )
    
    y = 80
    for line in text_content.split("\n"):
        page.insert_text((50, y), line, fontsize=11)
        y += 25

    page.insert_text((50, 770), "FOOTER - PAGE 1", fontsize=10)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_clause_invariants_hold():
    pdf_bytes = create_numbered_contract_pdf()
    parse_res = PDFParser.parse_pdf_bytes(pdf_bytes)
    clauses = ClauseSegmenter.segment_contract(parse_res["canonical_text"], parse_res["pages_data"])

    assert len(clauses) >= 4
    inv = validate_clause_invariants(parse_res["canonical_text"], clauses)
    assert inv["valid"] is True, f"Invariant errors: {inv['errors']}"

    # Verify I1: text equals slice
    for c in clauses:
        assert c["text"] == parse_res["canonical_text"][c["char_start"]:c["char_end"]]


def test_false_positive_rejection():
    # Dates like "1. January 2026" or "$1.5 million" should not be treated as clauses
    line1 = "1. January 2026 is the start date."
    line2 = "$1.5 million total fee."
    
    assert ClauseSegmenter._is_heading(line1) is None
    assert ClauseSegmenter._is_heading(line2) is None


def test_clause_classification_dictionary():
    term_clause = ("SECTION 2. TERM AND RENEWAL", "The initial term is 2 years.")
    term_type, conf = ClauseClassifier.classify_clause(term_clause[0], term_clause[1])
    assert term_type in ["term", "renewal"]
    assert conf >= 0.85

    lim_clause = ("SECTION 8. LIMITATION OF LIABILITY", "Aggregate liability capped at $100k.")
    lim_type, conf = ClauseClassifier.classify_clause(lim_clause[0], lim_clause[1])
    assert lim_type == "liability"


def test_cross_reference_resolution():
    clauses = [
        {"id": "c1", "temp_id": "c1", "number": "SECTION 2.2", "heading": "Renewal", "text": "Notice requirement."},
        {"id": "c2", "temp_id": "c2", "number": "SECTION 12.1", "heading": "Notices", "text": "Refer to Section 2.2 for notice requirements."},
    ]

    refs = CrossReferenceResolver.extract_and_resolve(clauses)
    assert len(refs) == 1
    assert refs[0]["ref_text"] == "Section 2.2"
    assert refs[0]["resolved_clause_id"] == "c1"


def test_defined_terms_extraction():
    clauses = [
        {"id": "c1", "temp_id": "c1", "number": "1.1", "text": '"Services" means the cloud infrastructure and software provided under this Agreement.', "char_start": 0}
    ]

    terms = DefinedTermsExtractor.extract_defined_terms(clauses[0]["text"], clauses)
    assert len(terms) == 1
    assert terms[0]["term"] == "Services"
    assert "cloud infrastructure" in terms[0]["definition"]
