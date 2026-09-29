"""Scraping endpoints — Google Places API (New) with monthly free-tier guard."""

import logging
from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.models.lead import ScrapeMapsRequest
from app.services.maps import fetch_places_new
from app.db.supabase import check_usage_limit, increment_usage_count, save_leads

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.post("/maps")
async def scrape_maps(request: Request, body: ScrapeMapsRequest):
    """Scrape Google Places API (New) for leads, subject to the 900 monthly call free-tier guard."""
    # 1. Enforce Free-Tier Guard: Max 900 Google Places calls per month
    is_under_limit, current_calls = check_usage_limit(limit=900)
    if not is_under_limit or current_calls >= 900:
        logger.warning("Places API monthly limit reached: %d/900 calls", current_calls)
        raise HTTPException(
            status_code=429,
            detail=(
                f"Monthly Google Places API limit reached ({current_calls}/900 calls). "
                "Free tier cap enforced. Never calling Google past 900. Resets next month."
            ),
        )

    # 2. Verify Google Maps API Key
    api_key = (body.api_key or "").strip() or settings.GOOGLE_MAPS_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Google Maps API key is required. Set GOOGLE_MAPS_API_KEY in the environment or provide it in the request.",
        )

    # 3. Call Places API (New)
    try:
        leads, requests_count = await fetch_places_new(
            niche=body.niche,
            city=body.city,
            brand=body.brand,
            api_key=api_key,
            max_results=body.max_results,
        )
    except RuntimeError as rerr:
        logger.error("Places API error: %s", rerr)
        raise HTTPException(status_code=502, detail=str(rerr)) from rerr
    except Exception as exc:
        logger.error("Unexpected error during Maps scrape: %s", exc)
        raise HTTPException(status_code=500, detail=f"Scrape error: {str(exc)}") from exc

    # 4. Increment usage counter by number of Places requests executed
    if requests_count > 0:
        increment_usage_count(count=requests_count)

    # 5. Save leads into Supabase (upserting on place_id)
    saved = save_leads(leads)

    return {
        "leads": saved,
        "count": len(saved),
        "brand": body.brand,
        "source": "maps",
        "requests_made": requests_count,
    }
