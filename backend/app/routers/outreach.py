"""Outreach generation endpoint."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.lead import OutreachRequest
from app.services.claude import generate_outreach
from app.db.supabase import get_lead, log_outreach

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.post("/")
async def create_outreach(body: OutreachRequest):
    """Generate an AI outreach DM for a lead."""
    lead = body.lead
    lead_id = body.lead_id

    # If lead_id provided, fetch from DB
    if lead_id and not lead:
        lead = get_lead(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

    if not lead:
        raise HTTPException(status_code=400, detail="Provide lead_id or lead dict")

    try:
        dm = await generate_outreach(lead=lead, brand=body.brand)

        # Log to outreach_log
        lid = lead_id or lead.get("id")
        if lid:
            log_outreach(lead_id=lid, brand=body.brand, dm_text=dm)

        return {"dm": dm, "lead_id": lid}
    except Exception as exc:
        logger.error("Outreach generation failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Outreach error: {exc}") from exc
