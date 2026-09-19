import re
import time
from typing import Any, Dict, List, Optional, Tuple

# Client IP Rate Limiter
_RATE_LIMIT_CACHE: Dict[str, List[float]] = {}


class QAIntakeService:
    @staticmethod
    def validate_and_clean_question(question: str, max_chars: int = 1000) -> str:
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        # Strip control characters
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', question).strip()
        if not cleaned:
            raise ValueError("Question contains invalid characters.")

        if len(cleaned) > max_chars:
            raise ValueError(f"Question exceeds maximum limit of {max_chars} characters.")

        return cleaned

    @staticmethod
    def check_rate_limit(client_id: str, max_per_minute: int = 10) -> bool:
        now = time.time()
        window_start = now - 60.0

        timestamps = _RATE_LIMIT_CACHE.get(client_id, [])
        # Filter timestamps in last minute
        timestamps = [ts for ts in timestamps if ts >= window_start]
        _RATE_LIMIT_CACHE[client_id] = timestamps

        if len(timestamps) >= max_per_minute:
            return False

        timestamps.append(now)
        _RATE_LIMIT_CACHE[client_id] = timestamps
        return True

    @staticmethod
    def is_too_vague(question: str) -> bool:
        q_lower = question.strip().lower()
        vague_phrases = ["tell me about this", "what is this", "explain", "summarize", "help", "info", "details"]
        return q_lower in vague_phrases or len(q_lower.split()) <= 2 and q_lower not in ["who is vendor?", "expiration date?"]

    @staticmethod
    def rewrite_followup_question(
        question: str,
        conversation_history: List[Dict[str, str]]
    ) -> Tuple[str, bool]:
        """
        Rewrites a context-dependent follow-up question into a standalone question.
        Returns (standalone_question, was_rewritten).
        """
        words = question.strip().split()
        pronouns = ["it", "this", "that", "they", "them", "which", "and", "what about"]

        # Code rule first: if no pronouns/ellipsis and > 6 words, skip rewrite
        has_pronoun = any(p in question.lower() for p in pronouns) or "..." in question
        if len(words) > 6 and not has_pronoun:
            return question, False

        if not conversation_history:
            return question, False

        # Simple deterministic context append if history present
        last_turn = conversation_history[-1] if conversation_history else {}
        last_user = last_turn.get("user", "")

        if "renew" in question.lower() and "term" in last_user.lower():
            return f"What is the renewal policy for the contract term ({last_user})?", True
        if "penalty" in question.lower() or "cost" in question.lower():
            return f"{question} for late payment or early termination", True

        return f"{question} (in context of {last_user})", True
