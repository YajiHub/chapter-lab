"""ORM models. FROZEN after Phase 0: change only through the orchestrator + a new migration."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _now() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def _fk(target: str, ondelete: str = "CASCADE", nullable: bool = False) -> Mapped[Any]:
    return mapped_column(
        UUID(as_uuid=True), ForeignKey(target, ondelete=ondelete), nullable=nullable, index=True
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('student','admin')", name="role_valid"),)

    id: Mapped[uuid.UUID] = _pk()
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="student")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _now()


class UserSession(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = _pk()
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = _fk("users.id")
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = _now()


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (Index("ix_lessons_owner_created", "owner_id", "created_at"),)

    id: Mapped[uuid.UUID] = _pk()
    owner_id: Mapped[uuid.UUID] = _fk("users.id")
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class StudyPack(Base):
    __tablename__ = "study_packs"
    __table_args__ = (Index("ix_packs_owner_created", "owner_id", "created_at"),)

    id: Mapped[uuid.UUID] = _pk()
    lesson_id: Mapped[uuid.UUID] = _fk("lessons.id")
    owner_id: Mapped[uuid.UUID] = _fk("users.id")  # denormalized for one-hop ownership checks
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    # Snapshot of the lesson at generation time: [{"id": 1, "text": "..."}]
    source_paragraphs: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    guide: Mapped[list[dict[str, str]]] = mapped_column(JSONB, nullable=False)
    comparison: Mapped[list[dict[str, str]] | None] = mapped_column(JSONB)
    ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provider: Mapped[str | None] = mapped_column(String(32))
    model: Mapped[str | None] = mapped_column(String(128))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("pack_id", "position", name="uq_questions_pack_position"),
        CheckConstraint("position BETWEEN 1 AND 5", name="position_valid"),
        CheckConstraint("correct_choice BETWEEN 0 AND 3", name="correct_choice_valid"),
        CheckConstraint("paragraph_id >= 1", name="paragraph_id_valid"),
    )

    id: Mapped[uuid.UUID] = _pk()
    pack_id: Mapped[uuid.UUID] = _fk("study_packs.id")
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    choices: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    correct_choice: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    paragraph_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quote: Mapped[str] = mapped_column(Text, nullable=False)


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        CheckConstraint("status IN ('in_progress','completed')", name="status_valid"),
        Index("ix_attempts_user_started", "user_id", "started_at"),
    )

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _fk("users.id")
    pack_id: Mapped[uuid.UUID] = _fk("study_packs.id")
    retry_of_attempt_id: Mapped[uuid.UUID | None] = _fk(
        "attempts.id", ondelete="SET NULL", nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="in_progress")
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = _now()
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AttemptItem(Base):
    """Snapshot of one question at attempt start plus the student's answer (ER: ATTEMPT_ANSWER)."""

    __tablename__ = "attempt_items"
    __table_args__ = (
        UniqueConstraint("attempt_id", "position", name="uq_attempt_items_position"),
        CheckConstraint("correct_choice BETWEEN 0 AND 3", name="correct_choice_valid"),
        CheckConstraint(
            "chosen_choice IS NULL OR chosen_choice BETWEEN 0 AND 3", name="chosen_choice_valid"
        ),
    )

    id: Mapped[uuid.UUID] = _pk()
    attempt_id: Mapped[uuid.UUID] = _fk("attempts.id")
    question_id: Mapped[uuid.UUID | None] = _fk("questions.id", ondelete="SET NULL", nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    choices: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    correct_choice: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    paragraph_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    passage_text: Mapped[str] = mapped_column(Text, nullable=False)
    chosen_choice: Mapped[int | None] = mapped_column(Integer)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GenerationRun(Base):
    """Metadata only: never store lesson text or raw provider output here."""

    __tablename__ = "generation_runs"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('running','success','quota','timeout','invalid_output','unavailable')",
            name="outcome_valid",
        ),
        Index("ix_generation_runs_user_started", "user_id", "started_at"),
    )

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _fk("users.id")
    lesson_id: Mapped[uuid.UUID] = _fk("lessons.id")
    started_at: Mapped[datetime] = _now()
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False, default="running")
    provider: Mapped[str | None] = mapped_column(String(32))
    model: Mapped[str | None] = mapped_column(String(128))
    # [{"provider": "gemini", "model": "...", "outcome": "quota", "ms": 812}]
    provider_trace: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    error_code: Mapped[str | None] = mapped_column(String(64))
    pack_id: Mapped[uuid.UUID | None] = _fk("study_packs.id", ondelete="SET NULL", nullable=True)


class IssueReport(Base):
    __tablename__ = "issue_reports"
    __table_args__ = (
        CheckConstraint(
            "reason IN ('wrong_answer','unsupported_source','unclear_question')",
            name="reason_valid",
        ),
    )

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _fk("users.id")
    question_id: Mapped[uuid.UUID] = _fk("questions.id")
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = _now()
