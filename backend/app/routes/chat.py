from fastapi import APIRouter
from app.services.smart_sql_agent import smart_sql_agent
from app.services.memory import extract_preferences, get_memory_summary
from app.services.rag import build_rag_chain

router = APIRouter()

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

@router.post("/chat")
def chat(query: str):
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