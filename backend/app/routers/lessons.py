import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ApiError, error_responses
from app.models import Lesson, StudyPack, User
from app.pagination import PAGE_SIZE, Paging, paginate
from app.routers._stub import todo
from app.schemas import GenerateOut, LessonInput, LessonOut, LessonSummary, PackInput, PackOut, Page
from app.security import Csrf, StudentUser

router = APIRouter(prefix="/lessons", tags=["lessons"])
Db = Annotated[Session, Depends(get_db)]


def _owned_lesson(db: Session, user: User, lesson_id: uuid.UUID) -> Lesson:
    lesson = db.scalar(
        select(Lesson).where(
            Lesson.id == lesson_id, Lesson.owner_id == user.id, Lesson.archived_at.is_(None)
        )
    )
    if lesson is None:
        raise ApiError("not_found", "Lesson not found.")
    return lesson


@router.get(
    "",
    response_model=Page[LessonSummary],
    responses=error_responses(401, 403, 422),
    summary="List owned lessons",
)
def list_lessons(user: StudentUser, db: Db, paging: Paging) -> Page[LessonSummary]:
    stmt = select(Lesson).where(Lesson.owner_id == user.id, Lesson.archived_at.is_(None))
    if paging.q:
        escaped = paging.q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        stmt = stmt.where(Lesson.title.ilike(f"%{escaped}%", escape="\\"))
    if paging.sort == "oldest":
        stmt = stmt.order_by(Lesson.created_at.asc(), Lesson.id.asc())
    else:
        stmt = stmt.order_by(Lesson.created_at.desc(), Lesson.id.desc())
    rows, total = paginate(db, stmt, paging.page)
    return Page[LessonSummary](
        items=[LessonSummary.model_validate(r) for r in rows],
        page=paging.page,
        page_size=PAGE_SIZE,
        total=total,
    )


@router.post(
    "",
    status_code=201,
    response_model=LessonOut,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 422),
    summary="Save lesson notes",
)
def create_lesson(body: LessonInput, user: StudentUser, db: Db) -> LessonOut:
    lesson = Lesson(owner_id=user.id, title=body.title, notes=body.notes)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return LessonOut.model_validate(lesson)


@router.get(
    "/{lesson_id}",
    response_model=LessonOut,
    responses=error_responses(401, 403, 404),
    summary="Read an owned lesson",
)
def get_lesson(lesson_id: uuid.UUID, user: StudentUser, db: Db) -> LessonOut:
    return LessonOut.model_validate(_owned_lesson(db, user, lesson_id))


@router.put(
    "/{lesson_id}",
    response_model=LessonOut,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404, 422),
    summary="Replace the title and notes",
)
def update_lesson(lesson_id: uuid.UUID, body: LessonInput, user: StudentUser, db: Db) -> LessonOut:
    lesson = _owned_lesson(db, user, lesson_id)
    lesson.title = body.title
    lesson.notes = body.notes
    db.commit()
    db.refresh(lesson)
    return LessonOut.model_validate(lesson)


@router.delete(
    "/{lesson_id}",
    status_code=204,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404),
    summary="Archive a lesson and its active packs",
)
def archive_lesson(lesson_id: uuid.UUID, user: StudentUser, db: Db) -> None:
    lesson = _owned_lesson(db, user, lesson_id)
    now = func.now()
    lesson.archived_at = now
    db.execute(
        update(StudyPack)
        .where(
            StudyPack.lesson_id == lesson.id,
            StudyPack.owner_id == user.id,
            StudyPack.archived_at.is_(None),
        )
        .values(archived_at=now)
    )
    db.commit()


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
