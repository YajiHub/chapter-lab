from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import error_responses
from app.routers._stub import todo
from app.schemas import Credentials, SessionOut
from app.security import Csrf, SessionAndUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=SessionOut,
    responses=error_responses(401, 403, 422, 429),
    summary="Sign in",
)
def login(
    body: Credentials,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> SessionOut:
    todo()


@router.get(
    "/me",
    response_model=SessionOut,
    responses=error_responses(401, 403),
    summary="Read the current account and session verification token",
)
def me(su: SessionAndUser) -> SessionOut:
    todo()


@router.post(
    "/logout",
    status_code=204,
    dependencies=[Csrf],
    responses=error_responses(401, 403),
    summary="End the current session",
)
def logout(su: SessionAndUser, response: Response, db: Annotated[Session, Depends(get_db)]) -> None:
    todo()
