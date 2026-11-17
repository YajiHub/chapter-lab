import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import error_responses
from app.pagination import Paging
from app.routers._stub import todo
from app.schemas import GenerateOut, LessonInput, LessonOut, LessonSummary, PackInput, PackOut, Page
from app.security import Csrf, StudentUser

router = APIRouter(prefix="/lessons", tags=["lessons"])
Db = Annotated[Session, Depends(get_db)]


@router.get(
    "",
    response_model=Page[LessonSummary],
    responses=error_responses(401, 403, 422),
    summary="List owned lessons",
)
def list_lessons(user: StudentUser, db: Db, paging: Paging) -> Page[LessonSummary]:
    todo()


@router.post(
    "",
    status_code=201,
    response_model=LessonOut,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 422),
    summary="Save lesson notes",
)
def create_lesson(body: LessonInput, user: StudentUser, db: Db) -> LessonOut:
    todo()


@router.get(
    "/{lesson_id}",
    response_model=LessonOut,
    responses=error_responses(401, 403, 404),
    summary="Read an owned lesson",
)
def get_lesson(lesson_id: uuid.UUID, user: StudentUser, db: Db) -> LessonOut:
    todo()


@router.put(
    "/{lesson_id}",
    response_model=LessonOut,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404, 422),
    summary="Replace the title and notes",
)
def update_lesson(lesson_id: uuid.UUID, body: LessonInput, user: StudentUser, db: Db) -> LessonOut:
    todo()


@router.delete(
    "/{lesson_id}",
    status_code=204,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404),
    summary="Archive a lesson and its active packs",
)
def archive_lesson(lesson_id: uuid.UUID, user: StudentUser, db: Db) -> None:
    todo()


@router.post(
    "/{lesson_id}/generate",
    status_code=201,
    response_model=GenerateOut,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404, 409, 422, 429, 502, 503),
    summary="Generate and save a study pack",
)
def generate_pack(lesson_id: uuid.UUID, user: StudentUser, db: Db) -> GenerateOut:
    todo()


@router.post(
    "/{lesson_id}/packs",
    status_code=201,
    response_model=PackOut,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404, 422),
    summary="Save a study pack for an owned lesson",
)
def create_pack(lesson_id: uuid.UUID, body: PackInput, user: StudentUser, db: Db) -> PackOut:
    todo()
