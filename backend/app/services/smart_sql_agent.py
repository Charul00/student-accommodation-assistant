from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import psycopg2
from urllib.parse import urlparse
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URI = os.getenv('DATABASE_URL')
if not DATABASE_URI:
    DB_USER = os.getenv('DB_USER', 'charulchim')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'accommodation')
    DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Database Schema
DB_SCHEMA = """
Table: accommodations
Columns:
- id: integer (primary key)
- type: text (values: 'pg', 'flat', 'hostel')
- rent: integer (monthly rent in rupees)
- location: text (area name)
- distance_from_college_km: float (distance in kilometers)
- furnished: boolean (true if furnished)
- non_alcoholic: boolean (true if alcohol not allowed)
- smoking_allowed: boolean (true if smoking allowed)
- safety_rating: integer (1-5, 5 being safest)
- roommates_allowed: boolean (true if roommates allowed)
- available: boolean (true if currently available)
"""

class SmartSQLAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.setup_chains()
    
    def setup_chains(self):
        """Setup LangChain chains for SQL generation and response formatting"""
        
        # 1. SQL Generation Chain
        sql_prompt = ChatPromptTemplate.from_template("""
You are an expert SQL query generator for a student accommodation database.

Database Schema:
{schema}

User Query: {query}
User Preferences: {preferences}

Generate a SAFE SQL query to find relevant accommodations. Rules:
1. Always include WHERE available = true
2. Use ORDER BY for logical sorting (rent for budget queries, distance for location queries, etc.)
3. Add appropriate LIMIT (usually 5-10 results)
4. Only use SELECT statements - no DELETE, UPDATE, INSERT, DROP, ALTER
5. Be flexible with user language (PG means paying guest)

SQL Query:
""")
        
        self.sql_chain = (
            {"schema": lambda x: DB_SCHEMA, "query": lambda x: x["query"], "preferences": lambda x: x["preferences"]}
            | sql_prompt 
            | self.llm 
            | StrOutputParser()
        )
        
        # 2. Response Formatting Chain
        format_prompt = ChatPromptTemplate.from_template("""
You are a helpful student accommodation assistant. Based on the user's query and the search results, provide a natural, conversational response.

User Query: {query}
Search Results: {results}
User Preferences: {preferences}

Provide a helpful response that:
1. Directly addresses the user's question
2. Summarizes the best options found
3. Highlights key features (rent, location, amenities)
4. Suggests next steps if appropriate
5. Uses friendly, conversational tone

Response:
""")
        
        self.format_chain = (
            {"query": lambda x: x["query"], "results": lambda x: x["results"], "preferences": lambda x: x["preferences"]}
            | format_prompt
            | self.llm
            | StrOutputParser()
        )
    
    def execute_sql(self, sql_query: str):
        """Execute SQL query and return results"""
        try:
            # Clean the SQL query
            sql_query = self.clean_sql(sql_query)
            
            # Safety check
            if not self.is_safe_sql(sql_query):
                raise Exception("Unsafe SQL query detected")
            
            # Execute query
            if DATABASE_URI.startswith('postgresql://'):
                connection_string = DATABASE_URI.replace('postgresql://', 'postgresql+psycopg2://')
            else:
                connection_string = DATABASE_URI
            
            # Parse URL for psycopg2
            parsed = urlparse(DATABASE_URI)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],  # Remove leading /
                user=parsed.username,
                password=parsed.password
            )
            
            cursor = conn.cursor()
            cursor.execute(sql_query)
            results = cursor.fetchall()
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to list of dictionaries
            data = [dict(zip(columns, row)) for row in results]
            
            cursor.close()
            conn.close()
            
            return data
            
        except Exception as e:
            print(f" SQL Execution Error: {e}")
            return []
    
    def clean_sql(self, sql_query: str) -> str:
        """Clean SQL query from markdown formatting"""
        if hasattr(sql_query, 'content'):
            sql_query = sql_query.content
        
        sql_query = str(sql_query)
        
        if "```sql" in sql_query:
            sql_query = sql_query.split("```sql")[1].split("```")[0]
        elif "```" in sql_query:
            sql_query = sql_query.split("```")[1].split("```")[0]
        
        return sql_query.strip()
    
    def is_safe_sql(self, sql: str) -> bool:
        """Check if SQL query is safe"""
        forbidden = ["delete", "drop", "update", "insert", "alter", "truncate", "create"]
        sql_lower = sql.lower()
        return not any(keyword in sql_lower for keyword in forbidden)
    
    def process_query(self, user_query: str, user_preferences: dict = None):
        """Complete query processing pipeline"""
        try:
            if user_preferences is None:
                user_preferences = {}
            
            print(f"🔸 Processing query: {user_query}")
            print(f"🔸 User preferences: {user_preferences}")
            
            # Step 1: Generate SQL using LangChain
            sql_input = {
                "query": user_query,
                "preferences": json.dumps(user_preferences, indent=2)
            }
            
            generated_sql = self.sql_chain.invoke(sql_input)
            print(f"🔹 Generated SQL: {generated_sql}")
            
            # Step 2: Execute SQL
            results = self.execute_sql(generated_sql)
            print(f"🔹 Found {len(results)} results")
            
            # Step 3: Format response using LangChain
            if results:
                format_input = {
                    "query": user_query,
                    "results": json.dumps(results[:5], indent=2),  # Limit for token efficiency
                    "preferences": json.dumps(user_preferences, indent=2)
                }
                
                formatted_response = self.format_chain.invoke(format_input)
                
                return {
                    "type": "accommodation_search",
                    "query": user_query,
                    "sql_generated": generated_sql,
                    "results_count": len(results),
                    "accommodations": results[:5],  # Return top 5
                    "response": formatted_response,
                    "preferences": user_preferences
                }
            else:
                return {
                    "type": "no_results",
                    "query": user_query,
                    "sql_generated": generated_sql,
                    "response": "I couldn't find any accommodations matching your criteria. Try adjusting your preferences like budget range or location.",
                    "preferences": user_preferences
                }
                
        except Exception as e:
            print(f"❌ Smart SQL Agent Error: {e}")
            return {
                "type": "error",
                "query": user_query,
                "error": str(e),
                "response": "I'm having trouble processing your request right now. Please try again or rephrase your question."
            }

# Global instance
smart_sql_agent = SmartSQLAgent()