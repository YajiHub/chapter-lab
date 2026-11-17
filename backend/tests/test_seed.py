from sqlalchemy import func, select

from app.models import Lesson, User
from app.seed import seed


def test_seed_is_idempotent_and_gives_student_the_demo_lesson(db, monkeypatch):
    monkeypatch.setenv("SEED_ADMIN_EMAIL", "Admin@Example.com")
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "admin-pass-123")
    monkeypatch.setenv("SEED_STUDENT_EMAIL", "student@example.com")
    monkeypatch.setenv("SEED_STUDENT_PASSWORD", "student-pass-123")
    monkeypatch.delenv("SEED_STUDENT2_EMAIL", raising=False)

    assert len(seed(db)) == 2
    assert seed(db) == []
    admin = db.scalar(select(User).where(User.email == "admin@example.com"))
    assert admin is not None and admin.role == "admin"
    assert db.scalar(select(func.count()).select_from(Lesson)) == 1
