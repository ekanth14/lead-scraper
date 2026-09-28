"""Database package."""

from app.db.supabase import (
    get_client,
    save_leads,
    get_leads,
    get_lead,
    delete_lead,
    get_stats,
    log_outreach,
    update_lead_dm,
)

__all__ = [
    "get_client",
    "save_leads",
    "get_leads",
    "get_lead",
    "delete_lead",
    "get_stats",
    "log_outreach",
    "update_lead_dm",
]
