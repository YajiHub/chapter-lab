import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import error_responses
from app.pagination import Paging
from app.routers._stub import todo
from app.schemas import AccountStatus, AdminReportOut, GenerationRunOut, Page, UserOut
from app.security import AdminUser, Csrf

router = APIRouter(prefix="/admin", tags=["admin"])
Db = Annotated[Session, Depends(get_db)]


@router.get(
    "/accounts",
    response_model=Page[UserOut],
    responses=error_responses(401, 403, 422),
    summary="List accounts for administration",
)
def list_accounts(admin: AdminUser, db: Db, paging: Paging) -> Page[UserOut]:
    todo()


@router.patch(
    "/accounts/{account_id}",
    response_model=UserOut,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404, 409, 422),
    summary="Change an account's enabled status",
)
def set_account_status(
    account_id: uuid.UUID, body: AccountStatus, admin: AdminUser, db: Db
) -> UserOut:
    todo()


@router.get(
    "/generation-runs",
    response_model=Page[GenerationRunOut],
    responses=error_responses(401, 403, 422),
    summary="Review generation outcomes without private note text",
)
def list_generation_runs(admin: AdminUser, db: Db, paging: Paging) -> Page[GenerationRunOut]:
    todo()


@router.get(
    "/reports",
    response_model=Page[AdminReportOut],
    responses=error_responses(401, 403, 422),
    summary="Review flagged issue categories and technical context",
)
def list_reports(admin: AdminUser, db: Db, paging: Paging) -> Page[AdminReportOut]:
    todo()
