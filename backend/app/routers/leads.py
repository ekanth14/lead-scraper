"""Lead management and export endpoints."""

import io
import logging
from datetime import date
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.db.supabase import get_leads, delete_lead, get_stats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", include_in_schema=False)
@router.get("/")
async def list_leads(
    brand: str = Query(..., pattern="^(orv|zien)$", description="Brand filter: 'orv' or 'zien'"),
    website_status: Optional[str] = Query(None, description="Filter by 'none', 'social_only', or 'has_website'"),
    label: Optional[str] = Query(None, description="Filter by 'hot', 'warm', or 'cold'"),
    limit: int = Query(50, ge=1, le=500, description="Max number of leads to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """Retrieve leads filtered by brand, website_status, and label, ordered by score descending."""
    leads, total = get_leads(
        brand=brand,
        website_status=website_status,
        label=label,
        limit=limit,
        offset=offset,
    )
    return {"leads": leads, "total": total, "brand": brand}


@router.get("/stats")
async def lead_stats(brand: str = Query(..., pattern="^(orv|zien)$")):
    """Return summary statistics (hot/warm/cold and website breakdown) for a brand."""
    stats = get_stats(brand)
    return stats


@router.get("/export")
async def export_leads(
    brand: str = Query(..., pattern="^(orv|zien)$", description="Brand filter: 'orv' or 'zien'"),
    website_status: Optional[str] = Query(None, description="Optional website status filter"),
    label: Optional[str] = Query(None, description="Optional qualification label filter"),
):
    """Export filtered leads to CSV with website and website_status included."""
    leads, _ = get_leads(
        brand=brand,
        website_status=website_status,
        label=label,
        limit=5000,
        offset=0,
    )
    if not leads:
        raise HTTPException(status_code=404, detail="No leads found for export with given filters")

    df = pd.DataFrame(leads)

    # Ensure website and website_status are prominently present
    if "website_status" not in df.columns:
        df["website_status"] = "none"
    if "website" not in df.columns:
        df["website"] = ""

    # Reorder columns logically if available
    preferred_order = [
        "name", "brand", "niche", "score", "label",
        "website_status", "website", "phone", "rating", "reviews",
        "address", "why", "maps_url", "place_id", "created_at"
    ]
    existing_cols = [c for c in preferred_order if c in df.columns]
    remaining_cols = [c for c in df.columns if c not in existing_cols]
    df = df[existing_cols + remaining_cols]

    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    filename = f"leads-{brand}-{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete("/{lead_id}", status_code=204)
async def remove_lead(lead_id: str):
    """Delete a lead by its UUID."""
    success = delete_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found or could not be deleted")
    return None
