import sqlite3

DB_FILE = "flats.db"

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
