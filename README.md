# JobPosting

Production-oriented pipeline to **scrape career sites**, normalize job postings, and generate multi-channel marketing copy (LinkedIn, WhatsApp, YouTube Shorts, Instagram Reels, and more) — then polish with **your existing AI subscriptions** (Claude, ChatGPT, Gemini). No LLM API keys required.

## Features

- **Sources** — Greenhouse, Lever, Ashby, Workday, custom URLs; enable/disable; scrape-all
- **Scheduled scrapes** — per-source interval with background scheduler and scrape run history
- **Job lifecycle** — active / archived / closed; auto-archive roles missing from the latest board scrape; content-change detection
- **Jobs inbox** — search, filters, pagination, bulk select → generate
- **Templates** — editable Jinja2 channels + polish instructions + live preview
- **Brand voice** — org tone, banned words, hashtag/CTA policy injected into AI prompt packs
- **Generate** — local Jinja drafts, prompt-pack copy/import, revision history, export `.txt` / `.md`
- **Dashboard** — pipeline metrics and recent activity
- **Production ops** — Docker, health live/ready, structured logging, rate limits, optional API key, SPA served from FastAPI, CI

## Quick start (local)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# API
cd backend
../.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# UI (dev)
cd frontend
npm install
npm run dev
```

- UI: http://localhost:5173  
- API docs: http://127.0.0.1:8000/docs  

### Production-style single process

```bash
cd frontend && npm run build && cd ..
cd backend
ENVIRONMENT=production SERVE_FRONTEND=true \
  uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000

### Docker

```bash
export API_KEY=change-me   # optional
docker compose up --build
```

## Subscription AI workflow

1. Generate drafts in the app (local Jinja)
2. **Copy AI prompt** (includes brand voice + custom requirement)
3. Polish in Claude / ChatGPT / Gemini
4. **Import result** back into the draft
5. Export and post manually

Agent skills: `.claude/skills/jobposting/`  
Instruction packs: `skills/chatgpt/`, `skills/gemini/`, `skills/openapi-actions.yaml`

## Configuration

See [`.env.example`](.env.example). Important production knobs:

| Variable | Purpose |
|----------|---------|
| `ENVIRONMENT` | `development` / `production` |
| `API_KEY` + `REQUIRE_API_KEY` | Protect write routes |
| `ENABLE_SCHEDULER` | Background auto-scrape |
| `ARCHIVE_MISSING_JOBS` | Mark jobs missing from board as archived |
| `RATE_LIMIT_*` | Per-IP API / scrape limits |
| `CORS_ORIGINS` | Browser origins |
| `LOG_JSON` | Structured logs |

## API surface (high level)

| Area | Endpoints |
|------|-----------|
| Health | `GET /api/health`, `/api/health/live`, `/api/health/ready` |
| Sources | CRUD, `POST /api/sources/{id}/scrape`, `POST /api/sources/scrape-all`, runs |
| Jobs | Paginated list + filters, CRUD |
| Templates | CRUD + `POST /api/templates/{id}/preview` |
| Drafts | generate, generate-bulk, prompt-pack, import, export, revisions |
| Brand | `GET/PATCH /api/brand` |
| Analytics | `GET /api/analytics/dashboard` |

## Tests & lint

```bash
cd backend
../.venv/bin/pytest -q
../.venv/bin/ruff check app tests
cd ../frontend && npm run build
```

## Architecture

```
Sources → Scrapers (ATS JSON / JSON-LD / HTML)
       → Jobs DB (dedupe, freshness, archive)
       → Jinja templates → Drafts
       → Prompt packs → External AI (subscriptions)
       → Import / revise → Export
```

## License

Use and modify for your recruiting / content workflows.
