# ChapterLab — agent guide

Active plan: [planning/chapterlab-3day-plan.md](planning/chapterlab-3day-plan.md). Product rules: `docs/DESIGN.md`. Route contract: `docs/openapi.yaml` (design) → `backend/openapi.json` (served, generated).

## Stack

- Backend: FastAPI + SQLAlchemy 2 (sync, psycopg 3) + Alembic + Pydantic v2, Python 3.12, managed with `uv`. Code in `backend/app/`.
- Frontend: React 19 + TypeScript 5.9 + Vite, React Router, TanStack Query, `openapi-fetch` (typed from `src/api/schema.d.ts`), Tailwind v4. Code in `frontend/src/`.
- Prod: one Render Docker service (`deploy/Dockerfile`, FastAPI also serves the React build) + Neon Postgres. Local: `deploy/docker-compose.yml`.

## Commands

```bash
docker compose -f deploy/docker-compose.yml up -d db          # local Postgres
cd backend && uv run alembic upgrade head                      # migrate local DB
cd backend && uv run uvicorn app.main:app --reload             # API on :8000
cd backend && uv run pytest --cov=app                          # tests (uses chapterlab_test DB)
cd backend && uv run ruff check . && uv run ruff format .      # lint + format
cd backend && uv run python -m app.dump_openapi openapi.json   # after any schema/route change
cd frontend && npm run dev                                     # UI on :5173, proxies /api to :8000
cd frontend && npm run gen:api                                 # regenerate src/api/schema.d.ts
cd frontend && npm run lint && npm run build
```

## Frozen contract (do not edit inside a lane)

`backend/app/models.py`, `backend/app/schemas.py`, `backend/app/errors.py`, `backend/app/security.py`, `backend/alembic/versions/*`, `backend/openapi.json`, `frontend/src/api/*`.
If a lane needs a change here, stop and report it to the orchestrator. Do not work around it.

## Lanes and ownership

| Lane | Owns |
|---|---|
| L1 Auth & platform | `routers/auth.py`, `routers/admin.py`, `app/logging.py`, `app/ratelimit.py` |
| L2 Study domain | `routers/lessons.py` (except `generate_pack`), `routers/packs.py`, `routers/attempts.py`, `routers/reports.py` |
| L3 Generation | `app/generation/*`, `generate_pack` in `routers/lessons.py`, `tests/fixtures/` |
| L4 Frontend A | app shell, `pages/SignIn`, `Dashboard`, `Lessons`, `LessonForm`, `Admin` |
| L5 Frontend B | `pages/Packs`, `PackEditor`, `Workspace`, `Results` |
| L6 Infra | `deploy/*`, `.github/workflows/*`, `app/seed.py` |
| L7 QA & docs | `frontend/e2e/*`, `docs/*` |

Each lane writes its own test file(s): `backend/tests/test_<lane-area>.py`.

## Rules every lane follows

- Routers replace `todo()` stubs; keep the decorator, path, `response_model`, and status codes as they are.
- Use dependencies from `app.security`: `StudentUser` / `AdminUser` / `CurrentUser`, and `dependencies=[Csrf]` on every write.
- Errors: `raise ApiError("<code>", "<human message>")` with codes from `app/errors.py`. Never return ad-hoc error bodies.
- Ownership: filter every student query by `owner_id == user.id` (or `user_id`) **in the SQL**. Another student's record → `not_found` (404), never 403.
- Archived rows (`archived_at IS NOT NULL`) disappear from lists and GETs but stay for attempt history.
- Quiz responses never include `correct_choice`, `explanation`, `quote`, or passage until that item is answered.
- Never log or echo passwords, session tokens, lesson notes, or provider output.
- Tests: write the failing test first. Use the fixtures in `tests/conftest.py` (`make_user`, `login_as`, `db`, `client`). Cover success + every documented error status for each endpoint. Tests never call real AI providers (`PROVIDER_MODE=stub`).
- Done = `ruff check`, `ruff format --check`, `pytest` all green, and `openapi.json` unchanged (or the change was approved).
