# ChapterLab project plan

## Deliverable

Build a self-service chapter reviewer for college exam preparation. The demonstration is one complete workflow using a computing lesson: save notes, generate a private study pack, miss a scenario question, open the exact source passage, and retry the missed question.

**Users.** Students own and manage their notes and packs. An administrator can activate or disable accounts and view generation failure records and reported issues. Administrator access does not grant access to private lesson text or attempts. Human review is limited to the evaluation sample.

**Scope.** Pasted text from one chapter excerpt at a time, a short concept guide, an optional comparison when the source supports one, five multiple-choice questions, feedback, source passages, saved scores, and retries. Scope exclusions for this release are PDF import, flashcards, free-form chat, essay grading, and public sharing.

## First milestone

Confirm the instructor's written solo approval, the actual due date, and the lab deployment setup. With an eligible Gemini API model, test two short, shareable excerpts and record the model ID, available quota, response time, and whether the citations and questions validate. Use the included demo lesson for the first deployed flow. Confirm the free host and stable HTTPS address early.

## Two week schedule

| Days after approval | Work | Evidence |
| --- | --- | --- |
| 1–2 | Start React, FastAPI, PostgreSQL, and Compose. Test model access. Get a public HTTPS health check showing database status and commit ID. | Healthy deployment and two trial generations |
| 3–5 | Add sign-in, owner checks, lesson management, pack generation and validation, and the Review screen. | Save an excerpt and generate a grounded pack on the deployed app |
| 6–8 | Finish pack management, quiz grading, source feedback, retry, issue reporting, and admin views. Enable CI checks and deployment on merge. | Two roles work end to end and a deployment updates the reported commit |
| 9–11 | Test authorization, failures, and restore. Run AI evaluation and five user task sessions. | Test output, anonymized feedback, and recorded evaluation |
| 12–14 | Fix demo blockers, complete required submissions, tag the release, and rehearse. | Public site, `v1.0` release, required documents, and backup demo video |

Dates are relative to the build start because the revised course deadline has not been confirmed. Begin the system documentation, user manual, and paper outlines during implementation. Before adding features, protect time for the live demo, tests, deployment, and required documents.
