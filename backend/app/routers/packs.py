import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import error_responses
from app.pagination import Paging
from app.routers._stub import todo
from app.schemas import PackInput, PackOut, PackSummary, Page
from app.security import Csrf, StudentUser

router = APIRouter(prefix="/packs", tags=["packs"])
Db = Annotated[Session, Depends(get_db)]


@router.get(
    "",
    response_model=Page[PackSummary],
    responses=error_responses(401, 403, 422),
    summary="List owned study packs",
)
def list_packs(
    user: StudentUser,
    db: Db,
    paging: Paging,
    lesson_id: Annotated[uuid.UUID | None, Query(alias="lessonId")] = None,
) -> Page[PackSummary]:
    todo()


@router.get(
    "/{pack_id}",
    response_model=PackOut,
    responses=error_responses(401, 403, 404),
    summary="Read an owned pack for review or editing",
)
def get_pack(pack_id: uuid.UUID, user: StudentUser, db: Db) -> PackOut:
    todo()


@router.put(
    "/{pack_id}",
    response_model=PackOut,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404, 422),
    summary="Replace the study content for future attempts",
)
def update_pack(pack_id: uuid.UUID, body: PackInput, user: StudentUser, db: Db) -> PackOut:
    todo()


@router.delete(
    "/{pack_id}",
    status_code=204,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404),
    summary="Archive a study pack",
)
def archive_pack(pack_id: uuid.UUID, user: StudentUser, db: Db) -> None:
    todo()
