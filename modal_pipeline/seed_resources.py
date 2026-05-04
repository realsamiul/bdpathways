import modal
import time
import httpx
import os
import json
import re
from bs4 import BeautifulSoup
from google import genai

# ── INLINED CONFIG ──────────────────────────────────────────────

SCRAPE_AND_SUMMARIZE = [
    {
        "url": "https://admission.brown.edu/apply",
        "institution": "Brown",
        "tier": 1,
        "subtype": "static_policy",
        "country": "us",
        "category": "admissions"
    },
    {
        "url": "https://www.admissionsbeat.com/",
        "institution": "Brown",
        "tier": 1,
        "subtype": "ao_blog",
        "ao_name": "Logan Powell",
        "ao_title": "Dean of Admission",
        "country": "us",
        "category": "admissions"
    },
    {
        "url": "https://undergrad.admissions.columbia.edu/apply/first-year",
        "institution": "Columbia",
        "tier": 1,
        "subtype": "static_policy",
        "country": "us",
        "category": "admissions"
    },
    {
        "url": "https://admissions.cornell.edu/community/blog",
        "institution": "Cornell",
        "tier": 1,
        "subtype": "ao_blog",
        "country": "us",
        "category": "admissions"
    },
    {
        "url": "https://caltechadmissions.blog/",
        "institution": "Caltech",
        "tier": 1,
        "subtype": "ao_blog",
        "country": "us",
        "category": "admissions"
    },
    {
        "url": "https://sites.gatech.edu/admission-blog/",
        "institution": "Georgia Tech",
        "tier": 1,
        "subtype": "ao_blog",
        "ao_name": "Rick Clark",
        "ao_title": "Director of Undergraduate Admission",
        "country": "us",
        "category": "admissions"
    },
    {
        "url": "https://mitadmissions.org/apply/",
        "institution": "MIT",
        "tier": 1,
        "subtype": "static_policy",
        "country": "us",
        "category": "admissions"
    },
    {
        "url": "https://admission.princeton.edu/blogs/applying-college",
        "institution": "Princeton",
        "tier": 1,
        "subtype": "ao_blog",
        "country": "us",
        "category": "admissions"
    },
    {
        "url": "https://satsuite.collegeboard.org/sat/preparation",
        "institution": "College Board",
        "tier": 1,
        "subtype": "static_policy",
        "country": "us",
        "category": "sat_prep"
    },
]

LINK_ONLY = [
    {
        "url": "https://initialview.com/tuesdaytalks/",
        "title": "InitialView Tuesday Talks",
        "tier": 1,
        "subtype": "video_webinar",
        "content_format": "video",
        "is_scrapeable": False,
        "country": "us",
        "category": "admissions"
    },
    {
        "url": "https://admissions.yale.edu/podcast",
        "title": "Yale Admissions Podcast",
        "tier": 1,
        "subtype": "video_webinar",
        "content_format": "podcast",
        "is_scrapeable": False,
        "country": "us",
        "category": "admissions"
    },
    {
        "url": "https://enrollify.org/masteringthenext/",
        "title": "NYU Mastering the Next Podcast",
        "tier": 1,
        "subtype": "video_webinar",
        "content_format": "podcast",
        "is_scrapeable": False,
        "country": "us",
        "category": "admissions"
    },
]

# ── END CONFIG ──────────────────────────────────────────────────


# ── MODAL APP + IMAGE ───────────────────────────────────────────

app = modal.App("bdpathways-seed")

image = (
    modal.Image.debian_slim()
    .pip_install([
        "httpx",
        "beautifulsoup4",
        "supabase",
        "google-genai",
        "python-dotenv"
    ])
)

# ── MAIN SEED FUNCTION ──────────────────────────────────────────

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("bdpathways-secrets")],
    timeout=600
)
def seed():
    from supabase import create_client

    # Initialise clients inside the function
    # (Modal injects secrets as env vars at runtime)
    supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"]
    )

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    # ── SCRAPE AND SUMMARIZE ──────────────────────────────────

    for item in SCRAPE_AND_SUMMARIZE:
        try:
            print(f"🔄 Fetching: {item['url']}")

            resp = httpx.get(
                item["url"],
                timeout=20,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; BDPathways/1.0)"}
            )

            soup = BeautifulSoup(resp.text, "html.parser")

            # Strip all noise — keep only readable content
            for tag in soup(["nav", "footer", "script", "style", "header", "aside"]):
                tag.decompose()

            text = soup.get_text(separator=" ", strip=True)[:6000]

            prompt = f"""
You are helping Bangladeshi students understand university admissions abroad.
From the following webpage text, extract information for an international applicant.

Return ONLY valid JSON — no markdown, no code fences, no explanation.
Use exactly this format:
{{
  "summary": "A 2-sentence plain English summary of the most important facts for an international applicant.",
  "authored_by_ao": true or false,
  "ao_name": "Full name if authored by a named admissions officer, otherwise null",
  "ao_title": "Their title if known, otherwise null",
  "source_subtype": "One of: static_policy, ao_blog, student_blog, aggregator"
}}

Webpage text:
{text}
"""

            time.sleep(6)  # gentle pacing
            result = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            raw = result.text.strip()

            # Strip markdown code fences if Gemini wraps response anyway
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"^```\s*",     "", raw)
            raw = re.sub(r"\s*```$",     "", raw)

            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                raise ValueError(f"No JSON object found in Gemini response: {raw[:200]}")

            enriched = json.loads(json_match.group())

            # Compute reliability index
            if item.get("subtype") == "static_policy":
                reliability = 90
            elif enriched.get("authored_by_ao"):
                reliability = 85
            else:
                reliability = 70

            # Build slug from URL — unique identifier in DB
            slug = (
                item["url"]
                .replace("https://", "")
                .replace("http://", "")
                .replace("/", "-")
                .rstrip("-")
            )[:80]

            # Page title fallback
            page_title = (
                soup.title.string.strip()
                if soup.title and soup.title.string
                else item["institution"]
            )

            record = {
                "slug":              slug,
                "title":             page_title,
                "url":               item["url"],
                "category":          item.get("category", "admissions"),
                "country":           item.get("country", "us"),
                "source_tier":       item.get("tier", 1),
                "source_subtype":    enriched.get("source_subtype") or item.get("subtype"),
                "reliability_index": reliability,
                "source_type":       item.get("subtype"),
                "authored_by_ao":    enriched.get("authored_by_ao", False),
                "ao_name":           enriched.get("ao_name") or item.get("ao_name"),
                "ao_title":          enriched.get("ao_title") or item.get("ao_title"),
                "content_format":    "text",
                "is_scrapeable":     True,
                "summary_generated": True,
                "gemini_summary":    enriched.get("summary"),
                "target_curriculum": ["alevels", "olevel", "ssc", "hsc"],
                "is_active":         True,
            }

            supabase.table("resources").upsert(
                record,
                on_conflict="slug"
            ).execute()

            print(f"✅ Seeded: {item['url']}")

        except Exception as e:
            # Log the failure but continue — don't let one bad URL kill the job
            print(f"❌ Failed: {item['url']} — {e}")
            continue

    # ── LINK ONLY ─────────────────────────────────────────────

    for item in LINK_ONLY:
        try:
            slug = (
                item["url"]
                .replace("https://", "")
                .replace("http://", "")
                .replace("/", "-")
                .rstrip("-")
            )[:80]

            record = {
                "slug":              slug,
                "title":             item.get("title", item["url"]),
                "url":               item["url"],
                "category":          item.get("category", "admissions"),
                "country":           item.get("country", "us"),
                "source_tier":       item.get("tier", 1),
                "source_subtype":    item.get("subtype"),
                "content_format":    item.get("content_format", "text"),
                "reliability_index": 80,
                "is_scrapeable":     False,
                "summary_generated": False,
                "gemini_summary":    None,
                "target_curriculum": ["alevels", "olevel", "ssc", "hsc"],
                "is_active":         True,
            }

            supabase.table("resources").upsert(
                record,
                on_conflict="slug"
            ).execute()

            print(f"🔗 Link-only inserted: {item['url']}")

        except Exception as e:
            print(f"❌ Failed (link-only): {item['url']} — {e}")
            continue

    print("\n🏁 Seed job complete.")


# ── WEEKLY LINK VERIFICATION CRON ──────────────────────────────

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("bdpathways-secrets")],
    schedule=modal.Period(days=7),
    timeout=300
)
def verify_links():
    from supabase import create_client

    supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"]
    )

    response = supabase.table("resources").select("id, url, reliability_index").execute()
    resources = response.data

    print(f"🔍 Verifying {len(resources)} URLs...")

    for resource in resources:
        try:
            resp = httpx.head(
                resource["url"],
                timeout=10,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; BDPathways/1.0)"}
            )

            if resp.status_code == 200:
                print(f"✅ OK ({resp.status_code}): {resource['url']}")
            else:
                # Deduct 5 points for non-200 response
                new_ri = max(0, (resource["reliability_index"] or 70) - 5)
                supabase.table("resources").update({
                    "reliability_index": new_ri
                }).eq("id", resource["id"]).execute()
                print(f"⚠️  Non-200 ({resp.status_code}): {resource['url']} — RI reduced to {new_ri}")

        except Exception as e:
            # Deduct 5 for unreachable URL
            new_ri = max(0, (resource["reliability_index"] or 70) - 5)
            supabase.table("resources").update({
                "reliability_index": new_ri
            }).eq("id", resource["id"]).execute()
            print(f"❌ Unreachable: {resource['url']} — {e} — RI reduced to {new_ri}")

    print("\n🏁 Link verification complete.")


# ── LOCAL ENTRYPOINT ────────────────────────────────────────────

@app.local_entrypoint()
def main():
    seed.remote()