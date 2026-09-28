"""Claude AI outreach generation service."""

import logging
from anthropic import AsyncAnthropic
from app.config import settings
from app.db.supabase import update_lead_dm

logger = logging.getLogger(__name__)

async def generate_outreach(lead: dict, brand: str) -> str:
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set — using placeholder DM.")
        return "Hey! Saw your business and thought we could help you grow. Let's chat for 15 mins!"
        
    try:
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        name = lead.get("name", "there")
        category = lead.get("category", "Business")
        location = lead.get("address") or lead.get("city", "")
        rating = lead.get("rating", "")
        reviews = lead.get("reviews", "")
        website = lead.get("website") or "None found"
        why = lead.get("why", "")
        
        if brand.lower() == 'orv':
            prompt = f"""You write cold outreach DMs for Orvyqmedia, a marketing and advertising agency based in Bangalore, India.

Write a short, friendly, personalised cold DM (under 110 words) to:

Business : {name}
Type     : {category}
Location : {location}
Rating   : {rating} stars ({reviews} reviews)
Website  : {website}
Why      : {why}

Offer better social media, Meta or Google Ads, or brand identity.
Reference something specific about their business.
End with a soft CTA for a 15-minute call.
Sound human. No corporate language. No emojis.
"""
        elif brand.lower() == 'zien':
            prompt = f"""You write cold outreach DMs for Zien Technologies (ziennexus.app), a tech company in Bangalore that builds websites, automated workflows, digital solutions, and 3D visualization for homes and buildings.

Write a short, friendly, personalised cold DM (under 110 words) to:

Business : {name}
Type     : {category}
Location : {location}
Website  : {website}
Why      : {why}

Match offer to business type:
- Architect / real estate / interior → interactive 3D walkthrough + website
- Startup / SME / logistics → automated workflows or custom web app
- Construction → 3D building visualization for client presentations
Reference something specific. CTA: offer a free demo.
Sound human. No corporate language. No emojis.
"""
        else:
            prompt = f"""Write a short, friendly cold DM to {name} in {location}. They are a {category}. No emojis."""
            
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        dm_text = response.content[0].text.strip()
        
        lead_id = lead.get("id")
        if lead_id:
            update_lead_dm(lead_id, dm_text)
            
        return dm_text
    except Exception as e:
        logger.error("Error generating outreach: %s", e)
        return "Hey! Saw your business and thought we could help you grow. Let's chat!"
