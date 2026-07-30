import pytest
from app.config import clear_settings_cache
from app.database import Base, get_db
from app.main import create_app
from app.seed import seed_brand_profile, seed_templates
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("ENABLE_SCHEDULER", "false")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    clear_settings_cache()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    seed_templates(db)
    seed_brand_profile(db)

    app = create_app()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    db.close()
    clear_settings_cache()


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    ready = client.get("/api/health/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_templates_seeded(client):
    res = client.get("/api/templates")
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) >= 4
    channels = {t["channel"] for t in templates}
    assert "linkedin" in channels
    assert "whatsapp" in channels


def test_generate_draft(client):
    job = client.post(
        "/api/jobs",
        json={
            "title": "Engineer",
            "company": "TestCo",
            "location": "Remote",
            "description_text": "Build things.",
            "apply_url": "https://test.co/apply",
        },
    ).json()

    templates = client.get("/api/templates").json()
    linkedin = next(t for t in templates if t["channel"] == "linkedin")

    res = client.post(
        "/api/drafts/generate",
        json={"job_id": job["id"], "template_ids": [linkedin["id"]]},
    )
    assert res.status_code == 200
    drafts = res.json()
    assert len(drafts) == 1
    assert "Engineer" in drafts[0]["content"]
    assert "TestCo" in drafts[0]["content"]


def test_jobs_pagination_and_search(client):
    client.post(
        "/api/jobs",
        json={"title": "Backend Engineer", "company": "Acme", "location": "NYC"},
    )
    client.post(
        "/api/jobs",
        json={"title": "Designer", "company": "Acme", "location": "Remote"},
    )
    res = client.get("/api/jobs?q=Backend&page=1&page_size=10")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Backend Engineer"


def test_brand_and_prompt_pack(client):
    brand = client.get("/api/brand").json()
    assert "tone" in brand
    client.patch("/api/brand", json={"organization_name": "Acme Talent", "tone": "warm"})

    job = client.post(
        "/api/jobs",
        json={"title": "PM", "company": "Acme", "location": "Remote", "apply_url": "https://x.test"},
    ).json()
    templates = client.get("/api/templates").json()
    tpl = templates[0]
    draft = client.post(
        "/api/drafts/generate",
        json={"job_id": job["id"], "template_ids": [tpl["id"]]},
    ).json()[0]

    pack = client.post(
        f"/api/drafts/{draft['id']}/prompt-pack",
        json={"requirement": "Keep it short"},
    ).json()
    assert "Acme Talent" in pack["prompt"]
    assert "Keep it short" in pack["prompt"]


def test_dashboard(client):
    res = client.get("/api/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "jobs_active" in data
    assert "templates_total" in data


def test_bulk_generate(client):
    j1 = client.post("/api/jobs", json={"title": "A", "company": "C"}).json()
    j2 = client.post("/api/jobs", json={"title": "B", "company": "C"}).json()
    templates = client.get("/api/templates").json()
    ids = [t["id"] for t in templates[:2]]
    res = client.post(
        "/api/drafts/generate-bulk",
        json={"job_ids": [j1["id"], j2["id"]], "template_ids": ids},
    )
    assert res.status_code == 200
    assert res.json()["jobs_processed"] == 2
    assert len(res.json()["drafts"]) == 4


def test_generate_skips_reviewed_unless_overwrite(client):
    job = client.post(
        "/api/jobs",
        json={"title": "Engineer", "company": "Co", "location": "Remote"},
    ).json()
    templates = client.get("/api/templates").json()
    tpl = next(t for t in templates if t["channel"] == "linkedin")
    draft = client.post(
        "/api/drafts/generate",
        json={"job_id": job["id"], "template_ids": [tpl["id"]]},
    ).json()[0]
    polished = "POLISHED COPY"
    client.patch(f"/api/drafts/{draft['id']}", json={"content": polished, "status": "reviewed"})

    skipped = client.post(
        "/api/drafts/generate",
        json={"job_id": job["id"], "template_ids": [tpl["id"]], "overwrite_reviewed": False},
    ).json()[0]
    assert skipped["content"] == polished
    assert skipped["status"] == "reviewed"

    overwritten = client.post(
        "/api/drafts/generate",
        json={"job_id": job["id"], "template_ids": [tpl["id"]], "overwrite_reviewed": True},
    ).json()[0]
    assert overwritten["content"] != polished
    assert overwritten["status"] == "draft"
    assert "Engineer" in overwritten["content"]


def test_dismiss_content_changed(client):
    job = client.post(
        "/api/jobs",
        json={"title": "X", "company": "Y", "content_changed": False},
    ).json()
    # content_changed is not on create payload fields that stick via JobCreate - set via update path
    # simulate scrape flag by direct update
    updated = client.patch(f"/api/jobs/{job['id']}", json={"content_changed": True}).json()
    assert updated["content_changed"] is True
    cleared = client.patch(f"/api/jobs/{job['id']}", json={"content_changed": False}).json()
    assert cleared["content_changed"] is False
