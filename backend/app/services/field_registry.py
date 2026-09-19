from typing import Any, Dict, List, Optional


class FieldSpec:
    def __init__(
        self,
        name: str,
        label: str,
        value_type: str,
        target_clause_types: List[str],
        keyword_hints: List[str],
        description: str,
        group: str,
    ):
        self.name = name
        self.label = label
        self.value_type = value_type
        self.target_clause_types = target_clause_types
        self.keyword_hints = keyword_hints
        self.description = description
        self.group = group


FIELD_REGISTRY: Dict[str, FieldSpec] = {
    # Group A: Parties & Dates
    "parties": FieldSpec(
        name="parties",
        label="Contract Parties",
        value_type="party_list",
        target_clause_types=["definitions", "preamble", "other"],
        keyword_hints=["between", "entered into", "client", "vendor", "party"],
        description="The contracting legal entities and their assigned roles (e.g., Client, Vendor).",
        group="A",
    ),
    "effective_date": FieldSpec(
        name="effective_date",
        label="Effective Date",
        value_type="date",
        target_clause_types=["term", "preamble", "definitions"],
        keyword_hints=["effective date", "effective as of", "commencing on", "dated"],
        description="The date on which the agreement becomes active and legally binding.",
        group="A",
    ),
    "expiration_date": FieldSpec(
        name="expiration_date",
        label="Expiration Date",
        value_type="date",
        target_clause_types=["term", "renewal", "termination"],
        keyword_hints=["expire", "expiration", "end date", "terminate on"],
        description="The fixed end date of the agreement term if specified.",
        group="A",
    ),
    "term_length": FieldSpec(
        name="term_length",
        label="Initial Term Length",
        value_type="duration",
        target_clause_types=["term", "renewal"],
        keyword_hints=["initial term", "period of", "years", "months", "duration"],
        description="The total duration of the initial agreement term (e.g. 2 years).",
        group="A",
    ),

    # Group B: Renewal & Non-Renewal Terms
    "renewal_type": FieldSpec(
        name="renewal_type",
        label="Renewal Type",
        value_type="enum",
        target_clause_types=["renewal", "term"],
        keyword_hints=["automatically renew", "auto-renew", "successive", "extension", "manual"],
        description="Whether the contract renews automatically, manually, or not at all.",
        group="B",
    ),
    "renewal_term": FieldSpec(
        name="renewal_term",
        label="Renewal Term Duration",
        value_type="duration",
        target_clause_types=["renewal", "term"],
        keyword_hints=["renewal period", "successive terms", "additional year", "one year"],
        description="The length of each subsequent renewal period.",
        group="B",
    ),
    "notice_period_nonrenewal": FieldSpec(
        name="notice_period_nonrenewal",
        label="Non-Renewal Notice Period",
        value_type="duration",
        target_clause_types=["renewal", "term", "notices"],
        keyword_hints=["notice of non-renewal", "days prior", "written notice", "expiration"],
        description="Required advance notice period to prevent automatic renewal (e.g. 90 days).",
        group="B",
    ),

    # Group C: Commercial & Liability
    "payment_terms": FieldSpec(
        name="payment_terms",
        label="Payment Terms",
        value_type="text",
        target_clause_types=["payment", "fees"],
        keyword_hints=["net 30", "net 45", "due within", "invoicing", "payable"],
        description="Payment schedule and credit terms (e.g. Net 30 days from invoice).",
        group="C",
    ),
    "contract_value_or_fees": FieldSpec(
        name="contract_value_or_fees",
        label="Contract Value / Fees",
        value_type="money",
        target_clause_types=["fees", "payment"],
        keyword_hints=["total fee", "annual fee", "monthly fee", "$", "USD"],
        description="Total monetary contract value or recurring subscription fees.",
        group="C",
    ),
    "liability_cap": FieldSpec(
        name="liability_cap",
        label="Limitation of Liability Cap",
        value_type="money",
        target_clause_types=["liability"],
        keyword_hints=["aggregate liability", "exceed", "total liability", "fees paid"],
        description="Maximum aggregate liability amount or cap formula.",
        group="C",
    ),

    # Group D: Termination & Governing Law
    "termination_for_convenience": FieldSpec(
        name="termination_for_convenience",
        label="Termination for Convenience",
        value_type="boolean",
        target_clause_types=["termination"],
        keyword_hints=["without cause", "for convenience", "any reason"],
        description="Whether either party can terminate without specifying cause.",
        group="D",
    ),
    "termination_notice_period": FieldSpec(
        name="termination_notice_period",
        label="Termination Notice Period",
        value_type="duration",
        target_clause_types=["termination", "notices"],
        keyword_hints=["notice of termination", "days written notice", "prior notice"],
        description="Advance written notice required for convenience or cause termination.",
        group="D",
    ),
    "governing_law": FieldSpec(
        name="governing_law",
        label="Governing Law & Jurisdiction",
        value_type="text",
        target_clause_types=["governing_law", "dispute_resolution"],
        keyword_hints=["governed by", "laws of", "jurisdiction", "state of"],
        description="State, country, or jurisdiction whose laws govern the agreement.",
        group="D",
    ),
}

GROUPS = {
    "A": ["parties", "effective_date", "expiration_date", "term_length"],
    "B": ["renewal_type", "renewal_term", "notice_period_nonrenewal"],
    "C": ["payment_terms", "contract_value_or_fees", "liability_cap"],
    "D": ["termination_for_convenience", "termination_notice_period", "governing_law"],
}

EXTRACTION_GROUPS = {
    "dates_and_term": {
        "name": "Group A: Parties & Dates",
        "fields": GROUPS["A"]
    },
    "renewal_and_termination": {
        "name": "Group B: Renewal & Non-Renewal",
        "fields": GROUPS["B"]
    },
    "fees_and_liability": {
        "name": "Group C: Commercial & Liability",
        "fields": GROUPS["C"]
    },
    "governing_law_and_disputes": {
        "name": "Group D: Termination & Governing Law",
        "fields": GROUPS["D"]
    }
}

TARGET_FIELDS = [
    {
        "field_name": spec.name,
        "display_label": spec.label,
        "value_type": spec.value_type,
        "target_clause_types": spec.target_clause_types,
        "keyword_hints": spec.keyword_hints,
        "description": spec.description,
        "group_name": spec.group
    }
    for spec in FIELD_REGISTRY.values()
]


def get_field_def(field_name: str) -> Optional[Dict[str, Any]]:
    spec = FIELD_REGISTRY.get(field_name)
    if not spec:
        return None
    return {
        "field_name": spec.name,
        "display_label": spec.label,
        "value_type": spec.value_type,
        "target_clause_types": spec.target_clause_types,
        "keyword_hints": spec.keyword_hints,
        "description": spec.description,
        "group_name": spec.group
    }
