# ChapterLab 3-day build plan

Replaces the two-week schedule in `docs/PLAN.md`. Scope, data rules, and checks still come from `docs/DESIGN.md`, `docs/openapi.yaml`, and `docs/VERIFICATION.md` unless overridden here.

## Destination & Scope

**Done =** public HTTPS site with student + admin sign-in, the full study flow (save notes → generate pack → quiz → see cited passage → retry missed), admin views, `/api/docs`, `/api/health` with commit + DB status, CI on PRs, deploy-on-merge, tests ≥60% backend coverage, AI evaluation, 5 user sessions, and `v1.0` release with required documents.

**In scope:** everything in `DESIGN.md` + `openapi.yaml` (full option C), plus a multi-provider generation fallback.

**Out of scope:** PDF import, flashcards, chat, essay grading, public sharing (per `PLAN.md`); Caddy in production; paid hosting; LLM-based model ranking.

## Locked Decisions

| # | Decision | Why | By |
|---|---|---|---|
| 1 | Full scope (C), built with parallel agents after a contract freeze | Agents parallelize code; the frozen contract prevents merge collisions | me |
| 2 | Backend: Python 3.12 (Docker), FastAPI, SQLAlchemy 2 (sync, psycopg 3), Alembic, Pydantic v2, pwdlib[argon2], httpx; uv; ruff; pytest + pytest-cov | Matches proposal; OpenAPI at `/api/docs` for free; Pydantic validates LLM output | delegated |
| 3 | Frontend: React + TypeScript + Vite, React Router, TanStack Query, `openapi-typescript` + `openapi-fetch`, Tailwind; Playwright for e2e | Matches proposal; typed client generated from the frozen contract | delegated |
| 4 | Hosting ₱0: one Render free Docker web service (FastAPI also serves built React) + Neon free Postgres. Compose for local dev only. No Caddy | No school server; Azure blocked; same origin keeps cookies/CSRF simple | me |
| 5 | CI/CD: GitHub Actions on a **public** repo. PR = lint + tests + e2e (stub model). Merge to `main` = tests → Render deploy hook → poll `/api/health` until it reports the merged commit | Free Actions + branch protection need public repo | me |
| 6 | Quota safety net: 5 generations/hour/student, global daily cap via env, clean 429, seeded pre-generated demo pack, CI uses stub provider | Demo must survive quota exhaustion | me |
| 7 | Provider fallback chain: Gemini → Groq → OpenRouter free models. OpenRouter models chosen by **deterministic filter + rank** of its daily model list, not by asking Gemini | Asking Gemini to rank fails exactly when Gemini is out of quota, and burns quota. A filter is free and testable | me, modified by delegated |
| 8 | Server-side sessions in Postgres (cookie `chapterlab_session`, HttpOnly, Secure, SameSite=Lax) + CSRF token in session, sent as `X-CSRF-Token` | Disabling an account revokes access instantly; matches `openapi.yaml` | delegated |

## Architecture

```
Browser ──HTTPS──> Render web service (Docker)
                    ├─ /            React build (static, SPA fallback)
                    ├─ /api/v1/*    FastAPI
                    ├─ /api/docs    OpenAPI UI
                    └─ /api/health  {status, version=RENDER_GIT_COMMIT, database}
                         ├──> Neon Postgres
                         └──> Generation chain: Gemini → Groq → OpenRouter(:free)
```

Container start: `alembic upgrade head` then `uvicorn`. Dockerfile is multi-stage (node builds `frontend/dist`, python image copies it to `/app/static`).

## Generation fallback chain

- One `OpenAICompatibleProvider(base_url, api_key, model)` class used for all three (Gemini OpenAI-compatible endpoint, Groq, OpenRouter). Verify each provider's `response_format` json_schema support on day 1. If one only supports `json_object`, use that; Pydantic validation is the real gate anyway.
- `StubProvider` returns fixture JSON (valid, bad citation, bad answer index, 429, timeout) for tests and CI.
- Try next provider on: 429, 5xx, timeout (25 s per call), invalid JSON/schema, failed citation/answer validation. Skip a provider with missing key or 401. Overall deadline 60 s. Then return 429 (all quota), 503 (all unavailable), or 502 (all invalid).
- OpenRouter picker: `GET /api/v1/models`, cached 24 h in process. Keep models with zero prompt + completion price (`:free`), `response_format` or `structured_outputs` in `supported_parameters`, context ≥ 16k. Rank by a static preferred-family list in config, then by context length. Try the top 2.
- `generation_runs.provider_trace` (jsonb) records every try: provider, model, outcome, ms. Packs record the final provider + model and are labelled AI generated.
- AI evaluation pins Gemini only (fallback disabled via env) so quality numbers are interpretable.
- Privacy: fallback sends lesson text to more third parties, and free tiers may log/train on prompts. Demo and evaluation use only original sample notes. State this in the user manual.

## Domain & File Impact

### Data model (`backend/app/models.py`, one initial Alembic migration)

| Table | Key columns | Notes |
|---|---|---|
| users | id uuid, email unique, password_hash, role `student\|admin`, enabled, created_at | |
| sessions | id, token_hash, user_id, csrf_token, expires_at | Delete on logout; reject if user disabled |
| lessons | id, owner_id, title ≤160, notes ≤6000, archived_at, created/updated | Delete = archive and archive its active packs |
| study_packs | id, lesson_id, owner_id, title, source_paragraphs jsonb (snapshot `[{id, text}]`), guide jsonb, comparison jsonb null, ai_generated, generation_run_id, provider, model, archived_at, timestamps | owner_id is denormalized for one-hop ownership checks |
| questions | id, pack_id, position 1–5, prompt, choices jsonb[4], correct_choice 0–3, explanation, paragraph_id, quote | Pack PUT updates the 5 rows in place by position, so IDs stay stable for reports |
| attempts | id, user_id, pack_id, retry_of_attempt_id null, status `in_progress\|completed`, score, total, started_at, completed_at | |
| attempt_items | id, attempt_id, question_id, position, snapshot (prompt, choices, correct_choice, explanation, paragraph_id, quote, passage_text), chosen_choice null, is_correct null, answered_at | This is the ER's ATTEMPT_ANSWER. The API's `questionId` in the attempt flow = attempt_item id. Answering twice returns 409 |
| generation_runs | id, user_id, lesson_id, started_at, duration_ms, outcome `success\|quota\|timeout\|invalid_output\|unavailable`, provider, model, provider_trace jsonb, pack_id null | Never store lesson text or raw output |
| issue_reports | id, user_id, question_id, reason enum, created_at | Admin view shows pack id, run id, model, and reason, never the text |

Rules: a student requesting another student's record gets 404; a student calling an admin route gets 403; quiz responses never contain `correct_choice`, explanation, or quote until that item is answered; score is computed server-side; retry copies only missed items from the completed attempt's snapshot (409 if the attempt is not completed or nothing was missed).

### Repo layout

```
backend/
  app/main.py            app factory, static mount, SPA fallback, middleware
  app/config.py          pydantic-settings
  app/db.py              engine, session dependency
  app/models.py          ORM (frozen in Phase 0)
  app/schemas.py         all request/response models (frozen in Phase 0)
  app/errors.py          {code, message} errors + error code list
  app/security.py        hashing, sessions, CSRF, role deps, rate limits
  app/logging.py         request-id middleware, JSON logs (no secrets or lesson text)
  app/routers/{auth,lessons,packs,attempts,reports,admin,health}.py
  app/generation/{providers.py,openrouter_picker.py,prompt.py,validate.py,service.py}
  app/seed.py            admin, 2 students, demo lesson, pre-generated demo pack
  alembic/
  tests/                 pytest, fixtures/ for stub outputs
frontend/
  src/api/schema.d.ts    generated from backend OpenAPI (frozen in Phase 0)
  src/api/client.ts      openapi-fetch + CSRF header
  src/pages/             SignIn, Dashboard, Lessons, LessonForm, Packs, PackEditor, Workspace, Results, Admin
  e2e/                   Playwright: login, main flow
deploy/
  Dockerfile, docker-compose.yml (local: api + postgres), backup.sh, restore.sh
.github/workflows/ci.yml, deploy.yml
AGENTS.md                agent rules, lane ownership, commands
```

## Agent lanes (after the Phase 0 freeze)

Each lane owns its folders. Only Phase 0 touches `models.py`, `schemas.py`, `errors.py`, `schema.d.ts`; later changes go through the orchestrator. Every lane must be red/green tested, then checked by `hygiene-reviewer` before merge.

| Lane | Owns | Agent |
|---|---|---|
| L1 Auth & platform | security.py, logging.py, routers/auth, health, admin | expressive-dev |
| L2 Study domain | routers/lessons, packs, attempts, reports | expressive-dev |
| L3 Generation | app/generation/*, stub fixtures | expressive-dev, second opinion from antigravity |
| L4 Frontend A | SignIn, Dashboard, Lessons, LessonForm, Admin, app shell | opencode / antigravity |
| L5 Frontend B | Packs, PackEditor, Workspace, Results | opencode / antigravity |
| L6 Infra | deploy/*, .github/workflows/*, seed.py | expressive-dev |
| L7 QA & docs | e2e/, docs updates, user manual | qa-tester + general-purpose |

## Phased Execution Checklist

### Before Day 1, human-only (start now)
- [x] 🧑 Create a GitHub account and **public** repo. Run `git init` here and push.
- [ ] 🧑 Sign up for Render (GitHub login), Neon, Google AI Studio (Gemini key), Groq, and OpenRouter. Store the keys only in Render env vars and a local `.env`.
- [ ] 🧑 Recruit 5 testers for Day 3 afternoon. Prepare the course consent form and SUS / ISO 25010 forms.
- [ ] 🧑 Confirm the due date and solo approval with the instructor.
- [ ] 🧑 Check free-tier limits (Render, Neon, Gemini, Groq, OpenRouter) and note them in `docs/sessions/`.

### Day 1 AM — Phase 0: Contract freeze (sequential, no parallel agents)
- [x] 🤖 Scaffold backend (uv, FastAPI app factory, config, db, ruff, pytest) and frontend (Vite React TS, Tailwind, Router, Query).
- [x] 🤝 Write `models.py` + initial Alembic migration per the data model above.
- [x] 🤖 Write `schemas.py` and `errors.py` covering every route in `openapi.yaml`. Stub routers return 501 so the OpenAPI document is complete.
- [x] 🤖 Generate `frontend/src/api/schema.d.ts` from `/api/openapi.json`. Add `client.ts` with the CSRF header.
- [x] 🤖 Write `AGENTS.md`: lane ownership, frozen files, commands, test rules.
- [x] 🤖 Dockerfile + local compose + `/api/health` + GitHub Actions `ci.yml` (ruff, pytest with a Postgres service).
- **Verify:** `docker compose up` serves `/api/docs`, `/api/health` shows `database: ok`, CI is green on the first PR.

### Day 1 PM — Phase 1: Walking skeleton live + parallel lanes start
- [ ] 🤖 L6: Render service + Neon + deploy hook + `deploy.yml` (deploy after green main, poll health for the commit). Branch protection on `main`.
- [x] 🤖 L1: login/logout/me, argon2, sessions, CSRF, role deps, disabled-account check, login rate limit, request logging.
- [x] 🤖 L2: lessons CRUD with search/sort/pagination, owner 404s, archive.
- [x] 🤖 L3: providers, stub, prompt with numbered paragraphs, chain, OpenRouter picker.
- [x] 🤝 L3: `validate.py`: 5 questions, 4 distinct choices, index 0–3, known paragraph id, quote is an exact substring of that paragraph after whitespace normalization. You must be able to explain this in the defense.
- [x] 🤖 L4: app shell, SignIn, Lessons list + form.
- [x] 🧑 Run two real trial generations with the demo lesson against each provider. Record model ID, time, and validation result.
- **Verify:** the public URL shows the health check with the merged commit; you can sign in and save a lesson on the deployed app.

### Day 2 — Phase 2: Full feature set
- [ ] 🤖 L3: generate endpoint, per-student 5/h + global daily cap, generation_runs with trace, error mapping 429/502/503/409.
- [ ] 🤖 L2: packs CRUD (manual create, PUT in place, archive), attempts start/get/list, answers (no key leak, 409 on duplicate), reports.
- [ ] 🤝 L2: scoring + retry from snapshot (missed items only, own score).
- [ ] 🤖 L1: admin accounts list/patch (cannot disable self = 409), generation-runs and reports lists without private text.
- [ ] 🤖 L4: Dashboard, Admin pages.
- [ ] 🤖 L5: Packs list, PackEditor, Workspace (guide, Practice tab, Revisit tab, source passage expandable below the answer on mobile, labelled radio choices), Results + retry.
- [ ] 🤖 L6: `seed.py` with demo accounts and the pre-generated demo pack. `backup.sh` / `restore.sh` (pg_dump → second Neon database).
- [ ] 🤖 L7: Playwright login + main flow against local compose with the stub provider. Add it to CI.
- [ ] 🤖 `qa-tester` runs the full user flow on the deployed site, on phone + desktop widths.
- **Verify:** both roles work end to end on the public URL; a merge updates the reported commit; coverage ≥60%; cross-account, duplicate-answer, bad-citation, quota, and timeout tests all pass.

### Day 3 — Phase 3: Evidence and release
- [ ] 🧑 AI evaluation: 4 original computing excerpts × 5 questions, Gemini pinned. Mark correctness and citation support yourself. Record failed runs.
- [ ] 🧑 Restore drill: run backup → restore into a second database, screenshot the row counts.
- [ ] 🧑 5 user sessions (sign in, generate, answer, find the passage, retry), then SUS + ISO 25010 forms. Anonymize results.
- [ ] 🤖 Fix blockers found by users and the QA agent.
- [ ] 🤖 Update `README.md` (run instructions, URL, demo accounts) and `DESIGN.md` (Render + Neon, fallback chain, no Caddy). Draft the system documentation, user manual, and IEEE paper from the code and results.
- [ ] 🤝 Final review of paper and slides. Record a backup demo video.
- [ ] 🧑 Tag `v1.0`, submit to Classroom, rehearse. Wake the Render service 5 minutes before the demo.
- **Verify:** the `VERIFICATION.md` "Final delivery and demo" checklist is fully ticked.

## Risks

- **Render cold start** (~30–60 s after 15 min idle): wake the service before the demo; mention it as a known free-tier limit.
- **Free-tier terms change:** verify every limit at sign-up; the fallback chain and seeded pack cover quota loss.
- **Agent drift:** freeze the contract first, keep lanes inside their folders, and do not merge without a reviewer pass and green CI.
- **Day 3 is human-bound:** if Day 2 slips, cut polish, not the evaluation or user sessions.
- **Login rate limit is in memory** (single Render instance). shortcut: resets on restart, move to Postgres if more than one instance runs.
