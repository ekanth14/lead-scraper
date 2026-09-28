"""LinkedIn scraper service using Apify."""

import asyncio
import logging
from apify_client import ApifyClient

logger = logging.getLogger(__name__)

async def fetch(niche: str, city: str, token: str, brand: str) -> list[dict]:
    leads = []
    if not token:
        logger.warning("Apify token not set for linkedin")
        return leads

    def run_scraper():
        client = ApifyClient(token)
        run_input = {
            "keyword": niche,
            "location": city,
            "maxResults": 25
        }
        logger.info("Starting Apify linkedin scraper with keyword: %s, location: %s", niche, city)
        run = client.actor("curious_coder/linkedin-company-search-export").call(run_input=run_input)
        return list(client.dataset(run["defaultDatasetId"]).iterate_items())

    try:
        items = await asyncio.to_thread(run_scraper)
        for item in items:
            employees_count = int(item.get("employeeCount") or 0)
            
            if employees_count < 10:
                score = 82
                why = "Early-stage startup — needs digital foundation"
            elif employees_count < 30:
                score = 60
                why = "Growing company"
            else:
                score = 35
                why = "Established business"
                
            follower_count = int(item.get('followerCount') or 0)
            
            lead = {
                "name": item.get("name") or item.get("companyName", "Unknown"),
                "industry": item.get("industry", ""),
                "employees_count": employees_count,
                "followers": f"{follower_count:,} LinkedIn followers",
                "website": item.get("website", ""),
                "city": city,
                "category": niche,
                "source": "linkedin",
                "brand": brand,
                "niche": niche,
                "score": score,
                "why": why
            }
            leads.append(lead)
    except Exception as e:
        logger.error("Error fetching from linkedin: %s", e)
        
    return leads
