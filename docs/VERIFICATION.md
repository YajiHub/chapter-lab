# ChapterLab verification and defense

## Engineering checks

| Area | Evidence to collect |
| --- | --- |
| Client | At least eight screens, phone and desktop layouts, labeled controls, keyboard use, search/filter/pagination, and clear validation |
| API | OpenAPI at `/api/docs`, two full CRUD resources, database health and commit ID at `/api/health`, regular request and error logs |
| Security | Hashed passwords, owner isolation, admin restrictions, authorization on nested records, login and generation rate limits, and no committed secrets |
| Database | Versioned migrations, demo seed with synthetic data, persistent volume, and one verified backup restore |
| CI and deployment | Lint and tests on PRs, required checks on main, automated deployment on merge, stable public HTTPS URL, and verified commit ID |
| Test coverage | Target at least 60% backend line coverage, successful and failing cases for each endpoint, and automated browser tests for login and the main workflow |

Use a stubbed model response for routine CI. Exercise valid generation, invalid citations, invalid answer keys, quota errors, timeouts, duplicate answer submission, retries, and cross-account access. Use the real model for the integration evaluation.

## AI evaluation

Use four short computing excerpts with permission to use them. Generate five questions per excerpt. Before edits, mark whether each generated answer is correct and whether its cited passage supports the answer. Record model ID, run time, failure reason, and any corrected item. Report generated item counts and denominators. Also report failed generation runs so the quality rates are interpretable. Results are pending until testing.

Suggested evaluation record columns: excerpt ID, generation ID, question number, correct answer, citation supports answer, issue notes. Record generation duration and error status once per run.

## User acceptance

Recruit at least five target users and obtain the consent required by the course. Ask each person to sign in, generate a pack with sample notes, answer a question, locate its supporting passage, and retry a missed question. Capture completion and issues, then collect the course's SUS and ISO/IEC 25010 responses. Store anonymized results and avoid publishing identifiable account or lesson data.

## Final delivery and demo

- Finish the system documentation, user manual, OpenAPI reference, IEEE format paper, and README with confirmed setup and demo details.
- Publish the `v1.0` release and complete the required Classroom submission, slides, backup video, and scoresheet.
- On the public URL, demonstrate student and administrator sign-in, one complete study flow, a restricted request, `/api/docs`, and `/api/health`.
- Demonstrate how the app handles a generation failure and show the AI evaluation, user acceptance results, and automated deployment evidence.
