"""Supabase database operations."""

import logging
from typing import Optional, Any

from supabase import Client, create_client

from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_client() -> Optional[Client]:
    global _client
    if _client is not None:
        return _client
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if not url or not key:
        logger.warning("SUPABASE_URL or SUPABASE_KEY not set — DB operations unavailable.")
        return None
    _client = create_client(url, key)
    logger.info("Supabase client initialised for %s", url)
    return _client


def save_leads(leads: list[dict], brand: str) -> list[dict]:
    """Upsert leads to the leads table. Conflict on (name, address, brand)."""
    client = get_client()
    if not client:
        logger.warning("No DB client — returning leads without saving.")
        return leads
    try:
        for lead in leads:
            lead["brand"] = brand
        result = client.table("leads").upsert(
            leads, on_conflict="name,address,brand"
        ).execute()
        logger.info("Upserted %d leads for brand=%s", len(result.data), brand)
        return result.data
    except Exception as e:
        logger.error("Failed to save leads: %s", e)
        return leads


def get_leads(
    brand: str,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Fetch leads filtered by brand and optional source. Returns (leads, total)."""
    client = get_client()
    if not client:
        return [], 0
    try:
        query = client.table("leads").select("*", count="exact").eq("brand", brand)
        if source and source != "all":
            query = query.eq("source", source)
        query = query.order("score", desc=True).order("created_at", desc=True)
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        return result.data, result.count or len(result.data)
    except Exception as e:
        logger.error("Failed to fetch leads: %s", e)
        return [], 0


def get_lead(lead_id: str) -> Optional[dict]:
    """Fetch a single lead by ID."""
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("leads").select("*").eq("id", lead_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error("Failed to fetch lead %s: %s", lead_id, e)
        return None


def delete_lead(lead_id: str) -> bool:
    """Delete a lead by ID. Returns True on success."""
    client = get_client()
    if not client:
        return False
    try:
        client.table("leads").delete().eq("id", lead_id).execute()
        return True
    except Exception as e:
        logger.error("Failed to delete lead %s: %s", lead_id, e)
        return False


def get_stats(brand: str) -> dict[str, Any]:
    """Return hot/warm/cold counts and by-source breakdown."""
    client = get_client()
    if not client:
        return {"hot": 0, "warm": 0, "cold": 0, "total": 0, "by_source": {"maps": 0, "instagram": 0, "linkedin": 0}}
    try:
        result = client.table("leads").select("score,source").eq("brand", brand).execute()
        rows = result.data
        hot = sum(1 for r in rows if (r.get("score") or 0) >= 70)
        warm = sum(1 for r in rows if 45 <= (r.get("score") or 0) < 70)
        cold = sum(1 for r in rows if (r.get("score") or 0) < 45)
        by_source = {"maps": 0, "instagram": 0, "linkedin": 0}
        for r in rows:
            src = r.get("source", "")
            if src in by_source:
                by_source[src] += 1
        return {"hot": hot, "warm": warm, "cold": cold, "total": len(rows), "by_source": by_source}
    except Exception as e:
        logger.error("Failed to get stats: %s", e)
        return {"hot": 0, "warm": 0, "cold": 0, "total": 0, "by_source": {"maps": 0, "instagram": 0, "linkedin": 0}}


def log_outreach(lead_id: str, brand: str, dm_text: str) -> Optional[dict]:
    """Insert a row into outreach_log."""
    client = get_client()
    if not client:
        return None
    try:
        result = client.table("outreach_log").insert({
            "lead_id": lead_id,
            "brand": brand,
            "dm_text": dm_text,
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error("Failed to log outreach: %s", e)
        return None


def update_lead_dm(lead_id: str, dm_text: str) -> bool:
    """Cache the generated DM back to the leads table."""
    client = get_client()
    if not client:
        return False
    try:
        client.table("leads").update({"outreach_dm": dm_text}).eq("id", lead_id).execute()
        return True
    except Exception as e:
        logger.error("Failed to update lead DM: %s", e)
        return False
