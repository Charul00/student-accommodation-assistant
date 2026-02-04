from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.services.smart_sql_agent import smart_sql_agent
from app.services.memory import extract_preferences, get_memory_summary
from app.services.rag import build_rag_chain

router = APIRouter()

# Response models for API documentation
class PolicyResponse(BaseModel):
    type: str = "policy_answer"
    question: str
    answer: str
    source: str = "accommodation_policies"

class AccommodationResult(BaseModel):
    id: int
    type: str
    rent: int
    location: str
    distance_from_college_km: float
    furnished: bool
    non_alcoholic: bool
    smoking_allowed: bool
    safety_rating: int
    roommates_allowed: bool
    available: bool

class AccommodationSearchResponse(BaseModel):
    type: str = "accommodation_search"
    query: str
    sql_generated: str
    results_count: int
    accommodations: List[AccommodationResult]
    response: str
    preferences: Dict[str, Any]
    memory: Dict[str, Any]
    memory_summary: str

class ErrorResponse(BaseModel):
    type: str = "error"
    query: str
    error: Optional[str] = None
    response: str

# Simple session memory (in-memory store for now)
SESSION_MEMORY = {
    "budget": None,
    "preferred_location": None,
    "room_type": None,
    "non_alcoholic": None,
    "furnished": None,
    "smoking_allowed": None
}

# Initialize RAG chain on startup
print("🔄 Initializing RAG chain...")
RAG_CHAIN = build_rag_chain()

def is_policy_question(query: str) -> bool:
    """
    Detect if query is asking about policies/rules rather than data search
    """
    policy_keywords = [
        "rule", "policy", "allowed", "document", "verification", 
        "alcohol", "smoking", "guest", "required", "permit", 
        "regulation", "guideline", "procedure", "process",
        "what documents", "police verification", "is alcohol",
        "can i smoke", "are guests", "how to", "what is"
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in policy_keywords)

@router.post(
    "/chat",
    summary="Chat with Student Accommodation Assistant",
    description="""
    Chat with the AI assistant to find student accommodations or get policy information.
    
    **Query Types:**
    - **Accommodation Search**: "find cheap PG near college", "furnished flat under 10k"
    - **Policy Questions**: "what are the smoking rules?", "alcohol policy", "required documents"
    
    **Features:**
    - AI-powered SQL query generation
    - Memory-based preference tracking
    - Natural language responses
    - Policy document retrieval (RAG)
    """,
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Successful response with accommodation results or policy information",
            "content": {
                "application/json": {
                    "examples": {
                        "accommodation_search": {
                            "summary": "Accommodation search result",
                            "value": {
                                "type": "accommodation_search",
                                "query": "find cheap accommodation",
                                "results_count": 5,
                                "response": "I found several affordable accommodations for you...",
                                "accommodations": [
                                    {
                                        "id": 1,
                                        "type": "pg",
                                        "rent": 8000,
                                        "location": "Viman Nagar",
                                        "furnished": True
                                    }
                                ]
                            }
                        },
                        "policy_answer": {
                            "summary": "Policy question result", 
                            "value": {
                                "type": "policy_answer",
                                "question": "What are the smoking rules?",
                                "answer": "Smoking policies vary by accommodation...",
                                "source": "accommodation_policies"
                            }
                        }
                    }
                }
            }
        }
    }
)
def chat(
    query: str = Query(
        ..., 
        description="Your question about accommodations or policies",
        example="find me a cheap PG near college"
    )
):
    global SESSION_MEMORY

    # 🔹 RAG PATH: Handle policy/rule questions
    if is_policy_question(query):
        if RAG_CHAIN:
            try:
                answer = RAG_CHAIN.invoke(query)
                return {
                    "type": "policy_answer",
                    "question": query,
                    "answer": answer,
                    "source": "accommodation_policies"
                }
            except Exception as e:
                print(f"❌ RAG Error: {e}")
                return {
                    "type": "error",
                    "question": query,
                    "answer": "Sorry, I couldn't access the policy information at the moment. Please try asking about specific accommodations instead."
                }
        else:
            return {
                "type": "error", 
                "question": query,
                "answer": "Policy information service is currently unavailable. Please contact support for policy questions."
            }

    # 🔹 NEW SMART SQL AGENT PATH - Uses LangChain + OpenAI for entire flow
    
    # Update memory from current query
    SESSION_MEMORY = extract_preferences(query, SESSION_MEMORY)
    
    # Generate memory summary
    memory_summary = get_memory_summary(SESSION_MEMORY)
    
    print(f"🔸 Original query: {query}")
    print(f"🔸 Current memory: {SESSION_MEMORY}")

    # Use Smart SQL Agent for complete LangChain-powered processing
    result = smart_sql_agent.process_query(query, SESSION_MEMORY)
    
    # Add memory information to response
    result["memory"] = SESSION_MEMORY
    result["memory_summary"] = memory_summary
    
    return result