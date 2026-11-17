import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

from app.models import Lesson, StudyPack

URL = "/api/v1/lessons"


def _make(c, title="Cell biology", notes="Mitochondria make ATP."):
    r = c.post(URL, json={"title": title, "notes": notes})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def student(make_user, login_as):
    return login_as(make_user())


@pytest.fixture
def other(make_user, login_as):
    return login_as(make_user())


# ---------- create ----------


def test_create_returns_lesson(student):
    body = _make(student, title="  Photosynthesis  ", notes="Light reactions.")
    assert set(body) == {"id", "title", "notes", "createdAt", "updatedAt"}
    assert body["title"] == "Photosynthesis"
    assert body["notes"] == "Light reactions."


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "", "notes": "x"},
        {"title": "   ", "notes": "x"},
        {"title": "x" * 161, "notes": "x"},
        {"title": "ok", "notes": "x" * 6001},
        {"title": "ok", "notes": ""},
        {"title": "ok"},
        {"notes": "x"},
        {},
    ],
)
def test_create_validation(student, payload):
    r = student.post(URL, json=payload)
    assert r.status_code == 422
    assert r.json()["code"] == "validation_error"


def test_create_accepts_limits(student):
    _make(student, title="x" * 160, notes="y" * 6000)


def test_create_requires_csrf(make_user, login_as):
    c = login_as(make_user())
    del c.headers["X-CSRF-Token"]
    assert c.post(URL, json={"title": "a", "notes": "b"}).status_code == 403


# ---------- list ----------


def test_list_only_own(student, other):
    mine = _make(student, title="Mine")
    _make(other, title="Theirs")
    r = student.get(URL)
    assert r.status_code == 200
    body = r.json()
    assert [i["id"] for i in body["items"]] == [mine["id"]]
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["pageSize"] == 10
    assert set(body["items"][0]) == {"id", "title", "createdAt", "updatedAt"}


def test_list_pagination(student):
    for i in range(12):
        _make(student, title=f"L{i}")
    p1 = student.get(URL, params={"page": 1}).json()
    p2 = student.get(URL, params={"page": 2}).json()
    assert len(p1["items"]) == 10 and p1["total"] == 12
    assert len(p2["items"]) == 2 and p2["total"] == 12 and p2["page"] == 2
    assert not {i["id"] for i in p1["items"]} & {i["id"] for i in p2["items"]}


def test_list_bad_page(student):
    assert student.get(URL, params={"page": 0}).status_code == 422


def test_list_search_case_insensitive_and_literal(student):
    a = _make(student, title="Cell Biology")
    b = _make(student, title="100% Chemistry")
    _make(student, title="1000 Physics")
    _make(student, title="Under_score")
    _make(student, title="Underxscore")

    ids = [i["id"] for i in student.get(URL, params={"q": "cELL"}).json()["items"]]
    assert ids == [a["id"]]
    ids = [i["id"] for i in student.get(URL, params={"q": "0%"}).json()["items"]]
    assert ids == [b["id"]]
    items = student.get(URL, params={"q": "_"}).json()["items"]
    assert [i["title"] for i in items] == ["Under_score"]


def test_list_sort(student, db):
    first = _make(student, title="First")
    second = _make(student, title="Second")
    # Make created_at differ deterministically.
    db.execute(
        update(Lesson)
        .where(Lesson.id == uuid.UUID(first["id"]))
        .values(created_at=datetime.now(UTC) - timedelta(days=1))
    )
    db.commit()
    newest = [i["id"] for i in student.get(URL).json()["items"]]
    oldest = [i["id"] for i in student.get(URL, params={"sort": "oldest"}).json()["items"]]
    assert newest == [second["id"], first["id"]]
    assert oldest == [first["id"], second["id"]]
    assert student.get(URL, params={"sort": "bogus"}).status_code == 422


# ---------- get ----------


def test_get_own(student):
    lesson = _make(student)
    r = student.get(f"{URL}/{lesson['id']}")
    assert r.status_code == 200
    assert r.json() == lesson


def test_get_other_students_is_404(student, other):
    lesson = _make(other)
    r = student.get(f"{URL}/{lesson['id']}")
    assert r.status_code == 404
    assert r.json()["code"] == "not_found"


def test_get_missing_is_404(student):
    assert student.get(f"{URL}/{uuid.uuid4()}").status_code == 404


# ---------- update ----------


def test_update_own(student):
    lesson = _make(student)
    r = student.put(f"{URL}/{lesson['id']}", json={"title": "New", "notes": "New notes"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == lesson["id"]
    assert body["title"] == "New" and body["notes"] == "New notes"
    assert student.get(f"{URL}/{lesson['id']}").json()["title"] == "New"


def test_update_other_students_is_404(student, other):
    lesson = _make(other, title="Theirs")
    r = student.put(f"{URL}/{lesson['id']}", json={"title": "Hack", "notes": "x"})
    assert r.status_code == 404
    assert other.get(f"{URL}/{lesson['id']}").json()["title"] == "Theirs"


def test_update_missing_is_404(student):
    r = student.put(f"{URL}/{uuid.uuid4()}", json={"title": "a", "notes": "b"})
    assert r.status_code == 404


def test_update_validation(student):
    lesson = _make(student)
    r = student.put(f"{URL}/{lesson['id']}", json={"title": "", "notes": "x"})
    assert r.status_code == 422
    r = student.put(f"{URL}/{lesson['id']}", json={"title": "ok", "notes": "x" * 6001})
    assert r.status_code == 422


# ---------- archive ----------


def test_archive_hides_lesson(student):
    lesson = _make(student)
    assert student.delete(f"{URL}/{lesson['id']}").status_code == 204
    assert student.get(f"{URL}/{lesson['id']}").status_code == 404
    assert student.get(URL).json()["items"] == []
    assert student.delete(f"{URL}/{lesson['id']}").status_code == 404
    r = student.put(f"{URL}/{lesson['id']}", json={"title": "a", "notes": "b"})
    assert r.status_code == 404


def test_archive_other_students_is_404(student, other):
    lesson = _make(other)
    assert student.delete(f"{URL}/{lesson['id']}").status_code == 404
    assert other.get(f"{URL}/{lesson['id']}").status_code == 200


def test_archive_missing_is_404(student):
    assert student.delete(f"{URL}/{uuid.uuid4()}").status_code == 404


def test_archive_archives_packs(student, db):
    lesson = _make(student)
    lesson_id = uuid.UUID(lesson["id"])
    owner_id = db.scalar(select(Lesson.owner_id).where(Lesson.id == lesson_id))
    earlier = datetime(2020, 1, 1, tzinfo=UTC)

    def pack(archived_at=None):
        return StudyPack(
            lesson_id=lesson_id,
            owner_id=owner_id,
            title="Pack",
            source_paragraphs=[{"id": 1, "text": "x"}],
            guide=[{"label": "a", "description": "b"}],
            archived_at=archived_at,
        )

    active, old = pack(), pack(earlier)
    db.add_all([active, old])
    db.commit()
    active_id, old_id = active.id, old.id

    assert student.delete(f"{URL}/{lesson['id']}").status_code == 204
    db.expire_all()
    assert db.get(StudyPack, active_id).archived_at is not None
    assert db.get(StudyPack, old_id).archived_at == earlier  # already-archived untouched
    assert db.get(Lesson, lesson_id).archived_at is not None


# ---------- auth ----------


def test_admin_forbidden(make_user, login_as):
    admin = login_as(make_user(role="admin"))
    r = admin.get(URL)
    assert r.status_code == 403
    assert r.json()["code"] == "forbidden"


def test_no_session_401(client):
    assert client.get(URL).status_code == 401
    assert client.post(URL, json={"title": "a", "notes": "b"}).status_code == 401
    assert client.get(f"{URL}/{uuid.uuid4()}").status_code == 401
