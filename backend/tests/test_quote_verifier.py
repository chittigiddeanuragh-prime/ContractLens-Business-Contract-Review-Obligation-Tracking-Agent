import pytest
from app.services.quote_verifier import QuoteVerifier, normalize_with_map


def test_normalize_with_map():
    raw_text = "This   is a “test” — with   dashes."
    norm_str, idx_map = normalize_with_map(raw_text)
    assert norm_str == 'This is a "test" - with dashes.'
    assert len(idx_map) == len(norm_str)
    # Ensure mapping matches
    for i, norm_char in enumerate(norm_str):
        orig_char_idx = idx_map[i]
        assert orig_char_idx < len(raw_text)


def test_quote_verifier_exact_match():
    canonical = "This Agreement is entered into on January 15, 2026 by and between Acme Corp and Beta LLC."
    quote = "January 15, 2026"
    res = QuoteVerifier.verify_quote(quote, canonical)

    assert res["verification_status"] == "exact"
    assert res["char_start"] == 34
    assert res["char_end"] == 50
    assert canonical[res["char_start"]:res["char_end"]] == quote
    assert res["similarity"] == 1.0


def test_quote_verifier_whitespace_dash_normalization():
    canonical = "Liability shall not exceed   Five Hundred Thousand Dollars ($500,000) — total."
    quote = 'Five Hundred Thousand Dollars ($500,000) - total.'
    res = QuoteVerifier.verify_quote(quote, canonical)

    assert res["verification_status"] in ("exact", "outside_clause")
    assert res["char_start"] is not None
    assert res["char_end"] is not None


def test_quote_verifier_hallucinated_quote_rejection():
    canonical = "This contract expires in 2 years."
    quote = "This contract shall automatically renew for 5 years."
    res = QuoteVerifier.verify_quote(quote, canonical)

    assert res["verification_status"] == "failed"
    assert res["char_start"] is None
    assert res["char_end"] is None
    assert res["similarity"] == 0.0
