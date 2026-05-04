import modal  
import httpx  
import os  
from bs4 import BeautifulSoup  
from supabase import create_client  
import google.generativeai as genai  
from config import SCRAPE_AND_SUMMARIZE, LINK_ONLY  
  
app = modal.App("bdpathways-seed")  
  
image = modal.Image.debian_slim().pip_install_from_requirements("requirements.txt")  
  
@app.function(  
    image=image,  
    secrets=[  
        modal.Secret.from_name("bdpathways-secrets")  # set this in Modal dashboard  
    ],  
    timeout=600  
)  
def seed():  
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])  
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])  
    model = genai.GenerativeModel("gemini-2.5-pro")  
  
    # --- SCRAPE AND SUMMARIZE ---  
    for item in SCRAPE_AND_SUMMARIZE:  
        try:  
            resp = httpx.get(item["url"], timeout=15, follow_redirects=True)  
            soup = BeautifulSoup(resp.text, "html.parser")  
  
            # Strip noise  
            for tag in soup(["nav","footer","script","style","header","aside"]):  
                tag.decompose()  
            text = soup.get_text(separator=" ", strip=True)[:6000]  # cap tokens  
  
            prompt = f"""  
You are helping Bangladeshi students understand university admissions abroad.  
From the following webpage text, extract for an international applicant:  
1. A 2-sentence plain English summary of the most important facts  
2. Whether a named admissions officer authored this content — if yes, give their name and title  
3. Confirm the source subtype: static_policy, ao_blog, student_blog, or aggregator  
  
Return ONLY valid JSON in this format:  
{{  
  "summary": "...",  
  "authored_by_ao": true/false,  
  "ao_name": "..." or null,  
  "ao_title": "..." or null,  
  "source_subtype": "..."  
}}  
  
Webpage text:  
{text}  
"""  
            result = model.generate_content(prompt)  
            import json, re  
            json_str = re.search(r'\{.*\}', result.text, re.DOTALL).group()  
            enriched = json.loads(json_str)  
  
            reliability = 90 if item.get("subtype") == "static_policy" else \  
                          85 if enriched.get("authored_by_ao") else 70  
  
            record = {  
                "slug": item["url"].replace("https://","").replace("/","-")[:80],  
                "title": soup.title.string if soup.title else item["url"],  
                "url": item["url"],  
                "category": item.get("category", "admissions"),  
                "country": item.get("country", "us"),  
                "source_tier": item.get("tier", 1),  
                "source_subtype": enriched.get("source_subtype", item.get("subtype")),  
                "reliability_index": reliability,  
                "authored_by_ao": enriched.get("authored_by_ao", False),  
                "ao_name": enriched.get("ao_name") or item.get("ao_name"),  
                "ao_title": enriched.get("ao_title") or item.get("ao_title"),  
                "gemini_summary": enriched.get("summary"),  
                "summary_generated": True,  
                "is_scrapeable": True,  
                "target_curriculum": ["alevels","olevel","ssc","hsc"],  
                "is_active": True,  
            }  
            supabase.table("resources").upsert(record, on_conflict="slug").execute()  
            print(f"✅ Seeded: {item['url']}")  
  
        except Exception as e:  
            print(f"❌ Failed: {item['url']} — {e}")  
  
    # --- LINK ONLY ---  
    for item in LINK_ONLY:  
        record = {  
            "slug": item["url"].replace("https://","").replace("/","-")[:80],  
            "title": item.get("title", item["url"]),  
            "url": item["url"],  
            "category": item.get("category", "admissions"),  
            "country": item.get("country", "us"),  
            "source_tier": item.get("tier", 1),  
            "source_subtype": item.get("subtype"),  
            "content_format": item.get("content_format", "text"),  
            "reliability_index": 80,  
            "is_scrapeable": False,  
            "summary_generated": False,  
            "target_curriculum": ["alevels","olevel","ssc","hsc"],  
            "is_active": True,  
        }  
        supabase.table("resources").upsert(record, on_conflict="slug").execute()  
        print(f"🔗 Link-only inserted: {item['url']}")  
  
@app.local_entrypoint()  
def main():  
    seed.remote()  