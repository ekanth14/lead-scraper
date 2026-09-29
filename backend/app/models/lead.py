"""Pydantic models for the lead scraper."""

from typing import Optional, List, Union
from pydantic import BaseModel, Field


class ScrapeMapsRequest(BaseModel):
    """Request body for POST /scrape/maps."""
    niche: str = Field(..., min_length=1, description="Search niche, e.g. 'architect' or 'cafe'")
    city: str = Field("Bangalore", description="City to search in")
    brand: str = Field(..., pattern="^(orv|zien)$", description="Target brand: 'orv' or 'zien'")
    max_results: int = Field(20, ge=1, le=40, description="Max results (defaults to 20, supports up to 40)")
    api_key: Optional[str] = Field(None, description="Optional Google Maps API key override")


# Alias for backward compatibility
ScrapeRequest = ScrapeMapsRequest


class OutreachRequest(BaseModel):
    """Request body for POST /outreach."""
    lead_id: Optional[str] = Field(None, description="Lead UUID — fetch from DB")
    lead: Optional[dict] = Field(None, description="Lead dict if not using lead_id")
    brand: str = Field(..., pattern="^(orv|zien)$")


class Lead(BaseModel):
    """Full lead record corresponding to Supabase leads table."""
    id: Optional[str] = None
    place_id: str
    brand: str
    niche: Optional[str] = None
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    website_status: str = "none"
    rating: Optional[float] = None
    reviews: Optional[int] = None
    score: int = 40
    label: str = "cold"
    why: Optional[Union[str, List[str]]] = None
    maps_url: Optional[str] = None
    source: Optional[str] = "maps"
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
