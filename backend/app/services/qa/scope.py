import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

OUT_OF_SCOPE_TEXT = "I can only answer questions using the text of this contract, and I can't provide legal advice."


class QAScopeService:
    @staticmethod
    def check_out_of_scope(question: str) -> Tuple[bool, Optional[str]]:
        q_lower = question.strip().lower()

        # Prompt extraction / system prompt reveal / override attempts
        if any(w in q_lower for w in ["reveal system prompt", "show api key", "ignore all rules", "system prompt", "override", "api keys"]):
            logger.warning(f"Prompt injection / system prompt extraction attempt detected: '{question[:50]}'")
            return True, OUT_OF_SCOPE_TEXT

        # Legal advice / subjective opinion / enforceability questions
        legal_advice_keywords = [
            "should i sign", "is this enforceable", "enforceable", "will i win", "is this legal",
            "is this fair", "should i accept", "what should i do", "advice"
        ]

        if any(kw in q_lower for kw in legal_advice_keywords):
            return True, OUT_OF_SCOPE_TEXT

        return False, None
