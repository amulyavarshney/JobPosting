# JobPosting

Scrape career sites, normalize job postings, and generate multi-channel marketing copy (LinkedIn, WhatsApp, YouTube Shorts, Instagram Reels, and more). Polish with your existing AI subscriptions (Claude, ChatGPT, Gemini) — **no LLM API keys required**.

**Live demo (browser-only):** [https://amulyavarshney.github.io/JobPosting/](https://amulyavarshney.github.io/JobPosting/)

## Features

- **Sources** — Greenhouse, Lever, Ashby, Workday, custom URLs; scrape-all; per-source history and auto-scrape intervals
- **Jobs** — search, filters (including “changed” / needs fill), pagination, bulk select → generate
- **Templates** — editable Jinja2 channels with polish instructions and live preview
- **Brand voice** — tone and CTA rules injected into AI prompt packs
- **Generate** — local drafts, copy prompt / import result, revision history, export `.txt` / `.md`
- **Dashboard** — metrics, pending drafts queue, recent scrapes
- **Ops** — Docker, health checks, rate limits, optional API key, CI + GitHub Pages deploy

## Quick start (full app)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Terminal 1 — API
cd backend
../.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — UI
cd frontend
npm install
npm run dev
```

- UI: http://localhost:5173  
- API docs: http://127.0.0.1:8000/docs  

### Production-style (API serves the built SPA)

```bash
cd frontend && npm run build && cd ..
cd backend
ENVIRONMENT=production SERVE_FRONTEND=true \
  ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker compose up --build
```

## GitHub Pages demo

GitHub Pages cannot run FastAPI. On push to `main`, Actions builds a **static demo** (localStorage-backed) and deploys from **this repository** via GitHub Pages (not the `amulyavarshney.github.io` user repo).

Local Pages build:

```bash
chmod +x scripts/build-pages.sh
BASE_PATH=/JobPosting ./scripts/build-pages.sh
# output in _site/
```

One-time GitHub setup (required or the site stays 404):

1. Open [repo Settings → Pages](https://github.com/amulyavarshney/JobPosting/settings/pages)
2. Set **Source** to **GitHub Actions**
3. Re-run **Deploy GitHub Pages** from the Actions tab (or push to `main`)

Public URL path matches the repo name: `/JobPosting/`.

## Subscription AI workflow

1. Generate drafts (local Jinja / demo templates)
2. **Copy AI prompt** (includes brand voice + custom requirement)
3. Polish in Claude / ChatGPT / Gemini
4. **Import result** into the draft
5. Export and post manually

Agent skills & instruction packs:

| Tool | Path |
|------|------|
| Cursor | `.cursor/skills/jobposting/` (+ curl helpers in `scripts/`) |
| Claude Code | `.claude/skills/jobposting/` |
| ChatGPT Custom GPT | `skills/chatgpt/jobposting.custom-gpt.md` |
| Gemini Gem | `skills/gemini/jobposting-instructions.md` |
| OpenAPI (Actions) | `skills/openapi-actions.yaml` |

## Configuration

See [`.env.example`](.env.example).

| Variable | Purpose |
|----------|---------|
| `ENVIRONMENT` | `development` / `production` |
| `API_KEY` + `REQUIRE_API_KEY` | Protect write routes |
| `ENABLE_SCHEDULER` | Background auto-scrape |
| `ARCHIVE_MISSING_JOBS` | Archive roles missing from board |
| `CORS_ORIGINS` | Browser origins |
| `SERVE_FRONTEND` | Serve `frontend/dist` from FastAPI |

## Tests

```bash
cd backend && ../.venv/bin/pytest -q
cd frontend && npm run build
```

## License

Use and modify for your recruiting / content workflows.
