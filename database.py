import sqlite3
import os

DB_FILE = "flats.db"

def init_db():
    """Initialize the database if it doesn't already exist."""
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exposes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expose_id TEXT UNIQUE,
                title TEXT,
                price_kalt TEXT,
                price_warm TEXT,
                location TEXT,
                size TEXT,
                number_of_rooms TEXT,
                agent_name TEXT,
                real_estate_agency TEXT,
                energetic_rating TEXT,
                construction_year TEXT,
                description TEXT,
                neighborhood TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed INTEGER DEFAULT 0
            );
        """)
        conn.commit()
        conn.close()
        print("Database created and initialized.")
    else:
        print("Database already exists.")

def insert_expose(data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO exposes (
                expose_id, title, price_kalt, price_warm, location, size, 
                number_of_rooms, agent_name, real_estate_agency, energetic_rating, 
                construction_year, description, neighborhood, processed
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        print(f"Inserted expose {data[0]} into the database.")
    except sqlite3.IntegrityError:
        print(f"Expose {data[0]} already exists in the database.")
    conn.close()

def expose_exists(expose_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM exposes WHERE expose_id=?", (expose_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists
