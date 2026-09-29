"""Scoring logic for leads according to brand and qualification signals."""

from typing import Optional, List, Dict, Any


def score_lead(
    website_status: str,
    rating: Optional[float],
    reviews: Optional[int],
    brand: str,
    niche: str,
) -> Dict[str, Any]:
    """Calculate lead score (base 40, cap 99), qualification label, and explanatory signals.

    Rules:
    - Base: 40
    - "none" website: +30
    - "social_only" website: +25
    - rating < 4.0: +10
    - reviews < 50: +10
    - brand 'zien' and niche has architect, interior, real estate, or construction: +10
    - Capped at 99
    - Label: hot (>= 70), warm (>= 45), cold (< 45)
    - Returns score, label, why (signal list)
    """
    score = 40
    signals: List[str] = []

    # Website status scoring
    if website_status == "none":
        score += 30
        signals.append("No website (+30)")
    elif website_status == "social_only":
        score += 25
        signals.append("Social/Bio link only (+25)")

    # Rating scoring (< 4.0)
    if rating is not None and rating < 4.0:
        score += 10
        signals.append(f"Rating {rating} < 4.0 (+10)")

    # Review count scoring (< 50 or unreviewed)
    if reviews is not None and reviews < 50:
        score += 10
        signals.append(f"Reviews {reviews} < 50 (+10)")
    elif reviews is None or reviews == 0:
        score += 10
        signals.append("Reviews < 50 (+10)")

    # Brand 'zien' target niche bonus
    brand_lower = (brand or "").strip().lower()
    niche_lower = (niche or "").strip().lower()
    zien_target_niches = ["architect", "interior", "real estate", "construction"]
    if brand_lower == "zien" and any(target in niche_lower for target in zien_target_niches):
        score += 10
        signals.append("Target industry for Zien (+10)")

    # Cap at 99
    score = min(score, 99)

    # Label qualification
    if score >= 70:
        label = "hot"
    elif score >= 45:
        label = "warm"
    else:
        label = "cold"

    return {
        "score": score,
        "label": label,
        "why": signals,
    }
