import json
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.contract import Contract, ContractVersion
from app.models.clause import Clause
from app.models.document_page import DocumentPage
from app.models.audit_log import AuditLog
from app.models.qa import QAConversation, QAMessage, QAFeedback
from app.services.qa.intake import QAIntakeService
from app.services.qa.router import QARouter
from app.services.qa.structured import StructuredAnswerer, NOT_FOUND_TEXT
from app.services.qa.retriever import QARetriever
from app.services.qa.verifier import QACitationVerifier
from app.services.qa.confidence import QAConfidenceCalculator
from app.services.qa.scope import QAScopeService
from app.agents.qa_answerer import QAAnswererAgent

router = APIRouter(prefix="/qa", tags=["qa"])


class AskQuestionRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    rating: str  # up, down
    comment: Optional[str] = None


@router.post("/contracts/{contract_id}/versions/{version_id}/qa/ask")
def ask_question(
    contract_id: str,
    version_id: str,
    req: AskQuestionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    start_time = time.time()
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Rate limiting (10 per minute)
    if not QAIntakeService.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. You can ask up to 10 questions per minute."
        )

    # Validate version status
    version = db.query(ContractVersion).filter_by(id=version_id, contract_id=contract_id).first()
    if not version or version.status not in ("ready", "ready_with_warnings", "segmented"):
        raise HTTPException(
            status_code=409,
            detail=f"Contract version status is '{version.status if version else 'not_found'}'. Q&A requires status 'ready' or 'ready_with_warnings'."
        )

    # Validate and clean question
    try:
        cleaned_question = QAIntakeService.validate_and_clean_question(req.question)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    # Get or create conversation
    if req.conversation_id:
        conversation = db.query(QAConversation).filter_by(id=req.conversation_id, version_id=version_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    else:
        conversation = QAConversation(
            version_id=version_id,
            title=cleaned_question[:40],
            org_id=version.org_id
        )
        db.add(conversation)
        db.flush()

    # Save user message
    user_msg = QAMessage(
        conversation_id=conversation.id,
        role="user",
        content=cleaned_question,
        org_id=version.org_id
    )
    db.add(user_msg)
    db.commit()

    # Handle vague question
    if QAIntakeService.is_too_vague(cleaned_question):
        suggested = [
            "When does this contract expire?",
            "What is the limitation of liability cap?",
            "What are the termination notice requirements?"
        ]
        asst_msg = QAMessage(
            conversation_id=conversation.id,
            role="assistant",
            content="Could you clarify your question? Here are a few suggested topics:",
            answer_status="needs_clarification",
            answer_json=json.dumps({"suggestions": suggested}),
            confidence=1.0,
            org_id=version.org_id
        )
        db.add(asst_msg)
        db.commit()
        return _format_message_response(asst_msg, conversation.id, suggested=suggested)

    # Check out-of-scope (legal advice / prompt injection)
    is_out_of_scope, scope_msg = QAScopeService.check_out_of_scope(cleaned_question)
    if is_out_of_scope:
        asst_msg = QAMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=scope_msg,
            answer_status="out_of_scope",
            confidence=1.0,
            org_id=version.org_id
        )
        db.add(asst_msg)
        db.commit()
        return _format_message_response(asst_msg, conversation.id)

    # Check follow-up rewriting
    prev_turns = [
        {"user": m.content}
        for m in conversation.messages
        if m.role == "user" and m.id != user_msg.id
    ]
    standalone_q, was_rewritten = QAIntakeService.rewrite_followup_question(cleaned_question, prev_turns)

    # Route question
    route_data = QARouter.route_question(standalone_q)
    route = route_data["route"]
    matched_fields = route_data["matched_fields"]

    answer_payload = {}
    clauses_db = db.query(Clause).filter_by(version_id=version_id).all()
    clauses_data = [
        {
            "id": c.id,
            "temp_id": getattr(c, "temp_id", None) or c.id,
            "clause_number": c.number,
            "heading": c.heading,
            "category": c.clause_type,
            "text": c.text,
            "char_start": c.char_start,
            "char_end": c.char_end,
            "page_start": c.page_start
        }
        for c in clauses_db
    ]

    pages_db = db.query(DocumentPage).filter_by(version_id=version_id).all()
    pages_data = [
        {"page_number": p.page_number, "char_start": p.char_start, "char_end": p.char_end}
        for p in pages_db
    ]

    retrieved_clause_ids = []

    if route == "compare_unsupported":
        answer_payload = {
            "answer_status": "answered",
            "answer_text": "Version comparison isn't available yet.",
            "claims": [],
            "citations": []
        }
    elif route == "fields":
        answer_payload = StructuredAnswerer.answer_fields_route(db, version_id, matched_fields)
    elif route == "obligations":
        answer_payload = StructuredAnswerer.answer_obligations_route(db, version_id)
    else:
        # Semantic Clauses / Hybrid Route
        ret_res = QARetriever.retrieve_relevant_clauses(
            query=standalone_q,
            clauses=clauses_data,
            canonical_text=version.canonical_text or ""
        )
        if not ret_res["gate_passed"]:
            answer_payload = {
                "answer_status": "not_found",
                "answer_text": NOT_FOUND_TEXT,
                "scope_line": f"Searched canonical contract text for: {ret_res['scanned_terms']}.",
                "claims": [],
                "citations": []
            }
        else:
            ret_clauses = ret_res["retrieved_clauses"]
            retrieved_clause_ids = [c["id"] for c in ret_clauses]

            agent = QAAnswererAgent(db)
            answer_payload = agent.answer_question(
                question=standalone_q,
                retrieved_clauses=ret_clauses,
                canonical_text=version.canonical_text or "",
                clauses_all=clauses_data,
                pages_data=pages_data,
                file_hash=version.file_hash
            )

    # Calculate Confidence
    conf_res = QAConfidenceCalculator.calculate_qa_confidence(
        llm_confidence=0.90,
        answer_status=answer_payload.get("answer_status", "answered"),
        citations=answer_payload.get("citations", []),
        dropped_claims=answer_payload.get("dropped_claim_count", 0)
    )

    latency_ms = int((time.time() - start_time) * 1000)

    # Save Assistant QAMessage
    asst_msg = QAMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=answer_payload.get("answer_text", NOT_FOUND_TEXT),
        answer_status=answer_payload.get("answer_status", "answered"),
        route=route,
        answer_json=json.dumps(answer_payload),
        confidence=conf_res["confidence"],
        confidence_breakdown=json.dumps(conf_res["confidence_breakdown"]),
        retrieved_clause_ids=json.dumps(retrieved_clause_ids),
        rewritten_question=standalone_q if was_rewritten else None,
        latency_ms=latency_ms,
        org_id=version.org_id
    )
    db.add(asst_msg)
    db.commit()

    suggested = [
        "What happens if I terminate early?",
        "What is the limitation of liability cap?",
        "Does the contract mention cryptocurrency payments?"
    ]

    return _format_message_response(asst_msg, conversation.id, payload=answer_payload, suggested=suggested)


@router.get("/contracts/{contract_id}/versions/{version_id}/qa/suggested-questions")
def get_suggested_questions(contract_id: str, version_id: str, db: Session = Depends(get_db)):
    return {
        "suggested_questions": [
            "When does this contract expire?",
            "What is the notice period for non-renewal?",
            "What happens if I terminate early?",
            "What is the limitation of liability cap?",
            "What are the payment terms?",
            "Which state's governing law applies?",
            "Does the contract mention cryptocurrency payments?" # Demo unanswerable question
        ]
    }


@router.get("/contracts/{contract_id}/versions/{version_id}/qa/conversations")
def list_conversations(contract_id: str, version_id: str, db: Session = Depends(get_db)):
    convs = db.query(QAConversation).filter_by(version_id=version_id, status="active").all()
    return {
        "version_id": version_id,
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "message_count": len(c.messages)
            }
            for c in convs
        ]
    }


@router.get("/qa/conversations/{conversation_id}")
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conv = db.query(QAConversation).filter_by(id=conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conv.id,
        "version_id": conv.version_id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "answer_status": m.answer_status,
                "route": m.route,
                "confidence": m.confidence,
                "answer_payload": json.loads(m.answer_json) if m.answer_json else None,
                "created_at": m.created_at.isoformat()
            }
            for m in conv.messages
        ]
    }


@router.delete("/qa/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conv = db.query(QAConversation).filter_by(id=conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.status = "archived"
    audit = AuditLog(
        user_id="system",
        action="delete_qa_conversation",
        entity_type="qa_conversation",
        entity_id=conversation_id,
        changes_after=json.dumps({"status": "archived"}),
        org_id=conv.org_id
    )
    db.add(audit)
    db.commit()

    return {"message": "Conversation archived", "id": conversation_id}


@router.post("/qa/messages/{message_id}/feedback")
def submit_feedback(message_id: str, req: FeedbackRequest, db: Session = Depends(get_db)):
    msg = db.query(QAMessage).filter_by(id=message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    feedback = db.query(QAFeedback).filter_by(message_id=message_id).first()
    if not feedback:
        feedback = QAFeedback(message_id=message_id, rating=req.rating, comment=req.comment, org_id=msg.org_id)
        db.add(feedback)
    else:
        feedback.rating = req.rating
        feedback.comment = req.comment

    audit = AuditLog(
        user_id="system",
        action="submit_qa_feedback",
        entity_type="qa_feedback",
        entity_id=message_id,
        changes_after=json.dumps({"rating": req.rating, "comment": req.comment}),
        org_id=msg.org_id
    )
    db.add(audit)
    db.commit()

    return {"message": "Feedback recorded", "message_id": message_id}


def _format_message_response(msg: QAMessage, conversation_id: str, payload: Dict = None, suggested: List[str] = None):
    return {
        "id": msg.id,
        "conversation_id": conversation_id,
        "role": msg.role,
        "content": msg.content,
        "answer_status": msg.answer_status,
        "route": msg.route,
        "confidence": msg.confidence,
        "confidence_breakdown": json.loads(msg.confidence_breakdown) if msg.confidence_breakdown else None,
        "answer_payload": payload or (json.loads(msg.answer_json) if msg.answer_json else None),
        "suggested_followups": suggested or [],
        "latency_ms": msg.latency_ms
    }
