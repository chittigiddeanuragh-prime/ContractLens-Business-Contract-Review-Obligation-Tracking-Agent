from typing import Dict, Tuple

PROMPT_VERSIONS: Dict[str, str] = {
    "ping_extract": "v1.0.0",
    "field_extraction": "v1.0.0",
    "extract_dates_and_term": "v1.0.0",
    "extract_renewal_and_termination": "v1.0.0",
    "extract_fees_and_liability": "v1.0.0",
    "extract_governing_law_and_disputes": "v1.0.0",
    "clause_segmentation": "v1.0.0",
    "obligation_extraction": "v1.0.0",
    "grounded_qa": "v1.0.0",
}

PROMPTS: Dict[str, str] = {
    "ping_extract": (
        "You are a contract intelligence test system. Given any input text, extract a tiny summary JSON object "
        "with keys 'status' (string, value 'ok'), 'contract_type' (string), and 'summary' (string)."
    ),
    "field_extraction": (
        "You are a contract metadata extraction assistant. Extract specified key fields from the contract text "
        "along with exact quotes, clause numbers, and page numbers."
    ),
    "extract_dates_and_term": (
        "You are a legal contract field extraction assistant. Extract contract parties, effective date, expiration date, and term length."
    ),
    "extract_renewal_and_termination": (
        "You are a legal contract field extraction assistant. Extract renewal type, renewal term duration, and non-renewal notice period."
    ),
    "extract_fees_and_liability": (
        "You are a legal contract field extraction assistant. Extract payment terms, total fees or contract value, and limitation of liability cap."
    ),
    "extract_governing_law_and_disputes": (
        "You are a legal contract field extraction assistant. Extract termination for convenience, termination notice period, and governing law jurisdiction."
    ),
    "clause_segmentation": (
        "You are a legal document parser. Segment the contract text into a hierarchical tree of numbered clauses."
    ),
    "obligation_extraction": (
        "Extract active legal obligations, responsible party, trigger rule, severity, and deadline type."
    ),
    "grounded_qa": (
        "Answer the user query based ONLY on the provided contract clauses. If not found, output 'Not found in the contract.'"
    ),
}


def get_prompt(task_name: str) -> Tuple[str, str]:
    """
    Returns (system_prompt, version) for the given task.
    """
    if task_name in PROMPTS:
        return PROMPTS[task_name], PROMPT_VERSIONS.get(task_name, "v1.0.0")
    elif task_name.startswith("extract_"):
        return PROMPTS["field_extraction"], "v1.0.0"
    else:
        raise ValueError(f"Unknown prompt task: {task_name}")
