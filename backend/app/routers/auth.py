from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import security
from app.db import get_db
from app.errors import ApiError, error_responses
from app.models import User
from app.ratelimit import login_limiter
from app.schemas import Credentials, SessionOut, UserOut
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
    email = body.email.lower()
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{email}"
    if not login_limiter.hit(key):
        raise ApiError("rate_limited", "Too many sign-in attempts. Try again in a few minutes.")
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    ok = security.verify_password(body.password, user.password_hash if user else None)
    if user is None or not ok:
        raise ApiError("invalid_credentials", "Email or password is incorrect.")
    if not user.enabled:
        raise ApiError("account_disabled", "This account is disabled.")
    login_limiter.reset(key)
    sess = security.start_session(db, response, user)
    return SessionOut(user=UserOut.model_validate(user), csrf_token=sess.csrf_token)


@router.get(
    "/me",
    response_model=SessionOut,
    responses=error_responses(401, 403),
    summary="Read the current account and session verification token",
)
def me(su: SessionAndUser) -> SessionOut:
    sess, user = su
    return SessionOut(user=UserOut.model_validate(user), csrf_token=sess.csrf_token)


@router.post(
    "/logout",
    status_code=204,
    dependencies=[Csrf],
    responses=error_responses(401, 403),
    summary="End the current session",
)
def logout(su: SessionAndUser, response: Response, db: Annotated[Session, Depends(get_db)]) -> None:
    security.end_session(db, response, su[0])
