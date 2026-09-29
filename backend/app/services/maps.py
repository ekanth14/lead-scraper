"""Google Places API (New) service for searching places, classifying websites, and scoring leads."""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urlparse

import httpx

from app.services.scoring import score_lead

logger = logging.getLogger(__name__)

PLACES_NEW_URL = "https://places.googleapis.com/v1/places:searchText"

FIELD_MASK = (
    "places.id,"
    "places.displayName,"
    "places.formattedAddress,"
    "places.rating,"
    "places.userRatingCount,"
    "places.websiteUri,"
    "places.nationalPhoneNumber,"
    "places.types,"
    "places.googleMapsUri,"
    "places.businessStatus,"
    "nextPageToken"
)

SOCIAL_AND_BIO_DOMAINS = {
    "facebook.com",
    "fb.com",
    "m.facebook.com",
    "instagram.com",
    "instagr.am",
    "linktr.ee",
    "linktree.com",
    "wa.me",
    "api.whatsapp.com",
    "whatsapp.com",
    "bio.link",
    "beacons.ai",
    "campsite.bio",
    "taplink.cc",
    "carrd.co",
    "solo.to",
    "bento.me",
    "linkin.bio",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "linkedin.com",
}


def classify_website(url: Optional[str]) -> str:
    """Classify a website into:
    - 'none': null, empty, or placeholder
    - 'social_only': facebook, instagram, linktree, wa.me, or bio links
    - 'has_website': legitimate business domain
    """
    if not url or not str(url).strip():
        return "none"

    cleaned = str(url).strip().lower()
    if cleaned in ("none", "null", "undefined", "n/a", "no website"):
        return "none"

    if not cleaned.startswith(("http://", "https://")):
        cleaned = "https://" + cleaned

    try:
        parsed = urlparse(cleaned)
        netloc = (parsed.netloc or "").lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        for domain in SOCIAL_AND_BIO_DOMAINS:
            if netloc == domain or netloc.endswith("." + domain):
                return "social_only"

        return "has_website"
    except Exception:
        return "has_website"


async def fetch_places_new(
    niche: str,
    city: str,
    brand: str,
    api_key: str,
    max_results: int = 20,
) -> Tuple[List[Dict[str, Any]], int]:
    """Search Google Places API (New) using searchText.

    Returns:
        (leads, requests_count) where requests_count is the number of Places API requests made.
    """
    if not api_key:
        raise ValueError("Google Maps API key is required")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    query = f"{niche} in {city}"
    page1_size = min(20, max_results)
    body = {
        "textQuery": query,
        "pageSize": page1_size,
        "regionCode": "IN",
    }

    requests_count = 0
    all_places: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Page 1
        logger.info("Calling Places API (New) for query: '%s', pageSize: %d", query, page1_size)
        resp = await client.post(PLACES_NEW_URL, headers=headers, json=body)
        requests_count += 1

        if resp.status_code != 200:
            err_text = resp.text
            logger.error("Places API error %d: %s", resp.status_code, err_text)
            if "API_KEY_HTTP_REFERRER_BLOCKED" in err_text:
                raise RuntimeError(
                    "Google Maps API key has HTTP referrer restrictions in Google Cloud Console. "
                    "For server-side Places API (New) calls, go to Google Cloud Console > Credentials > Key Restrictions "
                    "and set Application Restrictions to 'None' (or IP restriction)."
                )
            raise RuntimeError(f"Places API request failed ({resp.status_code}): {err_text}")

        data = resp.json()
        places_p1 = data.get("places", [])
        all_places.extend(places_p1)
        next_token = data.get("nextPageToken")

        # Page 2 (if max_results > 20 and token exists)
        if max_results > 20 and next_token:
            # Places API (New) requires a short delay before next page token is valid
            await asyncio.sleep(1.5)
            page2_size = min(20, max_results - 20)
            body_p2 = {
                "textQuery": query,
                "pageSize": page2_size,
                "regionCode": "IN",
                "pageToken": next_token,
            }
            logger.info("Calling Places API (New) page 2 for query: '%s'", query)
            resp2 = await client.post(PLACES_NEW_URL, headers=headers, json=body_p2)
            requests_count += 1
            if resp2.status_code == 200:
                data2 = resp2.json()
                places_p2 = data2.get("places", [])
                all_places.extend(places_p2)
            else:
                logger.warning("Places API page 2 failed (%d): %s", resp2.status_code, resp2.text)

    # Transform raw places into scored lead records
    leads: List[Dict[str, Any]] = []
    seen_place_ids = set()

    for item in all_places:
        name_obj = item.get("displayName") or {}
        name = name_obj.get("text", "").strip()
        if not name:
            continue

        place_id = item.get("id") or f"custom_{abs(hash(name + (item.get('formattedAddress') or '')))}"
        if place_id in seen_place_ids:
            continue
        seen_place_ids.add(place_id)

        address = item.get("formattedAddress")
        phone = item.get("nationalPhoneNumber")
        website = item.get("websiteUri")
        website_status = classify_website(website)
        rating = item.get("rating")
        reviews = item.get("userRatingCount")
        maps_url = item.get("googleMapsUri")

        scoring = score_lead(
            website_status=website_status,
            rating=rating,
            reviews=reviews,
            brand=brand,
            niche=niche,
        )

        lead = {
            "place_id": place_id,
            "brand": brand,
            "niche": niche,
            "name": name,
            "address": address,
            "phone": phone,
            "website": website,
            "website_status": website_status,
            "rating": rating,
            "reviews": reviews,
            "score": scoring["score"],
            "label": scoring["label"],
            "why": scoring["why"],
            "maps_url": maps_url,
            "source": "maps",
        }
        leads.append(lead)

    return leads[:max_results], requests_count


# Backwards compatibility helper
async def fetch(niche: str, city: str, api_key: str, brand: str) -> List[Dict[str, Any]]:
    leads, _ = await fetch_places_new(
        niche=niche,
        city=city,
        brand=brand,
        api_key=api_key,
        max_results=20,
    )
    return leads
