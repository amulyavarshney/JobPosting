---
name: jobposting
description: Interact with the local JobPosting API to scrape jobs, generate Jinja drafts, polish marketing copy with your Claude subscription, and save revisions. Use for job posting content workflows without LLM API keys.
---

# JobPosting Skill (Claude Code)

Use the **local REST API** for storage and your **Claude subscription** for rewriting.

## API base

`http://127.0.0.1:8000/api`

Start server:
```bash
cd backend && uvicorn app.main:app --reload
```

## Typical flow

1. `GET /api/jobs` — pick a job
2. `POST /api/drafts/generate` — `{ "job_id": 1, "template_ids": [1,2,3,4] }`
3. `GET /api/drafts/{id}` — read draft + channel
4. Rewrite using polish instructions from `GET /api/templates/{template_id}`
5. `PATCH /api/drafts/{id}` — `{ "content": "...", "status": "reviewed" }`

Or `POST /api/drafts/{id}/import` with polished text.

## Scrape

`POST /api/sources/{id}/scrape`

## Constraints

- No cloud LLM API calls in v1 unless user configured optional keys
- Export/copy only — no auto-publish
- Fix incomplete jobs via `PATCH /api/jobs/{id}` when `needs_manual_fill` is true

See `skills/openapi-actions.yaml` for OpenAPI schema.
