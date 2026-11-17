"""Phase 0 platform checks: health, error shape, auth dependencies wired on routes."""


def test_health_reports_database_and_version(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["database"] == "ok" and body["version"]


def test_unknown_api_path_is_json_404(client):
    r = client.get("/api/v1/nope")
    assert r.status_code == 404


def test_student_route_requires_sign_in(client):
    r = client.get("/api/v1/lessons")
    assert r.status_code == 401
    assert r.json()["code"] == "unauthenticated"


def test_admin_route_forbidden_for_student(make_user, login_as):
    r = login_as(make_user("student")).get("/api/v1/admin/accounts")
    assert r.status_code == 403
    assert r.json()["code"] == "forbidden"


def test_disabled_account_loses_access(make_user, login_as):
    r = login_as(make_user("student", enabled=False)).get("/api/v1/lessons")
    assert r.status_code == 403
    assert r.json()["code"] == "account_disabled"


def test_write_without_csrf_is_rejected(make_user, login_as):
    c = login_as(make_user("student"))
    del c.headers["X-CSRF-Token"]
    r = c.post("/api/v1/lessons", json={"title": "t", "notes": "n"})
    assert r.status_code == 403
    assert r.json()["code"] == "csrf_failed"


def test_validation_error_does_not_echo_input(make_user, login_as):
    r = login_as(make_user("student")).post(
        "/api/v1/lessons", json={"title": "", "notes": "secret lesson text"}
    )
    assert r.status_code == 422
    assert r.json()["code"] == "validation_error"
    assert "secret lesson text" not in r.text
