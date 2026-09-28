"""Instagram scraper service using Apify."""

import asyncio
import logging
from apify_client import ApifyClient

logger = logging.getLogger(__name__)

async def fetch(niche: str, city: str, token: str, brand: str) -> list[dict]:
    leads = []
    if not token:
        logger.warning("Apify token not set for instagram")
        return leads

    def run_scraper():
        client = ApifyClient(token)
        niche_clean = niche.replace(' ', '').lower()
        city_clean = city.replace(' ', '').lower()
        hashtags = [
            f"{niche_clean}{city_clean}",
            niche_clean,
            f"{city.lower()}business"
        ]
        run_input = {
            "hashtags": hashtags,
            "resultsLimit": 30
        }
        logger.info("Starting Apify instagram scraper with hashtags: %s", hashtags)
        run = client.actor("apify/instagram-hashtag-scraper").call(run_input=run_input)
        return list(client.dataset(run["defaultDatasetId"]).iterate_items())

    try:
        items = await asyncio.to_thread(run_scraper)
        for item in items:
            followers_count = int(item.get("ownerFollowersCount") or 0)
            
            if followers_count < 800:
                score = 88
                why = "Micro account — high growth potential"
            elif followers_count < 3000:
                score = 65
                why = "Growing account"
            else:
                score = 40
                why = "Established account"
                
            lead = {
                "name": item.get("ownerUsername", "unknown"),
                "bio": item.get("ownerBiography", ""),
                "followers_count": followers_count,
                "followers": f"{followers_count:,} followers",
                "city": city,
                "category": niche,
                "source": "instagram",
                "brand": brand,
                "niche": niche,
                "score": score,
                "why": why
            }
            leads.append(lead)
    except Exception as e:
        logger.error("Error fetching from instagram: %s", e)
        
    return leads
