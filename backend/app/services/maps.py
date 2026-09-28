"""Google Maps scraper service supporting Places API (New) with legacy fallback."""

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


async def _fetch_places_new(client: httpx.AsyncClient, query: str, api_key: str, brand: str, niche: str, city: str) -> list[dict]:
    """Fetch using modern Google Places API (New) — single request for search + details."""
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.websiteUri,places.internationalPhoneNumber,places.primaryType",
    }
    body = {"textQuery": query, "pageSize": 20}
    res = await client.post(url, headers=headers, json=body, timeout=20.0)
    res.raise_for_status()
    data = res.json()
    places = data.get("places", [])

    leads = []
    for item in places:
        name_obj = item.get("displayName") or {}
        name = name_obj.get("text", "")
        if not name:
            continue

        lead = {
            "name": name,
            "address": item.get("formattedAddress", ""),
            "rating": item.get("rating"),
            "reviews": item.get("userRatingCount"),
            "website": item.get("websiteUri", ""),
            "phone": item.get("internationalPhoneNumber", ""),
            "category": item.get("primaryType", niche),
            "city": city,
            "brand": brand,
            "niche": niche,
        }
        scored = score_lead(lead, brand, niche, "maps")
        leads.append(scored)

    return leads


async def _fetch_places_legacy(client: httpx.AsyncClient, query: str, api_key: str, brand: str, niche: str, city: str) -> list[dict]:
    """Fetch using legacy Google Places Text Search + Details."""
    search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    search_res = await client.get(search_url, params={"query": query, "key": api_key}, timeout=20.0)
    search_res.raise_for_status()
    results = search_res.json().get("results", [])[:20]

    leads = []
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
        details_res = await client.get(details_url, params=params, timeout=10.0)
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
        scored = score_lead(lead, brand, niche, "maps")
        leads.append(scored)

    return leads


async def fetch(niche: str, city: str, api_key: str, brand: str) -> list[dict]:
    """Fetch leads from Google Places API (supports both Places API New & Legacy)."""
    global MAPS_CALLS_TODAY
    leads = []
    if not api_key:
        logger.warning("Google Maps API key not set")
        return leads

    MAPS_CALLS_TODAY += 1
    query = f"{niche} in {city}"
    logger.info("Searching maps for: '%s' (call #%d/%d today)", query, MAPS_CALLS_TODAY, MAPS_LIMIT)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Try modern Places API (New) first (single call, faster, cheaper)
        try:
            leads = await _fetch_places_new(client, query, api_key, brand, niche, city)
            if leads:
                logger.info("Places API (New) returned %d leads for '%s'", len(leads), query)
                return leads
        except Exception as new_api_err:
            logger.warning("Places API (New) returned %s, trying legacy Places API...", new_api_err)

        # 2. Fallback to Legacy Places API
        try:
            leads = await _fetch_places_legacy(client, query, api_key, brand, niche, city)
            logger.info("Legacy Places API returned %d leads for '%s'", len(leads), query)
        except Exception as legacy_err:
            logger.error("Error fetching from maps: %s", legacy_err)
            raise legacy_err

    return leads
