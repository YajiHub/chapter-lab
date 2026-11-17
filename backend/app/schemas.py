"""Request/response models. FROZEN after Phase 0: the frontend client is generated from these.

JSON uses camelCase (matches docs/openapi.yaml); Python uses snake_case.
"""

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator
from pydantic.alias_generators import to_camel

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
Role = Literal["student", "admin"]
Sort = Literal["newest", "oldest"]
ReportReason = Literal["wrong_answer", "unsupported_source", "unclear_question"]
RunOutcome = Literal["running", "success", "quota", "timeout", "invalid_output", "unavailable"]


class Schema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


# ---------- common ----------


class ErrorOut(Schema):
    code: str
    message: str
    details: Any | None = None


class Health(Schema):
    status: Literal["ok", "degraded"]
    version: str
    database: Literal["ok", "unavailable"]


class Page[T](Schema):
    items: list[T]
    page: int
    page_size: int
    total: int


# ---------- auth / accounts ----------


class Credentials(Schema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserOut(Schema):
    id: uuid.UUID
    email: str
    role: Role
    enabled: bool
    created_at: datetime


class SessionOut(Schema):
    user: UserOut
    csrf_token: str


class AccountStatus(Schema):
    enabled: bool


# ---------- lessons ----------


class LessonInput(Schema):
    title: Title
    notes: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=6000)]


class LessonSummary(Schema):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class LessonOut(LessonSummary):
    notes: str


# ---------- packs ----------


class Concept(Schema):
    label: Text
    description: Text


class PackQuestion(Schema):
    prompt: Text
    choices: list[Text] = Field(min_length=4, max_length=4)
    correct_choice: int = Field(ge=0, le=3)
    explanation: Text
    paragraph_id: int = Field(ge=1)
    quote: Text

    @field_validator("choices")
    @classmethod
    def distinct_choices(cls, v: list[str]) -> list[str]:
        if len({c.casefold() for c in v}) != 4:
            raise ValueError("choices must be four distinct options")
        return v


class PackInput(Schema):
    title: Title
    guide: list[Concept] = Field(min_length=1)
    comparison: list[Concept] | None = None
    questions: list[PackQuestion] = Field(min_length=5, max_length=5)


class SourceParagraph(Schema):
    id: int
    text: str


class QuestionOut(PackQuestion):
    id: uuid.UUID
    position: int


class PackSummary(Schema):
    id: uuid.UUID
    lesson_id: uuid.UUID
    title: str
    ai_generated: bool
    provider: str | None
    model: str | None
    created_at: datetime
    updated_at: datetime


class PackOut(PackSummary):
    """Owner's review/edit view: includes answer keys (editor needs them)."""

    source_paragraphs: list[SourceParagraph]
    guide: list[Concept]
    comparison: list[Concept] | None
    questions: list[QuestionOut]


class GenerateOut(Schema):
    pack_id: uuid.UUID
    generation_run_id: uuid.UUID


# ---------- attempts ----------


class AttemptInput(Schema):
    pack_id: uuid.UUID


class Feedback(Schema):
    """Only present on an item after it is answered."""

    correct_choice: int
    explanation: str
    paragraph_id: int
    quote: str
    passage: str


class AttemptItemOut(Schema):
    id: uuid.UUID  # send this as AnswerInput.questionId
    question_id: uuid.UUID | None  # pack question, for issue reports
    position: int
    prompt: str
    choices: list[str]
    answered: bool
    chosen_choice: int | None = None
    is_correct: bool | None = None
    feedback: Feedback | None = None


class AttemptSummary(Schema):
    id: uuid.UUID
    pack_id: uuid.UUID
    pack_title: str
    retry_of_attempt_id: uuid.UUID | None
    status: Literal["in_progress", "completed"]
    score: int
    total: int
    started_at: datetime
    completed_at: datetime | None


class AttemptOut(AttemptSummary):
    items: list[AttemptItemOut]


class AnswerInput(Schema):
    question_id: uuid.UUID = Field(description="Attempt item id (AttemptItemOut.id)")
    choice: int = Field(ge=0, le=3)


class AnswerOut(Schema):
    item: AttemptItemOut
    status: Literal["in_progress", "completed"]
    score: int
    total: int


# ---------- reports ----------


class ReportInput(Schema):
    question_id: uuid.UUID
    reason: ReportReason


class ReportCreated(Schema):
    id: uuid.UUID


# ---------- admin ----------


class ProviderTry(Schema):
    provider: str
    model: str | None
    outcome: str
    ms: int


class GenerationRunOut(Schema):
    id: uuid.UUID
    user_email: str
    lesson_id: uuid.UUID
    started_at: datetime
    duration_ms: int | None
    outcome: RunOutcome
    provider: str | None
    model: str | None
    error_code: str | None
    provider_trace: list[ProviderTry]
    pack_id: uuid.UUID | None


class AdminReportOut(Schema):
    """Technical context only: no lesson text, prompts, or answers."""

    id: uuid.UUID
    reason: ReportReason
    created_at: datetime
    reporter_email: str
    question_id: uuid.UUID
    pack_id: uuid.UUID
    position: int
    provider: str | None
    model: str | None
