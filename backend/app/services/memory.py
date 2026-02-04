import re

def extract_preferences(query: str, memory: dict):
    """
    Extract user preferences from natural language query and update memory.
    
    Args:
        query: User's natural language query
        memory: Current memory dictionary to update
        
    Returns:
        Updated memory dictionary with extracted preferences
    """
    q = query.lower()

    # Budget extraction - look for 4-5 digit numbers (rent amounts)
    budget_match = re.search(r'under\s+(\d{4,5})|below\s+(\d{4,5})|(\d{4,5})', q)
    if budget_match:
        # Get the first non-None group
        budget_value = next(group for group in budget_match.groups() if group is not None)
        memory["budget"] = int(budget_value)

    # Location extraction - common areas in Mumbai, Pune, Bangalore
    locations = [
        "andheri", "bandra", "powai", "malad", "borivali", "thane", "mumbai",
        "viman nagar", "hinjewadi", "koregaon park", "wakad", "baner", "pune", 
        "koramangala", "indiranagar", "electronic city", "whitefield", "bangalore"
    ]
    for loc in locations:
        if loc in q:
            memory["preferred_location"] = loc.title()
            break

    # Room type extraction
    if "pg" in q or "paying guest" in q:
        memory["room_type"] = "pg"
    elif "1rk" in q or "1 rk" in q:
        memory["room_type"] = "1rk"
    elif "1bhk" in q or "1 bhk" in q:
        memory["room_type"] = "1bhk"
    elif "3bhk" in q or "3 bhk" in q:
        memory["room_type"] = "3bhk"

    # Lifestyle preferences
    if "non-alcoholic" in q or "no alcohol" in q or "alcohol free" in q:
        memory["non_alcoholic"] = True
    elif "alcohol allowed" in q or "drinking allowed" in q:
        memory["non_alcoholic"] = False

    # Additional preferences
    if "furnished" in q:
        memory["furnished"] = True
    elif "unfurnished" in q:
        memory["furnished"] = False

    if "smoking" in q and ("allowed" in q or "ok" in q):
        memory["smoking_allowed"] = True
    elif "no smoking" in q or "smoking not allowed" in q:
        memory["smoking_allowed"] = False

    return memory

def merge_memory_with_query(query: str, memory: dict) -> str:
    """
    Merge user's stored preferences with the current query to create a comprehensive search.
    
    Args:
        query: Current user query
        memory: Stored user preferences
        
    Returns:
        Enhanced query with memory context
    """
    # Start with the original query
    enhanced_parts = [query]
    
    # Add memory-based constraints that aren't already in the query
    query_lower = query.lower()
    
    # Add room type if remembered and not in current query
    if memory.get("room_type") and memory["room_type"] not in query_lower:
        enhanced_parts.append(f"{memory['room_type']} accommodation")
    
    # Add location if remembered and not in current query
    if memory.get("preferred_location"):
        location_in_query = any(loc in query_lower for loc in [
            memory["preferred_location"].lower(), 
            memory["preferred_location"].lower().replace(" ", "")
        ])
        if not location_in_query:
            enhanced_parts.append(f"in {memory['preferred_location']}")
    
    # Add budget if remembered and not in current query
    if memory.get("budget") and not re.search(r'\d{4,5}', query_lower):
        enhanced_parts.append(f"under {memory['budget']}")
    
    # Add lifestyle preferences if remembered and not in current query
    # Use clearer, non-conflicting terms
    if memory.get("non_alcoholic") is True and "alcohol" not in query_lower:
        enhanced_parts.append("alcohol-free accommodation")
    elif memory.get("non_alcoholic") is False and "alcohol" not in query_lower:
        enhanced_parts.append("alcohol allowed accommodation")
    
    # Add smoking preference if remembered and not in current query
    if memory.get("smoking_allowed") is False and "smoking" not in query_lower:
        enhanced_parts.append("smoke-free accommodation")
    elif memory.get("smoking_allowed") is True and "smoking" not in query_lower:
        enhanced_parts.append("smoking friendly accommodation")
    
    # Add furnished preference if remembered and not in current query
    if memory.get("furnished") is True and "furnished" not in query_lower:
        enhanced_parts.append("furnished accommodation")
    elif memory.get("furnished") is False and "furnished" not in query_lower:
        enhanced_parts.append("unfurnished accommodation")
    
    # Join all parts into a comprehensive query
    enhanced_query = " ".join(enhanced_parts)
    
    return enhanced_query

def get_memory_summary(memory: dict) -> str:
    """
    Generate a human-readable summary of current user preferences.
    
    Args:
        memory: Current memory dictionary
        
    Returns:
        String summary of preferences
    """
    summary_parts = []
    
    if memory.get("budget"):
        summary_parts.append(f"Budget: ₹{memory['budget']:,}")
    
    if memory.get("preferred_location"):
        summary_parts.append(f"Location: {memory['preferred_location']}")
    
    if memory.get("room_type"):
        summary_parts.append(f"Type: {memory['room_type'].upper()}")
    
    if memory.get("non_alcoholic") is not None:
        alcohol_pref = "No alcohol" if memory["non_alcoholic"] else "Alcohol allowed"
        summary_parts.append(alcohol_pref)
    
    if memory.get("furnished") is not None:
        furnished_pref = "Furnished" if memory["furnished"] else "Unfurnished"
        summary_parts.append(furnished_pref)
    
    if memory.get("smoking_allowed") is not None:
        smoking_pref = "Smoking allowed" if memory["smoking_allowed"] else "No smoking"
        summary_parts.append(smoking_pref)
    
    if summary_parts:
        return f"🧠 Your preferences: {' | '.join(summary_parts)}"
    else:
        return "🧠 No specific preferences set yet. Tell me what you're looking for!"