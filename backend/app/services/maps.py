"""Google Maps scraper service."""

import httpx
import logging
from app.services.scoring import score_lead

logger = logging.getLogger(__name__)

MAPS_CALLS_TODAY = 0
MAPS_LIMIT = 40  # Google gives $200/month credit, ~40 searches/day is safe


def reset_maps_calls():
    """Reset the daily Google Maps call counter."""
    global MAPS_CALLS_TODAY
    MAPS_CALLS_TODAY = 0
    logger.info("Google Maps daily counter reset to 0.")


async def fetch(niche: str, city: str, api_key: str, brand: str) -> list[dict]:
    global MAPS_CALLS_TODAY
    leads = []
    if not api_key:
        logger.warning("Google Maps API key not set")
        return leads

    MAPS_CALLS_TODAY += 1

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            query = f"{niche} in {city}"
            logger.info("Searching maps for: %s (call #%d/%d today)", query, MAPS_CALLS_TODAY, MAPS_LIMIT)
            search_res = await client.get(search_url, params={"query": query, "key": api_key})
            search_res.raise_for_status()
            results = search_res.json().get("results", [])[:20]

            for item in results:
                place_id = item.get("place_id")
                if not place_id:
                    continue

                details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                params = {
                    "place_id": place_id,
                    "fields": "name,formatted_address,rating,user_ratings_total,website,formatted_phone_number,types",
                    "key": api_key,
                }
                details_res = await client.get(details_url, params=params)
                details_res.raise_for_status()
                details = details_res.json().get("result", {})

                lead = {
                    "name": details.get("name", ""),
                    "address": details.get("formatted_address", ""),
                    "rating": details.get("rating"),
                    "reviews": details.get("user_ratings_total"),
                    "website": details.get("website", ""),
                    "phone": details.get("formatted_phone_number", ""),
                    "category": niche,
                    "city": city,
                    "brand": brand,
                    "niche": niche,
                }
                scored_lead = score_lead(lead, brand, niche, "maps")
                leads.append(scored_lead)

    except Exception as e:
        logger.error("Error fetching from maps: %s", e)

    return leads
