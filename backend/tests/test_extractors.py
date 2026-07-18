
from app.extractors.custom import extract_from_html
from app.scrapers.base import ScrapedJob

JSON_LD_HTML = """
<html>
<head><title>Engineer role</title></head>
<body>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "JobPosting",
  "title": "Senior Software Engineer",
  "description": "<p>Build great products.</p>",
  "hiringOrganization": {"name": "Acme Corp"},
  "jobLocation": {"address": {"addressLocality": "San Francisco", "addressRegion": "CA"}},
  "employmentType": "FULL_TIME",
  "url": "https://example.com/jobs/123"
}
</script>
</body>
</html>
"""


def test_extract_json_ld_job():
    job = extract_from_html(JSON_LD_HTML, "https://example.com/jobs/123")
    assert job.title == "Senior Software Engineer"
    assert job.company == "Acme Corp"
    assert "San Francisco" in job.location
    assert job.employment_type == "FULL_TIME"
    assert "Build great products" in job.description_text
    assert job.needs_manual_fill is False


def test_extract_opengraph_fallback():
    html = """
    <html><head>
    <meta property="og:title" content="Product Manager" />
    <meta property="og:description" content="Lead product initiatives." />
    <meta property="og:site_name" content="Beta Inc" />
    </head><body></body></html>
    """
    job = extract_from_html(html, "https://beta.com/careers/pm")
    assert job.title == "Product Manager"
    assert job.company == "Beta Inc"
    assert "Lead product" in job.description_text


def test_scraped_job_defaults():
    job = ScrapedJob(external_id="abc")
    assert job.skills == []
    assert job.title == ""
