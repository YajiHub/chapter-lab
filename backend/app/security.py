"""Password hashing, DB-backed sessions, CSRF, and role dependencies.

Routers use: `StudentUser`, `AdminUser`, `CurrentUser`, and `Depends(require_csrf)` on writes.
Cookie + CSRF are read from the request directly so they don't leak into OpenAPI params.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Request, Response
from fastapi.security import APIKeyCookie
from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.errors import ApiError
from app.models import User, UserSession

COOKIE_NAME = "chapterlab_session"
CSRF_HEADER = "X-CSRF-Token"

_hasher = PasswordHash.recommended()
# Documents the cookie scheme in OpenAPI; actual lookup happens in current_session.
session_cookie = APIKeyCookie(name=COOKIE_NAME, auto_error=False)
# Verifying against a fixed hash for unknown emails keeps login timing uniform.
_DUMMY_HASH = _hasher.hash("timing-equalizer")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        _hasher.verify(password, _DUMMY_HASH)
        return False
    return _hasher.verify(password, password_hash)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def start_session(db: Session, response: Response, user: User) -> UserSession:
    """Create a session row, set the cookie, and return the session (holds csrf_token)."""
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    sess = UserSession(
        token_hash=_token_hash(token),
        user_id=user.id,
        csrf_token=secrets.token_urlsafe(32),
        expires_at=datetime.now(UTC) + timedelta(hours=settings.session_hours),
    )
    db.add(sess)
    db.commit()
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.session_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return sess


def end_session(db: Session, response: Response, sess: UserSession) -> None:
    db.execute(delete(UserSession).where(UserSession.id == sess.id))
    db.commit()
    response.delete_cookie(COOKIE_NAME, path="/")


def current_session(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    _cookie: Annotated[str | None, Depends(session_cookie)] = None,
) -> tuple[UserSession, User]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise ApiError("unauthenticated", "Sign in to continue.")
    row = db.execute(
        select(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .where(UserSession.token_hash == _token_hash(token))
    ).first()
    if row is None or row[0].expires_at <= datetime.now(UTC):
        raise ApiError("unauthenticated", "Your session has ended. Sign in again.")
    sess, user = row
    if not user.enabled:
        raise ApiError("account_disabled", "This account is disabled.")
    request.state.user_id = str(user.id)
    return sess, user


SessionAndUser = Annotated[tuple[UserSession, User], Depends(current_session)]


def get_current_user(su: SessionAndUser) -> User:
    return su[1]


def require_csrf(request: Request, su: SessionAndUser) -> None:
    sent = request.headers.get(CSRF_HEADER, "")
    if not secrets.compare_digest(sent, su[0].csrf_token):
        raise ApiError("csrf_failed", "Request verification failed. Reload the page.")


def require_student(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "student":
        raise ApiError("forbidden", "Only student accounts can do this.")
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != "admin":
        raise ApiError("forbidden", "Administrator access required.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
StudentUser = Annotated[User, Depends(require_student)]
AdminUser = Annotated[User, Depends(require_admin)]
Csrf = Depends(require_csrf)
