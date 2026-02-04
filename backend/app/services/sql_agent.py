from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database configuration - prioritize DATABASE_URL for deployment
DATABASE_URI = os.getenv('DATABASE_URL')

if not DATABASE_URI:
    # Fallback to individual environment variables (local development)
    DB_USER = os.getenv('DB_USER', 'charulchim')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'accommodation')
    DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQL Safety Configuration
FORBIDDEN_KEYWORDS = ["delete", "drop", "update", "insert", "alter", "truncate"]

def is_safe_sql(sql: str) -> bool:
    sql_lower = sql.lower()
    return not any(keyword in sql_lower for keyword in FORBIDDEN_KEYWORDS)

def clean_sql(sql_query) -> str:
    """Clean up SQL query by removing markdown code block formatting and extract content from AIMessage"""
    # Handle AIMessage objects
    if hasattr(sql_query, 'content'):
        sql_query = sql_query.content
    
    # Convert to string if not already
    sql_query = str(sql_query)
    
    if sql_query.startswith("```sql"):
        sql_query = sql_query.replace("```sql\n", "").replace("```", "").strip()
    elif sql_query.startswith("```"):
        sql_query = sql_query.replace("```\n", "").replace("```", "").strip()
    return sql_query.strip()

try:
    db = SQLDatabase.from_uri(DATABASE_URI)
except Exception as e:
    print(f"Error connecting to database: {e}")
    db = None

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# Create SQL chain using SQLDatabaseChain
sql_db_chain = None
if db:
    try:
        sql_db_chain = SQLDatabaseChain.from_llm(
            llm=llm,
            db=db,
            verbose=True,
            return_intermediate_steps=False
        )
    except Exception as e:
        print(f"Error creating SQL chain: {e}")

SQL_PROMPT_TEXT = """
You are an expert PostgreSQL assistant for student accommodation search.

Database schema:
Table: accommodations
- id: integer
- type: pg | 1rk | 1bhk | 3bhk
- rent: monthly rent in INR
- location: area name (like "Andheri", "Viman Nagar", "Koregaon Park", etc.)
- distance_from_college_km: float
- furnished: boolean
- non_alcoholic: boolean (True = no alcohol allowed, False = alcohol allowed)
- smoking_allowed: boolean
- safety_rating: integer (1 to 5)
- roommates_allowed: boolean
- available: boolean

Location matching rules:
- Use ILIKE for case-insensitive matching
- For city queries like "Pune", use: location ILIKE '%pune%'
- For specific areas, use exact matching: location ILIKE '%area_name%'

Lifestyle preference mapping rules:
- "alcohol-free" or "non-alcoholic" → non_alcoholic = true
- "alcohol allowed" → non_alcoholic = false
- "smoking friendly" or "smoking allowed" → smoking_allowed = true  
- "smoke-free" or "no smoking" → smoking_allowed = false
- "furnished accommodation" → furnished = true
- "unfurnished accommodation" → furnished = false

Query rules:
- Generate ONLY a SELECT query
- Do NOT use markdown or ```sql
- Always include WHERE available = true
- Use ILIKE for location matching
- Order by rent ASC for better results
- Limit results to max 10 rows
"""

def format_natural_response(result, query_type="search"):
    """Format database results into natural language response"""
    if not result or result == "[]" or len(str(result).strip()) <= 2:
        return "🏠 Sorry, we couldn't find any accommodations matching your criteria. This might not be under our services currently. Please try searching in different cities or areas like Mumbai, Pune, Bangalore, or adjust your requirements like budget or accommodation type."
    
    try:
        # If result is a string representation of a list
        if isinstance(result, str):
            if result.startswith('[') and result.endswith(']'):
                # Parse the string representation of results
                import ast
                try:
                    parsed_result = ast.literal_eval(result)
                    if not parsed_result:
                        return "🏠 Sorry, we couldn't find any accommodations matching your criteria. This might not be under our services currently. Please try searching in different cities or areas like Mumbai, Pune, Bangalore, or adjust your requirements like budget or accommodation type."
                except:
                    pass
        
        return f"🏠 Found accommodation options:\n{result}"
    except Exception as e:
        return "🏠 Sorry, we couldn't find any accommodations matching your criteria. This might not be under our services currently. Please try searching in different cities or areas like Mumbai, Pune, Bangalore, or adjust your requirements like budget or accommodation type."

def format_sql_result(result):
    """Format SQL result into clean JSON structure"""
    # If LangChain returned a string, convert it
    if isinstance(result, str):
        try:
            import ast
            result = ast.literal_eval(result)
        except Exception:
            return []

    if not isinstance(result, list):
        return []

    columns = [
        "id",
        "type", 
        "rent",
        "location",
        "distance_from_college_km",
        "furnished",
        "non_alcoholic",
        "smoking_allowed",
        "safety_rating",
        "roommates_allowed",
        "available"
    ]

    formatted = []
    for row in result:
        formatted.append(dict(zip(columns, row)))

    return formatted

def run_sql_query(question: str):
    if db is None or sql_db_chain is None:
        return None, "Database connection not available"
    
    try:
        # First, let's check if we have any data at all
        try:
            check_data = db.run("SELECT COUNT(*) as total_count FROM accommodations;")
            print(f"🔍 Total accommodations in database: {check_data}")
            
            sample_data = db.run("SELECT location, type, rent, available FROM accommodations LIMIT 5;")
            print(f"🔍 Sample data: {sample_data}")
        except Exception as check_error:
            print(f"🔍 Database check error: {check_error}")
        
        # Prepare the prompt with context
        full_question = f"{SQL_PROMPT_TEXT}\n\nUser question: {question}\n\nGenerate the SQL query to find relevant accommodations:"
        
        # Use SQLDatabaseChain to run the query
        result = sql_db_chain.run(full_question)
        print(f"🔹 RAW RESULT: {result}")
        print(f"🔹 RESULT TYPE: {type(result)}")
        
        # For SQLDatabaseChain, result is typically a string, so we need to parse it
        # Let's format it into the structure expected by the frontend
        formatted_result = format_sql_result(result)
        
        return "SQL query executed", formatted_result
        
    except Exception as e:
        print(f"🔹 SQL Error: {e}")
        return None, f"🏠 Sorry, we encountered an issue processing your request. Please try rephrasing your query or search for accommodations in major cities like Mumbai, Pune, or Bangalore. Error: {e}"