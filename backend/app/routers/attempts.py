import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import error_responses
from app.pagination import Paging
from app.routers._stub import todo
from app.schemas import AnswerInput, AnswerOut, AttemptInput, AttemptOut, AttemptSummary, Page
from app.security import Csrf, StudentUser

router = APIRouter(prefix="/attempts", tags=["attempts"])
Db = Annotated[Session, Depends(get_db)]


@router.get(
    "",
    response_model=Page[AttemptSummary],
    responses=error_responses(401, 403, 422),
    summary="List owned attempts",
)
def list_attempts(user: StudentUser, db: Db, paging: Paging) -> Page[AttemptSummary]:
    todo()


@router.post(
    "",
    status_code=201,
    response_model=AttemptOut,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404, 422),
    summary="Start a practice attempt",
)
def start_attempt(body: AttemptInput, user: StudentUser, db: Db) -> AttemptOut:
    todo()


@router.get(
    "/{attempt_id}",
    response_model=AttemptOut,
    responses=error_responses(401, 403, 404),
    summary="Read saved progress or final results",
)
def get_attempt(attempt_id: uuid.UUID, user: StudentUser, db: Db) -> AttemptOut:
    todo()


@router.post(
    "/{attempt_id}/answers",
    response_model=AnswerOut,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404, 409, 422),
    summary="Submit an answer and get feedback",
)
def submit_answer(attempt_id: uuid.UUID, body: AnswerInput, user: StudentUser, db: Db) -> AnswerOut:
    todo()


@router.post(
    "/{attempt_id}/retry",
    status_code=201,
    response_model=AttemptOut,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404, 409),
    summary="Start a new attempt containing missed questions",
)
def retry_attempt(attempt_id: uuid.UUID, user: StudentUser, db: Db) -> AttemptOut:
    todo()
