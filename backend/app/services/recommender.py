def recommend(accommodations: list, user_preferences: dict):
    """
    Recommendation system with transparent, explainable scoring logic.
    
    Scoring Formula:
    score = 0.35 * rent_score + 0.25 * distance_score + 0.20 * safety_score + 
            0.10 * furnished_bonus + 0.10 * lifestyle_bonus
    
    Args:
        accommodations: List of accommodation dictionaries
        user_preferences: Dictionary with user preferences like max_budget, non_alcoholic, etc.
    
    Returns:
        List of top 5 accommodations sorted by score with explanations
    """
    recommendations = []

    # Handle None budget by using reasonable default or inferring from data
    max_budget = user_preferences.get("max_budget")
    if max_budget is None:
        # If no budget provided, use 1.5x the highest rent in results as reasonable max
        if accommodations:
            highest_rent = max(acc["rent"] for acc in accommodations)
            max_budget = int(highest_rent * 1.5)
        else:
            max_budget = 15000  # Fallback default

    for acc in accommodations:
        # Normalize rent (lower is better)
        rent_score = max(0, 1 - (acc["rent"] / max_budget))

        # Normalize distance (closer is better, cap at 10km)
        distance_score = max(0, 1 - (acc["distance_from_college_km"] / 10))

        # Safety rating (1–5)
        safety_score = acc["safety_rating"] / 5

        # Furnished bonus
        furnished_bonus = 1 if acc["furnished"] else 0

        # Enhanced lifestyle matching with memory
        lifestyle_bonus = 1
        
        # Check non-alcoholic preference
        if user_preferences.get("non_alcoholic") is True and not acc["non_alcoholic"]:
            lifestyle_bonus = 0
        elif user_preferences.get("non_alcoholic") is False and acc["non_alcoholic"]:
            lifestyle_bonus = 0.5  # Partial match if user wants alcohol but place doesn't allow
            
        # Check smoking preference
        if user_preferences.get("smoking_allowed") is True and not acc["smoking_allowed"]:
            lifestyle_bonus *= 0.5
        elif user_preferences.get("smoking_allowed") is False and acc["smoking_allowed"]:
            lifestyle_bonus *= 0.7
            
        # Check furnished preference
        if user_preferences.get("furnished") is True and not acc["furnished"]:
            furnished_bonus *= 0.5
        elif user_preferences.get("furnished") is False and acc["furnished"]:
            furnished_bonus *= 0.7

        # Final score calculation
        score = (
            0.35 * rent_score +
            0.25 * distance_score +
            0.20 * safety_score +
            0.10 * furnished_bonus +
            0.10 * lifestyle_bonus
        )

        # Generate explanation reasons
        reasons = []
        if rent_score > 0.7:
            reasons.append("Affordable rent")
        elif rent_score > 0.5:
            reasons.append("Reasonable rent")
            
        if distance_score > 0.7:
            reasons.append("Close to college")
        elif distance_score > 0.5:
            reasons.append("Moderate distance")
            
        if safety_score > 0.6:
            reasons.append("Good safety rating")
        elif safety_score > 0.4:
            reasons.append("Average safety")
            
        if furnished_bonus > 0.5:
            reasons.append("Furnished")
            
        if lifestyle_bonus > 0.7:
            reasons.append("Perfect lifestyle match")
        elif lifestyle_bonus > 0.5:
            reasons.append("Good lifestyle match")

        # Add memory-based explanations
        if user_preferences.get("non_alcoholic") and acc["non_alcoholic"]:
            reasons.append("Alcohol-free environment")
        if user_preferences.get("smoking_allowed") is False and not acc["smoking_allowed"]:
            reasons.append("Smoke-free environment")

        recommendations.append({
            **acc,
            "score": round(score, 2),
            "reason": ", ".join(reasons) if reasons else "Basic accommodation"
        })

    # Sort by score (descending)
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    return recommendations[:5]
