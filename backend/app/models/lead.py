"""Pydantic models for the lead scraper."""

from typing import Optional
from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    """Request body for all /scrape/* routes."""
    niche: str = Field(..., min_length=1, description="Search niche, e.g. 'restaurant'")
    city: str = Field("Bangalore", description="City to search in")
    api_key: Optional[str] = Field(None, description="Optional override API key or Apify token")
    brand: str = Field(..., pattern="^(orv|zien)$", description="Brand: 'orv' or 'zien'")


class OutreachRequest(BaseModel):
    """Request body for POST /outreach."""
    lead_id: Optional[str] = Field(None, description="Lead UUID — fetch from DB")
    lead: Optional[dict] = Field(None, description="Lead dict if not using lead_id")
    brand: str = Field(..., pattern="^(orv|zien)$")


class Lead(BaseModel):
    """Full lead record from the database."""
    id: Optional[str] = None
    brand: str
    source: str
    name: str
    category: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    followers: Optional[str] = None
    score: Optional[int] = None
    why: Optional[str] = None
    outreach_dm: Optional[str] = None
    niche: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
