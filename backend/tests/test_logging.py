import json
import logging
import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.logging import install_request_logging

LOGGER = "chapterlab.request"


@pytest.fixture(autouse=True)
def _enable_logger() -> None:
    # conftest runs alembic in-process; its fileConfig disables pre-existing loggers.
    logging.getLogger(LOGGER).disabled = False


def _records(caplog):
    return [json.loads(r.getMessage()) for r in caplog.records if r.name == LOGGER]


def test_generates_request_id(client):
    r = client.get("/api/health")
    assert re.fullmatch(r"[0-9a-f]{32}", r.headers["X-Request-ID"])


def test_echoes_valid_and_replaces_invalid_request_id(client):
    r = client.get("/api/health", headers={"X-Request-ID": "abc-123"})
    assert r.headers["X-Request-ID"] == "abc-123"
    r = client.get("/api/health", headers={"X-Request-ID": "bad id\n<script>"})
    assert r.headers["X-Request-ID"] != "bad id\n<script>"
    assert len(r.headers["X-Request-ID"]) == 32


def test_log_has_route_template_and_no_secrets(caplog, make_user, login_as):
    user = make_user()
    c = login_as(user)
    with caplog.at_level(logging.INFO, logger=LOGGER):
        c.get(
            "/api/v1/lessons/00000000-0000-0000-0000-000000000000?secret=qs",
            headers={"X-Request-ID": "req-1"},
        )
        c.post("/api/v1/auth/login", json={"email": user.email, "password": "password123"})
    recs = _records(caplog)
    lesson = next(r for r in recs if r["request_id"] == "req-1")
    assert lesson["route"] == "/api/v1/lessons/{lesson_id}"
    assert lesson["method"] == "GET"
    assert isinstance(lesson["status"], int)
    assert isinstance(lesson["duration_ms"], (int, float))
    assert set(lesson) == {"request_id", "method", "route", "status", "duration_ms", "user_id"}
    text = caplog.text
    assert "secret=qs" not in text and "qs" not in json.dumps(lesson)
    assert "password123" not in text
    login = next(r for r in recs if r["route"] == "/api/v1/auth/login")
    assert login["status"] == 200


def test_log_user_id_and_unmatched(caplog, make_user, login_as):
    user = make_user()
    c = login_as(user)
    with caplog.at_level(logging.INFO, logger=LOGGER):
        c.get("/api/v1/auth/me")
        c.get("/api/v1/no-such-thing")
    me, missing = _records(caplog)
    assert me["user_id"] == str(user.id)
    assert missing["route"] == "unmatched"
    assert missing["user_id"] is None


def test_unhandled_exception_returns_500_json(caplog):
    app = FastAPI()
    install_request_logging(app)

    @app.get("/boom")
    def boom():
        raise RuntimeError("kaboom secret")

    c = TestClient(app, raise_server_exceptions=False)
    with caplog.at_level(logging.INFO, logger=LOGGER):
        r = c.get("/boom", headers={"X-Request-ID": "r-500"})
    assert r.status_code == 500
    assert r.json() == {"code": "internal_error", "message": "Something went wrong."}
    assert r.headers["X-Request-ID"] == "r-500"
    rec = next(x for x in _records(caplog) if x["request_id"] == "r-500")
    assert rec["status"] == 500
    assert rec["route"] == "/boom"
