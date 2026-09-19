import pytest
from app.services.normalizers import (
    normalize_date,
    normalize_duration,
    normalize_money,
    normalize_payment_terms,
    normalize_renewal_type,
    check_word_digit_mismatch
)
from app.services.confidence import ConfidenceCalculator
from app.services.baseline_extractor import BaselineExtractor


def test_normalizers():
    # Date
    d_iso, d_err = normalize_date("January 15, 2026")
    assert d_iso == "2026-01-15"
    assert d_err is None

    # Duration
    dur = normalize_duration("ninety (90) days")
    assert dur["value"] == 90
    assert dur["unit"] == "days"
    assert dur["warning"] is None

    # Money
    m = normalize_money("$500,000")
    assert m["amount"] == 500000.0
    assert m["currency"] == "USD"

    # Payment terms
    p = normalize_payment_terms("Net 45 days")
    assert p["normalized"] == "Net 45"
    assert p["due_days"] == 45

    # Renewal
    r = normalize_renewal_type("automatic 1-year renewal")
    assert r == "auto_renew"


def test_word_digit_mismatch():
    warn = check_word_digit_mismatch("ninety (60) days")
    assert warn is not None
    assert "mismatch" in warn.lower()

    no_warn = check_word_digit_mismatch("ninety (90) days")
    assert no_warn is None


def test_confidence_calculator():
    res_exact = {
        "verification_status": "exact",
        "similarity": 1.0
    }
    calc = ConfidenceCalculator.calculate_confidence(
        field_name="effective_date",
        verification_res=res_exact,
        cited_clause_type="Preamble",
        normalized_success=True,
        llm_prob=0.95,
        baseline_match=True
    )

    assert calc["confidence"] == 1.0
    assert calc["review_status"] == "verified"
    assert calc["confidence_breakdown"]["quote_match"] == 0.40

    # Test hallucinated quote penalty
    res_fail = {"verification_status": "failed", "similarity": 0.0}
    calc_fail = ConfidenceCalculator.calculate_confidence(
        field_name="effective_date",
        verification_res=res_fail,
        normalized_success=False
    )
    assert calc_fail["confidence"] <= 0.15
    assert calc_fail["review_status"] in ("needs_review", "low_confidence", "not_found")


def test_baseline_extractor():
    text = "This Agreement is dated as of January 15, 2026 by and between Party A and Party B. Payment terms shall be Net 30."
    clauses = [{"char_start": 0, "char_end": len(text), "id": "c1", "temp_id": "c1"}]

    eff_date = BaselineExtractor.extract_single_field("effective_date", text, clauses)
    assert eff_date["value_raw"] == "January 15, 2026"
    assert eff_date["verification_status"] in ("exact", "outside_clause")

    pay_terms = BaselineExtractor.extract_single_field("payment_terms", text, clauses)
    assert pay_terms["value_raw"] == "Net 30"
