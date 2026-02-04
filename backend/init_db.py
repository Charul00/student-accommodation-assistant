#!/usr/bin/env python3
"""
Database initialization script for deployment
This script will be run automatically when the app starts
"""
import psycopg2
import os
import sys
from urllib.parse import urlparse

def get_db_connection():
    """Get database connection from environment variables"""
    # First try DATABASE_URL (Render format)
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
    
    # Fallback to individual environment variables (local development)
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'accommodation'),
        user=os.getenv('DB_USER', 'charulchim'),
        password=os.getenv('DB_PASSWORD', 'password')
    )

def create_tables():
    """Create database tables if they don't exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create accommodations table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS accommodations (
            id SERIAL PRIMARY KEY,
            type VARCHAR(10) NOT NULL,
            rent INTEGER NOT NULL,
            location VARCHAR(100) NOT NULL,
            distance_from_college_km FLOAT,
            furnished BOOLEAN,
            non_alcoholic BOOLEAN,
            smoking_allowed BOOLEAN,
            safety_rating INTEGER CHECK (safety_rating >= 1 AND safety_rating <= 5),
            roommates_allowed BOOLEAN,
            available BOOLEAN DEFAULT TRUE
        );
        """
        cursor.execute(create_table_sql)
        conn.commit()
        print("✅ Database tables created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def populate_sample_data():
    """Populate database with sample data if empty"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM accommodations;")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insert sample data
            sample_data = [
                # Pune locations
                ('pg', 8000, 'Viman Nagar', 2.5, True, False, True, 4, True, True),
                ('pg', 9500, 'Koregaon Park', 1.8, False, True, False, 5, True, True),
                ('1rk', 12000, 'Baner', 3.2, True, False, False, 4, False, True),
                ('pg', 7500, 'Kharadi', 4.1, True, True, False, 3, True, True),
                ('1bhk', 15000, 'Wakad', 5.0, True, False, True, 4, True, True),
                
                # Mumbai locations  
                ('pg', 11000, 'Andheri', 1.5, True, True, False, 4, True, True),
                ('pg', 9000, 'Malad', 2.8, False, False, True, 3, True, True),
                ('1rk', 18000, 'Bandra', 0.8, True, True, False, 5, False, True),
                ('pg', 8500, 'Powai', 3.5, True, False, False, 4, True, True),
                
                # Bangalore locations
                ('pg', 9000, 'Koramangala', 2.0, True, False, True, 4, True, True),
                ('1bhk', 16000, 'Indiranagar', 1.2, True, True, False, 5, True, True),
                ('pg', 7000, 'Electronic City', 8.5, False, False, True, 3, True, True),
            ]
            
            insert_sql = """
            INSERT INTO accommodations 
            (type, rent, location, distance_from_college_km, furnished, non_alcoholic, 
             smoking_allowed, safety_rating, roommates_allowed, available)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_sql, sample_data)
            conn.commit()
            print(f"✅ Added {len(sample_data)} sample accommodations to the database")
        else:
            print(f"ℹ️ Database already has {count} accommodations")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error populating data: {e}")
        return False

def init_database():
    """Initialize database for deployment"""
    print("🔧 Initializing database...")
    
    if not create_tables():
        sys.exit(1)
    
    if not populate_sample_data():
        sys.exit(1)
    
    print("✅ Database initialization complete!")

if __name__ == "__main__":
    init_database()