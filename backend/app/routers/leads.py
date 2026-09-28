"""Lead management endpoints."""

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


@router.get("/")
async def list_leads(
    brand: str = Query(..., pattern="^(orv|zien)$"),
    source: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Return leads filtered by brand, ordered by score desc."""
    leads, total = get_leads(brand=brand, source=source, limit=limit, offset=offset)
    return {"leads": leads, "total": total, "brand": brand}


@router.get("/stats")
async def lead_stats(brand: str = Query(..., pattern="^(orv|zien)$")):
    """Return hot/warm/cold counts and by-source breakdown."""
    stats = get_stats(brand)
    return stats


@router.get("/export")
async def export_leads(
    brand: str = Query(..., pattern="^(orv|zien)$"),
    source: Optional[str] = Query(None),
    format: str = Query("csv"),
):
    """Export leads as CSV file download."""
    leads, _ = get_leads(brand=brand, source=source, limit=5000, offset=0)
    if not leads:
        raise HTTPException(status_code=404, detail="No leads found for export")

    df = pd.DataFrame(leads)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    filename = f"{brand}-leads-{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete("/{lead_id}", status_code=204)
async def remove_lead(lead_id: str):
    """Delete a lead by ID."""
    success = delete_lead(lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found or could not be deleted")
    return None
