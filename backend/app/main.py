"""Lead Scraper API — FastAPI application entry point with 24/7 background maintenance."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.db.supabase import get_client
from app.routers import scrape, leads, outreach
from app.routers.scrape import limiter as scrape_limiter, reset_all_daily_counters
import app.services.maps as maps_service

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Daily Google Maps limit constants (referenced for free-tier monitoring)
MAPS_CALLS_TODAY = 0
MAPS_LIMIT = 40  # Google gives $200/month credit, ~40 searches/day is safe


# ── Timezone Helper (IST: UTC+5:30) ──────────────────────────────
def _seconds_until_ist(hour: int, minute: int = 0) -> float:
    """Calculate seconds from now until the next occurrence of target IST time."""
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist_tz)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


# ── Background Task: Daily Cleanup at 2:00 AM IST ───────────────
async def cleanup_old_leads():
    """Background task running daily at 2am IST to keep Supabase DB within 500MB free tier limit."""
    while True:
        delay = _seconds_until_ist(2, 0)
        logger.info("[DB Cleanup] Next run scheduled in %.1f hours (at 2:00 AM IST)", delay / 3600)
        await asyncio.sleep(delay)

        try:
            client = get_client()
            if not client:
                logger.warning("[DB Cleanup] Supabase client unavailable — skipping cleanup.")
                continue

            cutoff_leads = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            cutoff_logs = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()

            # Delete leads older than 30 days
            client.table("leads").delete().lt("created_at", cutoff_leads).execute()

            # Delete outreach_log entries older than 60 days
            client.table("outreach_log").delete().lt("created_at", cutoff_logs).execute()

            # Log current table sizes to console
            leads_res = client.table("leads").select("id", count="exact").execute()
            logs_res = client.table("outreach_log").select("id", count="exact").execute()

            leads_count = leads_res.count if leads_res else 0
            logs_count = logs_res.count if logs_res else 0

            logger.info(
                "[DB Cleanup] Complete. Current table sizes: leads=%s rows, outreach_log=%s rows",
                leads_count,
                logs_count,
            )
        except Exception as exc:
            logger.error("[DB Cleanup] Error during execution: %s", exc)


# ── Background Task: Daily Rate Limit Reset at Midnight IST ─────
async def reset_daily_counters_task():
    """Background task running daily at midnight IST to reset daily scrape counters."""
    global MAPS_CALLS_TODAY
    while True:
        delay = _seconds_until_ist(0, 0)
        logger.info("[Rate Limit] Next counter reset in %.1f hours (at midnight IST)", delay / 3600)
        await asyncio.sleep(delay)

        MAPS_CALLS_TODAY = 0
        maps_service.reset_maps_calls()
        reset_all_daily_counters()
        logger.info("[Rate Limit] Daily scrape counters have been reset for the new day.")


# ── Application Lifespan ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: spawn background maintenance tasks
    task_cleanup = asyncio.create_task(cleanup_old_leads())
    task_reset = asyncio.create_task(reset_daily_counters_task())
    logger.info("Background tasks started (2am IST cleanup, midnight IST counter reset)")
    yield
    # Shutdown: cancel background tasks cleanly
    task_cleanup.cancel()
    task_reset.cancel()
    logger.info("Background tasks shut down cleanly.")


# ── App ──────────────────────────────────────────────────────────
app = FastAPI(
    title="Lead Scraper API",
    description="Scrape, score, and manage business leads with AI-powered outreach.",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = scrape_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ─────────────────────────────────────────────────────────
origins = ["http://localhost:5173"]
if settings.FRONTEND_URL and settings.FRONTEND_URL not in origins:
    origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Logging Middleware ───────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    brand = request.query_params.get("brand", "-")
    logger.info(
        "%s %s brand=%s status=%d duration=%.1fms",
        request.method,
        request.url.path,
        brand,
        response.status_code,
        duration_ms,
    )
    return response


# ── Error Handling Middleware ────────────────────────────────────
@app.middleware("http")
async def error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": type(exc).__name__, "detail": str(exc), "status": 500},
        )


# ── Routers ──────────────────────────────────────────────────────
app.include_router(scrape.router)
app.include_router(leads.router)
app.include_router(outreach.router)


# ── Health & Keep-Alive Endpoints ────────────────────────────────
@app.api_route("/", methods=["GET", "HEAD"], tags=["health"])
async def root():
    return {"status": "ok", "service": "lead-scraper-api", "version": "1.0.0"}


@app.api_route("/health", methods=["GET", "HEAD"], tags=["health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.api_route("/ping", methods=["GET", "HEAD"], tags=["keep-alive"])
def ping():
    """Keep-alive endpoint pinged every 5 min by UptimeRobot to prevent Render free-tier spin down."""
    return {"pong": True}


logger.info("Lead Scraper API v1.0.0 ready — CORS origins: %s", origins)
