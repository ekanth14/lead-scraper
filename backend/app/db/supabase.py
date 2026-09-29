"""Supabase database operations, Free-tier usage guard, and lead persistence."""

from datetime import datetime, timezone
import logging
from typing import Optional, List, Dict, Any, Tuple

from supabase import Client, create_client

from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[Client] = None
MONTHLY_FREE_TIER_LIMIT = 900


def get_client() -> Optional[Client]:
    """Retrieve or initialize singleton Supabase client."""
    global _client
    if _client is not None:
        return _client

    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if not url or not key:
        logger.warning("SUPABASE_URL or SUPABASE_KEY not set — DB operations unavailable.")
        return None

    _client = create_client(url, key)
    logger.info("Supabase client initialized for %s", url)
    return _client


# ── Free-Tier Usage Guard ─────────────────────────────────────────

def get_current_month() -> str:
    """Return current month in YYYY-MM format (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def get_monthly_usage(month: Optional[str] = None) -> int:
    """Query the usage table for the number of Places API calls made in the specified month."""
    client = get_client()
    if not client:
        return 0

    target_month = month or get_current_month()
    try:
        res = client.table("usage").select("calls").eq("month", target_month).execute()
        if res.data and len(res.data) > 0:
            return int(res.data[0].get("calls") or 0)
        return 0
    except Exception as exc:
        logger.error("Failed to query monthly usage: %s", exc)
        return 0


def increment_usage_count(count: int = 1, month: Optional[str] = None) -> int:
    """Increment the Places API call count in the usage table for the given month."""
    client = get_client()
    if not client or count <= 0:
        return 0

    target_month = month or get_current_month()
    try:
        # Use RPC increment_usage if available
        rpc_res = client.rpc("increment_usage", {"p_month": target_month, "p_count": count}).execute()
        if rpc_res.data is not None:
            return int(rpc_res.data)
    except Exception as rpc_err:
        logger.debug("RPC increment_usage failed, falling back to direct table update: %s", rpc_err)

    try:
        current = get_monthly_usage(target_month)
        new_total = current + count
        client.table("usage").upsert({"month": target_month, "calls": new_total}).execute()
        return new_total
    except Exception as exc:
        logger.error("Failed to increment usage in table: %s", exc)
        return 0


def check_usage_limit(month: Optional[str] = None, limit: int = MONTHLY_FREE_TIER_LIMIT) -> Tuple[bool, int]:
    """Check if monthly Places API calls are within the free-tier limit.

    Returns:
        (is_allowed: bool, current_calls: int)
    """
    calls = get_monthly_usage(month)
    return (calls < limit, calls)


# ── Lead Storage & Retrieval ──────────────────────────────────────

def save_leads(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Upsert leads into Supabase leads table with conflict resolution on place_id."""
    if not leads:
        return []

    client = get_client()
    if not client:
        logger.warning("No DB client available — returning leads without saving.")
        return leads

    # Normalize leads for DB schema
    clean_leads: List[Dict[str, Any]] = []
    for lead in leads:
        record = dict(lead)
        # Convert why list to string if needed for text column
        if isinstance(record.get("why"), list):
            record["why"] = ", ".join(record["why"])

        # Retain only recognized columns for the leads table
        clean_record = {
            "place_id": record.get("place_id"),
            "brand": record.get("brand"),
            "niche": record.get("niche"),
            "name": record.get("name"),
            "address": record.get("address"),
            "phone": record.get("phone"),
            "website": record.get("website"),
            "website_status": record.get("website_status", "none"),
            "rating": record.get("rating"),
            "reviews": record.get("reviews"),
            "score": record.get("score", 40),
            "label": record.get("label", "cold"),
            "why": record.get("why"),
            "maps_url": record.get("maps_url"),
            "source": record.get("source", "maps"),
        }
        clean_leads.append(clean_record)

    try:
        res = client.table("leads").upsert(clean_leads, on_conflict="place_id").execute()
        logger.info("Successfully upserted %d leads on place_id", len(res.data or clean_leads))
        return res.data or clean_leads
    except Exception as exc:
        logger.error("Failed to upsert leads on place_id: %s", exc)
        # Fallback to name,address,brand conflict if place_id unique index is different
        try:
            res_fb = client.table("leads").upsert(clean_leads, on_conflict="name,address,brand").execute()
            return res_fb.data or clean_leads
        except Exception as fb_exc:
            logger.error("Fallback upsert also failed: %s", fb_exc)
            return leads


def get_leads(
    brand: str,
    website_status: Optional[str] = None,
    label: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Dict[str, Any]], int]:
    """Fetch leads filtered by brand, website_status, and label.

    Returns:
        (leads, total_count)
    """
    client = get_client()
    if not client:
        return [], 0

    try:
        query = client.table("leads").select("*", count="exact").eq("brand", brand)
        if website_status and website_status.strip():
            query = query.eq("website_status", website_status.strip().lower())
        if label and label.strip():
            query = query.eq("label", label.strip().lower())

        query = query.order("score", desc=True).order("created_at", desc=True)
        query = query.range(offset, offset + limit - 1)
        res = query.execute()

        data = res.data or []
        count = res.count if res.count is not None else len(data)
        return data, count
    except Exception as exc:
        logger.error("Failed to fetch leads: %s", exc)
        return [], 0


def get_lead(lead_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single lead by its UUID."""
    client = get_client()
    if not client:
        return None
    try:
        res = client.table("leads").select("*").eq("id", lead_id).execute()
        return res.data[0] if res.data else None
    except Exception as exc:
        logger.error("Failed to fetch lead %s: %s", lead_id, exc)
        return None


def log_outreach(lead_id: str, brand: str, dm_text: str) -> Optional[Dict[str, Any]]:
    """Insert a record into outreach_log."""
    client = get_client()
    if not client:
        return None
    try:
        res = client.table("outreach_log").insert({
            "lead_id": lead_id,
            "brand": brand,
            "dm_text": dm_text,
        }).execute()
        return res.data[0] if res.data else None
    except Exception as exc:
        logger.error("Failed to log outreach: %s", exc)
        return None


def update_lead_dm(lead_id: str, dm_text: str) -> bool:
    """Update outreach_dm for a lead."""
    client = get_client()
    if not client:
        return False
    try:
        client.table("leads").update({"outreach_dm": dm_text}).eq("id", lead_id).execute()
        return True
    except Exception as exc:
        logger.error("Failed to update lead DM: %s", exc)
        return False


def delete_lead(lead_id: str) -> bool:
    """Delete a lead by its UUID."""
    client = get_client()
    if not client:
        return False
    try:
        client.table("leads").delete().eq("id", lead_id).execute()
        return True
    except Exception as exc:
        logger.error("Failed to delete lead %s: %s", lead_id, exc)
        return False


def get_stats(brand: str) -> Dict[str, Any]:
    """Calculate summary statistics for a brand's leads."""
    client = get_client()
    if not client:
        return {
            "hot": 0, "warm": 0, "cold": 0, "total": 0,
            "no_website": 0, "social_only": 0, "has_website": 0,
        }

    try:
        res = client.table("leads").select("score,website_status").eq("brand", brand).execute()
        rows = res.data or []
        hot = sum(1 for r in rows if (r.get("score") or 0) >= 70)
        warm = sum(1 for r in rows if 45 <= (r.get("score") or 0) < 70)
        cold = sum(1 for r in rows if (r.get("score") or 0) < 45)

        no_web = sum(1 for r in rows if r.get("website_status") == "none")
        social = sum(1 for r in rows if r.get("website_status") == "social_only")
        has_web = sum(1 for r in rows if r.get("website_status") == "has_website")

        return {
            "hot": hot,
            "warm": warm,
            "cold": cold,
            "total": len(rows),
            "no_website": no_web,
            "social_only": social,
            "has_website": has_web,
        }
    except Exception as exc:
        logger.error("Failed to get lead stats: %s", exc)
        return {
            "hot": 0, "warm": 0, "cold": 0, "total": 0,
            "no_website": 0, "social_only": 0, "has_website": 0,
        }
