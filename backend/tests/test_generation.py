from datetime import UTC, datetime

from app.generation.renderer import build_prompt_pack, render_template
from app.models import Draft, Job, Template


def test_render_template_linkedin():
    job = Job(
        id=1,
        title="Backend Engineer",
        company="Acme",
        location="Remote",
        employment_type="Full-time",
        salary_text="$150k",
        description_text="We build APIs.",
        apply_url="https://acme.com/apply",
        scraped_at=datetime.now(UTC),
    )
    job.skills = ["Python", "FastAPI"]

    template = Template(
        id=1,
        channel="linkedin",
        name="LinkedIn",
        body="Hiring {{ job.title }} at {{ job.company }}! Apply: {{ job.apply_url }}",
        polish_instructions="Keep it professional.",
    )

    content = render_template(template, job)
    assert "Backend Engineer" in content
    assert "Acme" in content
    assert "https://acme.com/apply" in content


def test_build_prompt_pack_includes_requirement():
    job = Job(id=1, title="Designer", company="Co", scraped_at=datetime.now(UTC))
    template = Template(
        id=1,
        channel="twitter",
        name="Twitter",
        body="x",
        polish_instructions="Be concise.",
    )
    draft = Draft(id=5, job_id=1, template_id=1, channel="twitter", content="Draft text here.")

    prompt = build_prompt_pack(draft, job, template, requirement="Add emoji")
    assert "Designer" in prompt
    assert "Draft text here." in prompt
    assert "Add emoji" in prompt
    assert "Be concise." in prompt
