import re
from typing import Any, Dict, Optional, Tuple
from dateutil import parser as date_parser


def normalize_date(date_str: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses date string into ISO 8601 (YYYY-MM-DD).
    Returns (iso_date_string, error_message).
    """
    if not date_str or not date_str.strip():
        return None, "Empty date string"

    text = date_str.strip()
    # Clean up phrases like "15th day of January, 2026" -> "January 15, 2026"
    day_of_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s+day\s+of\s+([A-Za-z]+)[,\s]+(\d{4})', text, re.IGNORECASE)
    if day_of_match:
        text = f"{day_of_match.group(2)} {day_of_match.group(1)}, {day_of_match.group(3)}"

    try:
        dt = date_parser.parse(text, fuzzy=True)
        return dt.strftime("%Y-%m-%d"), None
    except Exception as e:
        return None, f"Could not parse date: {str(e)}"


def check_word_digit_mismatch(text: str) -> Optional[str]:
    """
    Checks if a phrase like "ninety (60) days" or "five hundred thousand (100,000)"
    has conflicting written word and numeric digit values.
    Returns warning message if mismatch found, else None.
    """
    if not text:
        return None

    WORD_TO_NUM = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
        "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000, "million": 1000000
    }

    # Pattern like: "ninety (60)" or "five hundred (100)"
    match = re.search(r'([A-Za-z\s\-]+)\s*[\(\[]\s*\$?([0-9,]+)\s*[\)\]]', text)
    if match:
        word_part = match.group(1).strip().lower()
        digit_part_str = match.group(2).replace(",", "").strip()

        if digit_part_str.isdigit():
            digit_val = int(digit_part_str)

            # Try basic single word lookup
            if word_part in WORD_TO_NUM:
                word_val = WORD_TO_NUM[word_part]
                if word_val != digit_val:
                    return f"Word/digit mismatch: written '{word_part}' vs numeric {digit_val}"
            # Composite words like "ninety (60)"
            words = [w.strip() for w in re.split(r'[\s\-]+', word_part) if w.strip() in WORD_TO_NUM]
            if words:
                # Sum simple compound numbers e.g. "ninety five" -> 95
                calc_val = 0
                temp = 0
                for w in words:
                    v = WORD_TO_NUM[w]
                    if v in (100, 1000, 1000000):
                        temp = (temp or 1) * v
                        calc_val += temp
                        temp = 0
                    else:
                        temp += v
                calc_val += temp
                if calc_val > 0 and calc_val != digit_val:
                    return f"Word/digit mismatch: written words suggest {calc_val} vs numeric {digit_val}"

    return None


def normalize_duration(duration_str: Optional[str]) -> Dict[str, Any]:
    """
    Parses duration string like '3 years', 'ninety (90) days', '12 months'.
    Returns normalized dictionary with duration details & word/digit mismatch flags.
    """
    if not duration_str or not duration_str.strip():
        return {"raw": duration_str, "unit": None, "value": None, "normalized_text": None, "warning": None}

    text = duration_str.strip()
    warning = check_word_digit_mismatch(text)

    # Extract digits
    digit_match = re.search(r'([0-9,]+)', text)
    digit_val = int(digit_match.group(1).replace(",", "")) if digit_match else None

    unit = None
    text_lower = text.lower()
    if "day" in text_lower:
        unit = "days"
    elif "month" in text_lower:
        unit = "months"
    elif "year" in text_lower or "yr" in text_lower:
        unit = "years"
    elif "week" in text_lower:
        unit = "weeks"

    norm_text = f"{digit_val} {unit}" if digit_val is not None and unit else text

    return {
        "raw": text,
        "value": digit_val,
        "unit": unit,
        "normalized_text": norm_text,
        "warning": warning
    }


def normalize_money(money_str: Optional[str]) -> Dict[str, Any]:
    """
    Parses money strings like '$500,000', 'USD 500,000', '$10,000 / month'.
    Returns structured amount, currency, frequency, and mismatch warning.
    """
    if not money_str or not money_str.strip():
        return {"raw": money_str, "amount": None, "currency": "USD", "period": None, "warning": None}

    text = money_str.strip()
    warning = check_word_digit_mismatch(text)

    # Detect currency
    currency = "USD"
    if "EUR" in text or "€" in text:
        currency = "EUR"
    elif "GBP" in text or "£" in text:
        currency = "GBP"
    elif "CAD" in text:
        currency = "CAD"
    elif "AUD" in text:
        currency = "AUD"

    # Extract numeric amount
    amount_match = re.search(r'[\$\€\£]?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|\d+(?:\.\d+)?)', text)
    amount = float(amount_match.group(1).replace(",", "")) if amount_match else None

    # Detect recurring period
    period = None
    text_lower = text.lower()
    if "month" in text_lower or "/mo" in text_lower or "per month" in text_lower:
        period = "monthly"
    elif "year" in text_lower or "/yr" in text_lower or "per year" in text_lower or "annually" in text_lower:
        period = "annually"
    elif "one-time" in text_lower or "total" in text_lower:
        period = "one_time"

    return {
        "raw": text,
        "amount": amount,
        "currency": currency,
        "period": period,
        "warning": warning
    }


def normalize_payment_terms(terms_str: Optional[str]) -> Dict[str, Any]:
    """
    Parses payment terms string into standardized format (e.g. 'Net 30', 'Net 45').
    """
    if not terms_str or not terms_str.strip():
        return {"raw": terms_str, "normalized": None}

    text = terms_str.strip()
    net_match = re.search(r'net\s*(\d+)', text, re.IGNORECASE)
    if net_match:
        days = net_match.group(1)
        return {"raw": text, "normalized": f"Net {days}", "due_days": int(days)}

    if "receipt" in text.lower():
        return {"raw": text, "normalized": "Due on Receipt", "due_days": 0}

    return {"raw": text, "normalized": text, "due_days": None}


def normalize_renewal_type(type_str: Optional[str]) -> str:
    """
    Normalizes renewal_type into enum: auto_renew, manual_opt_in, non_cancelable_term, not_specified
    """
    if not type_str:
        return "not_specified"

    text = type_str.lower()
    if "auto" in text or "automatic" in text or "successive" in text:
        return "auto_renew"
    if "opt-in" in text or "written notice" in text or "mutual agreement" in text or "option to renew" in text:
        return "manual_opt_in"
    if "non-cancelable" in text or "no renewal" in text or "expires" in text:
        return "non_cancelable_term"
    return "not_specified"
