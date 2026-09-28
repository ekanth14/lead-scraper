"""Scoring logic for leads."""

def score_lead(lead: dict, brand: str, niche: str, source: str) -> dict:
    score = 45
    signals = []
    
    website = lead.get("website")
    if not website or str(website).strip().lower() == "none found":
        score += 28
        signals.append("No website found")
        
    rating = lead.get("rating")
    if rating is not None and isinstance(rating, (int, float)) and rating < 4.0:
        score += 14
        signals.append(f"Low rating {rating}⭐")
        
    reviews = lead.get("reviews")
    if reviews is not None and isinstance(reviews, (int, float)) and reviews < 60:
        score += 13
        signals.append(f"Few reviews ({reviews})")
        
    niche_lower = niche.lower()
    if brand.lower() == 'zien' and any(n in niche_lower for n in ['architect', 'real estate', 'interior', 'construction']):
        score += 10
        
    if brand.lower() == 'orv' and rating is not None and isinstance(rating, (int, float)) and rating < 3.5:
        score += 8
        
    score = min(score, 99)
    
    lead["score"] = score
    lead["why"] = " · ".join(signals) if signals else ""
    lead["source"] = source
    return lead
