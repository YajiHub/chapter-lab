from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import error_responses
from app.routers._stub import todo
from app.schemas import ReportCreated, ReportInput
from app.security import Csrf, StudentUser

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "",
    status_code=201,
    response_model=ReportCreated,
    dependencies=[Csrf],
    responses=error_responses(401, 403, 404, 422),
    summary="Report an issue with an owned question",
)
def create_report(
    body: ReportInput, user: StudentUser, db: Annotated[Session, Depends(get_db)]
) -> ReportCreated:
    todo()
