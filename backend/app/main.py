"""FastAPI entry point for the Lead Scraper API serving Orvyqmedia ('orv') and Zien Technologies ('zien')."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import scrape, leads

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lead Scraper API",
    description="Dual-brand Lead Scraper backend for Orvyqmedia ('orv') and Zien Technologies ('zien').",
    version="1.0.0",
)

# ── CORS Middleware ──────────────────────────────────────────────
allowed_origins = ["http://localhost:5173"]
if settings.FRONTEND_URL and settings.FRONTEND_URL not in allowed_origins:
    allowed_origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include Routers ──────────────────────────────────────────────
app.include_router(scrape.router)
app.include_router(leads.router)


# ── Health & Keep-Alive Endpoints ────────────────────────────────
@app.api_route("/ping", methods=["GET", "HEAD"], tags=["keep-alive"])
def ping():
    """Keep-alive endpoint supporting GET and HEAD for UptimeRobot monitoring."""
    return {"pong": True}


@app.api_route("/", methods=["GET", "HEAD"], tags=["health"])
def root():
    return {
        "status": "ok",
        "service": "lead-scraper-api",
        "brands": ["orv", "zien"],
        "version": "1.0.0",
    }


@app.api_route("/health", methods=["GET", "HEAD"], tags=["health"])
def health():
    return {"status": "ok", "version": "1.0.0"}


logger.info("Lead Scraper API initialized with CORS origins: %s", allowed_origins)
