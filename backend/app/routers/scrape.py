"""Scraping endpoints — Google Maps, Instagram, LinkedIn."""

import logging

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.models.lead import ScrapeRequest
from app.services import maps, instagram, linkedin
from app.db.supabase import save_leads

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scrape", tags=["scrape"])
limiter = Limiter(key_func=get_remote_address)

# Daily call limits for free tiers
APIFY_CALLS_TODAY = 0
APIFY_LIMIT = 25  # Apify free tier $5/mo credit (~25 runs/mo, safe daily cap)


def reset_apify_calls():
    """Reset the daily Apify call counter."""
    global APIFY_CALLS_TODAY
    APIFY_CALLS_TODAY = 0
    logger.info("Apify daily counter reset to 0.")


def reset_all_daily_counters():
    """Reset all daily scrape limits (called at midnight IST)."""
    maps.reset_maps_calls()
    reset_apify_calls()


@router.post("/maps")
@limiter.limit("10/minute")
async def scrape_maps(request: Request, body: ScrapeRequest):
    """Scrape Google Maps Places for leads (subject to daily free tier cap)."""
    if maps.MAPS_CALLS_TODAY >= maps.MAPS_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Daily limit reached, resets at midnight",
        )

    api_key = (body.api_key or "").strip() or settings.GOOGLE_MAPS_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Google Maps API key is required. Please set GOOGLE_MAPS_API_KEY on the server or enter it in the search bar.",
        )

    try:
        leads = await maps.fetch(
            niche=body.niche,
            city=body.city,
            api_key=api_key,
            brand=body.brand,
        )
        saved = save_leads(leads, body.brand)
        return {"leads": saved, "count": len(saved), "brand": body.brand, "source": "maps"}
    except Exception as exc:
        logger.error("Maps scrape failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Maps scrape error: {exc}") from exc


@router.post("/instagram")
@limiter.limit("10/minute")
async def scrape_instagram(request: Request, body: ScrapeRequest):
    """Scrape Instagram via Apify for leads (subject to daily free tier cap)."""
    global APIFY_CALLS_TODAY
    if APIFY_CALLS_TODAY >= APIFY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Daily limit reached, resets at midnight",
        )

    token = (body.api_key or "").strip() or settings.APIFY_TOKEN
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Apify Token is required for Instagram. Please set APIFY_TOKEN on the server or enter it in the search bar.",
        )

    APIFY_CALLS_TODAY += 1

    try:
        leads = await instagram.fetch(
            niche=body.niche,
            city=body.city,
            token=token,
            brand=body.brand,
        )
        saved = save_leads(leads, body.brand)
        return {"leads": saved, "count": len(saved), "brand": body.brand, "source": "instagram"}
    except Exception as exc:
        logger.error("Instagram scrape failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Instagram scrape error: {exc}") from exc


@router.post("/linkedin")
@limiter.limit("10/minute")
async def scrape_linkedin(request: Request, body: ScrapeRequest):
    """Scrape LinkedIn via Apify for leads (subject to daily free tier cap)."""
    global APIFY_CALLS_TODAY
    if APIFY_CALLS_TODAY >= APIFY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Daily limit reached, resets at midnight",
        )

    token = (body.api_key or "").strip() or settings.APIFY_TOKEN
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Apify Token is required for LinkedIn. Please set APIFY_TOKEN on the server or enter it in the search bar.",
        )

    APIFY_CALLS_TODAY += 1

    try:
        leads = await linkedin.fetch(
            niche=body.niche,
            city=body.city,
            token=token,
            brand=body.brand,
        )
        saved = save_leads(leads, body.brand)
        return {"leads": saved, "count": len(saved), "brand": body.brand, "source": "linkedin"}
    except Exception as exc:
        logger.error("LinkedIn scrape failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"LinkedIn scrape error: {exc}") from exc


@router.get("/status/{run_id}")
async def scrape_status(request: Request, run_id: str):
    """Poll Apify run status."""
    from apify_client import ApifyClient
    from app.config import settings

    token = settings.APIFY_TOKEN
    if not token:
        return {"run_id": run_id, "status": "UNKNOWN", "note": "APIFY_TOKEN not configured"}
    try:
        client = ApifyClient(token)
        run_info = client.run(run_id).get()
        return {
            "run_id": run_id,
            "status": run_info.get("status", "UNKNOWN"),
            "started_at": run_info.get("startedAt"),
            "finished_at": run_info.get("finishedAt"),
            "dataset_id": run_info.get("defaultDatasetId"),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Apify status error: {exc}") from exc
