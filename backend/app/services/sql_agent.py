from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
import psycopg2
from urllib.parse import urlparse
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

# SQL Safety Configuration
FORBIDDEN_KEYWORDS = ["delete", "drop", "update", "insert", "alter", "truncate"]

def is_safe_sql(sql: str) -> bool:
    sql_lower = sql.lower()
    return not any(keyword in sql_lower for keyword in FORBIDDEN_KEYWORDS)

def get_db_connection():
    """Get direct database connection"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        parsed = urlparse(database_url)
        return psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remove leading '/'
            user=parsed.username,
            password=parsed.password
        )
    
    # Fallback for local development
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'accommodation'),
        user=os.getenv('DB_USER', 'charulchim'),
        password=os.getenv('DB_PASSWORD', 'password')
    )

def simple_search_accommodations(question: str):
    """Simple accommodation search using basic SQL"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Parse the question for common search patterns
        question_lower = question.lower()
        
        # Build WHERE conditions based on question
        conditions = ["available = true"]
        
        # Location search
        for location in ['andheri', 'malad', 'bandra', 'powai', 'viman nagar', 'koregaon park', 'baner', 'kharadi', 'wakad', 'koramangala', 'indiranagar', 'electronic city']:
            if location in question_lower:
                conditions.append(f"location ILIKE '%{location}%'")
                break
        
        # City search
        if 'mumbai' in question_lower and not any('location ILIKE' in c for c in conditions[1:]):
            conditions.append("location ILIKE '%andheri%' OR location ILIKE '%malad%' OR location ILIKE '%bandra%' OR location ILIKE '%powai%'")
        elif 'pune' in question_lower and not any('location ILIKE' in c for c in conditions[1:]):
            conditions.append("location ILIKE '%viman nagar%' OR location ILIKE '%koregaon park%' OR location ILIKE '%baner%' OR location ILIKE '%kharadi%' OR location ILIKE '%wakad%'")
        elif 'bangalore' in question_lower and not any('location ILIKE' in c for c in conditions[1:]):
            conditions.append("location ILIKE '%koramangala%' OR location ILIKE '%indiranagar%' OR location ILIKE '%electronic city%'")
        
        # Budget search
        if 'under' in question_lower or 'below' in question_lower:
            import re
            budget_match = re.search(r'(\d+)k?', question_lower)
            if budget_match:
                budget = int(budget_match.group(1))
                if budget < 1000:  # Assume 'k' format (e.g., "10k")
                    budget *= 1000
                conditions.append(f"rent <= {budget}")
        
        # Type search
        if 'pg' in question_lower:
            conditions.append("type = 'pg'")
        elif '1bhk' in question_lower or '1 bhk' in question_lower:
            conditions.append("type = '1bhk'")
        elif '1rk' in question_lower or '1 rk' in question_lower:
            conditions.append("type = '1rk'")
        
        # Furnished search
        if 'furnished' in question_lower:
            conditions.append("furnished = true")
        elif 'unfurnished' in question_lower:
            conditions.append("furnished = false")
        
        # Alcohol policy
        if 'alcohol free' in question_lower or 'non alcoholic' in question_lower:
            conditions.append("non_alcoholic = true")
        elif 'alcohol allowed' in question_lower:
            conditions.append("non_alcoholic = false")
        
        # Smoking policy
        if 'no smoking' in question_lower or 'smoke free' in question_lower:
            conditions.append("smoking_allowed = false")
        elif 'smoking allowed' in question_lower:
            conditions.append("smoking_allowed = true")
        
        # Build final query
        where_clause = " AND ".join(conditions)
        if len(conditions) > 1:  # More than just 'available = true'
            where_clause = f"({where_clause})"
        
        sql = f"""
        SELECT id, type, rent, location, distance_from_college_km, furnished, 
               non_alcoholic, smoking_allowed, safety_rating, roommates_allowed, available
        FROM accommodations 
        WHERE {where_clause}
        ORDER BY rent ASC
        LIMIT 10
        """
        
        print(f"🔹 GENERATED SQL: {sql}")
        
        cursor.execute(sql)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Format results
        columns = [
            "id", "type", "rent", "location", "distance_from_college_km",
            "furnished", "non_alcoholic", "smoking_allowed", "safety_rating",
            "roommates_allowed", "available"
        ]
        
        formatted_results = []
        for row in results:
            formatted_results.append(dict(zip(columns, row)))
        
        return "SQL query executed", formatted_results
        
    except Exception as e:
        print(f"🔹 Search Error: {e}")
        return None, f"🏠 Sorry, we encountered an issue. Error: {e}"

try:
    db = SQLDatabase.from_uri(DATABASE_URI)
except Exception as e:
    print(f"Error connecting to database: {e}")
    db = None

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

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
    """Run accommodation search query"""
    try:
        # Use simple search function instead of complex LangChain chain
        return simple_search_accommodations(question)
        
    except Exception as e:
        print(f"🔹 SQL Error: {e}")
        return None, f"🏠 Sorry, we encountered an issue processing your request. Please try rephrasing your query or search for accommodations in major cities like Mumbai, Pune, or Bangalore. Error: {e}"