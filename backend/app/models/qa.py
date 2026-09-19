from typing import Optional
from sqlalchemy import String, Text, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BaseModelMixin


class QAConversation(Base, BaseModelMixin):
    __tablename__ = "qa_conversations"

    version_id: Mapped[str] = mapped_column(String(36), ForeignKey("contract_versions.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Contract Q&A")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active") # active, archived

    messages: Mapped[list["QAMessage"]] = relationship("QAMessage", back_populates="conversation", cascade="all, delete-orphan")


class QAMessage(Base, BaseModelMixin):
    __tablename__ = "qa_messages"

    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("qa_conversations.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False) # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    answer_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True) # answered, partially_answered, not_found, out_of_scope, needs_clarification, unavailable
    route: Mapped[Optional[str]] = mapped_column(String(32), nullable=True) # fields, obligations, clauses, hybrid, compare_unsupported
    answer_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON structured answer
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_breakdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON
    retrieved_clause_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON list
    rewritten_question: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cache_hit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    conversation: Mapped["QAConversation"] = relationship("QAConversation", back_populates="messages")
    feedback: Mapped[Optional["QAFeedback"]] = relationship("QAFeedback", back_populates="message", uselist=False)


class QAFeedback(Base, BaseModelMixin):
    __tablename__ = "qa_feedback"

    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("qa_messages.id"), nullable=False, index=True)
    rating: Mapped[str] = mapped_column(String(16), nullable=False) # up, down
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    message: Mapped["QAMessage"] = relationship("QAMessage", back_populates="feedback")
