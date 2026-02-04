import streamlit as st
import requests
import json

API_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(page_title="Student Accommodation Assistant", page_icon="🏠")

st.title("🏠 Student Accommodation Assistant")
st.caption("Find the best place for you — smart, personalized, and safe.")

# Session chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Ask me about PGs, flats, rules, or preferences...")

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call backend API
    try:
        response = requests.post(API_URL, params={"query": user_input})
        data = response.json()

        with st.chat_message("assistant"):
            # RAG response (Policy questions)
            if data.get("type") == "policy_answer":
                st.markdown("📋 **Policy Information:**")
                st.markdown(data["answer"])
                
                # Store assistant response
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"📋 **Policy Information:**\n\n{data['answer']}"
                })

            # Error response
            elif data.get("type") == "error":
                st.error("⚠️ " + data["answer"])
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"⚠️ {data['answer']}"
                })

            # Recommendation response (Data search)
            else:
                # Show memory summary if available
                if "memory_summary" in data and data["memory_summary"]:
                    st.info(data["memory_summary"])

                recommendations = data.get("recommendations", [])

                if not recommendations:
                    st.warning("🏠 No matching accommodations found. Try adjusting your criteria or search in different areas.")
                else:
                    st.success(f"✅ Found {len(recommendations)} accommodation(s) matching your preferences:")
                    
                    for i, rec in enumerate(recommendations, 1):
                        with st.container():
                            # Main accommodation header
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.subheader(f"{i}. ₹{rec['rent']}/month • {rec['type'].upper()} • {rec['location']}")
                            with col2:
                                st.metric("Score", f"{rec['score']:.2f}")
                            
                            # Reason and details
                            st.write(f"**Why this fits:** {rec['reason']}")
                            
                            # Key metrics in columns
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("🚗 Distance", f"{rec['distance_from_college_km']:.1f} km")
                            with col2:
                                st.metric("🛡️ Safety", f"{rec['safety_rating']}/5")
                            with col3:
                                furnished_emoji = "✅" if rec["furnished"] else "❌"
                                st.metric("🛏️ Furnished", f"{furnished_emoji}")
                            with col4:
                                alcohol_emoji = "🍺" if not rec["non_alcoholic"] else "🚫"
                                st.metric("🍺 Alcohol", f"{alcohol_emoji}")
                            
                            # Additional details in expandable section
                            with st.expander("📋 More Details"):
                                details_col1, details_col2 = st.columns(2)
                                with details_col1:
                                    st.write(f"**Accommodation ID:** {rec['id']}")
                                    st.write(f"**Smoking Allowed:** {'Yes' if rec['smoking_allowed'] else 'No'}")
                                with details_col2:
                                    st.write(f"**Roommates Allowed:** {'Yes' if rec['roommates_allowed'] else 'No'}")
                                    st.write(f"**Available:** {'Yes' if rec['available'] else 'No'}")
                            
                            st.divider()

                # Store assistant response for chat history
                response_content = f"Found {len(recommendations)} accommodation(s)"
                if "memory_summary" in data:
                    response_content += f"\n{data['memory_summary']}"
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_content
                })

    except requests.exceptions.ConnectionError:
        with st.chat_message("assistant"):
            st.error("🚫 **Connection Error:** Cannot connect to the backend server. Please make sure the FastAPI server is running on http://127.0.0.1:8000")
    except Exception as e:
        with st.chat_message("assistant"):
            st.error(f"❌ **Error:** {str(e)}")

# Sidebar with helpful information
with st.sidebar:
    st.header("💡 How to Use")
    st.markdown("""
    **Ask about accommodations:**
    - "Show me PGs under 10k in Andheri"
    - "Find furnished 1BHK apartments"
    - "Budget under 15000, furnished, near college"
    
    **Ask about policies:**
    - "Is alcohol allowed in PGs?"
    - "What documents are required?"
    - "Can I smoke in hostels?"
    
    **The system remembers your preferences!**
    """)
    
    st.header("🔧 System Status")
    try:
        # Quick health check
        health_response = requests.get("http://127.0.0.1:8000", timeout=2)
        st.success("✅ Backend Connected")
    except:
        st.error("❌ Backend Offline")
