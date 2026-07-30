"""Seed default channel templates and brand profile."""

DEFAULT_TEMPLATES = [
    {
        "channel": "linkedin",
        "name": "LinkedIn Post",
        "is_default": True,
        "polish_instructions": (
            "Polish this LinkedIn job post. Keep it professional, engaging, and under 3000 "
            "characters. Use short paragraphs, 3-5 relevant hashtags at the end, and a clear CTA."
        ),
        "body": """We're hiring: {{ job.title }} at {{ job.company }}!

📍 {{ job.location }}
{% if job.employment_type %}💼 {{ job.employment_type }}{% endif %}
{% if job.salary_text %}💰 {{ job.salary_text }}{% endif %}

{% if job.description_text %}
{{ job.description_text[:800] }}{% if job.description_text|length > 800 %}...{% endif %}
{% endif %}

{% if job.skills %}
Key skills: {{ job.skills[:8]|join(', ') }}
{% endif %}

Apply here: {{ job.apply_url }}

#hiring #jobs #{{ job.company|replace(' ', '')|lower }}
""",
    },
    {
        "channel": "whatsapp",
        "name": "WhatsApp Community",
        "is_default": True,
        "polish_instructions": (
            "Rewrite for a WhatsApp community. Short, scannable, friendly. Use line breaks. "
            "No hashtags. Include apply link clearly."
        ),
        "body": """*New opening*

{{ job.title }} @ {{ job.company }}
Location: {{ job.location }}
{% if job.employment_type %}Type: {{ job.employment_type }}{% endif %}

{% if job.description_text %}{{ job.description_text[:400] }}{% if job.description_text|length > 400 %}...{% endif %}{% endif %}

Apply: {{ job.apply_url }}
""",
    },
    {
        "channel": "youtube_shorts",
        "name": "YouTube Shorts Script",
        "is_default": True,
        "polish_instructions": (
            "Turn into a 30–45s YouTube Shorts script with HOOK / BODY / CTA beats. "
            "Spoken language, energetic, no fluff."
        ),
        "body": """HOOK: "{{ job.company }} is hiring a {{ job.title }} — here's why it matters."

BODY:
- Role: {{ job.title }}
- Where: {{ job.location }}
{% if job.skills %}- Skills: {{ job.skills[:5]|join(', ') }}{% endif %}
{% if job.salary_text %}- Comp: {{ job.salary_text }}{% endif %}

CTA: "Link in description — apply now: {{ job.apply_url }}"
""",
    },
    {
        "channel": "instagram_reel",
        "name": "Instagram Reel Script",
        "is_default": True,
        "polish_instructions": (
            "Rewrite as an Instagram Reel script with on-screen text cues and a punchy CTA. "
            "Keep under 45 seconds spoken."
        ),
        "body": """[0-3s TEXT ON SCREEN] Hiring: {{ job.title }}

VO: "{{ job.company }} just opened a {{ job.title }} role in {{ job.location }}."

[TEXT] {% if job.employment_type %}{{ job.employment_type }}{% else %}Apply today{% endif %}

VO: "{% if job.skills %}Looking for {{ job.skills[:3]|join(', ') }}.{% else %}If this sounds like you, tap the link.{% endif %}"

CTA: Apply → {{ job.apply_url }}
""",
    },
    {
        "channel": "twitter",
        "name": "Twitter/X Post",
        "is_default": False,
        "polish_instructions": (
            "Rewrite for Twitter/X. Max 280 characters if possible, otherwise thread-friendly "
            "short paragraphs. Include apply link. Max 2 hashtags."
        ),
        "body": """🚀 {{ job.company }} is hiring a {{ job.title }}!

📍 {{ job.location }}
{% if job.apply_url %}Apply: {{ job.apply_url }}{% endif %}

#hiring #{{ job.company|replace(' ', '')|lower }}
""",
    },
    {
        "channel": "newsletter",
        "name": "Newsletter Blurb",
        "is_default": False,
        "polish_instructions": (
            "Polish for an email newsletter audience. Warm tone, 2-3 short paragraphs, "
            "highlight why the role matters and who it's for."
        ),
        "body": """## {{ job.title }} — {{ job.company }}

**Location:** {{ job.location }}
{% if job.employment_type %}**Type:** {{ job.employment_type }}{% endif %}
{% if job.salary_text %}**Compensation:** {{ job.salary_text }}{% endif %}

{% if job.description_text %}
{{ job.description_text[:1200] }}
{% else %}
We're looking for a talented {{ job.title }} to join {{ job.company }}.
{% endif %}

{% if job.skills %}
**Skills we're looking for:** {{ job.skills|join(', ') }}
{% endif %}

[Apply now]({{ job.apply_url }})
""",
    },
]


def seed_templates(db) -> None:
    from app.models import Template

    existing_channels = {t.channel for t in db.query(Template).all()}
    added = False
    for tpl in DEFAULT_TEMPLATES:
        if tpl["channel"] in existing_channels:
            continue
        db.add(Template(**tpl))
        existing_channels.add(tpl["channel"])
        added = True
    if added or not existing_channels:
        db.commit()


def seed_brand_profile(db) -> None:
    from app.models import BrandProfile

    if db.query(BrandProfile).count() > 0:
        return
    db.add(
        BrandProfile(
            organization_name="",
            tone="professional, clear, human",
            voice_notes="Prefer concrete benefits over buzzwords. Keep claims accurate to the job description.",
            banned_words="ninja, rockstar, guru, hustle",
            hashtag_policy="Use 2-5 relevant hashtags on LinkedIn; none on WhatsApp.",
            cta_preference="End with a clear apply CTA and the apply URL.",
        )
    )
    db.commit()
