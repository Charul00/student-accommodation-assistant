#!/usr/bin/env python3

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DB_USER = os.getenv('DB_USER', 'charulchim')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'accommodation')

def create_table_and_sample_data():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
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
        
        # Display current data
        cursor.execute("SELECT * FROM accommodations LIMIT 5;")
        results = cursor.fetchall()
        print("\n📋 Sample data in database:")
        for row in results:
            print(f"ID: {row[0]}, Type: {row[1]}, Rent: {row[2]}, Location: {row[3]}")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_table_and_sample_data()