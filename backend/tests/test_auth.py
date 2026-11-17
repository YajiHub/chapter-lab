from collections.abc import Iterator

import pytest

from app.ratelimit import RateLimiter, login_limiter
from app.security import COOKIE_NAME

LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"
LOGOUT = "/api/v1/auth/logout"


@pytest.fixture(autouse=True)
def _clear_limiter() -> Iterator[None]:
    login_limiter._hits.clear()
    yield
    login_limiter._hits.clear()


def test_rate_limiter_sliding_window():
    now = [0.0]
    rl = RateLimiter(2, 10, clock=lambda: now[0])
    assert rl.hit("k") and rl.hit("k")
    assert not rl.hit("k")
    assert rl.hit("other")
    now[0] = 10.5
    assert rl.hit("k")
    rl.reset("k")
    assert rl.hit("k") and rl.hit("k")


def test_login_success_sets_cookie(client, make_user):
    user = make_user(role="admin")
    r = client.post(LOGIN, json={"email": user.email, "password": "password123"})
    assert r.status_code == 200
    body = r.json()
    assert body["csrfToken"]
    assert body["user"]["role"] == "admin"
    assert body["user"]["email"] == user.email
    assert COOKIE_NAME in r.cookies
    assert "httponly" in r.headers["set-cookie"].lower()


def test_login_email_case_insensitive(client, make_user):
    user = make_user(email="Mixed.Case@example.com")
    r = client.post(LOGIN, json={"email": "mixed.case@EXAMPLE.com", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["user"]["id"] == str(user.id)


def test_login_wrong_password_and_unknown_email_same_401(client, make_user):
    user = make_user()
    bad = client.post(LOGIN, json={"email": user.email, "password": "nope"})
    unknown = client.post(LOGIN, json={"email": "ghost@example.com", "password": "password123"})
    assert bad.status_code == unknown.status_code == 401
    assert bad.json() == unknown.json()
    assert bad.json()["code"] == "invalid_credentials"
    assert "nope" not in bad.text


def test_login_disabled_403(client, make_user):
    user = make_user(enabled=False)
    r = client.post(LOGIN, json={"email": user.email, "password": "password123"})
    assert r.status_code == 403
    assert r.json()["code"] == "account_disabled"
    assert COOKIE_NAME not in r.cookies


def test_login_rate_limited_on_11th_attempt(client, make_user):
    user = make_user()
    for _ in range(10):
        r = client.post(LOGIN, json={"email": user.email, "password": "wrong"})
        assert r.status_code == 401
    r = client.post(LOGIN, json={"email": user.email.upper(), "password": "password123"})
    assert r.status_code == 429
    assert r.json()["code"] == "rate_limited"


def test_login_success_resets_limit(client, make_user):
    user = make_user()
    for _ in range(9):
        client.post(LOGIN, json={"email": user.email, "password": "wrong"})
    ok = client.post(LOGIN, json={"email": user.email, "password": "password123"})
    assert ok.status_code == 200
    for _ in range(9):
        assert client.post(LOGIN, json={"email": user.email, "password": "x"}).status_code == 401


def test_me(client, make_user, login_as):
    user = make_user()
    c = login_as(user)
    r = c.get(ME)
    assert r.status_code == 200
    assert r.json()["user"]["id"] == str(user.id)
    assert r.json()["csrfToken"] == c.headers["X-CSRF-Token"]
    assert client.get(ME).status_code == 401


def test_logout_then_me_401(make_user, login_as):
    c = login_as(make_user())
    r = c.post(LOGOUT)
    assert r.status_code == 204
    assert r.content == b""
    set_cookie = r.headers.get("set-cookie", "")
    assert COOKIE_NAME in set_cookie and "max-age=0" in set_cookie.lower()
    assert c.get(ME).status_code == 401


def test_logout_without_csrf_403(make_user, login_as):
    c = login_as(make_user())
    del c.headers["X-CSRF-Token"]
    r = c.post(LOGOUT)
    assert r.status_code == 403
    assert r.json()["code"] == "csrf_failed"
    c.headers["X-CSRF-Token"] = "x"
    assert c.get(ME).status_code == 200


def test_logout_unauthenticated_401(client):
    assert client.post(LOGOUT).status_code == 401
