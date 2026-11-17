"""Idempotent seed: `python -m app.seed`. Creates accounts from env vars; skips any already present.

SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD
SEED_STUDENT_EMAIL / SEED_STUDENT_PASSWORD     (gets the demo lesson)
SEED_STUDENT2_EMAIL / SEED_STUDENT2_PASSWORD   (second account for owner-isolation demos)
"""

import os
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Lesson, User
from app.security import hash_password

DEMO_LESSON = Path(__file__).parent / "seed_data" / "demo_lesson.md"
ACCOUNTS = [("ADMIN", "admin"), ("STUDENT", "student"), ("STUDENT2", "student")]


def seed(db: Session) -> list[str]:
    created = []
    for prefix, role in ACCOUNTS:
        email = os.environ.get(f"SEED_{prefix}_EMAIL", "").strip().lower()
        password = os.environ.get(f"SEED_{prefix}_PASSWORD", "")
        if not email or not password:
            continue
        if db.scalar(select(User).where(User.email == email)):
            continue
        user = User(email=email, password_hash=hash_password(password), role=role)
        db.add(user)
        db.flush()
        if prefix == "STUDENT":
            db.add(
                Lesson(
                    owner_id=user.id,
                    title="Web rendering approaches",
                    notes=DEMO_LESSON.read_text().strip(),
                )
            )
        created.append(f"{role}:{email}")
    db.commit()
    return created


if __name__ == "__main__":
    with SessionLocal() as session:
        made = seed(session)
    print("seed: created " + (", ".join(made) if made else "nothing (already seeded)"))
