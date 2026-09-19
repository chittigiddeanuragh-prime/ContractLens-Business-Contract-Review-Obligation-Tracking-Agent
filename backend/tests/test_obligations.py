import pytest
from datetime import date
from app.services.obligation_extractor import ObligationExtractorService


def test_obligation_as_of_date():
    as_of = ObligationExtractorService.get_as_of_date()
    assert isinstance(as_of, date)
    assert as_of.year == 2026
