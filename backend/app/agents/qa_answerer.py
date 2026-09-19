import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.llm.client import LLMClient
from app.llm.safety import wrap_untrusted
from app.services.qa.verifier import QACitationVerifier, NOT_FOUND_TEXT

logger = logging.getLogger(__name__)


class QAAnswererAgent:
    """
    LLM Grounded Q&A Answerer Agent.
    Strictly enforces Non-Negotiable Invariants Q1-Q8:
      Q1: Every factual claim verified by code against canonical text.
      Q2: Exact refusal text: 'Not found in the contract.'
      Q3: LLM refers only to provided clause IDs.
      Q4: No outside knowledge / legal advice.
      Q6: Both contract context and user question wrapped with wrap_untrusted().
      Q8: Graceful degradation when LLM unavailable.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def answer_question(
        self,
        question: str,
        retrieved_clauses: List[Dict[str, Any]],
        canonical_text: str,
        clauses_all: List[Dict[str, Any]],
        pages_data: List[Dict[str, Any]],
        file_hash: Optional[str] = None
    ) -> Dict[str, Any]:

        if not retrieved_clauses:
            return {
                "answer_status": "not_found",
                "answer_text": NOT_FOUND_TEXT,
                "claims": [],
                "citations": []
            }

        # Format context clauses
        clause_blocks = []
        for c in retrieved_clauses:
            c_id = c.get("id") or c.get("temp_id")
            c_num = c.get("number") or c.get("clause_number", "")
            c_page = c.get("page_start", 1)
            c_type = c.get("category") or c.get("clause_type", "other")
            clause_blocks.append(f"[CLAUSE id={c_id} number={c_num} page={c_page} type={c_type}]\n{c.get('text')}\n[/CLAUSE]")

        context_str = "\n\n".join(clause_blocks)
        wrapped_context = wrap_untrusted(context_str)
        wrapped_question = f"<UNTRUSTED_USER_QUESTION>\n{question}\n</UNTRUSTED_USER_QUESTION>"

        system_prompt = (
            "You are a legal contract Q&A assistant. Answer the user question based ONLY on the provided clauses.\n"
            "CRITICAL RULES:\n"
            "1. Answer ONLY using facts present in the provided clauses.\n"
            "2. Each claim must be a concise factual statement with a verbatim contiguous quote copied from the cited clause.\n"
            "3. Do NOT give legal advice, predictions, or opinions on enforceability.\n"
            "4. If the clauses do not answer the question, return status 'not_found' with empty claims.\n"
            "5. Format your output strictly as a JSON object with keys: 'status', 'claims' (list of {text, citations: [{clause_id, quote}]})."
        )

        user_prompt = (
            f"Question:\n{wrapped_question}\n\n"
            f"Contract Context:\n{wrapped_context}\n\n"
            "Respond ONLY with a valid JSON object."
        )

        try:
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                coro = LLMClient.run(
                    task="grounded_qa",
                    system=system_prompt,
                    user=user_prompt,
                    file_hash=file_hash,
                    db=self.db
                )
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, coro)
                    llm_res = future.result(timeout=15)
            else:
                llm_res = loop.run_until_complete(
                    LLMClient.run(
                        task="grounded_qa",
                        system=system_prompt,
                        user=user_prompt,
                        file_hash=file_hash,
                        db=self.db
                    )
                )

            status_val = llm_res.get("status", "answered")
            raw_claims = llm_res.get("claims", [])

            if status_val == "not_found" or not raw_claims:
                return {
                    "answer_status": "not_found",
                    "answer_text": NOT_FOUND_TEXT,
                    "claims": [],
                    "citations": []
                }

            # Verify claims with Code Citation Verifier (Invariant Q1)
            verified_res = QACitationVerifier.verify_and_assemble_answer(
                claims=raw_claims,
                canonical_text=canonical_text,
                clauses=clauses_all,
                pages_data=pages_data
            )
            return verified_res

        except Exception as e:
            logger.warning(f"LLM QA generation failed: {e}. Falling back to retrieved clauses (Invariant Q8).")
            # Invariant Q8: Graceful degradation when LLM fails
            top_clause_text = "\n".join([f"• Section {c.get('number', '')}: {c.get('text', '')[:150]}..." for c in retrieved_clauses[:3]])
            fallback_text = f"AI answering is unavailable right now; here are the most relevant clauses:\n{top_clause_text}"

            return {
                "answer_status": "unavailable",
                "answer_text": fallback_text,
                "claims": [],
                "citations": [
                    {
                        "citation_index": idx + 1,
                        "clause_id": c.get("id") or c.get("temp_id"),
                        "quote": c.get("text", "")[:100],
                        "page_start": c.get("page_start", 1)
                    }
                    for idx, c in enumerate(retrieved_clauses[:3])
                ]
            }
