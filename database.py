import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_FILE = os.getenv("DB_FILE", "flats.db")
MAX_ATTEMPTS_EXPOSE = int(os.getenv("MAX_ATTEMPTS_EXPOSE", 50))

def init_db():
    """Initialize the database if it doesn't already exist."""
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exposes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expose_id TEXT UNIQUE,
                source TEXT,
                title TEXT,
                price_kalt TEXT,
                price_warm TEXT,
                nebekosten TEXT,
                location TEXT,
                square_meters TEXT,
                number_of_rooms TEXT,
                agent_name TEXT,
                real_estate_agency TEXT,
                energetic_rating TEXT,
                construction_year TEXT,
                description TEXT,
                neighborhood TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed INTEGER DEFAULT 0,
                failures INTEGER DEFAULT 0
            );
        """)
        conn.commit()
        conn.close()
        print("Database created and initialized.")
    else:
        print("Database already exists.")
        

def insert_expose(expose_id, **fields):
    """Insert a new expose into the database with optional fields."""
    default_fields = {
        'source': None, 'title': None, 'price_kalt': None, 'price_warm': None, 'nebekosten': None, 
        'location': None, 'square_meters': None, 'number_of_rooms': None, 
        'agent_name': None, 'real_estate_agency': None, 'energetic_rating': None, 
        'construction_year': None, 'description': None, 'neighborhood': None, 'processed': 0, 'failures' : 0
    }
    default_fields.update(fields)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO exposes (
                expose_id, source, title, price_kalt, price_warm, nebekosten, location, square_meters, 
                number_of_rooms, agent_name, real_estate_agency, energetic_rating, 
                construction_year, description, neighborhood, processed, failures
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            expose_id, default_fields['source'], default_fields['title'], default_fields['price_kalt'], 
            default_fields['price_warm'], default_fields['nebekosten'], default_fields['location'], 
            default_fields['square_meters'], default_fields['number_of_rooms'], default_fields['agent_name'], 
            default_fields['real_estate_agency'], default_fields['energetic_rating'], default_fields['construction_year'], 
            default_fields['description'], default_fields['neighborhood'], default_fields['processed'], default_fields['failures']
        ))
        conn.commit()
        print(f"Expose {expose_id} inserted successfully.")
    except sqlite3.IntegrityError:
        print(f"Expose {expose_id} already exists in the database.")
    conn.close()

def expose_exists(expose_id):
    """Check if an expose already exists in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM exposes WHERE expose_id=?", (expose_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def print_all_exposes():
    """Prints all exposes in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exposes")
    rows = cursor.fetchall()

    if rows:
        print("\n=== All Exposes in Database ===")
        for row in rows:
            print(row)
        print("================================\n")
    else:
        print("No exposes found in the database.\n")
    conn.close()

def clear_exposes():
    """Deletes all exposes from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exposes")
    conn.commit()
    print("All exposes have been deleted from the database.\n")
    conn.close()

def delete_expose_by_id(expose_id):
    """Deletes a specific expose by expose_id."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exposes WHERE expose_id=?", (expose_id,))
    if cursor.rowcount:
        print(f"Expose {expose_id} deleted from the database.\n")
    else:
        print(f"Expose {expose_id} not found in the database.\n")
    conn.commit()
    conn.close()

def mark_expose_as_processed(expose_id):
    """Marks an expose as processed."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE exposes SET processed=1 WHERE expose_id=?
    """, (expose_id,))
    if cursor.rowcount:
        print(f"Expose {expose_id} marked as processed.\n")
    else:
        print(f"Expose {expose_id} not found in the database.\n")
    conn.commit()
    conn.close()

def get_unprocessed_exposes():
    """Retrieves all unprocessed exposes."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enable access by column names
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exposes WHERE processed=0 AND failures < 6")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_expose(expose_id, **fields):
    """Updates specific fields of a given expose."""
    if not fields:
        print("No fields to update.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    placeholders = ", ".join([f"{key}=?" for key in fields.keys()])
    values = list(fields.values()) + [expose_id]

    cursor.execute(f"""
        UPDATE exposes SET {placeholders} WHERE expose_id=?
    """, values)

    if cursor.rowcount:
        print(f"Expose {expose_id} updated successfully.\n")
    else:
        print(f"Expose {expose_id} not found in the database.\n")
    conn.commit()
    conn.close()

def increase_failures_count(expose_id):
    """Increases the failures count by one for the specified expose_id.
    Marks the expose as processed if the failures count exceeds MAX_ATTEMPTS_EXPOSE.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Increment failures count
    cursor.execute("""
        UPDATE exposes SET failures = failures + 1 WHERE expose_id=?
    """, (expose_id,))

    # Check updated failures count
    cursor.execute("""
        SELECT failures FROM exposes WHERE expose_id=?
    """, (expose_id,))
    result = cursor.fetchone()

    if result:
        failures_count = result[0]
        print(f"Failures count for expose {expose_id} increased to {failures_count}.")
        
        # Mark as processed if failures exceed maximum attempts
        if failures_count >= MAX_ATTEMPTS_EXPOSE:
            cursor.execute("""
                UPDATE exposes SET processed=1 WHERE expose_id=?
            """, (expose_id,))
            print(f"Expose {expose_id} marked as processed due to exceeding failures limit.\n")
    else:
        print(f"Expose {expose_id} not found in the database.\n")

    conn.commit()
    conn.close()
