---
name: jobposting
description: Interact with the local JobPosting API to scrape jobs, generate Jinja drafts, polish marketing copy with your Cursor subscription, and save revisions. Use for job posting content workflows without LLM API keys.
---

# JobPosting Skill (Cursor)

Use the **local REST API** for storage and your **Cursor agent model** for rewriting. Never call OpenAI/Anthropic/Gemini cloud APIs unless the user has configured optional API keys in `.env`.

## API base

`http://127.0.0.1:8000/api`

Start server:

```bash
cd backend && uvicorn app.main:app --reload
```

Helper scripts (from repo root):

```bash
.cursor/skills/jobposting/scripts/list-jobs.sh
.cursor/skills/jobposting/scripts/generate-drafts.sh <job_id> <template_id>[,...]
.cursor/skills/jobposting/scripts/prompt-pack.sh <draft_id> ["custom requirement"]
.cursor/skills/jobposting/scripts/save-draft.sh <draft_id> <path-to-content.txt>
.cursor/skills/jobposting/scripts/scrape-source.sh <source_id>
```

## Typical flow

1. `GET /api/jobs` — pick a job (or use `list-jobs.sh`)
2. `POST /api/drafts/generate` — `{ "job_id": 1, "template_ids": [1,2,3,4] }`
3. `GET /api/drafts/{id}` — read draft + channel
4. `GET /api/templates/{template_id}` — read `polish_instructions`
5. Rewrite the draft using polish instructions + optional user requirement (your subscription model)
6. `PATCH /api/drafts/{id}` — `{ "content": "...", "status": "reviewed" }`

Or `POST /api/drafts/{id}/import` with polished text.

## Prompt-pack workflow (no direct API write)

1. `POST /api/drafts/{id}/prompt-pack` — `{ "requirement": "..." }` (or `prompt-pack.sh`)
2. User copies prompt into ChatGPT/Claude/Gemini web
3. `POST /api/drafts/{id}/import` — `{ "content": "...", "requirement": "..." }`

## Scrape

`POST /api/sources/{id}/scrape` (or `scrape-source.sh`)

## Constraints

- No cloud LLM API calls in v1 unless user configured optional keys in server `.env`
- Export/copy only — no auto-publish to social platforms
- Fix incomplete jobs via `PATCH /api/jobs/{id}` when `needs_manual_fill` is true
- Respect protected draft statuses (`reviewed`, `approved`, `exported`) — use `overwrite_reviewed: true` only when regenerating from templates

## OpenAPI

See `skills/openapi-actions.yaml` for the full contract shared with ChatGPT Actions.
