from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat
import os

app = FastAPI(
    title="Student Accommodation Assistant API",
    description="AI-powered student accommodation search and policy assistant",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup if needed"""
    # Only initialize database in production (when DATABASE_URL is set)
    if os.getenv("DATABASE_URL"):
        try:
            import sys
            sys.path.append('..')
            from init_db import init_database
            init_database()
            print("✅ Database initialization completed successfully!")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            import traceback
            traceback.print_exc()
            raise e  # Re-raise to make deployment fail if DB init fails

@app.get("/")
def health_check():
    return {"status": "Backend is running "}

@app.get("/health")
def detailed_health_check():
    """Detailed health check including database status"""
    try:
        # Check database connection and data
        import sys
        sys.path.append('..')
        from init_db import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM accommodations;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return {
            "status": "healthy",
            "backend": "running",
            "database": "connected",
            "accommodations_count": count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "backend": "running",
            "database": "error",
            "error": str(e)
        }