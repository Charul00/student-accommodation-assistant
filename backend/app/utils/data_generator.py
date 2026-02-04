import random
import psycopg2
from faker import Faker
from dotenv import load_dotenv
import os

load_dotenv()
fake = Faker()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

cursor = conn.cursor()

LOCATIONS = ["Andheri", "Bandra", "Powai", "Viman Nagar", "Hinjewadi"]
ROOM_TYPES = ["pg", "1rk", "1bhk", "3bhk"]

print("Inserting accommodations...")

for _ in range(700):
    cursor.execute("""
        INSERT INTO accommodations
        (type, rent, location, distance_from_college_km, furnished,
         non_alcoholic, smoking_allowed, safety_rating,
         roommates_allowed, available)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        random.choice(ROOM_TYPES),
        random.randint(6000, 28000),
        random.choice(LOCATIONS),
        round(random.uniform(0.5, 12), 2),
        random.choice([True, False]),
        random.choice([True, False]),
        random.choice([True, False]),
        random.randint(1, 5),
        random.choice([True, False]),
        random.choice([True, True, True, False])  # mostly available
    ))

print("Inserting students...")

for _ in range(50):
    cursor.execute("""
        INSERT INTO students
        (name, budget, preferred_location, room_type,
         non_alcoholic, hobbies)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        fake.name(),
        random.randint(7000, 25000),
        random.choice(LOCATIONS),
        random.choice(ROOM_TYPES),
        random.choice([True, False]),
        ", ".join(fake.words(nb=3))
    ))

conn.commit()
cursor.close()
conn.close()

print("Data generation completed")