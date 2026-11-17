"""Shared fixtures. Tests run against a throwaway local Postgres DB, never Neon.

Fixtures for lanes:
  db                       SQLAlchemy session on the test DB
  client                   anonymous TestClient
  make_user(role=..., ...) insert a user, returns User (password: "password123")
  login_as(user)           TestClient with session cookie + X-CSRF-Token header set
"""

import os
import secrets
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta

TEST_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://chapterlab:chapterlab@localhost:5432/chapterlab_test"
)
if "neon.tech" in TEST_URL:
    raise RuntimeError("Refusing to run tests against Neon; set a local TEST_DATABASE_URL.")
# Must be set before app modules build their engine.
os.environ["DATABASE_URL"] = TEST_URL
os.environ["PROVIDER_MODE"] = "stub"
os.environ["COOKIE_SECURE"] = "false"

import psycopg  # noqa: E402
import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from alembic import command  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, User, UserSession  # noqa: E402
from app.security import COOKIE_NAME, CSRF_HEADER, _token_hash, hash_password  # noqa: E402

PASSWORD = "password123"
_PASSWORD_HASH = hash_password(PASSWORD)  # hash once; argon2 is deliberately slow


def _ensure_database() -> None:
    admin_url = TEST_URL.replace("postgresql+psycopg://", "postgresql://").rsplit("/", 1)[0]
    name = TEST_URL.rsplit("/", 1)[1].split("?")[0]
    with psycopg.connect(f"{admin_url}/postgres", autocommit=True) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone():
            conn.execute(f'CREATE DATABASE "{name}"')  # noqa: S608  name is from our own config


@pytest.fixture(scope="session", autouse=True)
def _schema() -> Iterator[None]:
    _ensure_database()
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "alembic"))
    command.upgrade(cfg, "head")  # exercises the real migrations, not create_all
    yield


@pytest.fixture(autouse=True)
def _clean_tables() -> Iterator[None]:
    yield
    names = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def make_user(db: Session) -> Callable[..., User]:
    def _make(role: str = "student", email: str | None = None, enabled: bool = True) -> User:
        user = User(
            email=email or f"{role}-{secrets.token_hex(4)}@example.com",
            password_hash=_PASSWORD_HASH,
            role=role,
            enabled=enabled,
        )
        db.add(user)
        db.commit()
        return user

    return _make


@pytest.fixture
def login_as(db: Session) -> Callable[[User], TestClient]:
    def _login(user: User) -> TestClient:
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        db.add(
            UserSession(
                token_hash=_token_hash(token),
                user_id=user.id,
                csrf_token=csrf,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        db.commit()
        c = TestClient(app, headers={CSRF_HEADER: csrf})
        c.cookies.set(COOKIE_NAME, token)
        return c

    return _login
